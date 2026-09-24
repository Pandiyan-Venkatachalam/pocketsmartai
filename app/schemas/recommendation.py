from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class RecommendationItemBase(BaseModel):
    name: str
    category: str
    estimated_price: float
    platform: str
    product_url: str
    reason: str
    image_url: Optional[str] = None

class RecommendationItemOut(RecommendationItemBase):
    id: int
    recommendation_id: int
    model_config = {"from_attributes": True}

class RecommendationOut(BaseModel):
    id: int
    user_id: int
    planner_type: str
    budget: float
    total_estimated_cost: float
    remaining_budget: float
    input_data: Dict[str, Any]
    ai_notes: Optional[str] = None
    is_mock_ai: bool = False
    created_at: datetime
    items: List[RecommendationItemOut] = []
    model_config = {"from_attributes": True}

class HistoryItemOut(BaseModel):
    id: int
    planner_type: str
    budget: float
    total_estimated_cost: float
    remaining_budget: float
    items_count: int
    created_at: datetime
    summary: str
    is_mock_ai: bool
    model_config = {"from_attributes": True}

class DashboardStats(BaseModel):
    user_name: str
    total_recommendations: int
    total_budget_planned: float
    planner_breakdown: Dict[str, int]
    recent_recommendations: List[HistoryItemOut]
