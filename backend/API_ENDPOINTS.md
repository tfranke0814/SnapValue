# SnapValue REST API Endpoints

This document provides comprehensive documentation for all REST API endpoints in the SnapValue backend.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Rate Limiting

- **Default**: 100 requests per minute
- **Premium**: 500 requests per minute
- **Enterprise**: 1000 requests per minute

## Response Format

All responses follow a consistent format:

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "success": false,
  "error_code": "ERROR_CODE",
  "message": "Error description",
  "details": { ... },
  "timestamp": "2024-01-15T10:30:00Z",
  "correlation_id": "corr_123456789"
}
```

## Endpoints

### 🖼️ Appraisal Endpoints

#### Submit Image for Appraisal
```http
POST /api/v1/appraisal/submit
```

**Description**: Submit an image for AI-powered appraisal analysis.

**Request**: `multipart/form-data`
- `image_file` (file, optional): Image file to analyze
- `image_url` (string, optional): URL of image to analyze
- `category` (string, optional): Item category hint
- `target_condition` (string, optional): Target condition for valuation
- `priority` (string, optional): Processing priority (low, normal, high, urgent)
- `use_cache` (boolean, optional): Whether to use cached results (default: true)
- `options` (string, optional): Additional options as JSON string
- `user_id` (string, optional): User identifier

**Response**: `201 Created`
```json
{
  "appraisal_id": "appraisal_123456",
  "task_id": "task_789012",
  "status": "submitted",
  "submitted_at": "2024-01-15T10:30:00Z",
  "estimated_completion_minutes": 3,
  "correlation_id": "corr_123456789"
}
```

#### Get Appraisal Results
```http
GET /api/v1/appraisal/{appraisal_id}
```

**Description**: Get complete appraisal results including estimated value, features, and comparable items.

**Response**: `200 OK`
```json
{
  "appraisal_id": "appraisal_123456",
  "status": "completed",
  "estimated_value": 299.99,
  "price_range": {
    "min": 250.00,
    "max": 350.00,
    "currency": "USD"
  },
  "confidence_score": 0.95,
  "category": "electronics",
  "condition": "good",
  "features": ["brand: Apple", "model: iPhone 12", "storage: 128GB"],
  "comparable_items": [...],
  "processing_time_seconds": 45.2,
  "completed_at": "2024-01-15T10:35:00Z"
}
```

#### Get Appraisal Status
```http
GET /api/v1/appraisal/{appraisal_id}/status
```

**Description**: Get current processing status and progress of an appraisal.

**Response**: `200 OK`
```json
{
  "appraisal_id": "appraisal_123456",
  "status": "processing_image",
  "progress_percentage": 65,
  "current_step": "ai_analysis",
  "estimated_completion_minutes": 1,
  "processing_steps": [...],
  "updated_at": "2024-01-15T10:32:00Z"
}
```

#### Submit Batch Appraisals
```http
POST /api/v1/appraisal/batch
```

**Description**: Submit multiple images for batch appraisal processing.

**Request**: `application/json`
```json
{
  "items": [
    {
      "image_url": "https://example.com/image1.jpg",
      "category": "electronics",
      "priority": "normal"
    },
    {
      "image_url": "https://example.com/image2.jpg",
      "category": "collectibles",
      "priority": "high"
    }
  ],
  "batch_options": {
    "priority": "normal",
    "notify_completion": true
  }
}
```

**Response**: `201 Created`
```json
{
  "batch_id": "batch_123456",
  "appraisal_ids": ["appraisal_123456", "appraisal_123457"],
  "total_items": 2,
  "estimated_completion_minutes": 6,
  "status": "submitted"
}
```

#### List User Appraisals
```http
GET /api/v1/appraisal/list
```

**Description**: Get paginated list of user's appraisals with optional filtering.

**Query Parameters**:
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20, max: 100)
- `status` (string): Filter by status
- `category` (string): Filter by category
- `start_date` (datetime): Filter by start date
- `end_date` (datetime): Filter by end date

**Response**: `200 OK`
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "has_next": true,
  "has_previous": false
}
```

### 🔐 Authentication Endpoints

