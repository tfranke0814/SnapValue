"""
Tests for Image Service - Step 3
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from PIL import Image
from sqlalchemy.orm import Session

from app.services.image_service import ImageService
from app.utils.exceptions import ValidationError, FileProcessingError
from app.utils.image_validation import ImageValidator
from app.utils.file_processing import FileProcessor
from app.services.storage_service import StorageService


class TestImageService:
    """Test cases for ImageService class"""
    
    def test_service_initialization(self):
        """Test ImageService initialization"""
        mock_db = Mock(spec=Session)
        
        with patch('app.services.image_service.StorageService') as mock_storage_service:
            service = ImageService(db=mock_db)
            
            assert service.db == mock_db
            assert isinstance(service.validator, ImageValidator)
            assert isinstance(service.processor, FileProcessor)
            mock_storage_service.assert_called_once_with(mock_db)
    
    def test_validate_input_valid(self):
        """Test input validation with valid data"""
        mock_db = Mock(spec=Session)
        
        with patch('app.services.image_service.StorageService'):
            service = ImageService(db=mock_db)
            
            valid_data = {
                'file_content': b'test content',
                'filename': 'test.jpg'
            }
            
            assert service.validate_input(valid_data) is True
    
    def test_validate_input_invalid_type(self):
        """Test input validation with invalid data type"""
        mock_db = Mock(spec=Session)
        
        with patch('app.services.image_service.StorageService'):
            service = ImageService(db=mock_db)
            
            # Test with non-dict input
            assert service.validate_input("not a dict") is False
            assert service.validate_input(None) is False
            assert service.validate_input(123) is False
    
    def test_validate_input_missing_required_fields(self):
        """Test input validation with missing required fields"""
        mock_db = Mock(spec=Session)
        
        with patch('app.services.image_service.StorageService'):
            service = ImageService(db=mock_db)
            
            # Test with missing file_content
            invalid_data = {'filename': 'test.jpg'}
            assert service.validate_input(invalid_data) is False
            
            # Test with missing filename
            invalid_data = {'file_content': b'test content'}
            assert service.validate_input(invalid_data) is False
            
            # Test with empty dict
            assert service.validate_input({}) is False
    
    @patch('app.services.image_service.StorageService')
    def test_process_success(self, mock_storage_service):
        """Test successful image processing"""
        mock_db = Mock(spec=Session)
        service = ImageService(db=mock_db)
        
        # Mock upload_image method
        service.upload_image = Mock(return_value={'success': True, 'file_id': 'test123'})
        
        data = {
            'file_content': b'test content',
            'filename': 'test.jpg',
            'user_id': 123,
            'metadata': {'description': 'test image'}
        }
        
        result = service.process(data)
        
        assert result['success'] is True
        assert result['file_id'] == 'test123'
        service.upload_image.assert_called_once_with(
            b'test content',
            'test.jpg',
            123,
            {'description': 'test image'}
        )
    
    @patch('app.services.image_service.StorageService')
    def test_process_invalid_input(self, mock_storage_service):
        """Test image processing with invalid input"""
        mock_db = Mock(spec=Session)
        service = ImageService(db=mock_db)
        
        invalid_data = {'filename': 'test.jpg'}  # Missing file_content
        
        with pytest.raises(ValidationError) as exc_info:
            service.process(invalid_data)
        
        assert "Invalid input data for image processing" in str(exc_info.value)
    
    @patch('app.services.image_service.StorageService')
    @patch('app.utils.image_validation.validate_image_file')
    def test_upload_image_success(self, mock_validate, mock_storage_service):
        """Test successful image upload"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock validation success
        mock_validate.return_value = {
            'valid': True,
            'errors': [],
            'metadata': {'file_size': 1024, 'image_format': 'JPEG'},
            'file_info': {'width': 100, 'height': 100}
        }
        
        # Mock file processing
        mock_processor = Mock()
        mock_processor.extract_metadata.return_value = {
            'filename': 'test.jpg',
            'file_size': 1024,
            'image_metadata': {'width': 100, 'height': 100}
        }
        mock_processor.generate_thumbnails.return_value = [
            ((150, 150), b'thumb1'),
            ((300, 300), b'thumb2')
        ]
        mock_processor.optimize_image.return_value = b'optimized content'
        
        # Mock storage upload
        mock_storage.upload_file.return_value = {
            'success': True,
            'file_path': 'test.jpg',
            'upload_url': 'https://storage.googleapis.com/bucket/test.jpg'
        }
        
        service = ImageService(db=mock_db)
        service.processor = mock_processor
        
        result = service.upload_image(b'test content', 'test.jpg', 123)
        
        assert result['success'] is True
        assert result['file_path'] == 'test.jpg'
        assert result['upload_url'] == 'https://storage.googleapis.com/bucket/test.jpg'
        assert 'metadata' in result
        assert 'thumbnails' in result
        
        # Verify validation was called
        mock_validate.assert_called_once_with(b'test content', 'test.jpg')
        
        # Verify processing was called
        mock_processor.extract_metadata.assert_called_once()
        mock_processor.generate_thumbnails.assert_called_once()
        mock_processor.optimize_image.assert_called_once()
        
        # Verify storage upload was called
        mock_storage.upload_file.assert_called()
    
    @patch('app.services.image_service.StorageService')
    @patch('app.utils.image_validation.validate_image_file')
    def test_upload_image_validation_failure(self, mock_validate, mock_storage_service):
        """Test image upload with validation failure"""
        mock_db = Mock(spec=Session)
        service = ImageService(db=mock_db)
        
        # Mock validation failure
        mock_validate.return_value = {
            'valid': False,
            'errors': [{'code': 'INVALID_FORMAT', 'message': 'Invalid image format'}],
            'metadata': {},
            'file_info': {}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            service.upload_image(b'invalid content', 'test.txt', 123)
        
        assert "Image validation failed" in str(exc_info.value)
    
    @patch('app.services.image_service.StorageService')
    @patch('app.utils.image_validation.validate_image_file')
    def test_upload_image_processing_failure(self, mock_validate, mock_storage_service):
        """Test image upload with processing failure"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock validation success
        mock_validate.return_value = {
            'valid': True,
            'errors': [],
            'metadata': {'file_size': 1024},
            'file_info': {'width': 100, 'height': 100}
        }
        
        # Mock processing failure
        mock_processor = Mock()
        mock_processor.extract_metadata.side_effect = FileProcessingError("Processing failed")
        
        service = ImageService(db=mock_db)
        service.processor = mock_processor
        
        with pytest.raises(FileProcessingError) as exc_info:
            service.upload_image(b'test content', 'test.jpg', 123)
        
        assert "Processing failed" in str(exc_info.value)
    
    @patch('app.services.image_service.StorageService')
    @patch('app.utils.image_validation.validate_image_file')
    def test_upload_image_storage_failure(self, mock_validate, mock_storage_service):
        """Test image upload with storage failure"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock validation success
        mock_validate.return_value = {
            'valid': True,
            'errors': [],
            'metadata': {'file_size': 1024},
            'file_info': {'width': 100, 'height': 100}
        }
        
        # Mock processing success
        mock_processor = Mock()
        mock_processor.extract_metadata.return_value = {'filename': 'test.jpg'}
        mock_processor.generate_thumbnails.return_value = []
        mock_processor.optimize_image.return_value = b'optimized content'
        
        # Mock storage failure
        mock_storage.upload_file.side_effect = Exception("Storage error")
        
        service = ImageService(db=mock_db)
        service.processor = mock_processor
        
        with pytest.raises(Exception) as exc_info:
            service.upload_image(b'test content', 'test.jpg', 123)
        
        assert "Storage error" in str(exc_info.value)
    
    @patch('app.services.image_service.StorageService')
    def test_get_image_success(self, mock_storage_service):
        """Test successful image retrieval"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock storage download
        mock_storage.download_file.return_value = {
            'success': True,
            'file_content': b'image content',
            'content_type': 'image/jpeg',
            'file_size': 1024
        }
        
        service = ImageService(db=mock_db)
        
        result = service.get_image('test.jpg')
        
        assert result['success'] is True
        assert result['file_content'] == b'image content'
        assert result['content_type'] == 'image/jpeg'
        assert result['file_size'] == 1024
        
        mock_storage.download_file.assert_called_once_with('test.jpg')
    
    @patch('app.services.image_service.StorageService')
    def test_get_image_not_found(self, mock_storage_service):
        """Test image retrieval when file doesn't exist"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock storage download failure
        mock_storage.download_file.side_effect = FileProcessingError("File not found")
        
        service = ImageService(db=mock_db)
        
        with pytest.raises(FileProcessingError) as exc_info:
            service.get_image('nonexistent.jpg')
        
        assert "File not found" in str(exc_info.value)
    
    @patch('app.services.image_service.StorageService')
    def test_delete_image_success(self, mock_storage_service):
        """Test successful image deletion"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock storage deletion
        mock_storage.delete_file.return_value = {
            'success': True,
            'file_path': 'test.jpg'
        }
        
        service = ImageService(db=mock_db)
        
        result = service.delete_image('test.jpg')
        
        assert result['success'] is True
        assert result['file_path'] == 'test.jpg'
        
        mock_storage.delete_file.assert_called_once_with('test.jpg')
    
    @patch('app.services.image_service.StorageService')
    def test_delete_image_not_found(self, mock_storage_service):
        """Test image deletion when file doesn't exist"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock storage deletion failure
        mock_storage.delete_file.side_effect = FileProcessingError("File not found")
        
        service = ImageService(db=mock_db)
        
        with pytest.raises(FileProcessingError) as exc_info:
            service.delete_image('nonexistent.jpg')
        
        assert "File not found" in str(exc_info.value)
    
    @patch('app.services.image_service.StorageService')
    def test_get_image_metadata_success(self, mock_storage_service):
        """Test successful image metadata retrieval"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock storage metadata retrieval
        mock_storage.get_file_metadata.return_value = {
            'success': True,
            'file_path': 'test.jpg',
            'file_size': 1024,
            'content_type': 'image/jpeg',
            'custom_metadata': {'user_id': '123', 'processed': True}
        }
        
        service = ImageService(db=mock_db)
        
        result = service.get_image_metadata('test.jpg')
        
        assert result['success'] is True
        assert result['file_path'] == 'test.jpg'
        assert result['file_size'] == 1024
        assert result['content_type'] == 'image/jpeg'
        assert result['custom_metadata']['user_id'] == '123'
        
        mock_storage.get_file_metadata.assert_called_once_with('test.jpg')
    
    @patch('app.services.image_service.StorageService')
    def test_list_images_success(self, mock_storage_service):
        """Test successful image listing"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock storage file listing
        mock_storage.list_files.return_value = {
            'success': True,
            'files': [
                {'name': 'image1.jpg', 'size': 1024, 'content_type': 'image/jpeg'},
                {'name': 'image2.png', 'size': 2048, 'content_type': 'image/png'}
            ]
        }
        
        service = ImageService(db=mock_db)
        
        result = service.list_images()
        
        assert result['success'] is True
        assert len(result['files']) == 2
        assert result['files'][0]['name'] == 'image1.jpg'
        assert result['files'][1]['name'] == 'image2.png'
        
        mock_storage.list_files.assert_called_once()
    
    @patch('app.services.image_service.StorageService')
    def test_list_images_with_prefix(self, mock_storage_service):
        """Test image listing with prefix filter"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock storage file listing
        mock_storage.list_files.return_value = {
            'success': True,
            'files': []
        }
        
        service = ImageService(db=mock_db)
        
        result = service.list_images(prefix='user123/')
        
        assert result['success'] is True
        mock_storage.list_files.assert_called_once_with(prefix='user123/')
    
    @patch('app.services.image_service.StorageService')
    def test_generate_image_url_success(self, mock_storage_service):
        """Test successful image URL generation"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock storage URL generation
        mock_storage.generate_signed_url.return_value = {
            'success': True,
            'signed_url': 'https://signed-url.com/test.jpg',
            'expires_in': 3600
        }
        
        service = ImageService(db=mock_db)
        
        result = service.generate_image_url('test.jpg', expiration=3600)
        
        assert result['success'] is True
        assert result['signed_url'] == 'https://signed-url.com/test.jpg'
        assert result['expires_in'] == 3600
        
        mock_storage.generate_signed_url.assert_called_once_with('test.jpg', expiration=3600)
    
    @patch('app.services.image_service.StorageService')
    def test_process_image_transformations(self, mock_storage_service):
        """Test image processing with transformations"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock processor methods
        mock_processor = Mock()
        mock_processor.resize_image.return_value = b'resized image'
        mock_processor.convert_format.return_value = b'converted image'
        mock_processor.optimize_image.return_value = b'optimized image'
        
        service = ImageService(db=mock_db)
        service.processor = mock_processor
        
        # Mock storage download
        mock_storage.download_file.return_value = {
            'success': True,
            'file_content': b'original image',
            'content_type': 'image/jpeg',
            'file_size': 1024
        }
        
        # Mock storage upload
        mock_storage.upload_file.return_value = {
            'success': True,
            'file_path': 'transformed_test.jpg',
            'upload_url': 'https://storage.googleapis.com/bucket/transformed_test.jpg'
        }
        
        transformations = {
            'resize': {'width': 300, 'height': 200},
            'format': 'PNG',
            'optimize': True
        }
        
        result = service.process_image_transformations('test.jpg', transformations)
        
        assert result['success'] is True
        assert result['file_path'] == 'transformed_test.jpg'
        
        # Verify transformations were applied
        mock_processor.resize_image.assert_called_once()
        mock_processor.convert_format.assert_called_once()
        mock_processor.optimize_image.assert_called_once()


class TestImageServiceIntegration:
    """Integration tests for ImageService"""
    
    @patch('app.services.image_service.StorageService')
    @patch('app.utils.image_validation.validate_image_file')
    def test_complete_image_workflow(self, mock_validate, mock_storage_service):
        """Test complete image workflow: upload, get, metadata, delete"""
        mock_db = Mock(spec=Session)
        mock_storage = Mock()
        mock_storage_service.return_value = mock_storage
        
        # Mock validation success
        mock_validate.return_value = {
            'valid': True,
            'errors': [],
            'metadata': {'file_size': 1024, 'image_format': 'JPEG'},
            'file_info': {'width': 100, 'height': 100}
        }
        
        # Mock file processing
        mock_processor = Mock()
        mock_processor.extract_metadata.return_value = {'filename': 'test.jpg'}
        mock_processor.generate_thumbnails.return_value = []
        mock_processor.optimize_image.return_value = b'optimized content'
        
        # Mock storage operations
        mock_storage.upload_file.return_value = {
            'success': True,
            'file_path': 'test.jpg',
            'upload_url': 'https://storage.googleapis.com/bucket/test.jpg'
        }
        mock_storage.download_file.return_value = {
            'success': True,
            'file_content': b'image content',
            'content_type': 'image/jpeg',
            'file_size': 1024
        }
        mock_storage.get_file_metadata.return_value = {
            'success': True,
            'file_path': 'test.jpg',
            'file_size': 1024,
            'content_type': 'image/jpeg'
        }
        mock_storage.delete_file.return_value = {
            'success': True,
            'file_path': 'test.jpg'
        }
        
        service = ImageService(db=mock_db)
        service.processor = mock_processor
        
        # Upload image
        upload_result = service.upload_image(b'test content', 'test.jpg', 123)
        assert upload_result['success'] is True
        
        # Get image
        get_result = service.get_image('test.jpg')
        assert get_result['success'] is True
        
        # Get metadata
        metadata_result = service.get_image_metadata('test.jpg')
        assert metadata_result['success'] is True
        
        # Delete image
        delete_result = service.delete_image('test.jpg')
        assert delete_result['success'] is True
