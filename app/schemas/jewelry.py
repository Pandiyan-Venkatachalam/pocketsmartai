from typing import List, Optional
from pydantic import BaseModel, Field

class JewelryPlannerInput(BaseModel):
    budget: float = Field(..., gt=0, description="Total budget in INR")
    occasion: str = Field(..., min_length=2, description="e.g. Wedding, Cocktail Party, Festive, Office")
    preferred_style: str = Field(..., min_length=2, description="e.g. Minimalist, Ethnic, Royal Traditional, Contemporary")
    jewelry_type: List[str] = Field(default_factory=list, description="Specific accessories desired (e.g. Earrings, Necklace)")
    color_preference: Optional[str] = Field(default="Gold / Silver", description="Metal or stone color tone")

class JewelryPlannerItem(BaseModel):
    name: str
    category: str
    estimated_price: float
    platform: str
    product_url: str
    reason: str
    image_url: Optional[str] = None

class JewelryPlannerOutput(BaseModel):
    planner: str = "jewelry"
    budget: float
    budget_used: float
    remaining_budget: float
    ai_notes: Optional[str] = None
    is_mock_ai: bool = False
    items: List[JewelryPlannerItem]
    recommendation_id: Optional[int] = None
