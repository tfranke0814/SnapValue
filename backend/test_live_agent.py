"""
Live test script for invoking the Vertex AI Agent Engine through the AppraisalService.

This script is designed to be run from the 'backend' directory.
It initializes the application's services, uploads a local test image to GCS,
and then calls the appraisal service to get a live appraisal from the deployed agent.

Usage:
1. Make sure your .env file is correctly configured with PRODUCTION credentials
   for GCS and Vertex AI.
2. Ensure the GOOGLE_APPLICATION_CREDENTIALS path is correct.
3. Make sure the test image 'test_phone.jpg' exists in the 'backend' directory.
4. Run from the 'backend' directory: python test_live_agent.py
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_environment():
    """Load environment variables and configure settings."""
    # Load from .env file in the current directory (backend/)
    load_dotenv()
    
    # Set APP_ENV to production to use real services
    os.environ['APP_ENV'] = 'production'
    
    # Manually set a test image path
    os.environ['TEST_IMAGE_PATH'] = 'test_phone.jpg'
    
    print("Environment Setup:")
    print(f"  APP_ENV: {os.getenv('APP_ENV')}")
    print(f"  GCS_BUCKET_NAME: {os.getenv('GCS_BUCKET_NAME')}")
    print(f"  VERTEX_AI_PROJECT: {os.getenv('VERTEX_AI_PROJECT')}")
    print(f"  VERTEX_AI_REASONING_ENGINE_ID: {os.getenv('VERTEX_AI_REASONING_ENGINE_ID')}")
    print("-" * 20)

async def main():
    """Main function to run the live agent test."""
    setup_environment()

    from app.core.config import settings
    from app.database.connection import SessionLocal
    from app.services.appraisal_service import AppraisalService
    from app.services.storage_factory import get_storage_service
    from app.utils.exceptions import FileProcessingError

    # --- Configuration Check ---
    if not all([
        settings.GCS_BUCKET_NAME,
        settings.VERTEX_AI_PROJECT,
        settings.VERTEX_AI_LOCATION,
        settings.VERTEX_AI_REASONING_ENGINE_ID,
        settings.GOOGLE_APPLICATION_CREDENTIALS
    ]):
        print("🔴 Error: Missing critical GCS or Vertex AI configuration in your .env file.")
        print("Please ensure GCS_BUCKET_NAME, VERTEX_AI_PROJECT, VERTEX_AI_LOCATION, VERTEX_AI_REASONING_ENGINE_ID, and GOOGLE_APPLICATION_CREDENTIALS are set.")
        return

    if not os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
        print(f"🔴 Error: Credentials file not found at '{settings.GOOGLE_APPLICATION_CREDENTIALS}'.")
        return

    db_session = SessionLocal()
    appraisal_service = AppraisalService(db=db_session)
    storage_service = get_storage_service()
    
    # --- 1. Upload test image to GCS ---
    local_image_path = os.getenv('TEST_IMAGE_PATH')
    if not os.path.exists(local_image_path):
        print(f"🔴 Error: Test image '{local_image_path}' not found in the 'backend' directory.")
        return
        
    print(f"🔄 Uploading '{local_image_path}' to GCS bucket '{settings.GCS_BUCKET_NAME}'...")
    
    try:
        with open(local_image_path, "rb") as f:
            file_content = f.read()
        
        # Use a unique name for the blob to avoid caching issues
        blob_name = f"live_tests/{os.path.basename(local_image_path)}"
        
        upload_result = storage_service.upload_file(
            file_content=file_content,
            filename=blob_name
        )
        gcs_uri = f"gs://{settings.GCS_BUCKET_NAME}/{upload_result['blob_name']}"
        print(f"✅ Image uploaded successfully. GCS URI: {gcs_uri}")
        
    except Exception as e:
        print(f"🔴 Error uploading image to GCS: {e}")
        return

    # --- 2. Call the AI Service with the GCS URI ---
    print("\n🔄 Calling Vertex AI Agent via AIService...")
    
    try:
        # Directly call the AI service to isolate the test to the agent interaction
        ai_service = appraisal_service.ai_service
        result = ai_service.get_appraisal_from_agent(image_uri=gcs_uri)
        
        print("✅ Agent responded successfully!")
        print("\n--- Agent Response ---")
        print(result)
        print("----------------------\n")
        
    except Exception as e:
        print(f"🔴 An error occurred while calling the AI agent: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db_session.close()

if __name__ == "__main__":
    asyncio.run(main())
