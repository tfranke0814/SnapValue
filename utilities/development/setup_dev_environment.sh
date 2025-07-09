#!/bin/bash

# SnapValue Development Environment Setup
# This script sets up the entire development environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo -e "${GREEN}🛠️  Setting up SnapValue Development Environment${NC}"
echo "Project Root: $PROJECT_ROOT"

# Setup backend
echo -e "${BLUE}🔧 Setting up backend...${NC}"
if [ -f "$PROJECT_ROOT/utilities/backend/setup_environment.sh" ]; then
    bash "$PROJECT_ROOT/utilities/backend/setup_environment.sh"
else
    echo -e "${RED}❌ Backend setup script not found${NC}"
fi

# TODO: Add frontend setup when available
# echo -e "${BLUE}🔧 Setting up frontend...${NC}"

# Create development shortcuts
echo -e "${GREEN}📝 Creating development shortcuts...${NC}"
cat > "$PROJECT_ROOT/dev.sh" << 'EOF'
#!/bin/bash

# SnapValue Development Shortcuts
# Usage: ./dev.sh [command]

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

case "$1" in
    "start"|"serve")
        echo "Starting backend server..."
        bash "$PROJECT_ROOT/utilities/backend/start_server.sh"
        ;;
    "test")
        echo "Running backend tests..."
        bash "$PROJECT_ROOT/utilities/backend/run_tests.sh"
        ;;
    "setup")
        echo "Setting up development environment..."
        bash "$PROJECT_ROOT/utilities/development/setup_dev_environment.sh"
        ;;
    *)
        echo "SnapValue Development Commands:"
        echo "  ./dev.sh start   - Start the backend server"
        echo "  ./dev.sh test    - Run backend tests"
        echo "  ./dev.sh setup   - Setup development environment"
        ;;
esac
EOF

chmod +x "$PROJECT_ROOT/dev.sh"

echo -e "${GREEN}✅ Development environment setup complete!${NC}"
echo -e "${BLUE}🚀 Quick start:${NC}"
echo "  ./dev.sh start   - Start the backend server"
echo "  ./dev.sh test    - Run backend tests"
echo "  ./dev.sh setup   - Setup development environment"
