"""
Tests for Image Validation - Step 3
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from PIL import Image
import hashlib

from app.utils.image_validation import ImageValidator, validate_image_file, sanitize_filename
from app.utils.exceptions import ValidationError, FileProcessingError
from app.core.config import settings


class TestImageValidator:
    """Test cases for ImageValidator class"""
    
    def test_validator_initialization(self):
        """Test ImageValidator initialization"""
        validator = ImageValidator()
        
        assert validator.max_file_size == settings.MAX_FILE_SIZE
        assert validator.allowed_types == settings.allowed_file_types_list
        assert validator.max_dimensions == (4096, 4096)
        assert validator.min_dimensions == (32, 32)
    
    def test_validate_file_size_valid(self):
        """Test file size validation with valid size"""
        validator = ImageValidator()
        
        # Create small test content
        test_content = b"test content"
        
        # Should not raise exception
        try:
            validator._validate_file_size(test_content)
        except ValidationError:
            pytest.fail("Validation should not fail for valid file size")
    
    def test_validate_file_size_too_large(self):
        """Test file size validation with oversized file"""
        validator = ImageValidator()
        
        # Create content larger than max size
        large_content = b"x" * (settings.MAX_FILE_SIZE + 1)
        
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_file_size(large_content)
        
        assert "File size exceeds maximum limit" in str(exc_info.value)
    
    def test_validate_file_size_empty(self):
        """Test file size validation with empty file"""
        validator = ImageValidator()
        
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_file_size(b"")
        
        assert "File is empty" in str(exc_info.value)
    
    @patch('magic.from_buffer')
    def test_validate_file_type_valid_jpeg(self, mock_magic):
        """Test file type validation with valid JPEG"""
        mock_magic.return_value = "image/jpeg"
        validator = ImageValidator()
        
        test_content = b"fake jpeg content"
        filename = "test.jpg"
        
        # Should not raise exception
        try:
            validator._validate_file_type(test_content, filename)
        except ValidationError:
            pytest.fail("Validation should not fail for valid JPEG")
    
    @patch('magic.from_buffer')
    def test_validate_file_type_invalid_mime(self, mock_magic):
        """Test file type validation with invalid MIME type"""
        mock_magic.return_value = "text/plain"
        validator = ImageValidator()
        
        test_content = b"fake text content"
        filename = "test.txt"
        
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_file_type(test_content, filename)
        
        assert "Invalid file type" in str(exc_info.value)
    
    @patch('magic.from_buffer')
    def test_validate_file_type_extension_mismatch(self, mock_magic):
        """Test file type validation with extension mismatch"""
        mock_magic.return_value = "image/jpeg"
        validator = ImageValidator()
        
        test_content = b"fake jpeg content"
        filename = "test.png"  # Extension doesn't match MIME type
        
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_file_type(test_content, filename)
        
        assert "File extension does not match content type" in str(exc_info.value)
    
    def test_validate_image_content_valid(self):
        """Test image content validation with valid image"""
        validator = ImageValidator()
        
        # Create a valid test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        result = validator._validate_image_content(img_content)
        
        assert result['format'] == 'JPEG'
        assert result['width'] == 100
        assert result['height'] == 100
        assert result['mode'] == 'RGB'
    
    def test_validate_image_content_invalid(self):
        """Test image content validation with invalid image"""
        validator = ImageValidator()
        
        invalid_content = b"not an image"
        
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_image_content(invalid_content)
        
        assert "Invalid image format" in str(exc_info.value)
    
    def test_validate_image_content_dimensions_too_large(self):
        """Test image content validation with oversized dimensions"""
        validator = ImageValidator()
        
        # Create image with dimensions larger than max
        img = Image.new('RGB', (5000, 5000), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_image_content(img_content)
        
        assert "Image dimensions exceed maximum" in str(exc_info.value)
    
    def test_validate_image_content_dimensions_too_small(self):
        """Test image content validation with undersized dimensions"""
        validator = ImageValidator()
        
        # Create image with dimensions smaller than min
        img = Image.new('RGB', (20, 20), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_image_content(img_content)
        
        assert "Image dimensions below minimum" in str(exc_info.value)
    
    def test_validate_file_security_safe_filename(self):
        """Test file security validation with safe filename"""
        validator = ImageValidator()
        
        test_content = b"test content"
        safe_filename = "test_image.jpg"
        
        # Should not raise exception
        try:
            validator._validate_file_security(test_content, safe_filename)
        except ValidationError:
            pytest.fail("Validation should not fail for safe filename")
    
    def test_validate_file_security_dangerous_filename(self):
        """Test file security validation with dangerous filename"""
        validator = ImageValidator()
        
        test_content = b"test content"
        dangerous_filename = "../../../etc/passwd"
        
        with pytest.raises(ValidationError) as exc_info:
            validator._validate_file_security(test_content, dangerous_filename)
        
        assert "Potentially dangerous filename" in str(exc_info.value)
    
    def test_generate_metadata(self):
        """Test metadata generation"""
        validator = ImageValidator()
        
        test_content = b"test content"
        filename = "test.jpg"
        image_info = {
            'format': 'JPEG',
            'width': 100,
            'height': 100,
            'mode': 'RGB'
        }
        
        metadata = validator._generate_metadata(test_content, filename, image_info)
        
        assert metadata['original_filename'] == filename
        assert metadata['file_size'] == len(test_content)
        assert metadata['image_format'] == 'JPEG'
        assert metadata['dimensions'] == (100, 100)
        assert 'file_hash' in metadata
        assert 'processed_at' in metadata
    
    @patch('magic.from_buffer')
    def test_validate_file_complete_success(self, mock_magic):
        """Test complete file validation with success"""
        mock_magic.return_value = "image/jpeg"
        validator = ImageValidator()
        
        # Create a valid test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        result = validator.validate_file(img_content, "test.jpg")
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
        assert 'metadata' in result
        assert 'file_info' in result


class TestValidateImageFile:
    """Test cases for validate_image_file function"""
    
    @patch('magic.from_buffer')
    def test_validate_image_file_success(self, mock_magic):
        """Test validate_image_file function with valid image"""
        mock_magic.return_value = "image/jpeg"
        
        # Create a valid test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        result = validate_image_file(img_content, "test.jpg")
        
        assert result['valid'] is True
        assert len(result['errors']) == 0
    
    @patch('magic.from_buffer')
    def test_validate_image_file_failure(self, mock_magic):
        """Test validate_image_file function with invalid image"""
        mock_magic.return_value = "text/plain"
        
        invalid_content = b"not an image"
        
        result = validate_image_file(invalid_content, "test.txt")
        
        assert result['valid'] is False
        assert len(result['errors']) > 0


class TestSanitizeFilename:
    """Test cases for sanitize_filename function"""
    
    def test_sanitize_filename_normal(self):
        """Test sanitizing normal filename"""
        filename = "test_image.jpg"
        result = sanitize_filename(filename)
        
        assert result == "test_image.jpg"
    
    def test_sanitize_filename_with_spaces(self):
        """Test sanitizing filename with spaces"""
        filename = "test image file.jpg"
        result = sanitize_filename(filename)
        
        assert result == "test_image_file.jpg"
    
    def test_sanitize_filename_with_special_chars(self):
        """Test sanitizing filename with special characters"""
        filename = "test@#$%^&*()image.jpg"
        result = sanitize_filename(filename)
        
        assert result == "test_image.jpg"
    
    def test_sanitize_filename_with_path_traversal(self):
        """Test sanitizing filename with path traversal"""
        filename = "../../../etc/passwd"
        result = sanitize_filename(filename)
        
        assert result == "etc_passwd"
    
    def test_sanitize_filename_unicode(self):
        """Test sanitizing filename with unicode characters"""
        filename = "tëst_imägé.jpg"
        result = sanitize_filename(filename)
        
        assert result == "tst_img.jpg"
    
    def test_sanitize_filename_empty(self):
        """Test sanitizing empty filename"""
        filename = ""
        result = sanitize_filename(filename)
        
        assert result == "unnamed_file"
    
    def test_sanitize_filename_only_extension(self):
        """Test sanitizing filename with only extension"""
        filename = ".jpg"
        result = sanitize_filename(filename)
        
        assert result == "unnamed_file.jpg"


class TestImageValidationIntegration:
    """Integration tests for image validation"""
    
    @patch('magic.from_buffer')
    def test_end_to_end_validation_success(self, mock_magic):
        """Test end-to-end validation with valid image"""
        mock_magic.return_value = "image/jpeg"
        
        # Create a valid test image
        img = Image.new('RGB', (500, 300), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        validator = ImageValidator()
        result = validator.validate_file(img_content, "test_photo.jpg")
        
        assert result['valid'] is True
        assert result['file_info']['format'] == 'JPEG'
        assert result['file_info']['width'] == 500
        assert result['file_info']['height'] == 300
        assert result['metadata']['image_format'] == 'JPEG'
        assert result['metadata']['dimensions'] == (500, 300)
        assert result['metadata']['file_size'] > 0
    
    @patch('magic.from_buffer')
    def test_end_to_end_validation_multiple_failures(self, mock_magic):
        """Test end-to-end validation with multiple validation failures"""
        mock_magic.return_value = "text/plain"
        
        # Create invalid content
        invalid_content = b"This is not an image file"
        
        validator = ImageValidator()
        result = validator.validate_file(invalid_content, "not_an_image.txt")
        
        assert result['valid'] is False
        assert len(result['errors']) >= 2  # Should have multiple errors
        
        # Check that errors contain expected messages
        error_messages = [error['message'] for error in result['errors']]
        assert any("Invalid file type" in msg for msg in error_messages)
        assert any("Invalid image format" in msg for msg in error_messages)
