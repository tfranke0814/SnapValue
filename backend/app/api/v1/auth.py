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
from app.core.dependencies import get_current_user, decode_access_token

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

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user with email and password"""
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password if hasattr(user, 'hashed_password') else ''):
        return None
    
    return user

@router.post("/login", response_model=LoginResponse, summary="User Login", responses={
    status.HTTP_401_UNAUTHORIZED: {
        "description": "Invalid credentials",
        "model": ErrorResponse
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: {
        "description": "Internal server error",
        "model": ErrorResponse
    }
})
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
            logger.warning(f"Failed login attempt for email: {request.email}")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        logger.info(f"User {user.email} logged in successfully")
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            user_info=UserInfo(
                id=str(user.id),
                email=user.email,
                full_name=user.full_name,
                is_active=user.is_active,
                roles=user.roles
            )
        )
    except ValidationError as e:
        logger.error(f"Validation error during login: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"An unexpected error occurred during login: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred")

@router.post("/logout", response_model=SuccessResponse, summary="User Logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Logs out the current user. In a token-based system, this is typically handled
    on the client-side by deleting the token. This endpoint can be used for
    server-side logging or token blacklisting if implemented.
    """
    logger.info(f"User {current_user.email} logged out")
    return SuccessResponse(message="Logout successful")

@router.get("/me", response_model=UserInfo, summary="Get Current User Info")
def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.
    """
    return UserInfo(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        roles=current_user.roles
    )

@router.post("/refresh", response_model=LoginResponse, summary="Refresh Access Token")
def refresh_token(current_user: User = Depends(get_current_user)):
    """
    Refreshes the access token for the current user.
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    logger.info(f"Access token refreshed for user {current_user.email}")
    return LoginResponse(
        access_token=new_access_token,
        token_type="bearer",
        user_info=UserInfo(
            id=str(current_user.id),
            email=current_user.email,
            full_name=current_user.full_name,
            is_active=current_user.is_active,
            roles=current_user.roles
        )
    )

@router.post("/validate-token", summary="Validate Access Token", response_model=SuccessResponse)
def validate_token(current_user: User = Depends(get_current_user)):
    """
    Validates the current access token. If the token is valid, returns a success message.
    If invalid, the `get_current_user` dependency will raise an exception.
    """
    logger.info(f"Token validated for user {current_user.email}")
    return SuccessResponse(message="Token is valid")

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserInfo, summary="Register a new user")
def register_user(
    email: str,
    password: str,
    full_name: str,
    db: Session = Depends(get_db)
):
    """
    Registers a new user.
    """
    if not email or not password or not full_name:
        raise ValidationError("Email, password, and full name are required")

    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    hashed_password = get_password_hash(password)
    
    new_user = User(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        is_active=True,
        roles=["user"]
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"New user registered: {email}")
    
    return UserInfo(
        id=str(new_user.id),
        email=new_user.email,
        full_name=new_user.full_name,
        is_active=new_user.is_active,
        roles=new_user.roles
    )

# Example of a protected route
@router.get("/protected", summary="Access a protected route")
def protected_route(current_user: User = Depends(get_current_user)):
    """
    An example of a route that requires authentication.
    """
    return {"message": f"Hello, {current_user.email}! This is a protected route."}

# --- Admin-only endpoints ---

def require_admin(current_user: User = Depends(get_current_user)):
    """
    Dependency to check if the user has the 'admin' role.
    """
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@router.get("/admin/dashboard", summary="Admin Dashboard", dependencies=[Depends(require_admin)])
def admin_dashboard(current_user: User = Depends(get_current_user)):
    """
    An example of an admin-only route.
    """
    return {"message": f"Welcome to the admin dashboard, {current_user.email}!"}

@router.get("/users", summary="List all users (Admin only)", dependencies=[Depends(require_admin)])
def list_users(db: Session = Depends(get_db)):
    """
    Retrieves a list of all users.
    """
    users = db.query(User).all()
    return [
        UserInfo(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            roles=user.roles
        ) for user in users
    ]

