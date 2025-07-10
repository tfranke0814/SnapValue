from typing import Dict, List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/docs-api", tags=["api-documentation"])

@router.get(
    "/endpoints",
    summary="List All API Endpoints",
    description="Get a comprehensive list of all available API endpoints with descriptions"
)
async def list_api_endpoints():
    """Get comprehensive API documentation"""
    
    endpoints = {
        "appraisal": {
            "prefix": "/v1/appraisal",
            "description": "AI-powered item appraisal services",
            "endpoints": {
                "POST /submit": {
                    "description": "Submit an image for appraisal",
                    "parameters": ["image_file", "image_url", "category", "priority"],
                    "responses": ["201 Created", "400 Bad Request", "500 Internal Server Error"]
                },
                "GET /{appraisal_id}": {
                    "description": "Get appraisal results",
                    "parameters": ["appraisal_id"],
                    "responses": ["200 OK", "404 Not Found", "500 Internal Server Error"]
                },
                "GET /{appraisal_id}/status": {
                    "description": "Get appraisal processing status",
                    "parameters": ["appraisal_id"],
                    "responses": ["200 OK", "404 Not Found", "500 Internal Server Error"]
                },
                "POST /batch": {
                    "description": "Submit multiple images for batch appraisal",
                    "parameters": ["items", "batch_options"],
                    "responses": ["201 Created", "400 Bad Request", "500 Internal Server Error"]
                },
                "GET /list": {
                    "description": "List user's appraisals with pagination",
                    "parameters": ["page", "page_size", "status", "category"],
                    "responses": ["200 OK", "400 Bad Request", "500 Internal Server Error"]
                }
            }
        },
        "auth": {
            "prefix": "/v1/auth",
            "description": "Authentication and authorization services",
            "endpoints": {
                "POST /login": {
                    "description": "User login with email and password",
                    "parameters": ["email", "password"],
                    "responses": ["200 OK", "401 Unauthorized", "500 Internal Server Error"]
                },
                "POST /logout": {
                    "description": "User logout",
                    "parameters": [],
                    "responses": ["200 OK", "401 Unauthorized", "500 Internal Server Error"]
                },
                "POST /refresh": {
                    "description": "Refresh access token",
                    "parameters": ["refresh_token"],
                    "responses": ["200 OK", "401 Unauthorized", "500 Internal Server Error"]
                },
                "GET /me": {
                    "description": "Get current user information",
                    "parameters": [],
                    "responses": ["200 OK", "401 Unauthorized", "500 Internal Server Error"]
                }
            }
        },
        "users": {
            "prefix": "/v1/users",
            "description": "User management services",
            "endpoints": {
                "POST /register": {
                    "description": "Register a new user account",
                    "parameters": ["email", "password", "full_name"],
                    "responses": ["201 Created", "400 Bad Request", "409 Conflict"]
                },
                "GET /profile": {
                    "description": "Get current user profile",
                    "parameters": [],
                    "responses": ["200 OK", "401 Unauthorized", "500 Internal Server Error"]
                },
                "PUT /profile": {
                    "description": "Update current user profile",
                    "parameters": ["full_name", "metadata"],
                    "responses": ["200 OK", "400 Bad Request", "401 Unauthorized"]
                },
                "GET /stats": {
                    "description": "Get user usage statistics",
                    "parameters": [],
                    "responses": ["200 OK", "401 Unauthorized", "500 Internal Server Error"]
                },
                "POST /regenerate-api-key": {
                    "description": "Generate new API key",
                    "parameters": [],
                    "responses": ["200 OK", "401 Unauthorized", "500 Internal Server Error"]
                },
                "DELETE /account": {
                    "description": "Delete user account",
                    "parameters": [],
                    "responses": ["200 OK", "401 Unauthorized", "500 Internal Server Error"]
                }
            }
        },
        "status": {
            "prefix": "/v1/status",
            "description": "Status and monitoring services",
            "endpoints": {
                "GET /appraisal/{appraisal_id}": {
                    "description": "Get detailed appraisal status",
                    "parameters": ["appraisal_id"],
                    "responses": ["200 OK", "404 Not Found", "500 Internal Server Error"]
                },
                "GET /appraisals": {
                    "description": "List appraisals with filtering",
                    "parameters": ["page", "page_size", "status", "category", "user_id"],
                    "responses": ["200 OK", "400 Bad Request", "500 Internal Server Error"]
                },
                "GET /user/{user_id}/appraisals": {
                    "description": "Get user's appraisals",
                    "parameters": ["user_id", "status_filter", "limit"],
                    "responses": ["200 OK", "404 Not Found", "500 Internal Server Error"]
                },
                "GET /queue": {
                    "description": "Get processing queue status",
                    "parameters": [],
                    "responses": ["200 OK", "500 Internal Server Error"]
                },
                "GET /stats": {
                    "description": "Get system statistics",
                    "parameters": [],
                    "responses": ["200 OK", "500 Internal Server Error"]
                },
                "POST /appraisal/{appraisal_id}/cancel": {
                    "description": "Cancel pending appraisal",
                    "parameters": ["appraisal_id"],
                    "responses": ["200 OK", "404 Not Found", "500 Internal Server Error"]
                },
                "GET /appraisal/{appraisal_id}/history": {
                    "description": "Get appraisal processing history",
                    "parameters": ["appraisal_id"],
                    "responses": ["200 OK", "404 Not Found", "500 Internal Server Error"]
                }
            }
        },
        "monitoring": {
            "prefix": "/v1/monitoring",
            "description": "System monitoring and health checks",
            "endpoints": {
                "GET /health": {
                    "description": "System health check",
                    "parameters": [],
                    "responses": ["200 OK", "503 Service Unavailable"]
                },
                "GET /metrics": {
                    "description": "Get system metrics",
                    "parameters": [],
                    "responses": ["200 OK", "500 Internal Server Error"]
                },
                "GET /performance": {
                    "description": "Get performance statistics",
                    "parameters": [],
                    "responses": ["200 OK", "500 Internal Server Error"]
                }
            }
        }
    }
    
    return JSONResponse(
        content={
            "api_version": "1.0.0",
            "description": "SnapValue API - AI-powered item appraisal service",
            "base_url": "/api/v1",
            "authentication": "JWT Bearer token required for most endpoints",
            "rate_limiting": "100 requests per minute per user",
            "endpoints": endpoints,
            "common_responses": {
                "200": "Success",
                "201": "Created",
                "400": "Bad Request - Invalid parameters",
                "401": "Unauthorized - Authentication required",
                "403": "Forbidden - Insufficient permissions",
                "404": "Not Found - Resource not found",
                "409": "Conflict - Resource already exists",
                "422": "Unprocessable Entity - Validation error",
                "429": "Too Many Requests - Rate limit exceeded",
                "500": "Internal Server Error - System error"
            },
            "example_requests": {
                "submit_appraisal": {
                    "url": "POST /api/v1/appraisal/submit",
                    "headers": {
                        "Authorization": "Bearer <jwt_token>",
                        "Content-Type": "multipart/form-data"
                    },
                    "body": {
                        "image_file": "<file>",
                        "category": "electronics",
                        "priority": "normal"
                    }
                },
                "get_appraisal": {
                    "url": "GET /api/v1/appraisal/{appraisal_id}",
                    "headers": {
                        "Authorization": "Bearer <jwt_token>"
                    }
                },
                "login": {
                    "url": "POST /api/v1/auth/login",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "email": "user@example.com",
                        "password": "password123"
                    }
                }
            }
        },
        status_code=200
    )

