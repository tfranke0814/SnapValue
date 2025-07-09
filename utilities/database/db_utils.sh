#!/bin/bash

# SnapValue Database Utilities
# This script provides database management utilities

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo -e "${GREEN}🗄️  SnapValue Database Utilities${NC}"

# Function to activate virtual environment
activate_venv() {
    cd "$BACKEND_DIR"
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        echo -e "${RED}❌ Virtual environment not found. Run setup first.${NC}"
        exit 1
    fi
}

# Function to initialize database
init_db() {
    echo -e "${GREEN}🔧 Initializing database...${NC}"
    # TODO: Add database initialization commands
    echo "# TODO: Add database initialization commands here"
}

# Function to migrate database
migrate_db() {
    echo -e "${GREEN}⬆️  Running database migrations...${NC}"
    # TODO: Add database migration commands
    echo "# TODO: Add database migration commands here"
}

# Function to seed database
seed_db() {
    echo -e "${GREEN}🌱 Seeding database with sample data...${NC}"
    # TODO: Add database seeding commands
    echo "# TODO: Add database seeding commands here"
}

# Function to backup database
backup_db() {
    echo -e "${GREEN}💾 Creating database backup...${NC}"
    BACKUP_DIR="$PROJECT_ROOT/backups"
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    
    if [ -f "$BACKEND_DIR/snapvalue.db" ]; then
        cp "$BACKEND_DIR/snapvalue.db" "$BACKUP_DIR/snapvalue_backup_$TIMESTAMP.db"
        echo -e "${GREEN}✅ Database backed up to: $BACKUP_DIR/snapvalue_backup_$TIMESTAMP.db${NC}"
    else
        echo -e "${YELLOW}⚠️  Database file not found${NC}"
    fi
}

# Function to reset database
reset_db() {
    echo -e "${YELLOW}⚠️  This will delete all database data. Are you sure? (y/N)${NC}"
    read -r confirm
    if [[ $confirm =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}🔄 Resetting database...${NC}"
        if [ -f "$BACKEND_DIR/snapvalue.db" ]; then
            rm "$BACKEND_DIR/snapvalue.db"
            echo -e "${GREEN}✅ Database reset complete${NC}"
        else
            echo -e "${YELLOW}⚠️  Database file not found${NC}"
        fi
    else
        echo -e "${BLUE}ℹ️  Database reset cancelled${NC}"
    fi
}

# Main script logic
case "$1" in
    "init")
        activate_venv
        init_db
        ;;
    "migrate")
        activate_venv
        migrate_db
        ;;
    "seed")
        activate_venv
        seed_db
        ;;
    "backup")
        backup_db
        ;;
    "reset")
        activate_venv
        reset_db
        ;;
    *)
        echo "SnapValue Database Utilities:"
        echo "  ./db_utils.sh init     - Initialize database"
        echo "  ./db_utils.sh migrate  - Run database migrations"
        echo "  ./db_utils.sh seed     - Seed database with sample data"
        echo "  ./db_utils.sh backup   - Create database backup"
        echo "  ./db_utils.sh reset    - Reset database (WARNING: deletes all data)"
        ;;
esac
