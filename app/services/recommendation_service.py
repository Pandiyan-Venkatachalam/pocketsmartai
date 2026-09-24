import json
import logging
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import requests
import cloudinary
import cloudinary.uploader

from app.core.config import settings
from app.models.recommendation import Recommendation, RecommendationItem
from app.models.user import User
from app.schemas.recommendation import HistoryItemOut, DashboardStats

logger = logging.getLogger(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME or "dqr1zbyeb",
    api_key=settings.CLOUDINARY_API_KEY or "273174792865529",
    api_secret=settings.CLOUDINARY_API_SECRET or "jF_wQ3z_92GCh6kCk_YxmN1G4r0",
    secure=True
)

CURATED_PHOTOS = [
    (["cement", "concrete"], "https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=600"),
    (["steel", "rebar", "iron"], "https://images.unsplash.com/photo-1504307651254-35680f356dfd?w=600"),
    (["brick", "block", "masonry"], "https://images.unsplash.com/photo-1590069261209-f8e9b8642343?w=600"),
    (["sand", "aggregate"], "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=600"),
    (["sofa", "couch", "living"], "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600"),
    (["fan", "ceiling fan"], "https://images.unsplash.com/photo-1598928506311-c55ded91a20c?w=600"),
    (["light", "lamp", "spotlight"], "https://images.unsplash.com/photo-1507473885765-e6ed057f782c?w=600"),
    (["dining", "dining table"], "https://images.unsplash.com/photo-1577140917170-285929fb55b7?w=600"),
    (["table", "desk"], "https://images.unsplash.com/photo-1533090161767-e6ffed986c88?w=600"),
    (["chair", "seating"], "https://images.unsplash.com/photo-1567538096630-e0c55bd6374c?w=600"),
    (["tv unit", "tv", "entertainment"], "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600"),
    (["wardrobe", "closet"], "https://images.unsplash.com/photo-1558997519-83ea9252edf8?w=600"),
    (["bed", "mattress"], "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=600"),
    (["kitchen", "cabinet"], "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=600"),
    (["paint", "primer", "color"], "https://images.unsplash.com/photo-1562259949-e8e7689d7828?w=600"),
    (["plate", "catering plates", "dinnerware"], "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600"),
    (["catering", "food", "dining"], "https://images.unsplash.com/photo-1555244162-803834f70033?w=600"),
    (["hotel", "accommodation", "resort"], "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600"),
    (["flight", "flight / transport", "airline"], "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=600"),
    (["transport", "tour", "travel", "misc"], "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=600"),
    (["photo", "video", "camera"], "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=600"),
    (["music", "dj", "sound", "entertainment"], "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=600"),
    (["floral", "decor", "flower"], "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?w=600"),
    (["venue", "hall"], "https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=600"),
    (["attire", "makeup", "dress"], "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600"),
    (["invitation", "cards", "favor"], "https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=600"),
    (["jewelry", "jewel", "necklace"], "https://images.unsplash.com/photo-1515562141207-7a88fb7ce338?w=600"),
    (["gold", "bangle", "bracelet"], "https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?w=600"),
    (["ring", "diamond"], "https://images.unsplash.com/photo-1605100804763-247f67b3557e?w=600"),
    (["charger", "ev"], "https://images.unsplash.com/photo-1563720223185-11003d516935?w=600"),
    (["espresso", "coffee"], "https://images.unsplash.com/photo-1517668808822-9ebb02f2a0e6?w=600"),
]

