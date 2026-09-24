from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class PartyPlannerInput(BaseModel):
    budget: float = Field(..., gt=0, description="Total budget in INR")
    event_type: str = Field(..., min_length=2, description="e.g. Birthday Party, Anniversary, Corporate Mixer")
    guest_count: int = Field(..., gt=0, le=1000, description="Estimated number of guests")
    location: Optional[str] = Field(default="City Center", description="Preferred neighborhood or city")
    event_date: Optional[str] = Field(default="", description="Target date or weekend")
    food_preferences: Optional[str] = Field(default="", description="Catering style, e.g. BBQ, 3-course, Hi-tea")
    decoration_preferences: Optional[str] = Field(default="", description="Theme, e.g. Neon, Floral, Minimalist")
    entertainment_preferences: Optional[str] = Field(default="", description="DJ, Live Acoustic, Photo Booth, Games")

class PartyPlannerItem(BaseModel):
    name: str
    category: str
    estimated_price: float
    platform: str
    product_url: str
    reason: str
    image_url: Optional[str] = None

class FeasibilityData(BaseModel):
    status: str
    details: Dict[str, Any] = Field(default_factory=dict)

class PartyPlannerOutput(BaseModel):
    planner: str = "party"
    domain: str = "EVENT"
    budget: float
    budget_used: float
    remaining_budget: float
    ai_notes: Optional[str] = None
    is_mock_ai: bool = False
    
    feasibility: Optional[FeasibilityData] = None
    cost_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    materials: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    recommendations: List[Dict[str, str]] = Field(default_factory=list)
    alternative_plans: List[Dict[str, Any]] = Field(default_factory=list)
    
    items: List[PartyPlannerItem] = Field(default_factory=list)
    recommendation_id: Optional[int] = None