#### User Login
```http
POST /api/v1/auth/login
```

**Description**: Authenticate user with email and password.

**Request**: `application/json`
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response**: `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "api_key": "sk_test_123456789",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### User Logout
```http
POST /api/v1/auth/logout
```

**Description**: Logout current user and invalidate token.

**Response**: `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
```

**Description**: Refresh access token using refresh token.

**Request**: `application/json`
```json
{
  "refresh_token": "refresh_token_here"
}
```

**Response**: `200 OK`
```json
{
  "access_token": "new_access_token_here",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### Get Current User
```http
GET /api/v1/auth/me
```

**Description**: Get current authenticated user information.

**Response**: `200 OK`
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "api_key": "sk_test_123456789",
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T10:30:00Z",
  "is_active": true,
  "appraisal_count": 25,
  "subscription_tier": "premium"
}
```

### 👤 User Management Endpoints

#### Register New User
```http
POST /api/v1/users/register
```

**Description**: Register a new user account.

**Request**: `application/json`
```json
{
  "email": "newuser@example.com",
  "password": "securepassword123",
  "full_name": "Jane Smith",
  "metadata": {
    "source": "web",
    "referral": "google"
  }
}
```

**Response**: `201 Created`
```json
{
  "user_id": 2,
  "email": "newuser@example.com",
  "full_name": "Jane Smith",
  "api_key": "sk_test_987654321",
  "created_at": "2024-01-15T10:30:00Z",
  "message": "User registered successfully"
}
```

#### Get User Profile
```http
GET /api/v1/users/profile
```

**Description**: Get current user's profile information.

**Response**: `200 OK`
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "api_key": "sk_test_123456789",
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T10:30:00Z",
  "is_active": true,
  "appraisal_count": 25,
  "subscription_tier": "premium"
}
```

#### Update User Profile
```http
PUT /api/v1/users/profile
```

**Description**: Update current user's profile information.

**Request**: `application/json`
```json
{
  "full_name": "John Smith",
  "metadata": {
    "preferences": {
      "notifications": true,
      "theme": "dark"
    }
  }
}
```

