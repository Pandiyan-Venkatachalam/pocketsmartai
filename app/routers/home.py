from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.home import HomePlannerInput, HomePlannerOutput
from app.services.home_service import home_service

router = APIRouter(prefix="", tags=["Home Interior Planner"])

@router.post("/api/planners/home", response_model=HomePlannerOutput)
@router.post("/generate-home", response_model=HomePlannerOutput)
def plan_home(
    data: HomePlannerInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates budget-aware home interior and furniture recommendations.
    Validates budget, checks available products, queries Gemini (or mock AI fallback),
    guarantees budget limits, and saves recommendations to user history.
    """
    if data.total_budget <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget must be greater than zero."
        )

    try:
        return home_service.plan_home_interior(data=data, user=current_user, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to generate home recommendations: {str(e)}"
        )
