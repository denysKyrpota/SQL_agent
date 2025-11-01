# Testing Guide for POST /queries Endpoint

This guide provides step-by-step instructions to test the current implementation of the SQL AI Agent API.

## Prerequisites

### 1. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Verify Installation

```bash
# Check FastAPI installation
python -c "import fastapi; print(f'FastAPI version: {fastapi.__version__}')"

# Check Uvicorn installation
python -c "import uvicorn; print(f'Uvicorn installed')"
```

---

## Starting the Server

### Option 1: Using Python Module

```bash
# From project root directory
python -m backend.app.main
```

### Option 2: Using Uvicorn Directly

```bash
# From project root directory
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### Expected Output

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Starting SQL AI Agent API server
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## Testing with cURL

### Test 1: Root Endpoint

**Purpose**: Verify server is running

```bash
curl -X GET http://localhost:8000/
```

**Expected Response** (200 OK):
```json
{
  "message": "SQL AI Agent API",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

---

### Test 2: OpenAPI Documentation

**Purpose**: Verify API documentation is accessible

```bash
# Open in browser
http://localhost:8000/docs
```

**What to Check**:
- ✅ Swagger UI loads successfully
- ✅ POST /api/queries endpoint is visible
- ✅ Request/response schemas are shown
- ✅ Status codes documented (201, 400, 401, 429, 503)

---

### Test 3: POST /queries - Authentication Error (Expected)

**Purpose**: Verify authentication is required

```bash
curl -X POST http://localhost:8000/api/queries \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language_query": "Show me all active users"
  }' \
  -v
```

**Expected Response** (401 Unauthorized):
```json
{
  "detail": "Authentication not yet configured"
}
```

**Why This Fails**: The `get_current_user()` dependency is a stub that raises 401. This is expected until Step 8 (Dependencies Module) is implemented.

---

### Test 4: POST /queries - Validation Error

**Purpose**: Test Pydantic validation (if we bypass auth)

**Note**: This test won't work until authentication is implemented, but here's how it would look:

```bash
# Empty query (validation error)
curl -X POST http://localhost:8000/api/queries \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language_query": "   "
  }' \
  -v
```

**Expected Response** (422 Unprocessable Entity):
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "natural_language_query"],
      "msg": "Query cannot be only whitespace",
      "input": "   "
    }
  ]
}
```

---

### Test 5: POST /queries - Query Too Long

**Purpose**: Test max length validation

```bash
# Create a 5001 character string (exceeds max)
curl -X POST http://localhost:8000/api/queries \
  -H "Content-Type: application/json" \
  -d "{
    \"natural_language_query\": \"$(python -c 'print("a" * 5001)')\"
  }" \
  -v
```

**Expected Response** (422 Unprocessable Entity):
```json
{
  "detail": [
    {
      "type": "string_too_long",
      "loc": ["body", "natural_language_query"],
      "msg": "String should have at most 5000 characters",
      "input": "aaa...",
      "ctx": {
        "max_length": 5000
      }
    }
  ]
}
```

---

### Test 6: POST /queries - Missing Required Field

**Purpose**: Test required field validation

```bash
curl -X POST http://localhost:8000/api/queries \
  -H "Content-Type: application/json" \
  -d '{}' \
  -v
```

**Expected Response** (422 Unprocessable Entity):
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "natural_language_query"],
      "msg": "Field required",
      "input": {}
    }
  ]
}
```

---

### Test 7: Check CORS Headers

**Purpose**: Verify CORS is configured for frontend

```bash
curl -X OPTIONS http://localhost:8000/api/queries \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v
```

**Expected Headers**:
```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true
```

---

### Test 8: Check Security Headers

**Purpose**: Verify security headers are present

```bash
curl -X GET http://localhost:8000/ -v 2>&1 | grep -E "(X-Content-Type|X-Frame|X-XSS)"
```

**Expected Headers**:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
```

---

## Testing Other Endpoints (Stubs)

These endpoints return 501 Not Implemented as expected:

### GET /queries/{id}

```bash
curl -X GET http://localhost:8000/api/queries/1 -v
```

**Expected**: 401 (auth required) or 501 (not implemented)

### GET /queries (List)

```bash
curl -X GET http://localhost:8000/api/queries?page=1&page_size=20 -v
```

**Expected**: 401 (auth required) or 501 (not implemented)

### POST /queries/{id}/execute

```bash
curl -X POST http://localhost:8000/api/queries/1/execute -v
```

**Expected**: 401 (auth required) or 501 (not implemented)

---

## Testing with Python Requests

Alternatively, use Python for testing:

```python
import requests

