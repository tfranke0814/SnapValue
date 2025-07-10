# SnapValue Scripts Documentation

This document provides comprehensive documentation for all utility scripts in the SnapValue project.

## 📋 Table of Contents

1. [Quick Reference](#quick-reference)
2. [Development Shortcuts](#development-shortcuts)
3. [Backend Scripts](#backend-scripts)
4. [Database Utilities](#database-utilities)
5. [Deployment Scripts](#deployment-scripts)
6. [Development Environment](#development-environment)
7. [Script Features](#script-features)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Reference

### Most Common Commands
```bash
# Start development server
./dev.sh start

# Run tests
./dev.sh test

# Setup environment
./dev.sh setup

# Show help
./dev.sh
```

---

## 🛠️ Development Shortcuts

### `./dev.sh` - Main Development Script
**Location**: `/dev.sh` (project root)

**Usage**: `./dev.sh [command]`

**Commands**:
- `start` or `serve` - Start the backend server
- `test` - Run all backend tests
- `setup` - Setup development environment
- (no args) - Show help menu

**Examples**:
```bash
./dev.sh start           # Start FastAPI server
./dev.sh test            # Run pytest tests
./dev.sh setup           # Setup entire dev environment
```

---

## 🔧 Backend Scripts

### `./utilities/backend/start_server.sh`
**Purpose**: Start the FastAPI backend server with full environment setup

**Features**:
- ✅ Automatic virtual environment activation
- ✅ Dependency installation/updates
- ✅ Environment validation
- ✅ Colored output with status indicators
- ✅ Clear server information display

**Usage**:
```bash
./utilities/backend/start_server.sh
```

**Output**:
- 🚀 Starting message with project paths
- 🔧 Environment activation status
- 📦 Dependency installation progress
- 🌟 Server startup information
- Server available at: http://localhost:8000
- API docs at: http://localhost:8000/docs

---

### `./utilities/backend/run_tests.sh`
**Purpose**: Run all backend tests with proper environment setup

**Features**:
- ✅ Virtual environment validation
- ✅ Pytest execution with verbose output
- ✅ Colored test results
- ✅ Error handling and reporting

**Usage**:
```bash
./utilities/backend/run_tests.sh
```

**Test Coverage**:
- `test_root_endpoint` - Tests API root endpoint
- `test_health_check` - Tests health check endpoint
- `test_ping` - Tests ping endpoint

---

### `./utilities/backend/setup_environment.sh`
**Purpose**: Setup backend development environment from scratch

**Features**:
- ✅ Python version checking
- ✅ Virtual environment creation
- ✅ Pip upgrade
- ✅ Dependency installation
- ✅ Environment file creation

**Usage**:
```bash
./utilities/backend/setup_environment.sh
```

**What it does**:
1. Creates virtual environment if missing
2. Activates virtual environment
3. Upgrades pip to latest version
4. Installs all dependencies from requirements.txt
5. Creates .env file from .env.example template

---

## 🗄️ Database Utilities

### `./utilities/database/db_utils.sh`
**Purpose**: Database management utilities

**Usage**: `./utilities/database/db_utils.sh [command]`

**Commands**:

#### `init` - Initialize Database
```bash
./utilities/database/db_utils.sh init
```
- Creates database schema
- Sets up initial tables
- Configures database settings

#### `migrate` - Run Database Migrations
```bash
./utilities/database/db_utils.sh migrate
```
- Applies database schema changes
- Updates existing data structures
- Handles version upgrades

#### `seed` - Seed Database with Sample Data
```bash
./utilities/database/db_utils.sh seed
```
- Populates database with test data
- Creates sample records
- Useful for development/testing

#### `backup` - Create Database Backup
```bash
./utilities/database/db_utils.sh backup
```
- Creates timestamped backup file
- Saves to `backups/` directory
- Format: `snapvalue_backup_YYYYMMDD_HHMMSS.db`

#### `reset` - Reset Database (⚠️ DESTRUCTIVE)
```bash
./utilities/database/db_utils.sh reset
```
- **WARNING**: Deletes all database data
- Requires confirmation (y/N)
- Removes database file completely

---

## 🚀 Deployment Scripts

### `./utilities/deployment/deploy.sh`
**Purpose**: Prepare application for deployment

**Features**:
- ✅ Pre-deployment testing
- ✅ Production requirements generation
- ✅ Deployment checklist
- ✅ Environment validation

**Usage**:
```bash
./utilities/deployment/deploy.sh
```

**Process**:
1. **🧪 Run Tests** - Ensures all tests pass before deployment
2. **📦 Create Production Requirements** - Generates `requirements.prod.txt`
3. **🐳 Docker Preparation** - Placeholder for Docker setup
4. **☁️ Cloud Deployment** - Placeholder for cloud deployment
5. **📝 Next Steps** - Provides deployment checklist

**Generated Files**:
- `requirements.prod.txt` - Production dependencies (excludes test packages)

---

## 🛠️ Development Environment

### `./utilities/development/setup_dev_environment.sh`
**Purpose**: Complete development environment setup

**Features**:
- ✅ Backend environment setup
- ✅ Development shortcuts creation
- ✅ Project structure validation
- ✅ Comprehensive environment preparation

**Usage**:
```bash
./utilities/development/setup_dev_environment.sh
```

**What it creates**:
- Backend virtual environment
- Development shortcut script (`dev.sh`)
- Environment configuration
- Project structure validation

---

## ✨ Script Features

### Common Features Across All Scripts

#### 🎨 **Colored Output**
- 🔴 **Red**: Errors and failures
- 🟢 **Green**: Success messages and completions
- 🟡 **Yellow**: Warnings and important notes
- 🔵 **Blue**: Information and process steps

#### 🔧 **Error Handling**
- `set -e` - Exit on any error
- Validation checks before execution
- Clear error messages with context
- Graceful failure handling

#### 📍 **Path Management**
- Automatic project root detection
- Relative path resolution
- Cross-platform compatibility
- Directory validation

#### 📚 **Help System**
- Help messages for all scripts
- Usage examples
- Command descriptions
- Clear documentation

---

## 🔍 Troubleshooting

### Common Issues and Solutions

#### **Issue**: "Virtual environment not found"
**Solution**: Run the setup script first:
```bash
./utilities/backend/setup_environment.sh
```

#### **Issue**: "Address already in use" (Port 8000)
**Solution**: Kill existing process:
```bash
sudo fuser -k 8000/tcp
```

#### **Issue**: "Permission denied"
**Solution**: Make scripts executable:
```bash
chmod +x utilities/backend/*.sh
chmod +x utilities/database/*.sh
chmod +x utilities/deployment/*.sh
chmod +x utilities/development/*.sh
```

#### **Issue**: "Command not found"
**Solution**: Run from project root:
```bash
cd /path/to/SnapValue
./dev.sh start
```

#### **Issue**: "Python import errors"
**Solution**: Ensure virtual environment is activated:
```bash
cd backend
source venv/bin/activate
```

---

## 📂 Script Locations

```
utilities/
├── backend/
│   ├── start_server.sh      # Start FastAPI server
│   ├── run_tests.sh         # Run backend tests
│   └── setup_environment.sh # Setup backend environment
├── database/
│   └── db_utils.sh          # Database management
├── deployment/
│   └── deploy.sh            # Deployment preparation
├── development/
│   └── setup_dev_environment.sh # Complete dev setup
└── README.md                # Utilities documentation

dev.sh                       # Main development shortcuts (project root)
```

---

## 🚦 Status Indicators

### Script Output Legend
- 🚀 **Starting/Launch**: Script initialization
- 🔧 **Setup/Configuration**: Environment setup
- 📦 **Dependencies**: Package installation
- 🌟 **Ready**: Server/service ready
- ✅ **Success**: Operation completed successfully
- ❌ **Error**: Operation failed
- ⚠️ **Warning**: Important notice
- 📝 **Info**: General information
- 🧪 **Testing**: Running tests
- 💾 **Backup**: Database backup operations
- 🗄️ **Database**: Database operations
- 🐳 **Docker**: Docker operations
- ☁️ **Cloud**: Cloud deployment

---

## 📄 Script Templates

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
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

echo -e "${GREEN}🔧 Script Name${NC}"

# Your script logic here
```

---

## 📞 Support

For issues with any script:

1. **Check Prerequisites**: Ensure Python 3.10+ is installed
2. **Verify Location**: Run scripts from project root
3. **Check Permissions**: Ensure scripts are executable
4. **Read Output**: Look for colored error messages
5. **Environment**: Ensure virtual environment is properly set up

For additional help, refer to individual script help messages:
```bash
./utilities/database/db_utils.sh
./dev.sh
```

---

*Last Updated: July 9, 2025*
*SnapValue Project - Utility Scripts Documentation*
