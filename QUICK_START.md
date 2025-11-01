# Quick Start - Testing the API

## 🚀 Start the Server

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the server
c
```

Server will start on: **http://localhost:8000**

---

## 📝 Quick cURL Tests

### Test 1: Root Endpoint ✅

```bash
curl http://localhost:8000/
```

**Expected Output:**
```json
{
  "message": "SQL AI Agent API",
  "version": "1.0.0",
  "docs": "/docs",
  "redoc": "/redoc"
}
```

---

### Test 2: POST /queries (Will fail with 401 - Expected) ⚠️

```bash
curl -X POST http://localhost:8000/api/queries \
  -H "Content-Type: application/json" \
  -d '{"natural_language_query": "Show me all active users"}'
```

**Expected Output:**
```json
{
  "detail": "Authentication not yet configured"
}
```

**Why?** The authentication system is not implemented yet (Step 8 pending).

---

### Test 3: Validation - Empty Query

```bash
curl -X POST http://localhost:8000/api/queries \
  -H "Content-Type: application/json" \
  -d '{"natural_language_query": "   "}'
```

**Expected Output:**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "natural_language_query"],
      "msg": "Query cannot be only whitespace"
    }
  ]
}
```

---

### Test 4: Validation - Missing Field

```bash
curl -X POST http://localhost:8000/api/queries \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Expected Output:**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "natural_language_query"],
      "msg": "Field required"
    }
  ]
}
```

---

### Test 5: Check OpenAPI Docs

Open in browser: **http://localhost:8000/docs**

You should see:
- Swagger UI interface
- POST /api/queries endpoint
- Full request/response schemas
- All status codes documented

---

## 🔧 Automated Testing

### Option 1: Python Script (Recommended)

```bash
python test_api.py
```

### Option 2: Bash Script (Linux/Mac)

```bash
chmod +x test_api.sh
./test_api.sh
```

### Option 3: Batch Script (Windows)

```cmd
test_api.bat
```

---

## 🎯 What Works Right Now

| Feature | Status | Notes |
|---------|--------|-------|
| Server startup | ✅ | FastAPI app runs successfully |
| Route registration | ✅ | POST /api/queries is available |
| Request validation | ✅ | Pydantic validates input |
| OpenAPI docs | ✅ | Auto-generated at /docs |
| CORS headers | ✅ | Configured for localhost:3000 |
| Security headers | ✅ | All headers present |
| Error responses | ✅ | Proper status codes |

---

## ⚠️ What Doesn't Work Yet

| Feature | Status | Reason |
|---------|--------|--------|
| Authentication | ❌ | Returns 401 - Dependencies module not implemented |
| Database ops | ❌ | No SQLAlchemy models/session |
| SQL generation | ❌ | LLM service not integrated |
| Query execution | ❌ | PostgreSQL connection not configured |

---

## 📋 Current Implementation Status

**Completed (Steps 1-6):**
- ✅ Database schema (migration exists)
- ✅ Pydantic request/response DTOs
- ✅ Service layer architecture
- ✅ Route handlers with error handling
- ✅ FastAPI app with middleware
- ✅ OpenAPI documentation

**Pending (Steps 7-9):**
- ❌ SQLAlchemy ORM models
- ❌ Database connection and session management
- ❌ Authentication dependencies (get_current_user, get_db)

---

## 🔍 Inspecting the API

### View OpenAPI Schema

```bash
curl http://localhost:8000/openapi.json | python -m json.tool
```

### Check All Routes

```bash
curl http://localhost:8000/docs
```

### Test CORS

```bash
curl -X OPTIONS http://localhost:8000/api/queries \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v
```

Look for these headers in response:
- `Access-Control-Allow-Origin: http://localhost:3000`
- `Access-Control-Allow-Credentials: true`

---

## 📊 Testing Checklist

- [ ] Server starts without errors
- [ ] Root endpoint returns JSON
- [ ] OpenAPI docs load at /docs
- [ ] POST /queries returns 401 (auth not configured)
- [ ] Validation errors return 422
- [ ] Security headers present in all responses
- [ ] CORS headers configured correctly

---

## 🐛 Troubleshooting

### Server won't start?

```bash
# Check if FastAPI is installed
pip list | grep fastapi

# Reinstall if needed
pip install -r requirements.txt
```

### Port 8000 already in use?

```bash
# Use a different port
uvicorn backend.app.main:app --port 8001
```

### Module not found error?

```bash
# Make sure you're in the project root
cd d:\10x_agent_sql\agent_sql

# Run as module
python -m backend.app.main
```

---

## 📚 Next Steps

1. **Review Implementation**: Check [TESTING.md](TESTING.md) for detailed test scenarios
2. **Implement Steps 7-9**: Database models, dependencies, and database config
3. **Add Authentication**: Login/logout endpoints
4. **Integrate LLM**: OpenAI API for SQL generation
5. **Full E2E Testing**: Complete workflow from query creation to execution

---

## 📞 Need Help?

- Full testing guide: [TESTING.md](TESTING.md)
- Implementation plan: [.ai/view-implementation-plan.md](.ai/view-implementation-plan.md)
- API specification: [.ai/api-plan.md](.ai/api-plan.md)

---

**Ready to continue?** Let me know when you want to implement Steps 7-9!
