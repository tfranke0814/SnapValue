from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.database.connection import get_db
from app.models.user import User
from app.schemas.response_schemas import (
    SuccessResponse, ErrorResponse, UserInfo, 
    PaginatedResponse, LoginRequest, LoginResponse,
    UserRegistrationRequest, UserRegistrationResponse,
    UserUpdateRequest, UserStatsResponse
)
from app.core.dependencies import get_current_user
from app.utils.logging import get_logger
from app.utils.exceptions import ValidationError, NotFoundError, DuplicateError

router = APIRouter(prefix="/users", tags=["users"])
logger = get_logger(__name__)

def get_user_service(db: Session = Depends(get_db)):
    """Get user service dependency"""
    from app.services.user_service import UserService
    return UserService(db)

@router.post(
    "/register",
    response_model=UserRegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New User",
    description="Register a new user account"
)
async def register_user(
    user_data: UserRegistrationRequest,
    user_service = Depends(get_user_service)
):
    """Register a new user"""
    
    try:
        # Check if user already exists
        existing_user = user_service.get_user_by_email(user_data.email)
        if existing_user:
            raise DuplicateError(f"User with email {user_data.email} already exists")
        
        # Create new user
        new_user = user_service.create_user(
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            metadata=user_data.metadata
        )
        
        return UserRegistrationResponse(
            user_id=new_user.id,
            email=new_user.email,
            full_name=new_user.full_name,
            api_key=new_user.api_key,
            created_at=new_user.created_at,
            message="User registered successfully"
        )
        
    except DuplicateError as e:
        logger.warning(f"Duplicate user registration attempt: {e}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "USER_EXISTS",
                "message": str(e)
            }
        )
    except ValidationError as e:
        logger.warning(f"Validation error in user registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to register user"
            }
        )

@router.get(
    "/profile",
    response_model=UserInfo,
    summary="Get User Profile",
    description="Get current user's profile information"
)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user's profile"""
    
    return UserInfo(
        user_id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        api_key=current_user.api_key,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        is_active=current_user.is_active,
        appraisal_count=current_user.appraisal_count,
        subscription_tier=current_user.subscription_tier
    )

@router.put(
    "/profile",
    response_model=UserInfo,
    summary="Update User Profile",
    description="Update current user's profile information"
)
async def update_user_profile(
    update_data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    user_service = Depends(get_user_service)
):
    """Update current user's profile"""
    
    try:
        updated_user = user_service.update_user(
            user_id=current_user.id,
            update_data=update_data.dict(exclude_unset=True)
        )
        
        return UserInfo(
            user_id=updated_user.id,
            email=updated_user.email,
            full_name=updated_user.full_name,
            api_key=updated_user.api_key,
            created_at=updated_user.created_at,
            last_login=updated_user.last_login,
            is_active=updated_user.is_active,
            appraisal_count=updated_user.appraisal_count,
            subscription_tier=updated_user.subscription_tier
        )
        
    except ValidationError as e:
        logger.warning(f"Validation error in profile update: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "VALIDATION_ERROR",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to update profile"
            }
        )

@router.get(
    "/stats",
    response_model=UserStatsResponse,
    summary="Get User Statistics",
    description="Get current user's usage statistics"
)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    user_service = Depends(get_user_service)
):
    """Get current user's statistics"""
    
    try:
        stats = user_service.get_user_stats(current_user.id)
        
        return UserStatsResponse(
            user_id=current_user.id,
            total_appraisals=stats.get('total_appraisals', 0),
            completed_appraisals=stats.get('completed_appraisals', 0),
            failed_appraisals=stats.get('failed_appraisals', 0),
            average_processing_time=stats.get('average_processing_time', 0),
            total_spent=stats.get('total_spent', 0),
            favorite_categories=stats.get('favorite_categories', []),
            recent_activity=stats.get('recent_activity', []),
            monthly_usage=stats.get('monthly_usage', {}),
            account_created=current_user.created_at,
            last_appraisal=stats.get('last_appraisal')
        )
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get user statistics"
            }
        )

@router.post(
    "/regenerate-api-key",
    response_model=Dict[str, str],
    summary="Regenerate API Key",
    description="Generate a new API key for the current user"
)
async def regenerate_api_key(
    current_user: User = Depends(get_current_user),
    user_service = Depends(get_user_service)
):
    """Regenerate API key for current user"""
    
    try:
        new_api_key = user_service.regenerate_api_key(current_user.id)
        
        return {
            "api_key": new_api_key,
            "message": "API key regenerated successfully",
            "regenerated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error regenerating API key: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to regenerate API key"
            }
        )

@router.delete(
    "/account",
    response_model=SuccessResponse,
    summary="Delete User Account",
    description="Delete the current user's account and all associated data"
)
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    user_service = Depends(get_user_service)
):
    """Delete current user's account"""
    
    try:
        user_service.delete_user(current_user.id)
        
        return SuccessResponse(
            message="User account deleted successfully",
            data={"user_id": current_user.id, "deleted_at": datetime.utcnow()}
        )
        
    except Exception as e:
        logger.error(f"Error deleting user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to delete user account"
            }
        )

# Admin endpoints (require admin privileges)
@router.get(
    "/admin/users",
    response_model=PaginatedResponse[UserInfo],
    summary="List All Users (Admin)",
    description="Get paginated list of all users (admin only)"
)
async def list_users_admin(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    current_user: User = Depends(get_current_user),
    user_service = Depends(get_user_service)
):
    """List all users (admin only)"""
    
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Admin privileges required"
            }
        )
    
    try:
        result = user_service.list_users(
            page=page,
            page_size=page_size,
            search=search
        )
        
        return PaginatedResponse(
            items=[UserInfo(**user) for user in result['items']],
            total=result['total'],
            page=page,
            page_size=page_size,
            total_pages=result['total_pages'],
            has_next=result['has_next'],
            has_previous=result['has_previous']
        )
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to list users"
            }
        )

@router.get(
    "/admin/stats",
    response_model=Dict,
    summary="Get User Statistics (Admin)",
    description="Get overall user statistics (admin only)"
)
async def get_user_stats_admin(
    current_user: User = Depends(get_current_user),
    user_service = Depends(get_user_service)
):
    """Get overall user statistics (admin only)"""
    
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "INSUFFICIENT_PERMISSIONS",
                "message": "Admin privileges required"
            }
        )
    
    try:
        stats = user_service.get_admin_stats()
        
        return {
            "total_users": stats.get('total_users', 0),
            "active_users": stats.get('active_users', 0),
            "new_users_today": stats.get('new_users_today', 0),
            "new_users_this_month": stats.get('new_users_this_month', 0),
            "total_appraisals": stats.get('total_appraisals', 0),
            "appraisals_today": stats.get('appraisals_today', 0),
            "average_appraisals_per_user": stats.get('average_appraisals_per_user', 0),
            "top_categories": stats.get('top_categories', []),
            "subscription_tiers": stats.get('subscription_tiers', {}),
            "last_updated": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error getting admin user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get user statistics"
            }
        )
