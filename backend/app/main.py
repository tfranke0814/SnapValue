from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
import time
import uuid

from app.api.v1.main import api_router
from app.core.config import settings
from app.utils.logging import get_logger
from app.utils.exceptions import ValidationError, AuthenticationError, AIProcessingError
from app.middleware.rate_limiting import rate_limit_middleware
from app.middleware.validation import request_validation_middleware

# Initialize logger
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="SnapValue API",
    description="AI-powered item appraisal service backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware
app.middleware("http")(rate_limit_middleware)

# Request validation middleware  
app.middleware("http")(request_validation_middleware)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests"""
    start_time = time.time()
    correlation_id = str(uuid.uuid4())
    
    # Add correlation ID to request state
    request.state.correlation_id = correlation_id
    
    # Log request
    logger.info(
        f"Request started",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "url": str(request.url),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    logger.info(
        f"Request completed",
        extra={
            "correlation_id": correlation_id,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2)
        }
    )
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response

# Exception handlers
@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """Handle validation errors"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.warning(
        f"Validation error: {exc}",
        extra={"correlation_id": correlation_id}
    )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": str(exc),
            "correlation_id": correlation_id
        }
    )

@app.exception_handler(AuthenticationError)
async def auth_error_handler(request: Request, exc: AuthenticationError):
    """Handle authentication errors"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.warning(
        f"Authentication error: {exc}",
        extra={"correlation_id": correlation_id}
    )
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error_code": "AUTHENTICATION_ERROR",
            "message": str(exc),
            "correlation_id": correlation_id
        }
    )

@app.exception_handler(AIProcessingError)
async def ai_processing_error_handler(request: Request, exc: AIProcessingError):
    """Handle AI processing errors"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.error(
        f"AI processing error: {exc}",
        extra={"correlation_id": correlation_id}
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "AI_PROCESSING_ERROR",
            "message": str(exc),
            "correlation_id": correlation_id
        }
    )

@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.error(
        f"Unhandled error: {exc}",
        extra={"correlation_id": correlation_id},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "correlation_id": correlation_id
        }
    )

# Include API routes
app.include_router(api_router, prefix="/api")

# Root endpoint
@app.get("/", summary="Service Root", description="SnapValue API service root")
async def root():
    """Service root endpoint"""
    return {
        "service": "SnapValue API",
        "version": "1.0.0",
        "status": "running",
        "api_docs": "/docs",
        "api_base": "/api/v1"
    }

# Simple health check at service root
@app.get("/health", summary="Simple Health Check", description="Basic health check endpoint")
async def health():
    """Simple health check"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "SnapValue API"
    }

# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="SnapValue API",
        version="1.0.0",
        description="""
# SnapValue API

AI-powered item appraisal service backend API.

## Features

- **Image Upload & Analysis**: Submit images for AI-powered appraisal
- **Real-time Processing**: Track appraisal progress in real-time  
- **Market Analysis**: Compare against market data for accurate valuations
- **Batch Processing**: Process multiple items simultaneously
- **Authentication**: JWT and API key authentication
- **Monitoring**: Comprehensive system monitoring and health checks

## Getting Started

1. Authenticate using `/api/v1/auth/login` or generate an API key
2. Submit an image for appraisal using `/api/v1/appraisal/submit`
3. Track progress using `/api/v1/appraisal/{id}/status`
4. Retrieve results using `/api/v1/appraisal/{id}/result`

## Authentication

The API supports two authentication methods:
- **JWT Tokens**: Obtain via `/api/v1/auth/login`
- **API Keys**: Generate via `/api/v1/auth/api-key/generate`

Include authentication in requests using the `Authorization` header:
- JWT: `Authorization: Bearer <token>`
- API Key: `Authorization: Bearer <api_key>`
        """,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "ApiKeyAuth": {
            "type": "http", 
            "scheme": "bearer",
            "bearerFormat": "API Key"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup"""
    logger.info("SnapValue API starting up...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown"""
    logger.info("SnapValue API shutting down...")

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )