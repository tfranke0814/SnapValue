#!/usr/bin/env python3
"""
Test script for SnapValue storage system
"""

import sys
import os
import asyncio
from pathlib import Path
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv

# Load environment variables from .env file
# Go up one level to the 'backend' directory
backend_dir = Path(__file__).parent.parent
load_dotenv(dotenv_path=backend_dir / '.env')

# Add the backend directory to Python path
sys.path.insert(0, str(backend_dir))

from app.services.storage_factory import get_storage_service, get_storage_config
from app.core.config import settings

def create_test_image() -> bytes:
    """Create a simple test image"""
    # Create a simple 100x100 red image
    img = Image.new('RGB', (100, 100), color='red')
    
    # Save to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes.read()

async def test_storage_system():
    """Test the storage system"""
    print("🧪 Testing SnapValue Storage System")
    print("=" * 50)
    
    # Show configuration
    config = get_storage_config()
    print("Configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()
    
    # Get storage service
    try:
        storage_service = get_storage_service()
        print(f"✅ Storage service created: {type(storage_service).__name__}")
    except Exception as e:
        print(f"❌ Failed to create storage service: {e}")
        return False
    
    # Test health check
    try:
        health_ok = storage_service.health_check()
        print(f"✅ Health check: {'PASSED' if health_ok else 'FAILED'}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Create test image
    print("\n📸 Creating test image...")
    test_image_data = create_test_image()
    print(f"✅ Test image created: {len(test_image_data)} bytes")
    
    # Test file upload
    print("\n📤 Testing file upload...")
    try:
        upload_result = storage_service.upload_file(
            file_content=test_image_data,
            filename="test_image.jpg",
            folder="test",
            metadata={"test": "true", "description": "Storage system test"}
        )
        print(f"✅ File uploaded successfully:")
        for key, value in upload_result.items():
            print(f"  {key}: {value}")
        
        # Store path for cleanup
        file_path = upload_result.get('relative_path') or upload_result.get('blob_name')
        
    except Exception as e:
        print(f"❌ File upload failed: {e}")
        return False
    
    # Test file exists
    print(f"\n🔍 Testing file exists check...")
    try:
        exists = storage_service.file_exists(file_path)
        print(f"✅ File exists: {exists}")
    except Exception as e:
        print(f"❌ File exists check failed: {e}")
    
    # Test file metadata
    print(f"\n📋 Testing file metadata...")
    try:
        metadata = storage_service.get_file_metadata(file_path)
        print(f"✅ File metadata retrieved:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"❌ File metadata failed: {e}")
    
    # Test file download
    print(f"\n📥 Testing file download...")
    try:
        downloaded_data = storage_service.download_file(file_path)
        print(f"✅ File downloaded: {len(downloaded_data)} bytes")
        print(f"✅ Data integrity: {'PASSED' if downloaded_data == test_image_data else 'FAILED'}")
    except Exception as e:
        print(f"❌ File download failed: {e}")
    
    # Test file listing
    print(f"\n📋 Testing file listing...")
    try:
        files = storage_service.list_files(prefix="test", limit=10)
        print(f"✅ Files listed: {len(files)} files found")
        for file_info in files[:3]:  # Show first 3 files
            print(f"  - {file_info.get('name', file_info.get('relative_path'))}")
    except Exception as e:
        print(f"❌ File listing failed: {e}")
    
    # Test cleanup
    print(f"\n🧹 Testing file deletion...")
    try:
        deleted = storage_service.delete_file(file_path)
        print(f"✅ File deleted: {deleted}")
    except Exception as e:
        print(f"❌ File deletion failed: {e}")
    
    # Test storage stats (if available)
    print(f"\n📊 Testing storage stats...")
    try:
        if hasattr(storage_service, 'get_storage_stats'):
            stats = storage_service.get_storage_stats()
            print(f"✅ Storage stats:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            print("ℹ️ Storage stats not available for this storage type")
    except Exception as e:
        print(f"❌ Storage stats failed: {e}")
    
    print(f"\n🎉 Storage system test completed!")
    return True

def main():
    """Main test function"""
    try:
        # Run async test
        success = asyncio.run(test_storage_system())
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
