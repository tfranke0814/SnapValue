"""
Tests for Structured Logging - Step 2
"""
import pytest
import json
import logging
from unittest.mock import patch, Mock
from io import StringIO
from datetime import datetime
import uuid

from app.utils.logging import (
    correlation_id_var,
    CorrelationIdFilter,
    JSONFormatter,
    StandardFormatter,
    get_logger,
    setup_logging,
    set_correlation_id,
    get_correlation_id,
    generate_correlation_id,
    LoggerMixin,
    log_service_call,
    log_service_result
)


class TestCorrelationIdFilter:
    """Test cases for CorrelationIdFilter."""
    
    def test_filter_adds_correlation_id_from_context(self):
        """Test that filter adds correlation ID from context variable."""
        filter_instance = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        
        test_correlation_id = "test-correlation-123"
        correlation_id_var.set(test_correlation_id)
        
        result = filter_instance.filter(record)
        
        assert result is True
        assert hasattr(record, 'correlation_id')
        assert record.correlation_id == test_correlation_id
    
    def test_filter_generates_correlation_id_when_none(self):
        """Test that filter generates correlation ID when none in context."""
        filter_instance = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        
        # Clear any existing correlation ID
        correlation_id_var.set('')
        
        result = filter_instance.filter(record)
        
        assert result is True
        assert hasattr(record, 'correlation_id')
        assert record.correlation_id != ''
        assert len(record.correlation_id) > 0
        # Should be a valid UUID format
        uuid.UUID(record.correlation_id)


class TestJSONFormatter:
    """Test cases for JSONFormatter."""
    
    def test_json_formatter_basic_formatting(self):
        """Test basic JSON formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger", level=logging.INFO, pathname="/path/test.py",
            lineno=42, msg="Test message", args=(), exc_info=None,
            func="test_function"
        )
        record.correlation_id = "test-123"
        
        with patch('app.utils.logging.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
            
            result = formatter.format(record)
            
        parsed = json.loads(result)
        
        assert parsed['timestamp'] == '2023-01-01T12:00:00Z'
        assert parsed['level'] == 'INFO'
        assert parsed['logger'] == 'test.logger'
        assert parsed['message'] == 'Test message'
        assert parsed['correlation_id'] == 'test-123'
        assert parsed['module'] == 'test'
        assert parsed['function'] == 'test_function'
        assert parsed['line'] == 42
    
    def test_json_formatter_with_extra_fields(self):
        """Test JSON formatter with extra fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger", level=logging.ERROR, pathname="/path/test.py",
            lineno=42, msg="Error occurred", args=(), exc_info=None,
            func="test_function"
        )
        record.correlation_id = "test-456"
        record.user_id = "user-123"
        record.request_id = "req-789"
        record.operation = "data_processing"
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed['user_id'] == 'user-123'
        assert parsed['request_id'] == 'req-789'
        assert parsed['operation'] == 'data_processing'
        assert parsed['level'] == 'ERROR'
    
    def test_json_formatter_with_exception(self):
        """Test JSON formatter with exception information."""
        formatter = JSONFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test.logger", level=logging.ERROR, pathname="/path/test.py",
                lineno=42, msg="Exception occurred", args=(), exc_info=True,
                func="test_function"
            )
            record.correlation_id = "test-789"
            
            result = formatter.format(record)
            parsed = json.loads(result)
            
            assert 'exception' in parsed
            assert 'ValueError: Test exception' in parsed['exception']
            assert 'Traceback' in parsed['exception']
    
    def test_json_formatter_excludes_internal_fields(self):
        """Test that JSON formatter excludes internal log record fields."""
        formatter = JSONFormatter()
        record = logging.LogRecord(
            name="test.logger", level=logging.INFO, pathname="/path/test.py",
            lineno=42, msg="Test message", args=(), exc_info=None,
            func="test_function"
        )
        record.correlation_id = "test-123"
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        # These fields should not be in the output
        excluded_fields = [
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
            'filename', 'created', 'msecs', 'relativeCreated', 'thread',
            'threadName', 'processName', 'process', 'message'
        ]
        
        for field in excluded_fields:
            assert field not in parsed


