# DTO Summary - Complete Type System Overview

This document provides a comprehensive overview of all DTOs (Data Transfer Objects) and type definitions across the full stack.

## Quick Reference

| Category | Backend Files | Frontend Files | Count |
|----------|--------------|----------------|-------|
| Auth | `schemas/auth.py` | `types/api.ts` | 6 types |
| Queries | `schemas/queries.py` | `types/api.ts` | 10 types |
| Admin | `schemas/admin.py` | `types/api.ts` | 8 types |
| Common | `schemas/common.py` | `types/common.ts` | 5 types |
| Health | `schemas/health.py` | `types/api.ts` | 2 types |
| **Total** | **5 files** | **4 files** | **31+ types** |

## Complete DTO Inventory

### Authentication (6 DTOs)

| Name | Type | Purpose | Used In |
|------|------|---------|---------|
| `LoginRequest` | Request | Username + password | POST /auth/login |
| `LoginResponse` | Response | User + session info | POST /auth/login |
| `LogoutResponse` | Response | Success message | POST /auth/logout |
| `SessionResponse` | Response | Current session info | GET /auth/session |
| `UserResponse` | Response | User details (no password) | Multiple endpoints |
| `SessionInfo` | Nested | Session token + expiry | Login/session responses |

**Backend:** `backend/app/schemas/auth.py`
**Frontend:** `frontend/src/types/api.ts`, `frontend/src/types/models.ts`

### Query Workflow (10 DTOs)

| Name | Type | Purpose | Used In |
|------|------|---------|---------|
| `CreateQueryRequest` | Request | Natural language query input | POST /queries |
| `QueryAttemptResponse` | Response | Basic query attempt data | POST /queries |
| `QueryAttemptDetailResponse` | Response | Full query with execution details | GET /queries/{id} |
| `SimplifiedQueryAttempt` | Response | Minimal query info for lists | GET /queries |
| `QueryListResponse` | Response | Paginated query list | GET /queries |
| `ExecuteQueryResponse` | Response | Execution result + timing | POST /queries/{id}/execute |
| `QueryResultsResponse` | Response | Paginated result rows | GET /queries/{id}/results |
| `RerunQueryResponse` | Response | New query from historical | POST /queries/{id}/rerun |
| `QueryResults` | Nested | Columns + rows structure | Execute/results responses |
| `ExecuteQueryRequest` | Request | Empty (uses path param) | POST /queries/{id}/execute |

**Backend:** `backend/app/schemas/queries.py`
**Frontend:** `frontend/src/types/api.ts`, `frontend/src/types/models.ts`

### Admin Operations (8 DTOs)

| Name | Type | Purpose | Used In |
|------|------|---------|---------|
| `RefreshSchemaResponse` | Response | Schema reload confirmation | POST /admin/schema/refresh |
| `SchemaSnapshotInfo` | Nested | Schema snapshot details | Schema refresh response |
| `ReloadKBResponse` | Response | KB reload confirmation | POST /admin/kb/reload |
| `KBReloadStats` | Nested | KB reload statistics | KB reload response |
| `MetricsRequest` | Request | Weeks parameter | GET /admin/metrics |
| `MetricsResponse` | Response | Usage metrics data | GET /admin/metrics |
| `MetricRow` | Nested | Single metric row | Metrics response |
| `MetricsSummary` | Nested | Aggregated statistics | Metrics response |

**Backend:** `backend/app/schemas/admin.py`
**Frontend:** `frontend/src/types/api.ts`, `frontend/src/types/models.ts`

### Common/Shared (5 DTOs)

| Name | Type | Purpose | Used In |
|------|------|---------|---------|
| `PaginationParams` | Request | Page + page_size params | List endpoints |
| `PaginationMetadata` | Response | Pagination info | List responses |
| `ErrorResponse` | Response | Standard error format | All error responses |
| `QueryStatus` | Enum | Query state enum | Query responses |
| `UserRole` | Enum | User role enum | User responses |

**Backend:** `backend/app/schemas/common.py`
**Frontend:** `frontend/src/types/common.ts`

### System Health (2 DTOs)

| Name | Type | Purpose | Used In |
|------|------|---------|---------|
| `HealthCheckResponse` | Response | System health status | GET /health |
| `ServiceStatus` | Nested | Individual service statuses | Health response |

**Backend:** `backend/app/schemas/health.py`
**Frontend:** `frontend/src/types/api.ts`, `frontend/src/types/models.ts`

## Endpoint-to-DTO Mapping

### Authentication Endpoints

```
POST   /auth/login
  ├─ Request:  LoginRequest
  └─ Response: LoginResponse
       ├─ user: UserResponse
       └─ session: SessionInfo

POST   /auth/logout
  └─ Response: LogoutResponse

GET    /auth/session
  └─ Response: SessionResponse
       ├─ user: UserResponse
       └─ session: SessionInfoWithoutToken
```

### Query Endpoints

