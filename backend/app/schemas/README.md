# Backend Schemas (Pydantic DTOs)

This directory contains all Pydantic models used for request/response validation in the FastAPI application.

## Structure

- **`__init__.py`** - Central export point for all schemas
- **`common.py`** - Shared types, enums, and base models
- **`auth.py`** - Authentication and session management DTOs
- **`queries.py`** - Query workflow DTOs (create, execute, results)
- **`admin.py`** - Administrative operation DTOs
- **`health.py`** - System health check DTOs

## Usage

### Importing Schemas

Always import from the package level for consistency:

```python
from backend.app.schemas import (
    LoginRequest,
    LoginResponse,
    CreateQueryRequest,
    QueryAttemptResponse,
)
```

### Using in FastAPI Endpoints

```python
from fastapi import FastAPI
from backend.app.schemas import CreateQueryRequest, QueryAttemptResponse

app = FastAPI()

@app.post("/queries", response_model=QueryAttemptResponse)
async def create_query(request: CreateQueryRequest):
    # Pydantic automatically validates the request body
    # Access validated data via request.natural_language_query
    ...
    return QueryAttemptResponse(...)
```

### Manual Validation

```python
from pydantic import ValidationError
from backend.app.schemas import LoginRequest

try:
    request = LoginRequest(username="user", password="pass123")
except ValidationError as e:
    print(e.json())  # Get detailed validation errors
```

### Converting from ORM Models

For schemas with `from_attributes = True`:

```python
from backend.app.schemas import UserResponse
from backend.app.models import User  # SQLAlchemy model

user = db.query(User).first()
user_response = UserResponse.from_orm(user)
# or
user_response = UserResponse.model_validate(user)
```

## Validation Features

### Field Constraints

All schemas use `Field()` for validation:

```python
username: str = Field(min_length=1, max_length=255)
page: int = Field(ge=1, description="Page number")
weeks: int = Field(default=4, ge=1, le=52)
```

### Custom Validators

Many schemas have custom validators for business logic:

```python
@field_validator("natural_language_query")
@classmethod
def validate_not_empty(cls, v: str) -> str:
    if not v.strip():
        raise ValueError("Query cannot be empty")
    return v.strip()
```

### Enum Validation

Enums ensure only valid values are accepted:

```python
status: QueryStatus  # Only accepts defined enum values
role: UserRole  # Only "admin" or "user"
```

## Schema Categories

### Request Schemas (Input)

These validate incoming data from clients:

- `LoginRequest`
- `CreateQueryRequest`
- `PaginationParams`
- `MetricsRequest`

Key features:
- Strict validation rules
- Custom validators for business logic
- Clear error messages

### Response Schemas (Output)

These define the structure of API responses:

- `LoginResponse`
- `QueryAttemptResponse`
- `QueryListResponse`
- `MetricsResponse`

Key features:
- `from_attributes = True` for ORM compatibility
- Nested models for complex structures
- Examples in `json_schema_extra`

### Common Schemas (Shared)

Reusable across multiple endpoints:

- `PaginationMetadata`
- `ErrorResponse`
- `UserResponse`
- `SessionInfo`

## Testing Schemas

### Unit Tests

```python
import pytest
from pydantic import ValidationError
from backend.app.schemas import CreateQueryRequest

def test_create_query_valid():
    request = CreateQueryRequest(
        natural_language_query="Show all users"
    )
    assert request.natural_language_query == "Show all users"

def test_create_query_too_long():
    with pytest.raises(ValidationError) as exc_info:
        CreateQueryRequest(natural_language_query="x" * 5001)

    errors = exc_info.value.errors()
    assert any(e["type"] == "string_too_long" for e in errors)

def test_create_query_empty():
    with pytest.raises(ValidationError) as exc_info:
        CreateQueryRequest(natural_language_query="   ")

    errors = exc_info.value.errors()
    assert "cannot be empty" in str(errors)
```

### Integration Tests

```python
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_create_query_endpoint():
    response = client.post(
        "/queries",
        json={"natural_language_query": "Show all users"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] in ["not_executed", "failed_generation"]
```

## Best Practices

### 1. Always Use Field() for Documentation

```python
# Good
username: str = Field(min_length=1, description="Username")

# Bad
username: str
```

### 2. Add Examples for API Documentation

```python
class Config:
    json_schema_extra = {
        "example": {
            "username": "john_doe",
            "password": "SecurePass123"
        }
    }
```

### 3. Use Descriptive Validator Error Messages

```python
@field_validator("username")
@classmethod
def validate_username(cls, v: str) -> str:
    if not v.strip():
        raise ValueError("Username cannot be empty or only whitespace")
    return v.strip()
```

### 4. Keep Response Models Flat When Possible

```python
# Prefer this
class QueryAttemptResponse(BaseModel):
    id: int
    status: QueryStatus
    # ... more fields

# Over deeply nested structures
class QueryAttemptResponse(BaseModel):
    query: QueryInfo
    execution: ExecutionInfo
    # ... unless there's a good reason
```

### 5. Reuse Common Schemas

Don't duplicate definitions. Use inheritance or composition:

```python
# Base model
class QueryAttemptResponse(BaseModel):
    id: int
    natural_language_query: str
    # ... common fields

# Extended model
class QueryAttemptDetailResponse(QueryAttemptResponse):
    executed_at: str | None
    execution_ms: int | None
    # ... additional fields
```

## Type Annotations

We use modern Python type annotations (3.10+):

```python
# Use | for unions (not Union[])
field: str | None

# Use list[] (not List[])
fields: list[str]

# Use dict[] (not Dict[])
mapping: dict[str, int]
```

## OpenAPI Schema Generation

FastAPI automatically generates OpenAPI schemas from these Pydantic models. To customize:

```python
class MyModel(BaseModel):
    field: str = Field(
        description="Field description",
        examples=["example1", "example2"],
        json_schema_extra={"format": "email"}
    )
```

## Troubleshooting

### Issue: "Field required" error

**Cause**: Missing required field in request
**Solution**: Provide the field or make it optional with `field: str | None = None`

### Issue: Validation error not descriptive enough

**Cause**: Using default Pydantic validation
**Solution**: Add custom `@field_validator` with clear error message

### Issue: ORM model not converting properly

**Cause**: Missing `from_attributes = True`
**Solution**: Add to `Config` class in schema

### Issue: Enum value not accepted

**Cause**: String value doesn't match enum value
**Solution**: Ensure enum values are lowercase and match API spec

## Related Documentation

- [API Plan](.ai/api-plan.md) - Full API specification
- [DTOs and Types](docs/dtos-and-types.md) - Cross-platform type guide
- [Frontend Types](frontend/src/types/) - TypeScript type definitions
- [Pydantic Docs](https://docs.pydantic.dev/) - Official Pydantic documentation
