from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.services.appraisal_service import AppraisalService
from app.schemas.appraisal_schemas import AppraisalResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/appraise", response_model=AppraisalResponse)
async def appraise_item(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Appraises an item based on an uploaded image.

    - **file**: The image file to be appraised.
    """
    try:
        appraisal_service = AppraisalService(db)
        file_content = await file.read()
        
        # The appraisal service will handle uploading to GCS and calling the AI agent
        appraisal_result = await appraisal_service.create_appraisal_from_upload(
            file_content=file_content,
            filename=file.filename
        )
        
        return appraisal_result
    except Exception as e:
        logger.error(f"Error during appraisal: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred during the appraisal process.")
