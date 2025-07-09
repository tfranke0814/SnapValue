"""
Tests for User model - Step 1 Database Models & Configuration
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user import User


class TestUserModel:
    """Test cases for User model."""
    
    def test_user_creation(self, db_session: Session, sample_user_data):
        """Test basic user creation."""
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.id is not None
        assert user.email == sample_user_data["email"]
        assert user.api_key == sample_user_data["api_key"]
        assert user.is_active is True
        assert isinstance(user.created_at, datetime)
        # updated_at is None on creation and only set when record is updated
        assert user.updated_at is None
    
    def test_user_email_uniqueness(self, db_session: Session, sample_user_data):
        """Test that email must be unique."""
        # Create first user
        user1 = User(**sample_user_data)
        db_session.add(user1)
        db_session.commit()
        
        # Try to create second user with same email
        user2 = User(**sample_user_data)
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_api_key_uniqueness(self, db_session: Session, sample_user_data):
        """Test that API key must be unique."""
        # Create first user
        user1 = User(**sample_user_data)
        db_session.add(user1)
        db_session.commit()
        
        # Try to create second user with same API key
        user2_data = sample_user_data.copy()
        user2_data["email"] = "different@example.com"
        user2 = User(**user2_data)
        db_session.add(user2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_user_string_representation(self, db_session: Session, sample_user_data):
        """Test user string representation."""
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        
        assert str(user) == f"<User(id={user.id}, email='{sample_user_data['email']}')>"
    
    def test_user_default_values(self, db_session: Session):
        """Test default values for user fields."""
        user = User(
            email="test@example.com",
            api_key="test_key"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        assert user.is_active is True  # Default should be True
        assert user.created_at is not None
        assert user.updated_at is None  # updated_at is None on creation
    
    def test_user_updated_at_changes(self, db_session: Session, sample_user_data):
        """Test that updated_at changes when user is modified."""
        user = User(**sample_user_data)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        # Initially updated_at is None
        assert user.updated_at is None
        
        # Modify user
        user.email = "updated@example.com"
        db_session.commit()
        db_session.refresh(user)
        
        # After update, updated_at should be set
        assert user.updated_at is not None
        assert isinstance(user.updated_at, datetime)
    
    def test_user_email_validation(self, db_session: Session):
        """Test email validation (if implemented)."""
        # Test valid email
        valid_user = User(
            email="valid@example.com",
            api_key="test_key"
        )
        db_session.add(valid_user)
        db_session.commit()
        
        # This would fail if email validation is implemented
        # For now, it's just checking the basic creation works
        assert valid_user.email == "valid@example.com"
    
    def test_user_cascade_delete_appraisals(self, db_session: Session, create_user, create_appraisal):
        """Test that deleting user cascades to appraisals."""
        # Create user
        user = create_user()
        
        # Create appraisal for user
        appraisal = create_appraisal(user_id=user.id)
        
        # Verify appraisal exists
        assert appraisal.user_id == user.id
        
        # Delete user
        db_session.delete(user)
        db_session.commit()
        
        # Verify appraisal is also deleted (cascade)
        from app.models.appraisal import Appraisal
        remaining_appraisals = db_session.query(Appraisal).filter_by(user_id=user.id).all()
        assert len(remaining_appraisals) == 0
    
    def test_user_relationship_with_appraisals(self, db_session: Session, create_user, create_appraisal):
        """Test relationship between user and appraisals."""
        # Create user
        user = create_user()
        
        # Create multiple appraisals for user
        appraisal1 = create_appraisal(user_id=user.id, market_price=100.0)
        appraisal2 = create_appraisal(user_id=user.id, market_price=200.0)
        
        # Test relationship
        db_session.refresh(user)
        assert len(user.appraisals) == 2
        assert appraisal1 in user.appraisals
        assert appraisal2 in user.appraisals
    
    def test_user_query_methods(self, db_session: Session, create_user):
        """Test common query methods for users."""
        # Create test users
        user1 = create_user(email="user1@example.com", is_active=True)
        user2 = create_user(email="user2@example.com", is_active=False)
        
        # Test query by email
        found_user = db_session.query(User).filter_by(email="user1@example.com").first()
        assert found_user.id == user1.id
        
        # Test query by active status
        active_users = db_session.query(User).filter_by(is_active=True).all()
        assert len(active_users) == 1
        assert active_users[0].id == user1.id
        
        # Test query by API key
        found_by_key = db_session.query(User).filter_by(api_key=user1.api_key).first()
        assert found_by_key.id == user1.id
