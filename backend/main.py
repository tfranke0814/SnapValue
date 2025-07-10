from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.routers import health, appraisal
from app.core.config import settings

app = FastAPI(
    title="SnapValue API",
    description="A FastAPI backend for SnapValue application",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(appraisal.router, prefix="/api/v1/appraisal", tags=["appraisal"])


@app.get("/")
async def root():
    return JSONResponse(
        content={
            "message": "Welcome to SnapValue API",
            "version": "1.0.0",
            "docs": "/docs"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
