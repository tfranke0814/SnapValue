from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "SnapValue API",
            "version": "1.0.0"
        }
    )

@router.get("/ping")
async def ping():
    """Simple ping endpoint"""
    return JSONResponse(content={"message": "pong"})
