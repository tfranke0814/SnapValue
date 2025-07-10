from fastapi import APIRouter
from app.api.v1 import appraisal, auth, monitoring, status, users, docs

# Create main API router
api_router = APIRouter(prefix="/v1")

# Include sub-routers
api_router.include_router(appraisal.router)
api_router.include_router(auth.router)
api_router.include_router(monitoring.router)
api_router.include_router(status.router)
api_router.include_router(users.router)
api_router.include_router(docs.router)

# Health check endpoint at root level
@api_router.get("/", summary="API Root", description="API root endpoint with basic information")
async def api_root():
    """API root endpoint"""
    return {
        "name": "SnapValue API",
        "version": "1.0.0",
        "description": "AI-powered item appraisal service",
        "endpoints": {
            "appraisal": "/v1/appraisal",
            "auth": "/v1/auth", 
            "monitoring": "/v1/monitoring",
            "status": "/v1/status",
            "users": "/v1/users",
            "docs": "/v1/docs-api"
        },
        "documentation": "/docs"
    }