#!/bin/bash

# SnapValue Deployment Script
# This script prepares and deploys the SnapValue application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${GREEN}🚀 SnapValue Deployment Script${NC}"
echo "Project Root: $PROJECT_ROOT"

# Check if we're in the right directory
if [ ! -f "$PROJECT_ROOT/backend/main.py" ]; then
    echo -e "${RED}❌ Backend main.py not found. Are you in the right directory?${NC}"
    exit 1
fi

# Run tests first
echo -e "${BLUE}🧪 Running tests before deployment...${NC}"
if [ -f "$PROJECT_ROOT/utilities/backend/run_tests.sh" ]; then
    bash "$PROJECT_ROOT/utilities/backend/run_tests.sh"
else
    echo -e "${YELLOW}⚠️  Test script not found, skipping tests${NC}"
fi

# Create production requirements if needed
echo -e "${GREEN}📦 Preparing production requirements...${NC}"
cd "$PROJECT_ROOT/backend"

# Create a production-ready requirements.txt without dev dependencies
if [ -f "requirements.txt" ]; then
    echo -e "${GREEN}📝 Creating production requirements...${NC}"
    # Remove test dependencies for production
    grep -v "pytest" requirements.txt > requirements.prod.txt || cp requirements.txt requirements.prod.txt
fi

# TODO: Add Docker build steps
echo -e "${BLUE}🐳 Docker deployment preparation...${NC}"
echo "# TODO: Add Docker build commands here"

# TODO: Add cloud deployment steps
echo -e "${BLUE}☁️  Cloud deployment preparation...${NC}"
echo "# TODO: Add cloud deployment commands here"

echo -e "${GREEN}✅ Deployment preparation complete!${NC}"
echo -e "${YELLOW}📝 Next steps:${NC}"
echo "1. Review requirements.prod.txt"
echo "2. Set up Docker configuration"
echo "3. Configure cloud deployment"
