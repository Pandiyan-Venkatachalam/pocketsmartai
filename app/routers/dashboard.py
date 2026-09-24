from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.recommendation import DashboardStats
from app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="", tags=["Dashboard"])

@router.get("/api/dashboard", response_model=DashboardStats)
def get_dashboard_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns analytics, recent recommendations, and statistics for the user dashboard."""
    return recommendation_service.get_dashboard_stats(db=db, user=current_user)

@router.get("/session-data")
def get_session_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compatibility endpoint for user metrics."""
    return recommendation_service.get_dashboard_stats(db=db, user=current_user)