@router.get(
    "/schemas",
    summary="Get API Schemas",
    description="Get all API request and response schemas"
)
async def get_api_schemas():
    """Get comprehensive API schemas"""
    
    schemas = {
        "requests": {
            "AppraisalSubmissionRequest": {
                "type": "object",
                "properties": {
                    "image_url": {"type": "string", "description": "URL of image to analyze"},
                    "category": {"type": "string", "description": "Item category hint"},
                    "target_condition": {"type": "string", "description": "Target condition"},
                    "priority": {"type": "string", "enum": ["low", "normal", "high", "urgent"]},
                    "use_cache": {"type": "boolean", "description": "Use cached results"},
                    "metadata": {"type": "object", "description": "Additional metadata"}
                },
                "required": []
            },
            "LoginRequest": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "User email"},
                    "password": {"type": "string", "description": "User password"}
                },
                "required": ["email", "password"]
            },
            "UserRegistrationRequest": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "User email"},
                    "password": {"type": "string", "minLength": 8, "description": "User password"},
                    "full_name": {"type": "string", "description": "User full name"},
                    "metadata": {"type": "object", "description": "Additional metadata"}
                },
                "required": ["email", "password", "full_name"]
            }
        },
        "responses": {
            "AppraisalSubmissionResponse": {
                "type": "object",
                "properties": {
                    "appraisal_id": {"type": "string", "description": "Unique appraisal ID"},
                    "task_id": {"type": "string", "description": "Processing task ID"},
                    "status": {"type": "string", "description": "Current status"},
                    "submitted_at": {"type": "string", "format": "date-time"},
                    "estimated_completion_minutes": {"type": "number"},
                    "correlation_id": {"type": "string"}
                }
            },
            "AppraisalResultResponse": {
                "type": "object",
                "properties": {
                    "appraisal_id": {"type": "string"},
                    "status": {"type": "string"},
                    "estimated_value": {"type": "number"},
                    "price_range": {
                        "type": "object",
                        "properties": {
                            "min": {"type": "number"},
                            "max": {"type": "number"},
                            "currency": {"type": "string"}
                        }
                    },
                    "confidence_score": {"type": "number"},
                    "category": {"type": "string"},
                    "condition": {"type": "string"},
                    "features": {"type": "array"},
                    "comparable_items": {"type": "array"},
                    "processing_time_seconds": {"type": "number"},
                    "completed_at": {"type": "string", "format": "date-time"}
                }
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "const": False},
                    "error_code": {"type": "string"},
                    "message": {"type": "string"},
                    "details": {"type": "object"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "correlation_id": {"type": "string"}
                }
            }
        }
    }
    
    return JSONResponse(content=schemas, status_code=200)

