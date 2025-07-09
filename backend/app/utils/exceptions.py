from typing import Optional, Dict, Any
from fastapi import HTTPException, status
import traceback

class BaseAppException(Exception):
    """Base exception for all application exceptions"""
    
    def __init__(
        self,
        message: str,
        error_code: str = "UNKNOWN_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'status_code': self.status_code
        }

class ValidationError(BaseAppException):
    """Validation error exception"""
    
    def __init__(self, message: str, field: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details or {},
            status_code=status.HTTP_400_BAD_REQUEST
        )
        if field:
            self.details['field'] = field

class NotFoundError(BaseAppException):
    """Resource not found exception"""
    
    def __init__(self, resource: str, identifier: str = None, details: Optional[Dict[str, Any]] = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        
        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            details=details or {},
            status_code=status.HTTP_404_NOT_FOUND
        )
        self.details['resource'] = resource
        if identifier:
            self.details['identifier'] = identifier

class AuthenticationError(BaseAppException):
    """Authentication error exception"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details or {},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

class AuthorizationError(BaseAppException):
    """Authorization error exception"""
    
    def __init__(self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details or {},
            status_code=status.HTTP_403_FORBIDDEN
        )

class DatabaseError(BaseAppException):
    """Database operation error exception"""
    
    def __init__(self, message: str, operation: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details or {},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        if operation:
            self.details['operation'] = operation

class ExternalServiceError(BaseAppException):
    """External service error exception"""
    
    def __init__(self, service: str, message: str = None, details: Optional[Dict[str, Any]] = None):
        message = message or f"External service '{service}' error"
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details or {},
            status_code=status.HTTP_502_BAD_GATEWAY
        )
        self.details['service'] = service

class FileProcessingError(BaseAppException):
    """File processing error exception"""
    
    def __init__(self, message: str, filename: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="FILE_PROCESSING_ERROR",
            details=details or {},
            status_code=status.HTTP_400_BAD_REQUEST
        )
        if filename:
            self.details['filename'] = filename

class AIProcessingError(BaseAppException):
    """AI processing error exception"""
    
    def __init__(self, message: str, model: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AI_PROCESSING_ERROR",
            details=details or {},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        if model:
            self.details['model'] = model

class RateLimitError(BaseAppException):
    """Rate limit exceeded exception"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details=details or {},
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

class ConfigurationError(BaseAppException):
    """Configuration error exception"""
    
    def __init__(self, message: str, setting: str = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details or {},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        if setting:
            self.details['setting'] = setting

def handle_exception(exc: Exception) -> BaseAppException:
    """Convert generic exceptions to application exceptions"""
    
    # If it's already an application exception, return as is
    if isinstance(exc, BaseAppException):
        return exc
    
    # Handle specific exception types
    if isinstance(exc, ValueError):
        return ValidationError(str(exc))
    
    if isinstance(exc, KeyError):
        return NotFoundError("Key", str(exc))
    
    if isinstance(exc, PermissionError):
        return AuthorizationError(str(exc))
    
    if isinstance(exc, FileNotFoundError):
        return NotFoundError("File", str(exc))
    
    # Generic exception handling
    return BaseAppException(
        message=str(exc),
        error_code="INTERNAL_ERROR",
        details={'exception_type': type(exc).__name__}
    )

def create_http_exception(exc: BaseAppException) -> HTTPException:
    """Convert application exception to FastAPI HTTPException"""
    
    return HTTPException(
        status_code=exc.status_code,
        detail={
            'error_code': exc.error_code,
            'message': exc.message,
            'details': exc.details
        }
    )

class ExceptionHandler:
    """Exception handler utility class"""
    
    @staticmethod
    def handle_and_log(exc: Exception, logger, operation: str = None) -> BaseAppException:
        """Handle exception with logging"""
        
        app_exc = handle_exception(exc)
        
        # Log the exception
        logger.error(f"Exception in {operation or 'operation'}: {app_exc.message}", extra={
            'error_code': app_exc.error_code,
            'exception_type': type(exc).__name__,
            'details': app_exc.details,
            'traceback': traceback.format_exc()
        })
        
        return app_exc
    
    @staticmethod
    def raise_http_exception(exc: Exception, logger, operation: str = None):
        """Handle exception and raise as HTTP exception"""
        
        app_exc = ExceptionHandler.handle_and_log(exc, logger, operation)
        raise create_http_exception(app_exc)