```
POST   /queries
  ├─ Request:  CreateQueryRequest
  └─ Response: QueryAttemptResponse

GET    /queries/{id}
  └─ Response: QueryAttemptDetailResponse

GET    /queries
  ├─ Query:    PaginationParams + status filter
  └─ Response: QueryListResponse
       ├─ queries: SimplifiedQueryAttempt[]
       └─ pagination: PaginationMetadata

POST   /queries/{id}/execute
  └─ Response: ExecuteQueryResponse
       └─ results?: QueryResults

GET    /queries/{id}/results
  ├─ Query:    page parameter
  └─ Response: QueryResultsResponse

POST   /queries/{id}/rerun
  └─ Response: RerunQueryResponse

GET    /queries/{id}/export
  └─ Response: CSV file (no DTO)
```

### Admin Endpoints

```
POST   /admin/schema/refresh
  └─ Response: RefreshSchemaResponse
       └─ snapshot: SchemaSnapshotInfo

POST   /admin/kb/reload
  └─ Response: ReloadKBResponse
       └─ stats: KBReloadStats

GET    /admin/metrics
  ├─ Query:    MetricsRequest (weeks param)
  └─ Response: MetricsResponse
       ├─ metrics: MetricRow[]
       └─ summary: MetricsSummary
```

### System Endpoints

```
GET    /health
  └─ Response: HealthCheckResponse
       └─ services: ServiceStatus
```

## Field-Level Details

### Common Field Types

| Field Name | Type | Validation | Description |
|------------|------|------------|-------------|
| `id` | `int` | Primary key | Database ID |
| `username` | `str` | 1-255 chars | Alphanumeric + underscore |
| `password` | `str` | 8-255 chars | Min 8 characters |
| `role` | `UserRole` | Enum | "admin" or "user" |
| `active` | `bool` | Boolean | Account active status |
| `status` | `QueryStatus` | Enum | Query attempt status |
| `*_at` fields | `str` | ISO 8601 | Timestamps |
| `*_ms` fields | `int` | Non-negative | Duration in milliseconds |
| `page` | `int` | >= 1 | Page number |
| `page_size` | `int` | 1-100 | Items per page |

### QueryStatus Enum Values

```typescript
"not_executed"      // SQL generated, not executed yet
"failed_generation" // Failed to generate SQL from NL query
"failed_execution"  // SQL execution failed (syntax/runtime error)
"success"           // Query executed successfully
"timeout"           // Query execution exceeded time limit
```

### UserRole Enum Values

```typescript
"admin"  // Full access including admin endpoints
"user"   // Standard user access
```

## Type Hierarchies

### User Types

```
UserResponse (base user info)
  ├─ Used in: LoginResponse, SessionResponse
  └─ Fields: id, username, role, active
```

### Query Types

```
QueryAttempt (base)
  ├─ Fields: id, natural_language_query, generated_sql, status,
  │          created_at, generated_at, generation_ms
  │
  ├─ QueryAttemptDetailResponse (extends QueryAttempt)
  │    └─ Additional: executed_at, execution_ms, original_attempt_id
  │
  ├─ SimplifiedQueryAttempt (subset)
  │    └─ Fields: id, natural_language_query, status, created_at, executed_at
  │
  └─ RerunQueryResponse (extends QueryAttempt)
       └─ Additional: original_attempt_id (required)
```

### Pagination Types

```
PaginationParams (request)
  └─ Fields: page?, page_size?

PaginationMetadata (response)
  └─ Fields: page, page_size, total_count, total_pages

PaginatedResponse<T> (generic wrapper)
  └─ Fields: items: T[], pagination: PaginationMetadata
```

## Validation Rules Summary

### String Validation

```python
# Username
- Length: 1-255 characters
- Pattern: Alphanumeric + underscore
- Custom: No whitespace-only

# Password
- Length: 8-255 characters minimum
- Custom: No whitespace-only

# Natural Language Query
- Length: 1-5000 characters
- Custom: No whitespace-only

# Generated SQL
- Custom: SELECT-only validation (server-side)
```

### Numeric Validation

```python
# Pagination
page: >= 1
page_size: 1-100

# Admin Metrics
weeks: 1-52

# Durations
*_ms fields: >= 0

# Rates (metrics)
success_rate: 0.0-1.0
acceptance_rate: 0.0-1.0
```

### Enum Validation

```python
# Automatically enforced by Pydantic/TypeScript
status: QueryStatus  # Only defined values accepted
role: UserRole       # Only "admin" or "user"
```

## Serialization Details

### Date/Time Handling

| Stage | Format | Example |
|-------|--------|---------|
| Database | ISO 8601 string | "2025-10-28T12:00:00Z" |
| Backend | `str` (no conversion) | "2025-10-28T12:00:00Z" |
| Frontend | `ISO8601Timestamp` (string) | "2025-10-28T12:00:00Z" |
| Display | Parse to Date then format | "Oct 28, 2025, 12:00 PM" |

