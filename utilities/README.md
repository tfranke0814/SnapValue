# SnapValue Utilities

This directory contains all utility scripts for the SnapValue project, organized by category.

## 📁 Directory Structure

```
utilities/
├── backend/              # Backend-related scripts
│   ├── start_server.sh   # Start the FastAPI server
│   ├── run_tests.sh      # Run backend tests
│   └── setup_environment.sh # Setup backend environment
├── development/          # Development utilities
│   └── setup_dev_environment.sh # Setup entire dev environment
├── deployment/           # Deployment scripts
│   └── deploy.sh         # Deployment preparation
├── database/             # Database utilities
│   └── db_utils.sh       # Database management utilities
└── README.md             # This file
```

## 🚀 Quick Start

### Setup Development Environment
```bash
# Setup the entire development environment
./utilities/development/setup_dev_environment.sh

# Or use the shortcut created in project root
./dev.sh setup
```

### Backend Operations
```bash
# Start the backend server
./utilities/backend/start_server.sh

# Run backend tests
./utilities/backend/run_tests.sh

# Setup backend environment only
./utilities/backend/setup_environment.sh
```

### Database Management
```bash
# Initialize database
./utilities/database/db_utils.sh init

# Run migrations
./utilities/database/db_utils.sh migrate

# Seed with sample data
./utilities/database/db_utils.sh seed

# Create backup
./utilities/database/db_utils.sh backup

# Reset database (WARNING: deletes all data)
./utilities/database/db_utils.sh reset
```

### Deployment
```bash
# Prepare for deployment
./utilities/deployment/deploy.sh
```

## 📝 Development Shortcuts

After running the development setup, you can use these shortcuts from the project root:

```bash
# Start backend server
./dev.sh start

# Run tests
./dev.sh test

# Setup environment
./dev.sh setup
```

## 🔧 Script Features

All scripts include:
- **Error handling** - Scripts exit on errors
- **Colored output** - Easy to read status messages
- **Path detection** - Automatically find project directories
- **Environment checks** - Verify prerequisites before running
- **Help messages** - Usage instructions when run without arguments

## 📋 Adding New Scripts

When adding new utility scripts:

1. Place them in the appropriate category directory
2. Make them executable: `chmod +x script_name.sh`
3. Include proper error handling and colored output
4. Add usage instructions when run without arguments
5. Update this README with the new script information

## 🛠️ Script Templates

### Basic Script Template
```bash
#!/bin/bash

# Script Description
# Brief description of what this script does

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${GREEN}🔧 Script Name${NC}"

# Your script logic here
```

## 📞 Support

If you encounter issues with any utility scripts:

1. Check that you're in the project root directory
2. Ensure all dependencies are installed
3. Verify file permissions are correct
4. Check the script output for error messages

For additional help, refer to the main project documentation.
