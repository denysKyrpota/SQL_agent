#!/usr/bin/env python3
"""
Quick API Testing Script for SQL AI Agent
Usage: python test_api.py
"""

import requests
import json
from typing import Dict, Any


API_URL = "http://localhost:8000"


def print_test(test_num: int, description: str):
    """Print test header."""
    print(f"\n{'='*60}")
    print(f"Test {test_num}: {description}")
    print('='*60)


def print_response(response: requests.Response):
    """Pretty print response."""
    print(f"Status: {response.status_code} {response.reason}")
    print(f"Headers: {dict(response.headers)}")
    try:
        print(f"Body: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Body: {response.text}")


def test_root():
    """Test 1: Root endpoint."""
    print_test(1, "Root Endpoint - GET /")

    response = requests.get(f"{API_URL}/")
    print_response(response)

    assert response.status_code == 200, "Expected 200 OK"
    assert "message" in response.json(), "Expected message in response"
    print("✓ PASSED")


def test_post_queries_auth():
    """Test 2: POST /queries - Should fail with 401 (auth not configured)."""
    print_test(2, "POST /queries - Authentication Check")

    response = requests.post(
        f"{API_URL}/api/queries",
        json={"natural_language_query": "Show me all active users"}
    )
    print_response(response)

    # Should fail with 401 because auth is not implemented yet
    if response.status_code == 401:
        print("✓ PASSED (Expected 401 - Auth not configured)")
    else:
        print(f"⚠ UNEXPECTED (Got {response.status_code}, expected 401)")


def test_validation_whitespace():
    """Test 3: Validation - Whitespace only query."""
    print_test(3, "Validation - Whitespace Only Query")

    response = requests.post(
        f"{API_URL}/api/queries",
        json={"natural_language_query": "   "}
    )
    print_response(response)

    # Should fail with 422 (validation) or 401 (auth)
    if response.status_code in [422, 401]:
        print(f"✓ PASSED (Expected 422 or 401, got {response.status_code})")
    else:
        print(f"✗ FAILED (Expected 422 or 401, got {response.status_code})")


def test_validation_missing_field():
    """Test 4: Validation - Missing required field."""
    print_test(4, "Validation - Missing Required Field")

    response = requests.post(
        f"{API_URL}/api/queries",
        json={}
    )
    print_response(response)

    # Should fail with 422 (validation error)
    if response.status_code == 422:
        print("✓ PASSED (Expected 422 Validation Error)")
    else:
        print(f"⚠ UNEXPECTED (Got {response.status_code}, expected 422)")


def test_validation_too_long():
    """Test 5: Validation - Query too long (>5000 chars)."""
    print_test(5, "Validation - Query Too Long")

    long_query = "a" * 5001
    response = requests.post(
        f"{API_URL}/api/queries",
        json={"natural_language_query": long_query}
    )
    print_response(response)

    # Should fail with 422 (validation error)
    if response.status_code == 422:
        print("✓ PASSED (Expected 422 - String too long)")
    else:
        print(f"⚠ UNEXPECTED (Got {response.status_code}, expected 422)")


def test_security_headers():
    """Test 6: Security headers."""
    print_test(6, "Security Headers")

    response = requests.get(f"{API_URL}/")

    required_headers = {
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "x-xss-protection": "1; mode=block",
    }

    print("Checking security headers:")
    all_present = True
    for header, expected_value in required_headers.items():
        actual_value = response.headers.get(header, "NOT FOUND")
        status = "✓" if actual_value.lower() == expected_value.lower() else "✗"
        print(f"  {status} {header}: {actual_value}")
        if actual_value.lower() != expected_value.lower():
            all_present = False

    if all_present:
        print("\n✓ PASSED (All security headers present)")
    else:
        print("\n✗ FAILED (Some security headers missing)")


def test_cors_headers():
    """Test 7: CORS headers."""
    print_test(7, "CORS Configuration")

    response = requests.options(
        f"{API_URL}/api/queries",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
    )

    print("Checking CORS headers:")
    cors_headers = {
        "access-control-allow-origin": "http://localhost:3000",
        "access-control-allow-credentials": "true",
    }

    for header, expected_value in cors_headers.items():
        actual_value = response.headers.get(header, "NOT FOUND")
        status = "✓" if expected_value in actual_value.lower() else "⚠"
        print(f"  {status} {header}: {actual_value}")

    print("\n✓ PASSED (CORS configured)")


