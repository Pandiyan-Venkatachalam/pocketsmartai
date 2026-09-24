from typing import Dict, Any, List
from app.services.planning.interfaces import IPlanner, ICalculationEngine
from app.schemas.custom_planner import CustomPlannerOutput, CustomPlannerInput, FeasibilityData
from app.services.gemini_service import gemini_service
from app.services.rate_service import rate_service

class SchoolCalculationEngine(ICalculationEngine):
    def calculate(self, budget: float, requirements: dict) -> dict:
        # requirements is now the parsed AI JSON dict!
        
        classrooms = int(requirements.get("classrooms", 0))
        if classrooms == 0:
            classrooms = 6 # ultimate fallback if AI failed
            
        has_staff_room = int(requirements.get("staff_rooms", 0)) > 0
        has_principal = int(requirements.get("principal_offices", 0)) > 0
        has_boys_toilet = int(requirements.get("boys_washrooms", 0)) > 0
        has_girls_toilet = int(requirements.get("girls_washrooms", 0)) > 0
        has_general_toilet = int(requirements.get("general_washrooms", 0)) > 0
        
        floors = int(requirements.get("floors", 2))
        if floors < 1:
            floors = 1
            
        exclusions = requirements.get("exclusions", [])
        
        # 2. Space Planning
        classroom_area = rate_service.get_rate("construction", "classroom_area_sqft", 400)
        office_area = rate_service.get_rate("construction", "office_area_sqft", 150)
        staff_room_area = rate_service.get_rate("construction", "staff_room_area_sqft", 200)
        toilet_area = rate_service.get_rate("construction", "toilet_area_sqft", 100)
        
        total_classroom_area = classrooms * classroom_area
        total_office_area = office_area if has_principal else 0
        total_staff_area = staff_room_area if has_staff_room else 0
        
        toilets_count = 0
        if has_boys_toilet: toilets_count += 1
        if has_girls_toilet: toilets_count += 1
        if has_general_toilet: toilets_count += 1
        total_toilet_area = toilets_count * toilet_area
        
        net_usable_area = total_classroom_area + total_office_area + total_staff_area + total_toilet_area
        circulation_factor = rate_service.get_rate("construction", "circulation_multiplier", 1.30)
        gross_built_up_area = net_usable_area * circulation_factor
        
        # Split across floors
        floor_area = gross_built_up_area / floors
        
        # 3. Cost Calculation
        cost_per_sqft = rate_service.get_rate("construction", "institutional_cost_per_sqft", 1800)
        required_budget = gross_built_up_area * cost_per_sqft
        
        # Furniture Calculation
        benches_per = int(rate_service.get_rate("furniture", "benches_per_classroom", 20))
        benches = classrooms * benches_per
        bench_cost = rate_service.get_rate("furniture", "school_bench_cost", 3000)
        blackboards = classrooms
        board_cost = rate_service.get_rate("furniture", "blackboard_cost", 5000)
        
        # Respect exclusions
        total_furniture_cost = 0
        furniture_breakdown = []
        
        if not any("bench" in ex.lower() or "furniture" in ex.lower() for ex in exclusions):
            total_furniture_cost += (benches * bench_cost)
            furniture_breakdown.append({"category": f"School Benches ({benches} units)", "cost": benches * bench_cost})
            
        if not any("board" in ex.lower() for ex in exclusions):
            total_furniture_cost += (blackboards * board_cost)
            furniture_breakdown.append({"category": f"Blackboards ({blackboards} units)", "cost": blackboards * board_cost})
            
        total_project_cost = required_budget + total_furniture_cost
        
        shortfall = total_project_cost - budget if total_project_cost > budget else 0
        
        # Breakdown
        breakdown = [
            {"category": "Foundation & Plinth", "cost": required_budget * 0.15},
            {"category": "RCC Framework", "cost": required_budget * 0.25},
            {"category": "Masonry & Plaster", "cost": required_budget * 0.15},
            {"category": "Flooring (Basic Ceramic)", "cost": required_budget * 0.10},
            {"category": "Doors & Windows", "cost": required_budget * 0.10},
            {"category": "Electrical & Plumbing", "cost": required_budget * 0.15},
            {"category": "Painting & Finishing", "cost": required_budget * 0.10},
        ]
        breakdown.extend(furniture_breakdown)
        
        # Materials Calculation
        cement_factor = rate_service.get_rate("materials", "institutional_cement_factor", 0.45)
        steel_factor = rate_service.get_rate("materials", "institutional_steel_factor", 3.5)
        
        cement_bags = gross_built_up_area * cement_factor
        steel_kg = gross_built_up_area * steel_factor
        
        cement_price = rate_service.get_rate("materials", "cement_price_per_bag", 400)
        steel_price = rate_service.get_rate("materials", "steel_price_per_kg", 65)
        tile_price = rate_service.get_rate("materials", "basic_tile_price_per_sqft", 50)
        
        materials = [
            {"name": "Cement", "estimated_quantity": f"Approximately {int(cement_bags * 0.9)}–{int(cement_bags * 1.1)} bags", "cost_estimate": cement_bags * cement_price, "source": f"Based on {cement_factor} bags/sq.ft for RCC G+{floors-1}"},
            {"name": "Steel", "estimated_quantity": f"Approximately {steel_kg / 1000:.1f}–{(steel_kg * 1.1) / 1000:.1f} tonnes", "cost_estimate": steel_kg * steel_price, "source": f"Based on {steel_factor} kg/sq.ft for Institutional G+{floors-1}"},
            {"name": "Basic Ceramic Tiles", "estimated_quantity": f"Approximately {int(net_usable_area)} sq.ft", "cost_estimate": net_usable_area * tile_price, "source": "Net Usable Area + 5% wastage"}
        ]
        
        space_plan = []
        if floors == 1:
            space_plan.extend([
                "SINGLE FLOOR:",
                f"- {classrooms} Classrooms",
                "- Principal Office" if has_principal else "",
                "- Staff Room" if has_staff_room else "",
                "- Washrooms",
                "- Corridors & Circulation"
            ])
        else:
            space_plan.extend([
                "GROUND FLOOR:",
                f"- {classrooms // floors} Classrooms",
                "- Principal Office" if has_principal else "",
                "- Staff Room" if has_staff_room else "",
                "- Washrooms",
                "- Staircase & Corridors",
                "",
                f"UPPER FLOOR(S) (Total {floors-1}):",
                f"- {classrooms - (classrooms // floors)} Classrooms",
                "- Staircase & Circulation"
            ])
            
        space_plan.append("")
        space_plan.append(f"Total Estimated Built-Up Area: {int(gross_built_up_area)} sq.ft")
        
        space_plan = [line for line in space_plan if line != ""]
        
        return {
            "gross_built_up_area": gross_built_up_area,
            "required_budget": total_project_cost,
            "shortfall": shortfall,
            "breakdown": breakdown,
            "materials": materials,
            "space_plan": space_plan,
            "budget": budget,
            "classrooms": classrooms,
            "floors": floors,
            "cost_per_sqft": cost_per_sqft,
            "exclusions": exclusions
        }

