from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field

class HomePlannerInput(BaseModel):
    total_budget: float = Field(..., gt=0, description="Total budget in INR")
    room_type: str = Field(..., min_length=2, description="e.g. Living Room, Bedroom, Dining Room, Kitchen")
    style: str = Field(..., min_length=2, description="e.g. Modern, Minimalist, Scandinavian, Traditional")
    required_items: List[str] = Field(default_factory=list, description="List of essential items needed")
    quantities: Dict[str, int] = Field(default_factory=dict, description="Item quantities, e.g. {'Sofa': 1, 'Lights': 2}")
    additional_preferences: Optional[str] = Field(default="", description="Specific notes, colors, or materials")

class HomePlannerItem(BaseModel):
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

class HomePlannerOutput(BaseModel):
    planner: str = "home"
    domain: str = "RENOVATION"
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
    
    items: List[HomePlannerItem] = Field(default_factory=list)
    recommendation_id: Optional[int] = None
