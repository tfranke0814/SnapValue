"""
Tests for Dependency Injection - Step 2
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import DependencyContainer


class MockService:
    """Mock service for testing dependency injection."""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.initialized = True
    
    def get_data(self):
        return "mock_data"


class MockSingletonService:
    """Mock singleton service for testing."""
    
    def __init__(self):
        self.creation_count = 0
        self.initialized = True
    
    def increment(self):
        self.creation_count += 1
        return self.creation_count


class TestDependencyContainer:
    """Test cases for DependencyContainer."""
    
    def test_container_initialization(self):
        """Test dependency container initialization."""
        container = DependencyContainer()
        
        assert hasattr(container, '_services')
        assert hasattr(container, '_factories')
        assert hasattr(container, '_singletons')
        assert hasattr(container, 'logger')
        assert isinstance(container._services, dict)
        assert isinstance(container._factories, dict)
        assert isinstance(container._singletons, dict)
    
    def test_register_service_transient(self):
        """Test registering a transient service."""
        container = DependencyContainer()
        
        with patch.object(container.logger, 'info') as mock_log:
            container.register_service('mock_service', MockService, singleton=False)
            
            assert 'mock_service' in container._services
            assert container._services['mock_service'] == MockService
            assert 'mock_service' not in container._singletons
            
            mock_log.assert_called_once()
            log_message = mock_log.call_args[0][0]
            assert 'mock_service' in log_message
            assert 'transient' in log_message
    
    def test_register_service_singleton(self):
        """Test registering a singleton service."""
        container = DependencyContainer()
        
        with patch.object(container.logger, 'info') as mock_log:
            container.register_service('singleton_service', MockSingletonService, singleton=True)
            
            assert 'singleton_service' in container._services
            assert 'singleton_service' in container._singletons
            assert container._singletons['singleton_service'] is None  # Not created yet
            
            mock_log.assert_called_once()
            log_message = mock_log.call_args[0][0]
            assert 'singleton_service' in log_message
            assert 'singleton' in log_message
    
    def test_register_factory(self):
        """Test registering a factory function."""
        container = DependencyContainer()
        
        def mock_factory():
            return MockService()
        
        with patch.object(container.logger, 'info') as mock_log:
            container.register_factory('factory_service', mock_factory)
            
            assert 'factory_service' in container._factories
            assert container._factories['factory_service'] == mock_factory
            
            mock_log.assert_called_once()
            log_message = mock_log.call_args[0][0]
            assert 'factory_service' in log_message
    
    def test_get_service_transient(self, db_session):
        """Test getting a transient service instance."""
        container = DependencyContainer()
        container.register_service('mock_service', MockService, singleton=False)
        
        # Get two instances
        service1 = container.get_service('mock_service', db=db_session)
        service2 = container.get_service('mock_service', db=db_session)
        
        # Should be different instances
        assert isinstance(service1, MockService)
        assert isinstance(service2, MockService)
        assert service1 is not service2
        assert service1.db == db_session
        assert service2.db == db_session
    
    def test_get_service_singleton(self):
        """Test getting a singleton service instance."""
        container = DependencyContainer()
        container.register_service('singleton_service', MockSingletonService, singleton=True)
        
        # Get two instances
        service1 = container.get_service('singleton_service')
        service2 = container.get_service('singleton_service')
        
        # Should be the same instance
        assert isinstance(service1, MockSingletonService)
        assert isinstance(service2, MockSingletonService)
        assert service1 is service2
    
    def test_get_service_factory(self):
        """Test getting a service from factory."""
        container = DependencyContainer()
        
        def mock_factory():
            service = MockService()
            service.factory_created = True
            return service
        
        container.register_factory('factory_service', mock_factory)
        
        service = container.get_service('factory_service')
        
        assert isinstance(service, MockService)
        assert hasattr(service, 'factory_created')
        assert service.factory_created is True
    
    def test_get_service_nonexistent(self):
        """Test getting a non-existent service."""
        container = DependencyContainer()
        
        with pytest.raises(ValueError, match="Service 'nonexistent_service' not found"):
            container.get_service('nonexistent_service')
    
    def test_create_service_with_db(self, db_session):
        """Test _create_service method with database session."""
        container = DependencyContainer()
        container.register_service('mock_service', MockService)
        
        service = container._create_service('mock_service', db=db_session)
        
        assert isinstance(service, MockService)
        assert service.db == db_session
    
    def test_create_service_without_db(self):
        """Test _create_service method without database session."""
        container = DependencyContainer()
        container.register_service('mock_service', MockSingletonService)  # No db parameter
        
        service = container._create_service('mock_service')
        
        assert isinstance(service, MockSingletonService)
    
    def test_create_service_factory_priority(self):
        """Test that factory takes priority over service class."""
        container = DependencyContainer()
        
        # Register both service class and factory with same name
        container.register_service('test_service', MockService)
        
        def custom_factory():
            service = MockService()
            service.from_factory = True
            return service
        
        container.register_factory('test_service', custom_factory)
        
        service = container._create_service('test_service')
        
        assert isinstance(service, MockService)
        assert hasattr(service, 'from_factory')
        assert service.from_factory is True
    
    def test_singleton_lazy_initialization(self):
        """Test that singletons are lazily initialized."""
        container = DependencyContainer()
        container.register_service('lazy_singleton', MockSingletonService, singleton=True)
        
        # Singleton should not be created yet
        assert container._singletons['lazy_singleton'] is None
        
        # First access should create it
        service1 = container.get_service('lazy_singleton')
        assert container._singletons['lazy_singleton'] is not None
        assert container._singletons['lazy_singleton'] is service1
        
        # Second access should return the same instance
        service2 = container.get_service('lazy_singleton')
        assert service1 is service2
    
    def test_service_with_constructor_parameters(self, db_session):
        """Test service creation with constructor parameters."""
        
        class ParameterizedService:
            def __init__(self, db: Optional[Session] = None, config: str = "default"):
                self.db = db
                self.config = config
        
        container = DependencyContainer()
        container.register_service('param_service', ParameterizedService)
        
        service = container.get_service('param_service', db=db_session)
        
        assert isinstance(service, ParameterizedService)
        assert service.db == db_session
        assert service.config == "default"
    
    def test_container_isolation(self):
        """Test that different container instances are isolated."""
        container1 = DependencyContainer()
        container2 = DependencyContainer()
        
        container1.register_service('test_service', MockService)
        
        # container2 should not have the service
        with pytest.raises(ValueError, match="Service 'test_service' not found"):
            container2.get_service('test_service')
        
        # container1 should have the service
        service = container1.get_service('test_service')
        assert isinstance(service, MockService)
    
    def test_service_registration_overwrite(self):
        """Test that service registration can overwrite existing services."""
        container = DependencyContainer()
        
        # Register first service
        container.register_service('test_service', MockService)
        
        # Register different service with same name
        container.register_service('test_service', MockSingletonService)
        
        service = container.get_service('test_service')
        assert isinstance(service, MockSingletonService)
        assert not isinstance(service, MockService)
    
    def test_factory_registration_overwrite(self):
        """Test that factory registration can overwrite existing factories."""
        container = DependencyContainer()
        
        def factory1():
            service = MockService()
            service.factory_version = 1
            return service
        
        def factory2():
            service = MockService()
            service.factory_version = 2
            return service
        
        container.register_factory('test_factory', factory1)
        container.register_factory('test_factory', factory2)
        
        service = container.get_service('test_factory')
        assert service.factory_version == 2
    
    def test_error_handling_in_service_creation(self):
        """Test error handling during service creation."""
        
        class FailingService:
            def __init__(self):
                raise ValueError("Service creation failed")
        
        container = DependencyContainer()
        container.register_service('failing_service', FailingService)
        
        # Should raise the original exception
        with pytest.raises(ValueError, match="Service creation failed"):
            container.get_service('failing_service')
    
    def test_error_handling_in_factory(self):
        """Test error handling during factory execution."""
        container = DependencyContainer()
        
        def failing_factory():
            raise RuntimeError("Factory execution failed")
        
        container.register_factory('failing_factory', failing_factory)
        
        # Should raise the original exception
        with pytest.raises(RuntimeError, match="Factory execution failed"):
            container.get_service('failing_factory')
    
    def test_logger_usage(self):
        """Test that container uses logger appropriately."""
        container = DependencyContainer()
        
        # Test service registration logging
        with patch.object(container.logger, 'info') as mock_log:
            container.register_service('test_service', MockService, singleton=True)
            mock_log.assert_called_once()
        
        # Test factory registration logging
        with patch.object(container.logger, 'info') as mock_log:
            container.register_factory('test_factory', lambda: MockService())
            mock_log.assert_called_once()


class TestDependencyContainerEdgeCases:
    """Test edge cases for DependencyContainer."""
    
    def test_none_service_class(self):
        """Test handling of None service class."""
        container = DependencyContainer()
        
        # This should work but service creation will fail
        container.register_service('none_service', None)
        
        with pytest.raises(TypeError):
            container.get_service('none_service')
    
    def test_none_factory(self):
        """Test handling of None factory."""
        container = DependencyContainer()
        
        # This should work but factory execution will fail
        container.register_factory('none_factory', None)
        
        with pytest.raises(TypeError):
            container.get_service('none_factory')
    
    def test_empty_service_name(self):
        """Test registration with empty service name."""
        container = DependencyContainer()
        
        container.register_service('', MockService)
        service = container.get_service('')
        
        assert isinstance(service, MockService)
    
    def test_service_without_optional_db_parameter(self):
        """Test service that doesn't accept db parameter."""
        
        class NoDbService:
            def __init__(self):
                self.created = True
        
        container = DependencyContainer()
        container.register_service('no_db_service', NoDbService)
        
        # Should fail gracefully when db is passed to service that doesn't accept it
        with pytest.raises(TypeError):
            container.get_service('no_db_service', db=Mock())
