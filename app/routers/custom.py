from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.custom_planner import CustomPlannerInput, CustomPlannerOutput
from app.services.custom_service import custom_service

router = APIRouter(prefix="", tags=["Universal Custom Budget Planner"])

@router.post("/api/planners/custom", response_model=CustomPlannerOutput)
@router.post("/generate-custom", response_model=CustomPlannerOutput)
def plan_custom(
    data: CustomPlannerInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a customized budget and recommendation plan for ANY user wish or domain:
    Travel, Tech Workstations, Fitness/Gyms, Gaming, Education, Hobbies, etc.
    """
    if data.budget <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget must be greater than zero."
        )

    try:
        return custom_service.plan_custom(data=data, user=current_user, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to generate custom recommendations: {str(e)}"
        )
