"""
Tests for Core Configuration Management - Step 2
"""
import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

from app.core.config import Settings, settings


class TestConfigurationManagement:
    """Test cases for configuration management system."""
    
    def test_default_settings(self):
        """Test default configuration values."""
        config = Settings()
        
        # Application settings
        assert config.APP_NAME == "SnapValue API"
        assert config.APP_VERSION == "1.0.0"
        assert config.DEBUG is True
        assert config.HOST == "0.0.0.0"
        assert config.PORT == 8000
        assert config.ENVIRONMENT == "development"
        
        # Security settings
        assert config.SECRET_KEY == "your-secret-key-here-change-in-production"
        assert config.ALGORITHM == "HS256"
        assert config.ACCESS_TOKEN_EXPIRE_MINUTES == 30
        
        # Database settings
        assert config.DATABASE_URL == "sqlite:///./snapvalue.db"
        assert config.DB_POOL_SIZE == 20
        assert config.DB_MAX_OVERFLOW == 30
        assert config.DB_POOL_PRE_PING is True
        assert config.DB_POOL_RECYCLE == 3600
        assert config.SQL_ECHO is False
    
    def test_environment_variable_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {
            'APP_NAME': 'Test App',
            'DEBUG': 'false',
            'PORT': '9000',
            'DB_POOL_SIZE': '10'
        }):
            config = Settings()
            assert config.APP_NAME == 'Test App'
            assert config.DEBUG is False
            assert config.PORT == 9000
            assert config.DB_POOL_SIZE == 10
    
    def test_allowed_origins_list_property(self):
        """Test allowed_origins_list property."""
        config = Settings()
        origins = config.allowed_origins_list
        
        assert isinstance(origins, list)
        assert len(origins) >= 1
        assert 'http://localhost:3000' in origins
        assert 'http://127.0.0.1:3000' in origins
    
    def test_allowed_file_types_list_property(self):
        """Test allowed_file_types_list property."""
        config = Settings()
        file_types = config.allowed_file_types_list
        
        assert isinstance(file_types, list)
        assert 'image/jpeg' in file_types
        assert 'image/png' in file_types
        assert 'image/webp' in file_types
    
    def test_environment_checks(self):
        """Test environment check properties."""
        # Test development environment
        config = Settings(ENVIRONMENT="development")
        assert config.is_development is True
        assert config.is_production is False
        
        # Test production environment
        config = Settings(ENVIRONMENT="production")
        assert config.is_development is False
        assert config.is_production is True
        
        # Test other environment
        config = Settings(ENVIRONMENT="testing")
        assert config.is_development is False
        assert config.is_production is False
    
    def test_database_config_property(self):
        """Test database_config property."""
        config = Settings()
        db_config = config.database_config
        
        assert isinstance(db_config, dict)
        assert 'url' in db_config
        assert 'pool_size' in db_config
        assert 'max_overflow' in db_config
        assert 'pool_pre_ping' in db_config
        assert 'pool_recycle' in db_config
        assert 'echo' in db_config
        
        assert db_config['url'] == config.DATABASE_URL
        assert db_config['pool_size'] == config.DB_POOL_SIZE
        assert db_config['max_overflow'] == config.DB_MAX_OVERFLOW
        assert db_config['pool_pre_ping'] == config.DB_POOL_PRE_PING
        assert db_config['pool_recycle'] == config.DB_POOL_RECYCLE
    
    def test_database_config_echo_behavior(self):
        """Test database echo behavior based on DEBUG setting."""
        # Debug=True, SQL_ECHO=True -> echo=True
        config = Settings(DEBUG=True, SQL_ECHO=True)
        assert config.database_config['echo'] is True
        
        # Debug=True, SQL_ECHO=False -> echo=False
        config = Settings(DEBUG=True, SQL_ECHO=False)
        assert config.database_config['echo'] is False
        
        # Debug=False, SQL_ECHO=True -> echo=False
        config = Settings(DEBUG=False, SQL_ECHO=True)
        assert config.database_config['echo'] is False
    
    def test_google_cloud_settings(self):
        """Test Google Cloud configuration."""
        config = Settings()
        
        # Default values should be None
        assert config.GOOGLE_CLOUD_PROJECT is None
        assert config.GOOGLE_APPLICATION_CREDENTIALS is None
        assert config.GCS_BUCKET_NAME is None
        assert config.GCS_REGION == "us-central1"
        
        # Test with environment variables
        with patch.dict(os.environ, {
            'GOOGLE_CLOUD_PROJECT': 'test-project',
            'GOOGLE_APPLICATION_CREDENTIALS': '/path/to/credentials.json',
            'GCS_BUCKET_NAME': 'test-bucket'
        }):
            config = Settings()
            assert config.GOOGLE_CLOUD_PROJECT == 'test-project'
            assert config.GOOGLE_APPLICATION_CREDENTIALS == '/path/to/credentials.json'
            assert config.GCS_BUCKET_NAME == 'test-bucket'
    
    def test_ai_service_settings(self):
        """Test AI service configuration."""
        config = Settings()
        
        # Vision AI settings
        assert config.VISION_AI_ENDPOINT is None
        assert config.VISION_AI_MODEL == "projects/your-project/locations/us-central1/models/general"
        
        # Vertex AI settings
        assert config.VERTEX_AI_PROJECT is None
        assert config.VERTEX_AI_LOCATION == "us-central1"
        assert config.VERTEX_AI_ENDPOINT is None
    
    def test_logging_settings(self):
        """Test logging configuration."""
        config = Settings()
        
        assert config.LOG_LEVEL == "INFO"
        assert config.LOG_FORMAT == "json"
        assert config.LOG_FILE is None
    
    def test_service_settings(self):
        """Test service-specific configuration."""
        config = Settings()
        
        assert config.MAX_FILE_SIZE == 10 * 1024 * 1024  # 10MB
        assert config.ALLOWED_FILE_TYPES == "image/jpeg,image/png,image/webp"
    
    def test_caching_settings(self):
        """Test caching configuration."""
        config = Settings()
        
        assert config.REDIS_URL is None
        assert config.CACHE_TTL == 3600
    
    def test_rate_limiting_settings(self):
        """Test rate limiting configuration."""
        config = Settings()
        
        assert config.RATE_LIMIT_REQUESTS == 100
        assert config.RATE_LIMIT_WINDOW == 60
    
    def test_settings_singleton(self):
        """Test that settings is a singleton instance."""
        assert settings is not None
        assert isinstance(settings, Settings)
        
        # Should be the same instance
        from app.core.config import settings as settings2
        assert settings is settings2
    
    def test_cors_settings(self):
        """Test CORS configuration."""
        config = Settings()
        
        assert config.ALLOWED_ORIGINS is not None
        origins = config.allowed_origins_list
        assert len(origins) > 0
        
        # Test custom CORS setting
        custom_origins = "http://example.com,https://app.example.com"
        config = Settings(ALLOWED_ORIGINS=custom_origins)
        origins = config.allowed_origins_list
        assert 'http://example.com' in origins
        assert 'https://app.example.com' in origins
    
    def test_type_validation(self):
        """Test that configuration validates types properly."""
        # Valid integer
        config = Settings(PORT=8080)
        assert config.PORT == 8080
        
        # Valid boolean
        config = Settings(DEBUG=False)
        assert config.DEBUG is False
        
        # Test with string numbers (should be converted)
        with patch.dict(os.environ, {'PORT': '9090'}):
            config = Settings()
            assert config.PORT == 9090
            assert isinstance(config.PORT, int)
