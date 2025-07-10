from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import json

from app.database.connection import get_db
from app.services.appraisal_service import AppraisalService
from app.services.processing_service import ProcessingService
from app.schemas.appraisal_schemas import (
    AppraisalSubmissionRequest, AppraisalSubmissionResponse,
    AppraisalStatusResponse, AppraisalResultResponse,
    BatchAppraisalRequest, BatchAppraisalResponse,
    AppraisalListResponse, AppraisalError,
    PriorityEnum, AppraisalOptionsRequest
)
from app.schemas.response_schemas import (
    SuccessResponse, ErrorResponse, OperationResponse
)
from app.utils.exceptions import ValidationError, AIProcessingError, ExceptionHandler
from app.utils.logging import get_logger, set_correlation_id
from app.utils.image_validation import validate_image_file
from app.core.dependencies import get_logger as get_dep_logger
import uuid

router = APIRouter(prefix="/appraisal", tags=["appraisal"])
logger = get_logger(__name__)

def get_appraisal_service(db: Session = Depends(get_db)) -> AppraisalService:
    """Get appraisal service dependency"""
    return AppraisalService(db)

def get_processing_service(db: Session = Depends(get_db)) -> ProcessingService:
    """Get processing service dependency"""
    return ProcessingService(db)

@router.post(
    "/submit",
    response_model=AppraisalSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Image for Appraisal",
    description="Submit an image for AI-powered appraisal analysis. Supports both file upload and image URL."
)
async def submit_appraisal(
    background_tasks: BackgroundTasks,
    image_file: Optional[UploadFile] = File(None, description="Image file to analyze"),
    image_url: Optional[str] = Form(None, description="URL of image to analyze"),
    category: Optional[str] = Form(None, description="Item category hint"),
    target_condition: Optional[str] = Form(None, description="Target condition for valuation"),
    priority: PriorityEnum = Form(PriorityEnum.NORMAL, description="Processing priority"),
    use_cache: bool = Form(True, description="Whether to use cached results"),
    options: Optional[str] = Form(None, description="Additional options as JSON string"),
    user_id: Optional[str] = Form(None, description="User identifier"),
    appraisal_service: AppraisalService = Depends(get_appraisal_service)
):
    """Submit an image for appraisal analysis"""
    
    # Generate correlation ID
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)
    
    try:
        # Validate input
        if not image_file and not image_url:
            raise ValidationError("Either image_file or image_url must be provided")
        
        if image_file and image_url:
            raise ValidationError("Provide either image_file or image_url, not both")
        
        # Process file if provided
        file_content = None
        filename = None
        
        if image_file:
            # Read and validate file
            file_content = await image_file.read()
            filename = image_file.filename
            
            # Validate image
            validation_result = validate_image_file(file_content, filename)
            if not validation_result['valid']:
                raise ValidationError(f"Image validation failed: {', '.join(validation_result['errors'])}")
        
        # Parse options
        parsed_options = {}
        if options:
            try:
                parsed_options = json.loads(options)
            except json.JSONDecodeError:
                raise ValidationError("Invalid JSON in options field")
        
        # Add form data to options
        parsed_options.update({
            'category': category,
            'target_condition': target_condition,
            'priority': priority,
            'use_cache': use_cache
        })
        
        # Submit appraisal
        result = appraisal_service.submit_appraisal(
            file_content=file_content,
            filename=filename,
            user_id=int(user_id) if user_id else None,
            image_url=image_url,
            options=parsed_options
        )
        
        logger.info(f"Appraisal submitted successfully: {result['appraisal_id']}")
        
        return AppraisalSubmissionResponse(
            appraisal_id=result['appraisal_id'],
            task_id=result['task_id'],
            status=result['status'],
            submitted_at=result['submitted_at'],
            estimated_completion_minutes=result['estimated_completion_minutes'],
            correlation_id=result['correlation_id']
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error in submit_appraisal: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "correlation_id": correlation_id
            }
        )
    except Exception as e:
        logger.error(f"Error in submit_appraisal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to submit appraisal",
                "correlation_id": correlation_id
            }
        )

