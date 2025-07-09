"""
Tests for Appraisal model - Step 1 Database Models & Configuration
"""
import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.appraisal import Appraisal
from app.models.user import User


class TestAppraisalModel:
    """Test cases for Appraisal model."""
    
    def test_appraisal_creation(self, db_session: Session, create_user, sample_appraisal_data):
        """Test basic appraisal creation."""
        # Create user first
        user = create_user()
        
        # Create appraisal
        appraisal_data = sample_appraisal_data.copy()
        appraisal_data["user_id"] = user.id
        
        appraisal = Appraisal(**appraisal_data)
        db_session.add(appraisal)
        db_session.commit()
        db_session.refresh(appraisal)
        
        assert appraisal.id is not None
        assert appraisal.user_id == user.id
        assert appraisal.image_url == sample_appraisal_data["image_url"]
        assert appraisal.status == sample_appraisal_data["status"]
        assert appraisal.estimated_value == sample_appraisal_data["estimated_value"]
        assert appraisal.confidence_score == sample_appraisal_data["confidence_score"]
        assert isinstance(appraisal.created_at, datetime)
        assert isinstance(appraisal.updated_at, datetime)
    
    def test_appraisal_foreign_key_constraint(self, db_session: Session, sample_appraisal_data):
        """Test foreign key constraint with user."""
        # Try to create appraisal with non-existent user_id
        appraisal_data = sample_appraisal_data.copy()
        appraisal_data["user_id"] = 999  # Non-existent user
        
        appraisal = Appraisal(**appraisal_data)
        db_session.add(appraisal)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_appraisal_json_fields(self, db_session: Session, create_user, sample_appraisal_data):
        """Test JSON fields storage and retrieval."""
        user = create_user()
        
        appraisal_data = sample_appraisal_data.copy()
        appraisal_data["user_id"] = user.id
        
        appraisal = Appraisal(**appraisal_data)
        db_session.add(appraisal)
        db_session.commit()
        db_session.refresh(appraisal)
        
        # Test detected_objects list
        assert appraisal.detected_objects == ["smartphone", "case"]
        
        # Test ai_results JSON
        assert appraisal.ai_results["vision_api"]["labels"] == ["smartphone", "electronics", "mobile device"]
        assert appraisal.ai_results["vision_api"]["confidence"] == 0.95
        
        # Test market_data JSON
        assert appraisal.market_data["price_range"]["average"] == 250
        assert appraisal.market_data["similar_items_count"] == 15
    
    def test_appraisal_status_enum(self, db_session: Session, create_user, sample_appraisal_data):
        """Test appraisal status field."""
        user = create_user()
        
        valid_statuses = ["pending", "processing", "completed", "failed"]
        
        for status in valid_statuses:
            appraisal_data = sample_appraisal_data.copy()
            appraisal_data["user_id"] = user.id
            appraisal_data["status"] = status
            
            appraisal = Appraisal(**appraisal_data)
            db_session.add(appraisal)
            db_session.commit()
            db_session.refresh(appraisal)
            
            assert appraisal.status == status
    
    def test_appraisal_confidence_score_validation(self, db_session: Session, create_user, sample_appraisal_data):
        """Test confidence score validation (0.0 to 1.0)."""
        user = create_user()
        
        # Test valid confidence scores
        valid_scores = [0.0, 0.5, 0.85, 1.0]
        
        for score in valid_scores:
            appraisal_data = sample_appraisal_data.copy()
            appraisal_data["user_id"] = user.id
            appraisal_data["confidence_score"] = score
            
            appraisal = Appraisal(**appraisal_data)
            db_session.add(appraisal)
            db_session.commit()
            db_session.refresh(appraisal)
            
            assert appraisal.confidence_score == score
    
    def test_appraisal_relationship_with_user(self, db_session: Session, create_user, sample_appraisal_data):
        """Test relationship between appraisal and user."""
        user = create_user()
        
        appraisal_data = sample_appraisal_data.copy()
        appraisal_data["user_id"] = user.id
        
        appraisal = Appraisal(**appraisal_data)
        db_session.add(appraisal)
        db_session.commit()
        db_session.refresh(appraisal)
        
        # Test back reference
        assert appraisal.user.id == user.id
        assert appraisal.user.email == user.email
    
    def test_appraisal_string_representation(self, db_session: Session, create_user, sample_appraisal_data):
        """Test appraisal string representation."""
        user = create_user()
        
        appraisal_data = sample_appraisal_data.copy()
        appraisal_data["user_id"] = user.id
        
        appraisal = Appraisal(**appraisal_data)
        db_session.add(appraisal)
        db_session.commit()
        db_session.refresh(appraisal)
        
        expected_str = f"Appraisal(id={appraisal.id}, status={appraisal.status})"
        assert str(appraisal) == expected_str
    
    def test_appraisal_default_values(self, db_session: Session, create_user):
        """Test default values for appraisal fields."""
        user = create_user()
        
        # Create minimal appraisal
        appraisal = Appraisal(
            user_id=user.id,
            image_url="https://example.com/test.jpg"
        )
        db_session.add(appraisal)
        db_session.commit()
        db_session.refresh(appraisal)
        
        assert appraisal.status == "pending"  # Default status
        assert appraisal.estimated_value is None
        assert appraisal.confidence_score is None
        assert appraisal.detected_objects == []
        assert appraisal.ai_results == {}
        assert appraisal.market_data == {}
    
    def test_appraisal_updated_at_changes(self, db_session: Session, create_user, sample_appraisal_data):
        """Test that updated_at changes when appraisal is modified."""
        user = create_user()
        
        appraisal_data = sample_appraisal_data.copy()
        appraisal_data["user_id"] = user.id
        
        appraisal = Appraisal(**appraisal_data)
        db_session.add(appraisal)
        db_session.commit()
        db_session.refresh(appraisal)
        
        original_updated_at = appraisal.updated_at
        
        # Modify appraisal
        appraisal.status = "completed"
        db_session.commit()
        db_session.refresh(appraisal)
        
        assert appraisal.updated_at > original_updated_at
    
    def test_appraisal_query_methods(self, db_session: Session, create_user, create_appraisal):
        """Test common query methods for appraisals."""
        user = create_user()
        
        # Create test appraisals
        appraisal1 = create_appraisal(user_id=user.id, status="pending")
        appraisal2 = create_appraisal(user_id=user.id, status="completed")
        appraisal3 = create_appraisal(user_id=user.id, status="failed")
        
        # Test query by status
        pending_appraisals = db_session.query(Appraisal).filter_by(status="pending").all()
        assert len(pending_appraisals) == 1
        assert pending_appraisals[0].id == appraisal1.id
        
        # Test query by user
        user_appraisals = db_session.query(Appraisal).filter_by(user_id=user.id).all()
        assert len(user_appraisals) == 3
        
        # Test query by confidence score range
        high_confidence = db_session.query(Appraisal).filter(
            Appraisal.confidence_score >= 0.8
        ).all()
        assert len(high_confidence) == 3  # All test appraisals have 0.85 confidence
    
    def test_appraisal_ordering(self, db_session: Session, create_user, create_appraisal):
        """Test ordering of appraisals."""
        user = create_user()
        
        # Create appraisals
        appraisal1 = create_appraisal(user_id=user.id)
        appraisal2 = create_appraisal(user_id=user.id)
        appraisal3 = create_appraisal(user_id=user.id)
        
        # Test ordering by created_at (newest first)
        appraisals = db_session.query(Appraisal).order_by(
            Appraisal.created_at.desc()
        ).all()
        
        assert appraisals[0].id == appraisal3.id  # Most recent
        assert appraisals[1].id == appraisal2.id
        assert appraisals[2].id == appraisal1.id  # Oldest
