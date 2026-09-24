from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class CustomPlannerInput(BaseModel):
    budget: float = Field(..., gt=0, description="Total budget in INR")
    plan_title: str = Field(..., min_length=2, description="e.g. Ultimate Gaming Setup, Goa Beach Vacation, Home Gym")
    category: str = Field(..., min_length=2, description="Category preset or Custom")
    custom_category: Optional[str] = Field(default="", description="User defined custom category if 'Custom' chosen")
    target_items: List[str] = Field(default_factory=list, description="Items or services desired")
    preferences: Optional[str] = Field(default="", description="Specific wishes, brands, materials, or requirements")

class CustomPlannerItem(BaseModel):
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

class CustomPlannerOutput(BaseModel):
    planner: str = "custom"
    plan_title: str
    domain: str = "GENERAL"
    budget: float
    budget_used: float
    remaining_budget: float
    ai_notes: Optional[str] = None
    is_mock_ai: bool = False
    
    # Rich Domain Planning Data
    feasibility: Optional[FeasibilityData] = None
    requirements: List[Dict[str, Any]] = Field(default_factory=list)
    cost_breakdown: List[Dict[str, Any]] = Field(default_factory=list)
    materials: List[Dict[str, Any]] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    recommendations: List[Dict[str, str]] = Field(default_factory=list)
    data_sources: List[Dict[str, str]] = Field(default_factory=list)
    alternative_plans: List[Dict[str, Any]] = Field(default_factory=list)

    items: List[CustomPlannerItem] = Field(default_factory=list)
    recommendation_id: Optional[int] = None
