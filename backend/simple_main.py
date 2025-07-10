from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import time
import uuid
from datetime import datetime

app = FastAPI(
    title="SnapValue API - Simple",
    description="Simplified SnapValue API for mobile integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return JSONResponse(
        content={
            "message": "Welcome to SnapValue API - Simple",
            "version": "1.0.0",
            "status": "running"
        }
    )

@app.get("/api/v1/health")
async def health_check():
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "SnapValue API",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.post("/api/v1/appraisal/submit")
async def submit_appraisal(image_file: UploadFile = File(...)):
    """Submit an image for appraisal - simplified version"""
    
    try:
        # Validate file type
        if not image_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Generate mock appraisal ID
        appraisal_id = f"appraisal_{uuid.uuid4().hex[:8]}"
        
        # Read file content (for future processing)
        content = await image_file.read()
        
        return JSONResponse(
            content={
                "success": True,
                "appraisal_id": appraisal_id,
                "status": "submitted",
                "submitted_at": datetime.now().isoformat(),
                "estimated_completion_seconds": 3,
                "message": "Image submitted for appraisal"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit appraisal: {str(e)}")

@app.get("/api/v1/appraisal/{appraisal_id}/status")
async def get_appraisal_status(appraisal_id: str):
    """Get appraisal status - simplified version"""
    
    return JSONResponse(
        content={
            "appraisal_id": appraisal_id,
            "status": "completed",
            "progress_percentage": 100,
            "message": "Appraisal completed successfully"
        }
    )

@app.get("/api/v1/appraisal/{appraisal_id}/result")
async def get_appraisal_result(appraisal_id: str):
    """Get appraisal result - simplified version with mock data"""
    
    # Mock result data
    mock_result = {
        "appraisal_id": appraisal_id,
        "status": "completed",
        "estimated_value": 1250.00,
        "price_range": {
            "min": 1100.00,
            "max": 1400.00,
            "currency": "USD"
        },
        "confidence_score": 0.92,
        "item_details": {
            "category": "Electronics",
            "brand": "Apple",
            "model": "iPhone 12 Pro",
            "condition": "Good",
            "features": [
                "128GB Storage",
                "Face ID",
                "Dual Camera System",
                "MagSafe Compatible"
            ]
        },
        "comparable_items": [
            {
                "price": 1100.00,
                "condition": "Fair",
                "source": "eBay"
            },
            {
                "price": 1300.00,
                "condition": "Excellent", 
                "source": "Swappa"
            },
            {
                "price": 1250.00,
                "condition": "Good",
                "source": "Gazelle"
            }
        ],
        "completed_at": datetime.now().isoformat(),
        "processing_time_seconds": 2.5
    }
    
    return JSONResponse(content=mock_result)

if __name__ == "__main__":
    uvicorn.run(
        "simple_main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 