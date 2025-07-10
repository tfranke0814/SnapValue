#!/usr/bin/env python3

import requests
import os

def test_api_submit():
    """Test the actual API endpoint"""
    
    # Create a test image file
    test_image_path = os.path.join(os.path.dirname(__file__), "upload_data", "test_phone.jpg")
    
    # Create a small test image if it doesn't exist
    if not os.path.exists(test_image_path):
        os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
        # Create a minimal JPEG file for testing
        with open(test_image_path, 'wb') as f:
            # Minimal JPEG header + data
            f.write(bytes.fromhex('FFD8FFE000104A464946000101010048004800FFDB00430001010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101FFDB004301010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101FFC00011080001000103012200021101031101FFC4001500010100000000000000000000000000000000FFC4001401000000000000000000000000000000000000FFDA000C03010002110311003F00BF800000000000000000000000000000000000000000000000000000000000000000000000000000000000000FFD9'))
    
    try:
        # Test with curl-like request
        url = 'http://localhost:8000/api/v1/appraisal/submit'
        
        with open(test_image_path, 'rb') as f:
            files = {'image_file': ('test_phone.jpg', f, 'image/jpeg')}
            data = {
                'category': 'electronics',
                'user_id': '1'
            }
            
            print("Testing API endpoint...")
            print(f"URL: {url}")
            print(f"Data: {data}")
            
            response = requests.post(url, files=files, data=data, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 201:
                print("✅ API test successful!")
                return True
            else:
                print("❌ API test failed!")
                return False
                
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server. Make sure it's running on http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

if __name__ == "__main__":
    test_api_submit()