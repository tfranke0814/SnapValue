from typing import Dict, Type, Any, Optional, Callable
from contextlib import contextmanager
from sqlalchemy.orm import Session
import threading
import logging

from app.core.dependencies import DependencyContainer
from app.utils.logging import get_logger
from app.utils.exceptions import ConfigurationError

class ServiceRegistry:
    """
    Service registry for managing application services
    """
    
    def __init__(self):
        self._services: Dict[str, Type] = {}
        self._instances: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._lock = threading.Lock()
        self.logger = get_logger(__name__)
        
    def register(
        self,
        service_name: str,
        service_class: Type,
        singleton: bool = False,
        factory: Optional[Callable] = None
    ):
        """Register a service"""
        with self._lock:
            if service_name in self._services:
                self.logger.warning(f"Service '{service_name}' already registered, overwriting")
            
            self._services[service_name] = service_class
            
            if singleton:
                self._singletons[service_name] = None
                
            if factory:
                self._factories[service_name] = factory
                
            self.logger.info(f"Registered service: {service_name} ({'singleton' if singleton else 'transient'})")
    
    def get(self, service_name: str, db: Optional[Session] = None) -> Any:
        """Get a service instance"""
        with self._lock:
            # Check if it's a singleton
            if service_name in self._singletons:
                if self._singletons[service_name] is None:
                    self._singletons[service_name] = self._create_instance(service_name, db)
                return self._singletons[service_name]
            
            # Return new instance
            return self._create_instance(service_name, db)
    
    def _create_instance(self, service_name: str, db: Optional[Session] = None) -> Any:
        """Create a service instance"""
        if service_name not in self._services:
            raise ConfigurationError(f"Service '{service_name}' not registered")
        
        # Use factory if available
        if service_name in self._factories:
            return self._factories[service_name](db)
        
        # Create instance from class
        service_class = self._services[service_name]
        try:
            if db:
                return service_class(db=db)
            else:
                return service_class()
        except Exception as e:
            self.logger.error(f"Failed to create service '{service_name}': {e}")
            raise ConfigurationError(f"Failed to create service '{service_name}': {e}")
    
    def is_registered(self, service_name: str) -> bool:
        """Check if a service is registered"""
        return service_name in self._services
    
    def get_registered_services(self) -> Dict[str, Type]:
        """Get all registered services"""
        return self._services.copy()
    
    def clear_singletons(self):
        """Clear all singleton instances"""
        with self._lock:
            self._singletons = {k: None for k in self._singletons}
            self.logger.info("Cleared all singleton instances")
    
    def unregister(self, service_name: str):
        """Unregister a service"""
        with self._lock:
            if service_name in self._services:
                del self._services[service_name]
                self._singletons.pop(service_name, None)
                self._factories.pop(service_name, None)
                self.logger.info(f"Unregistered service: {service_name}")

# Global service registry instance
registry = ServiceRegistry()

# Decorator for automatic service registration
def register_service(name: str, singleton: bool = False):
    """Decorator for automatic service registration"""
    def decorator(service_class: Type):
        registry.register(name, service_class, singleton)
        return service_class
    return decorator

# Context manager for service lifecycle
@contextmanager
def service_scope(service_name: str, db: Optional[Session] = None):
    """Context manager for service lifecycle"""
    service = registry.get(service_name, db)
    try:
        yield service
    finally:
        # Cleanup if needed
        if hasattr(service, 'cleanup'):
            service.cleanup()

# Service factory functions
def create_service_factory(service_class: Type):
    """Create a factory function for a service"""
    def factory(db: Optional[Session] = None):
        if db:
            return service_class(db=db)
        return service_class()
    return factory

# Integration with dependency container
def setup_service_registry(container: DependencyContainer):
    """Setup service registry with dependency container"""
    
    # Register services from registry to container
    for service_name, service_class in registry.get_registered_services().items():
        is_singleton = service_name in registry._singletons
        container.register_service(service_name, service_class, is_singleton)
    
    # Register factories
    for service_name, factory in registry._factories.items():
        container.register_factory(service_name, factory)

# Common service initialization
def initialize_services():
    """Initialize common services"""
    # This will be populated as services are created
    pass

# Health check for services
def check_service_health() -> Dict[str, bool]:
    """Check health of all registered services"""
    health_status = {}
    
    for service_name in registry.get_registered_services().keys():
        try:
            service = registry.get(service_name)
            if hasattr(service, 'health_check'):
                health_status[service_name] = service.health_check()
            else:
                health_status[service_name] = True
        except Exception as e:
            registry.logger.error(f"Health check failed for service '{service_name}': {e}")
            health_status[service_name] = False
    
    return health_status