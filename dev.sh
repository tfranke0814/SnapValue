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
    "test-step1")
        echo "🧪 Running Step 1 Database Tests..."
        bash "$PROJECT_ROOT/utilities/backend/test_step1.sh"
        ;;
    "test-step2")
        echo "🧪 Running Step 2 Core Backend Services Tests..."
        bash "$PROJECT_ROOT/utilities/backend/test_step2.sh"
        ;;
    "setup")
        echo "Setting up development environment..."
        bash "$PROJECT_ROOT/utilities/development/setup_dev_environment.sh"
        ;;
    "db")
        echo "🗄️ Database utilities..."
        bash "$PROJECT_ROOT/utilities/database/db_utils.sh" "$2"
        ;;
    *)
        echo "SnapValue Development Commands:"
        echo "  ./dev.sh start      - Start the backend server"
        echo "  ./dev.sh test       - Run all backend tests"
        echo "  ./dev.sh test-step1 - Run Step 1 database tests"
        echo "  ./dev.sh test-step2 - Run Step 2 core backend services tests"
        echo "  ./dev.sh setup      - Setup development environment"
        echo "  ./dev.sh db         - Database utilities"
        ;;
esac
