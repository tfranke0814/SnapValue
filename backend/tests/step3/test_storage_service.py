"""
Tests for Storage Service - Step 3
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from google.cloud.exceptions import NotFound, GoogleCloudError
from io import BytesIO

from app.services.storage_service import StorageService
from app.utils.exceptions import ExternalServiceError, ConfigurationError, FileProcessingError
from app.core.config import settings


class TestStorageService:
    """Test cases for StorageService class"""
    
    @patch('app.services.storage_service.storage')
    def test_service_initialization_success(self, mock_storage):
        """Test StorageService initialization with valid configuration"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                assert service.client == mock_client
                assert service.bucket == mock_bucket
                mock_storage.Client.assert_called_once_with(project='test-project')
                mock_client.bucket.assert_called_once_with('test-bucket')
    
    @patch('app.services.storage_service.storage')
    def test_service_initialization_missing_project(self, mock_storage):
        """Test StorageService initialization with missing project configuration"""
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', None):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                with pytest.raises(ConfigurationError) as exc_info:
                    StorageService()
                
                assert "GOOGLE_CLOUD_PROJECT not configured" in str(exc_info.value)
    
    @patch('app.services.storage_service.storage')
    def test_service_initialization_missing_bucket(self, mock_storage):
        """Test StorageService initialization with missing bucket configuration"""
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', None):
                with pytest.raises(ConfigurationError) as exc_info:
                    StorageService()
                
                assert "GCS_BUCKET_NAME not configured" in str(exc_info.value)
    
    @patch('app.services.storage_service.storage')
    def test_service_initialization_client_error(self, mock_storage):
        """Test StorageService initialization with client creation error"""
        mock_storage.Client.side_effect = Exception("Client creation failed")
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                with pytest.raises(ConfigurationError) as exc_info:
                    StorageService()
                
                assert "Failed to initialize Google Cloud Storage" in str(exc_info.value)
    
    @patch('app.services.storage_service.storage')
    def test_validate_input_valid(self, mock_storage):
        """Test input validation with valid data"""
        mock_storage.Client.return_value = Mock()
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                valid_data = {
                    'file_content': b'test content',
                    'filename': 'test.jpg',
                    'content_type': 'image/jpeg'
                }
                
                assert service.validate_input(valid_data) is True
    
    @patch('app.services.storage_service.storage')
    def test_validate_input_invalid(self, mock_storage):
        """Test input validation with invalid data"""
        mock_storage.Client.return_value = Mock()
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                # Test with missing required fields
                invalid_data = {'filename': 'test.jpg'}
                assert service.validate_input(invalid_data) is False
                
                # Test with non-dict data
                assert service.validate_input("not a dict") is False
    
    @patch('app.services.storage_service.storage')
    def test_upload_file_success(self, mock_storage):
        """Test successful file upload"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                file_content = b'test file content'
                filename = 'test.jpg'
                content_type = 'image/jpeg'
                
                result = service.upload_file(file_content, filename, content_type)
                
                assert result['success'] is True
                assert result['file_path'] == filename
                assert result['file_size'] == len(file_content)
                assert result['content_type'] == content_type
                assert 'upload_url' in result
                
                mock_bucket.blob.assert_called_once_with(filename)
                mock_blob.upload_from_string.assert_called_once_with(
                    file_content, content_type=content_type
                )
    
    @patch('app.services.storage_service.storage')
    def test_upload_file_with_metadata(self, mock_storage):
        """Test file upload with metadata"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                file_content = b'test file content'
                filename = 'test.jpg'
                content_type = 'image/jpeg'
                metadata = {'user_id': '123', 'processed': True}
                
                result = service.upload_file(file_content, filename, content_type, metadata)
                
                assert result['success'] is True
                mock_blob.upload_from_string.assert_called_once_with(
                    file_content, content_type=content_type
                )
                assert mock_blob.metadata == metadata
    
    @patch('app.services.storage_service.storage')
    def test_upload_file_google_cloud_error(self, mock_storage):
        """Test file upload with Google Cloud error"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.upload_from_string.side_effect = GoogleCloudError("Upload failed")
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                with pytest.raises(ExternalServiceError) as exc_info:
                    service.upload_file(b'test content', 'test.jpg', 'image/jpeg')
                
                assert "Failed to upload file to Google Cloud Storage" in str(exc_info.value)
    
    @patch('app.services.storage_service.storage')
    def test_download_file_success(self, mock_storage):
        """Test successful file download"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b'file content'
        mock_blob.content_type = 'image/jpeg'
        mock_blob.size = 12
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                result = service.download_file('test.jpg')
                
                assert result['success'] is True
                assert result['file_content'] == b'file content'
                assert result['content_type'] == 'image/jpeg'
                assert result['file_size'] == 12
                
                mock_bucket.blob.assert_called_once_with('test.jpg')
                mock_blob.download_as_bytes.assert_called_once()
    
    @patch('app.services.storage_service.storage')
    def test_download_file_not_found(self, mock_storage):
        """Test file download when file doesn't exist"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                with pytest.raises(FileProcessingError) as exc_info:
                    service.download_file('nonexistent.jpg')
                
                assert "File not found" in str(exc_info.value)
    
    @patch('app.services.storage_service.storage')
    def test_download_file_google_cloud_error(self, mock_storage):
        """Test file download with Google Cloud error"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.side_effect = GoogleCloudError("Download failed")
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                with pytest.raises(ExternalServiceError) as exc_info:
                    service.download_file('test.jpg')
                
                assert "Failed to download file from Google Cloud Storage" in str(exc_info.value)
    
    @patch('app.services.storage_service.storage')
    def test_delete_file_success(self, mock_storage):
        """Test successful file deletion"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                result = service.delete_file('test.jpg')
                
                assert result['success'] is True
                assert result['file_path'] == 'test.jpg'
                
                mock_bucket.blob.assert_called_once_with('test.jpg')
                mock_blob.delete.assert_called_once()
    
    @patch('app.services.storage_service.storage')
    def test_delete_file_not_found(self, mock_storage):
        """Test file deletion when file doesn't exist"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                with pytest.raises(FileProcessingError) as exc_info:
                    service.delete_file('nonexistent.jpg')
                
                assert "File not found" in str(exc_info.value)
    
    @patch('app.services.storage_service.storage')
    def test_get_file_metadata_success(self, mock_storage):
        """Test successful file metadata retrieval"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.reload.return_value = None
        mock_blob.size = 1024
        mock_blob.content_type = 'image/jpeg'
        mock_blob.time_created = Mock()
        mock_blob.updated = Mock()
        mock_blob.metadata = {'user_id': '123'}
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                result = service.get_file_metadata('test.jpg')
                
                assert result['success'] is True
                assert result['file_path'] == 'test.jpg'
                assert result['file_size'] == 1024
                assert result['content_type'] == 'image/jpeg'
                assert result['custom_metadata'] == {'user_id': '123'}
                
                mock_blob.reload.assert_called_once()
    
    @patch('app.services.storage_service.storage')
    def test_list_files_success(self, mock_storage):
        """Test successful file listing"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        
        # Mock blob objects
        mock_blob1 = Mock()
        mock_blob1.name = 'file1.jpg'
        mock_blob1.size = 1024
        mock_blob1.content_type = 'image/jpeg'
        mock_blob1.time_created = Mock()
        
        mock_blob2 = Mock()
        mock_blob2.name = 'file2.png'
        mock_blob2.size = 2048
        mock_blob2.content_type = 'image/png'
        mock_blob2.time_created = Mock()
        
        mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2]
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                result = service.list_files()
                
                assert result['success'] is True
                assert len(result['files']) == 2
                assert result['files'][0]['name'] == 'file1.jpg'
                assert result['files'][1]['name'] == 'file2.png'
    
    @patch('app.services.storage_service.storage')
    def test_list_files_with_prefix(self, mock_storage):
        """Test file listing with prefix filter"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.list_blobs.return_value = []
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                result = service.list_files(prefix='user123/')
                
                assert result['success'] is True
                mock_bucket.list_blobs.assert_called_once_with(prefix='user123/')
    
    @patch('app.services.storage_service.storage')
    def test_generate_signed_url_success(self, mock_storage):
        """Test successful signed URL generation"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.generate_signed_url.return_value = 'https://signed-url.com'
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                result = service.generate_signed_url('test.jpg', expiration=3600)
                
                assert result['success'] is True
                assert result['signed_url'] == 'https://signed-url.com'
                assert result['expires_in'] == 3600
    
    @patch('app.services.storage_service.storage')
    def test_generate_signed_url_file_not_found(self, mock_storage):
        """Test signed URL generation when file doesn't exist"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = False
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                with pytest.raises(FileProcessingError) as exc_info:
                    service.generate_signed_url('nonexistent.jpg')
                
                assert "File not found" in str(exc_info.value)


class TestStorageServiceIntegration:
    """Integration tests for StorageService"""
    
    @patch('app.services.storage_service.storage')
    def test_complete_file_lifecycle(self, mock_storage):
        """Test complete file lifecycle: upload, download, metadata, delete"""
        mock_client = Mock()
        mock_bucket = Mock()
        mock_blob = Mock()
        mock_storage.Client.return_value = mock_client
        mock_client.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.exists.return_value = True
        mock_blob.download_as_bytes.return_value = b'test content'
        mock_blob.content_type = 'image/jpeg'
        mock_blob.size = 12
        mock_blob.time_created = Mock()
        mock_blob.updated = Mock()
        mock_blob.metadata = {'user_id': '123'}
        
        with patch.object(settings, 'GOOGLE_CLOUD_PROJECT', 'test-project'):
            with patch.object(settings, 'GCS_BUCKET_NAME', 'test-bucket'):
                service = StorageService()
                
                # Upload file
                upload_result = service.upload_file(
                    b'test content', 
                    'test.jpg', 
                    'image/jpeg',
                    {'user_id': '123'}
                )
                assert upload_result['success'] is True
                
                # Download file
                download_result = service.download_file('test.jpg')
                assert download_result['success'] is True
                assert download_result['file_content'] == b'test content'
                
                # Get metadata
                metadata_result = service.get_file_metadata('test.jpg')
                assert metadata_result['success'] is True
                assert metadata_result['custom_metadata'] == {'user_id': '123'}
                
                # Delete file
                delete_result = service.delete_file('test.jpg')
                assert delete_result['success'] is True
