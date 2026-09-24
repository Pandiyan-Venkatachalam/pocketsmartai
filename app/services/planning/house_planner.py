from app.services.planning.interfaces import IPlanner, ICalculationEngine
from app.schemas.custom_planner import CustomPlannerOutput, CustomPlannerInput, FeasibilityData
from app.services.rate_service import rate_service

class HouseConstructionCalculationEngine(ICalculationEngine):
    def calculate(self, budget: float, requirements: dict) -> dict:
        # Simple heuristic: Assumed avg cost per sq ft is configurable
        cost_per_sqft = rate_service.get_rate("construction", "residential_cost_per_sqft", 1600)
        min_sqft = max(0, budget / (cost_per_sqft * 1.25))
        max_sqft = max(0, budget / (cost_per_sqft * 0.85))
        
        sqft_estimate = budget / cost_per_sqft
        reserve = budget * 0.05
        working_budget = budget - reserve
        
        # Breakdown percentages
        breakdown = [
            {"category": "Site Prep & Foundation", "cost": working_budget * 0.12},
            {"category": "RCC & Structure", "cost": working_budget * 0.25},
            {"category": "Brickwork & Plastering", "cost": working_budget * 0.15},
            {"category": "Roofing & Flooring", "cost": working_budget * 0.10},
            {"category": "Doors & Windows", "cost": working_budget * 0.10},
            {"category": "Electrical & Plumbing", "cost": working_budget * 0.12},
            {"category": "Painting & Finishes", "cost": working_budget * 0.10},
            {"category": "Miscellaneous", "cost": working_budget * 0.06},
        ]
        
        # Materials quantities
        cement_factor = rate_service.get_rate("materials", "residential_cement_factor", 0.42)
        steel_factor = rate_service.get_rate("materials", "residential_steel_factor", 3.2)
        
        cement_bags = sqft_estimate * cement_factor
        steel_kg = sqft_estimate * steel_factor
        
        cement_price = rate_service.get_rate("materials", "cement_price_per_bag", 400)
        steel_price = rate_service.get_rate("materials", "steel_price_per_kg", 65)
        
        materials = [
            {"name": "Cement", "estimated_quantity": f"{int(cement_bags*0.9)} - {int(cement_bags*1.1)} bags", "cost_estimate": cement_bags * cement_price, "source": "Estimated regional rate"},
            {"name": "Steel", "estimated_quantity": f"{int(steel_kg*0.9)} - {int(steel_kg*1.1)} kg", "cost_estimate": steel_kg * steel_price, "source": "Estimated regional rate"},
            {"name": "Bricks / Blocks", "estimated_quantity": f"{int(15 * sqft_estimate)} numbers", "cost_estimate": working_budget * 0.08, "source": "Estimated regional rate"},
            {"name": "M-Sand / River Sand", "estimated_quantity": f"{int(1.5 * sqft_estimate)} cu.ft", "cost_estimate": working_budget * 0.08, "source": "Estimated regional rate"}
        ]
        
        return {
            "sqft_range": {"min": int(min_sqft), "max": int(max_sqft), "unit": "sq.ft"},
            "reserve": reserve,
            "working_budget": working_budget,
            "breakdown": breakdown,
            "materials": materials
        }

class HouseConstructionPlanner(IPlanner):
    @property
    def domain(self) -> str:
        return "HOUSE_CONSTRUCTION"

    def __init__(self):
        self.engine = HouseConstructionCalculationEngine()

    def generate_plan(self, request: CustomPlannerInput) -> CustomPlannerOutput:
        calc_result = self.engine.calculate(request.budget, {})
        
        feasibility = FeasibilityData(
            status="PRELIMINARY_FEASIBLE" if request.budget >= 500000 else "LOW_BUDGET",
            details={"estimatedBuiltUpArea": calc_result["sqft_range"]}
        )
        
        assumptions = [
            "Land cost is excluded from this estimate.",
            "Based on standard single/double floor residential construction.",
            "Basic to standard finish quality assumed.",
            "Regional average material and labour rates applied.",
            "Approvals and architect fees are excluded."
        ]
        
        risks = [
            "Soil conditions may require deeper foundation costing more.",
            "Material prices fluctuate constantly.",
            "Changes in design will increase costs."
        ]
        
        recommendations = [
            {"title": "Prioritize Core Structure", "reason": "Ensure high-quality cement and steel even if you must delay premium finishing."},
            {"title": "Water Curing", "reason": "Budget for adequate curing time to prevent structural cracks."}
        ]
        
        alternatives = [
            {"name": "Option A — Basic Finish", "description": "Maximize area with basic tiles and standard fittings."},
            {"name": "Option B — Premium Finish", "description": "Reduce built-up area by 20% to afford premium interiors and sanitaryware."}
        ]
        
        return CustomPlannerOutput(
            planner="custom",
            plan_title=request.plan_title,
            domain=self.domain,
            budget=request.budget,
            budget_used=calc_result["working_budget"],
            remaining_budget=calc_result["reserve"],
            ai_notes="Preliminary construction estimate based on standard regional rates.",
            feasibility=feasibility,
            cost_breakdown=calc_result["breakdown"],
            materials=calc_result["materials"],
            assumptions=assumptions,
            risks=risks,
            alternative_plans=alternatives,
            recommendations=recommendations,
            items=[] # No ecommerce products for house construction!
        )
