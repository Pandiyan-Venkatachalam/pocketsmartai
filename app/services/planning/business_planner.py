from app.services.planning.interfaces import IPlanner, ICalculationEngine
from app.schemas.custom_planner import CustomPlannerOutput, CustomPlannerInput, FeasibilityData

class BusinessCalculationEngine(ICalculationEngine):
    def calculate(self, budget: float, requirements: dict) -> dict:
        reserve = budget * 0.10 # Business needs higher contingency
        working_budget = budget - reserve
        
        breakdown = [
            {"category": "Equipment & Machinery", "cost": working_budget * 0.35},
            {"category": "Rent & Deposit", "cost": working_budget * 0.20},
            {"category": "Inventory / Raw Materials", "cost": working_budget * 0.15},
            {"category": "Marketing & Branding", "cost": working_budget * 0.10},
            {"category": "Licenses & Legal", "cost": working_budget * 0.05},
            {"category": "Working Capital (3 months)", "cost": working_budget * 0.15},
        ]
        
        return {
            "reserve": reserve,
            "working_budget": working_budget,
            "breakdown": breakdown
        }

class BusinessSetupPlanner(IPlanner):
    @property
    def domain(self) -> str:
        return "BUSINESS_SETUP"

    def __init__(self):
        self.engine = BusinessCalculationEngine()

    def generate_plan(self, request: CustomPlannerInput) -> CustomPlannerOutput:
        calc_result = self.engine.calculate(request.budget, {})
        
        from app.services.rate_service import rate_service
        threshold = rate_service.get_rate("business", "budget_feasibility_threshold", 200000)
        
        feasibility = FeasibilityData(
            status="PRELIMINARY_FEASIBLE" if request.budget >= threshold else "LOW_BUDGET",
            details={"runway": {"min": 3, "max": 6, "unit": "months"}}
        )
        
        assumptions = [
            "Assumes a small-scale retail, service, or food business.",
            "Working capital is estimated to cover initial 3 months of operational expenses.",
            "Rental deposit assumed to be 6-10 months of rent (standard in major Indian cities)."
        ]
        
        risks = [
            "Unexpected licensing delays can burn working capital.",
            "Initial customer acquisition costs may be higher than estimated."
        ]
        
        recommendations = [
            {"title": "Protect Working Capital", "reason": "Do not spend all cash on interiors; keep cash for the first 6 months of operations."},
            {"title": "Lease instead of Buy", "reason": "Leasing equipment reduces initial capital expenditure."}
        ]
        
        alternatives = [
            {"name": "Option A — Lean Launch", "description": "Start online/cloud kitchen first to avoid rental deposit."},
            {"name": "Option B — Prime Location", "description": "Spend 40% on rent/deposit in a high-footfall area, reduce marketing."}
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
                    "estimated_quantity": "1 Unit/Setup",
                    "cost_estimate": item_budget,
                    "source": "Allocated from total budget."
                })
        else:
            materials = []
            
        return CustomPlannerOutput(
            planner="custom",
            plan_title=request.plan_title,
            domain=self.domain,
            budget=request.budget,
            budget_used=calc_result["working_budget"],
            remaining_budget=calc_result["reserve"],
            ai_notes="Preliminary business setup estimate.",
            feasibility=feasibility,
            cost_breakdown=calc_result["breakdown"],
            materials=materials,
            assumptions=assumptions,
            risks=risks,
            alternative_plans=alternatives,
            recommendations=recommendations,
            items=[] 
        )
