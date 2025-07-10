from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
import uuid

from app.database.connection import get_db
from app.models.user import User
from app.schemas.response_schemas import LoginRequest, LoginResponse, UserInfo, SuccessResponse, ErrorResponse
from app.core.config import settings
from app.utils.logging import get_logger
from app.utils.exceptions import AuthenticationError, ValidationError

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger(__name__)

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate password hash"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt

def decode_access_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise AuthenticationError("Invalid token")

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password if hasattr(user, 'hashed_password') else ''):
        return None
    
    return user

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = decode_access_token(token)
        
        user_id = payload.get("sub")
        if user_id is None:
            raise AuthenticationError("Invalid token payload")
        
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise AuthenticationError("User not found")
        
        if not user.is_active:
            raise AuthenticationError("User account is inactive")
        
        return user
        
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def generate_api_key() -> str:
    """Generate a new API key"""
    return f"sk_{uuid.uuid4().hex}"

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User Login",
    description="Authenticate user and return access token"
)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token"""
    
    try:
        # Validate input
        if not request.email or not request.password:
            raise ValidationError("Email and password are required")
        
        # Authenticate user
        user = authenticate_user(db, request.email, request.password)
        
        if not user:
            raise AuthenticationError("Invalid email or password")
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        logger.info(f"User {user.email} logged in successfully")
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(user.id)
        )
        
    except (ValidationError, AuthenticationError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "AUTHENTICATION_FAILED",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Login failed"
            }
        )

@router.get(
    "/me",
    response_model=UserInfo,
    summary="Get Current User",
    description="Get information about the currently authenticated user"
)
async def get_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user information"""
    
    try:
        return UserInfo(
            user_id=str(current_user.id),
            email=current_user.email,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            api_key=current_user.api_key if hasattr(current_user, 'api_key') else None
        )
        
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to get user information"
            }
        )

@router.post(
    "/refresh",
    response_model=LoginResponse,
    summary="Refresh Token",
    description="Refresh access token using current valid token"
)
async def refresh_token(
    current_user: User = Depends(get_current_active_user)
):
    """Refresh access token"""
    
    try:
        # Create new access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(current_user.id), "email": current_user.email},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Token refreshed for user {current_user.email}")
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=str(current_user.id)
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Token refresh failed"
            }
        )

@router.post(
    "/api-key/generate",
    response_model=SuccessResponse,
    summary="Generate API Key",
    description="Generate a new API key for the authenticated user"
)
async def generate_user_api_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate a new API key for the user"""
    
    try:
        # Generate new API key
        new_api_key = generate_api_key()
        
        # Update user record
        current_user.api_key = new_api_key
        current_user.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"New API key generated for user {current_user.email}")
        
        return SuccessResponse(
            message="API key generated successfully",
            data={"api_key": new_api_key}
        )
        
    except Exception as e:
        logger.error(f"API key generation error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to generate API key"
            }
        )

@router.post(
    "/api-key/revoke",
    response_model=SuccessResponse,
    summary="Revoke API Key",
    description="Revoke the current API key for the authenticated user"
)
async def revoke_api_key(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Revoke the user's API key"""
    
    try:
        # Revoke API key
        current_user.api_key = None
        current_user.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"API key revoked for user {current_user.email}")
        
        return SuccessResponse(
            message="API key revoked successfully"
        )
        
    except Exception as e:
        logger.error(f"API key revocation error: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Failed to revoke API key"
            }
        )

@router.post(
    "/logout",
    response_model=SuccessResponse,
    summary="User Logout",
    description="Logout user (client-side token invalidation)"
)
async def logout(
    current_user: User = Depends(get_current_active_user)
):
    """Logout user (client should invalidate token)"""
    
    try:
        logger.info(f"User {current_user.email} logged out")
        
        return SuccessResponse(
            message="Logged out successfully"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error_code": "INTERNAL_ERROR",
                "message": "Logout failed"
            }
        )

# API Key authentication (alternative to JWT)
class APIKeyAuth:
    """API Key authentication class"""
    
    @staticmethod
    def verify_api_key(api_key: str, db: Session) -> Optional[User]:
        """Verify API key and return user"""
        if not api_key.startswith("sk_"):
            return None
        
        user = db.query(User).filter(User.api_key == api_key).first()
        
        if not user or not user.is_active:
            return None
        
        return user

def get_api_key_user(
    api_key: str,
    db: Session = Depends(get_db)
) -> User:
    """Get user by API key"""
    user = APIKeyAuth.verify_api_key(api_key, db)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return user

# Optional: Combined authentication (JWT or API Key)
def get_authenticated_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    api_key: Optional[str] = None,
    db: Session = Depends(get_db)
) -> User:
    """Get authenticated user via JWT token or API key"""
    
    # Try API key first if provided
    if api_key:
        return get_api_key_user(api_key, db)
    
    # Fall back to JWT token
    if credentials:
        return get_current_user(credentials, db)
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )