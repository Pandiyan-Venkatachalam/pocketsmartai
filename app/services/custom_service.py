import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.custom_planner import CustomPlannerInput, CustomPlannerOutput, CustomPlannerItem
from app.services.gemini_service import gemini_service
from app.services.recommendation_service import recommendation_service
from app.services.planning.domain_detector import domain_detector
from app.services.planning.planner_factory import planner_factory

logger = logging.getLogger(__name__)

class CustomService:
    @staticmethod
    def plan_custom(
        data: CustomPlannerInput,
        user: User,
        db: Session
    ) -> CustomPlannerOutput:
        # Determine effective category
        effective_category = data.custom_category.strip() if (data.category.lower() == "custom" and data.custom_category) else data.category
        
        # 1. Intent / Domain Detection
        domain = domain_detector.detect_domain(data)
        logger.info(f"Detected domain for custom plan: {domain}")
        
        planner = planner_factory.get_planner(domain)
        
        if planner:
            # 2. Use domain-specific planner for complex planning
            logger.info(f"Using domain-specific planner: {planner.__class__.__name__}")
            plan_output = planner.generate_plan(data)
            is_mock = False # Domain planners are deterministic right now
            result = plan_output.model_dump()
            
            # Ensure it has basic format expected by recommendation_service
            # the legacy system expects result["budget_used"], etc.
        else:
            # 3. Fallback to generic shopping/product AI model
            logger.info("Using generic e-commerce/AI planner.")
            prompt = gemini_service.build_custom_prompt(
                budget=data.budget,
                plan_title=data.plan_title,
                category=effective_category,
                target_items=data.target_items,
                preferences=data.preferences or ""
            )

            result, is_mock = gemini_service.generate_recommendations(prompt)
            if not result or "items" not in result or not result["items"]:
                result = gemini_service.generate_fallback_custom(
                    budget=data.budget,
                    plan_title=data.plan_title,
                    category=effective_category,
                    target_items=data.target_items,
                    preferences=data.preferences or ""
                )
                is_mock = True
            
            result = gemini_service.enforce_budget_limits(result, data.budget)
            
            items_out = [
                CustomPlannerItem(
                    name=i.get("name", "Product/Service"),
                    category=i.get("category", effective_category),
                    estimated_price=float(i.get("estimated_price", 0)),
                    platform=i.get("platform", "Online"),
                    product_url=i.get("product_url", "#"),
                    reason=i.get("reason", "Curated for budget optimization."),
                    image_url=i.get("image_url")
                )
                for i in result.get("items", [])
            ]
            
            plan_output = CustomPlannerOutput(
                planner="custom",
                plan_title=data.plan_title,
                domain="GENERAL",
                budget=data.budget,
                budget_used=result.get("budget_used", 0.0),
                remaining_budget=result.get("remaining_budget", 0.0),
                ai_notes=result.get("ai_notes"),
                is_mock_ai=is_mock,
                items=items_out
            )

        # 4. Save to database
        input_dict = data.model_dump()
        input_dict["effective_category"] = effective_category

        rec_record = recommendation_service.save_recommendation(
            db=db,
            user_id=user.id,
            planner_type="custom",
            budget=data.budget,
            input_data=input_dict,
            ai_result=result,
            is_mock_ai=is_mock
        )

        plan_output.recommendation_id = rec_record.id
        return plan_output

custom_service = CustomService()
