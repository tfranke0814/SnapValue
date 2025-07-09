"""
Tests for MarketData model - Step 1 Database Models & Configuration
"""
import pytest
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.market_data import MarketData


class TestMarketDataModel:
    """Test cases for MarketData model."""
    
    def test_market_data_creation(self, db_session: Session, sample_market_data):
        """Test basic market data creation."""
        market_item = MarketData(**sample_market_data)
        db_session.add(market_item)
        db_session.commit()
        db_session.refresh(market_item)
        
        assert market_item.id is not None
        assert market_item.item_category == sample_market_data["item_category"]
        assert market_item.item_description == sample_market_data["item_description"]
        assert market_item.price == sample_market_data["price"]
        assert market_item.source == sample_market_data["source"]
        assert market_item.condition == sample_market_data["condition"]
        assert market_item.seller_rating == sample_market_data["seller_rating"]
        assert market_item.location == sample_market_data["location"]
        assert isinstance(market_item.created_at, datetime)
        assert isinstance(market_item.updated_at, datetime)
    
    def test_market_data_price_validation(self, db_session: Session, sample_market_data):
        """Test price validation (must be positive)."""
        # Test valid prices
        valid_prices = [0.01, 10.50, 999.99, 1000.0]
        
        for price in valid_prices:
            market_data = sample_market_data.copy()
            market_data["price"] = price
            
            market_item = MarketData(**market_data)
            db_session.add(market_item)
            db_session.commit()
            db_session.refresh(market_item)
            
            assert market_item.price == price
    
    def test_market_data_category_enum(self, db_session: Session, sample_market_data):
        """Test item category field."""
        valid_categories = [
            "electronics", "jewelry", "collectibles", 
            "furniture", "clothing", "books", "other"
        ]
        
        for category in valid_categories:
            market_data = sample_market_data.copy()
            market_data["item_category"] = category
            
            market_item = MarketData(**market_data)
            db_session.add(market_item)
            db_session.commit()
            db_session.refresh(market_item)
            
            assert market_item.item_category == category
    
    def test_market_data_source_validation(self, db_session: Session, sample_market_data):
        """Test source field validation."""
        valid_sources = ["ebay", "facebook", "craigslist", "depop", "mercari", "poshmark"]
        
        for source in valid_sources:
            market_data = sample_market_data.copy()
            market_data["source"] = source
            
            market_item = MarketData(**market_data)
            db_session.add(market_item)
            db_session.commit()
            db_session.refresh(market_item)
            
            assert market_item.source == source
    
    def test_market_data_condition_enum(self, db_session: Session, sample_market_data):
        """Test condition field."""
        valid_conditions = ["new", "like_new", "good", "fair", "poor"]
        
        for condition in valid_conditions:
            market_data = sample_market_data.copy()
            market_data["condition"] = condition
            
            market_item = MarketData(**market_data)
            db_session.add(market_item)
            db_session.commit()
            db_session.refresh(market_item)
            
            assert market_item.condition == condition
    
    def test_market_data_seller_rating_validation(self, db_session: Session, sample_market_data):
        """Test seller rating validation (0.0 to 5.0)."""
        valid_ratings = [0.0, 2.5, 4.8, 5.0]
        
        for rating in valid_ratings:
            market_data = sample_market_data.copy()
            market_data["seller_rating"] = rating
            
            market_item = MarketData(**market_data)
            db_session.add(market_item)
            db_session.commit()
            db_session.refresh(market_item)
            
            assert market_item.seller_rating == rating
    
    def test_market_data_listing_date(self, db_session: Session, sample_market_data):
        """Test listing date handling."""
        test_date = date(2025, 1, 1)
        
        market_data = sample_market_data.copy()
        market_data["listing_date"] = test_date
        
        market_item = MarketData(**market_data)
        db_session.add(market_item)
        db_session.commit()
        db_session.refresh(market_item)
        
        assert market_item.listing_date == test_date
    
    def test_market_data_embeddings_storage(self, db_session: Session, sample_market_data):
        """Test embeddings storage (JSON field)."""
        embeddings = {
            "image_embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
            "text_embedding": [0.6, 0.7, 0.8, 0.9, 1.0],
            "combined_embedding": [0.15, 0.25, 0.35, 0.45, 0.55]
        }
        
        market_data = sample_market_data.copy()
        market_data["embeddings"] = embeddings
        
        market_item = MarketData(**market_data)
        db_session.add(market_item)
        db_session.commit()
        db_session.refresh(market_item)
        
        assert market_item.embeddings == embeddings
        assert market_item.embeddings["image_embedding"] == [0.1, 0.2, 0.3, 0.4, 0.5]
    
    def test_market_data_additional_data_storage(self, db_session: Session, sample_market_data):
        """Test additional_data JSON field."""
        additional_data = {
            "shipping_cost": 15.99,
            "return_policy": "30 days",
            "brand": "Apple",
            "model": "iPhone 12 Pro",
            "color": "Pacific Blue",
            "storage": "256GB"
        }
        
        market_data = sample_market_data.copy()
        market_data["additional_data"] = additional_data
        
        market_item = MarketData(**market_data)
        db_session.add(market_item)
        db_session.commit()
        db_session.refresh(market_item)
        
        assert market_item.additional_data == additional_data
        assert market_item.additional_data["brand"] == "Apple"
        assert market_item.additional_data["shipping_cost"] == 15.99
    
    def test_market_data_string_representation(self, db_session: Session, sample_market_data):
        """Test market data string representation."""
        market_item = MarketData(**sample_market_data)
        db_session.add(market_item)
        db_session.commit()
        db_session.refresh(market_item)
        
        expected_str = f"MarketData(id={market_item.id}, category={market_item.item_category})"
        assert str(market_item) == expected_str
    
    def test_market_data_default_values(self, db_session: Session):
        """Test default values for market data fields."""
        # Create minimal market data
        market_item = MarketData(
            item_category="electronics",
            item_description="Test item",
            price=100.0,
            source="ebay"
        )
        db_session.add(market_item)
        db_session.commit()
        db_session.refresh(market_item)
        
        assert market_item.condition is None
        assert market_item.seller_rating is None
        assert market_item.location is None
        assert market_item.embeddings == {}
        assert market_item.additional_data == {}
        assert market_item.listing_date is None
    
    def test_market_data_updated_at_changes(self, db_session: Session, sample_market_data):
        """Test that updated_at changes when market data is modified."""
        market_item = MarketData(**sample_market_data)
        db_session.add(market_item)
        db_session.commit()
        db_session.refresh(market_item)
        
        original_updated_at = market_item.updated_at
        
        # Modify market data
        market_item.price = 699.99
        db_session.commit()
        db_session.refresh(market_item)
        
        assert market_item.updated_at > original_updated_at
    
    def test_market_data_query_methods(self, db_session: Session, create_market_data):
        """Test common query methods for market data."""
        # Create test market data
        item1 = create_market_data(
            item_category="electronics",
            price=100.0,
            source="ebay",
            condition="good"
        )
        item2 = create_market_data(
            item_category="electronics",
            price=150.0,
            source="facebook",
            condition="like_new"
        )
        item3 = create_market_data(
            item_category="jewelry",
            price=200.0,
            source="ebay",
            condition="new"
        )
        
        # Test query by category
        electronics = db_session.query(MarketData).filter_by(
            item_category="electronics"
        ).all()
        assert len(electronics) == 2
        
        # Test query by source
        ebay_items = db_session.query(MarketData).filter_by(source="ebay").all()
        assert len(ebay_items) == 2
        
        # Test query by price range
        affordable_items = db_session.query(MarketData).filter(
            MarketData.price <= 150.0
        ).all()
        assert len(affordable_items) == 2
        
        # Test query by condition
        new_items = db_session.query(MarketData).filter_by(condition="new").all()
        assert len(new_items) == 1
        assert new_items[0].id == item3.id
    
    def test_market_data_ordering(self, db_session: Session, create_market_data):
        """Test ordering of market data."""
        # Create market data with different prices
        item1 = create_market_data(price=100.0)
        item2 = create_market_data(price=50.0)
        item3 = create_market_data(price=200.0)
        
        # Test ordering by price (ascending)
        items_by_price = db_session.query(MarketData).order_by(
            MarketData.price.asc()
        ).all()
        
        assert items_by_price[0].id == item2.id  # $50
        assert items_by_price[1].id == item1.id  # $100
        assert items_by_price[2].id == item3.id  # $200
        
        # Test ordering by created_at (newest first)
        items_by_date = db_session.query(MarketData).order_by(
            MarketData.created_at.desc()
        ).all()
        
        assert items_by_date[0].id == item3.id  # Most recent
