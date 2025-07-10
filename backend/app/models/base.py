from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None
    timestamp: datetime = datetime.now()

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    message: str
    timestamp: datetime = datetime.now()

class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str
    version: str
