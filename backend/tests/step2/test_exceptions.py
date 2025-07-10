"""
Tests for Custom Exceptions - Step 2
"""
import pytest
from fastapi import status

from app.utils.exceptions import (
    BaseAppException,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    AuthorizationError,
    DatabaseError,
    ExternalServiceError,
    FileProcessingError,
    RateLimitError,
    ConfigurationError
)


class TestBaseAppException:
    """Test cases for BaseAppException."""
    
    def test_base_exception_creation(self):
        """Test basic exception creation."""
        exception = BaseAppException(
            message="Test error",
            error_code="TEST_ERROR",
            details={'key': 'value'},
            status_code=status.HTTP_400_BAD_REQUEST
        )
        
        assert exception.message == "Test error"
        assert exception.error_code == "TEST_ERROR"
        assert exception.details == {'key': 'value'}
        assert exception.status_code == status.HTTP_400_BAD_REQUEST
        assert str(exception) == "Test error"
    
    def test_base_exception_defaults(self):
        """Test base exception with default values."""
        exception = BaseAppException("Simple error")
        
        assert exception.message == "Simple error"
        assert exception.error_code == "UNKNOWN_ERROR"
        assert exception.details == {}
        assert exception.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_to_dict_method(self):
        """Test to_dict method."""
        exception = BaseAppException(
            message="Test error",
            error_code="TEST_ERROR",
            details={'context': 'testing'},
            status_code=status.HTTP_400_BAD_REQUEST
        )
        
        result = exception.to_dict()
        expected = {
            'error_code': 'TEST_ERROR',
            'message': 'Test error',
            'details': {'context': 'testing'},
            'status_code': status.HTTP_400_BAD_REQUEST
        }
        
        assert result == expected


class TestValidationError:
    """Test cases for ValidationError."""
    
    def test_validation_error_creation(self):
        """Test validation error creation."""
        error = ValidationError("Invalid input", field="email")
        
        assert error.message == "Invalid input"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.details['field'] == "email"
    
    def test_validation_error_without_field(self):
        """Test validation error without field specification."""
        error = ValidationError("General validation error")
        
        assert error.message == "General validation error"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert 'field' not in error.details
    
    def test_validation_error_with_details(self):
        """Test validation error with additional details."""
        details = {'allowed_values': ['A', 'B', 'C']}
        error = ValidationError("Invalid choice", field="category", details=details)
        
        assert error.details['field'] == "category"
        assert error.details['allowed_values'] == ['A', 'B', 'C']


class TestNotFoundError:
    """Test cases for NotFoundError."""
    
    def test_not_found_error_with_identifier(self):
        """Test not found error with identifier."""
        error = NotFoundError("User", "123")
        
        assert error.message == "User with id '123' not found"
        assert error.error_code == "NOT_FOUND"
        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert error.details['resource'] == "User"
        assert error.details['identifier'] == "123"
    
    def test_not_found_error_without_identifier(self):
        """Test not found error without identifier."""
        error = NotFoundError("Settings")
        
        assert error.message == "Settings not found"
        assert error.error_code == "NOT_FOUND"
        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert error.details['resource'] == "Settings"
        assert 'identifier' not in error.details
    
    def test_not_found_error_with_details(self):
        """Test not found error with additional details."""
        details = {'search_criteria': {'name': 'test', 'active': True}}
        error = NotFoundError("Product", details=details)
        
        assert error.details['resource'] == "Product"
        assert error.details['search_criteria'] == {'name': 'test', 'active': True}


class TestAuthenticationError:
    """Test cases for AuthenticationError."""
    
    def test_authentication_error_default(self):
        """Test authentication error with default message."""
        error = AuthenticationError()
        
        assert error.message == "Authentication failed"
        assert error.error_code == "AUTHENTICATION_ERROR"
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_authentication_error_custom_message(self):
        """Test authentication error with custom message."""
        error = AuthenticationError("Invalid credentials")
        
        assert error.message == "Invalid credentials"
        assert error.error_code == "AUTHENTICATION_ERROR"
        assert error.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_authentication_error_with_details(self):
        """Test authentication error with details."""
        details = {'reason': 'token_expired', 'expires_at': '2023-01-01T00:00:00Z'}
        error = AuthenticationError("Token expired", details=details)
        
        assert error.details['reason'] == 'token_expired'
        assert error.details['expires_at'] == '2023-01-01T00:00:00Z'


class TestAuthorizationError:
    """Test cases for AuthorizationError."""
    
    def test_authorization_error_default(self):
        """Test authorization error with default message."""
        error = AuthorizationError()
        
        assert error.message == "Access denied"
        assert error.error_code == "AUTHORIZATION_ERROR"
        assert error.status_code == status.HTTP_403_FORBIDDEN
    
    def test_authorization_error_custom_message(self):
        """Test authorization error with custom message."""
        error = AuthorizationError("Insufficient permissions")
        
        assert error.message == "Insufficient permissions"
        assert error.error_code == "AUTHORIZATION_ERROR"
        assert error.status_code == status.HTTP_403_FORBIDDEN
    
    def test_authorization_error_with_details(self):
        """Test authorization error with details."""
        details = {
            'required_permissions': ['read:users', 'write:users'],
            'user_permissions': ['read:users']
        }
        error = AuthorizationError("Missing permissions", details=details)
        
        assert error.details['required_permissions'] == ['read:users', 'write:users']
        assert error.details['user_permissions'] == ['read:users']


