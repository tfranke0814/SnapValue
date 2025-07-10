from typing import Union
from app.core.config import settings
from app.services.local_storage_service import LocalStorageService
from app.services.storage_service import StorageService
from app.utils.logging import get_logger

logger = get_logger(__name__)

def get_storage_service(db=None) -> Union[LocalStorageService, StorageService]:
    """
    Factory function to get the appropriate storage service based on configuration
    
    Args:
        db: Optional database session
        
    Returns:
        LocalStorageService or StorageService (GCS) based on STORAGE_TYPE setting
    """
    storage_type = settings.STORAGE_TYPE.lower()
    
    if storage_type == "gcs":
        logger.info("Using Google Cloud Storage service")
        return StorageService(db)
    else:
        logger.info("Using Local Storage service")
        return LocalStorageService(db)

def get_storage_config() -> dict:
    """Get current storage configuration"""
    return {
        'storage_type': settings.STORAGE_TYPE,
        'max_file_size': settings.MAX_FILE_SIZE,
        'allowed_file_types': settings.allowed_file_types_list,
        'local_storage_path': getattr(settings, 'LOCAL_STORAGE_PATH', None),
        'gcs_bucket': getattr(settings, 'GCS_BUCKET_NAME', None),
        'gcs_project': getattr(settings, 'GOOGLE_CLOUD_PROJECT', None)
    }
