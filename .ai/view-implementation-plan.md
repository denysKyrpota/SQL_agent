# API Endpoint Implementation Plan: [Endpoint Name]

## Analysis Summary
This template provides a comprehensive guide for implementing REST API endpoints in the SQL AI Agent project. It incorporates the project's tech stack (FastAPI + React/TypeScript), existing patterns, and implementation rules.

---

## 1. Endpoint Overview

### Purpose
[Brief description of what this endpoint does and why it exists]

### Business Context
- **User Story**: As a [user type], I want to [action] so that [benefit]
- **Primary Use Case**: [Main scenario where this endpoint is used]
- **Related Endpoints**: [List any related endpoints that work together with this one]

### Key Characteristics
- **Idempotency**: [Yes/No - Can the same request be made multiple times safely?]
- **Side Effects**: [List any state changes or external actions triggered]
- **Performance Expectations**: [Expected response time, e.g., <200ms, <5s for query execution]
- **Rate Limiting**: [Applicable rate limits, e.g., 10 requests/minute per user]

---

## 2. Request Details

### HTTP Method
`[GET/POST/PUT/PATCH/DELETE]`

**Rationale**: [Why this HTTP method is appropriate]

### URL Structure
```
[METHOD] /api/[resource]/[{id}]/[sub-resource]
```

**Example**: `POST /api/queries/123/execute`

### Route Parameters
| Parameter | Type | Required | Validation Rules | Description |
|-----------|------|----------|------------------|-------------|
| `id` | `int` | Yes | Positive integer, exists in database | [Description] |
| `[param]` | `[type]` | [Yes/No] | [Rules] | [Description] |

### Query Parameters
| Parameter | Type | Required | Default | Validation Rules | Description |
|-----------|------|----------|---------|------------------|-------------|
| `page` | `int` | No | `1` | >= 1 | Page number for pagination |
| `page_size` | `int` | No | `20` | 1-100 | Items per page |
| `[param]` | `[type]` | [Yes/No] | `[default]` | [Rules] | [Description] |

### Request Headers
| Header | Required | Value | Purpose |
|--------|----------|-------|---------|
| `Cookie` | Yes* | `session_token=[token]` | Authentication (*except public endpoints) |
| `Content-Type` | Yes** | `application/json` | Request body format (**for POST/PUT/PATCH) |

### Request Body
**Content-Type**: `application/json`

**Schema** (Pydantic Model):
```python
class [RequestName]Request(BaseModel):
    field_name: str = Field(
        min_length=1,
        max_length=255,
        description="[Description]"
    )
    optional_field: int | None = Field(
        default=None,
        ge=0,
        description="[Description]"
    )

    @field_validator("field_name")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Cannot be empty or only whitespace")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "field_name": "example value",
                "optional_field": 42
            }
        }
```

**Example Request**:
```json
{
  "field_name": "example value",
  "optional_field": 42
}
```

### Request Validation Rules
1. **Field-level validations**:
   - `field_name`: 1-255 characters, non-empty after trimming
   - `optional_field`: Non-negative integer if provided

2. **Cross-field validations**:
   - [Any rules that depend on multiple fields]

3. **Business logic validations** (in service layer):
   - [Resource existence checks]
   - [Permission checks]
   - [State transition validations]

---

## 3. Used Types

### Backend DTOs (Pydantic)

#### Request DTOs
**Location**: `backend/app/schemas/[resource].py`

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from .common import [SharedEnums]

class [RequestName]Request(BaseModel):
    """Request model for [endpoint description]"""
    # Fields defined above
    pass
```

#### Response DTOs
**Location**: `backend/app/schemas/[resource].py`

```python
class [ResponseName]Response(BaseModel):
    """Response model for [endpoint description]"""
    id: int = Field(description="Unique identifier")
    field_name: str = Field(description="[Description]")
    status: [StatusEnum] = Field(description="Current status")
    created_at: str = Field(description="ISO 8601 timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 123,
                "field_name": "example",
                "status": "success",
                "created_at": "2025-01-15T10:30:00Z"
            }
        }
```

### Frontend Types (TypeScript)

#### Request/Response Interfaces
**Location**: `frontend/src/types/api.ts`

```typescript
// Request interface
export interface [RequestName]Request {
  fieldName: string;
  optionalField?: number;
}

// Response interface
export interface [ResponseName]Response {
  id: number;
  fieldName: string;
  status: QueryStatus;
  createdAt: ISO8601Timestamp;
}
```

#### Domain Models (if needed)
**Location**: `frontend/src/types/models.ts`

```typescript
export interface [DomainModel] {
  id: number;
  // Domain-specific fields
}
```

### Database Models (SQLAlchemy)

**Location**: `backend/app/models/[resource].py`

```python
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from .base import Base

