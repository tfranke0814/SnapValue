from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import json
from datetime import datetime

from app.utils.logging import get_logger
from app.utils.exceptions import ValidationError
from app.core.config import settings

logger = get_logger(__name__)

class RequestValidator:
    """Request validation middleware"""
    
    def __init__(self):
        # Maximum request sizes (in bytes)
        self.max_sizes = {
            "default": 10 * 1024 * 1024,      # 10MB default
            "upload": 50 * 1024 * 1024,       # 50MB for uploads
            "batch": 100 * 1024 * 1024,       # 100MB for batch operations
        }
        
        # Required headers for certain endpoints
        self.required_headers = {
            "/api/v1/appraisal/submit": ["content-type"],
            "/api/v1/appraisal/batch": ["content-type"],
        }
        
        # Blocked user agents (bots, scrapers, etc.)
        # Note: Be more lenient in development mode
        if settings.is_production:
            self.blocked_user_agents = [
                "bot", "crawler", "spider", "scraper", "curl", "wget"
            ]
        else:
            # Allow testing tools in development
            self.blocked_user_agents = [
                "bot", "crawler", "spider", "scraper"
            ]
    
    def _get_max_size_for_path(self, path: str) -> int:
        """Get maximum request size for path"""
        if "/upload" in path or "/submit" in path:
            return self.max_sizes["upload"]
        elif "/batch" in path:
            return self.max_sizes["batch"]
        else:
            return self.max_sizes["default"]
    
    def _validate_user_agent(self, request: Request) -> bool:
        """Validate user agent"""
        user_agent = request.headers.get("user-agent", "").lower()
        
        # Allow empty user agent for API clients
        if not user_agent:
            return True
        
        # Block known bots and scrapers
        for blocked in self.blocked_user_agents:
            if blocked in user_agent:
                return False
        
        return True
    
    def _validate_content_type(self, request: Request) -> bool:
        """Validate content type for endpoints that require it"""
        path = request.url.path
        
        if path in self.required_headers:
            required = self.required_headers[path]
            
            if "content-type" in required:
                content_type = request.headers.get("content-type", "")
                
                # Allow multipart/form-data for file uploads
                if "/submit" in path:
                    return content_type.startswith(("multipart/form-data", "application/json"))
                
                # Allow JSON for other endpoints
                return content_type.startswith("application/json")
        
        return True
    
    def _validate_request_size(self, request: Request, content_length: int) -> bool:
        """Validate request size"""
        max_size = self._get_max_size_for_path(request.url.path)
        return content_length <= max_size
    
    def _validate_json_payload(self, content: bytes) -> Dict[str, Any]:
        """Validate JSON payload"""
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {str(e)}")
    
    def _sanitize_input(self, data: Any) -> Any:
        """Sanitize input data"""
        if isinstance(data, dict):
            return {k: self._sanitize_input(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_input(item) for item in data]
        elif isinstance(data, str):
            # Basic string sanitization
            # Remove potential script injection attempts
            sanitized = data.replace("<script", "&lt;script")
            sanitized = sanitized.replace("javascript:", "")
            return sanitized.strip()
        else:
            return data

async def request_validation_middleware(request: Request, call_next):
    """Request validation middleware"""
    
    validator = RequestValidator()
    
    # Skip validation for health checks and docs
    if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    try:
        # Validate user agent
        if not validator._validate_user_agent(request):
            logger.warning(
                f"Blocked request from suspicious user agent",
                extra={
                    "user_agent": request.headers.get("user-agent"),
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else "unknown"
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error_code": "FORBIDDEN",
                    "message": "Request blocked"
                }
            )
        
        # Validate content type
        if not validator._validate_content_type(request):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error_code": "INVALID_CONTENT_TYPE",
                    "message": "Invalid or missing content type"
                }
            )
        
        # Validate request size
        content_length = int(request.headers.get("content-length", 0))
        if content_length > 0 and not validator._validate_request_size(request, content_length):
            max_size = validator._get_max_size_for_path(request.url.path)
            
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={
                    "error_code": "REQUEST_TOO_LARGE",
                    "message": f"Request size {content_length} exceeds maximum {max_size} bytes"
                }
            )
        
        # For JSON endpoints, validate and sanitize payload
        if (request.method in ["POST", "PUT", "PATCH"] and 
            request.headers.get("content-type", "").startswith("application/json")):
            
            # Read and validate JSON
            body = await request.body()
            if body:
                try:
                    json_data = validator._validate_json_payload(body)
                    sanitized_data = validator._sanitize_input(json_data)
                    
                    # Store sanitized data in request state for use by endpoints
                    request.state.validated_json = sanitized_data
                    
                except ValidationError as e:
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={
                            "error_code": "VALIDATION_ERROR",
                            "message": str(e)
                        }
                    )
        
        # Add validation timestamp
        request.state.validated_at = datetime.utcnow()
        
        # Process request
        response = await call_next(request)
        
        return response
        
    except Exception as e:
        logger.error(
            f"Request validation error: {e}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown"
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Request validation failed"
            }
        )