from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Base Response Models
class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = Field(True, description="Whether the request was successful")
    message: str = Field("Success", description="Response message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Request success status")
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid request data",
                "details": {
                    "field": "image_file",
                    "reason": "File size exceeds maximum limit"
                },
                "timestamp": "2024-01-15T10:30:00Z",
                "correlation_id": "corr_123456789"
            }
        }

class SuccessResponse(BaseResponse):
    """Success response model"""
    data: Optional[Any] = Field(None, description="Response data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"result": "example"},
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class PaginatedResponse(BaseModel):
    """Paginated response model"""
    items: List[Any] = Field(..., description="List of items")
    total_count: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")

# Health Check Models
class ServiceHealth(BaseModel):
    """Individual service health status"""
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status (healthy, degraded, unhealthy)")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional health details")
    last_checked: datetime = Field(..., description="Last health check timestamp")

class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Overall system status")
    services: List[ServiceHealth] = Field(..., description="Individual service health statuses")
    timestamp: datetime = Field(..., description="Health check timestamp")
    uptime_seconds: Optional[float] = Field(None, description="System uptime in seconds")
    version: str = Field(..., description="API version")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "services": [
                    {
                        "name": "database",
                        "status": "healthy",
                        "response_time_ms": 15.2,
                        "last_checked": "2024-01-15T10:30:00Z"
                    },
                    {
                        "name": "ai_service",
                        "status": "healthy",
                        "response_time_ms": 234.5,
                        "last_checked": "2024-01-15T10:30:00Z"
                    }
                ],
                "timestamp": "2024-01-15T10:30:00Z",
                "uptime_seconds": 86400.0,
                "version": "1.0.0"
            }
        }

# System Status Models
class TaskManagerStats(BaseModel):
    """Task manager statistics"""
    total_tasks: int = Field(..., description="Total number of tasks")
    running_tasks: int = Field(..., description="Currently running tasks")
    queued_tasks: int = Field(..., description="Queued tasks")
    completed_tasks: int = Field(..., description="Completed tasks")
    failed_tasks: int = Field(..., description="Failed tasks")
    worker_utilization: float = Field(..., description="Worker utilization percentage")

class CacheStats(BaseModel):
    """Cache statistics"""
    size: int = Field(..., description="Current cache size")
    max_size: int = Field(..., description="Maximum cache size")
    hit_rate_percent: float = Field(..., description="Cache hit rate percentage")
    total_hits: int = Field(..., description="Total cache hits")
    total_misses: int = Field(..., description="Total cache misses")

class SystemStatusResponse(BaseModel):
    """System status response model"""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Status check timestamp")
    task_manager: TaskManagerStats = Field(..., description="Task manager statistics")
    cache_stats: Dict[str, CacheStats] = Field(..., description="Cache statistics")
    active_appraisals: int = Field(..., description="Number of active appraisals")
    system_metrics: Dict[str, Any] = Field(..., description="System metrics")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T10:30:00Z",
                "task_manager": {
                    "total_tasks": 150,
                    "running_tasks": 3,
                    "queued_tasks": 5,
                    "completed_tasks": 140,
                    "failed_tasks": 2,
                    "worker_utilization": 60.0
                },
                "cache_stats": {
                    "appraisal_cache": {
                        "size": 250,
                        "max_size": 500,
                        "hit_rate_percent": 85.5,
                        "total_hits": 1200,
                        "total_misses": 210
                    }
                },
                "active_appraisals": 8,
                "system_metrics": {
                    "uptime_hours": 24.5,
                    "total_processed_today": 45
                }
            }
        }

# Authentication Models
class LoginRequest(BaseModel):
    """Login request model"""
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")

class LoginResponse(BaseModel):
    """Login response model"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_id: str = Field(..., description="User identifier")
    
    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user_id": "user_123456"
            }
        }

class UserInfo(BaseModel):
    """User information model"""
    user_id: str = Field(..., description="User identifier")
    email: str = Field(..., description="User email")
    is_active: bool = Field(..., description="Whether user is active")
    created_at: datetime = Field(..., description="User creation timestamp")
    api_key: Optional[str] = Field(None, description="User API key")

# Processing Queue Models
class QueueStatus(BaseModel):
    """Processing queue status model"""
    queue_length: int = Field(..., description="Number of items in queue")
    running_tasks: int = Field(..., description="Currently running tasks")
    active_appraisals: int = Field(..., description="Active appraisals")
    estimated_wait_time_minutes: float = Field(..., description="Estimated wait time in minutes")
    worker_utilization_percent: float = Field(..., description="Worker utilization percentage")
    
    class Config:
        schema_extra = {
            "example": {
                "queue_length": 12,
                "running_tasks": 5,
                "active_appraisals": 18,
                "estimated_wait_time_minutes": 3.5,
                "worker_utilization_percent": 75.0
            }
        }

# Statistics Models
class ProcessingStats(BaseModel):
    """Processing statistics model"""
    total_appraisals: int = Field(..., description="Total number of appraisals")
    completed_appraisals: int = Field(..., description="Completed appraisals")
    failed_appraisals: int = Field(..., description="Failed appraisals")
    average_processing_time_seconds: Optional[float] = Field(None, description="Average processing time")
    success_rate_percent: float = Field(..., description="Success rate percentage")
    daily_volume: int = Field(..., description="Daily processing volume")

class UserStatsResponse(BaseModel):
    """User statistics response model"""
    user_id: str = Field(..., description="User identifier")
    total_appraisals: int = Field(..., description="Total appraisals submitted")
    completed_appraisals: int = Field(..., description="Completed appraisals")
    pending_appraisals: int = Field(..., description="Pending appraisals")
    failed_appraisals: int = Field(..., description="Failed appraisals")
    average_confidence_score: Optional[float] = Field(None, description="Average confidence score")
    total_estimated_value: Optional[float] = Field(None, description="Total estimated value")
    last_appraisal_at: Optional[datetime] = Field(None, description="Last appraisal timestamp")

# Utility Response Models
class OperationResponse(BaseModel):
    """Generic operation response"""
    operation: str = Field(..., description="Operation name")
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Operation message")
    data: Optional[Dict[str, Any]] = Field(None, description="Operation data")
    timestamp: datetime = Field(..., description="Operation timestamp")

class BatchOperationResponse(BaseModel):
    """Batch operation response"""
    batch_id: str = Field(..., description="Batch operation identifier")
    total_items: int = Field(..., description="Total number of items")
    successful_items: int = Field(..., description="Successfully processed items")
    failed_items: int = Field(..., description="Failed items")
    items: List[Dict[str, Any]] = Field(..., description="Individual item results")
    started_at: datetime = Field(..., description="Batch start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Batch completion timestamp")

class MetricsResponse(BaseModel):
    """Metrics response model"""
    metrics: Dict[str, Any] = Field(..., description="System metrics")
    collected_at: datetime = Field(..., description="Metrics collection timestamp")
    period: str = Field(..., description="Metrics period")
    
    class Config:
        schema_extra = {
            "example": {
                "metrics": {
                    "requests_per_minute": 45.2,
                    "average_response_time_ms": 234.5,
                    "error_rate_percent": 0.5,
                    "active_users": 12
                },
                "collected_at": "2024-01-15T10:30:00Z",
                "period": "last_hour"
            }
        }