class [ModelName](Base):
    __tablename__ = "[table_name]"

    id = Column(Integer, primary_key=True)
    field_name = Column(String(255), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(Text, nullable=False)  # ISO 8601

    # Relationships
    user = relationship("User", back_populates="[resources]")

    # Indexes
    __table_args__ = (
        Index("idx_[table]_user_created", "user_id", "created_at"),
    )
```

---

## 4. Response Details

### Success Response

#### Status Code: `[200/201]`
- **200 OK**: For successful GET, PUT, PATCH, DELETE operations
- **201 Created**: For successful POST operations that create a new resource

#### Response Headers
```
Content-Type: application/json
Set-Cookie: session_token=[token]; HttpOnly; Secure; SameSite=Strict (if auth endpoint)
```

#### Response Body Schema
```json
{
  "id": 123,
  "field_name": "example value",
  "status": "success",
  "created_at": "2025-01-15T10:30:00Z",
  "nested_data": {
    "count": 5,
    "items": []
  }
}
```

#### Response Field Descriptions
| Field | Type | Description | Format/Constraints |
|-------|------|-------------|-------------------|
| `id` | `integer` | Unique identifier | Positive integer |
| `field_name` | `string` | [Description] | [Constraints] |
| `status` | `string` | Current status | Enum: [values] |
| `created_at` | `string` | Creation timestamp | ISO 8601 format |

### Pagination Response (if applicable)

```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_count": 100,
    "total_pages": 5
  }
}
```

### Error Responses

#### 400 Bad Request
**When**: Invalid input data, validation failures

```json
{
  "detail": "Validation error message",
  "error_code": "VALIDATION_ERROR"
}
```

**Common Scenarios**:
- Required field missing
- Field value out of range
- Invalid format (e.g., not ISO 8601 for dates)

#### 401 Unauthorized
**When**: Missing or invalid session token

```json
{
  "detail": "Session token is missing or invalid",
  "error_code": "AUTH_SESSION_INVALID"
}
```

#### 403 Forbidden
**When**: User lacks required permissions

```json
{
  "detail": "Insufficient permissions to perform this action",
  "error_code": "PERMISSION_DENIED"
}
```

**Common Scenarios**:
- User role is 'user' but endpoint requires 'admin'
- User trying to access another user's resources

#### 404 Not Found
**When**: Resource doesn't exist

```json
{
  "detail": "[Resource] with ID [id] not found",
  "error_code": "[RESOURCE]_NOT_FOUND"
}
```

#### 422 Unprocessable Entity
**When**: Pydantic validation fails

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "field_name"],
      "msg": "Field cannot be empty or only whitespace",
      "input": "   "
    }
  ]
}
```

#### 429 Too Many Requests
**When**: Rate limit exceeded

```json
{
  "detail": "Rate limit exceeded. Try again in [X] seconds.",
  "error_code": "RATE_LIMIT_EXCEEDED"
}
```

#### 500 Internal Server Error
**When**: Unexpected server error

```json
{
  "detail": "An internal error occurred. Please try again later.",
  "error_code": "INTERNAL_ERROR"
}
```

**Note**: Sensitive error details are logged but not exposed to client

#### 503 Service Unavailable
**When**: External service (OpenAI, PostgreSQL) is unavailable

```json
{
  "detail": "[Service] is currently unavailable. Please try again later.",
  "error_code": "[SERVICE]_UNAVAILABLE"
}
```

---

## 5. Data Flow

### High-Level Flow
```
1. Client → FastAPI Router (Request validation)
2. Router → Authentication Middleware (Session validation)
3. Router → Route Handler (Extract params, call service)
4. Route Handler → Service Layer (Business logic)
5. Service → Database / External API (Data operations)
6. Service → Route Handler (Return result)
7. Route Handler → Client (JSON response)
```

### Detailed Step-by-Step Flow

#### Step 1: Request Reception
```python
@router.[method]("/[resource]/[{id}]")
async def [handler_name](
    [id]: int,
    request: [Request]Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> [Response]Response:
    """
    [Endpoint description]

    - **Authentication**: Required (user/admin)
    - **Rate Limit**: [X requests/minute]
    """
```

**Automatic Processing**:
- Pydantic validates request body against schema
- Dependency injection validates session token
- Rate limiting checks request count

#### Step 2: Authorization Check
```python
# Check resource ownership or admin privilege
if user.role != "admin" and resource.user_id != user.id:
    raise HTTPException(
        status_code=403,
        detail="Insufficient permissions",
    )
```

#### Step 3: Business Logic Execution
```python
# Call service layer
result = await [service].[method](
    db=db,
    user_id=user.id,
    [params]
)
```

**Service Layer** (`backend/app/services/[service].py`):
```python
class [Service]:
    async def [method](
        self,
        db: Session,
        user_id: int,
        [params]
    ) -> [ReturnType]:
        # 1. Validate business rules
        # 2. Check resource existence
        # 3. Perform operations (database, external APIs)
        # 4. Update status/state
        # 5. Log important events
        # 6. Return result or raise exception
```

#### Step 4: Database Operations

**Read Operation**:
```python
resource = db.query([Model])\
    .filter([Model].id == resource_id)\
    .first()

if not resource:
    raise HTTPException(404, detail="Resource not found")
```

