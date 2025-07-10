import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
import uuid

from app.core.config import settings

# Context variable for correlation ID
correlation_id_var: ContextVar[str] = ContextVar('correlation_id', default='')

class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records"""
    
    def filter(self, record):
        record.correlation_id = correlation_id_var.get() or str(uuid.uuid4())
        return True

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': getattr(record, 'correlation_id', ''),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'message', 'correlation_id']:
                log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

class StandardFormatter(logging.Formatter):
    """Standard formatter with correlation ID"""
    
    def __init__(self):
        super().__init__(
            fmt='%(asctime)s [%(levelname)s] %(name)s - %(correlation_id)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

def setup_logging():
    """Setup application logging"""
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Set formatter based on configuration
    if settings.LOG_FORMAT.lower() == 'json':
        formatter = JSONFormatter()
    else:
        formatter = StandardFormatter()
    
    handler.setFormatter(formatter)
    
    # Add correlation ID filter
    correlation_filter = CorrelationIdFilter()
    handler.addFilter(correlation_filter)
    
    root_logger.addHandler(handler)
    
    # Add file handler if configured
    if settings.LOG_FILE:
        file_handler = logging.FileHandler(settings.LOG_FILE)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(
        logging.INFO if settings.SQL_ECHO else logging.WARNING
    )

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)

def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context"""
    correlation_id_var.set(correlation_id)

def get_correlation_id() -> str:
    """Get current correlation ID"""
    return correlation_id_var.get()

def generate_correlation_id() -> str:
    """Generate a new correlation ID"""
    return str(uuid.uuid4())

class LoggerMixin:
    """Mixin to add logging capabilities to classes"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class"""
        return get_logger(self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs):
        """Log info message with extra data"""
        self.logger.info(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with extra data"""
        self.logger.warning(message, extra=kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message with extra data"""
        self.logger.error(message, extra=kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with extra data"""
        self.logger.debug(message, extra=kwargs)

def log_service_call(service_name: str, method_name: str, **kwargs):
    """Log a service method call"""
    logger = get_logger(f"service.{service_name}")
    logger.info(f"Calling {method_name}", extra={
        'service': service_name,
        'method': method_name,
        **kwargs
    })

def log_service_result(service_name: str, method_name: str, success: bool, **kwargs):
    """Log a service method result"""
    logger = get_logger(f"service.{service_name}")
    level = logging.INFO if success else logging.ERROR
    message = f"Completed {method_name}" if success else f"Failed {method_name}"
    logger.log(level, message, extra={
        'service': service_name,
        'method': method_name,
        'success': success,
        **kwargs
    })