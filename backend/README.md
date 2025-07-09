# SnapValue Backend API

A FastAPI-based backend service for the SnapValue application.

## Features

- **FastAPI Framework**: Modern, fast (high-performance) web framework
- **Automatic API Documentation**: Interactive API docs at `/docs` and `/redoc`
- **CORS Support**: Configured for frontend integration
- **Environment Configuration**: Using pydantic-settings for environment management
- **Testing**: Pytest setup with test coverage
- **Health Checks**: Built-in health check endpoints

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py          # Application configuration
│   ├── models/
│   │   ├── __init__.py
│   │   └── base.py            # Base Pydantic models
│   ├── routers/
│   │   ├── __init__.py
│   │   └── health.py          # Health check endpoints
│   └── utils/
│       ├── __init__.py
│       └── helpers.py         # Utility functions
├── venv/                      # Virtual environment
├── main.py                    # FastAPI application entry point
├── requirements.txt           # Python dependencies
├── test_main.py              # Test cases
├── start_server.sh           # Server startup script
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Quick Start

### 1. Setup Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and configure as needed:

```bash
cp .env.example .env
# Edit .env file with your configuration
```

### 3. Run the Server

#### Option 1: Using the startup script
```bash
./start_server.sh
```

#### Option 2: Direct uvicorn command
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Option 3: Running via Python
```bash
python main.py
```

### 4. Access the API

Once the server is running, you can access:

- **API Root**: http://localhost:8000/
- **Interactive API Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health
- **Ping**: http://localhost:8000/api/v1/ping

## Testing

Run tests using pytest:

```bash
pytest test_main.py -v
```

## API Endpoints

### Health Endpoints

- `GET /api/v1/health` - Health check endpoint
- `GET /api/v1/ping` - Simple ping endpoint

### Root Endpoint

- `GET /` - API information and welcome message

## Development

### Adding New Endpoints

1. Create a new router file in `app/routers/`
2. Define your endpoints using FastAPI decorators
3. Include the router in `main.py`

### Adding New Models

1. Create model files in `app/models/`
2. Use Pydantic for data validation and serialization

### Configuration

Environment variables are managed through `app/core/config.py`. Add new settings to the `Settings` class as needed.

## Dependencies

- **FastAPI**: Web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation
- **Python-Jose**: JWT handling
- **Passlib**: Password hashing
- **Pytest**: Testing framework

## Next Steps

- Add database integration
- Implement authentication and authorization
- Add more API endpoints for your application logic
- Set up logging and monitoring
- Configure production deployment settings
