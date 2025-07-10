"""
Tests for File Processing - Step 3
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import BytesIO
from PIL import Image
import json
from datetime import datetime

from app.utils.file_processing import (
    FileProcessor, 
    extract_file_metadata, 
    create_image_thumbnails,
    optimize_image,
    convert_image_format
)
from app.utils.exceptions import FileProcessingError


class TestFileProcessor:
    """Test cases for FileProcessor class"""
    
    def test_processor_initialization(self):
        """Test FileProcessor initialization"""
        processor = FileProcessor()
        
        assert processor.supported_formats == ['JPEG', 'PNG', 'WEBP']
        assert processor.thumbnail_sizes == [(150, 150), (300, 300), (600, 600)]
    
    def test_extract_metadata_success(self):
        """Test metadata extraction with valid image"""
        processor = FileProcessor()
        
        # Create a test image
        img = Image.new('RGB', (200, 150), color='green')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        metadata = processor.extract_metadata(img_content, "test.jpg")
        
        assert metadata['filename'] == "test.jpg"
        assert metadata['file_size'] == len(img_content)
        assert 'file_hash' in metadata
        assert 'processed_at' in metadata
        assert 'image_metadata' in metadata
        assert 'exif_data' in metadata
        assert 'file_info' in metadata
    
    def test_extract_metadata_invalid_image(self):
        """Test metadata extraction with invalid image"""
        processor = FileProcessor()
        
        invalid_content = b"not an image"
        
        with pytest.raises(FileProcessingError) as exc_info:
            processor.extract_metadata(invalid_content, "test.txt")
        
        assert "Metadata extraction failed" in str(exc_info.value)
    
    def test_extract_image_metadata(self):
        """Test image metadata extraction"""
        processor = FileProcessor()
        
        # Create a test image
        img = Image.new('RGB', (300, 200), color='red')
        
        metadata = processor._extract_image_metadata(img)
        
        assert metadata['width'] == 300
        assert metadata['height'] == 200
        assert metadata['format'] == 'RGB'
        assert metadata['mode'] == 'RGB'
        assert metadata['has_transparency'] is False
    
    def test_extract_image_metadata_with_transparency(self):
        """Test image metadata extraction with transparency"""
        processor = FileProcessor()
        
        # Create a test image with transparency
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        
        metadata = processor._extract_image_metadata(img)
        
        assert metadata['mode'] == 'RGBA'
        assert metadata['has_transparency'] is True
    
    def test_extract_exif_data_with_exif(self):
        """Test EXIF data extraction with EXIF data"""
        processor = FileProcessor()
        
        # Create a test image with simulated EXIF data
        img = Image.new('RGB', (100, 100), color='blue')
        
        # Mock EXIF data
        with patch.object(img, 'getexif') as mock_getexif:
            mock_exif = {
                256: 100,  # ImageWidth
                257: 100,  # ImageLength
                271: 'Test Camera',  # Make
                272: 'Test Model'   # Model
            }
            mock_getexif.return_value = mock_exif
            
            exif_data = processor._extract_exif_data(img)
            
            assert 'ImageWidth' in exif_data
            assert 'ImageLength' in exif_data
            assert 'Make' in exif_data
            assert 'Model' in exif_data
    
    def test_extract_exif_data_without_exif(self):
        """Test EXIF data extraction without EXIF data"""
        processor = FileProcessor()
        
        # Create a test image without EXIF data
        img = Image.new('RGB', (100, 100), color='blue')
        
        exif_data = processor._extract_exif_data(img)
        
        assert exif_data == {}
    
    def test_extract_file_info(self):
        """Test file info extraction"""
        processor = FileProcessor()
        
        # Create a test image
        img = Image.new('RGB', (100, 100), color='yellow')
        filename = "test_image.jpg"
        
        file_info = processor._extract_file_info(img, filename)
        
        assert file_info['filename'] == filename
        assert file_info['extension'] == '.jpg'
        assert file_info['format'] == 'RGB'
        assert file_info['color_mode'] == 'RGB'
        assert file_info['bit_depth'] == 8
    
    def test_calculate_hash(self):
        """Test file hash calculation"""
        processor = FileProcessor()
        
        test_content = b"test content for hashing"
        
        hash_value = processor._calculate_hash(test_content)
        
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 hash length
    
    def test_generate_thumbnails(self):
        """Test thumbnail generation"""
        processor = FileProcessor()
        
        # Create a test image
        img = Image.new('RGB', (1000, 800), color='purple')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        thumbnails = processor.generate_thumbnails(img_content, 'JPEG')
        
        assert len(thumbnails) == 3  # Three thumbnail sizes
        
        for size, thumb_data in thumbnails:
            assert isinstance(size, tuple)
            assert len(size) == 2
            assert isinstance(thumb_data, bytes)
            assert len(thumb_data) > 0
    
    def test_generate_thumbnails_invalid_image(self):
        """Test thumbnail generation with invalid image"""
        processor = FileProcessor()
        
        invalid_content = b"not an image"
        
        with pytest.raises(FileProcessingError) as exc_info:
            processor.generate_thumbnails(invalid_content, 'JPEG')
        
        assert "Thumbnail generation failed" in str(exc_info.value)
    
    def test_optimize_image_jpeg(self):
        """Test JPEG image optimization"""
        processor = FileProcessor()
        
        # Create a test image
        img = Image.new('RGB', (500, 400), color='orange')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        optimized = processor.optimize_image(img_content, 'JPEG')
        
        assert isinstance(optimized, bytes)
        assert len(optimized) > 0
        # Optimized image should typically be smaller or same size
        assert len(optimized) <= len(img_content)
    
    def test_optimize_image_png(self):
        """Test PNG image optimization"""
        processor = FileProcessor()
        
        # Create a test image
        img = Image.new('RGB', (300, 200), color='cyan')
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_content = img_bytes.getvalue()
        
        optimized = processor.optimize_image(img_content, 'PNG')
        
        assert isinstance(optimized, bytes)
        assert len(optimized) > 0
    
    def test_optimize_image_invalid_format(self):
        """Test image optimization with invalid format"""
        processor = FileProcessor()
        
        # Create a test image
        img = Image.new('RGB', (100, 100), color='magenta')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        with pytest.raises(FileProcessingError) as exc_info:
            processor.optimize_image(img_content, 'INVALID')
        
        assert "Unsupported format for optimization" in str(exc_info.value)
    
    def test_resize_image(self):
        """Test image resizing"""
        processor = FileProcessor()
        
        # Create a test image
        img = Image.new('RGB', (800, 600), color='brown')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        resized = processor.resize_image(img_content, (400, 300), 'JPEG')
        
        assert isinstance(resized, bytes)
        assert len(resized) > 0
        
        # Verify the resized image has correct dimensions
        resized_img = Image.open(BytesIO(resized))
        assert resized_img.size == (400, 300)
    
    def test_resize_image_maintain_aspect_ratio(self):
        """Test image resizing with aspect ratio maintenance"""
        processor = FileProcessor()
        
        # Create a test image
        img = Image.new('RGB', (800, 400), color='pink')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        resized = processor.resize_image(img_content, (200, 200), 'JPEG', maintain_aspect_ratio=True)
        
        assert isinstance(resized, bytes)
        assert len(resized) > 0
        
        # Verify the resized image maintains aspect ratio
        resized_img = Image.open(BytesIO(resized))
        # Should be 200x100 to maintain 2:1 aspect ratio
        assert resized_img.size == (200, 100)
    
    def test_convert_format(self):
        """Test image format conversion"""
        processor = FileProcessor()
        
        # Create a test image in JPEG
        img = Image.new('RGB', (100, 100), color='gray')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        converted = processor.convert_format(img_content, 'PNG')
        
        assert isinstance(converted, bytes)
        assert len(converted) > 0
        
        # Verify the converted image is in PNG format
        converted_img = Image.open(BytesIO(converted))
        assert converted_img.format == 'PNG'
    
    def test_convert_format_invalid_target(self):
        """Test image format conversion with invalid target format"""
        processor = FileProcessor()
        
        # Create a test image
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        with pytest.raises(FileProcessingError) as exc_info:
            processor.convert_format(img_content, 'INVALID')
        
        assert "Unsupported target format" in str(exc_info.value)


class TestExtractFileMetadata:
    """Test cases for extract_file_metadata function"""
    
    def test_extract_file_metadata_success(self):
        """Test file metadata extraction function"""
        # Create a test image
        img = Image.new('RGB', (150, 100), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        metadata = extract_file_metadata(img_content, "test.jpg")
        
        assert metadata['filename'] == "test.jpg"
        assert metadata['file_size'] == len(img_content)
        assert 'file_hash' in metadata
        assert 'image_metadata' in metadata
    
    def test_extract_file_metadata_failure(self):
        """Test file metadata extraction function with invalid data"""
        invalid_content = b"not an image"
        
        with pytest.raises(FileProcessingError):
            extract_file_metadata(invalid_content, "test.txt")


class TestCreateImageThumbnails:
    """Test cases for create_image_thumbnails function"""
    
    def test_create_image_thumbnails_success(self):
        """Test thumbnail creation function"""
        # Create a test image
        img = Image.new('RGB', (1000, 800), color='blue')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        thumbnails = create_image_thumbnails(img_content, 'JPEG')
        
        assert len(thumbnails) == 3
        for size, thumb_data in thumbnails:
            assert isinstance(size, tuple)
            assert isinstance(thumb_data, bytes)
    
    def test_create_image_thumbnails_failure(self):
        """Test thumbnail creation function with invalid data"""
        invalid_content = b"not an image"
        
        with pytest.raises(FileProcessingError):
            create_image_thumbnails(invalid_content, 'JPEG')


class TestOptimizeImage:
    """Test cases for optimize_image function"""
    
    def test_optimize_image_success(self):
        """Test image optimization function"""
        # Create a test image
        img = Image.new('RGB', (300, 200), color='green')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        optimized = optimize_image(img_content, 'JPEG')
        
        assert isinstance(optimized, bytes)
        assert len(optimized) > 0
    
    def test_optimize_image_failure(self):
        """Test image optimization function with invalid data"""
        invalid_content = b"not an image"
        
        with pytest.raises(FileProcessingError):
            optimize_image(invalid_content, 'JPEG')


class TestConvertImageFormat:
    """Test cases for convert_image_format function"""
    
    def test_convert_image_format_success(self):
        """Test image format conversion function"""
        # Create a test image
        img = Image.new('RGB', (100, 100), color='yellow')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        converted = convert_image_format(img_content, 'PNG')
        
        assert isinstance(converted, bytes)
        assert len(converted) > 0
        
        # Verify the converted format
        converted_img = Image.open(BytesIO(converted))
        assert converted_img.format == 'PNG'
    
    def test_convert_image_format_failure(self):
        """Test image format conversion function with invalid data"""
        invalid_content = b"not an image"
        
        with pytest.raises(FileProcessingError):
            convert_image_format(invalid_content, 'PNG')


class TestFileProcessingIntegration:
    """Integration tests for file processing"""
    
    def test_complete_processing_workflow(self):
        """Test complete file processing workflow"""
        processor = FileProcessor()
        
        # Create a test image
        img = Image.new('RGB', (600, 400), color='purple')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_content = img_bytes.getvalue()
        
        # Extract metadata
        metadata = processor.extract_metadata(img_content, "test.jpg")
        assert metadata['image_metadata']['width'] == 600
        assert metadata['image_metadata']['height'] == 400
        
        # Generate thumbnails
        thumbnails = processor.generate_thumbnails(img_content, 'JPEG')
        assert len(thumbnails) == 3
        
        # Optimize image
        optimized = processor.optimize_image(img_content, 'JPEG')
        assert len(optimized) > 0
        
        # Resize image
        resized = processor.resize_image(img_content, (300, 200), 'JPEG')
        resized_img = Image.open(BytesIO(resized))
        assert resized_img.size == (300, 200)
        
        # Convert format
        converted = processor.convert_format(img_content, 'PNG')
        converted_img = Image.open(BytesIO(converted))
        assert converted_img.format == 'PNG'
