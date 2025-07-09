#!/bin/bash

# SnapValue Backend Testing Script
# This script runs all tests for the backend with proper environment setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo -e "${GREEN}🧪 Running SnapValue Backend Tests${NC}"
echo "Project Root: $PROJECT_ROOT"
echo "Backend Directory: $BACKEND_DIR"

# Navigate to backend directory
cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Run start_server.sh first.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Run tests
echo -e "${GREEN}🏃 Running tests...${NC}"
if [ -f "test_main.py" ]; then
    pytest test_main.py -v --tb=short
else
    echo -e "${YELLOW}⚠️  No test files found${NC}"
fi

echo -e "${GREEN}✅ Tests completed!${NC}"