**Utilities:**
- Backend: Store as strings, no datetime object needed
- Frontend: `parseISO8601()`, `getRelativeTime()`, `formatDuration()`

### Boolean Handling

| Stage | Format | Values |
|-------|--------|--------|
| Database | INTEGER | 0 (false), 1 (true) |
| Backend | `bool` | True, False |
| Frontend | `boolean` | true, false |

**Note:** Pydantic automatically converts DB integers to Python bools

### Null Handling

| Language | Syntax | Convention |
|----------|--------|------------|
| Python | `str \| None` or `Optional[str]` | Use `\| None` |
| TypeScript | `string \| null \| undefined` | Prefer `\| null` for API |
| JSON | `null` | Never use `undefined` in JSON |

### Array/List Types

| Python | TypeScript | Example |
|--------|------------|---------|
| `list[str]` | `Array<string>` or `string[]` | Column names |
| `list[list[Any]]` | `Array<Array<any>>` | Query result rows |
| `list[MetricRow]` | `Array<MetricRow>` | Metrics data |

## Code Examples

### Backend (Pydantic)

```python
from pydantic import BaseModel, Field, field_validator
from backend.app.schemas import QueryStatus

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

class QueryAttemptResponse(BaseModel):
    id: int
    natural_language_query: str
    generated_sql: str | None
    status: QueryStatus
    created_at: str
    generated_at: str | None
    generation_ms: int | None

    class Config:
        from_attributes = True
```

### Frontend (TypeScript)

```typescript
import type {
  CreateQueryRequest,
  QueryAttemptResponse,
  APIError,
} from "@/types";
import { isAPIError } from "@/types";

async function createQuery(
  request: CreateQueryRequest
): Promise<QueryAttemptResponse> {
  try {
    const response = await fetch("/api/queries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new APIError(
        response.status,
        error.detail,
        error.error_code
      );
    }

    return response.json();
  } catch (error) {
    if (isAPIError(error)) {
      console.error(`API Error: ${error.detail}`);
    }
    throw error;
  }
}
```

## Testing Strategy

### Backend Testing

```python
# Test Pydantic validation
def test_create_query_validation():
    # Valid request
    req = CreateQueryRequest(natural_language_query="Show users")
    assert req.natural_language_query == "Show users"

    # Invalid - too long
    with pytest.raises(ValidationError):
        CreateQueryRequest(natural_language_query="x" * 5001)

    # Invalid - whitespace only
    with pytest.raises(ValidationError):
        CreateQueryRequest(natural_language_query="   ")
```

### Frontend Testing

```typescript
// Type-level tests (compile time)
import { expectType } from "tsd";

const request: CreateQueryRequest = {
  natural_language_query: "Show all users"
};
expectType<CreateQueryRequest>(request);

// Runtime validation tests
import { isQueryStatus } from "@/types/utils";

describe("Type Guards", () => {
  it("validates QueryStatus", () => {
    expect(isQueryStatus("success")).toBe(true);
    expect(isQueryStatus("invalid")).toBe(false);
  });
});
```

### Integration Testing

```python
# Test full request/response cycle
def test_create_query_endpoint(client: TestClient):
    response = client.post(
        "/queries",
        json={"natural_language_query": "Show all users"}
    )

    assert response.status_code == 201
    data = response.json()

    # Validate response schema
    query = QueryAttemptResponse(**data)
    assert query.id > 0
    assert query.status in ["not_executed", "failed_generation"]
```

## Maintenance Checklist

When adding a new endpoint:

- [ ] Document in API plan (`.ai/api-plan.md`)
- [ ] Create Pydantic request model (if needed)
- [ ] Create Pydantic response model
- [ ] Add validation rules (Field, validators)
- [ ] Add to `backend/app/schemas/__init__.py`
- [ ] Create TypeScript request type (if needed)
- [ ] Create TypeScript response type
- [ ] Add to `frontend/src/types/index.ts`
- [ ] Add type guards (if using enums/unions)
- [ ] Write backend validation tests
- [ ] Write frontend type tests
- [ ] Write integration tests
- [ ] Update this documentation

## Related Files

### Documentation
- [DTOs and Types Guide](./dtos-and-types.md) - Detailed guide
- [Backend Schemas README](../backend/app/schemas/README.md) - Pydantic usage
- [Frontend Types README](../frontend/src/types/README.md) - TypeScript usage
- [API Plan](../.ai/api-plan.md) - Full API specification

### Source Code
- **Backend:** `backend/app/schemas/*.py`
- **Frontend:** `frontend/src/types/*.ts`

### Tools
- Type generation: `make generate-types`
- Backend validation: `mypy backend/`
- Frontend type check: `npm run type-check`

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-28 | Initial comprehensive DTO system |

---

**Last Updated:** 2025-10-28
**Maintained By:** Development Team
**Contact:** See project README for contact information
