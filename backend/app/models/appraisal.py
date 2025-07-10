from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
import enum
from app.database.base import Base

class AppraisalStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Appraisal(Base):
    __tablename__ = "appraisals"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    image_path = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    
    # AI Analysis Results
    vision_results = Column(JSON, nullable=True)
    detected_objects = Column(JSON, nullable=True)
    embeddings = Column(JSON, nullable=True)
    
    # Market Analysis
    similar_items = Column(JSON, nullable=True)
    market_price = Column(Float, nullable=True)
    price_range_min = Column(Float, nullable=True)
    price_range_max = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    
    # Processing Status
    status = Column(String, default=AppraisalStatus.PENDING)
    error_message = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="appraisals")
    
    def __repr__(self):
        return f"<Appraisal(id={self.id}, user_id={self.user_id}, status='{self.status}')>"