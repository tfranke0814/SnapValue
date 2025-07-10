from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.connection import get_db
from app.services.appraisal_service import AppraisalService
from app.services.processing_service import ProcessingService
from app.schemas.appraisal_schemas import (
    AppraisalStatusResponse, AppraisalListResponse, 
    AppraisalResultResponse, AppraisalHistoryResponse
)
from app.schemas.response_schemas import (
    SuccessResponse, ErrorResponse, PaginatedResponse
)
from app.utils.logging import get_logger
from app.utils.exceptions import ValidationError, NotFoundError

router = APIRouter(prefix="/status", tags=["status"])
logger = get_logger(__name__)

def get_appraisal_service(db: Session = Depends(get_db)) -> AppraisalService:
    """Get appraisal service dependency"""
    return AppraisalService(db)

def get_processing_service(db: Session = Depends(get_db)) -> ProcessingService:
    """Get processing service dependency"""
    return ProcessingService(db)

@router.get(
    "/appraisal/{appraisal_id}",
    response_model=AppraisalStatusResponse,
    summary="Get Appraisal Status",
    description="Get the current status and progress of a specific appraisal"
)
async def get_appraisal_status(
    appraisal_id: str,
    appraisal_service: AppraisalService = Depends(get_appraisal_service)
):
    """Get detailed status of a specific appraisal"""
    
    try:
        status_info = appraisal_service.get_appraisal_status(appraisal_id)
        
        if not status_info:
            raise NotFoundError(f"Appraisal {appraisal_id} not found")
        
        return AppraisalStatusResponse(**status_info)
        
    except NotFoundError as e:
        logger.warning(f"Appraisal not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "APPRAISAL_NOT_FOUND",
                "message": str(e)
            }
        )
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
    "/appraisals",
    response_model=PaginatedResponse[AppraisalListResponse],
    summary="List Appraisals",
    description="Get a paginated list of appraisals with optional filtering"
)
async def list_appraisals(
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    appraisal_service: AppraisalService = Depends(get_appraisal_service)
):
    """Get paginated list of appraisals with filtering options"""
    
    try:
        filters = {
            'user_id': user_id,
            'status': status_filter,
            'category': category,
            'start_date': start_date,
            'end_date': end_date
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        result = appraisal_service.list_appraisals(
            filters=filters,
            page=page,
            page_size=page_size
        )
        
        return PaginatedResponse(
            items=[AppraisalListResponse(**item) for item in result['items']],
            total=result['total'],
            page=page,
            page_size=page_size,
            total_pages=result['total_pages']
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error in list_appraisals: {e}")
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

@router.get(
    "/user/{user_id}/appraisals",
    response_model=List[AppraisalListResponse],
    summary="Get User Appraisals",
    description="Get all appraisals for a specific user"
)
async def get_user_appraisals(
    user_id: int,
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    appraisal_service: AppraisalService = Depends(get_appraisal_service)
):
    """Get all appraisals for a specific user"""
    
    try:
        appraisals = appraisal_service.get_user_appraisals(
            user_id=user_id,
            status_filter=status_filter,
            limit=limit
        )
        
        return [AppraisalListResponse(**appraisal) for appraisal in appraisals]
        
    except Exception as e:
        logger.error(f"Error getting user appraisals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get user appraisals"
            }
        )

@router.get(
    "/queue",
    response_model=Dict,
    summary="Get Processing Queue Status",
    description="Get current processing queue status and statistics"
)
async def get_queue_status(
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """Get processing queue status and statistics"""
    
    try:
        queue_status = processing_service.get_queue_status()
        
        return {
            "queue_length": queue_status.get('queue_length', 0),
            "processing_count": queue_status.get('processing_count', 0),
            "completed_today": queue_status.get('completed_today', 0),
            "failed_today": queue_status.get('failed_today', 0),
            "average_processing_time": queue_status.get('average_processing_time', 0),
            "estimated_wait_time": queue_status.get('estimated_wait_time', 0),
            "last_updated": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get queue status"
            }
        )

@router.get(
    "/stats",
    response_model=Dict,
    summary="Get System Statistics",
    description="Get overall system statistics and metrics"
)
async def get_system_stats(
    processing_service: ProcessingService = Depends(get_processing_service)
):
    """Get system-wide statistics"""
    
    try:
        stats = processing_service.get_system_stats()
        
        return {
            "total_appraisals": stats.get('total_appraisals', 0),
            "appraisals_today": stats.get('appraisals_today', 0),
            "appraisals_this_month": stats.get('appraisals_this_month', 0),
            "success_rate": stats.get('success_rate', 0),
            "average_processing_time": stats.get('average_processing_time', 0),
            "total_users": stats.get('total_users', 0),
            "active_users_today": stats.get('active_users_today', 0),
            "system_uptime": stats.get('system_uptime', 0),
            "last_updated": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_SERVER,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get system statistics"
            }
        )

@router.post(
    "/appraisal/{appraisal_id}/cancel",
    response_model=SuccessResponse,
    summary="Cancel Appraisal",
    description="Cancel a pending or processing appraisal"
)
async def cancel_appraisal(
    appraisal_id: str,
    appraisal_service: AppraisalService = Depends(get_appraisal_service)
):
    """Cancel an appraisal that is pending or processing"""
    
    try:
        result = appraisal_service.cancel_appraisal(appraisal_id)
        
        if not result:
            raise NotFoundError(f"Appraisal {appraisal_id} not found or cannot be cancelled")
        
        return SuccessResponse(
            message=f"Appraisal {appraisal_id} cancelled successfully",
            data={"appraisal_id": appraisal_id, "status": "cancelled"}
        )
        
    except NotFoundError as e:
        logger.warning(f"Appraisal not found for cancellation: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "APPRAISAL_NOT_FOUND",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error cancelling appraisal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to cancel appraisal"
            }
        )

@router.get(
    "/appraisal/{appraisal_id}/history",
    response_model=AppraisalHistoryResponse,
    summary="Get Appraisal History",
    description="Get detailed processing history for an appraisal"
)
async def get_appraisal_history(
    appraisal_id: str,
    appraisal_service: AppraisalService = Depends(get_appraisal_service)
):
    """Get detailed processing history for an appraisal"""
    
    try:
        history = appraisal_service.get_appraisal_history(appraisal_id)
        
        if not history:
            raise NotFoundError(f"Appraisal {appraisal_id} not found")
        
        return AppraisalHistoryResponse(**history)
        
    except NotFoundError as e:
        logger.warning(f"Appraisal not found for history: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "APPRAISAL_NOT_FOUND",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error getting appraisal history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get appraisal history"
            }
        )
