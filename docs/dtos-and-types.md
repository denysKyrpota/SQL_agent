# DTOs and Type Definitions

This document describes the Data Transfer Objects (DTOs) and type definitions used throughout the application, covering both backend (Python/Pydantic) and frontend (TypeScript).

## Overview

The application uses a strongly-typed architecture where:
- **Backend**: Pydantic models provide validation and serialization for FastAPI endpoints
- **Frontend**: TypeScript types ensure type safety in React components and API calls
- **Synchronization**: Types are manually kept in sync based on the API plan

## Backend Structure (Python/Pydantic)

Located in `backend/app/schemas/`:

```
backend/app/schemas/
├── __init__.py       # Central exports
├── common.py         # Shared types (enums, pagination)
├── auth.py           # Authentication DTOs
├── queries.py        # Query workflow DTOs
├── admin.py          # Admin operation DTOs
└── health.py         # Health check DTOs
```

### Key Pydantic Features Used

1. **Field Validation**
   ```python
   from pydantic import BaseModel, Field

   class LoginRequest(BaseModel):
       username: str = Field(min_length=1, max_length=255)
       password: str = Field(min_length=8, max_length=255)
   ```

2. **Custom Validators**
   ```python
   from pydantic import field_validator

   @field_validator("username")
   @classmethod
   def validate_username(cls, v: str) -> str:
       if not v.strip():
           raise ValueError("Username cannot be only whitespace")
       return v.strip()
   ```

3. **ORM Mode**
   ```python
   class Config:
       from_attributes = True  # For SQLAlchemy model compatibility
   ```

4. **Enums**
   ```python
   from enum import Enum

   class QueryStatus(str, Enum):
       NOT_EXECUTED = "not_executed"
       FAILED_GENERATION = "failed_generation"
       # ...
   ```

## Frontend Structure (TypeScript)

Located in `frontend/src/types/`:

```
frontend/src/types/
├── index.ts          # Central exports
├── common.ts         # Shared types (enums, pagination)
├── models.ts         # Domain models
├── api.ts            # API request/response types
├── utils.ts          # Type guards and utilities
└── database.types.ts # Auto-generated DB schema types
```

### Key TypeScript Features Used

1. **Type Aliases and Unions**
   ```typescript
   export type QueryStatus =
     | "not_executed"
     | "failed_generation"
     | "failed_execution"
     | "success"
     | "timeout";
   ```

2. **Interface Extension**
   ```typescript
   export interface QueryAttemptDetail extends QueryAttempt {
       executed_at: ISO8601Timestamp | null;
       execution_ms: number | null;
   }
   ```

3. **Generic Types**
   ```typescript
   export interface PaginatedResponse<T> {
       items: T[];
       pagination: PaginationMetadata;
   }
   ```

4. **Type Guards**
   ```typescript
   export function isQueryStatus(value: unknown): value is QueryStatus {
       return typeof value === "string" &&
              ["not_executed", ...].includes(value);
   }
   ```

## DTO Categories

### 1. Authentication DTOs

**Backend:**
- `LoginRequest` - User credentials
- `LoginResponse` - User + session info
- `LogoutResponse` - Success message
- `SessionResponse` - Current session validation
- `UserResponse` - User info (excludes password_hash)
- `SessionInfo` - Session details

**Frontend:**
- Corresponding TypeScript types in `api.ts` and `models.ts`

### 2. Query Workflow DTOs

**Backend:**
- `CreateQueryRequest` - Natural language query input
- `QueryAttemptResponse` - Basic query attempt info
- `QueryAttemptDetailResponse` - Full query details with execution
- `SimplifiedQueryAttempt` - For list views
- `QueryListResponse` - Paginated query list
- `ExecuteQueryResponse` - Execution results
- `QueryResultsResponse` - Paginated result rows
- `RerunQueryResponse` - Re-run with original_attempt_id

**Frontend:**
- Corresponding types in `api.ts`
- Domain models in `models.ts`

### 3. Admin DTOs

**Backend:**
- `RefreshSchemaResponse` - Schema reload result
- `SchemaSnapshotInfo` - Schema snapshot details
- `ReloadKBResponse` - Knowledge base reload result
- `KBReloadStats` - KB reload statistics
- `MetricsRequest` - Metrics query params
- `MetricsResponse` - Usage metrics data
- `MetricRow` - Single metric row
- `MetricsSummary` - Aggregated metrics

**Frontend:**
- Corresponding types in `api.ts`

### 4. Common/Shared DTOs

**Backend:**
- `QueryStatus` - Enum for query states
- `UserRole` - Enum for user roles
- `PaginationParams` - Query params for pagination
- `PaginationMetadata` - Pagination response data
- `ErrorResponse` - Standard error format

**Frontend:**
- All shared types in `common.ts`

## Type Transformations

### Dates and Timestamps

- **Database**: Stored as ISO 8601 strings in SQLite
- **Backend**: Keep as `str` type for API responses (no datetime conversion needed)
- **Frontend**: `ISO8601Timestamp` type alias (string)
- **Utilities**: `parseISO8601()` and `toISO8601()` helpers in `utils.ts`

### Enums

- **Backend**: Python `Enum` classes (string-based)
  ```python
  class QueryStatus(str, Enum):
      SUCCESS = "success"
  ```
- **Frontend**: TypeScript union types
  ```typescript
  type QueryStatus = "success" | "failed" | ...
  ```

### Booleans