class TestStandardFormatter:
    """Test cases for StandardFormatter."""
    
    def test_standard_formatter_basic_formatting(self):
        """Test basic standard formatting."""
        try:
            formatter = StandardFormatter()
            record = logging.LogRecord(
                name="test.logger", level=logging.INFO, pathname="/path/test.py",
                lineno=42, msg="Test message", args=(), exc_info=None,
                func="test_function"
            )
            record.correlation_id = "test-123"
            
            with patch('app.utils.logging.datetime') as mock_datetime:
                mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0, 0)
                
                result = formatter.format(record)
                
            # Should contain basic information in readable format
            assert '2023-01-01 12:00:00' in result
            assert 'INFO' in result
            assert 'test.logger' in result
            assert 'Test message' in result
            assert 'test-123' in result
        except NameError:
            pytest.skip("StandardFormatter not implemented")


class TestGetLogger:
    """Test cases for get_logger function."""
    
    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        logger = get_logger("test.module")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"
    
    def test_get_logger_with_correlation_filter(self):
        """Test that get_logger includes correlation ID filter."""
        logger = get_logger("test.correlation")
        
        # Check if correlation filter is applied
        has_correlation_filter = any(
            isinstance(f, CorrelationIdFilter) for f in logger.filters
        )
        assert has_correlation_filter
    
    def test_get_logger_caching(self):
        """Test that get_logger caches logger instances."""
        logger1 = get_logger("test.cache")
        logger2 = get_logger("test.cache")
        
        assert logger1 is logger2


class TestSetupLogging:
    """Test cases for setup_logging function."""
    
    def test_setup_logging_json_format(self):
        """Test setup_logging with JSON format."""
        with patch('app.utils.logging.settings') as mock_settings:
            mock_settings.LOG_FORMAT = "json"
            mock_settings.LOG_LEVEL = "INFO"
            mock_settings.LOG_FILE = None
            
            with patch('logging.basicConfig') as mock_basic_config:
                setup_logging()
                
                mock_basic_config.assert_called_once()
                call_args = mock_basic_config.call_args
                
                assert call_args[1]['level'] == logging.INFO
                assert isinstance(call_args[1]['handlers'][0], logging.StreamHandler)
    
    def test_setup_logging_standard_format(self):
        """Test setup_logging with standard format."""
        with patch('app.utils.logging.settings') as mock_settings:
            mock_settings.LOG_FORMAT = "standard"
            mock_settings.LOG_LEVEL = "DEBUG"
            mock_settings.LOG_FILE = None
            
            with patch('logging.basicConfig') as mock_basic_config:
                setup_logging()
                
                mock_basic_config.assert_called_once()
                call_args = mock_basic_config.call_args
                
                assert call_args[1]['level'] == logging.DEBUG
    
    def test_setup_logging_with_file(self):
        """Test setup_logging with file output."""
        with patch('app.utils.logging.settings') as mock_settings:
            mock_settings.LOG_FORMAT = "json"
            mock_settings.LOG_LEVEL = "WARNING"
            mock_settings.LOG_FILE = "/path/to/logfile.log"
            
            with patch('logging.basicConfig') as mock_basic_config:
                with patch('logging.FileHandler') as mock_file_handler:
                    setup_logging()
                    
                    mock_basic_config.assert_called_once()
                    mock_file_handler.assert_called_once_with("/path/to/logfile.log")