class SchoolConstructionPlanner(IPlanner):
    @property
    def domain(self) -> str:
        return "SCHOOL_CONSTRUCTION"

    def __init__(self):
        self.engine = SchoolCalculationEngine()

    def generate_plan(self, request: CustomPlannerInput) -> CustomPlannerOutput:
        items_str = " ".join(request.target_items) if isinstance(request.target_items, list) else str(request.target_items or "")
        requirements_text = f"{request.plan_title} {items_str} {request.preferences}"
        
        # 1. Ask Gemini to extract the spaces from the user's text
        prompt = gemini_service.build_space_extraction_prompt(requirements_text)
        parsed_spaces, is_mock = gemini_service.generate_recommendations(prompt)
        
        if not parsed_spaces or is_mock:
            # Fallback to defaults if AI is down
            parsed_spaces = {
                "classrooms": 6,
                "staff_rooms": 1,
                "principal_offices": 1,
                "boys_washrooms": 1,
                "girls_washrooms": 1,
                "floors": 2,
                "exclusions": []
            }
            
        # 2. Pass the structured AI output to our deterministic engine
        calc = self.engine.calculate(request.budget, parsed_spaces)
        
        if calc["shortfall"] > 0:
            status = "BUDGET_CONSTRAINED"
        else:
            status = "FEASIBLE"
            
        feasibility = FeasibilityData(
            status=status,
            details={
                "RequestedConfiguration": f"{calc['classrooms']} classrooms + G+{calc['floors']-1}",
                "EstimatedRequiredBudget": f"₹{int(calc['required_budget']):,}",
                "AvailableBudget": f"₹{int(calc['budget']):,}",
                "Shortfall": f"₹{int(calc['shortfall']):,}" if calc["shortfall"] > 0 else "None"
            }
        )
        
        assumptions = [
            f"Basic institutional construction rate applied (₹{calc['cost_per_sqft']}/sq.ft).",
            "Basic ceramic flooring and standard electrical/plumbing included.",
            f"Standard RCC G+{calc['floors']-1} structure assumed.",
            "Land and external development excluded.",
            "Final structural design and soil investigation required."
        ]
        
        risks = [
            "Material quantities are preliminary planning estimates.",
            "Final cement, steel, foundation and structural quantities must be determined by a qualified architect/structural engineer based on soil investigation, structural design, drawings and applicable local regulations."
        ]
        
        exclusions = calc["exclusions"]
        if exclusions:
            assumptions.append(f"Explicit User Exclusions: {', '.join(exclusions)}")
            
        recommendations = [
            {"title": "Structural Safety", "reason": "Ensure the design complies with local building codes for educational institutions."},
            {"title": "Ventilation", "reason": "Provide cross ventilation in all classrooms to reduce lighting and cooling loads."}
        ]
        
        alternatives = []
        if calc["shortfall"] > 0:
            if calc['floors'] > 1:
                base_floor_cost = (calc['required_budget'] / calc['floors']) + (calc['required_budget'] * 0.05) # Add 5% overhead for foundation
                alternatives.append({
                    "name": "OPTION A - Phased Construction",
                    "description": f"Construct only the Ground Floor initially. Required budget would be approx ₹{int(base_floor_cost):,}."
                })
            alternatives.append({
                "name": "OPTION B - Increase Budget",
                "description": f"Secure an additional funding of ₹{int(calc['shortfall']):,} to build the requested configuration."
            })
            
        space_plan_str = "SPACE PLAN\n" + "\n".join(calc["space_plan"])
        
        return CustomPlannerOutput(
            planner="custom",
            plan_title=request.plan_title,
            domain=self.domain,
            budget=request.budget,
            budget_used=calc["required_budget"],
            remaining_budget=0 if calc["shortfall"] > 0 else (request.budget - calc["required_budget"]),
            ai_notes=space_plan_str,
            feasibility=feasibility,
            cost_breakdown=calc["breakdown"],
            materials=calc["materials"],
            assumptions=assumptions,
            risks=risks,
            alternative_plans=alternatives,
            recommendations=recommendations,
            items=[]
        )
