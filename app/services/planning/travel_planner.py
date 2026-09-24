from app.services.planning.interfaces import IPlanner, ICalculationEngine
from app.schemas.custom_planner import CustomPlannerOutput, CustomPlannerInput, FeasibilityData

class TravelCalculationEngine(ICalculationEngine):
    def calculate(self, budget: float, requirements: dict) -> dict:
        reserve = budget * 0.05
        working_budget = budget - reserve
        
        breakdown = [
            {"category": "Flights / Transport", "cost": working_budget * 0.35},
            {"category": "Accommodation", "cost": working_budget * 0.30},
            {"category": "Food & Dining", "cost": working_budget * 0.15},
            {"category": "Activities & Tours", "cost": working_budget * 0.10},
            {"category": "Local Transport & Misc", "cost": working_budget * 0.10},
        ]
        
        # Heuristic for days/people based on budget
        # Assume ~₹8000 per person per day for standard travel
        from app.services.rate_service import rate_service
        avg_cost_pp_pd = rate_service.get_rate("travel", "avg_cost_pp_pd", 8000)
        estimated_person_days = working_budget / avg_cost_pp_pd
        
        return {
            "reserve": reserve,
            "working_budget": working_budget,
            "breakdown": breakdown,
            "estimated_person_days": int(max(1, estimated_person_days))
        }

class TravelPlanner(IPlanner):
    @property
    def domain(self) -> str:
        return "TRAVEL"

    def __init__(self):
        self.engine = TravelCalculationEngine()

    def generate_plan(self, request: CustomPlannerInput) -> CustomPlannerOutput:
        calc_result = self.engine.calculate(request.budget, {})
        
        from app.services.rate_service import rate_service
        threshold = rate_service.get_rate("travel", "budget_feasibility_threshold", 10000)
        
        feasibility = FeasibilityData(
            status="PRELIMINARY_FEASIBLE" if request.budget >= threshold else "LOW_BUDGET",
            details={"estimatedPersonDays": {"min": calc_result["estimated_person_days"] - 1, "max": calc_result["estimated_person_days"] + 2, "unit": "person-days"}}
        )
        
        assumptions = [
            "Based on standard travel costs (mid-range hotels, standard flights).",
            "Excludes visa fees and premium travel insurance.",
            "Subject to seasonal price variations and booking timing."
        ]
        
        risks = [
            "Flight prices can increase dramatically close to travel dates.",
            "Exchange rate fluctuations for international travel."
        ]
        
        recommendations = [
            {"title": "Book Flights Early", "reason": "Transport is 35% of your budget. Booking 2-3 months ahead saves 20%."},
            {"title": "Use Public Transit", "reason": "Local transport can drain budget quickly if using taxis."}
        ]
        
        alternatives = [
            {"name": "Option A — Shorter Trip, Luxury", "description": "Halve the days, double the accommodation quality."},
            {"name": "Option B — Longer Trip, Budget", "description": "Stay in hostels, use buses, extend trip duration."}
        ]
        
        # Process user's requested items
        materials = []
        items_list = []
        if request.target_items:
            if isinstance(request.target_items, list):
                for item in request.target_items:
                    if isinstance(item, str):
                        items_list.extend([i.strip() for i in item.split(',') if i.strip()])
                    elif item:
                        items_list.append(str(item).strip())
            elif isinstance(request.target_items, str):
                items_list = [i.strip() for i in request.target_items.split(',') if i.strip()]

        if items_list:
            item_budget = calc_result["working_budget"] / len(items_list)
            for item in items_list:
                materials.append({
                    "name": item.title(),
                    "estimated_quantity": "1 Booking",
                    "cost_estimate": item_budget,
                    "source": "Allocated from total budget."
                })
        else:
            materials = [
                {"name": "Flights & Transport", "estimated_quantity": "Round Trip", "cost_estimate": calc_result["working_budget"] * 0.35, "source": "Standard travel model"},
                {"name": "Hotel / Accommodation", "estimated_quantity": f"~{calc_result['estimated_person_days']} nights", "cost_estimate": calc_result["working_budget"] * 0.30, "source": "Standard travel model"}
            ]
            
        return CustomPlannerOutput(
            planner="custom",
            plan_title=request.plan_title,
            domain=self.domain,
            budget=request.budget,
            budget_used=calc_result["working_budget"],
            remaining_budget=calc_result["reserve"],
            ai_notes="Preliminary travel estimate based on standard daily expenditure models.",
            feasibility=feasibility,
            cost_breakdown=calc_result["breakdown"],
            materials=materials,
            assumptions=assumptions,
            risks=risks,
            alternative_plans=alternatives,
            recommendations=recommendations,
            items=[] 
        )
