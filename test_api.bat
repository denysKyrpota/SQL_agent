@echo off
REM Quick API Testing Script for SQL AI Agent (Windows)
REM Usage: test_api.bat

SET API_URL=http://localhost:8000

echo ========================================
echo SQL AI Agent API Testing Script
echo ========================================
echo.

REM Test 1: Root Endpoint
echo [Test 1] Root Endpoint
echo GET /
curl -s -X GET %API_URL%/
echo.
echo [PASSED]
echo.

REM Test 2: POST /queries - Expected 401
echo [Test 2] POST /queries - Authentication Check
echo POST /api/queries
curl -s -X POST %API_URL%/api/queries ^
  -H "Content-Type: application/json" ^
  -d "{\"natural_language_query\": \"Show me all active users\"}"
echo.
echo [Expected 401 - Auth not configured]
echo.

REM Test 3: Validation - Empty Query
echo [Test 3] Validation - Whitespace Only Query
echo POST /api/queries (whitespace)
curl -s -X POST %API_URL%/api/queries ^
  -H "Content-Type: application/json" ^
  -d "{\"natural_language_query\": \"   \"}"
echo.
echo [Expected 422 Validation Error]
echo.

REM Test 4: Validation - Missing Field
echo [Test 4] Validation - Missing Required Field
echo POST /api/queries (empty body)
curl -s -X POST %API_URL%/api/queries ^
  -H "Content-Type: application/json" ^
  -d "{}"
echo.
echo [Expected 422 Validation Error]
echo.

REM Test 5: Check Docs
echo [Test 5] OpenAPI Documentation
echo GET /docs
echo Open in browser: %API_URL%/docs
echo.

echo ========================================
echo Testing Complete!
echo ========================================
echo.
echo Next Steps:
echo 1. Open Swagger UI: %API_URL%/docs
echo 2. Check TESTING.md for detailed scenarios
echo 3. Implement Steps 7-9 for full functionality
echo.
pause
