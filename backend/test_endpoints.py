#!/usr/bin/env python3
"""
Test script for SnapValue API endpoints
"""
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """Test if all modules can be imported"""
    try:
        print("Testing imports...")
        
        # Test basic FastAPI import
        from fastapi import FastAPI
        print("✓ FastAPI imported successfully")
        
        # Test app core modules
        from app.core.config import settings
        print("✓ App config imported successfully")
        
        from app.schemas.response_schemas import SuccessResponse, ErrorResponse
        print("✓ Response schemas imported successfully")
        
        from app.schemas.appraisal_schemas import AppraisalStatusEnum
        print("✓ Appraisal schemas imported successfully")
        
        # Test API routers
        from app.api.v1.docs import router as docs_router
        print("✓ Docs router imported successfully")
        
        from app.api.v1.status import router as status_router
        print("✓ Status router imported successfully")
        
        from app.api.v1.users import router as users_router
        print("✓ Users router imported successfully")
        
        from app.api.v1.main import api_router
        print("✓ Main API router imported successfully")
        
        # Test main app
        from main import app
        print("✓ Main FastAPI app imported successfully")
        
        print("\n✅ All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_endpoints():
    """Test endpoint structure"""
    try:
        from app.api.v1.main import api_router
        
        print("\nTesting API endpoints structure...")
        
        # Get all routes
        routes = api_router.routes
        print(f"Found {len(routes)} routes in API router")
        
        # Count endpoints by prefix
        endpoint_counts = {}
        for route in routes:
            if hasattr(route, 'path'):
                path_parts = route.path.split('/')
                if len(path_parts) > 2:
                    prefix = path_parts[2]  # Get the prefix after /v1/
                    endpoint_counts[prefix] = endpoint_counts.get(prefix, 0) + 1
        
        print("Endpoint counts by prefix:")
        for prefix, count in endpoint_counts.items():
            print(f"  {prefix}: {count} endpoints")
        
        expected_prefixes = ['appraisal', 'auth', 'monitoring', 'status', 'users', 'docs-api']
        missing_prefixes = [p for p in expected_prefixes if p not in endpoint_counts]
        
        if missing_prefixes:
            print(f"❌ Missing prefixes: {missing_prefixes}")
            return False
        else:
            print("✅ All expected endpoint prefixes found!")
            return True
            
    except Exception as e:
        print(f"❌ Error testing endpoints: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("SnapValue API Endpoint Test")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 2
    
    # Test imports
    if test_imports():
        tests_passed += 1
    
    # Test endpoints
    if test_endpoints():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {tests_passed}/{total_tests} passed")
    
    if tests_passed == total_tests:
        print("✅ All tests passed! REST API endpoints are ready.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