**Response**: `200 OK`
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "full_name": "John Smith",
  "api_key": "sk_test_123456789",
  "created_at": "2024-01-15T10:30:00Z",
  "last_login": "2024-01-15T10:30:00Z",
  "is_active": true,
  "appraisal_count": 25,
  "subscription_tier": "premium"
}
```

#### Get User Statistics
```http
GET /api/v1/users/stats
```

**Description**: Get current user's usage statistics.

**Response**: `200 OK`
```json
{
  "user_id": 1,
  "total_appraisals": 25,
  "completed_appraisals": 23,
  "failed_appraisals": 2,
  "average_processing_time": 42.5,
  "total_spent": 125.00,
  "favorite_categories": ["electronics", "collectibles"],
  "recent_activity": [...],
  "monthly_usage": {
    "2024-01": 15,
    "2024-02": 10
  },
  "account_created": "2024-01-01T00:00:00Z",
  "last_appraisal": "2024-01-15T10:30:00Z"
}
```

#### Regenerate API Key
```http
POST /api/v1/users/regenerate-api-key
```

**Description**: Generate a new API key for the current user.

**Response**: `200 OK`
```json
{
  "api_key": "sk_test_new_key_123456789",
  "message": "API key regenerated successfully",
  "regenerated_at": "2024-01-15T10:30:00Z"
}
```

#### Delete User Account
```http
DELETE /api/v1/users/account
```

**Description**: Delete current user's account and all associated data.

**Response**: `200 OK`
```json
{
  "message": "User account deleted successfully",
  "data": {
    "user_id": 1,
    "deleted_at": "2024-01-15T10:30:00Z"
  }
}
```

### 📊 Status & Monitoring Endpoints

#### Get Appraisal Status
```http
GET /api/v1/status/appraisal/{appraisal_id}
```

**Description**: Get detailed status of a specific appraisal.

**Response**: `200 OK`
```json
{
  "appraisal_id": "appraisal_123456",
  "status": "processing",
  "progress_percentage": 75,
  "current_step": "market_analysis",
  "steps_completed": 6,
  "total_steps": 8,
  "estimated_completion_minutes": 1,
  "processing_steps": [...],
  "updated_at": "2024-01-15T10:32:00Z"
}
```

#### List Appraisals with Filters
```http
GET /api/v1/status/appraisals
```

**Description**: Get paginated list of appraisals with filtering options.

**Query Parameters**:
- `user_id` (integer): Filter by user ID
- `status` (string): Filter by status
- `category` (string): Filter by category
- `start_date` (datetime): Filter by start date
- `end_date` (datetime): Filter by end date
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20, max: 100)

**Response**: `200 OK`
```json
{
  "items": [...],
  "total": 1250,
  "page": 1,
  "page_size": 20,
  "total_pages": 63,
  "has_next": true,
  "has_previous": false
}
```

#### Get Processing Queue Status
```http
GET /api/v1/status/queue
```

**Description**: Get current processing queue status and statistics.

**Response**: `200 OK`
```json
{
  "queue_length": 15,
  "processing_count": 3,
  "completed_today": 245,
  "failed_today": 5,
  "average_processing_time": 42.5,
  "estimated_wait_time": 180,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### Get System Statistics
```http
GET /api/v1/status/stats
```

**Description**: Get overall system statistics and metrics.

**Response**: `200 OK`
```json
{
  "total_appraisals": 15280,
  "appraisals_today": 245,
  "appraisals_this_month": 3240,
  "success_rate": 0.968,
  "average_processing_time": 42.5,
  "total_users": 1250,
  "active_users_today": 85,
  "system_uptime": 2592000,
  "last_updated": "2024-01-15T10:30:00Z"
}
```

#### Cancel Appraisal
```http
POST /api/v1/status/appraisal/{appraisal_id}/cancel
```

**Description**: Cancel a pending or processing appraisal.

**Response**: `200 OK`
```json
{
  "message": "Appraisal appraisal_123456 cancelled successfully",
  "data": {
    "appraisal_id": "appraisal_123456",
    "status": "cancelled"
  }
}
```

#### Get Appraisal Processing History
```http
GET /api/v1/status/appraisal/{appraisal_id}/history
```

**Description**: Get detailed processing history for an appraisal.

**Response**: `200 OK`
```json
{
  "appraisal_id": "appraisal_123456",
  "total_duration_seconds": 45.2,
  "steps": [
    {
      "step_name": "image_validation",
      "status": "completed",
      "started_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:30:05Z",
      "duration_seconds": 5.0,
      "details": {
        "file_size": 1024000,
        "format": "JPEG"
      }
    },
    {
      "step_name": "ai_analysis",
      "status": "completed",
      "started_at": "2024-01-15T10:30:05Z",
      "completed_at": "2024-01-15T10:30:35Z",
      "duration_seconds": 30.0,
      "details": {
        "confidence": 0.95,
        "objects_detected": 3
      }
    }
  ],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

### 🏥 System Monitoring Endpoints

#### System Health Check
```http
GET /api/v1/monitoring/health
```

**Description**: Get comprehensive system health status.

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "services": [
    {
      "name": "database",
      "status": "healthy",
      "response_time_ms": 15.2,
      "last_checked": "2024-01-15T10:30:00Z"
    },
    {
      "name": "ai_service",
      "status": "healthy",
      "response_time_ms": 234.5,
      "last_checked": "2024-01-15T10:30:00Z"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z",
  "uptime_seconds": 86400.0,
  "version": "1.0.0"
}
```

#### Get System Metrics
```http
GET /api/v1/monitoring/metrics
```

**Description**: Get detailed system metrics and performance data.

**Response**: `200 OK`
```json
{
  "cpu_usage_percent": 45.2,
  "memory_usage_percent": 62.8,
  "disk_usage_percent": 34.1,
  "active_connections": 150,
  "requests_per_minute": 85,
  "error_rate_percent": 0.5,
  "cache_hit_rate_percent": 92.3,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Get Performance Statistics
```http
GET /api/v1/monitoring/performance
```

**Description**: Get performance statistics and benchmarks.

**Response**: `200 OK`
```json
{
  "average_response_time_ms": 125.5,
  "p95_response_time_ms": 250.0,
  "p99_response_time_ms": 500.0,
  "throughput_requests_per_second": 45.2,
  "concurrent_users": 25,
  "database_query_time_ms": 15.2,
  "ai_processing_time_ms": 2500.0,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 📚 API Documentation Endpoints

#### List All Endpoints
```http
GET /api/v1/docs-api/endpoints
```

**Description**: Get comprehensive list of all available API endpoints.

**Response**: `200 OK`
```json
{
  "api_version": "1.0.0",
  "description": "SnapValue API - AI-powered item appraisal service",
  "base_url": "/api/v1",
  "authentication": "JWT Bearer token required for most endpoints",
  "rate_limiting": "100 requests per minute per user",
  "endpoints": {...},
  "common_responses": {...},
  "example_requests": {...}
}
```

#### Get API Schemas
```http
GET /api/v1/docs-api/schemas
```

**Description**: Get all API request and response schemas.

**Response**: `200 OK`
```json
{
  "requests": {
    "AppraisalSubmissionRequest": {...},
    "LoginRequest": {...},
    "UserRegistrationRequest": {...}
  },
  "responses": {
    "AppraisalSubmissionResponse": {...},
    "AppraisalResultResponse": {...},
    "ErrorResponse": {...}
  }
}
```

#### Get Rate Limiting Information
```http
GET /api/v1/docs-api/rate-limits
```

**Description**: Get information about API rate limits and usage.

**Response**: `200 OK`
```json
{
  "default": {
    "requests_per_minute": 100,
    "requests_per_hour": 1000,
    "requests_per_day": 10000
  },
  "premium": {
    "requests_per_minute": 500,
    "requests_per_hour": 5000,
    "requests_per_day": 50000
  },
  "endpoints": {...},
  "headers": {...}
}
```

### 🩺 Health Check Endpoints

#### Basic Health Check
```http
GET /api/v1/health
```

**Description**: Simple health check endpoint.

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "service": "SnapValue API",
  "version": "1.0.0"
}
```

#### Simple Ping
```http
GET /api/v1/ping
```

**Description**: Simple ping endpoint for basic connectivity testing.

**Response**: `200 OK`
```json
{
  "message": "pong"
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Invalid request parameters |
| `AUTHENTICATION_ERROR` | Invalid or missing authentication |
| `AUTHORIZATION_ERROR` | Insufficient permissions |
| `RESOURCE_NOT_FOUND` | Requested resource not found |
| `RESOURCE_CONFLICT` | Resource already exists |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `EXTERNAL_SERVICE_ERROR` | External service failure |
| `AI_PROCESSING_ERROR` | AI service error |
| `STORAGE_ERROR` | File storage error |
| `INTERNAL_ERROR` | Internal server error |

## Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request |
| `401` | Unauthorized |
| `403` | Forbidden |
| `404` | Not Found |
| `409` | Conflict |
| `422` | Unprocessable Entity |
| `429` | Too Many Requests |
| `500` | Internal Server Error |
| `502` | Bad Gateway |
| `503` | Service Unavailable |

## Testing

To test the API endpoints:

1. **Start the server**:
   ```bash
   cd /home/vphilavong/Projects/SnapValue/backend
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access interactive documentation**:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

3. **Test with curl**:
   ```bash
   # Health check
   curl http://localhost:8000/api/v1/health
   
   # List endpoints
   curl http://localhost:8000/api/v1/docs-api/endpoints
   
   # Login (get token)
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com", "password": "password"}'
   
   # Submit appraisal (with token)
   curl -X POST http://localhost:8000/api/v1/appraisal/submit \
     -H "Authorization: Bearer <token>" \
     -F "image_file=@/path/to/image.jpg" \
     -F "category=electronics"
   ```

## Next Steps

1. **Fix remaining import issues** in service dependencies
2. **Test endpoints** with a running FastAPI server
3. **Create unit tests** for each endpoint
4. **Add integration tests** for complete workflows
5. **Implement authentication middleware**
6. **Add rate limiting middleware**
7. **Create API client SDK** for easier integration

---

*This completes Step 7: REST API Endpoints for the SnapValue backend development plan.*
