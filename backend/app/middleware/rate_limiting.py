from typing import Dict, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import time
import asyncio
from collections import defaultdict, deque
from datetime import datetime, timedelta

from app.utils.logging import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """Rate limiting implementation using token bucket algorithm"""
    
    def __init__(self):
        # Storage for rate limit buckets
        self.buckets: Dict[str, Dict] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
        
        # Default rate limits (requests per time window)
        self.default_limits = {
            "general": {"requests": 100, "window": 60},  # 100 requests per minute
            "upload": {"requests": 10, "window": 60},    # 10 uploads per minute
            "auth": {"requests": 5, "window": 300},      # 5 auth requests per 5 minutes
            "batch": {"requests": 2, "window": 300},     # 2 batch requests per 5 minutes
        }
    
    def _get_client_id(self, request: Request) -> str:
        """Get unique client identifier"""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def _get_rate_limit_type(self, request: Request) -> str:
        """Determine rate limit type based on endpoint"""
        path = request.url.path
        
        if "/upload" in path or "/submit" in path:
            return "upload"
        elif "/auth/" in path:
            return "auth"
        elif "/batch" in path:
            return "batch"
        else:
            return "general"
    
    def _cleanup_old_buckets(self):
        """Remove old bucket entries"""
        current_time = time.time()
        
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # Remove entries older than 1 hour
        
        for client_id in list(self.buckets.keys()):
            bucket = self.buckets[client_id]
            if bucket.get('last_request', 0) < cutoff_time:
                del self.buckets[client_id]
        
        self.last_cleanup = current_time
    
    def is_allowed(self, request: Request) -> tuple[bool, Dict]:
        """Check if request is allowed under rate limits"""
        self._cleanup_old_buckets()
        
        client_id = self._get_client_id(request)
        limit_type = self._get_rate_limit_type(request)
        
        # Get rate limit configuration
        limit_config = self.default_limits.get(limit_type, self.default_limits["general"])
        max_requests = limit_config["requests"]
        window_seconds = limit_config["window"]
        
        current_time = time.time()
        
        # Initialize bucket if not exists
        if client_id not in self.buckets:
            self.buckets[client_id] = {
                "requests": deque(),
                "last_request": current_time
            }
        
        bucket = self.buckets[client_id]
        requests = bucket["requests"]
        
        # Remove old requests outside the window
        while requests and requests[0] <= current_time - window_seconds:
            requests.popleft()
        
        # Check if limit exceeded
        if len(requests) >= max_requests:
            # Calculate reset time
            reset_time = requests[0] + window_seconds
            
            return False, {
                "limit": max_requests,
                "remaining": 0,
                "reset": int(reset_time),
                "retry_after": int(reset_time - current_time)
            }
        
        # Add current request
        requests.append(current_time)
        bucket["last_request"] = current_time
        
        return True, {
            "limit": max_requests,
            "remaining": max_requests - len(requests),
            "reset": int(current_time + window_seconds),
            "retry_after": 0
        }

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    
    # Skip rate limiting for health checks and docs
    if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
        return await call_next(request)
    
    # Check rate limit
    allowed, limit_info = rate_limiter.is_allowed(request)
    
    if not allowed:
        logger.warning(
            f"Rate limit exceeded for client",
            extra={
                "client_id": rate_limiter._get_client_id(request),
                "endpoint": request.url.path,
                "limit_type": rate_limiter._get_rate_limit_type(request)
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error_code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded",
                "retry_after": limit_info["retry_after"]
            },
            headers={
                "X-RateLimit-Limit": str(limit_info["limit"]),
                "X-RateLimit-Remaining": str(limit_info["remaining"]),
                "X-RateLimit-Reset": str(limit_info["reset"]),
                "Retry-After": str(limit_info["retry_after"])
            }
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers to response
    response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(limit_info["reset"])
    
    return response