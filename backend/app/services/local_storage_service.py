import os
import uuid
import shutil
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
from fastapi import UploadFile

from app.core.config import settings
from app.services.base_service import BaseService
from app.utils.exceptions import FileProcessingError, ConfigurationError
from app.utils.logging import get_logger, log_service_call, log_service_result
from app.utils.image_validation import sanitize_filename

logger = get_logger(__name__)

class LocalStorageService(BaseService):
    """Local file storage service for development and small-scale deployment"""
    
    def __init__(self, db=None):
        super().__init__(db)
        self.storage_path = Path(settings.LOCAL_STORAGE_PATH)
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize local storage directory"""
        try:
            # Create storage directory if it doesn't exist
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            (self.storage_path / "images").mkdir(exist_ok=True)
            (self.storage_path / "temp").mkdir(exist_ok=True)
            
            log_service_call("LocalStorageService", "initialize_storage", 
                           storage_path=str(self.storage_path))
            
        except Exception as e:
            self.log_error(e, "initialize_storage")
            raise ConfigurationError(f"Failed to initialize local storage: {str(e)}")
    
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
    
    async def upload_file_from_upload(
        self,
        image_file: UploadFile,
        folder: str = 'images',
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Upload file from FastAPI UploadFile
        
        Args:
            image_file: FastAPI UploadFile object
            folder: Storage folder/prefix
            user_id: Optional user ID for organization
            
        Returns:
            Dictionary with upload results
        """
        try:
            # Read file content
            file_content = await image_file.read()
            
            # Reset file pointer
            await image_file.seek(0)
            
            # Call main upload method
            return self.upload_file(
                file_content,
                image_file.filename,
                metadata={'content_type': image_file.content_type},
                folder=folder,
                user_id=user_id
            )
            
        except Exception as e:
            self.log_error(e, "upload_file_from_upload")
            raise FileProcessingError(f"File upload failed: {str(e)}")
    
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        metadata: Optional[Dict] = None,
        folder: str = 'images',
        user_id: Optional[int] = None
    ) -> Dict:
        """
        Upload file to local storage
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            metadata: Optional metadata dictionary
            folder: Storage folder/prefix
            user_id: Optional user ID for organization
            
        Returns:
            Dictionary with upload results
        """
        log_service_call("LocalStorageService", "upload_file", 
                        filename=filename, folder=folder, user_id=user_id)
        
        try:
            # Generate unique filename
            unique_filename = self._generate_unique_filename(filename)
            
            # Create file path
            if user_id:
                file_path = self.storage_path / folder / f"user_{user_id}" / unique_filename
            else:
                file_path = self.storage_path / folder / unique_filename
            
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Generate relative path for storage
            relative_path = str(file_path.relative_to(self.storage_path))
            
            # Get content type
            content_type = self._get_content_type(filename)
            
            result = {
                'file_path': str(file_path),
                'relative_path': relative_path,
                'filename': unique_filename,
                'original_filename': filename,
                'size': len(file_content),
                'content_type': content_type,
                'uploaded_at': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            log_service_result("LocalStorageService", "upload_file", True, 
                             file_path=relative_path, size=len(file_content))
            
            return result
            
        except Exception as e:
            self.log_error(e, "upload_file")
            raise FileProcessingError(f"File upload failed: {str(e)}")
    
    def download_file(self, relative_path: str) -> bytes:
        """Download file from local storage"""
        log_service_call("LocalStorageService", "download_file", relative_path=relative_path)
        
        try:
            file_path = self.storage_path / relative_path
            
            if not file_path.exists():
                raise FileProcessingError(f"File {relative_path} not found")
            
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            log_service_result("LocalStorageService", "download_file", True, 
                             relative_path=relative_path, size=len(file_content))
            
            return file_content
            
        except FileNotFoundError:
            raise FileProcessingError(f"File {relative_path} not found")
        except Exception as e:
            self.log_error(e, "download_file")
            raise FileProcessingError(f"File download failed: {str(e)}")
    
    def delete_file(self, relative_path: str) -> bool:
        """Delete file from local storage"""
        log_service_call("LocalStorageService", "delete_file", relative_path=relative_path)
        
        try:
            file_path = self.storage_path / relative_path
            
            if not file_path.exists():
                log_service_result("LocalStorageService", "delete_file", False, 
                                 relative_path=relative_path, reason="File not found")
                return False
            
            file_path.unlink()
            
            log_service_result("LocalStorageService", "delete_file", True, 
                             relative_path=relative_path)
            return True
            
        except Exception as e:
            self.log_error(e, "delete_file")
            raise FileProcessingError(f"File deletion failed: {str(e)}")
    
    def file_exists(self, relative_path: str) -> bool:
        """Check if file exists in local storage"""
        try:
            file_path = self.storage_path / relative_path
            return file_path.exists()
        except Exception as e:
            self.log_error(e, "file_exists")
            return False
    
    def get_file_metadata(self, relative_path: str) -> Dict:
        """Get file metadata from local storage"""
        log_service_call("LocalStorageService", "get_file_metadata", relative_path=relative_path)
        
        try:
            file_path = self.storage_path / relative_path
            
            if not file_path.exists():
                raise FileProcessingError(f"File {relative_path} not found")
            
            stat = file_path.stat()
            
            metadata = {
                'name': file_path.name,
                'path': str(file_path),
                'relative_path': relative_path,
                'size': stat.st_size,
                'content_type': self._get_content_type(file_path.name),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }
            
            log_service_result("LocalStorageService", "get_file_metadata", True, 
                             relative_path=relative_path, size=stat.st_size)
            
            return metadata
            
        except FileNotFoundError:
            raise FileProcessingError(f"File {relative_path} not found")
        except Exception as e:
            self.log_error(e, "get_file_metadata")
            raise FileProcessingError(f"Get file metadata failed: {str(e)}")
    
    def list_files(self, prefix: str = None, limit: int = 100) -> List[Dict]:
        """List files in local storage"""
        log_service_call("LocalStorageService", "list_files", prefix=prefix, limit=limit)
        
        try:
            search_path = self.storage_path
            if prefix:
                search_path = self.storage_path / prefix
            
            files = []
            count = 0
            
            for file_path in search_path.rglob('*'):
                if file_path.is_file() and count < limit:
                    relative_path = str(file_path.relative_to(self.storage_path))
                    stat = file_path.stat()
                    
                    files.append({
                        'name': file_path.name,
                        'relative_path': relative_path,
                        'size': stat.st_size,
                        'content_type': self._get_content_type(file_path.name),
                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
                    count += 1
            
            log_service_result("LocalStorageService", "list_files", True, 
                             count=len(files), prefix=prefix)
            
            return files
            
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
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
            '.tiff': 'image/tiff'
        }
        
        return content_types.get(ext, 'application/octet-stream')
    
    def health_check(self) -> bool:
        """Health check for local storage service"""
        try:
            # Check if storage directory is accessible and writable
            test_file = self.storage_path / "temp" / "health_check.txt"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write test file
            with open(test_file, 'w') as f:
                f.write("health_check")
            
            # Read test file
            with open(test_file, 'r') as f:
                content = f.read()
            
            # Clean up
            test_file.unlink()
            
            return content == "health_check"
            
        except Exception as e:
            self.log_error(e, "health_check")
            return False
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        try:
            stats = {
                'storage_type': 'local',
                'storage_path': str(self.storage_path),
                'total_files': 0,
                'total_size': 0,
                'folders': []
            }
            
            for folder in ['images', 'temp']:
                folder_path = self.storage_path / folder
                if folder_path.exists():
                    file_count = sum(1 for _ in folder_path.rglob('*') if _.is_file())
                    folder_size = sum(f.stat().st_size for f in folder_path.rglob('*') if f.is_file())
                    
                    stats['folders'].append({
                        'name': folder,
                        'file_count': file_count,
                        'size': folder_size
                    })
                    
                    stats['total_files'] += file_count
                    stats['total_size'] += folder_size
            
            return stats
            
        except Exception as e:
            self.log_error(e, "get_storage_stats")
            return {'error': str(e)}
