from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, TypeVar, Generic
from sqlalchemy.orm import Session
from contextlib import contextmanager
import logging
import uuid
from datetime import datetime

from app.database.connection import SessionLocal

T = TypeVar('T')

class BaseService(ABC, Generic[T]):
    """
    Base service class with common functionality for all services
    """
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)
        self.correlation_id = str(uuid.uuid4())
        
    @contextmanager
    def get_db_session(self):
        """Context manager for database sessions"""
        if self.db:
            yield self.db
        else:
            db = SessionLocal()
            try:
                yield db
            finally:
                db.close()
                
    def log_operation(self, operation: str, details: Dict[str, Any] = None):
        """Log service operations with correlation ID"""
        log_data = {
            'operation': operation,
            'service': self.__class__.__name__,
            'correlation_id': self.correlation_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        if details:
            log_data.update(details)
            
        self.logger.info(f"Service Operation: {operation}", extra=log_data)
        
    def log_error(self, error: Exception, operation: str = None, details: Dict[str, Any] = None):
        """Log service errors with correlation ID"""
        log_data = {
            'error': str(error),
            'error_type': type(error).__name__,
            'service': self.__class__.__name__,
            'correlation_id': self.correlation_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        if operation:
            log_data['operation'] = operation
        if details:
            log_data.update(details)
            
        self.logger.error(f"Service Error: {error}", extra=log_data)
        
    @abstractmethod
    def validate_input(self, data: Any) -> bool:
        """Validate input data - to be implemented by subclasses"""
        pass
        
    @abstractmethod
    def process(self, data: Any) -> T:
        """Main processing method - to be implemented by subclasses"""
        pass
        
    def execute_with_logging(self, operation: str, func, *args, **kwargs) -> Any:
        """Execute a function with automatic logging"""
        try:
            self.log_operation(f"Starting {operation}")
            result = func(*args, **kwargs)
            self.log_operation(f"Completed {operation}")
            return result
        except Exception as e:
            self.log_error(e, operation)
            raise
            
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request tracking"""
        self.correlation_id = correlation_id
        
    def get_correlation_id(self) -> str:
        """Get current correlation ID"""
        return self.correlation_id