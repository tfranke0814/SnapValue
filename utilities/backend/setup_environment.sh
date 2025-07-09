#!/bin/bash

# SnapValue Backend Setup Script
# This script sets up the backend environment from scratch

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo -e "${GREEN}🔧 Setting up SnapValue Backend Environment${NC}"
echo "Project Root: $PROJECT_ROOT"
echo "Backend Directory: $BACKEND_DIR"

# Create backend directory if it doesn't exist
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${YELLOW}📁 Creating backend directory...${NC}"
    mkdir -p "$BACKEND_DIR"
fi

# Navigate to backend directory
cd "$BACKEND_DIR"

# Check Python version
echo -e "${BLUE}🐍 Checking Python version...${NC}"
python3 --version

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${GREEN}🏗️  Creating virtual environment...${NC}"
    python3 -m venv venv
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${GREEN}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo -e "${GREEN}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}📦 Installing dependencies from requirements.txt...${NC}"
    pip install -r requirements.txt
else
    echo -e "${YELLOW}⚠️  requirements.txt not found${NC}"
fi

# Create .env file from template if it doesn't exist
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo -e "${GREEN}📝 Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please review and update the .env file with your settings${NC}"
fi

echo -e "${GREEN}✅ Backend environment setup complete!${NC}"
echo -e "${BLUE}🚀 You can now run: ./start_server.sh${NC}"
