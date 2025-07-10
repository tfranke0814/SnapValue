#!/bin/bash

# Step 3 Image Storage Backend Service Test Runner
# Tests image validation, file processing, storage service, and image service

set -e

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🖼️  Running Step 3: Image Storage Backend Service Tests"
echo "======================================================"

# Navigate to backend directory
cd "$BACKEND_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found. Please run ./dev.sh setup first."
    exit 1
fi

# Install dependencies if needed
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Running Image Validation Tests..."
python -m pytest tests/step3/test_image_validation.py -v

echo ""
echo "🔧 Running File Processing Tests..."
python -m pytest tests/step3/test_file_processing.py -v

echo ""
echo "☁️  Running Storage Service Tests..."
python -m pytest tests/step3/test_storage_service.py -v

echo ""
echo "🖼️  Running Image Service Tests..."
python -m pytest tests/step3/test_image_service.py -v

echo ""
echo "📊 Running All Step 3 Tests Summary..."
python -m pytest tests/step3/ --tb=short -v

echo ""
echo "✅ Step 3 Image Storage Backend Service Tests Complete!"
echo "📄 Features tested:"
echo "   • Image validation (size, format, security)"
echo "   • File processing (metadata, thumbnails, optimization)"
echo "   • Google Cloud Storage integration"
echo "   • Complete image service workflow"
echo "🚀 Ready to proceed to Step 4: API Endpoints"
