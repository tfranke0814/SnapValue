"""
Tests for Base Service Classes - Step 2
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid
from datetime import datetime

from app.services.base_service import BaseService


class ConcreteTestService(BaseService):
    """Test service implementation for testing base service functionality."""
    
    def validate_input(self, data):
        return isinstance(data, dict) and 'test' in data
    
    def process(self, data):
        return f"Processed: {data.get('test', 'unknown')}"


class TestBaseService:
    """Test cases for BaseService class."""
    
    def test_service_initialization(self, db_session):
        """Test service initialization."""
        service = ConcreteTestService(db=db_session)
        
        assert service.db == db_session
        assert hasattr(service, 'logger')
        assert hasattr(service, 'correlation_id')
        assert service.correlation_id is not None
        assert isinstance(service.correlation_id, str)
    
    def test_service_initialization_without_db(self):
        """Test service initialization without database session."""
        service = ConcreteTestService()
        
        assert service.db is None
        assert hasattr(service, 'logger')
        assert hasattr(service, 'correlation_id')
    
    def test_get_db_session_with_existing_db(self, db_session):
        """Test get_db_session with existing database session."""
        service = ConcreteTestService(db=db_session)
        
        with service.get_db_session() as db:
            assert db == db_session
    
    def test_get_db_session_without_existing_db(self):
        """Test get_db_session without existing database session."""
        service = ConcreteTestService()
        
        with patch('app.services.base_service.SessionLocal') as mock_session_local:
            mock_db = Mock()
            mock_session_local.return_value = mock_db
            
            with service.get_db_session() as db:
                assert db == mock_db
            
            mock_db.close.assert_called_once()
    
    def test_log_operation(self):
        """Test log_operation method."""
        service = ConcreteTestService()
        
        with patch.object(service.logger, 'info') as mock_info:
            service.log_operation('test_operation', {'key': 'value'})
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            
            assert 'Service Operation: test_operation' in args[0]
            assert 'extra' in kwargs
            
            extra_data = kwargs['extra']
            assert extra_data['operation'] == 'test_operation'
            assert extra_data['service'] == 'ConcreteTestService'
            assert extra_data['correlation_id'] == service.correlation_id
            assert 'timestamp' in extra_data
            assert extra_data['key'] == 'value'
    
    def test_log_operation_without_details(self):
        """Test log_operation without additional details."""
        service = ConcreteTestService()
        
        with patch.object(service.logger, 'info') as mock_info:
            service.log_operation('simple_operation')
            
            mock_info.assert_called_once()
            args, kwargs = mock_info.call_args
            
            extra_data = kwargs['extra']
            assert extra_data['operation'] == 'simple_operation'
            assert extra_data['service'] == 'ConcreteTestService'
            assert 'timestamp' in extra_data
    
    def test_log_error(self):
        """Test log_error method."""
        service = ConcreteTestService()
        error = ValueError("Test error")
        
        with patch.object(service.logger, 'error') as mock_error:
            service.log_error(error, 'test_operation', {'context': 'test'})
            
            mock_error.assert_called_once()
            args, kwargs = mock_error.call_args
            
            assert 'Service Error: Test error' in args[0]
            assert 'extra' in kwargs
            
            extra_data = kwargs['extra']
            assert extra_data['error'] == 'Test error'
            assert extra_data['error_type'] == 'ValueError'
            assert extra_data['service'] == 'ConcreteTestService'
            assert extra_data['correlation_id'] == service.correlation_id
            assert extra_data['operation'] == 'test_operation'
            assert extra_data['context'] == 'test'
            assert 'timestamp' in extra_data
    
    def test_log_error_minimal(self):
        """Test log_error with minimal parameters."""
        service = ConcreteTestService()
        error = RuntimeError("Runtime error")
        
        with patch.object(service.logger, 'error') as mock_error:
            service.log_error(error)
            
            mock_error.assert_called_once()
            args, kwargs = mock_error.call_args
            
            extra_data = kwargs['extra']
            assert extra_data['error'] == 'Runtime error'
            assert extra_data['error_type'] == 'RuntimeError'
            assert 'operation' not in extra_data or extra_data['operation'] is None
    
    def test_validate_input_implementation(self):
        """Test validate_input implementation."""
        service = ConcreteTestService()
        
        # Valid input
        assert service.validate_input({'test': 'value'}) is True
        
        # Invalid input
        assert service.validate_input({'other': 'value'}) is False
        assert service.validate_input('string') is False
        assert service.validate_input(None) is False
    
    def test_process_implementation(self):
        """Test process implementation."""
        service = ConcreteTestService()
        
        result = service.process({'test': 'data'})
        assert result == "Processed: data"
        
        result = service.process({'other': 'value'})
        assert result == "Processed: unknown"
    
    def test_execute_with_logging_success(self):
        """Test execute_with_logging with successful execution."""
        service = ConcreteTestService()
        
        def test_function(x, y):
            return x + y
        
        with patch.object(service, 'log_operation') as mock_log:
            result = service.execute_with_logging('add_operation', test_function, 2, 3)
            
            assert result == 5
            assert mock_log.call_count == 2
            mock_log.assert_any_call('Starting add_operation')
            mock_log.assert_any_call('Completed add_operation')
    
    def test_execute_with_logging_with_exception(self):
        """Test execute_with_logging with exception."""
        service = ConcreteTestService()
        
        def failing_function():
            raise ValueError("Test error")
        
        with patch.object(service, 'log_operation') as mock_log_op:
            with patch.object(service, 'log_error') as mock_log_error:
                with pytest.raises(ValueError, match="Test error"):
                    service.execute_with_logging('failing_operation', failing_function)
                
                mock_log_op.assert_called_once_with('Starting failing_operation')
                mock_log_error.assert_called_once()
                
                # Check the error was logged correctly
                args, kwargs = mock_log_error.call_args
                assert isinstance(args[0], ValueError)
                assert args[1] == 'failing_operation'
    
    def test_correlation_id_management(self):
        """Test correlation ID management."""
        service = ConcreteTestService()
        original_id = service.get_correlation_id()
        
        assert original_id is not None
        assert isinstance(original_id, str)
        
        # Set new correlation ID
        new_id = "test-correlation-123"
        service.set_correlation_id(new_id)
        
        assert service.get_correlation_id() == new_id
        assert service.correlation_id == new_id
    
    def test_correlation_id_uniqueness(self):
        """Test that each service instance gets a unique correlation ID."""
        service1 = ConcreteTestService()
        service2 = ConcreteTestService()
        
        assert service1.get_correlation_id() != service2.get_correlation_id()
    
    def test_logger_naming(self):
        """Test that logger is named after the service class."""
        service = ConcreteTestService()
        
        assert service.logger.name == 'ConcreteTestService'
    
    def test_abstract_methods_enforcement(self):
        """Test that abstract methods must be implemented."""
        with pytest.raises(TypeError):
            # This should fail because BaseService is abstract
            BaseService()
    
    def test_service_with_kwargs_in_execute_with_logging(self):
        """Test execute_with_logging with keyword arguments."""
        service = ConcreteTestService()
        
        def test_function(a, b, c=None, d=None):
            return f"{a}-{b}-{c}-{d}"
        
        with patch.object(service, 'log_operation'):
            result = service.execute_with_logging(
                'test_kwargs', 
                test_function, 
                'arg1', 'arg2',
                c='kwarg1', d='kwarg2'
            )
            
            assert result == "arg1-arg2-kwarg1-kwarg2"
    
    def test_generic_type_parameter(self):
        """Test that BaseService properly handles generic type parameter."""
        # This is more of a type checking test, but we can verify the service works
        service = ConcreteTestService()
        
        # The service should work with any return type from process method
        result = service.process({'test': 'value'})
        assert isinstance(result, str)
    
    def test_datetime_in_logging(self):
        """Test that datetime is properly included in log operations."""
        service = ConcreteTestService()
        
        with patch.object(service.logger, 'info') as mock_info:
            with patch('app.services.base_service.datetime') as mock_datetime:
                mock_now = datetime(2023, 1, 1, 12, 0, 0)
                mock_datetime.utcnow.return_value = mock_now
                
                service.log_operation('test_datetime')
                
                args, kwargs = mock_info.call_args
                extra_data = kwargs['extra']
                assert extra_data['timestamp'] == '2023-01-01T12:00:00'
