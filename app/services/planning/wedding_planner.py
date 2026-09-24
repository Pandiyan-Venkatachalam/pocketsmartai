from app.services.planning.interfaces import IPlanner, ICalculationEngine
from app.schemas.custom_planner import CustomPlannerOutput, CustomPlannerInput, FeasibilityData

class WeddingCalculationEngine(ICalculationEngine):
    def calculate(self, budget: float, requirements: dict) -> dict:
        reserve = budget * 0.05
        working_budget = budget - reserve
        
        breakdown = [
            {"category": "Venue & Catering", "cost": working_budget * 0.45},
            {"category": "Decorations & Floral", "cost": working_budget * 0.15},
            {"category": "Photography & Video", "cost": working_budget * 0.12},
            {"category": "Attire & Makeup", "cost": working_budget * 0.12},
            {"category": "Invitations & Favors", "cost": working_budget * 0.05},
            {"category": "Entertainment & Music", "cost": working_budget * 0.06},
            {"category": "Miscellaneous", "cost": working_budget * 0.05},
        ]
        
        # Heuristic for guests based on budget
        # Assume ~₹2500 per guest for venue/food
        from app.services.rate_service import rate_service
        avg_cost_per_guest = rate_service.get_rate("events", "wedding_avg_cost_per_guest", 2500)
        estimated_guests = (working_budget * 0.45) / avg_cost_per_guest
        
        return {
            "reserve": reserve,
            "working_budget": working_budget,
            "breakdown": breakdown,
            "estimated_guests": int(max(10, estimated_guests))
        }

class WeddingPlanner(IPlanner):
    @property
    def domain(self) -> str:
        return "WEDDING"

    def __init__(self):
        self.engine = WeddingCalculationEngine()

    def generate_plan(self, request: CustomPlannerInput) -> CustomPlannerOutput:
        calc_result = self.engine.calculate(request.budget, {})
        
        from app.services.rate_service import rate_service
        threshold = rate_service.get_rate("events", "wedding_budget_feasibility_threshold", 100000)
        
        feasibility = FeasibilityData(
            status="PRELIMINARY_FEASIBLE" if request.budget >= threshold else "LOW_BUDGET",
            details={"estimatedGuests": {"min": int(calc_result["estimated_guests"] * 0.8), "max": int(calc_result["estimated_guests"] * 1.2), "unit": "guests"}}
        )
        
        assumptions = [
            "Based on standard regional venue and catering costs.",
            "Photography package covers 1-2 days of standard coverage.",
            "Gold/Jewelry is EXCLUDED from this event execution budget."
        ]
        
        risks = [
            "Guest count exceeding estimates heavily inflates catering costs.",
            "Premium venues require booking 6-12 months in advance."
        ]
        
        recommendations = [
            {"title": "Lock Venue Early", "reason": "Securing the venue defines the date and consumes 45% of budget."},
            {"title": "Trim the Guest List", "reason": "Every 50 guests removed saves ~₹1.25 Lakhs."}
        ]
        
        alternatives = [
            {"name": "Option A — Intimate & Premium", "description": "Invite 50 guests but use premium 5-star venue."},
            {"name": "Option B — Large & Traditional", "description": "Invite 500+ guests at a standard community hall."}
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
                    "estimated_quantity": "1 Package/Unit",
                    "cost_estimate": item_budget,
                    "source": "Evenly allocated from requested items."
                })
        else:
            materials = [
                {"name": "Premium Venue Booking", "estimated_quantity": "1"
                , "cost_estimate": calc_result["working_budget"] * 0.25, "source": "Standard Allocation"},
                {"name": "Catering Service", "estimated_quantity": f"~{int(calc_result['estimated_guests'])} guests", "cost_estimate": calc_result["working_budget"] * 0.20, "source": "Standard Allocation"},
                {"name": "Floral & Decor Setup", "estimated_quantity": "1 Package", "cost_estimate": calc_result["working_budget"] * 0.15, "source": "Standard Allocation"},
            ]
            
        return CustomPlannerOutput(
            planner="custom",
            plan_title=request.plan_title,
            domain=self.domain,
            budget=request.budget,
            budget_used=calc_result["working_budget"],
            remaining_budget=calc_result["reserve"],
            ai_notes="Preliminary wedding event estimate.",
            feasibility=feasibility,
            cost_breakdown=calc_result["breakdown"],
            materials=materials,
            assumptions=assumptions,
            risks=risks,
            alternative_plans=alternatives,
            recommendations=recommendations,
            items=[] 
        )
