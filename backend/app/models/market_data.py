from sqlalchemy import Column, Integer, String, DateTime, Float, Text, JSON, Index
from sqlalchemy.sql import func
from datetime import datetime
from app.database.base import Base

class MarketData(Base):
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Item Information
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False, index=True)
    subcategory = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    condition = Column(String, nullable=True)
    
    # Price Information
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    original_price = Column(Float, nullable=True)
    
    # Source Information
    source = Column(String, nullable=False)  # e.g., "ebay", "amazon", "etsy"
    source_url = Column(String, nullable=True)
    source_id = Column(String, nullable=True)
    
    # AI/ML Data
    embeddings = Column(JSON, nullable=True)  # Vector embeddings for similarity search
    features = Column(JSON, nullable=True)    # Extracted features
    image_url = Column(String, nullable=True)
    
    # Metadata
    scraped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Search Performance
    __table_args__ = (
        Index('idx_category_price', 'category', 'price'),
        Index('idx_source_category', 'source', 'category'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<MarketData(id={self.id}, title='{self.title}', price={self.price})>"