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
from unittest.mock import Mock, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json
import io
from PIL import Image

# Import your database models and configuration
from app.database.base import Base
from app.database.connection import get_db
from app.models.user import User
from app.models.appraisal import Appraisal
from app.models.market_data import MarketData
from app.main import app


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


# API Testing Fixtures
@pytest.fixture
def test_client(override_get_db):
    """Create a test client with database dependency override."""
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}


@pytest.fixture
def authenticated_client(test_client, create_user):
    """Create an authenticated test client."""
    # Create a test user
    user = create_user(email="auth@test.com", api_key="test_auth_key")
    
    # Set authentication header
    test_client.headers.update({"Authorization": f"Bearer test_auth_key"})
    
    return test_client, user


# Mock Service Fixtures
@pytest.fixture
def mock_storage_service():
    """Mock storage service for testing."""
    mock = Mock()
    mock.upload_image = AsyncMock(return_value={
        'url': 'https://example.com/test-image.jpg',
        'path': 'test/path/image.jpg',
        'size': 1024
    })
    mock.delete_image = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_vision_service():
    """Mock vision service for testing."""
    mock = Mock()
    mock.analyze_image = AsyncMock(return_value={
        'labels': [
            {'description': 'smartphone', 'score': 0.95},
            {'description': 'electronics', 'score': 0.90}
        ],
        'objects': [
            {'name': 'mobile phone', 'score': 0.92}
        ],
        'text': {'full_text': ''},
        'faces': []
    })
    return mock


@pytest.fixture
def mock_ai_service():
    """Mock AI service for testing."""
    mock = Mock()
    mock.generate_embeddings = AsyncMock(return_value=[0.1, 0.2, 0.3, 0.4, 0.5])
    mock.extract_features = AsyncMock(return_value={
        'category': 'electronics',
        'brand': 'Apple',
        'model': 'iPhone'
    })
    return mock


@pytest.fixture
def mock_market_service():
    """Mock market service for testing."""
    mock = Mock()
    mock.find_similar_items = AsyncMock(return_value=[
        {'price': 299.99, 'similarity': 0.95, 'source': 'ebay'},
        {'price': 315.00, 'similarity': 0.90, 'source': 'amazon'}
    ])
    mock.get_market_analysis = AsyncMock(return_value={
        'average_price': 307.50,
        'price_range': {'min': 250.00, 'max': 350.00},
        'market_activity': 'high'
    })
    return mock


# Test Data Fixtures
@pytest.fixture
def test_image_file():
    """Create a test image file for upload testing."""
    # Create a simple test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes


@pytest.fixture
def test_image_data():
    """Test image metadata."""
    return {
        'filename': 'test_image.jpg',
        'content_type': 'image/jpeg',
        'size': 1024
    }


@pytest.fixture
def jwt_token(create_user):
    """Create a valid JWT token for testing."""
    from app.api.v1.auth import create_access_token
    
    user_data = {"sub": "test_user_123", "email": "test@example.com"}
    token = create_access_token(data=user_data)
    return token


@pytest.fixture
def auth_headers(jwt_token):
    """Authorization headers for API testing."""
    return {"Authorization": f"Bearer {jwt_token}"}


# Performance Testing Fixtures
@pytest.fixture
def performance_test_data():
    """Generate test data for performance testing."""
    return {
        'batch_size': 10,
        'concurrent_requests': 5,
        'timeout_seconds': 30
    }


# Mock External Services
@pytest.fixture
def mock_google_cloud_services():
    """Mock Google Cloud services."""
    mocks = {
        'storage': Mock(),
        'vision': Mock(),
        'vertex_ai': Mock()
    }
    
    # Configure storage mock
    mocks['storage'].upload_blob = Mock(return_value='gs://bucket/path/file.jpg')
    mocks['storage'].delete_blob = Mock(return_value=True)
    
    # Configure vision mock
    mocks['vision'].detect_objects = Mock(return_value=[
        {'name': 'smartphone', 'confidence': 0.95}
    ])
    
    # Configure Vertex AI mock
    mocks['vertex_ai'].predict = Mock(return_value={
        'predictions': [{'embeddings': [0.1, 0.2, 0.3]}]
    })
    
    return mocks


@pytest.fixture
def error_scenarios():
    """Common error scenarios for testing."""
    return {
        'network_timeout': TimeoutError("Network timeout"),
        'invalid_image': ValueError("Invalid image format"),
        'service_unavailable': ConnectionError("Service unavailable"),
        'quota_exceeded': Exception("Quota exceeded"),
        'authentication_failed': Exception("Authentication failed")
    }