def generate_item_image(item_name: str, category: str = "") -> Optional[str]:
    """Uploads a product photo to Cloudinary and returns the secure URL."""
    if not item_name:
        return None
    try:
        clean = item_name.strip().lower()
        src_url = None
        for keywords, url in CURATED_PHOTOS:
            for kw in keywords:
                if kw in clean:
                    src_url = url
                    break
            if src_url:
                break
        
        if not src_url:
            safe = requests.utils.quote(f"product photography of {item_name}, clean background, commercial high quality")
            src_url = f"https://image.pollinations.ai/prompt/{safe}?width=400&height=400&nologo=true"

        res = cloudinary.uploader.upload(src_url, folder="pocketsmart_items")
        url = res.get("secure_url")
        if url:
            logger.info(f"Generated and uploaded image to Cloudinary for '{item_name}': {url}")
            return url
    except Exception as e:
        logger.error(f"Error generating/uploading image for '{item_name}': {e}")
        try:
            return f"https://image.pollinations.ai/prompt/{requests.utils.quote(item_name)}?width=400&height=400&nologo=true"
        except Exception:
            pass
    return None

def is_valid_image_url(url: Optional[str]) -> bool:
    if not url:
        return False
    url_str = str(url).strip()
    if url_str.startswith("<") or not (url_str.startswith("http://") or url_str.startswith("https://")):
        return False
    return True