@router.get(
    "/{appraisal_id}/status",
    response_model=AppraisalStatusResponse,
    summary="Get Appraisal Status",
    description="Get the current status and progress of an appraisal"
)
async def get_appraisal_status(
    appraisal_id: str,
    appraisal_service: AppraisalService = Depends(get_appraisal_service)
):
    """Get appraisal status and progress"""
    
    try:
        status_info = appraisal_service.get_appraisal_status(appraisal_id)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "NOT_FOUND",
                    "message": f"Appraisal {appraisal_id} not found"
                }
            )
        
        return AppraisalStatusResponse(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appraisal status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get appraisal status"
            }
        )

@router.get(
    "/{appraisal_id}/result",
    response_model=AppraisalResultResponse,
    summary="Get Appraisal Result",
    description="Get the complete results of a completed appraisal"
)
async def get_appraisal_result(
    appraisal_id: str,
    include_detailed_analysis: bool = False,
    appraisal_service: AppraisalService = Depends(get_appraisal_service)
):
    """Get completed appraisal results"""
    
    try:
        result = appraisal_service.get_appraisal_result(appraisal_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "NOT_FOUND",
                    "message": f"Appraisal result {appraisal_id} not found or not completed"
                }
            )
        
        # Convert to response model
        response_data = {
            "appraisal_id": result["appraisal_id"],
            "estimated_value": result["estimated_value"],
            "currency": result.get("currency", "USD"),
            "confidence_score": result["confidence_score"],
            "price_range": result["price_range"],
            "ai_analysis": {
                "objects_detected": len(result.get("detected_objects", [])),
                "labels_found": len(result.get("vision_analysis", {}).get("labels", [])),
                "has_text": bool(result.get("vision_analysis", {}).get("text", {}).get("full_text")),
                "has_faces": len(result.get("vision_analysis", {}).get("faces", [])) > 0,
                "confidence_score": result["confidence_score"],
                "top_objects": [obj["name"] for obj in result.get("detected_objects", [])[:5]],
                "top_labels": [label["description"] for label in result.get("vision_analysis", {}).get("labels", [])[:5]]
            },
            "market_analysis": {
                "comparable_items_found": 0,  # Would be extracted from market analysis
                "close_matches": 0,
                "market_activity": 0,
                "trend_direction": "stable",
                "average_market_price": result["estimated_value"],
                "market_positioning": "unknown"
            },
            "image_info": result["image_info"],
            "recommendations": [],
            "processed_at": result.get("completed_at", result.get("created_at"))
        }
        
        if include_detailed_analysis:
            response_data["detailed_analysis"] = {
                "vision_analysis": result.get("vision_analysis"),
                "embeddings": result.get("embeddings"),
                "similar_items": result.get("similar_items")
            }
        
        return AppraisalResultResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appraisal result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get appraisal result"
            }
        )

@router.post(
    "/batch",
    response_model=BatchAppraisalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Batch Appraisal",
    description="Submit multiple images for batch appraisal processing"
)
async def submit_batch_appraisal(
    request: BatchAppraisalRequest,
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """Submit multiple items for batch appraisal"""
    
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)
    
    try:
        # Convert request to processing format
        items = []
        for item in request.items:
            items.append({
                "image_url": item.image_url,
                "category": item.category,
                "target_condition": item.target_condition,
                "priority": item.priority,
                "use_cache": item.use_cache,
                "metadata": item.metadata
            })
        
        # Execute batch workflow
        result = processing_service.execute_workflow(
            "batch_appraisal",
            {"items": items},
            request.batch_options or {}
        )
        
        return BatchAppraisalResponse(
            batch_id=result["execution_id"],
            total_items=result["batch_results"]["total_items"],
            submitted_items=result["batch_results"]["successful_items"],
            failed_items=result["batch_results"]["failed_items"],
            items=result["batch_results"]["items"],
            submitted_at=result["executed_at"]
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "correlation_id": correlation_id
            }
        )
    except Exception as e:
        logger.error(f"Error in batch appraisal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to submit batch appraisal",
                "correlation_id": correlation_id
            }
        )

