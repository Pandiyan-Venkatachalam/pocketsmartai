import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.jewelry import JewelryPlannerInput, JewelryPlannerOutput, JewelryPlannerItem
from app.services.product_service import product_service
from app.services.gemini_service import gemini_service
from app.services.recommendation_service import recommendation_service

logger = logging.getLogger(__name__)

class JewelryService:
    @staticmethod
    def plan_jewelry(
        data: JewelryPlannerInput,
        user: User,
        db: Session,
        image_bytes: Optional[bytes] = None,
        image_mime: str = "image/jpeg"
    ) -> JewelryPlannerOutput:
        """
        Executes the Jewelry Budget recommendation pipeline:
        1. Fetch candidates from verified jewelry catalog
        2. Call Gemini AI multimodal (with optional outfit image) or fallback
        3. Enforce budget invariant (sum <= budget)
        4. Save to DB
        5. Return response
        """
        has_image = bool(image_bytes and len(image_bytes) > 0)

        candidates = product_service.get_jewelry_candidates(
            jewelry_types=data.jewelry_type,
            preferred_style=data.preferred_style,
            max_budget=data.budget
        )

        prompt = gemini_service.build_jewelry_prompt(
            budget=data.budget,
            occasion=data.occasion,
            preferred_style=data.preferred_style,
            jewelry_types=data.jewelry_type,
            color_preference=data.color_preference or "Silver / Gold",
            has_image=has_image,
            candidates=candidates
        )

        result, is_mock = gemini_service.generate_recommendations(
            prompt=prompt,
            image_bytes=image_bytes if has_image else None,
            image_mime=image_mime
        )

        if not result or "items" not in result or not result["items"]:
            logger.info("Using intelligent heuristic fallback for Jewelry Planner.")
            result = gemini_service.generate_fallback_jewelry(
                budget=data.budget,
                occasion=data.occasion,
                preferred_style=data.preferred_style,
                jewelry_types=data.jewelry_type,
                color_preference=data.color_preference or "Silver / Gold",
                has_image=has_image,
                candidates=candidates
            )
            is_mock = True

        result = gemini_service.enforce_budget_limits(result, data.budget)

        input_dict = data.model_dump()
        input_dict["has_image_uploaded"] = has_image

        rec_record = recommendation_service.save_recommendation(
            db=db,
            user_id=user.id,
            planner_type="jewelry",
            budget=data.budget,
            input_data=input_dict,
            ai_result=result,
            is_mock_ai=is_mock
        )

        items_out = [
            JewelryPlannerItem(
                name=i.get("name", "Jewelry Piece"),
                category=i.get("category", "Jewelry"),
                estimated_price=float(i.get("estimated_price", 0)),
                platform=i.get("platform", "Amazon"),
                product_url=i.get("product_url", "#"),
                reason=i.get("reason", "Curated for outfit and occasion harmony."),
                image_url=i.get("image_url")
            )
            for i in result.get("items", [])
        ]

        return JewelryPlannerOutput(
            planner="jewelry",
            budget=data.budget,
            budget_used=result.get("budget_used", 0.0),
            remaining_budget=result.get("remaining_budget", 0.0),
            ai_notes=result.get("ai_notes"),
            is_mock_ai=is_mock,
            items=items_out,
            recommendation_id=rec_record.id
        )

jewelry_service = JewelryService()