- **Database**: INTEGER (0/1) in SQLite
- **Backend**: `bool` in Pydantic models
- **Frontend**: `boolean` type
- **Note**: Pydantic automatically converts from DB integers to Python bools

### Nullable Fields

- **Backend**: `str | None` or `Optional[str]`
- **Frontend**: `string | null`
- **Convention**: Use `null` in JSON, not `undefined`

### Binary Data (Embeddings)

- **Database**: BLOB type
- **Backend**: `bytes` (not exposed in API)
- **Frontend**: Not present in API types

## Validation Rules

### Authentication

- Username: 1-255 chars, alphanumeric + underscore, no whitespace-only
- Password: 8-255 chars minimum, no whitespace-only

### Queries

- Natural language query: 1-5000 chars, no whitespace-only
- Generated SQL: Must be SELECT-only (validated server-side)
- Status: Must be one of the defined enum values

### Pagination

- Page: integer >= 1
- Page size: integer 1-100

### Admin

- Weeks parameter: integer 1-52

## Error Handling

### Backend Error Responses

All errors follow the `ErrorResponse` schema:
```python
{
    "detail": "Human-readable error message",
    "error_code": "MACHINE_READABLE_CODE"  # optional
}
```

### Frontend Error Handling

Use the `APIError` class and type guard:
```typescript
import { APIError, isAPIError } from "@/types";

try {
    await apiCall();
} catch (error) {
    if (isAPIError(error)) {
        console.error(error.detail, error.errorCode);
    }
}
```

## Best Practices

### Backend (Pydantic)

1. **Always use Field()** for constraints and documentation
2. **Add examples** in `Config.json_schema_extra` for API docs
3. **Use validators** for complex validation logic
4. **Enable from_attributes** when working with SQLAlchemy models
5. **Document with docstrings** on class and field level
6. **Keep validation DRY** - reuse validators across models

### Frontend (TypeScript)

1. **Import from index.ts** for convenience
2. **Use type guards** for runtime validation
3. **Prefer interfaces** over types for object shapes
4. **Use utility types** (Pick, Omit, Partial) to derive types
5. **Add JSDoc comments** for complex types
6. **Use branded types** for IDs if extra type safety needed

### Cross-Platform

1. **Keep naming consistent** - snake_case in JSON
2. **Document transformations** when types differ
3. **Test serialization** for complex nested types
4. **Version your APIs** if breaking changes are needed
5. **Validate on both sides** - frontend for UX, backend for security

## Type Generation

### Backend

Pydantic models are manually written and maintained in `backend/app/schemas/`.

### Frontend

TypeScript types are manually written based on the API plan. Database types are auto-generated:

```bash
make generate-types  # Generates frontend/src/types/database.types.ts
```

### Keeping Types in Sync

1. **API Plan is source of truth** - see `.ai/api-plan.md`
2. **Update backend first** - Pydantic models with validation
3. **Update frontend second** - TypeScript types matching backend
4. **Run type checks** - `mypy` for Python, `tsc` for TypeScript
5. **Integration tests** - Verify serialization works end-to-end

## Examples

### Creating a New DTO

**Step 1: Add to API Plan**
Document the endpoint and payload structure in `.ai/api-plan.md`

**Step 2: Create Pydantic Model**
```python
# backend/app/schemas/queries.py
class CreateQueryRequest(BaseModel):
    natural_language_query: str = Field(
        min_length=1,
        max_length=5000,
        description="Natural language query"
    )

    @field_validator("natural_language_query")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()
```

**Step 3: Create TypeScript Type**
```typescript
// frontend/src/types/api.ts
export interface CreateQueryRequest {
    /** Natural language query to convert to SQL */
    natural_language_query: string;
}
```

**Step 4: Export**
Add to `__init__.py` (backend) and `index.ts` (frontend)

**Step 5: Use in API**
```python
# Backend
@app.post("/queries", response_model=QueryAttemptResponse)
async def create_query(request: CreateQueryRequest):
    ...
```

```typescript
// Frontend
import { CreateQueryRequest, QueryAttemptResponse } from "@/types";

async function createQuery(
    request: CreateQueryRequest
): Promise<QueryAttemptResponse> {
    const response = await fetch("/api/queries", {
        method: "POST",
        body: JSON.stringify(request),
    });
    return response.json();
}
```

## Testing Types

### Backend

```python
# Test Pydantic validation
def test_login_request_validation():
    # Valid
    req = LoginRequest(username="user", password="password123")
    assert req.username == "user"

    # Invalid - too short password
    with pytest.raises(ValidationError):
        LoginRequest(username="user", password="short")
```

### Frontend

```typescript
// Type checking at compile time
const request: CreateQueryRequest = {
    natural_language_query: "Show all users"
};

// Runtime validation with type guards
if (isQueryStatus(response.status)) {
    // TypeScript knows response.status is QueryStatus
}
```

## Troubleshooting

### Issue: Type mismatch between backend and frontend

**Solution**: Check the API plan, update both backend and frontend to match the documented contract.

### Issue: Pydantic validation error in production

**Solution**: Add more specific validation rules and helpful error messages. Test with edge cases.

### Issue: TypeScript "any" types appearing

**Solution**: Add proper type definitions. Use type guards for runtime validation.

### Issue: Date parsing fails

**Solution**: Ensure backend always returns ISO 8601 format. Use `parseISO8601()` utility on frontend.

## References

- [Pydantic Documentation](https://docs.pydantic.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- API Plan: `.ai/api-plan.md`
