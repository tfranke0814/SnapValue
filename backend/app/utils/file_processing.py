import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
from io import BytesIO
from PIL import Image, ExifTags, ImageOps
import json

from app.utils.exceptions import FileProcessingError
from app.utils.logging import get_logger

logger = get_logger(__name__)

class FileProcessor:
    """Utility class for file processing operations"""
    
    def __init__(self):
        self.supported_formats = ['JPEG', 'PNG', 'WEBP']
        self.thumbnail_sizes = [(150, 150), (300, 300), (600, 600)]
    
    def extract_metadata(self, file_content: bytes, filename: str) -> Dict:
        """Extract comprehensive metadata from file"""
        try:
            metadata = {
                'filename': filename,
                'file_size': len(file_content),
                'file_hash': self._calculate_hash(file_content),
                'processed_at': datetime.utcnow().isoformat(),
                'image_metadata': {},
                'exif_data': {},
                'file_info': {}
            }
            
            # Extract image metadata
            try:
                image = Image.open(BytesIO(file_content))
                metadata['image_metadata'] = self._extract_image_metadata(image)
                metadata['exif_data'] = self._extract_exif_data(image)
                metadata['file_info'] = self._extract_file_info(image, filename)
            except Exception as e:
                logger.warning(f"Failed to extract image metadata: {e}")
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract metadata: {e}")
            raise FileProcessingError(f"Metadata extraction failed: {str(e)}")
    
    def _extract_image_metadata(self, image: Image.Image) -> Dict:
        """Extract basic image metadata"""
        return {
            'format': image.format,
            'mode': image.mode,
            'size': image.size,
            'width': image.width,
            'height': image.height,
            'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info,
            'is_animated': getattr(image, 'is_animated', False),
            'n_frames': getattr(image, 'n_frames', 1)
        }
    
    def _extract_exif_data(self, image: Image.Image) -> Dict:
        """Extract EXIF data from image"""
        exif_data = {}
        
        try:
            exif = image._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = ExifTags.TAGS.get(tag_id, tag_id)
                    
                    # Convert bytes to string for JSON serialization
                    if isinstance(value, bytes):
                        try:
                            value = value.decode('utf-8')
                        except:
                            value = str(value)
                    
                    exif_data[tag] = value
                    
        except Exception as e:
            logger.debug(f"Failed to extract EXIF data: {e}")
        
        return exif_data
    
    def _extract_file_info(self, image: Image.Image, filename: str) -> Dict:
        """Extract file-specific information"""
        return {
            'extension': os.path.splitext(filename)[1].lower(),
            'color_mode': image.mode,
            'bit_depth': self._get_bit_depth(image),
            'compression': self._get_compression_info(image),
            'dpi': image.info.get('dpi', (72, 72))
        }
    
    def _get_bit_depth(self, image: Image.Image) -> int:
        """Get bit depth of image"""
        mode_to_depth = {
            '1': 1,
            'L': 8,
            'P': 8,
            'RGB': 24,
            'RGBA': 32,
            'CMYK': 32,
            'YCbCr': 24,
            'LAB': 24,
            'HSV': 24
        }
        return mode_to_depth.get(image.mode, 8)
    
    def _get_compression_info(self, image: Image.Image) -> str:
        """Get compression information"""
        if image.format == 'JPEG':
            return 'JPEG'
        elif image.format == 'PNG':
            return 'PNG (Lossless)'
        elif image.format == 'WEBP':
            return 'WebP'
        return 'Unknown'
    
    def _calculate_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file"""
        return hashlib.sha256(file_content).hexdigest()
    
    def create_thumbnails(self, file_content: bytes) -> Dict[str, bytes]:
        """Create thumbnails of different sizes"""
        thumbnails = {}
        
        try:
            image = Image.open(BytesIO(file_content))
            
            # Fix orientation based on EXIF
            image = ImageOps.exif_transpose(image)
            
            for size in self.thumbnail_sizes:
                thumbnail = self._create_thumbnail(image, size)
                size_name = f"{size[0]}x{size[1]}"
                thumbnails[size_name] = thumbnail
                
        except Exception as e:
            logger.error(f"Failed to create thumbnails: {e}")
            raise FileProcessingError(f"Thumbnail creation failed: {str(e)}")
        
        return thumbnails
    
    def _create_thumbnail(self, image: Image.Image, size: Tuple[int, int]) -> bytes:
        """Create a single thumbnail"""
        # Create thumbnail maintaining aspect ratio
        thumbnail = image.copy()
        thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if necessary for JPEG
        if thumbnail.mode in ('RGBA', 'LA', 'P'):
            thumbnail = thumbnail.convert('RGB')
        
        # Save to bytes
        thumbnail_io = BytesIO()
        thumbnail.save(thumbnail_io, format='JPEG', quality=85, optimize=True)
        
        return thumbnail_io.getvalue()
    
    def optimize_image(self, file_content: bytes, quality: int = 85) -> bytes:
        """Optimize image for web use"""
        try:
            image = Image.open(BytesIO(file_content))
            
            # Fix orientation
            image = ImageOps.exif_transpose(image)
            
            # Convert to RGB if needed
            if image.mode in ('RGBA', 'LA'):
                # Create white background for transparency
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode == 'P':
                image = image.convert('RGB')
            
            # Optimize and save
            optimized_io = BytesIO()
            image.save(optimized_io, format='JPEG', quality=quality, optimize=True)
            
            return optimized_io.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to optimize image: {e}")
            raise FileProcessingError(f"Image optimization failed: {str(e)}")
    
    def resize_image(self, file_content: bytes, max_width: int, max_height: int) -> bytes:
        """Resize image to fit within specified dimensions"""
        try:
            image = Image.open(BytesIO(file_content))
            
            # Fix orientation
            image = ImageOps.exif_transpose(image)
            
            # Calculate new size maintaining aspect ratio
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Save resized image
            resized_io = BytesIO()
            image.save(resized_io, format='JPEG', quality=90, optimize=True)
            
            return resized_io.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to resize image: {e}")
            raise FileProcessingError(f"Image resize failed: {str(e)}")
    
    def convert_format(self, file_content: bytes, target_format: str) -> bytes:
        """Convert image to different format"""
        try:
            image = Image.open(BytesIO(file_content))
            
            # Fix orientation
            image = ImageOps.exif_transpose(image)
            
            # Handle format-specific conversions
            if target_format.upper() == 'JPEG':
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                save_kwargs = {'format': 'JPEG', 'quality': 90, 'optimize': True}
            elif target_format.upper() == 'PNG':
                save_kwargs = {'format': 'PNG', 'optimize': True}
            elif target_format.upper() == 'WEBP':
                save_kwargs = {'format': 'WEBP', 'quality': 90, 'method': 6}
            else:
                raise FileProcessingError(f"Unsupported target format: {target_format}")
            
            # Convert and save
            converted_io = BytesIO()
            image.save(converted_io, **save_kwargs)
            
            return converted_io.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to convert image format: {e}")
            raise FileProcessingError(f"Format conversion failed: {str(e)}")
    
    def get_color_info(self, file_content: bytes) -> Dict:
        """Extract color information from image"""
        try:
            image = Image.open(BytesIO(file_content))
            
            # Convert to RGB for analysis
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get dominant colors (simplified)
            colors = image.getcolors(maxcolors=256*256*256)
            if colors:
                # Sort by frequency
                colors.sort(key=lambda x: x[0], reverse=True)
                dominant_colors = [color[1] for color in colors[:5]]
            else:
                dominant_colors = []
            
            return {
                'mode': image.mode,
                'dominant_colors': dominant_colors,
                'has_transparency': image.mode in ('RGBA', 'LA') or 'transparency' in image.info
            }
            
        except Exception as e:
            logger.error(f"Failed to extract color info: {e}")
            return {}

# Utility functions
def extract_file_metadata(file_content: bytes, filename: str) -> Dict:
    """Extract metadata from file"""
    processor = FileProcessor()
    return processor.extract_metadata(file_content, filename)

def create_image_thumbnails(file_content: bytes) -> Dict[str, bytes]:
    """Create thumbnails for image"""
    processor = FileProcessor()
    return processor.create_thumbnails(file_content)

def optimize_image_for_web(file_content: bytes, quality: int = 85) -> bytes:
    """Optimize image for web usage"""
    processor = FileProcessor()
    return processor.optimize_image(file_content, quality)

def resize_image_to_fit(file_content: bytes, max_width: int, max_height: int) -> bytes:
    """Resize image to fit within dimensions"""
    processor = FileProcessor()
    return processor.resize_image(file_content, max_width, max_height)

def optimize_image(file_content: bytes, quality: int = 85) -> bytes:
    """Optimize image (alias for optimize_image_for_web)"""
    return optimize_image_for_web(file_content, quality)

def convert_image_format(file_content: bytes, target_format: str) -> bytes:
    """Convert image to target format"""
    processor = FileProcessor()
    return processor.convert_format(file_content, target_format)