**Write Operation**:
```python
new_resource = [Model](
    field_name=request.field_name,
    user_id=user.id,
    created_at=datetime.utcnow().isoformat()
)
db.add(new_resource)
db.commit()
db.refresh(new_resource)
```

**Transaction Handling**:
```python
try:
    # Multiple operations
    db.commit()
except Exception as e:
    db.rollback()
    logger.error(f"Transaction failed: {e}")
    raise HTTPException(500, detail="Operation failed")
```

#### Step 5: External Service Calls (if applicable)

**Example: OpenAI API**:
```python
try:
    response = await openai_client.create_completion(
        model="gpt-4",
        messages=[...],
        timeout=30.0
    )
except OpenAIError as e:
    logger.error(f"OpenAI API error: {e}")
    raise HTTPException(503, detail="AI service unavailable")
```

**Retry Logic** (for transient failures):
```python
for attempt in range(3):
    try:
        result = await external_service_call()
        break
    except TransientError:
        if attempt == 2:
            raise
        await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

#### Step 6: Response Construction
```python
return [Response]Response(
    id=result.id,
    field_name=result.field_name,
    status=result.status,
    created_at=result.created_at
)
```

**Automatic Processing**:
- Pydantic serializes response to JSON
- FastAPI adds appropriate headers
- Status code set based on return annotation

### Database Interactions

#### Tables Accessed
- **Read**: `[table_names]`
- **Write**: `[table_names]`
- **Join**: `[table_names if applicable]`

#### Indexes Used
- `idx_[table]_[columns]` - For efficient lookups
- `idx_[table]_[columns]` - For pagination queries

#### Query Performance
- **Expected Query Time**: [<10ms for simple queries, <100ms for complex joins]
- **Optimization Strategy**: [Index usage, query limits, pagination]

### External Service Interactions

#### [Service Name] (if applicable)
- **Purpose**: [Why this service is called]
- **Request Format**: [API request details]
- **Response Format**: [API response details]
- **Timeout**: [e.g., 30 seconds]
- **Retry Strategy**: [e.g., 3 attempts with exponential backoff]
- **Error Handling**: [How failures are handled]

---

## 6. Security Considerations

### Authentication

#### Session-Based Authentication
```python
async def get_current_user(
    session_token: str = Depends(get_session_token),
    db: Session = Depends(get_db)
) -> User:
    """Validate session token and return current user"""

    # Query session
    session = db.query(SessionModel)\
        .filter(SessionModel.token == session_token)\
        .first()

    # Validation checks
    if not session:
        raise HTTPException(401, detail="Invalid session token")

    if session.revoked:
        raise HTTPException(401, detail="Session has been revoked")

    if datetime.fromisoformat(session.expires_at) < datetime.utcnow():
        raise HTTPException(401, detail="Session has expired")

    # Get user
    user = db.query(User).filter(User.id == session.user_id).first()

    if not user or not user.active:
        raise HTTPException(401, detail="User account is inactive")

    return user
