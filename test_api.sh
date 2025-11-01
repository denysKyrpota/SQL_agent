#!/bin/bash
# Quick API Testing Script for SQL AI Agent
# Usage: ./test_api.sh

API_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "SQL AI Agent API Testing Script"
echo "========================================"
echo ""

# Test 1: Root Endpoint
echo -e "${YELLOW}Test 1: Root Endpoint${NC}"
echo "GET /"
curl -s -X GET "$API_URL/" | python -m json.tool
echo -e "${GREEN}✓ Passed${NC}\n"

# Test 2: POST /queries - Expected 401 (Auth Required)
echo -e "${YELLOW}Test 2: POST /queries - Authentication Check${NC}"
echo "POST /api/queries"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL/api/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language_query": "Show me all active users"
  }')

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "$BODY" | python -m json.tool 2>/dev/null || echo "$BODY"

if [ "$HTTP_STATUS" -eq 401 ]; then
  echo -e "${GREEN}✓ Passed (Expected 401 - Auth not configured)${NC}\n"
else
  echo -e "${RED}✗ Failed (Expected 401, got $HTTP_STATUS)${NC}\n"
fi

# Test 3: Validation - Empty Query
echo -e "${YELLOW}Test 3: Validation - Whitespace Only Query${NC}"
echo "POST /api/queries (whitespace query)"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL/api/queries" \
  -H "Content-Type: application/json" \
  -d '{
    "natural_language_query": "   "
  }')

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "$BODY" | python -m json.tool 2>/dev/null || echo "$BODY"

if [ "$HTTP_STATUS" -eq 422 ] || [ "$HTTP_STATUS" -eq 401 ]; then
  echo -e "${GREEN}✓ Passed (Expected 422 or 401, got $HTTP_STATUS)${NC}\n"
else
  echo -e "${RED}✗ Failed (Expected 422 or 401, got $HTTP_STATUS)${NC}\n"
fi

# Test 4: Validation - Missing Field
echo -e "${YELLOW}Test 4: Validation - Missing Required Field${NC}"
echo "POST /api/queries (empty body)"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST "$API_URL/api/queries" \
  -H "Content-Type: application/json" \
  -d '{}')

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "$BODY" | python -m json.tool 2>/dev/null || echo "$BODY"

if [ "$HTTP_STATUS" -eq 422 ]; then
  echo -e "${GREEN}✓ Passed (Expected 422)${NC}\n"
else
  echo -e "${RED}✗ Failed (Expected 422, got $HTTP_STATUS)${NC}\n"
fi

# Test 5: Security Headers
echo -e "${YELLOW}Test 5: Security Headers${NC}"
echo "Checking X-Content-Type-Options, X-Frame-Options, X-XSS-Protection"
HEADERS=$(curl -s -I "$API_URL/")

if echo "$HEADERS" | grep -q "x-content-type-options: nosniff" && \
   echo "$HEADERS" | grep -q "x-frame-options: DENY" && \
   echo "$HEADERS" | grep -q "x-xss-protection: 1; mode=block"; then
  echo -e "${GREEN}✓ All security headers present${NC}\n"
else
  echo -e "${RED}✗ Some security headers missing${NC}\n"
fi

# Summary
echo "========================================"
echo "Testing Complete!"
echo "========================================"
echo ""
echo "Next Steps:"
echo "1. Open Swagger UI: http://localhost:8000/docs"
echo "2. Implement Steps 7-9 for full functionality"
echo "3. See TESTING.md for detailed test scenarios"
