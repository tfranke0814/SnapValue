from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List, Optional
import os

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=True)
    
    # Application settings
    APP_NAME: str = "SnapValue API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS settings
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8080,http://127.0.0.1:8080"
    
    # Database settings
    DATABASE_URL: str = "sqlite:///./snapvalue.db"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 3600
    SQL_ECHO: bool = False
    
    # Google Cloud settings
    GOOGLE_CLOUD_PROJECT: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Google Cloud Storage settings
    GCS_BUCKET_NAME: Optional[str] = None
    GCS_REGION: str = "us-central1"
    
    # Vision AI settings
    VISION_AI_ENDPOINT: Optional[str] = None
    VISION_AI_MODEL: str = "projects/your-project/locations/us-central1/models/general"
    
    # Vertex AI settings
    VERTEX_AI_PROJECT: Optional[str] = None
    VERTEX_AI_LOCATION: Optional[str] = None
    VERTEX_AI_REASONING_ENGINE_ID: Optional[str] = None

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # Service settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: str = "image/jpeg,image/png,image/webp"
    
    # Caching settings
    REDIS_URL: Optional[str] = None
    CACHE_TTL: int = 3600  # 1 hour
    
    # API Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Storage settings
    STORAGE_TYPE: str = "local"  # "local" or "gcs"
    LOCAL_STORAGE_PATH: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: str = "image/jpeg,image/png,image/webp"

    @property
    def allowed_origins_list(self) -> List[str]:
        """Convert ALLOWED_ORIGINS string to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(',')]
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Convert ALLOWED_FILE_TYPES string to list"""
        return [file_type.strip() for file_type in self.ALLOWED_FILE_TYPES.split(',')]
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def database_config(self) -> dict:
        """Get database configuration"""
        return {
            "url": self.DATABASE_URL,
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_pre_ping": self.DB_POOL_PRE_PING,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "echo": self.SQL_ECHO and self.DEBUG
        }

settings = Settings()
