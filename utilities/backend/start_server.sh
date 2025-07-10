#!/bin/bash

# SnapValue Backend Server Startup Script
# This script starts the FastAPI backend server with proper environment setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo -e "${GREEN}🚀 Starting SnapValue Backend Server${NC}"
echo "Project Root: $PROJECT_ROOT"
echo "Backend Directory: $BACKEND_DIR"

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}❌ Backend directory not found: $BACKEND_DIR${NC}"
    exit 1
fi

# Navigate to backend directory
cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Check if requirements.txt exists and install dependencies
if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}📦 Installing/updating dependencies...${NC}"
    pip install -r requirements.txt
else
    echo -e "${YELLOW}⚠️  requirements.txt not found${NC}"
fi

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ main.py not found in backend directory${NC}"
    exit 1
fi

# Start the server
echo -e "${GREEN}🌟 Starting FastAPI server...${NC}"
echo "Server will be available at: http://localhost:8000"
echo "API Documentation: http://localhost:8000/docs"
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
