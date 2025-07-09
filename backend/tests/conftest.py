"""
Test configuration and fixtures for SnapValue backend testing.
"""
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Generator, AsyncGenerator
import tempfile
import os

# Import your database models and configuration
from app.database.base import Base
from app.database.connection import get_db
from app.models.user import User
from app.models.appraisal import Appraisal
from app.models.market_data import MarketData


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test.db")
    db_url = f"sqlite:///{db_path}"
    
    # Create engine with SQLite for testing
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL debugging
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine, db_url
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    os.unlink(db_path)
    os.rmdir(temp_dir)


@pytest.fixture
def db_session(temp_db):
    """Create a database session for each test."""
    engine, db_url = temp_db
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def override_get_db(db_session):
    """Override the get_db dependency for testing."""
    def _get_db():
        try:
            yield db_session
        finally:
            pass
    return _get_db


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "api_key": "test_api_key_123",
        "is_active": True
    }


@pytest.fixture
def sample_appraisal_data():
    """Sample appraisal data for testing."""
    return {
        "image_path": "/path/to/image.jpg",
        "image_url": "https://example.com/image.jpg",
        "status": "completed",
        "market_price": 250.50,
        "confidence_score": 0.85,
        "detected_objects": ["smartphone", "case"],
        "vision_results": {
            "vision_api": {
                "labels": ["smartphone", "electronics", "mobile device"],
                "confidence": 0.95
            }
        },
        "similar_items": {
            "price_range": {"low": 200, "high": 300, "average": 250},
            "similar_items_count": 15
        }
    }


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        "item_category": "electronics",
        "item_description": "iPhone 12 Pro 256GB",
        "price": 599.99,
        "source": "ebay",
        "listing_date": "2025-01-01",
        "condition": "used",
        "seller_rating": 4.8,
        "location": "New York, NY"
    }


@pytest.fixture
def create_user(db_session, sample_user_data):
    """Factory function to create a test user."""
    counter = 0
    def _create_user(**kwargs):
        nonlocal counter
        counter += 1
        user_data = sample_user_data.copy()
        
        # Make email and api_key unique if not overridden
        if 'email' not in kwargs:
            user_data['email'] = f"test{counter}@example.com"
        if 'api_key' not in kwargs:
            user_data['api_key'] = f"test_api_key_{counter}"
        
        user_data.update(kwargs)
        user = User(**user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user
    return _create_user


@pytest.fixture
def create_appraisal(db_session, sample_appraisal_data):
    """Factory function to create a test appraisal."""
    def _create_appraisal(user_id, **kwargs):
        appraisal_data = sample_appraisal_data.copy()
        appraisal_data.update(kwargs)
        appraisal_data["user_id"] = user_id
        appraisal = Appraisal(**appraisal_data)
        db_session.add(appraisal)
        db_session.commit()
        db_session.refresh(appraisal)
        return appraisal
    return _create_appraisal


@pytest.fixture
def create_market_data(db_session, sample_market_data):
    """Factory function to create test market data."""
    def _create_market_data(**kwargs):
        market_data = sample_market_data.copy()
        market_data.update(kwargs)
        market_item = MarketData(**market_data)
        db_session.add(market_item)
        db_session.commit()
        db_session.refresh(market_item)
        return market_item
    return _create_market_data
