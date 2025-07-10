"""
Unit tests for AppraisalService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import uuid

from app.services.appraisal_service import AppraisalService
from app.models.appraisal import Appraisal
from app.utils.exceptions import ValidationError, AIProcessingError


@pytest.mark.unit
@pytest.mark.services
class TestAppraisalService:
    
    def test_init(self, db_session):
        """Test service initialization"""
        service = AppraisalService(db_session)
        assert service.db == db_session
        assert hasattr(service, 'storage_service')
        assert hasattr(service, 'vision_service')
        assert hasattr(service, 'ai_service')
    
    def test_validate_input_valid_file_content(self, db_session):
        """Test input validation with valid file content"""
        service = AppraisalService(db_session)
        
        data = {
            'file_content': b'fake_image_data',
            'filename': 'test.jpg',
            'user_id': 1
        }
        
        assert service.validate_input(data) is True
    
    def test_validate_input_valid_image_url(self, db_session):
        """Test input validation with valid image URL"""
        service = AppraisalService(db_session)
        
        data = {
            'image_url': 'https://example.com/image.jpg',
            'user_id': 1
        }
        
        assert service.validate_input(data) is True
    
    def test_validate_input_invalid_no_image(self, db_session):
        """Test input validation with no image source"""
        service = AppraisalService(db_session)
        
        data = {'user_id': 1}
        
        assert service.validate_input(data) is False
    
    def test_validate_input_invalid_no_user_id(self, db_session):
        """Test input validation with no user ID"""
        service = AppraisalService(db_session)
        
        data = {
            'file_content': b'fake_image_data',
            'filename': 'test.jpg'
        }
        
        assert service.validate_input(data) is False
    
    @patch('app.services.appraisal_service.StorageService')
    @patch('app.services.appraisal_service.VisionService')
    @patch('app.services.appraisal_service.AIService')
    def test_submit_appraisal_with_file(self, mock_ai, mock_vision, mock_storage, 
                                       db_session, create_user, test_image_file):
        """Test submitting appraisal with file upload"""
        # Setup mocks
        mock_storage_instance = Mock()
        mock_storage.return_value = mock_storage_instance
        mock_storage_instance.upload_image = AsyncMock(return_value={
            'url': 'https://example.com/uploaded.jpg',
            'path': 'uploads/test.jpg',
            'size': 1024
        })
        
        mock_vision_instance = Mock()
        mock_vision.return_value = mock_vision_instance
        mock_vision_instance.analyze_image = AsyncMock(return_value={
            'labels': [{'description': 'smartphone', 'score': 0.95}],
            'objects': [{'name': 'phone', 'score': 0.90}]
        })
        
        mock_ai_instance = Mock()
        mock_ai.return_value = mock_ai_instance
        mock_ai_instance.generate_embeddings = AsyncMock(return_value=[0.1, 0.2, 0.3])
        
        # Create test user
        user = create_user()
        
        # Create service and submit appraisal
        service = AppraisalService(db_session)
        
        with patch('app.services.appraisal_service.submit_appraisal_task') as mock_task:
            mock_task.return_value = 'task_123'
            
            result = service.submit_appraisal(
                file_content=test_image_file.read(),
                filename='test.jpg',
                user_id=user.id
            )
        
        # Verify result
        assert 'appraisal_id' in result
        assert 'task_id' in result
        assert result['status'] == 'submitted'
        assert 'submitted_at' in result
        
        # Verify appraisal was created in database
        appraisal = db_session.query(Appraisal).filter(
            Appraisal.id == result['appraisal_id']
        ).first()
        assert appraisal is not None
        assert appraisal.user_id == user.id
        assert appraisal.status == 'submitted'
    
    def test_submit_appraisal_with_url(self, db_session, create_user):
        """Test submitting appraisal with image URL"""
        user = create_user()
        service = AppraisalService(db_session)
        
        with patch('app.services.appraisal_service.submit_appraisal_task') as mock_task:
            mock_task.return_value = 'task_456'
            
            result = service.submit_appraisal(
                image_url='https://example.com/test.jpg',
                user_id=user.id
            )
        
        assert 'appraisal_id' in result
        assert result['status'] == 'submitted'
    
    def test_submit_appraisal_invalid_input(self, db_session):
        """Test submitting appraisal with invalid input"""
        service = AppraisalService(db_session)
        
        with pytest.raises(ValidationError):
            service.submit_appraisal()  # No parameters
    
    def test_get_appraisal_status_exists(self, db_session, create_user, create_appraisal):
        """Test getting status for existing appraisal"""
        user = create_user()
        appraisal = create_appraisal(user.id, status='processing')
        
        service = AppraisalService(db_session)
        
        with patch('app.services.appraisal_service.status_tracker') as mock_tracker:
            mock_tracker.get_status.return_value = Mock(
                appraisal_id=str(appraisal.id),
                status='processing',
                progress_percentage=50.0,
                current_step='vision_analysis'
            )
            
            status = service.get_appraisal_status(str(appraisal.id))
        
        assert status is not None
        assert status['appraisal_id'] == str(appraisal.id)
        assert status['status'] == 'processing'
    
    def test_get_appraisal_status_not_found(self, db_session):
        """Test getting status for non-existent appraisal"""
        service = AppraisalService(db_session)
        
        status = service.get_appraisal_status('non-existent-id')
        assert status is None
    
    def test_get_appraisal_result_completed(self, db_session, create_user, create_appraisal):
        """Test getting result for completed appraisal"""
        user = create_user()
        appraisal = create_appraisal(
            user.id, 
            status='completed',
            market_price=299.99,
            confidence_score=0.85
        )
        
        service = AppraisalService(db_session)
        result = service.get_appraisal_result(str(appraisal.id))
        
        assert result is not None
        assert result['appraisal_id'] == str(appraisal.id)
        assert result['estimated_value'] == 299.99
        assert result['confidence_score'] == 0.85
    
    def test_get_appraisal_result_not_completed(self, db_session, create_user, create_appraisal):
        """Test getting result for incomplete appraisal"""
        user = create_user()
        appraisal = create_appraisal(user.id, status='processing')
        
        service = AppraisalService(db_session)
        result = service.get_appraisal_result(str(appraisal.id))
        
        assert result is None
    
    def test_list_user_appraisals(self, db_session, create_user, create_appraisal):
        """Test listing user appraisals"""
        user1 = create_user(email='user1@test.com')
        user2 = create_user(email='user2@test.com')
        
        # Create appraisals for both users
        appraisal1 = create_appraisal(user1.id)
        appraisal2 = create_appraisal(user1.id)
        appraisal3 = create_appraisal(user2.id)
        
        service = AppraisalService(db_session)
        
        # Get appraisals for user1
        user1_appraisals = service.list_user_appraisals(user1.id)
        assert len(user1_appraisals) == 2
        
        # Get appraisals for user2
        user2_appraisals = service.list_user_appraisals(user2.id)
        assert len(user2_appraisals) == 1
    
    def test_list_user_appraisals_with_limit(self, db_session, create_user, create_appraisal):
        """Test listing user appraisals with limit"""
        user = create_user()
        
        # Create multiple appraisals
        for i in range(5):
            create_appraisal(user.id)
        
        service = AppraisalService(db_session)
        appraisals = service.list_user_appraisals(user.id, limit=3)
        
        assert len(appraisals) == 3
    
    def test_cancel_appraisal_success(self, db_session, create_user, create_appraisal):
        """Test successfully canceling an appraisal"""
        user = create_user()
        appraisal = create_appraisal(user.id, status='processing')
        
        service = AppraisalService(db_session)
        
        with patch('app.services.appraisal_service.task_manager') as mock_task_manager:
            mock_task_manager.cancel_task.return_value = True
            
            success = service.cancel_appraisal(str(appraisal.id), user.id)
        
        assert success is True
        
        # Verify appraisal status was updated
        db_session.refresh(appraisal)
        assert appraisal.status == 'cancelled'
    
    def test_cancel_appraisal_not_found(self, db_session):
        """Test canceling non-existent appraisal"""
        service = AppraisalService(db_session)
        success = service.cancel_appraisal('non-existent-id', 1)
        assert success is False
    
    def test_cancel_appraisal_wrong_user(self, db_session, create_user, create_appraisal):
        """Test canceling appraisal by wrong user"""
        user1 = create_user(email='user1@test.com')
        user2 = create_user(email='user2@test.com')
        appraisal = create_appraisal(user1.id)
        
        service = AppraisalService(db_session)
        success = service.cancel_appraisal(str(appraisal.id), user2.id)
        assert success is False
    
    def test_health_check_healthy(self, db_session):
        """Test health check when service is healthy"""
        service = AppraisalService(db_session)
        
        with patch.object(service, 'storage_service') as mock_storage, \
             patch.object(service, 'vision_service') as mock_vision, \
             patch.object(service, 'ai_service') as mock_ai:
            
            mock_storage.health_check.return_value = True
            mock_vision.health_check.return_value = True
            mock_ai.health_check.return_value = True
            
            health = service.health_check()
        
        assert health is True
    
    def test_health_check_unhealthy(self, db_session):
        """Test health check when a dependency is unhealthy"""
        service = AppraisalService(db_session)
        
        with patch.object(service, 'storage_service') as mock_storage, \
             patch.object(service, 'vision_service') as mock_vision, \
             patch.object(service, 'ai_service') as mock_ai:
            
            mock_storage.health_check.return_value = True
            mock_vision.health_check.return_value = False  # Unhealthy
            mock_ai.health_check.return_value = True
            
            health = service.health_check()
        
        assert health is False
    
    @patch('app.services.appraisal_service.logger')
    def test_error_handling_and_logging(self, mock_logger, db_session):
        """Test error handling and logging"""
        service = AppraisalService(db_session)
        
        # Simulate an error in validation
        with pytest.raises(ValidationError):
            service.process({})  # Invalid data
        
        # Verify error was logged
        mock_logger.error.assert_called()
    
    def test_process_method_delegation(self, db_session, create_user):
        """Test that process method properly delegates to submit_appraisal"""
        user = create_user()
        service = AppraisalService(db_session)
        
        data = {
            'operation': 'submit_appraisal',
            'image_url': 'https://example.com/test.jpg',
            'user_id': user.id
        }
        
        with patch.object(service, 'submit_appraisal') as mock_submit:
            mock_submit.return_value = {'appraisal_id': 'test_id'}
            
            result = service.process(data)
            
            mock_submit.assert_called_once()
            assert result == {'appraisal_id': 'test_id'}