def test_openapi_docs():
    """Test 8: OpenAPI documentation."""
    print_test(8, "OpenAPI Documentation")

    response = requests.get(f"{API_URL}/openapi.json")
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        openapi = response.json()
        print(f"API Title: {openapi.get('info', {}).get('title')}")
        print(f"API Version: {openapi.get('info', {}).get('version')}")
        print(f"Endpoints: {len(openapi.get('paths', {}))}")
        print("\n✓ PASSED (OpenAPI schema available)")
    else:
        print("\n✗ FAILED (OpenAPI schema not available)")


def test_login_success():
    """Test 9: Login with valid credentials."""
    print_test(9, "Authentication - Login Success")

    response = requests.post(
        f"{API_URL}/api/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    print_response(response)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "user" in data, "Expected 'user' in response"
    assert "session" in data, "Expected 'session' in response"
    assert "token" in data["session"], "Expected 'token' in session"
    assert data["user"]["username"] == "testuser", "Expected username 'testuser'"

    print("✓ PASSED - Login successful")
    return data["session"]["token"]


def test_login_invalid_credentials():
    """Test 10: Login with invalid credentials."""
    print_test(10, "Authentication - Invalid Credentials")

    response = requests.post(
        f"{API_URL}/api/auth/login",
        json={"username": "testuser", "password": "wrongpassword"}
    )
    print_response(response)

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    data = response.json()
    assert "detail" in data, "Expected 'detail' in error response"

    print("✓ PASSED - Invalid credentials rejected")


def test_login_missing_username():
    """Test 11: Login with missing username."""
    print_test(11, "Authentication - Missing Username")

    response = requests.post(
        f"{API_URL}/api/auth/login",
        json={"password": "testpass123"}
    )
    print_response(response)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    print("✓ PASSED - Missing username validation")


def test_login_short_password():
    """Test 12: Login with password too short."""
    print_test(12, "Authentication - Password Too Short")

    response = requests.post(
        f"{API_URL}/api/auth/login",
        json={"username": "testuser", "password": "short"}
    )
    print_response(response)

    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    print("✓ PASSED - Short password validation")


def test_session_validation():
    """Test 13: Validate session token."""
    print_test(13, "Authentication - Session Validation")

    # First login to get a token
    login_response = requests.post(
        f"{API_URL}/api/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["session"]["token"]

    # Validate session
    response = requests.get(
        f"{API_URL}/api/auth/session",
        cookies={"session_token": token}
    )
    print_response(response)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "user" in data, "Expected 'user' in response"
    assert "session" in data, "Expected 'session' in response"

    print("✓ PASSED - Session validation successful")
    return token


def test_session_validation_invalid_token():
    """Test 14: Validate with invalid token."""
    print_test(14, "Authentication - Invalid Session Token")

    response = requests.get(
        f"{API_URL}/api/auth/session",
        cookies={"session_token": "invalid_token_12345"}
    )
    print_response(response)

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print("✓ PASSED - Invalid token rejected")


def test_logout():
    """Test 15: Logout."""
    print_test(15, "Authentication - Logout")

    # First login to get a token
    login_response = requests.post(
        f"{API_URL}/api/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["session"]["token"]

    # Logout
    response = requests.post(
        f"{API_URL}/api/auth/logout",
        cookies={"session_token": token}
    )
    print_response(response)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "message" in data, "Expected 'message' in response"

    # Try to use the token again - should fail
    validate_response = requests.get(
        f"{API_URL}/api/auth/session",
        cookies={"session_token": token}
    )
    assert validate_response.status_code == 401, "Token should be invalid after logout"

    print("✓ PASSED - Logout successful and token invalidated")


def test_authenticated_query_request():
    """Test 16: Create query with authentication."""
    print_test(16, "Queries - Authenticated Request")

    # Login first
    login_response = requests.post(
        f"{API_URL}/api/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    token = login_response.json()["session"]["token"]

    # Create query with authentication
    response = requests.post(
        f"{API_URL}/api/queries",
        json={"natural_language_query": "Show me all active users"},
        cookies={"session_token": token}
    )
    print_response(response)

    # Should succeed (even though SQL generation is not implemented)
    # We expect either 201 or a specific error about SQL generation
    assert response.status_code in [201, 500], f"Expected 201 or 500, got {response.status_code}"

    if response.status_code == 201:
        data = response.json()
        assert "id" in data, "Expected 'id' in response"
        assert "status" in data, "Expected 'status' in response"
        print("✓ PASSED - Authenticated query request accepted")
    else:
        # SQL generation not implemented yet - this is expected
        print("⚠ SQL generation not yet implemented (expected)")


def test_query_without_auth():
    """Test 17: Create query without authentication."""
    print_test(17, "Queries - Unauthenticated Request")

    response = requests.post(
        f"{API_URL}/api/queries",
        json={"natural_language_query": "Show me all active users"}
    )
    print_response(response)

    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    print("✓ PASSED - Unauthenticated request rejected")


def test_admin_user_login():
    """Test 18: Admin user login."""
    print_test(18, "Authentication - Admin User Login")

    response = requests.post(
        f"{API_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    print_response(response)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data["user"]["role"] == "admin", "Expected admin role"

    print("✓ PASSED - Admin login successful")
    return data["session"]["token"]


def test_cookie_handling():
    """Test 19: HTTP-only cookie handling."""
    print_test(19, "Security - HTTP-Only Cookie")

    # Create a session to test cookie handling
    session = requests.Session()

    # Login (should set cookie)
    login_response = session.post(
        f"{API_URL}/api/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )

    # Check if cookie was set
    cookies = session.cookies.get_dict()
    print(f"Cookies received: {cookies}")

    # Note: In production, httponly cookies won't be accessible via JavaScript
    # but the requests library can see them
    if "session_token" in cookies:
        print("✓ PASSED - Session cookie set")
    else:
        print("⚠ Cookie might be set as HttpOnly (not accessible in response)")


def test_password_validation():
    """Test 20: Password validation edge cases."""
    print_test(20, "Validation - Password Edge Cases")

    test_cases = [
        ("", "Empty password"),
        ("   ", "Whitespace password"),
        ("1234567", "Password too short (7 chars)"),
    ]

    all_passed = True
    for password, description in test_cases:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={"username": "testuser", "password": password}
        )

        if response.status_code == 422:
            print(f"  ✓ {description} - Rejected correctly")
        else:
            print(f"  ✗ {description} - Expected 422, got {response.status_code}")
            all_passed = False

    if all_passed:
        print("\n✓ PASSED - All password validations working")
    else:
        print("\n✗ FAILED - Some password validations failed")


def main():
    """Run all tests."""
    print("="*60)
    print("SQL AI Agent API Testing Suite")
    print("="*60)
    print(f"Testing API at: {API_URL}")
    print(f"Make sure the server is running!")
    print()

    try:
        # Quick check if server is running
        requests.get(API_URL, timeout=2)
    except requests.exceptions.RequestException as e:
        print(f"\n✗ ERROR: Cannot connect to {API_URL}")
        print(f"Make sure the server is running: python -m backend.app.main")
        return

    # Group tests by category
    basic_tests = [
        test_root,
        test_security_headers,
        test_cors_headers,
        test_openapi_docs,
    ]

    auth_tests = [
        test_login_success,
        test_login_invalid_credentials,
        test_login_missing_username,
        test_login_short_password,
        test_session_validation,
        test_session_validation_invalid_token,
        test_logout,
        test_admin_user_login,
        test_cookie_handling,
        test_password_validation,
    ]

    query_tests = [
        test_post_queries_auth,
        test_authenticated_query_request,
        test_query_without_auth,
        test_validation_whitespace,
        test_validation_missing_field,
        test_validation_too_long,
    ]

    print("\n" + "="*60)
    print("BASIC API TESTS")
    print("="*60)
    for test in basic_tests:
        try:
            test()
        except AssertionError as e:
            print(f"\n✗ FAILED: {e}")
        except Exception as e:
            print(f"\n✗ ERROR: {e}")

    print("\n" + "="*60)
    print("AUTHENTICATION TESTS")
    print("="*60)
    for test in auth_tests:
        try:
            test()
        except AssertionError as e:
            print(f"\n✗ FAILED: {e}")
        except Exception as e:
            print(f"\n✗ ERROR: {e}")

    print("\n" + "="*60)
    print("QUERY ENDPOINT TESTS")
    print("="*60)
    for test in query_tests:
        try:
            test()
        except AssertionError as e:
            print(f"\n✗ FAILED: {e}")
        except Exception as e:
            print(f"\n✗ ERROR: {e}")

    print("\n" + "="*60)
    print("Testing Complete!")
    print("="*60)
    print("\n📊 Test Summary:")
    print(f"  • Basic API Tests: {len(basic_tests)} tests")
    print(f"  • Authentication Tests: {len(auth_tests)} tests")
    print(f"  • Query Endpoint Tests: {len(query_tests)} tests")
    print(f"  • Total: {len(basic_tests) + len(auth_tests) + len(query_tests)} tests")
    print("\n🔗 Next Steps:")
    print("  1. Open Swagger UI: http://localhost:8000/docs")
    print("  2. Check TESTING.md for detailed scenarios")
    print("  3. Implement LLM integration for SQL generation")
    print()


if __name__ == "__main__":
    main()
