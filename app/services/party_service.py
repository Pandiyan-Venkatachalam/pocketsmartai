import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.party import PartyPlannerInput, PartyPlannerOutput, PartyPlannerItem, FeasibilityData
from app.services.recommendation_service import recommendation_service

logger = logging.getLogger(__name__)

class PartyService:
    @staticmethod
    def plan_party(
        data: PartyPlannerInput,
        user: User,
        db: Session
    ) -> PartyPlannerOutput:
        
        reserve = data.budget * 0.05
        working_budget = data.budget - reserve
        
        breakdown = [
            {"category": "Venue / Location Setup", "cost": working_budget * 0.25},
            {"category": "Food & Catering", "cost": working_budget * 0.45},
            {"category": "Decorations", "cost": working_budget * 0.15},
            {"category": "Entertainment & Music", "cost": working_budget * 0.10},
            {"category": "Miscellaneous", "cost": working_budget * 0.05},
        ]
        
        avg_cost_per_guest = working_budget * 0.45 / data.guest_count if data.guest_count > 0 else 0
        
        assumptions = [
            f"Based on {data.guest_count} guests for a {data.event_type}.",
            f"Assumes {data.food_preferences} style catering in {data.location}.",
            "Does not include expensive alcohol or premium return gifts."
        ]
        
        risks = [
            "Guest count exceeding estimates heavily inflates catering costs.",
            "Weather disruptions if the venue is outdoors."
        ]
        
        recommendations = [
            {"title": "Buffer Food", "reason": "Always arrange food for 10% more guests than confirmed."},
            {"title": "Decor Priorities", "reason": "Focus decoration on the entrance and the main stage/cake table."}
        ]
        
        alternatives = [
            {"name": "Option A — Premium Catering", "description": "Reduce guest count by 20% and upgrade to a 5-course gourmet menu."},
            {"name": "Option B — Casual Vibe", "description": "Switch to buffet style with minimal seating to save on venue rental."}
        ]
        
        materials = [
            {
                "name": "Catering Plates",
                "estimated_quantity": f"{int(data.guest_count * 1.1)} units",
                "cost_estimate": working_budget * 0.45,
                "source": "Calculated based on guest count"
            },
            {
                "name": "Seating / Chairs",
                "estimated_quantity": f"{data.guest_count} units",
                "cost_estimate": working_budget * 0.10,
                "source": "Standard event rental"
            }
        ]
            
        from app.services.rate_service import rate_service
        threshold = rate_service.get_rate("events", "party_budget_feasibility_threshold_pp", 500)
        
        feasibility = FeasibilityData(
            status="PRELIMINARY_FEASIBLE" if avg_cost_per_guest >= threshold else "LOW_BUDGET",
            details={"estimatedCostPerGuestForFood": {"min": int(avg_cost_per_guest * 0.8), "max": int(avg_cost_per_guest * 1.2), "unit": "INR"}}
        )

        plan_output = PartyPlannerOutput(
            planner="party",
            domain="EVENT",
            budget=data.budget,
            budget_used=working_budget,
            remaining_budget=reserve,
            ai_notes=f"Generated an event plan for {data.event_type} with {data.guest_count} guests.",
            is_mock_ai=False,
            feasibility=feasibility,
            cost_breakdown=breakdown,
            materials=materials,
            assumptions=assumptions,
            risks=risks,
            recommendations=recommendations,
            alternative_plans=alternatives,
            items=[]
        )

        input_dict = data.model_dump()
        rec_record = recommendation_service.save_recommendation(
            db=db,
            user_id=user.id,
            planner_type="party",
            budget=data.budget,
            input_data=input_dict,
            ai_result=plan_output.model_dump(),
            is_mock_ai=False
        )

        plan_output.recommendation_id = rec_record.id
        return plan_output

party_service = PartyService()
