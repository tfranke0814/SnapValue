from fastapi import HTTPException, status
from datetime import datetime, timedelta
from typing import Optional, Any
import logging

def create_response(success: bool = True, message: str = "Success", data: Any = None) -> dict:
    """Create a standardized API response"""
    return {
        "success": success,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

def create_error_response(error: str, message: str, status_code: int = 400) -> HTTPException:
    """Create a standardized error response"""
    return HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "error": error,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    )

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)