@router.put("/users/{user_id}/roles", summary="Update user roles (Admin only)", dependencies=[Depends(require_admin)])
def update_user_roles(user_id: str, roles: list[str], db: Session = Depends(get_db)):
    """
    Updates the roles for a specific user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.roles = roles
    db.commit()
    
    logger.info(f"Updated roles for user {user.email} to {roles}")
    return SuccessResponse(message="User roles updated successfully")

@router.put("/users/{user_id}/status", summary="Update user status (Admin only)", dependencies=[Depends(require_admin)])
def update_user_status(user_id: str, is_active: bool, db: Session = Depends(get_db)):
    """
    Updates the active status for a specific user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user.is_active = is_active
    db.commit()
    
    logger.info(f"Updated status for user {user.email} to {'active' if is_active else 'inactive'}")
    return SuccessResponse(message="User status updated successfully")

@router.delete("/users/{user_id}", summary="Delete a user (Admin only)", dependencies=[Depends(require_admin)])
def delete_user(user_id: str, db: Session = Depends(get_db)):
    """
    Deletes a user from the database.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    db.delete(user)
    db.commit()
    
    logger.info(f"Deleted user {user.email}")
    return SuccessResponse(message="User deleted successfully")

# --- Token introspection ---

@router.post("/introspect", summary="Token Introspection")
def introspect_token(token: str, db: Session = Depends(get_db)):
    """
    Introspects a token to check its validity and return its payload.
    This is useful for debugging and for resource servers to validate a token.
    """
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            return {"active": False, "detail": "Invalid token payload"}
            
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user or not user.is_active:
            return {"active": False, "detail": "User not found or inactive"}
            
        return {
            "active": True,
            "sub": user_id,
            "exp": payload.get("exp"),
            "iat": payload.get("iat"),
            "email": user.email,
            "roles": user.roles
        }
    except AuthenticationError as e:
        return {"active": False, "detail": str(e)}
    except Exception as e:
        logger.error(f"Token introspection error: {e}")
        return {"active": False, "detail": "Token introspection failed"}

# --- Password Management ---

@router.post("/forgot-password", summary="Request Password Reset")
def forgot_password(email: str, db: Session = Depends(get_db)):
    """
    Initiates a password reset request. In a real application, this would
    generate a password reset token and send an email to the user.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Note: We don't want to reveal if an email is registered or not
        # for security reasons. So, we return a generic success message.
        logger.info(f"Password reset requested for non-existent email: {email}")
        return SuccessResponse(message="If an account with this email exists, a password reset link has been sent.")

    # In a real app, you would generate a token, save it, and email it.
    # For this example, we'll just log it.
    reset_token = str(uuid.uuid4())
    logger.info(f"Password reset token for {email}: {reset_token}")
    
    # You would typically save this token with an expiry date in the database.
    # user.reset_token = reset_token
    # user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    # db.commit()

    return SuccessResponse(message="If an account with this email exists, a password reset link has been sent.")

@router.post("/reset-password", summary="Reset Password")
def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """
    Resets the user's password using a reset token.
    """
    # In a real app, you would find the user by the reset token.
    # user = db.query(User).filter(User.reset_token == token, User.reset_token_expires > datetime.utcnow()).first()
    
    # For this example, we'll simulate a token check.
    if not token or len(token) < 10: # Dummy validation
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    # Let's assume we found the user by the token.
    # For this example, we'll just pick the first user for demonstration.
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user.hashed_password = get_password_hash(new_password)
    # user.reset_token = None # Clear the reset token
    # user.reset_token_expires = None
    db.commit()
    
    logger.info(f"Password has been reset for user {user.email}")
    return SuccessResponse(message="Password has been reset successfully.")

@router.put("/change-password", summary="Change Password for Authenticated User")
def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows an authenticated user to change their own password.
    """
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")
    
    current_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    logger.info(f"User {current_user.email} changed their password.")
    return SuccessResponse(message="Password changed successfully.")