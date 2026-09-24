from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    planner_type = Column(String(50), nullable=False, index=True)  # 'home', 'party', 'jewelry'
    budget = Column(Float, nullable=False)
    total_estimated_cost = Column(Float, nullable=False)
    remaining_budget = Column(Float, nullable=False)
    input_data = Column(Text, nullable=False)  # Serialized JSON string of inputs
    plan_data = Column(Text, nullable=True)    # Serialized JSON string of rich planning result
    ai_notes = Column(Text, nullable=True)     # Notes or style rationale
    is_mock_ai = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="recommendations")
    items = relationship(
        "RecommendationItem",
        back_populates="recommendation",
        cascade="all, delete-orphan",
        order_by="RecommendationItem.id"
    )

    def __repr__(self):
        return f"<Recommendation id={self.id} planner={self.planner_type} budget={self.budget}>"


class RecommendationItem(Base):
    __tablename__ = "recommendation_items"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(Integer, ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    estimated_price = Column(Float, nullable=False)
    platform = Column(String(100), nullable=False)
    product_url = Column(String(500), nullable=False)
    reason = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)

    # Relationship
    recommendation = relationship("Recommendation", back_populates="items")

    def __repr__(self):
        return f"<RecommendationItem id={self.id} name={self.name} price={self.estimated_price}>"
