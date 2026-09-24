import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.home import HomePlannerInput, HomePlannerOutput, HomePlannerItem, FeasibilityData
from app.services.recommendation_service import recommendation_service

logger = logging.getLogger(__name__)

class HomeService:
    @staticmethod
    def plan_home_interior(
        data: HomePlannerInput,
        user: User,
        db: Session
    ) -> HomePlannerOutput:
        
        reserve = data.total_budget * 0.05
        working_budget = data.total_budget - reserve
        
        # Breakdown percentages based on room type
        if data.room_type.lower() == "kitchen":
            breakdown = [
                {"category": "Cabinetry & Woodwork", "cost": working_budget * 0.40},
                {"category": "Countertop & Backsplash", "cost": working_budget * 0.20},
                {"category": "Appliances", "cost": working_budget * 0.20},
                {"category": "Plumbing & Sink", "cost": working_budget * 0.10},
                {"category": "Electrical & Lighting", "cost": working_budget * 0.10},
            ]
        elif data.room_type.lower() == "bedroom":
            breakdown = [
                {"category": "Wardrobe & Storage", "cost": working_budget * 0.35},
                {"category": "Bed & Mattress", "cost": working_budget * 0.25},
                {"category": "False Ceiling & Lighting", "cost": working_budget * 0.15},
                {"category": "Wall Paint / Wallpaper", "cost": working_budget * 0.10},
                {"category": "Decor & Furnishings", "cost": working_budget * 0.15},
            ]
        else:
            # Default Living Room or other
            breakdown = [
                {"category": "Sofa & Seating", "cost": working_budget * 0.30},
                {"category": "TV Unit & Woodwork", "cost": working_budget * 0.25},
                {"category": "False Ceiling & Lighting", "cost": working_budget * 0.20},
                {"category": "Paint & Wall Treatment", "cost": working_budget * 0.10},
                {"category": "Decor, Rugs & Furnishings", "cost": working_budget * 0.15},
            ]
            
        assumptions = [
            f"Based on standard regional rates for a mid-range {data.style} {data.room_type}.",
            "Does not include structural civil changes or wall breaking.",
            "Appliances are estimated; exact cost depends on brand choices."
        ]
        
        risks = [
            "Plywood and laminate costs can vary by up to 30% based on brand (e.g. Century vs local).",
            "Hidden electrical rewiring needs can increase lighting budget."
        ]
        
        recommendations = [
            {"title": "Invest in Hardware", "reason": "Spend more on hinges and channels (Hettich/Blum); they determine longevity."},
            {"title": "Optimal Lighting", "reason": "Use a mix of task lighting and ambient lighting instead of one bright center light."}
        ]
        
        alternatives = [
            {"name": "Option A — Premium Finishes", "description": "Use acrylic or PU finish instead of laminates, but reduce the scope of false ceiling."},
            {"name": "Option B — Minimalist Lean", "description": "Skip the TV unit woodwork; use a minimal floating shelf to save 20% budget."}
        ]
        
        materials = []
        for req, qty in data.quantities.items():
            cost_per_item = (working_budget * 0.10) # rough heuristic
            materials.append({
                "name": req,
                "estimated_quantity": f"{qty} units",
                "cost_estimate": cost_per_item * qty,
                "source": "Estimated standard rate"
            })
            
        from app.services.rate_service import rate_service
        threshold = rate_service.get_rate("renovation", "budget_feasibility_threshold", 50000)
        premium = rate_service.get_rate("renovation", "premium_threshold", 300000)
        
        feasibility = FeasibilityData(
            status="PRELIMINARY_FEASIBLE" if data.total_budget >= threshold else "LOW_BUDGET",
            details={"estimatedQuality": "Premium" if data.total_budget > premium else "Standard"}
        )

        plan_output = HomePlannerOutput(
            planner="home",
            domain="RENOVATION",
            budget=data.total_budget,
            budget_used=working_budget,
            remaining_budget=reserve,
            ai_notes=f"Generated an interior design plan for {data.room_type} with {data.style} aesthetics.",
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

        # Save to database
        input_dict = data.model_dump()
        rec_record = recommendation_service.save_recommendation(
            db=db,
            user_id=user.id,
            planner_type="home",
            budget=data.total_budget,
            input_data=input_dict,
            ai_result=plan_output.model_dump(),
            is_mock_ai=False
        )

        plan_output.recommendation_id = rec_record.id
        return plan_output

home_service = HomeService()
