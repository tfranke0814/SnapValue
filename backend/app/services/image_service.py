from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.base_service import BaseService
from app.services.storage_factory import get_storage_service
from app.utils.image_validation import ImageValidator, validate_image_file
from app.utils.file_processing import FileProcessor, extract_file_metadata, create_image_thumbnails
from app.utils.exceptions import ValidationError, FileProcessingError
from app.utils.logging import get_logger, log_service_call, log_service_result
from app.core.registry import registry

logger = get_logger(__name__)

class ImageService(BaseService):
    """Service for handling image uploads and processing"""
    
    def __init__(self, db: Optional[Session] = None):
        super().__init__(db)
        self.validator = ImageValidator()
        self.processor = FileProcessor()
        self.storage_service = get_storage_service(db)
    
    def validate_input(self, data) -> bool:
        """Validate input for image processing"""
        if not isinstance(data, dict):
            return False
        
        required_fields = ['file_content', 'filename']
        return all(field in data for field in required_fields)
    
    def process(self, data: Dict) -> Dict:
        """Process image upload - main entry point"""
        if not self.validate_input(data):
            raise ValidationError("Invalid input data for image processing")
        
        return self.upload_image(
            data['file_content'],
            data['filename'],
            data.get('user_id'),
            data.get('metadata', {})
        )
    
    def upload_image(
        self,
        file_content: bytes,
        filename: str,
        user_id: Optional[int] = None,
        additional_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Complete image upload pipeline
        
        Args:
            file_content: Raw file content
            filename: Original filename
            user_id: User ID for the upload
            additional_metadata: Additional metadata to store
            
        Returns:
            Dictionary with upload results and metadata
        """
        log_service_call("ImageService", "upload_image", 
                        filename=filename, user_id=user_id)
        
        try:
            # Step 1: Validate image
            validation_result = self.validator.validate_file(file_content, filename)
            
            if not validation_result['valid']:
                raise ValidationError(
                    f"Image validation failed: {', '.join(validation_result['errors'])}"
                )
            
            # Step 2: Extract metadata
            metadata = self.processor.extract_metadata(file_content, filename)
            
            # Step 3: Create thumbnails
            thumbnails = self.processor.create_thumbnails(file_content)
            
            # Step 4: Optimize original image
            optimized_image = self.processor.optimize_image(file_content)
            
            # Step 5: Upload to storage
            upload_results = self._upload_to_storage(
                optimized_image, filename, metadata, thumbnails, user_id, additional_metadata
            )
            
            # Step 6: Prepare response
            result = {
                'upload_id': upload_results['upload_id'],
                'original_image': upload_results['original'],
                'thumbnails': upload_results['thumbnails'],
                'metadata': upload_results['metadata'],
                'validation_info': validation_result,
                'processing_info': {
                    'optimized_size': len(optimized_image),
                    'original_size': len(file_content),
                    'compression_ratio': len(optimized_image) / len(file_content),
                    'thumbnails_created': len(thumbnails)
                },
                'uploaded_at': datetime.utcnow().isoformat()
            }
            
            log_service_result("ImageService", "upload_image", True, 
                             upload_id=upload_results['upload_id'],
                             original_size=len(file_content),
                             optimized_size=len(optimized_image))
            
            return result
            
        except Exception as e:
            self.log_error(e, "upload_image")
            raise
    
    def _upload_to_storage(
        self,
        optimized_image: bytes,
        filename: str,
        metadata: Dict,
        thumbnails: Dict[str, bytes],
        user_id: Optional[int],
        additional_metadata: Optional[Dict]
    ) -> Dict:
        """Upload image and thumbnails to storage"""
        
        # Generate upload ID
        upload_id = f"img_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{user_id or 'anon'}"
        
        # Prepare storage metadata
        storage_metadata = {
            'upload_id': upload_id,
            'user_id': str(user_id) if user_id else 'anonymous',
            'uploaded_at': datetime.utcnow().isoformat(),
            'file_metadata': metadata
        }
        
        if additional_metadata:
            storage_metadata.update(additional_metadata)
        
        # Upload original image
        original_result = self.storage_service.upload_file(
            optimized_image,
            filename,
            storage_metadata,
            f"images/{upload_id}"
        )
        
        # Upload thumbnails
        thumbnail_results = {}
        for size, thumbnail_data in thumbnails.items():
            thumbnail_filename = f"thumb_{size}_{filename}"
            thumbnail_result = self.storage_service.upload_file(
                thumbnail_data,
                thumbnail_filename,
                {**storage_metadata, 'thumbnail_size': size},
                f"images/{upload_id}/thumbnails"
            )
            thumbnail_results[size] = thumbnail_result
        
        return {
            'upload_id': upload_id,
            'original': original_result,
            'thumbnails': thumbnail_results,
            'metadata': storage_metadata
        }
    
    def get_image_info(self, blob_name: str) -> Dict:
        """Get image information from storage"""
        log_service_call("ImageService", "get_image_info", blob_name=blob_name)
        
        try:
            metadata = self.storage_service.get_file_metadata(blob_name)
            
            log_service_result("ImageService", "get_image_info", True, 
                             blob_name=blob_name)
            
            return metadata
            
        except Exception as e:
            self.log_error(e, "get_image_info")
            raise
    
    def download_image(self, blob_name: str) -> bytes:
        """Download image from storage"""
        log_service_call("ImageService", "download_image", blob_name=blob_name)
        
        try:
            file_content = self.storage_service.download_file(blob_name)
            
            log_service_result("ImageService", "download_image", True, 
                             blob_name=blob_name, size=len(file_content))
            
            return file_content
            
        except Exception as e:
            self.log_error(e, "download_image")
            raise
    
    def delete_image(self, blob_name: str) -> bool:
        """Delete image from storage"""
        log_service_call("ImageService", "delete_image", blob_name=blob_name)
        
        try:
            result = self.storage_service.delete_file(blob_name)
            
            log_service_result("ImageService", "delete_image", result, 
                             blob_name=blob_name)
            
            return result
            
        except Exception as e:
            self.log_error(e, "delete_image")
            raise
    
    def list_user_images(self, user_id: int, limit: int = 50) -> List[Dict]:
        """List images uploaded by a user"""
        log_service_call("ImageService", "list_user_images", 
                        user_id=user_id, limit=limit)
        
        try:
            prefix = f"images/img_*_{user_id}"
            files = self.storage_service.list_files(prefix=prefix, limit=limit)
            
            log_service_result("ImageService", "list_user_images", True, 
                             user_id=user_id, count=len(files))
            
            return files
            
        except Exception as e:
            self.log_error(e, "list_user_images")
            raise
    
    def resize_image(self, blob_name: str, max_width: int, max_height: int) -> bytes:
        """Resize an existing image"""
        log_service_call("ImageService", "resize_image", 
                        blob_name=blob_name, max_width=max_width, max_height=max_height)
        
        try:
            # Download original image
            original_content = self.storage_service.download_file(blob_name)
            
            # Resize image
            resized_content = self.processor.resize_image(original_content, max_width, max_height)
            
            log_service_result("ImageService", "resize_image", True, 
                             blob_name=blob_name, 
                             original_size=len(original_content),
                             resized_size=len(resized_content))
            
            return resized_content
            
        except Exception as e:
            self.log_error(e, "resize_image")
            raise
    
    def convert_image_format(self, blob_name: str, target_format: str) -> bytes:
        """Convert image to different format"""
        log_service_call("ImageService", "convert_image_format", 
                        blob_name=blob_name, target_format=target_format)
        
        try:
            # Download original image
            original_content = self.storage_service.download_file(blob_name)
            
            # Convert format
            converted_content = self.processor.convert_format(original_content, target_format)
            
            log_service_result("ImageService", "convert_image_format", True, 
                             blob_name=blob_name, target_format=target_format,
                             original_size=len(original_content),
                             converted_size=len(converted_content))
            
            return converted_content
            
        except Exception as e:
            self.log_error(e, "convert_image_format")
            raise
    
    def health_check(self) -> bool:
        """Health check for image service"""
        try:
            # Check storage service health
            storage_health = self.storage_service.health_check()
            return storage_health
        except Exception as e:
            self.log_error(e, "health_check")
            return False

# Register service
registry.register("image_service", ImageService, singleton=False)