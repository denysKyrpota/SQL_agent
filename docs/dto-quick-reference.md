# DTO Quick Reference Card

A cheat sheet for working with DTOs in this application.

## Import Statements

### Backend (Python)

```python
# Import from package level
from backend.app.schemas import (
    # Auth
    LoginRequest, LoginResponse, SessionResponse, UserResponse,
    # Queries
    CreateQueryRequest, QueryAttemptResponse, ExecuteQueryResponse,
    # Admin
    MetricsResponse, RefreshSchemaResponse,
    # Common
    ErrorResponse, PaginationParams, QueryStatus, UserRole,
)
```

### Frontend (TypeScript)

```typescript
// Import from types package
import type {
  // Auth
  LoginRequest, LoginResponse, SessionResponse, User,
  // Queries
  CreateQueryRequest, QueryAttemptResponse, ExecuteQueryResponse,
  // Admin
  MetricsResponse, RefreshSchemaResponse,
  // Common
  ErrorResponse, PaginationParams, QueryStatus, UserRole,
  // Utilities
  ISO8601Timestamp,
} from "@/types";

// Import utilities
import { isQueryStatus, parseISO8601, formatDuration } from "@/types/utils";
```

## Common Patterns

### Backend: Define Endpoint

```python
from fastapi import APIRouter
from backend.app.schemas import CreateQueryRequest, QueryAttemptResponse

router = APIRouter()

@router.post("/queries", response_model=QueryAttemptResponse, status_code=201)
async def create_query(request: CreateQueryRequest):
    # Request automatically validated
    return QueryAttemptResponse(...)
```

### Frontend: API Call

```typescript
import type { CreateQueryRequest, QueryAttemptResponse } from "@/types";

async function createQuery(
  queryText: string
): Promise<QueryAttemptResponse> {
  const response = await fetch("/api/queries", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ natural_language_query: queryText }),
  });
  return response.json();
}
```

### Backend: Custom Validator

```python
from pydantic import BaseModel, field_validator

class MyRequest(BaseModel):
    field: str

    @field_validator("field")
    @classmethod
    def validate_field(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()
```

### Frontend: Type Guard

```typescript
import { isQueryStatus } from "@/types/utils";

const value: unknown = data.status;
if (isQueryStatus(value)) {
  // TypeScript now knows value is QueryStatus
  console.log(value); // "success" | "failed_generation" | ...
}
```

## Validation Cheat Sheet

| Field | Backend | Frontend | Rules |
|-------|---------|----------|-------|
| username | `str = Field(min_length=1, max_length=255)` | `string` | 1-255 chars, no whitespace-only |
| password | `str = Field(min_length=8)` | `string` | Min 8 chars |
| natural_language_query | `str = Field(min_length=1, max_length=5000)` | `string` | 1-5000 chars |
| page | `int = Field(ge=1)` | `number` | >= 1 |
| page_size | `int = Field(ge=1, le=100)` | `number` | 1-100 |
| status | `QueryStatus` (Enum) | `QueryStatus` (Union) | 5 defined values |
| role | `UserRole` (Enum) | `UserRole` (Union) | "admin" \| "user" |

## Enum Values

### QueryStatus

```python
# Backend
class QueryStatus(str, Enum):
    NOT_EXECUTED = "not_executed"
    FAILED_GENERATION = "failed_generation"
    FAILED_EXECUTION = "failed_execution"
    SUCCESS = "success"
    TIMEOUT = "timeout"
```

```typescript
// Frontend
type QueryStatus =
  | "not_executed"
  | "failed_generation"
  | "failed_execution"
  | "success"
  | "timeout";
```

### UserRole

```python
# Backend
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
```

```typescript
// Frontend
type UserRole = "admin" | "user";
```

## Type Conversions

| Database | Python | TypeScript | Notes |
|----------|--------|------------|-------|
| `TEXT` (ISO 8601) | `str` | `ISO8601Timestamp` (string) | No conversion needed |
| `INTEGER` (0/1) | `bool` | `boolean` | Pydantic auto-converts |
| `INTEGER` | `int` | `number` | Direct mapping |
| `TEXT` | `str` | `string` | Direct mapping |
| `BLOB` | `bytes` | N/A | Not exposed in API |
| `NULL` | `None` | `null` | Use `field \| None` |

## Utility Functions

### Backend Helpers