class RecommendationService:
    """
    Central persistence and analytics service for user recommendations and history.
    """

    @staticmethod
    def save_recommendation(
        db: Session,
        user_id: int,
        planner_type: str,
        budget: float,
        input_data: Dict[str, Any],
        ai_result: Dict[str, Any],
        is_mock_ai: bool
    ) -> Recommendation:
        """Persists a generated recommendation and all its recommended items to the database."""
        total_estimated = float(ai_result.get("budget_used", 0.0))
        remaining = float(ai_result.get("remaining_budget", max(0.0, budget - total_estimated)))
        ai_notes = ai_result.get("ai_notes", "")

        rec = Recommendation(
            user_id=user_id,
            planner_type=planner_type,
            budget=budget,
            total_estimated_cost=total_estimated,
            remaining_budget=remaining,
            input_data=json.dumps(input_data),
            plan_data=json.dumps(ai_result),
            ai_notes=ai_notes,
            is_mock_ai=is_mock_ai
        )
        db.add(rec)
        db.flush()  # Populates rec.id

        # Insert items
        items = ai_result.get("items", [])
        if not items and ai_result.get("materials"):
            items = [
                {
                    "name": m.get("name", "Material / Service"),
                    "category": m.get("category", "Materials & Services"),
                    "estimated_price": float(m.get("cost_estimate", 0.0)),
                    "platform": m.get("source", "Standard Market Rate"),
                    "product_url": "#",
                    "reason": f"Quantity: {m.get('estimated_quantity', '1 unit')}",
                    "image_url": m.get("image_url")
                }
                for m in ai_result.get("materials", [])
            ]
        elif not items and ai_result.get("cost_breakdown"):
            items = [
                {
                    "name": cb.get("category", "Cost Allocation"),
                    "category": cb.get("category", "Breakdown"),
                    "estimated_price": float(cb.get("cost", 0.0)),
                    "platform": "Budget Allocation",
                    "product_url": "#",
                    "reason": f"{cb.get('percentage', 0)}% of total working budget",
                    "image_url": cb.get("image_url")
                }
                for cb in ai_result.get("cost_breakdown", [])
            ]

        for item in items:
            img = item.get("image_url")
            if not is_valid_image_url(img):
                img = generate_item_image(item.get("name", "Product"), item.get("category", ""))

            rec_item = RecommendationItem(
                recommendation_id=rec.id,
                name=item.get("name", "Recommended Item"),
                category=item.get("category", "General"),
                estimated_price=float(item.get("estimated_price", 0.0)),
                platform=item.get("platform", "Online"),
                product_url=item.get("product_url", "#"),
                reason=item.get("reason", "Matches budget and requirements."),
                image_url=img
            )
            db.add(rec_item)

        db.commit()
        db.refresh(rec)
        logger.info(f"Saved recommendation {rec.id} for user {user_id} ({planner_type}) with {len(items)} items")
        return rec

    @staticmethod
    def get_user_history(
        db: Session,
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> List[HistoryItemOut]:
        """Retrieves past recommendation history for a specific user."""
        records = (
            db.query(Recommendation)
            .filter(Recommendation.user_id == user_id)
            .order_by(Recommendation.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        history_items = []
        for r in records:
            # Parse input summary
            summary = ""
            try:
                inputs = json.loads(r.input_data)
                if r.planner_type == "home":
                    summary = f"{inputs.get('room_type', 'Room')} • {inputs.get('style', 'Modern')}"
                elif r.planner_type == "party":
                    summary = f"{inputs.get('event_type', 'Event')} • {inputs.get('guest_count', 0)} Guests"
                elif r.planner_type == "jewelry":
                    summary = f"{inputs.get('occasion', 'Occasion')} • {inputs.get('preferred_style', 'Style')}"
                elif r.planner_type == "custom":
                    title = inputs.get("plan_title", "Custom Plan")
                    cat = inputs.get("effective_category", inputs.get("category", "Custom"))
                    summary = f"{title} • {cat}"
            except Exception:
                summary = f"{r.planner_type.capitalize()} Plan"

            # Compute items count accurately with fallbacks
            count = len(r.items) if r.items else 0
            if count == 0 and r.plan_data:
                try:
                    plan = json.loads(r.plan_data)
                    if plan.get("items"):
                        count = len(plan["items"])
                    elif plan.get("materials"):
                        count = len(plan["materials"])
                    elif plan.get("cost_breakdown"):
                        count = len(plan["cost_breakdown"])
                except Exception:
                    pass

            history_items.append(
                HistoryItemOut(
                    id=r.id,
                    planner_type=r.planner_type,
                    budget=r.budget,
                    total_estimated_cost=r.total_estimated_cost,
                    remaining_budget=r.remaining_budget,
                    items_count=count,
                    created_at=r.created_at,
                    summary=summary,
                    is_mock_ai=r.is_mock_ai
                )
            )

        return history_items

    @staticmethod
    def get_recommendation_by_id(
        db: Session,
        rec_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Recommendation]:
        """Gets a recommendation by ID, optionally verifying ownership. Auto-fills missing item images."""
        query = db.query(Recommendation).filter(Recommendation.id == rec_id)
        if user_id is not None:
            query = query.filter(Recommendation.user_id == user_id)
        rec = query.first()
        if not rec:
            return None

        # Auto-heal any items missing image_url
        updated = False
        for item in rec.items:
            if not is_valid_image_url(item.image_url):
                item.image_url = generate_item_image(item.name, item.category)
                updated = True
        if updated:
            db.commit()
            db.refresh(rec)

        return rec

    @staticmethod
    def delete_recommendation(db: Session, rec_id: int, user_id: int) -> bool:
        """Deletes a recommendation by ID."""
        rec = db.query(Recommendation).filter(
            Recommendation.id == rec_id,
            Recommendation.user_id == user_id
        ).first()
        if not rec:
            return False
        db.delete(rec)
        db.commit()
        return True

    @staticmethod
    def get_dashboard_stats(db: Session, user: User) -> DashboardStats:
        """Computes high-level user statistics for the dashboard."""
        recs = (
            db.query(Recommendation)
            .filter(Recommendation.user_id == user.id)
            .order_by(Recommendation.created_at.desc())
            .all()
        )

        total_count = len(recs)
        total_budget = sum(r.budget for r in recs)

        planner_breakdown = {"home": 0, "party": 0, "jewelry": 0, "custom": 0}
        for r in recs:
            pt = r.planner_type.lower()
            if pt in planner_breakdown:
                planner_breakdown[pt] += 1
            else:
                planner_breakdown[pt] = 1

        recent_history = RecommendationService.get_user_history(db, user.id, limit=5)

        return DashboardStats(
            user_name=user.name,
            total_recommendations=total_count,
            total_budget_planned=round(total_budget, 2),
            planner_breakdown=planner_breakdown,
            recent_recommendations=recent_history
        )

recommendation_service = RecommendationService()
