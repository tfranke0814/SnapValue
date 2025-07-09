import os
import magic
from PIL import Image
from io import BytesIO
from typing import Dict, List, Optional, Tuple
import hashlib
import mimetypes

from app.core.config import settings
from app.utils.exceptions import ValidationError, FileProcessingError
from app.utils.logging import get_logger

logger = get_logger(__name__)

class ImageValidator:
    """Image validation utility class"""
    
    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_types = settings.allowed_file_types_list
        self.max_dimensions = (4096, 4096)  # Max width, height
        self.min_dimensions = (32, 32)     # Min width, height
        
    def validate_file(self, file_content: bytes, filename: str) -> Dict[str, any]:
        """
        Comprehensive file validation
        Returns validation results with metadata
        """
        validation_result = {
            'valid': False,
            'errors': [],
            'metadata': {},
            'file_info': {}
        }
        
        try:
            # Basic file validation
            self._validate_file_size(file_content)
            self._validate_file_type(file_content, filename)
            
            # Image-specific validation
            image_info = self._validate_image_content(file_content)
            validation_result['file_info'] = image_info
            
            # Security validation
            self._validate_file_security(file_content, filename)
            
            # Generate metadata
            validation_result['metadata'] = self._generate_metadata(file_content, filename, image_info)
            
            validation_result['valid'] = True
            logger.info(f"File validation successful for {filename}")
            
        except (ValidationError, FileProcessingError) as e:
            validation_result['errors'].append(str(e))
            logger.warning(f"File validation failed for {filename}: {e}")
            
        return validation_result
    
    def _validate_file_size(self, file_content: bytes):
        """Validate file size"""
        if len(file_content) > self.max_file_size:
            raise ValidationError(
                f"File size {len(file_content)} exceeds maximum allowed size {self.max_file_size}",
                field="file_size"
            )
        
        if len(file_content) == 0:
            raise ValidationError("File is empty", field="file_size")
    
    def _validate_file_type(self, file_content: bytes, filename: str):
        """Validate file type using both extension and magic bytes"""
        # Check file extension
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            raise ValidationError(
                f"File extension {file_ext} not allowed",
                field="file_type"
            )
        
        # Check MIME type using magic bytes
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
        except Exception:
            # Fallback to mimetypes if magic fails
            mime_type = mimetypes.guess_type(filename)[0]
        
        if mime_type not in self.allowed_types:
            raise ValidationError(
                f"File type {mime_type} not allowed",
                field="mime_type"
            )
    
    def _validate_image_content(self, file_content: bytes) -> Dict[str, any]:
        """Validate image content and extract information"""
        try:
            # Open image with PIL
            image = Image.open(BytesIO(file_content))
            
            # Get image information
            image_info = {
                'format': image.format,
                'mode': image.mode,
                'size': image.size,
                'width': image.width,
                'height': image.height,
                'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            }
            
            # Validate dimensions
            if image.width > self.max_dimensions[0] or image.height > self.max_dimensions[1]:
                raise ValidationError(
                    f"Image dimensions {image.width}x{image.height} exceed maximum {self.max_dimensions}",
                    field="dimensions"
                )
            
            if image.width < self.min_dimensions[0] or image.height < self.min_dimensions[1]:
                raise ValidationError(
                    f"Image dimensions {image.width}x{image.height} below minimum {self.min_dimensions}",
                    field="dimensions"
                )
            
            # Validate image format
            if image.format not in ['JPEG', 'PNG', 'WEBP']:
                raise ValidationError(
                    f"Image format {image.format} not supported",
                    field="format"
                )
            
            return image_info
            
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise FileProcessingError(f"Failed to process image: {str(e)}")
    
    def _validate_file_security(self, file_content: bytes, filename: str):
        """Security validation to prevent malicious files"""
        # Check for suspicious file headers
        suspicious_headers = [
            b'<?php',
            b'<script',
            b'javascript:',
            b'<html',
            b'<body',
            b'MZ',  # Windows executable
            b'\x7fELF',  # Linux executable
        ]
        
        for header in suspicious_headers:
            if file_content.startswith(header):
                raise ValidationError(
                    "File contains suspicious content",
                    field="security"
                )
        
        # Check filename for suspicious patterns
        suspicious_patterns = ['..', '/', '\\', '<', '>', '|', ':', '*', '?', '"']
        for pattern in suspicious_patterns:
            if pattern in filename:
                raise ValidationError(
                    f"Filename contains suspicious pattern: {pattern}",
                    field="filename"
                )
    
    def _generate_metadata(self, file_content: bytes, filename: str, image_info: Dict) -> Dict[str, any]:
        """Generate file metadata"""
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        metadata = {
            'filename': filename,
            'file_size': len(file_content),
            'file_hash': file_hash,
            'mime_type': magic.from_buffer(file_content, mime=True),
            'image_info': image_info,
            'validation_timestamp': None  # Will be set by service
        }
        
        return metadata

def validate_image_file(file_content: bytes, filename: str) -> Dict[str, any]:
    """Convenience function for image validation"""
    validator = ImageValidator()
    return validator.validate_file(file_content, filename)

def is_valid_image_type(mime_type: str) -> bool:
    """Check if MIME type is valid for images"""
    return mime_type in settings.allowed_file_types_list

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove path components
    filename = os.path.basename(filename)
    
    # Replace suspicious characters
    safe_chars = []
    for char in filename:
        if char.isalnum() or char in '.-_':
            safe_chars.append(char)
        else:
            safe_chars.append('_')
    
    sanitized = ''.join(safe_chars)
    
    # Ensure filename is not empty and has reasonable length
    if not sanitized or sanitized.startswith('.'):
        sanitized = 'image' + sanitized
    
    if len(sanitized) > 255:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:255-len(ext)] + ext
    
    return sanitized

def get_image_dimensions(file_content: bytes) -> Tuple[int, int]:
    """Get image dimensions without full validation"""
    try:
        image = Image.open(BytesIO(file_content))
        return image.width, image.height
    except Exception as e:
        raise FileProcessingError(f"Failed to get image dimensions: {str(e)}")

def is_image_corrupted(file_content: bytes) -> bool:
    """Check if image is corrupted"""
    try:
        image = Image.open(BytesIO(file_content))
        image.verify()
        return False
    except Exception:
        return True