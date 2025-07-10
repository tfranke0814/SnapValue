"""
Unit tests for ProcessingService
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import uuid

from app.services.processing_service import ProcessingService
from app.utils.exceptions import ValidationError, AIProcessingError


@pytest.mark.unit
@pytest.mark.services
class TestProcessingService:
    
    def test_init(self, db_session):
        """Test service initialization"""
        service = ProcessingService(db_session)
        assert service.db == db_session
        assert hasattr(service, 'appraisal_service')
        assert hasattr(service, 'workflows')
        assert 'standard_appraisal' in service.workflows
        assert 'batch_appraisal' in service.workflows
        assert 'priority_appraisal' in service.workflows
    
    def test_validate_input_valid_workflow(self, db_session):
        """Test input validation with valid workflow data"""
        service = ProcessingService(db_session)
        
        data = {
            'workflow_type': 'standard_appraisal',
            'workflow_data': {'image_url': 'https://example.com/test.jpg'}
        }
        
        assert service.validate_input(data) is True
    
    def test_validate_input_valid_operation(self, db_session):
        """Test input validation with valid operation data"""
        service = ProcessingService(db_session)
        
        data = {'operation': 'system_status'}
        
        assert service.validate_input(data) is True
    
    def test_validate_input_invalid(self, db_session):
        """Test input validation with invalid data"""
        service = ProcessingService(db_session)
        
        # No workflow_type or operation
        data = {'some_field': 'value'}
        
        assert service.validate_input(data) is False
    
    def test_execute_workflow_standard_appraisal(self, db_session):
        """Test executing standard appraisal workflow"""
        service = ProcessingService(db_session)
        
        workflow_data = {
            'image_url': 'https://example.com/test.jpg',
            'user_id': 1
        }
        
        with patch.object(service.appraisal_service, 'submit_appraisal') as mock_submit:
            mock_submit.return_value = {
                'appraisal_id': 'test_id',
                'task_id': 'task_123',
                'status': 'submitted'
            }
            
            result = service.execute_workflow('standard_appraisal', workflow_data)
        
        assert result['workflow_type'] == 'standard_appraisal'
        assert 'execution_id' in result
        assert 'appraisal_result' in result
        assert result['status'] == 'submitted'
        assert 'executed_at' in result
    
    def test_execute_workflow_priority_appraisal(self, db_session):
        """Test executing priority appraisal workflow"""
        service = ProcessingService(db_session)
        
        workflow_data = {
            'image_url': 'https://example.com/test.jpg',
            'user_id': 1
        }
        
        with patch.object(service.appraisal_service, 'submit_appraisal') as mock_submit:
            mock_submit.return_value = {
                'appraisal_id': 'test_id',
                'task_id': 'task_123',
                'status': 'submitted'
            }
            
            result = service.execute_workflow('priority_appraisal', workflow_data)
        
        assert result['workflow_type'] == 'priority_appraisal'
        assert result['priority'] == 'high'
        assert 'execution_id' in result
    
    def test_execute_workflow_batch_appraisal(self, db_session):
        """Test executing batch appraisal workflow"""
        service = ProcessingService(db_session)
        
        workflow_data = {
            'items': [
                {'image_url': 'https://example.com/test1.jpg', 'user_id': 1},
                {'image_url': 'https://example.com/test2.jpg', 'user_id': 1}
            ]
        }
        
        with patch.object(service.appraisal_service, 'submit_appraisal') as mock_submit:
            mock_submit.return_value = {
                'appraisal_id': 'test_id',
                'task_id': 'task_123',
                'status': 'submitted'
            }
            
            result = service.execute_workflow('batch_appraisal', workflow_data)
        
        assert result['workflow_type'] == 'batch_appraisal'
        assert 'batch_results' in result
        assert result['batch_results']['total_items'] == 2
        assert result['batch_results']['successful_items'] == 2
        assert result['batch_results']['failed_items'] == 0
    
    def test_execute_workflow_batch_with_failures(self, db_session):
        """Test batch workflow with some failures"""
        service = ProcessingService(db_session)
        
        workflow_data = {
            'items': [
                {'image_url': 'https://example.com/test1.jpg', 'user_id': 1},
                {'image_url': 'https://example.com/test2.jpg', 'user_id': 1}
            ]
        }
        
        def side_effect(*args, **kwargs):
            # First call succeeds, second fails
            if side_effect.call_count == 1:
                side_effect.call_count += 1
                return {'appraisal_id': 'test_id', 'task_id': 'task_123'}
            else:
                raise Exception("Processing failed")
        
        side_effect.call_count = 1
        
        with patch.object(service.appraisal_service, 'submit_appraisal') as mock_submit:
            mock_submit.side_effect = side_effect
            
            result = service.execute_workflow('batch_appraisal', workflow_data)
        
        assert result['batch_results']['total_items'] == 2
        assert result['batch_results']['successful_items'] == 1
        assert result['batch_results']['failed_items'] == 1
    
    def test_execute_workflow_unknown_type(self, db_session):
        """Test executing unknown workflow type"""
        service = ProcessingService(db_session)
        
        with pytest.raises(ValidationError):
            service.execute_workflow('unknown_workflow', {})
    
    def test_execute_workflow_empty_batch(self, db_session):
        """Test batch workflow with no items"""
        service = ProcessingService(db_session)
        
        workflow_data = {'items': []}
        
        with pytest.raises(ValidationError):
            service.execute_workflow('batch_appraisal', workflow_data)
    
    @patch('app.services.processing_service.task_manager')
    @patch('app.services.processing_service.status_tracker')
    @patch('app.services.processing_service.get_all_cache_stats')
    def test_get_system_status(self, mock_cache_stats, mock_status_tracker, 
                              mock_task_manager, db_session):
        """Test getting system status"""
        # Setup mocks
        mock_task_manager.get_stats.return_value = {
            'total_tasks': 100,
            'running_tasks': 5,
            'queued_tasks': 10,
            'completed_tasks': 85,
            'failed_tasks': 0
        }
        
        mock_status_tracker.get_statistics.return_value = {
            'active_appraisals': 15,
            'average_processing_time_seconds': 120.5
        }
        
        mock_status_tracker.get_active_appraisals.return_value = [
            Mock(id='1'), Mock(id='2'), Mock(id='3')
        ]
        
        mock_cache_stats.return_value = {
            'appraisal_cache': {
                'size': 250,
                'hit_rate': 0.85
            }
        }
        
        service = ProcessingService(db_session)
        
        with patch.object(service.appraisal_service, 'health_check') as mock_health:
            mock_health.return_value = True
            
            status = service.get_system_status()
        
        assert status['status'] == 'healthy'
        assert 'timestamp' in status
        assert 'task_manager' in status
        assert 'cache_stats' in status
        assert status['active_appraisals'] == 3
        assert 'system_metrics' in status
    
    @patch('app.services.processing_service.task_manager')
    @patch('app.services.processing_service.status_tracker')
    def test_get_processing_queue_status(self, mock_status_tracker, 
                                       mock_task_manager, db_session):
        """Test getting processing queue status"""
        mock_task_manager.get_stats.return_value = {
            'queued_tasks': 8,
            'running_tasks': 3,
            'max_workers': 5
        }
        
        mock_status_tracker.get_active_appraisals.return_value = [
            Mock(status='processing'),
            Mock(status='validating'),
            Mock(status='processing')
        ]
        
        service = ProcessingService(db_session)
        queue_status = service.get_processing_queue_status()
        
        assert queue_status['queue_length'] == 8
        assert queue_status['running_tasks'] == 3
        assert queue_status['active_appraisals'] == 3
        assert 'worker_utilization' in queue_status
        assert 'estimated_wait_time_minutes' in queue_status
    
    @patch('app.services.processing_service.task_manager')
    @patch('app.services.processing_service.status_tracker')
    @patch('app.services.processing_service.cleanup_all_caches')
    def test_cleanup_system(self, mock_cleanup_caches, mock_status_tracker, 
                           mock_task_manager, db_session):
        """Test system cleanup"""
        # Setup successful cleanup
        mock_task_manager.cleanup_old_tasks = AsyncMock()
        mock_status_tracker.cleanup_old_statuses.return_value = None
        mock_cleanup_caches.return_value = None
        
        service = ProcessingService(db_session)
        result = service.cleanup_system()
        
        assert 'started_at' in result
        assert 'completed_at' in result
        assert 'operations' in result
        assert result['success'] is True
        assert 'task_cleanup' in result['operations']
        assert 'status_cleanup' in result['operations']
        assert 'cache_cleanup' in result['operations']
    
    def test_pause_processing(self, db_session):
        """Test pausing processing"""
        service = ProcessingService(db_session)
        result = service.pause_processing()
        
        assert result['action'] == 'pause_processing'
        assert result['status'] == 'requested'
        assert 'timestamp' in result
    
    def test_resume_processing(self, db_session):
        """Test resuming processing"""
        service = ProcessingService(db_session)
        result = service.resume_processing()
        
        assert result['action'] == 'resume_processing'
        assert result['status'] == 'requested'
        assert 'timestamp' in result
    
    def test_process_workflow_operation(self, db_session):
        """Test process method with workflow operation"""
        service = ProcessingService(db_session)
        
        data = {
            'operation': 'workflow',
            'workflow_type': 'standard_appraisal',
            'workflow_data': {'image_url': 'https://example.com/test.jpg'}
        }
        
        with patch.object(service, 'execute_workflow') as mock_execute:
            mock_execute.return_value = {'result': 'success'}
            
            result = service.process(data)
            
            mock_execute.assert_called_once_with('standard_appraisal', 
                                               {'image_url': 'https://example.com/test.jpg'}, {})
            assert result == {'result': 'success'}
    
    def test_process_batch_operation(self, db_session):
        """Test process method with batch operation"""
        service = ProcessingService(db_session)
        
        data = {
            'operation': 'batch_process',
            'items': [{'image_url': 'test.jpg'}]
        }
        
        with patch.object(service, 'process_batch') as mock_batch:
            mock_batch.return_value = {'batch_result': 'success'}
            
            result = service.process(data)
            
            mock_batch.assert_called_once_with([{'image_url': 'test.jpg'}], {})
            assert result == {'batch_result': 'success'}
    
    def test_process_system_status_operation(self, db_session):
        """Test process method with system status operation"""
        service = ProcessingService(db_session)
        
        data = {'operation': 'system_status'}
        
        with patch.object(service, 'get_system_status') as mock_status:
            mock_status.return_value = {'status': 'healthy'}
            
            result = service.process(data)
            
            mock_status.assert_called_once()
            assert result == {'status': 'healthy'}
    
    def test_process_unknown_operation(self, db_session):
        """Test process method with unknown operation"""
        service = ProcessingService(db_session)
        
        data = {'operation': 'unknown_operation'}
        
        with pytest.raises(ValidationError):
            service.process(data)
    
    def test_estimate_queue_wait_time(self, db_session):
        """Test queue wait time estimation"""
        service = ProcessingService(db_session)
        
        # Test with all workers busy
        task_stats = {
            'queued_tasks': 10,
            'running_tasks': 5,
            'max_workers': 5
        }
        
        wait_time = service._estimate_queue_wait_time(task_stats)
        assert wait_time > 0
        
        # Test with available workers
        task_stats = {
            'queued_tasks': 2,
            'running_tasks': 2,
            'max_workers': 5
        }
        
        wait_time = service._estimate_queue_wait_time(task_stats)
        assert wait_time == 0.0
    
    def test_get_daily_processing_count(self, db_session):
        """Test getting daily processing count"""
        service = ProcessingService(db_session)
        
        with patch('app.services.processing_service.status_tracker') as mock_tracker:
            # Create mock statuses
            today = datetime.utcnow().date()
            mock_statuses = {
                'id1': Mock(
                    status='completed',
                    completed_at=datetime.combine(today, datetime.min.time())
                ),
                'id2': Mock(
                    status='processing',
                    completed_at=None
                ),
                'id3': Mock(
                    status='completed',
                    completed_at=datetime.combine(today, datetime.min.time())
                )
            }
            
            mock_tracker.statuses = mock_statuses
            
            count = service._get_daily_processing_count()
            assert count == 2  # Two completed today
    
    def test_health_check(self, db_session):
        """Test service health check"""
        service = ProcessingService(db_session)
        
        with patch.object(service.appraisal_service, 'health_check') as mock_health:
            mock_health.return_value = True
            
            health = service.health_check()
            assert health is True
            
            mock_health.return_value = False
            health = service.health_check()
            assert health is False
    
    @patch('app.services.processing_service.logger')
    def test_error_handling_and_logging(self, mock_logger, db_session):
        """Test error handling and logging"""
        service = ProcessingService(db_session)
        
        # Test with invalid input
        with pytest.raises(ValidationError):
            service.process({'invalid': 'data'})
        
        # Verify error was logged
        mock_logger.error.assert_called()