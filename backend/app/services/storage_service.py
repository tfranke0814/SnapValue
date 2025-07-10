import os
import uuid
from datetime import datetime
from typing import Dict, Optional, Tuple, List
from io import BytesIO
from google.cloud import storage
from google.cloud.exceptions import NotFound, GoogleCloudError

from app.core.config import settings
from app.services.base_service import BaseService
from app.utils.exceptions import ExternalServiceError, ConfigurationError, FileProcessingError
from app.utils.logging import get_logger, log_service_call, log_service_result
from app.utils.image_validation import sanitize_filename

logger = get_logger(__name__)

class StorageService(BaseService):
    """Google Cloud Storage service for file operations"""
    
    def __init__(self, db=None):
        super().__init__(db)
        self.client = None
        self.bucket = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Cloud Storage client"""
        try:
            # Check if credentials are configured
            if not settings.GOOGLE_CLOUD_PROJECT:
                raise ConfigurationError("GOOGLE_CLOUD_PROJECT not configured")
            
            if not settings.GCS_BUCKET_NAME:
                raise ConfigurationError("GCS_BUCKET_NAME not configured")
            
            # Initialize client
            self.client = storage.Client(project=settings.GOOGLE_CLOUD_PROJECT)
            self.bucket = self.client.bucket(settings.GCS_BUCKET_NAME)
            
            log_service_call("StorageService", "initialize_client", 
                           bucket=settings.GCS_BUCKET_NAME, 
                           project=settings.GOOGLE_CLOUD_PROJECT)
            
        except Exception as e:
            self.log_error(e, "initialize_client")
            raise ConfigurationError(f"Failed to initialize Google Cloud Storage: {str(e)}")
    
    def validate_input(self, data) -> bool:
        """Validate input for storage operations"""
        if not isinstance(data, dict):
            return False
        
        required_fields = ['file_content', 'filename']
        return all(field in data for field in required_fields)
    
    def process(self, data: Dict) -> Dict:
        """Process file upload - main entry point"""
        if not self.validate_input(data):
            raise FileProcessingError("Invalid input data for storage")
        
        return self.upload_file(
            data['file_content'],
            data['filename'],
            data.get('metadata', {}),
            data.get('folder', 'uploads')
        )
    
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        metadata: Optional[Dict] = None,
        folder: str = 'uploads'
    ) -> Dict:
        """
        Upload file to Google Cloud Storage
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            metadata: Optional metadata dictionary
            folder: Storage folder/prefix
            
        Returns:
            Dictionary with upload results
        """
        log_service_call("StorageService", "upload_file", 
                        filename=filename, folder=folder)
        
        try:
            # Generate unique filename
            unique_filename = self._generate_unique_filename(filename)
            blob_name = f"{folder}/{unique_filename}"
            
            # Create blob
            blob = self.bucket.blob(blob_name)
            
            # Set metadata
            if metadata:
                blob.metadata = metadata
            
            # Set content type
            content_type = self._get_content_type(filename)
            blob.content_type = content_type
            
            # Upload file
            blob.upload_from_string(file_content, content_type=content_type)
            
            # Generate URLs
            public_url = blob.public_url
            signed_url = blob.generate_signed_url(
                expiration=datetime.utcnow().replace(year=datetime.utcnow().year + 1),
                method='GET'
            )
            
            result = {
                'blob_name': blob_name,
                'public_url': public_url,
                'signed_url': signed_url,
                'bucket': settings.GCS_BUCKET_NAME,
                'size': len(file_content),
                'content_type': content_type,
                'uploaded_at': datetime.utcnow().isoformat()
            }
            
            log_service_result("StorageService", "upload_file", True, 
                             blob_name=blob_name, size=len(file_content))
            
            return result
            
        except GoogleCloudError as e:
            self.log_error(e, "upload_file")
            raise ExternalServiceError("Google Cloud Storage", f"Upload failed: {str(e)}")
        except Exception as e:
            self.log_error(e, "upload_file")
            raise FileProcessingError(f"File upload failed: {str(e)}")
    
    def download_file(self, blob_name: str) -> bytes:
        """Download file from Google Cloud Storage"""
        log_service_call("StorageService", "download_file", blob_name=blob_name)
        
        try:
            blob = self.bucket.blob(blob_name)
            
            if not blob.exists():
                raise FileProcessingError(f"File {blob_name} not found")
            
            file_content = blob.download_as_bytes()
            
            log_service_result("StorageService", "download_file", True, 
                             blob_name=blob_name, size=len(file_content))
            
            return file_content
            
        except NotFound:
            raise FileProcessingError(f"File {blob_name} not found")
        except GoogleCloudError as e:
            self.log_error(e, "download_file")
            raise ExternalServiceError("Google Cloud Storage", f"Download failed: {str(e)}")
        except Exception as e:
            self.log_error(e, "download_file")
            raise FileProcessingError(f"File download failed: {str(e)}")
    
    def delete_file(self, blob_name: str) -> bool:
        """Delete file from Google Cloud Storage"""
        log_service_call("StorageService", "delete_file", blob_name=blob_name)
        
        try:
            blob = self.bucket.blob(blob_name)
            
            if not blob.exists():
                log_service_result("StorageService", "delete_file", False, 
                                 blob_name=blob_name, reason="File not found")
                return False
            
            blob.delete()
            
            log_service_result("StorageService", "delete_file", True, blob_name=blob_name)
            return True
            
        except GoogleCloudError as e:
            self.log_error(e, "delete_file")
            raise ExternalServiceError("Google Cloud Storage", f"Delete failed: {str(e)}")
        except Exception as e:
            self.log_error(e, "delete_file")
            raise FileProcessingError(f"File deletion failed: {str(e)}")
    
    def file_exists(self, blob_name: str) -> bool:
        """Check if file exists in Google Cloud Storage"""
        try:
            blob = self.bucket.blob(blob_name)
            return blob.exists()
        except Exception as e:
            self.log_error(e, "file_exists")
            return False
    
    def get_file_metadata(self, blob_name: str) -> Dict:
        """Get file metadata from Google Cloud Storage"""
        log_service_call("StorageService", "get_file_metadata", blob_name=blob_name)
        
        try:
            blob = self.bucket.blob(blob_name)
            blob.reload()
            
            if not blob.exists():
                raise FileProcessingError(f"File {blob_name} not found")
            
            metadata = {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created.isoformat() if blob.time_created else None,
                'updated': blob.updated.isoformat() if blob.updated else None,
                'etag': blob.etag,
                'md5_hash': blob.md5_hash,
                'crc32c': blob.crc32c,
                'metadata': blob.metadata or {},
                'public_url': blob.public_url
            }
            
            log_service_result("StorageService", "get_file_metadata", True, 
                             blob_name=blob_name, size=blob.size)
            
            return metadata
            
        except NotFound:
            raise FileProcessingError(f"File {blob_name} not found")
        except GoogleCloudError as e:
            self.log_error(e, "get_file_metadata")
            raise ExternalServiceError("Google Cloud Storage", f"Get metadata failed: {str(e)}")
        except Exception as e:
            self.log_error(e, "get_file_metadata")
            raise FileProcessingError(f"Get file metadata failed: {str(e)}")
    
    def list_files(self, prefix: str = None, limit: int = 100) -> List[Dict]:
        """List files in Google Cloud Storage"""
        log_service_call("StorageService", "list_files", prefix=prefix, limit=limit)
        
        try:
            blobs = self.bucket.list_blobs(prefix=prefix, max_results=limit)
            
            files = []
            for blob in blobs:
                files.append({
                    'name': blob.name,
                    'size': blob.size,
                    'content_type': blob.content_type,
                    'created': blob.time_created.isoformat() if blob.time_created else None,
                    'updated': blob.updated.isoformat() if blob.updated else None,
                    'public_url': blob.public_url
                })
            
            log_service_result("StorageService", "list_files", True, 
                             count=len(files), prefix=prefix)
            
            return files
            
        except GoogleCloudError as e:
            self.log_error(e, "list_files")
            raise ExternalServiceError("Google Cloud Storage", f"List files failed: {str(e)}")
        except Exception as e:
            self.log_error(e, "list_files")
            raise FileProcessingError(f"List files failed: {str(e)}")
    
    def _generate_unique_filename(self, filename: str) -> str:
        """Generate unique filename for storage"""
        # Sanitize filename
        safe_filename = sanitize_filename(filename)
        
        # Add timestamp and UUID
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        
        name, ext = os.path.splitext(safe_filename)
        unique_filename = f"{timestamp}_{unique_id}_{name}{ext}"
        
        return unique_filename
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type based on filename"""
        ext = os.path.splitext(filename)[1].lower()
        
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    def health_check(self) -> bool:
        """Health check for storage service"""
        try:
            # Simple bucket access check
            self.bucket.reload()
            return True
        except Exception as e:
            self.log_error(e, "health_check")
            return False