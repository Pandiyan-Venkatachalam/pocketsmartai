import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.recommendation import HistoryItemOut, RecommendationOut, RecommendationItemOut
from app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="", tags=["Recommendation History"])

@router.get("/api/history", response_model=List[HistoryItemOut])
def get_user_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves list of past recommendations created by the user."""
    return recommendation_service.get_user_history(
        db=db,
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )

@router.get("/api/history/{rec_id}", response_model=RecommendationOut)
@router.get("/api/recommendations/{rec_id}", response_model=RecommendationOut)
def get_recommendation_details(
    rec_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves a single recommendation by ID, including its full item cards."""
    rec = recommendation_service.get_recommendation_by_id(
        db=db,
        rec_id=rec_id,
        user_id=current_user.id
    )
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found or unauthorized access."
        )

    try:
        parsed_inputs = json.loads(rec.input_data)
    except Exception:
        parsed_inputs = {}

    items_out = [
        RecommendationItemOut(
            id=item.id,
            recommendation_id=item.recommendation_id,
            name=item.name,
            category=item.category,
            estimated_price=item.estimated_price,
            platform=item.platform,
            product_url=item.product_url,
            reason=item.reason,
            image_url=item.image_url
        )
        for item in rec.items
    ]

    return RecommendationOut(
        id=rec.id,
        user_id=rec.user_id,
        planner_type=rec.planner_type,
        budget=rec.budget,
        total_estimated_cost=rec.total_estimated_cost,
        remaining_budget=rec.remaining_budget,
        input_data=parsed_inputs,
        ai_notes=rec.ai_notes,
        is_mock_ai=rec.is_mock_ai,
        created_at=rec.created_at,
        items=items_out
    )

@router.get("/recommendations-details")
def get_recommendation_details_query(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compatibility query endpoint: /recommendations-details?id=123"""
    return get_recommendation_details(rec_id=id, current_user=current_user, db=db)

@router.delete("/api/history/{rec_id}")
def delete_recommendation_item(
    rec_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes a recommendation from user history."""
    deleted = recommendation_service.delete_recommendation(
        db=db,
        rec_id=rec_id,
        user_id=current_user.id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recommendation not found."
        )
    return {"message": "Recommendation deleted successfully", "id": rec_id}
