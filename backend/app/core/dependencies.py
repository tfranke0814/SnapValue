from typing import Dict, Any, Optional, Type, TypeVar, Callable
from functools import lru_cache
from sqlalchemy.orm import Session
import logging

from app.database.connection import get_db

T = TypeVar('T')

class DependencyContainer:
    """
    Dependency injection container for managing service dependencies
    """
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._singletons: Dict[str, Any] = {}
        self.logger = logging.getLogger(__name__)
        
    def register_service(self, name: str, service_class: Type[T], singleton: bool = False):
        """Register a service class"""
        if singleton:
            self._singletons[name] = None
        self._services[name] = service_class
        self.logger.info(f"Registered service: {name} ({'singleton' if singleton else 'transient'})")
        
    def register_factory(self, name: str, factory: Callable[[], T]):
        """Register a factory function"""
        self._factories[name] = factory
        self.logger.info(f"Registered factory: {name}")
        
    def get_service(self, name: str, db: Optional[Session] = None) -> Any:
        """Get a service instance"""
        # Check if it's a singleton
        if name in self._singletons:
            if self._singletons[name] is None:
                self._singletons[name] = self._create_service(name, db)
            return self._singletons[name]
            
        # Create new instance
        return self._create_service(name, db)
        
    def _create_service(self, name: str, db: Optional[Session] = None) -> Any:
        """Create a service instance"""
        if name in self._factories:
            return self._factories[name]()
            
        if name in self._services:
            service_class = self._services[name]
            if db:
                return service_class(db=db)
            else:
                return service_class()
                
        raise ValueError(f"Service '{name}' not found")
        
    def clear_singletons(self):
        """Clear all singleton instances"""
        self._singletons = {k: None for k in self._singletons}
        self.logger.info("Cleared all singleton instances")

# Global dependency container instance
container = DependencyContainer()

# Dependency injection functions for FastAPI
def get_container() -> DependencyContainer:
    """Get the global dependency container"""
    return container

def get_db_session() -> Session:
    """Get database session dependency"""
    return next(get_db())

# Service factory functions
def create_service_factory(service_name: str):
    """Create a factory function for a service"""
    def factory(db: Session = None) -> Any:
        return container.get_service(service_name, db)
    return factory

# Decorator for automatic dependency injection
def inject_dependencies(*service_names):
    """Decorator for automatic dependency injection"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            db = kwargs.get('db') or next(get_db())
            for service_name in service_names:
                if service_name not in kwargs:
                    kwargs[service_name] = container.get_service(service_name, db)
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Common dependency functions
@lru_cache()
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return logging.getLogger(name)

def setup_dependencies():
    """Setup common dependencies"""
    # Register common services here
    # This will be called during app startup
    pass