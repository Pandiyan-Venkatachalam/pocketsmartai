from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.jewelry import JewelryPlannerInput, JewelryPlannerOutput
from app.services.jewelry_service import jewelry_service

router = APIRouter(prefix="", tags=["Jewelry Budget Planner"])

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit

@router.post("/api/planners/jewelry", response_model=JewelryPlannerOutput)
@router.post("/generate-jewelry", response_model=JewelryPlannerOutput)
async def plan_jewelry_multipart(
    budget: float = Form(...),
    occasion: str = Form(...),
    preferred_style: str = Form(...),
    jewelry_types: Optional[str] = Form(None),  # Comma-separated
    color_preference: Optional[str] = Form("Gold / Silver"),
    outfit_image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accepts multipart/form-data for Jewelry Planner, including optional outfit image for Gemini Vision analysis.
    """
    if budget <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget must be greater than zero."
        )

    # Validate image if provided
    image_bytes = None
    image_mime = "image/jpeg"
    if outfit_image and outfit_image.filename:
        # Check mime type
        valid_mimes = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
        if outfit_image.content_type not in valid_mimes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image format ({outfit_image.content_type}). Supported formats: JPEG, PNG, WEBP."
            )

        content = await outfit_image.read()
        if len(content) > MAX_IMAGE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image file too large. Maximum allowed size is 5MB."
            )
        image_bytes = content
        image_mime = outfit_image.content_type

    parsed_types = [t.strip() for t in jewelry_types.split(",")] if jewelry_types else []

    data = JewelryPlannerInput(
        budget=budget,
        occasion=occasion,
        preferred_style=preferred_style,
        jewelry_type=parsed_types,
        color_preference=color_preference or "Gold / Silver"
    )

    try:
        return jewelry_service.plan_jewelry(
            data=data,
            user=current_user,
            db=db,
            image_bytes=image_bytes,
            image_mime=image_mime
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to generate jewelry recommendations: {str(e)}"
        )

@router.post("/api/planners/jewelry/json", response_model=JewelryPlannerOutput)
def plan_jewelry_json(
    data: JewelryPlannerInput,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Direct JSON endpoint for programmatic / API-only integration."""
    if data.budget <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budget must be greater than zero."
        )
    try:
        return jewelry_service.plan_jewelry(
            data=data,
            user=current_user,
            db=db,
            image_bytes=None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unable to generate jewelry recommendations: {str(e)}"
        )