# Test root endpoint
response = requests.get("http://localhost:8000/")
print(response.json())

# Test POST /queries (will fail with 401)
response = requests.post(
    "http://localhost:8000/api/queries",
    json={"natural_language_query": "Show me all active users"}
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Test validation error
response = requests.post(
    "http://localhost:8000/api/queries",
    json={"natural_language_query": "   "}  # Whitespace only
)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

---

## Interactive Testing with Swagger UI

1. **Open Swagger UI**: http://localhost:8000/docs
2. **Expand** POST /api/queries endpoint
3. **Click** "Try it out"
4. **Modify** the example request:
   ```json
   {
     "natural_language_query": "Show me all users who registered in the last 30 days"
   }
   ```
5. **Click** "Execute"
6. **Observe** response (should be 401 - Authentication not configured)

---

## Current Implementation Limitations

### ✅ What Works

1. **Server Startup**: FastAPI app starts successfully
2. **Route Registration**: POST /api/queries is registered
3. **Request Validation**: Pydantic validates input (after auth bypass)
4. **OpenAPI Docs**: Auto-generated documentation available
5. **CORS**: Configured for localhost:3000
6. **Security Headers**: All security headers present
7. **Error Handling**: Proper status codes and error responses

### ❌ What Doesn't Work Yet

1. **Authentication**: All requests fail with 401
   - **Why**: `get_current_user()` is a stub
   - **Fix**: Implement Step 8 (Dependencies Module)

2. **Database Operations**: No actual DB queries
   - **Why**: `get_db()` is a stub, no SQLAlchemy models
   - **Fix**: Implement Steps 7-9 (Models, Dependencies, Database)

3. **SQL Generation**: Would fail even if auth worked
   - **Why**: `_generate_sql()` raises NotImplemented
   - **Fix**: Implement LLM Service integration

4. **Rate Limiting**: Not enforced
   - **Why**: Not yet implemented
   - **Fix**: Add rate limiting middleware

---

## Expected Behavior After Steps 7-9

Once database and authentication are implemented:

```bash
# 1. Login first (future)
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }' \
  -c cookies.txt  # Save session cookie

# 2. Create query using session
curl -X POST http://localhost:8000/api/queries \
  -H "Content-Type: application/json" \
  -b cookies.txt \  # Use session cookie
  -d '{
    "natural_language_query": "Show me all active users"
  }'

# Expected: 201 Created with query attempt details
```

---

## Troubleshooting

### Server Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`

**Solution**:
```bash
pip install -r requirements.txt
```

---

**Error**: `ImportError: cannot import name 'queries' from 'backend.app.api'`

**Solution**: Ensure you're running from project root:
```bash
cd d:\10x_agent_sql\agent_sql
python -m backend.app.main
```

---

**Error**: Port 8000 already in use

**Solution**: Use a different port:
```bash
uvicorn backend.app.main:app --port 8001
```

---

### CORS Issues

**Symptom**: Browser shows CORS error when calling from React

**Solution**: Verify frontend URL in `main.py`:
```python
allow_origins=[
    "http://localhost:3000",  # React dev server
    "http://localhost:5173",  # Vite dev server
]
```

---

## Monitoring Server Logs

Watch logs in real-time to see request flow:

```bash
# Run server with DEBUG logging
uvicorn backend.app.main:app --log-level debug
```

**What to Look For**:
- Request path and method
- Status code
- Response time
- Error tracebacks (if any)

---

## Next Steps for Full Testing

After implementing Steps 7-9, you'll be able to test:

1. ✅ **Authentication flow** (login → session cookie → authenticated requests)
2. ✅ **Database operations** (create query attempt in SQLite)
3. ✅ **SQL generation** (OpenAI API integration)
4. ✅ **Error scenarios** (rate limits, service unavailable, timeouts)
5. ✅ **End-to-end workflow** (create → generate → execute → results)

---

## Quick Reference

| Test | Endpoint | Expected Status | Current Status |
|------|----------|----------------|----------------|
| Root | GET / | 200 | ✅ Works |
| Docs | GET /docs | 200 | ✅ Works |
| Create Query | POST /api/queries | 201 | ❌ 401 (auth stub) |
| Get Query | GET /api/queries/{id} | 200 | ❌ 401 (auth stub) |
| List Queries | GET /api/queries | 200 | ❌ 401 (auth stub) |
| Execute | POST /api/queries/{id}/execute | 200 | ❌ 501 (not implemented) |

---

**Ready to test? Start the server and run the curl commands above!**