```

#### Cookie Security
```python
response.set_cookie(
    key="session_token",
    value=session.token,
    httponly=True,      # Prevent JavaScript access
    secure=True,        # HTTPS only
    samesite="strict",  # CSRF protection
    max_age=28800       # 8 hours
)
```

### Authorization

#### Role-Based Access Control
```python
def require_admin(user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return user
```

#### Resource Ownership Check
```python
def check_resource_ownership(
    resource_id: int,
    user: User,
    db: Session
) -> [Model]:
    """Verify user owns the resource or is admin"""
    resource = db.query([Model]).filter([Model].id == resource_id).first()

    if not resource:
        raise HTTPException(404, detail="Resource not found")

    if user.role != "admin" and resource.user_id != user.id:
        raise HTTPException(403, detail="Access denied")

    return resource
```

### Input Validation & Sanitization

#### SQL Injection Prevention
- **Use parameterized queries** via SQLAlchemy ORM
- **Never** construct SQL strings with user input
- **Validate** generated SQL is SELECT-only before PostgreSQL execution

```python
# GOOD: Parameterized query
db.query(User).filter(User.username == username).first()

# BAD: String concatenation (NEVER DO THIS)
# db.execute(f"SELECT * FROM users WHERE username = '{username}'")
```

#### Input Sanitization
```python
@field_validator("field_name")
@classmethod
def sanitize_field_name(cls, v: str) -> str:
    # Trim whitespace
    v = v.strip()

    # Validate not empty after trimming
    if not v:
        raise ValueError("Cannot be empty")

    # Additional sanitization (if needed)
    # - Remove control characters
    # - Normalize unicode
    # - Validate character set

    return v
```

#### Length Limits
- Prevent DoS attacks via large payloads
- Enforce at Pydantic schema level
- Database constraints as backup

```python
field_name: str = Field(min_length=1, max_length=255)
```

### Rate Limiting

#### Per-User Rate Limits
```python
# In middleware or dependency
rate_limiter = RateLimiter(
    key_func=lambda user: f"user:{user.id}",
    max_requests=10,
    window_seconds=60
)

if rate_limiter.is_exceeded(user):
    raise HTTPException(
        status_code=429,
        detail="Rate limit exceeded. Try again in 60 seconds."
    )
```

#### Per-IP Rate Limits (for auth endpoints)
```python
rate_limiter = RateLimiter(
    key_func=lambda request: request.client.host,
    max_requests=5,
    window_seconds=900  # 15 minutes
)
```

### Data Privacy

#### Sensitive Data Handling
- **Never log**: Passwords, session tokens, API keys
- **Mask in logs**: Email addresses (e.g., `u***@example.com`)
- **Exclude from responses**: Password hashes, internal IDs

```python
class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    # password_hash excluded

    class Config:
        from_attributes = True
```

#### Password Security
- **Hashing**: bcrypt with cost factor 12
- **Storage**: Store only hashed passwords
- **Validation**: Compare hashes, never plaintext

```python
from bcrypt import hashpw, checkpw, gensalt

# Hashing
password_hash = hashpw(password.encode("utf-8"), gensalt(rounds=12))

# Verification
is_valid = checkpw(password.encode("utf-8"), stored_hash)
```

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type"],
)
```

### Security Headers

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

---

## 7. Error Handling

### Error Categories

#### 1. Validation Errors (400, 422)
**Cause**: Invalid input data

**Handling Strategy**:
- Pydantic automatically returns 422 with detailed field errors
- Custom validators return 400 with business rule violations

**Example**:
```python
@field_validator("username")
@classmethod
def validate_username(cls, v: str) -> str:
    if not v.strip():
        raise ValueError("Username cannot be empty")
    if len(v) < 3:
        raise ValueError("Username must be at least 3 characters")
    return v
```

#### 2. Authentication Errors (401)
**Cause**: Missing, invalid, or expired session token

**Handling Strategy**:
```python
try:
    user = await get_current_user(session_token, db)
except HTTPException as e:
    # Log authentication failure
    logger.warning(f"Auth failed: {e.detail}")
    raise
```

**Client Action**: Redirect to login page

#### 3. Authorization Errors (403)
**Cause**: Insufficient permissions

**Handling Strategy**:
```python
if user.role != "admin":
    logger.warning(f"User {user.id} attempted admin action")
    raise HTTPException(
        status_code=403,
        detail="Admin privileges required",
        headers={"X-Error-Code": "PERMISSION_DENIED"}
    )
```

**Client Action**: Show "Access Denied" message

#### 4. Resource Not Found (404)
**Cause**: Requested resource doesn't exist

**Handling Strategy**:
```python
resource = db.query([Model]).filter([Model].id == resource_id).first()
if not resource:
    raise HTTPException(
        status_code=404,
        detail=f"[Resource] with ID {resource_id} not found"
    )
```

**Client Action**: Show "Not Found" message or redirect

#### 5. Business Logic Errors (400)
**Cause**: Operation violates business rules

**Examples**:
- Cannot delete resource that has dependencies
- Cannot transition from state A to state B
- Duplicate resource creation

**Handling Strategy**:
```python
if resource.status == "completed":
    raise HTTPException(
        status_code=400,
        detail="Cannot modify completed resource",
        headers={"X-Error-Code": "INVALID_STATE"}
    )
```

#### 6. External Service Errors (503)
**Cause**: OpenAI API, PostgreSQL, or other external service unavailable

**Handling Strategy**:
```python
try:
    result = await openai_client.call(...)
except OpenAIError as e:
    logger.error(f"OpenAI API error: {e}")
    raise HTTPException(
        status_code=503,
        detail="AI service temporarily unavailable",
        headers={"X-Error-Code": "LLM_SERVICE_UNAVAILABLE"}
    )
```

**Retry Strategy**: 3 attempts with exponential backoff

**Client Action**: Show retry option

#### 7. Database Errors (500)
**Cause**: Database constraint violations, connection errors

**Handling Strategy**:
```python
try:
    db.add(new_resource)
    db.commit()
except IntegrityError as e:
    db.rollback()
    logger.error(f"Database integrity error: {e}")
    raise HTTPException(
        status_code=400,
        detail="Duplicate resource or constraint violation"
    )
except Exception as e:
    db.rollback()
    logger.error(f"Database error: {e}")
    raise HTTPException(
        status_code=500,
        detail="An internal error occurred"
    )
```

#### 8. Timeout Errors (500/504)
**Cause**: Operation exceeds time limit

**Handling Strategy**:
```python
import asyncio

try:
    result = await asyncio.wait_for(
        long_running_operation(),
        timeout=300.0  # 5 minutes
    )
except asyncio.TimeoutError:
    logger.warning(f"Operation timed out for user {user.id}")
    raise HTTPException(
        status_code=500,
        detail="Operation timed out. Try with a smaller dataset.",
        headers={"X-Error-Code": "OPERATION_TIMEOUT"}
    )
```

### Error Response Structure

#### Standard Error Response
```python
class ErrorResponse(BaseModel):
    detail: str = Field(description="Human-readable error message")
    error_code: str | None = Field(
        default=None,
        description="Machine-readable error code"
    )
```

**Example**:
```json
{
  "detail": "Query attempt with ID 999 not found",
  "error_code": "QUERY_NOT_FOUND"
}
```

### Logging Strategy

#### Log Levels
- **DEBUG**: Detailed debug information (development only)
- **INFO**: Successful operations, state changes
- **WARNING**: Recoverable errors, auth failures
- **ERROR**: Unhandled exceptions, external service failures
- **CRITICAL**: System-wide failures

#### Structured Logging
```python
logger.info(
    "Resource created",
    extra={
        "user_id": user.id,
        "resource_id": resource.id,
        "endpoint": "/api/[resource]",
        "method": "POST",
        "duration_ms": 123
    }
)
```

#### What to Log
- ✅ Request method, endpoint, user ID
- ✅ Operation results (success/failure)
- ✅ Performance metrics (query time, API call duration)
- ✅ Business-critical events (resource creation, status changes)
- ✅ External API calls and responses (sanitized)
- ❌ Passwords, session tokens, API keys
- ❌ Full request/response bodies (unless debugging)

### Frontend Error Handling

#### API Client Error Handling
```typescript
async function apiCall<T>(
  url: string,
  options?: RequestInit
): Promise<T> {
  try {
    const response = await fetch(url, options);

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(
        response.status,
        error.detail,
        error.error_code
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      // Handle specific error codes
      if (error.status === 401) {
        // Redirect to login
        window.location.href = "/login";
      }
      throw error;
    }

    // Network error or other unexpected error
    throw new APIError(0, "Network error occurred");
  }
}
```

#### User-Facing Error Messages
```typescript
function getUserFriendlyMessage(error: APIError): string {
  switch (error.error_code) {
    case "AUTH_SESSION_EXPIRED":
      return "Your session has expired. Please log in again.";
    case "QUERY_NOT_FOUND":
      return "The requested query could not be found.";
    case "LLM_SERVICE_UNAVAILABLE":
      return "AI service is temporarily unavailable. Please try again.";
    default:
      return error.detail || "An unexpected error occurred.";
  }
}
```

---

## 8. Performance Considerations

### Database Performance

#### Query Optimization
1. **Use indexes** for frequently queried columns
   ```sql
   CREATE INDEX idx_[table]_[columns] ON [table]([column1], [column2]);
   ```

2. **Limit result sets** with pagination
   ```python
   query = query.offset((page - 1) * page_size).limit(page_size)
   ```

3. **Avoid N+1 queries** with eager loading
   ```python
   query = query.options(joinedload([Model].relationship))
   ```

4. **Use appropriate indexes** for sorting
   ```python
   # Index supports: ORDER BY created_at DESC
   query = query.order_by([Model].created_at.desc())
   ```

#### Connection Pooling
```python
# SQLAlchemy engine configuration
engine = create_engine(
    database_url,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_pre_ping=True  # Verify connections before use
)
```

### Caching Strategy

#### In-Memory Caching (where applicable)
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_schema_snapshot() -> dict:
    """Cache schema snapshot for 1 hour"""
    # Expensive operation
    return load_schema()
```

**Applicable for**:
- Schema snapshots (refresh every hour or on demand)
- Knowledge base examples (refresh on admin action)
- Static configuration data

**Not applicable for**:
- User-specific data
- Frequently changing data
- Large datasets

### API Call Optimization

#### Batch Operations (if applicable)
Instead of:
```python
# Multiple API calls
for item in items:
    await process_item(item)
```

Use:
```python
# Single batch call
await process_items_batch(items)
```

#### Async/Await for I/O
```python
async def endpoint_handler():
    # Concurrent I/O operations
    results = await asyncio.gather(
        fetch_from_db(),
        call_external_api(),
        read_file()
    )
```

### Response Size Optimization

#### Pagination
- Default page size: 20 items
- Max page size: 100 items
- Include pagination metadata for client navigation

#### Field Selection (if applicable)
```python
# Allow clients to request specific fields
?fields=id,name,created_at
```

#### Compression
```python
# Enable gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Monitoring & Metrics

#### Performance Metrics to Track
- **Request latency**: p50, p95, p99 response times
- **Error rate**: % of requests returning 5xx
- **Throughput**: Requests per second
- **Database query time**: Average and max query duration
- **External API latency**: OpenAI API response time

#### Performance Targets
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| API response time (simple) | <200ms | >1s |
| API response time (complex) | <2s | >10s |
| Database query time | <50ms | >500ms |
| Error rate | <1% | >5% |
| Uptime | >99.5% | <99% |

### Bottleneck Prevention

#### Common Bottlenecks
1. **Slow database queries**: Add indexes, optimize queries
2. **Large result sets**: Implement pagination, limit rows
3. **External API calls**: Add caching, implement circuit breakers
4. **Synchronous processing**: Use async/await for I/O
5. **Memory leaks**: Close connections, clear caches

#### Scalability Considerations
- **Horizontal scaling**: Stateless API servers
- **Database scaling**: Read replicas, connection pooling
- **Caching layer**: Redis for shared cache (future)
- **Background jobs**: Celery for long-running tasks (future)

---

## 9. Implementation Steps

### Step 1: Define Database Model (if new table needed)
**File**: `backend/app/models/[resource].py`

**Tasks**:
1. Create SQLAlchemy model class
2. Define columns with appropriate types and constraints
3. Add foreign key relationships
4. Create indexes for performance
5. Add `__repr__` method for debugging

**Verification**:
- [ ] Model matches database schema design
- [ ] Foreign keys reference correct tables
- [ ] Indexes cover common query patterns

**Example**:
```python
class [ModelName](Base):
    __tablename__ = "[table_name]"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    field_name = Column(String(255), nullable=False)
    created_at = Column(Text, nullable=False)

    user = relationship("User", back_populates="[resources]")

    __table_args__ = (
        Index("idx_[table]_user_created", "user_id", "created_at"),
    )
```

---

### Step 2: Create Database Migration (if schema change)
**File**: `migrations/[timestamp]_[description].sql`

**Tasks**:
1. Run `python scripts/create_migration.py [description]`
2. Write migration SQL (CREATE TABLE, ALTER TABLE, CREATE INDEX)
3. Test migration on development database
4. Document any data migrations needed

**Verification**:
- [ ] Migration runs without errors
- [ ] Indexes are created
- [ ] Foreign keys are enforced
- [ ] Migration is idempotent (safe to re-run)

**Example**:
```sql
-- Migration: Create [table_name] table
CREATE TABLE IF NOT EXISTS [table_name] (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_[table]_user_created
ON [table_name](user_id, created_at);
```

---

### Step 3: Define Pydantic Schemas
**File**: `backend/app/schemas/[resource].py`

**Tasks**:
1. Create request DTO with validation rules
2. Create response DTO with field descriptions
3. Add field validators for custom logic
4. Add JSON schema examples
5. Import shared types from `common.py`

**Verification**:
- [ ] All required fields are marked as required
- [ ] Optional fields have appropriate defaults
- [ ] Validators enforce business rules
- [ ] Examples are provided for documentation

**Example**:
```python
from pydantic import BaseModel, Field, field_validator
from .common import [SharedEnum]

class [Request]Request(BaseModel):
    field_name: str = Field(min_length=1, max_length=255)

    @field_validator("field_name")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Cannot be empty")
        return v.strip()

class [Response]Response(BaseModel):
    id: int
    field_name: str
    created_at: str

    class Config:
        from_attributes = True
```

---

### Step 4: Implement Service Layer
**File**: `backend/app/services/[service].py`

**Tasks**:
1. Create service class with methods for business logic
2. Implement CRUD operations
3. Add validation and error handling
4. Integrate external APIs (if needed)
5. Add logging for important events
6. Write unit tests for service methods

**Verification**:
- [ ] Service methods are async (for I/O operations)
- [ ] Errors are raised with appropriate messages
- [ ] Database transactions are handled correctly
- [ ] External API calls have retry logic
- [ ] Important events are logged

**Example**:
```python
class [Service]:
    async def create_[resource](
        self,
        db: Session,
        user_id: int,
        request: [Request]Request
    ) -> [Model]:
        # Validation
        # ...

        # Create resource
        resource = [Model](
            user_id=user_id,
            field_name=request.field_name,
            created_at=datetime.utcnow().isoformat()
        )

        db.add(resource)
        db.commit()
        db.refresh(resource)

        logger.info(f"Created [resource] {resource.id} for user {user_id}")

        return resource
```

---

### Step 5: Create Route Handler
**File**: `backend/app/api/[resource].py`

**Tasks**:
1. Create FastAPI router
2. Define route with HTTP method and path
3. Add dependency injection for auth and database
4. Call service layer methods
5. Handle exceptions and return appropriate status codes
6. Add OpenAPI documentation (docstrings)

**Verification**:
- [ ] Route path follows RESTful conventions
- [ ] Authentication is enforced (if required)
- [ ] Request/response types are annotated
- [ ] Docstring describes endpoint purpose
- [ ] Status codes are documented

**Example**:
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_current_user, get_db
from ..schemas.[resource] import [Request]Request, [Response]Response
from ..services.[service] import [Service]

router = APIRouter(prefix="/[resource]", tags=["[Resource]"])
service = [Service]()

@router.[method]("/[path]")
async def [handler_name](
    request: [Request]Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> [Response]Response:
    """
    [Endpoint description]

    - **Authentication**: Required
    - **Rate Limit**: [X requests/minute]
    """
    try:
        result = await service.[method](db, user.id, request)
        return [Response]Response.from_orm(result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in [handler]: {e}")
        raise HTTPException(status_code=500, detail="Internal error")
```

---

### Step 6: Register Route in Main App
**File**: `backend/app/main.py`

**Tasks**:
1. Import router from `api.[resource]`
2. Include router in FastAPI app with prefix
3. Verify route appears in OpenAPI docs

**Verification**:
- [ ] Route is accessible at `/api/[resource]/[path]`
- [ ] Route appears in Swagger UI at `/docs`
- [ ] Authentication middleware is applied

**Example**:
```python
from .api import [resource]

app.include_router(
    [resource].router,
    prefix="/api",
    tags=["[Resource]"]
)
```

---

### Step 7: Define TypeScript Types
**File**: `frontend/src/types/api.ts` and `models.ts`

**Tasks**:
1. Create request interface matching Pydantic request
2. Create response interface matching Pydantic response
3. Add to central export in `index.ts`
4. Run type generation if database types changed

**Verification**:
- [ ] TypeScript types match backend DTOs
- [ ] Field names are in camelCase (not snake_case)
- [ ] Optional fields use `?` or `| null` appropriately
- [ ] Enums are defined as union types

**Example**:
```typescript
// api.ts
export interface [Request]Request {
  fieldName: string;
  optionalField?: number;
}

export interface [Response]Response {
  id: number;
  fieldName: string;
  createdAt: ISO8601Timestamp;
}

// index.ts
export type { [Request]Request, [Response]Response } from './api';
```

---

### Step 8: Implement Frontend API Service
**File**: `frontend/src/services/[resource].service.ts`

**Tasks**:
1. Create service class or module
2. Implement API call function with fetch
3. Add error handling with APIError
4. Add request/response type annotations
5. Handle authentication (cookies sent automatically)

**Verification**:
- [ ] API calls use correct HTTP method and URL
- [ ] Request body is JSON-serialized
- [ ] Response is type-checked
- [ ] Errors are properly thrown as APIError
- [ ] Auth redirects on 401

**Example**:
```typescript
import { APIError } from '../types';
import type { [Request]Request, [Response]Response } from '../types';

export async function [method][Resource](
  request: [Request]Request
): Promise<[Response]Response> {
  const response = await fetch('/api/[resource]/[path]', {
    method: '[METHOD]',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include', // Send cookies
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new APIError(response.status, error.detail, error.error_code);
  }

  return await response.json();
}
```

---

### Step 9: Create React Component/Hook
**File**: `frontend/src/components/[Component].tsx` or `hooks/use[Resource].ts`

**Tasks**:
1. Create component or custom hook
2. Implement state management for loading/error states
3. Call API service function
4. Handle user interactions
5. Display errors user-friendly
6. Add loading indicators

**Verification**:
- [ ] Component handles loading state
- [ ] Errors are displayed to user
- [ ] Success feedback is provided
- [ ] Form validation (frontend)
- [ ] Accessibility (ARIA labels, keyboard navigation)

**Example (Custom Hook)**:
```typescript
import { useState } from 'react';
import { [method][Resource] } from '../services/[resource].service';
import { APIError } from '../types';

export function use[Resource]() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [methodName] = async (request: [Request]Request) => {
    setLoading(true);
    setError(null);

    try {
      const result = await [method][Resource](request);
      return result;
    } catch (err) {
      if (err instanceof APIError) {
        setError(getUserFriendlyMessage(err));
      } else {
        setError('An unexpected error occurred');
      }
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { [methodName], loading, error };
}
```

---

### Step 10: Write Tests

#### Backend Unit Tests
**File**: `backend/tests/test_[resource].py`

**Tasks**:
1. Create test fixtures for database and auth
2. Write tests for service layer methods
3. Write tests for route handlers
4. Test validation rules
5. Test error scenarios
6. Test authorization checks

**Verification**:
- [ ] All service methods have tests
- [ ] All routes have tests (success and error cases)
- [ ] Edge cases are covered
- [ ] Tests use mocks for external services
- [ ] Test coverage >80%

**Example**:
```python
import pytest
from fastapi.testclient import TestClient
from ..main import app
from ..models import User

client = TestClient(app)

def test_create_[resource]_success(auth_headers):
    response = client.post(
        "/api/[resource]",
        json={"field_name": "test"},
        headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["field_name"] == "test"

def test_create_[resource]_unauthorized():
    response = client.post("/api/[resource]", json={"field_name": "test"})
    assert response.status_code == 401
```

#### Frontend Unit Tests
**File**: `frontend/src/[component].test.tsx`

**Tasks**:
1. Write tests for custom hooks
2. Write tests for components
3. Test user interactions
4. Test error states
5. Mock API calls

**Verification**:
- [ ] Components render correctly
- [ ] User interactions work as expected
- [ ] Error states are displayed
- [ ] API calls are mocked
- [ ] Test coverage >70%

**Example**:
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { use[Resource] } from './use[Resource]';

test('should successfully call API', async () => {
  const { result } = renderHook(() => use[Resource]());

  await waitFor(() => result.current.[method]({ fieldName: 'test' }));

  expect(result.current.loading).toBe(false);
  expect(result.current.error).toBeNull();
});
```

---

### Step 11: Integration Testing

**Tasks**:
1. Test full request/response cycle
2. Test with real database (test DB)
3. Verify data persistence
4. Test pagination (if applicable)
5. Test rate limiting
6. Test with different user roles

**Verification**:
- [ ] End-to-end flow works correctly
- [ ] Data is correctly stored in database
- [ ] Authentication and authorization work
- [ ] Rate limiting is enforced
- [ ] Pagination returns correct results

---

### Step 12: Documentation

**Tasks**:
1. Update OpenAPI documentation (automatic from Pydantic)
2. Add code comments for complex logic
3. Update project README if needed
4. Document any manual testing steps
5. Document deployment considerations

**Verification**:
- [ ] Swagger UI shows endpoint with examples
- [ ] Complex logic has explanatory comments
- [ ] Error codes are documented
- [ ] Rate limits are documented

---

### Step 13: Manual Testing

**Test Cases**:

#### Happy Path
- [ ] Valid request returns expected response
- [ ] Data is persisted correctly
- [ ] Response format matches schema

#### Authentication
- [ ] Request without session token returns 401
- [ ] Expired session token returns 401
- [ ] Valid session token allows access

#### Authorization
- [ ] User cannot access other user's resources
- [ ] Admin can access all resources
- [ ] Correct 403 response for insufficient permissions

#### Validation
- [ ] Missing required field returns 400/422
- [ ] Invalid field value returns 400/422
- [ ] Field length limits are enforced
- [ ] Custom validators work correctly

#### Error Handling
- [ ] Database errors return 500 with generic message
- [ ] External API failures return 503
- [ ] Timeouts return appropriate error
- [ ] Error responses include error_code

#### Performance
- [ ] Response time meets targets
- [ ] Pagination works correctly
- [ ] Rate limiting enforces limits
- [ ] No N+1 query problems

#### Edge Cases
- [ ] Empty result sets handled correctly
- [ ] Maximum length inputs accepted
- [ ] Concurrent requests handled correctly
- [ ] Special characters in inputs handled

---

### Step 14: Code Review

**Review Checklist**:

#### Code Quality
- [ ] Code follows project style guide
- [ ] No hardcoded values (use config/env vars)
- [ ] Proper error handling throughout
- [ ] No code duplication
- [ ] Functions are single-purpose
- [ ] Variable names are descriptive

#### Security
- [ ] Input validation is thorough
- [ ] SQL injection prevention (parameterized queries)
- [ ] Authentication is enforced
- [ ] Authorization checks are correct
- [ ] Sensitive data not logged
- [ ] Rate limiting is implemented

#### Performance
- [ ] Database queries are optimized
- [ ] Indexes are used appropriately
- [ ] Pagination is implemented
- [ ] No unnecessary API calls
- [ ] Async/await used for I/O

#### Testing
- [ ] Unit tests cover main scenarios
- [ ] Error cases are tested
- [ ] Mocks are used appropriately
- [ ] Test coverage is adequate

---

### Step 15: Deployment Preparation

**Tasks**:
1. Run database migrations on staging
2. Test on staging environment
3. Update environment variables
4. Deploy backend changes
5. Deploy frontend changes
6. Monitor logs for errors

**Verification**:
- [ ] Migrations run successfully
- [ ] No errors in application logs
- [ ] Health check endpoint returns 200
- [ ] Smoke tests pass
- [ ] Rollback plan is ready

---

## 10. Additional Notes

### Related Endpoints
[List any endpoints that interact with or depend on this endpoint]

### Future Enhancements
[Potential improvements or features to add later]

### Known Limitations
[Any current limitations or constraints]

### References
- [Link to API specification in `.ai/api-plan.md`]
- [Link to database schema in `.ai/db_plan.md`]
- [Link to related documentation]

---

## Appendix: Quick Reference

### HTTP Status Codes
| Code | Name | Usage |
|------|------|-------|
| 200 | OK | Successful GET, PUT, PATCH, DELETE |
| 201 | Created | Successful POST creating resource |
| 400 | Bad Request | Validation error, business rule violation |
| 401 | Unauthorized | Missing/invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Pydantic validation failure |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | External service unavailable |

### Common Error Codes
| Code | Description |
|------|-------------|
| `AUTH_SESSION_INVALID` | Session token missing or invalid |
| `AUTH_SESSION_EXPIRED` | Session has expired |
| `PERMISSION_DENIED` | Insufficient role/permissions |
| `[RESOURCE]_NOT_FOUND` | Resource with ID not found |
| `VALIDATION_ERROR` | Input validation failed |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `LLM_SERVICE_UNAVAILABLE` | OpenAI API unavailable |
| `DATABASE_ERROR` | Database operation failed |
| `OPERATION_TIMEOUT` | Operation exceeded time limit |

### Validation Patterns
| Field Type | Validation |
|------------|------------|
| Username | 1-255 chars, alphanumeric + underscore |
| Password | 8-255 chars minimum |
| Email | Valid email format |
| Query text | 1-5000 chars, non-whitespace |
| Pagination | page >= 1, page_size 1-100 |
| Enum | Value in allowed set |
| Date | ISO 8601 format |

### Rate Limits
| Endpoint Type | Limit |
|---------------|-------|
| Query submission | 10 requests/minute per user |
| Login attempts | 5 attempts/15 minutes per IP |
| General API | 100 requests/minute per user |
| Admin endpoints | 20 requests/minute per admin |

---

**Template Version**: 1.0
**Last Updated**: 2025-01-15
**Maintainer**: Development Team