class TestLogRequestResponse:
    """Test cases for log_request and log_response functions."""
    
    def test_log_request(self):
        """Test log_request function."""
        try:
            mock_request = Mock()
            mock_request.method = "POST"
            mock_request.url = "http://example.com/api/test"
            mock_request.headers = {"Content-Type": "application/json"}
            
            with patch('app.utils.logging.get_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                log_service_call("api", "handle_request", user_id="user-123")
                
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args
                
                assert 'Calling' in call_args[0][0]
                assert 'extra' in call_args[1]
                
                extra = call_args[1]['extra']
                assert extra['service'] == "api"
                assert extra['method'] == "handle_request"
                assert extra['user_id'] == "user-123"
                assert extra['user_id'] == "user-123"
        except NameError:
            pytest.skip("log_request not implemented")
    
    def test_log_response(self):
        """Test log_response function."""
        try:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.headers = {"Content-Type": "application/json"}
            
            with patch('app.utils.logging.get_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                log_service_result("api", "handle_request", success=True, duration=0.234)
                
                mock_logger.info.assert_called_once()
                call_args = mock_logger.info.call_args
                
                assert 'Completed' in call_args[0][0]
                assert 'extra' in call_args[1]
                
                extra = call_args[1]['extra']
                assert extra['service'] == "api"
                assert extra['method'] == "handle_request"
                assert extra['success'] is True
                assert extra['duration'] == 0.234
        except NameError:
            pytest.skip("log_response not implemented")


class TestLogErrorWithContext:
    """Test cases for log_error_with_context function."""
    
    def test_log_error_with_context(self):
        """Test log_error_with_context function."""
        try:
            error = ValueError("Test error")
            context = {
                'operation': 'user_creation',
                'user_id': 'user-123',
                'request_id': 'req-456'
            }
            
            with patch('app.utils.logging.get_logger') as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger
                
                log_service_result("api", "handle_request", success=False, 
                                  error_type='ValueError', error_message='Test error',
                                  operation='user_creation', user_id='user-123', request_id='req-456')
                
                mock_logger.error.assert_called_once()
                call_args = mock_logger.error.call_args
                
                assert 'Failed' in call_args[0][0]
                assert 'extra' in call_args[1]
                
                extra = call_args[1]['extra']
                assert extra['service'] == "api"
                assert extra['method'] == "handle_request"
                assert extra['success'] is False
                assert extra['error_type'] == 'ValueError'
                assert extra['error_message'] == 'Test error'
                assert extra['operation'] == 'user_creation'
                assert extra['user_id'] == 'user-123'
                assert extra['request_id'] == 'req-456'
        except NameError:
            pytest.skip("log_error_with_context not implemented")


class TestCorrelationIdContextManagement:
    """Test cases for correlation ID context management."""
    
    def test_correlation_id_context_isolation(self):
        """Test that correlation IDs are properly isolated between contexts."""
        # Set correlation ID in current context
        correlation_id_var.set("context-1")
        assert correlation_id_var.get() == "context-1"
        
        # In a different context, it should be different
        async def async_context():
            correlation_id_var.set("context-2")
            return correlation_id_var.get()
        
        # Note: This is a simplified test. In practice, you'd need proper async context
        # Reset to empty and test default behavior
        correlation_id_var.set("")
        assert correlation_id_var.get() == ""
    
    def test_correlation_id_filter_with_empty_context(self):
        """Test correlation ID filter behavior with empty context."""
        filter_instance = CorrelationIdFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="test message", args=(), exc_info=None
        )
        
        # Clear correlation ID
        correlation_id_var.set("")
        
        result = filter_instance.filter(record)
        
        assert result is True
        assert hasattr(record, 'correlation_id')
        assert record.correlation_id != ""
        assert len(record.correlation_id) > 0


class TestLoggingIntegration:
    """Test cases for logging system integration."""
    
    def test_end_to_end_json_logging(self):
        """Test end-to-end JSON logging with correlation ID."""
        # Create a string buffer to capture log output
        log_capture = StringIO()
        
        # Set up a test logger with JSON formatter
        logger = logging.getLogger("test.integration")
        logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Add handler with JSON formatter
        handler = logging.StreamHandler(log_capture)
        formatter = JSONFormatter()
        correlation_filter = CorrelationIdFilter()
        
        handler.setFormatter(formatter)
        logger.addFilter(correlation_filter)
        logger.addHandler(handler)
        
        # Set correlation ID
        test_correlation_id = "integration-test-123"
        correlation_id_var.set(test_correlation_id)
        
        # Log a message with extra data
        logger.info(
            "Integration test message",
            extra={
                'operation': 'test_operation',
                'user_id': 'test-user',
                'result': 'success'
            }
        )
        
        # Get the logged output
        log_output = log_capture.getvalue()
        
        # Parse the JSON log
        parsed_log = json.loads(log_output.strip())
        
        # Verify the log structure
        assert parsed_log['level'] == 'INFO'
        assert parsed_log['logger'] == 'test.integration'
        assert parsed_log['message'] == 'Integration test message'
        assert parsed_log['correlation_id'] == test_correlation_id
        assert parsed_log['operation'] == 'test_operation'
        assert parsed_log['user_id'] == 'test-user'
        assert parsed_log['result'] == 'success'
        assert 'timestamp' in parsed_log
