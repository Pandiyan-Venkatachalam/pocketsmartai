from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.party import PartyPlannerInput, PartyPlannerOutput
from app.services.party_service import party_service

router = APIRouter(prefix="", tags=["Party Budget Planner"])

@router.post("/api/planners/party", response_model=PartyPlannerOutput)
@router.post("/generate-party", response_model=PartyPlannerOutput)
def plan_party(
    data: PartyPlannerInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates budget-aware party and event recommendations.
    Splits budget across Catering, Venue, Decor, and Entertainment.
    """
    if data.budget <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget must be greater than zero."
        )
    if data.guest_count <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guest count must be at least 1."
        )

    try:
        return party_service.plan_party(data=data, user=current_user, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to generate party recommendations: {str(e)}"
        )