```python
from pydantic import Field, field_validator

# Field with constraints
field: str = Field(min_length=1, max_length=255, description="...")

# Custom validator
@field_validator("field")
@classmethod
def validate_field(cls, v: str) -> str:
    # validation logic
    return v

# ORM compatibility
class Config:
    from_attributes = True
```

### Frontend Helpers

```typescript
import { parseISO8601, formatDuration, getRelativeTime } from "@/types/utils";

// Parse ISO timestamp
const date = parseISO8601("2025-10-28T12:00:00Z");

// Format duration
formatDuration(2150); // "2.2s"

// Relative time
getRelativeTime("2025-10-28T12:00:00Z"); // "2 hours ago"
```

## Error Handling

### Backend

```python
from fastapi import HTTPException
from backend.app.schemas import ErrorResponse

# Return error
raise HTTPException(
    status_code=400,
    detail="Query already executed"
)

# With error code
raise HTTPException(
    status_code=400,
    detail="Invalid request",
    headers={"X-Error-Code": "INVALID_REQUEST"}
)
```

### Frontend

```typescript
import { APIError, isAPIError } from "@/types";

try {
  const response = await fetch("/api/endpoint");
  if (!response.ok) {
    const error = await response.json();
    throw new APIError(response.status, error.detail, error.error_code);
  }
  return response.json();
} catch (error) {
  if (isAPIError(error)) {
    console.error(`Error ${error.status}: ${error.detail}`);
  }
}
```

## Pagination Pattern

### Backend

```python
from backend.app.schemas import PaginationParams, PaginationMetadata, QueryListResponse

@router.get("/queries", response_model=QueryListResponse)
async def list_queries(pagination: PaginationParams):
    queries = db.query(...).limit(pagination.page_size).offset(
        (pagination.page - 1) * pagination.page_size
    ).all()

    total_count = db.query(...).count()

    return QueryListResponse(
        queries=[...],
        pagination=PaginationMetadata(
            page=pagination.page,
            page_size=pagination.page_size,
            total_count=total_count,
            total_pages=(total_count + pagination.page_size - 1) // pagination.page_size
        )
    )
```

### Frontend

```typescript
import type { QueryListResponse, PaginationParams } from "@/types";

async function fetchQueries(
  params: PaginationParams
): Promise<QueryListResponse> {
  const query = new URLSearchParams({
    page: params.page?.toString() || "1",
    page_size: params.page_size?.toString() || "20",
  });

  const response = await fetch(`/api/queries?${query}`);
  return response.json();
}
```

## Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Pydantic validation error | Check field constraints with `Field()` |
| TypeScript "any" type | Add proper type annotation |
| Date parsing fails | Ensure ISO 8601 format, use `parseISO8601()` |
| Type mismatch | Verify backend and frontend types match API plan |
| Enum not accepted | Check exact string values match between backend/frontend |
| Null handling error | Use `field \| None` (Python) or `field \| null` (TypeScript) |

## File Locations

### Backend

```
backend/app/schemas/
├── __init__.py       # Import from here
├── common.py         # Shared types
├── auth.py           # Auth DTOs
├── queries.py        # Query DTOs
├── admin.py          # Admin DTOs
└── health.py         # Health DTOs
```

### Frontend

```
frontend/src/types/
├── index.ts          # Import from here
├── common.ts         # Shared types
├── models.ts         # Domain models
├── api.ts            # API types
└── utils.ts          # Utilities
```

## Testing Templates

### Backend Test

```python
import pytest
from pydantic import ValidationError
from backend.app.schemas import CreateQueryRequest

def test_valid_request():
    req = CreateQueryRequest(natural_language_query="Show users")
    assert req.natural_language_query == "Show users"

def test_invalid_request():
    with pytest.raises(ValidationError):
        CreateQueryRequest(natural_language_query="")
```

### Frontend Test

```typescript
import { describe, it, expect } from "vitest";
import { isQueryStatus } from "@/types/utils";

describe("Type Guards", () => {
  it("validates QueryStatus", () => {
    expect(isQueryStatus("success")).toBe(true);
    expect(isQueryStatus("invalid")).toBe(false);
  });
});
```

## Documentation Links

- [Full DTO Guide](./dtos-and-types.md)
- [Complete Reference](./dto-summary.md)
- [Visual Diagrams](./dto-diagrams.md)
- [Backend README](../backend/app/schemas/README.md)
- [Frontend README](../frontend/src/types/README.md)

---

**Quick Tip:** When in doubt, check the API plan at `.ai/api-plan.md` for the source of truth.