class TestDatabaseError:
    """Test cases for DatabaseError."""
    
    def test_database_error_basic(self):
        """Test basic database error."""
        error = DatabaseError("Connection failed")
        
        assert error.message == "Connection failed"
        assert error.error_code == "DATABASE_ERROR"
        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    def test_database_error_with_operation(self):
        """Test database error with operation specification."""
        error = DatabaseError("Unique constraint violation", operation="insert_user")
        
        assert error.message == "Unique constraint violation"
        assert error.details['operation'] == "insert_user"
    
    def test_database_error_with_details(self):
        """Test database error with additional details."""
        details = {'table': 'users', 'constraint': 'email_unique'}
        error = DatabaseError("Constraint violation", operation="insert", details=details)
        
        assert error.details['operation'] == "insert"
        assert error.details['table'] == "users"
        assert error.details['constraint'] == "email_unique"


class TestExternalServiceError:
    """Test cases for ExternalServiceError."""
    
    def test_external_service_error_default_message(self):
        """Test external service error with default message."""
        error = ExternalServiceError("Google Vision API")
        
        assert error.message == "External service 'Google Vision API' error"
        assert error.error_code == "EXTERNAL_SERVICE_ERROR"
        assert error.status_code == status.HTTP_502_BAD_GATEWAY
        assert error.details['service'] == "Google Vision API"
    
    def test_external_service_error_custom_message(self):
        """Test external service error with custom message."""
        error = ExternalServiceError("Payment Gateway", "Payment processing failed")
        
        assert error.message == "Payment processing failed"
        assert error.error_code == "EXTERNAL_SERVICE_ERROR"
        assert error.details['service'] == "Payment Gateway"
    
    def test_external_service_error_with_details(self):
        """Test external service error with additional details."""
        details = {
            'status_code': 503,
            'response_body': 'Service Unavailable',
            'retry_after': 60
        }
        error = ExternalServiceError("API Service", details=details)
        
        assert error.details['service'] == "API Service"
        assert error.details['status_code'] == 503
        assert error.details['response_body'] == 'Service Unavailable'
        assert error.details['retry_after'] == 60


class TestFileProcessingError:
    """Test cases for FileProcessingError if it exists."""
    
    def test_file_processing_error_creation(self):
        """Test file processing error creation."""
        try:
            error = FileProcessingError("Invalid file format", filename="test.txt")
            
            assert error.message == "Invalid file format"
            assert error.error_code == "FILE_PROCESSING_ERROR"
            assert error.status_code == status.HTTP_400_BAD_REQUEST
            assert error.details['filename'] == "test.txt"
        except NameError:
            # FileProcessingError might not be implemented yet
            pytest.skip("FileProcessingError not implemented")


class TestRateLimitError:
    """Test cases for RateLimitError if it exists."""
    
    def test_rate_limit_error_creation(self):
        """Test rate limit error creation."""
        try:
            error = RateLimitError("Rate limit exceeded", details={"limit": 100, "window": 60})
            
            assert error.message == "Rate limit exceeded"
            assert error.error_code == "RATE_LIMIT_ERROR"
            assert error.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            assert error.details['limit'] == 100
            assert error.details['window'] == 60
        except NameError:
            # RateLimitError might not be implemented yet
            pytest.skip("RateLimitError not implemented")


class TestConfigurationError:
    """Test cases for ConfigurationError if it exists."""
    
    def test_configuration_error_creation(self):
        """Test configuration error creation."""
        try:
            error = ConfigurationError("Missing required configuration", setting="DATABASE_URL")
            
            assert error.message == "Missing required configuration"
            assert error.error_code == "CONFIGURATION_ERROR"
            assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert error.details['setting'] == "DATABASE_URL"
        except NameError:
            # ConfigurationError might not be implemented yet
            pytest.skip("ConfigurationError not implemented")


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""
    
    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from BaseAppException."""
        exceptions = [
            ValidationError("test"),
            NotFoundError("test"),
            AuthenticationError("test"),
            AuthorizationError("test"),
            DatabaseError("test"),
            ExternalServiceError("test", "test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, BaseAppException)
            assert isinstance(exc, Exception)
    
    def test_exception_str_method(self):
        """Test that all exceptions can be converted to string."""
        exceptions = [
            ValidationError("validation error"),
            NotFoundError("resource", "123"),
            AuthenticationError("auth error"),
            AuthorizationError("authz error"),
            DatabaseError("db error"),
            ExternalServiceError("service", "service error")
        ]
        
        for exc in exceptions:
            str_repr = str(exc)
            assert isinstance(str_repr, str)
            assert len(str_repr) > 0
    
    def test_exception_to_dict_consistency(self):
        """Test that all exceptions have consistent to_dict output."""
        exceptions = [
            ValidationError("validation error"),
            NotFoundError("resource", "123"),
            AuthenticationError("auth error"),
            AuthorizationError("authz error"),
            DatabaseError("db error"),
            ExternalServiceError("service", "service error")
        ]
        
        for exc in exceptions:
            dict_repr = exc.to_dict()
            
            # All exceptions should have these fields
            assert 'error_code' in dict_repr
            assert 'message' in dict_repr
            assert 'details' in dict_repr
            assert 'status_code' in dict_repr
            
            # Validate types
            assert isinstance(dict_repr['error_code'], str)
            assert isinstance(dict_repr['message'], str)
            assert isinstance(dict_repr['details'], dict)
            assert isinstance(dict_repr['status_code'], int)
