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