@router.get(
    "/list",
    response_model=AppraisalListResponse,
    summary="List User Appraisals",
    description="Get a list of appraisals for the authenticated user"
)
async def list_user_appraisals(
    user_id: str,
    page: int = 1,
    page_size: int = 20,
    status_filter: Optional[str] = None,
    appraisal_service: AppraisalService = Depends(get_appraisal_service)
):
    """List appraisals for a user"""
    
    try:
        # Validate pagination
        if page < 1:
            raise ValidationError("Page must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ValidationError("Page size must be between 1 and 100")
        
        offset = (page - 1) * page_size
        
        appraisals = appraisal_service.list_user_appraisals(
            user_id=int(user_id),
            limit=page_size,
            offset=offset
        )
        
        # Filter by status if requested
        if status_filter:
            appraisals = [a for a in appraisals if a["status"] == status_filter]
        
        # Convert to response models
        items = []
        for appraisal in appraisals:
            # Create a minimal response for listing
            items.append({
                "appraisal_id": appraisal["appraisal_id"],
                "estimated_value": appraisal["estimated_value"],
                "currency": "USD",
                "confidence_score": appraisal["confidence_score"],
                "price_range": {"min": 0, "max": 0, "currency": "USD"},
                "ai_analysis": {
                    "objects_detected": 0,
                    "labels_found": 0,
                    "has_text": False,
                    "has_faces": False,
                    "confidence_score": appraisal["confidence_score"] or 0,
                    "top_objects": [],
                    "top_labels": []
                },
                "market_analysis": {
                    "comparable_items_found": 0,
                    "close_matches": 0,
                    "market_activity": 0,
                    "trend_direction": "stable",
                    "average_market_price": appraisal["estimated_value"],
                    "market_positioning": "unknown"
                },
                "image_info": {"image_url": appraisal.get("image_url")},
                "recommendations": [],
                "processed_at": appraisal.get("completed_at", appraisal["created_at"])
            })
        
        return AppraisalListResponse(
            total_count=len(appraisals),
            items=items,
            page=page,
            page_size=page_size,
            has_next=len(appraisals) == page_size
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error listing appraisals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to list appraisals"
            }
        )

@router.delete(
    "/{appraisal_id}",
    response_model=OperationResponse,
    summary="Cancel Appraisal",
    description="Cancel a pending or processing appraisal"
)
async def cancel_appraisal(
    appraisal_id: str,
    user_id: Optional[str] = None,
    appraisal_service: AppraisalService = Depends(get_appraisal_service)
):
    """Cancel an appraisal"""
    
    try:
        success = appraisal_service.cancel_appraisal(
            appraisal_id=appraisal_id,
            user_id=int(user_id) if user_id else None
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error_code": "NOT_FOUND",
                    "message": f"Appraisal {appraisal_id} not found or cannot be cancelled"
                }
            )
        
        return OperationResponse(
            operation="cancel_appraisal",
            status="success",
            message=f"Appraisal {appraisal_id} cancelled successfully",
            data={"appraisal_id": appraisal_id},
            timestamp=None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling appraisal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to cancel appraisal"
            }
        )

@router.post(
    "/priority",
    response_model=AppraisalSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit Priority Appraisal",
    description="Submit an image for high-priority appraisal with expedited processing"
)
async def submit_priority_appraisal(
    request: AppraisalSubmissionRequest,
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """Submit a priority appraisal"""
    
    correlation_id = str(uuid.uuid4())
    set_correlation_id(correlation_id)
    
    try:
        # Execute priority workflow
        result = processing_service.execute_workflow(
            "priority_appraisal",
            {
                "image_url": request.image_url,
                "category": request.category,
                "target_condition": request.target_condition,
                "metadata": request.metadata
            },
            {"use_cache": request.use_cache}
        )
        
        appraisal_result = result["appraisal_result"]
        
        return AppraisalSubmissionResponse(
            appraisal_id=appraisal_result["appraisal_id"],
            task_id=appraisal_result["task_id"],
            status=appraisal_result["status"],
            submitted_at=appraisal_result["submitted_at"],
            estimated_completion_minutes=1,  # Priority processing
            correlation_id=appraisal_result["correlation_id"]
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e),
                "correlation_id": correlation_id
            }
        )
    except Exception as e:
        logger.error(f"Error in priority appraisal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to submit priority appraisal",
                "correlation_id": correlation_id
            }
        )