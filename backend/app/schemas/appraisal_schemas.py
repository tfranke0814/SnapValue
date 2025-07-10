from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

class AppraisalStatusEnum(str, Enum):
    """Appraisal status enumeration"""
    SUBMITTED = "submitted"
    VALIDATING = "validating"
    UPLOADING = "uploading"
    PROCESSING_IMAGE = "processing_image"
    ANALYZING_AI = "analyzing_ai"
    SEARCHING_MARKET = "searching_market"
    CALCULATING_PRICE = "calculating_price"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProcessingStepEnum(str, Enum):
    """Processing step enumeration"""
    IMAGE_VALIDATION = "image_validation"
    IMAGE_UPLOAD = "image_upload"
    METADATA_EXTRACTION = "metadata_extraction"
    VISION_ANALYSIS = "vision_analysis"
    EMBEDDING_GENERATION = "embedding_generation"
    FEATURE_EXTRACTION = "feature_extraction"
    SIMILARITY_SEARCH = "similarity_search"
    MARKET_ANALYSIS = "market_analysis"
    PRICE_CALCULATION = "price_calculation"
    RESULT_COMPILATION = "result_compilation"
    DATABASE_STORAGE = "database_storage"

class PriorityEnum(str, Enum):
    """Processing priority enumeration"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

# Request Models
class AppraisalSubmissionRequest(BaseModel):
    """Request model for submitting an appraisal"""
    image_url: Optional[str] = Field(None, description="URL of image to analyze")
    category: Optional[str] = Field(None, description="Item category hint")
    target_condition: Optional[str] = Field(None, description="Target condition for valuation")
    priority: PriorityEnum = Field(PriorityEnum.NORMAL, description="Processing priority")
    use_cache: bool = Field(True, description="Whether to use cached results if available")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "category": "electronics",
                "target_condition": "good",
                "priority": "normal",
                "use_cache": True,
                "metadata": {"source": "mobile_app"}
            }
        }

class BatchAppraisalRequest(BaseModel):
    """Request model for batch appraisal submission"""
    items: List[AppraisalSubmissionRequest] = Field(..., description="List of items to appraise")
    batch_options: Optional[Dict[str, Any]] = Field(None, description="Batch processing options")
    
    @validator('items')
    def validate_items_count(cls, v):
        if len(v) == 0:
            raise ValueError("At least one item is required")
        if len(v) > 50:
            raise ValueError("Maximum 50 items per batch")
        return v

class AppraisalOptionsRequest(BaseModel):
    """Advanced options for appraisal processing"""
    ai_features: Optional[List[str]] = Field(None, description="AI features to analyze")
    similarity_threshold: Optional[float] = Field(0.7, ge=0.0, le=1.0, description="Similarity threshold for market search")
    max_comparables: Optional[int] = Field(20, ge=1, le=100, description="Maximum comparable items to find")
    market_sources: Optional[List[str]] = Field(None, description="Market data sources to use")
    include_detailed_analysis: bool = Field(False, description="Include detailed analysis in results")

# Response Models
class PriceRange(BaseModel):
    """Price range model"""
    min: float = Field(..., description="Minimum estimated value")
    max: float = Field(..., description="Maximum estimated value")
    currency: str = Field("USD", description="Currency code")

class ImageInfo(BaseModel):
    """Image information model"""
    image_path: Optional[str] = Field(None, description="Storage path of image")
    image_url: Optional[str] = Field(None, description="Public URL of image")
    image_size: Optional[int] = Field(None, description="Image size in bytes")
    image_dimensions: Optional[Dict[str, int]] = Field(None, description="Image dimensions")

class ProcessingStepResult(BaseModel):
    """Processing step result model"""
    step: ProcessingStepEnum = Field(..., description="Processing step name")
    status: str = Field(..., description="Step status (success, failed, running)")
    duration_ms: Optional[int] = Field(None, description="Step duration in milliseconds")
    error: Optional[str] = Field(None, description="Error message if failed")

class AppraisalProgress(BaseModel):
    """Appraisal progress model"""
    current_step: Optional[ProcessingStepEnum] = Field(None, description="Current processing step")
    progress_percentage: float = Field(0.0, ge=0.0, le=100.0, description="Progress percentage")
    steps_completed: List[ProcessingStepResult] = Field([], description="Completed processing steps")
    estimated_completion_at: Optional[datetime] = Field(None, description="Estimated completion time")

class AIAnalysisSummary(BaseModel):
    """AI analysis summary model"""
    objects_detected: int = Field(0, description="Number of objects detected")
    labels_found: int = Field(0, description="Number of labels found")
    has_text: bool = Field(False, description="Whether text was detected")
    has_faces: bool = Field(False, description="Whether faces were detected")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="AI analysis confidence")
    top_objects: List[str] = Field([], description="Top detected objects")
    top_labels: List[str] = Field([], description="Top detected labels")

class MarketAnalysisSummary(BaseModel):
    """Market analysis summary model"""
    comparable_items_found: int = Field(0, description="Number of comparable items found")
    close_matches: int = Field(0, description="Number of close matches")
    market_activity: int = Field(0, description="Market activity level")
    trend_direction: str = Field("stable", description="Market trend direction")
    average_market_price: Optional[float] = Field(None, description="Average market price")
    market_positioning: str = Field("unknown", description="Market positioning")

class AppraisalSubmissionResponse(BaseModel):
    """Response model for appraisal submission"""
    appraisal_id: str = Field(..., description="Unique appraisal identifier")
    task_id: str = Field(..., description="Task identifier for tracking")
    status: AppraisalStatusEnum = Field(..., description="Current appraisal status")
    submitted_at: datetime = Field(..., description="Submission timestamp")
    estimated_completion_minutes: int = Field(..., description="Estimated completion time in minutes")
    correlation_id: str = Field(..., description="Correlation ID for tracking")
    
    class Config:
        schema_extra = {
            "example": {
                "appraisal_id": "123e4567-e89b-12d3-a456-426614174000",
                "task_id": "task_987fcdeb-51a2-43d8-9012-123456789abc",
                "status": "submitted",
                "submitted_at": "2024-01-15T10:30:00Z",
                "estimated_completion_minutes": 2,
                "correlation_id": "corr_456def78-90ab-cdef-1234-567890abcdef"
            }
        }

class AppraisalStatusResponse(BaseModel):
    """Response model for appraisal status"""
    appraisal_id: str = Field(..., description="Unique appraisal identifier")
    user_id: Optional[str] = Field(None, description="User identifier")
    status: AppraisalStatusEnum = Field(..., description="Current appraisal status")
    progress: AppraisalProgress = Field(..., description="Processing progress")
    submitted_at: datetime = Field(..., description="Submission timestamp")
    started_processing_at: Optional[datetime] = Field(None, description="Processing start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    duration_seconds: Optional[float] = Field(None, description="Total processing duration")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    correlation_id: str = Field(..., description="Correlation ID for tracking")

class AppraisalResultResponse(BaseModel):
    """Response model for appraisal results"""
    appraisal_id: str = Field(..., description="Unique appraisal identifier")
    estimated_value: float = Field(..., description="Estimated item value")
    currency: str = Field("USD", description="Currency code")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    price_range: PriceRange = Field(..., description="Price range estimate")
    
    # Analysis summaries
    ai_analysis: AIAnalysisSummary = Field(..., description="AI analysis summary")
    market_analysis: MarketAnalysisSummary = Field(..., description="Market analysis summary")
    
    # Image and metadata
    image_info: ImageInfo = Field(..., description="Image information")
    
    # Recommendations
    recommendations: List[str] = Field([], description="Appraisal recommendations")
    
    # Timestamps
    processed_at: datetime = Field(..., description="Processing completion timestamp")
    
    # Optional detailed data
    detailed_analysis: Optional[Dict[str, Any]] = Field(None, description="Detailed analysis data")
    
    class Config:
        schema_extra = {
            "example": {
                "appraisal_id": "123e4567-e89b-12d3-a456-426614174000",
                "estimated_value": 125.50,
                "currency": "USD",
                "confidence_score": 0.85,
                "price_range": {
                    "min": 100.00,
                    "max": 150.00,
                    "currency": "USD"
                },
                "ai_analysis": {
                    "objects_detected": 3,
                    "labels_found": 8,
                    "has_text": False,
                    "has_faces": False,
                    "confidence_score": 0.92,
                    "top_objects": ["watch", "metal", "luxury item"],
                    "top_labels": ["timepiece", "analog", "stainless steel"]
                },
                "market_analysis": {
                    "comparable_items_found": 45,
                    "close_matches": 12,
                    "market_activity": 23,
                    "trend_direction": "stable",
                    "average_market_price": 128.75,
                    "market_positioning": "mid_market"
                },
                "recommendations": [
                    "Good market conditions for selling",
                    "Consider professional cleaning to maximize value"
                ],
                "processed_at": "2024-01-15T10:32:15Z"
            }
        }

class BatchAppraisalResponse(BaseModel):
    """Response model for batch appraisal submission"""
    batch_id: str = Field(..., description="Batch identifier")
    total_items: int = Field(..., description="Total number of items")
    submitted_items: int = Field(..., description="Number of successfully submitted items")
    failed_items: int = Field(..., description="Number of items that failed to submit")
    items: List[Dict[str, Any]] = Field(..., description="Individual item results")
    submitted_at: datetime = Field(..., description="Batch submission timestamp")

class AppraisalListResponse(BaseModel):
    """Response model for listing appraisals"""
    total_count: int = Field(..., description="Total number of appraisals")
    items: List[AppraisalResultResponse] = Field(..., description="Appraisal items")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(20, description="Items per page")
    has_next: bool = Field(False, description="Whether there are more pages")

class AppraisalListItemResponse(BaseModel):
    """Appraisal list item response model"""
    appraisal_id: str = Field(..., description="Appraisal ID")
    user_id: Optional[int] = Field(None, description="User ID")
    status: AppraisalStatusEnum = Field(..., description="Current appraisal status")
    category: Optional[str] = Field(None, description="Item category")
    submitted_at: datetime = Field(..., description="Submission timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    estimated_value: Optional[float] = Field(None, description="Estimated value")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL")
    
    class Config:
        schema_extra = {
            "example": {
                "appraisal_id": "appraisal_123456",
                "user_id": 1,
                "status": "completed",
                "category": "electronics",
                "submitted_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T10:35:00Z",
                "estimated_value": 299.99,
                "thumbnail_url": "https://storage.googleapis.com/snapvalue/thumbnails/123456.jpg"
            }
        }

class AppraisalHistoryStep(BaseModel):
    """Individual step in appraisal history"""
    step_name: str = Field(..., description="Step name")
    status: str = Field(..., description="Step status")
    started_at: datetime = Field(..., description="Step start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Step completion timestamp")
    duration_seconds: Optional[float] = Field(None, description="Step duration in seconds")
    details: Optional[Dict[str, Any]] = Field(None, description="Step details")
    error_message: Optional[str] = Field(None, description="Error message if step failed")

class AppraisalHistoryResponse(BaseModel):
    """Appraisal history response model"""
    appraisal_id: str = Field(..., description="Appraisal ID")
    total_duration_seconds: Optional[float] = Field(None, description="Total processing duration")
    steps: List[AppraisalHistoryStep] = Field(..., description="Processing steps history")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "appraisal_id": "appraisal_123456",
                "total_duration_seconds": 45.2,
                "steps": [
                    {
                        "step_name": "image_validation",
                        "status": "completed",
                        "started_at": "2024-01-15T10:30:00Z",
                        "completed_at": "2024-01-15T10:30:05Z",
                        "duration_seconds": 5.0,
                        "details": {"file_size": 1024000, "format": "JPEG"}
                    },
                    {
                        "step_name": "ai_analysis",
                        "status": "completed",
                        "started_at": "2024-01-15T10:30:05Z",
                        "completed_at": "2024-01-15T10:30:35Z",
                        "duration_seconds": 30.0,
                        "details": {"confidence": 0.95, "objects_detected": 3}
                    }
                ],
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:35:00Z"
            }
        }

# Error Models
class AppraisalError(BaseModel):
    """Appraisal error model"""
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    appraisal_id: Optional[str] = Field(None, description="Related appraisal ID")
    timestamp: datetime = Field(..., description="Error timestamp")

class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Optional[Any] = Field(None, description="Invalid value")

class ValidationError(BaseModel):
    """Validation error response"""
    error_code: str = Field("VALIDATION_ERROR", description="Error code")
    message: str = Field(..., description="Error message")
    details: List[ValidationErrorDetail] = Field(..., description="Validation error details")
    timestamp: datetime = Field(..., description="Error timestamp")