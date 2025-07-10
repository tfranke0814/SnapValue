#!/usr/bin/env python3
"""
Test script for SnapValue appraisal service
"""

import sys
import os
import asyncio
from pathlib import Path
from sqlalchemy.orm import Session

# Add the backend directory to Python path
# Go up one level to the 'backend' directory
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database.connection import SessionLocal
from app.services.appraisal_service import AppraisalService
from PIL import Image
from io import BytesIO

def create_test_image() -> bytes:
    """Create a simple test image"""
    img = Image.new('RGB', (100, 100), color='green')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes.read()

async def test_appraisal_service():
    """Test the appraisal service"""
    print("🧪 Testing SnapValue Appraisal Service")
    print("=" * 50)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Create appraisal service
        appraisal_service = AppraisalService(db)
        print("✅ Appraisal service created")
        
        # Create test image
        image_data = create_test_image()
        print(f"✅ Test image created: {len(image_data)} bytes")
        
        # Test file submission (without async processing)
        print("\n📤 Testing appraisal submission...")
        
        result = appraisal_service.submit_appraisal(
            file_content=image_data,
            filename="test_image.jpg",
            user_id=1,
            options={
                'category': 'electronics',
                'target_condition': 'good'
            }
        )
        
        print(f"✅ Appraisal submitted successfully:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()

def main():
    """Main test function"""
    try:
        success = asyncio.run(test_appraisal_service())
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
