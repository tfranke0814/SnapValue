#!/bin/bash

# SnapValue Step 1 Testing Script
# Tests for Database Models & Configuration

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

echo -e "${GREEN}🧪 SnapValue Step 1 Testing Suite${NC}"
echo -e "${BLUE}Testing: Database Models & Configuration${NC}"
echo "Project Root: $PROJECT_ROOT"
echo "Backend Directory: $BACKEND_DIR"

# Navigate to backend directory
cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Run setup first.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${GREEN}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Install testing dependencies
echo -e "${GREEN}📦 Installing testing dependencies...${NC}"
pip install -r requirements.txt

# Run specific Step 1 tests
echo -e "${GREEN}🏃 Running Step 1 Database Tests...${NC}"
echo ""

# Test 1: User Model Tests
echo -e "${BLUE}1️⃣ Testing User Model...${NC}"
pytest tests/models/test_user.py -v --tb=short

# Test 2: Appraisal Model Tests
echo -e "${BLUE}2️⃣ Testing Appraisal Model...${NC}"
pytest tests/models/test_appraisal.py -v --tb=short

# Test 3: MarketData Model Tests
echo -e "${BLUE}3️⃣ Testing MarketData Model...${NC}"
pytest tests/models/test_market_data.py -v --tb=short

# Test 4: Database Connection Tests
echo -e "${BLUE}4️⃣ Testing Database Connection...${NC}"
pytest tests/database/test_connection.py -v --tb=short

# Run all Step 1 tests together
echo -e "${GREEN}🔄 Running All Step 1 Tests Together...${NC}"
pytest tests/models/ tests/database/ -v --tb=short --cov=app/models --cov=app/database --cov-report=term-missing

# Generate test report
echo -e "${GREEN}📊 Generating Test Coverage Report...${NC}"
pytest tests/models/ tests/database/ --cov=app/models --cov=app/database --cov-report=html --cov-report=term

echo ""
echo -e "${GREEN}✅ Step 1 Testing Complete!${NC}"
echo -e "${BLUE}📋 Test Summary:${NC}"
echo "  ✅ User Model Tests"
echo "  ✅ Appraisal Model Tests"  
echo "  ✅ MarketData Model Tests"
echo "  ✅ Database Connection Tests"
echo ""
echo -e "${YELLOW}📁 Coverage report available in: htmlcov/index.html${NC}"
echo -e "${GREEN}🚀 Ready for Step 2: Core Backend Services Architecture${NC}"