@router.get(
    "/rate-limits",
    summary="Get Rate Limiting Information",
    description="Get information about API rate limits and usage"
)
async def get_rate_limits():
    """Get rate limiting information"""
    
    rate_limits = {
        "default": {
            "requests_per_minute": 100,
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        },
        "premium": {
            "requests_per_minute": 500,
            "requests_per_hour": 5000,
            "requests_per_day": 50000
        },
        "enterprise": {
            "requests_per_minute": 1000,
            "requests_per_hour": 10000,
            "requests_per_day": 100000
        },
        "endpoints": {
            "appraisal_submit": {
                "rate_limit": "10 requests per minute",
                "description": "Image submission for appraisal"
            },
            "appraisal_get": {
                "rate_limit": "60 requests per minute",
                "description": "Get appraisal results"
            },
            "auth_login": {
                "rate_limit": "5 requests per minute",
                "description": "User authentication"
            },
            "status_endpoints": {
                "rate_limit": "30 requests per minute",
                "description": "Status and monitoring endpoints"
            }
        },
        "headers": {
            "X-RateLimit-Limit": "Maximum requests per window",
            "X-RateLimit-Remaining": "Remaining requests in current window",
            "X-RateLimit-Reset": "Time when rate limit resets (Unix timestamp)"
        }
    }
    
    return JSONResponse(content=rate_limits, status_code=200)
