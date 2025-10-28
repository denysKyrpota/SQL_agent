# DTO Architecture Diagrams

Visual representations of the DTO structure and data flow.

## Table of Contents
1. [System Overview](#system-overview)
2. [Authentication Flow](#authentication-flow)
3. [Query Workflow](#query-workflow)
4. [Type Hierarchy](#type-hierarchy)
5. [Validation Pipeline](#validation-pipeline)

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              TypeScript Types                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │  common.ts  │  │  models.ts  │  │   api.ts    │      │  │
│  │  │  (Enums,    │  │  (Domain    │  │  (Request/  │      │  │
│  │  │   Shared)   │  │   Models)   │  │  Response)  │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  │         ▲                ▲                ▲               │  │
│  └─────────┼────────────────┼────────────────┼───────────────┘  │
│            │                │                │                  │
└────────────┼────────────────┼────────────────┼──────────────────┘
             │                │                │
             │         JSON over HTTP/REST     │
             │                │                │
┌────────────┼────────────────┼────────────────┼──────────────────┐
│            ▼                ▼                ▼                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Pydantic Schemas                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │  │
│  │  │  common.py  │  │  queries.py │  │   auth.py   │      │  │
│  │  │  (Enums,    │  │  (Query     │  │  (Auth      │      │  │
│  │  │   Shared)   │  │   DTOs)     │  │   DTOs)     │      │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘      │  │
│  │         ▲                ▲                ▲               │  │
│  └─────────┼────────────────┼────────────────┼───────────────┘  │
│            │                │                │                  │
│            │      Validation & Serialization │                  │
│            │                │                │                  │
│  ┌─────────▼────────────────▼────────────────▼───────────────┐  │
│  │              FastAPI Endpoints                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                         Backend (Python)                        │
└─────────────────────────────────────────────────────────────────┘
             │                │                │
             ▼                ▼                ▼
        ┌─────────┐     ┌──────────┐    ┌──────────┐
        │ SQLite  │     │PostgreSQL│    │ OpenAI   │
        │   DB    │     │    DB    │    │   API    │
        └─────────┘     └──────────┘    └──────────┘
```

## Authentication Flow

```
┌──────────────┐                                    ┌──────────────┐
│   Frontend   │                                    │   Backend    │
│  Component   │                                    │   FastAPI    │
└──────┬───────┘                                    └──────┬───────┘
       │                                                   │
       │ 1. User enters credentials                       │
       │                                                   │
       │ 2. Create LoginRequest                           │
       │    ┌────────────────────────┐                    │
       │    │ {                      │                    │
       │    │   username: "john",    │                    │
       │    │   password: "pass123"  │                    │
       │    │ }                      │                    │
       │    └────────────────────────┘                    │
       │                                                   │
       │ POST /auth/login                                 │
       ├──────────────────────────────────────────────────>│
       │                                                   │
       │                              3. Validate with    │
       │                                 Pydantic         │
       │                                 LoginRequest     │
       │                                                   │
       │                              4. Check DB         │
       │                                 (users table)    │
       │                                                   │
       │                              5. Create session   │
       │                                 (sessions table) │
       │                                                   │
       │                              6. Build Response   │
       │                                 LoginResponse    │
       │                                 ├─ UserResponse  │
       │                                 └─ SessionInfo   │
       │                                                   │
       │ 200 OK + LoginResponse                           │
       │<──────────────────────────────────────────────────┤
       │    ┌────────────────────────────────────┐        │
       │    │ {                                  │        │
       │    │   user: {                          │        │
       │    │     id: 1,                         │        │
       │    │     username: "john",              │        │
       │    │     role: "user",                  │        │
       │    │     active: true                   │        │
       │    │   },                               │        │
       │    │   session: {                       │        │
       │    │     token: "a1b2c3...",            │        │
       │    │     expires_at: "2025-10-28..."    │        │
       │    │   }                                │        │
       │    │ }                                  │        │
       │    └────────────────────────────────────┘        │
       │                                                   │
       │ 7. Store session in state/context                │
       │                                                   │
```

## Query Workflow

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Complete Query Lifecycle                     │
└──────────────────────────────────────────────────────────────────────┘

Step 1: CREATE QUERY
┌──────────┐
│ Frontend │  CreateQueryRequest
└────┬─────┘  { natural_language_query: "Show all users" }
     │
     │ POST /queries
     ▼
┌──────────┐
│ Backend  │  Validate → Generate SQL → Store
└────┬─────┘
     │
     │ QueryAttemptResponse
     │ { id: 42, status: "not_executed", generated_sql: "SELECT...", ... }
     ▼
┌──────────┐
│ Frontend │  Display query with "Execute" button
└──────────┘


Step 2: EXECUTE QUERY
┌──────────┐
│ Frontend │  POST /queries/42/execute
└────┬─────┘
     │
     ▼
┌──────────┐
│ Backend  │  Validate SQL → Execute on PostgreSQL → Store results
└────┬─────┘
     │
     │ ExecuteQueryResponse
     │ { id: 42, status: "success", execution_ms: 342,
     │   results: { columns: [...], rows: [...], total_rows: 150 } }
     ▼
┌──────────┐
│ Frontend │  Display results table
└──────────┘


Step 3: VIEW PAGINATED RESULTS
┌──────────┐
│ Frontend │  GET /queries/42/results?page=2
└────┬─────┘
     │
     ▼
┌──────────┐
│ Backend  │  Fetch page from PostgreSQL
└────┬─────┘
     │
     │ QueryResultsResponse
     │ { attempt_id: 42, current_page: 2, page_size: 500,
     │   columns: [...], rows: [...500 more rows...] }
     ▼
┌──────────┐
│ Frontend │  Display page 2 of results
└──────────┘


Step 4: EXPORT TO CSV
┌──────────┐
│ Frontend │  GET /queries/42/export
└────┬─────┘
     │
     ▼
┌──────────┐
│ Backend  │  Generate CSV (up to 10k rows)
└────┬─────┘
     │
     │ text/csv file download
     ▼
┌──────────┐
│ Frontend │  Browser downloads CSV file
└──────────┘
```

## Type Hierarchy

### User Types

```
┌──────────────────────────┐
│      Users (DB Table)    │
│ ────────────────────────│
│ id: INTEGER PK          │
│ username: TEXT          │
│ password_hash: TEXT     │  ◄── Excluded from API
│ role: TEXT              │
│ active: INTEGER (0/1)   │
│ created_at: TEXT        │
└────────────┬─────────────┘
             │
             │ ORM Mapping
             │
             ▼
┌──────────────────────────┐
│     UserResponse (DTO)   │
│ ────────────────────────│
│ id: int                 │
│ username: str           │
│ role: UserRole          │  ◄── Enum conversion
│ active: bool            │  ◄── Integer to bool
└────────────┬─────────────┘
             │
             │ Used in
             │
    ┌────────┴────────┐
    ▼                 ▼
┌─────────────┐  ┌─────────────┐
│LoginResponse│  │SessionResp. │
│─────────────│  │─────────────│
│user: User   │  │user: User   │
│session: ... │  │session: ... │
└─────────────┘  └─────────────┘
```

### Query Types

```
┌────────────────────────────────────────────────────┐
│           QueryAttempt (Base Type)                 │
│────────────────────────────────────────────────────│
│ id: int                                            │
│ natural_language_query: str                        │
│ generated_sql: str | None                          │
│ status: QueryStatus                                │
│ created_at: ISO8601Timestamp                       │
│ generated_at: ISO8601Timestamp | None              │
│ generation_ms: int | None                          │
└────────────────┬───────────────────────────────────┘
                 │
     ┌───────────┼───────────┐
     │           │           │
     ▼           ▼           ▼
┌────────┐  ┌──────────┐  ┌─────────────────┐
│Simplified│ │QueryAttempt│ │QueryAttemptDetail│
│Query     │ │Response  │ │Response          │
│Attempt   │ │          │ │──────────────────│
│──────────│ │(same as  │ │+ executed_at     │
│id        │ │base)     │ │+ execution_ms    │
│nl_query │ │          │ │+ original_attempt│
│status    │ │          │ │  _id             │
│created_at│ │          │ │                  │
│executed_at│ │          │ │                  │
└──────────┘ └──────────┘ └─────────────────┘
    │                           │
    │ Used in:                  │ Used in:
    │ - QueryListResponse       │ - GET /queries/{id}
    │   (list view)             │   (detail view)
    │                           │
    └───────────────────────────┘
                │
                ▼
        ┌─────────────────┐
        │ RerunQueryResp. │
        │─────────────────│
        │ (extends base)  │
        │+ original_      │
        │  attempt_id     │
        │  (required)     │
        └─────────────────┘
```

### Pagination Types

```
┌──────────────────────────┐
│   PaginationParams       │  ◄── Request
│  (Query Parameters)      │
│──────────────────────────│
│ page?: int = 1           │
│ page_size?: int = 20     │
└────────────┬─────────────┘
             │
             │ Used in GET /queries, etc.
             │
             ▼
┌──────────────────────────┐
│  Backend Processing      │
│──────────────────────────│
│ 1. Validate params       │
│ 2. Query database        │
│ 3. Calculate metadata    │
└────────────┬─────────────┘
             │
             │ Returns
             │
             ▼
┌──────────────────────────┐
│  PaginationMetadata      │  ◄── Response
│──────────────────────────│
│ page: int                │
│ page_size: int           │
│ total_count: int         │
│ total_pages: int         │
└────────────┬─────────────┘
             │
             │ Included in
             │
    ┌────────┴────────┐
    ▼                 ▼
┌──────────┐    ┌──────────┐
│QueryList │    │Generic   │
│Response  │    │Paginated │
│──────────│    │Response<T>│
│queries   │    │──────────│
│pagination│    │items: T[]│
└──────────┘    │pagination│
                └──────────┘
```

## Validation Pipeline

```
┌────────────────────────────────────────────────────────────────┐
│                    Request Validation Flow                     │
└────────────────────────────────────────────────────────────────┘

Frontend Validation (Optional, for UX)
┌──────────────────────────────────────┐
│ 1. TypeScript Type Check             │
│    - Compile-time validation         │
│    - IDE autocomplete & errors       │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│ 2. Runtime Type Guards (Optional)    │
│    - isQueryStatus()                 │
│    - isUserRole()                    │
│    - Custom validation functions     │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│ 3. Form Validation (Optional)        │
│    - Min/max length checks           │
│    - Required field checks           │
│    - Format validation               │
└────────────────┬─────────────────────┘
                 │
                 │ HTTP Request
                 │ (JSON payload)
                 │
                 ▼
═══════════════════════════════════════════
Backend Validation (Required, for Security)
═══════════════════════════════════════════
                 │
                 ▼
┌──────────────────────────────────────┐
│ 4. FastAPI Request Parsing           │
│    - Parse JSON                      │
│    - Extract path/query params       │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│ 5. Pydantic Schema Validation        │
│    ┌────────────────────────────────┐│
│    │ Field() Constraints            ││
│    │ - min_length, max_length       ││
│    │ - ge, le (numeric)             ││
│    │ - pattern (regex)              ││
│    └────────────────────────────────┘│
│    ┌────────────────────────────────┐│
│    │ @field_validator               ││
│    │ - Custom validation logic      ││
│    │ - Transform values             ││
│    │ - Cross-field validation       ││
│    └────────────────────────────────┘│
│    ┌────────────────────────────────┐│
│    │ Type Coercion                  ││
│    │ - String to int/bool           ││
│    │ - Enum validation              ││
│    └────────────────────────────────┘│
└────────────────┬─────────────────────┘
                 │
          ┌──────┴──────┐
          │             │
      Valid?           Invalid
          │             │
          │             ▼
          │    ┌────────────────────┐
          │    │ ValidationError    │
          │    │ (HTTP 422)         │
          │    │ - Detailed errors  │
          │    │ - Field locations  │
          │    └────────────────────┘
          │
          ▼
┌──────────────────────────────────────┐
│ 6. Business Logic Validation         │
│    - SQL SELECT-only check           │
│    - Permission checks               │
│    - Rate limiting                   │
│    - Database constraints            │
└────────────────┬─────────────────────┘
                 │
          ┌──────┴──────┐
          │             │
      Valid?           Invalid
          │             │
          │             ▼
          │    ┌────────────────────┐
          │    │ HTTP 400/401/403   │
          │    │ ErrorResponse      │
          │    └────────────────────┘
          │
          ▼
┌──────────────────────────────────────┐
│ 7. Process Request                   │
│    - Execute business logic          │
│    - Query databases                 │
│    - Call external APIs              │
└────────────────┬─────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────┐
│ 8. Build Response                    │
│    - Create Pydantic response model  │
│    - Serialize to JSON               │
│    - Set HTTP status code            │
└────────────────┬─────────────────────┘
                 │
                 │ HTTP Response
                 ▼
        ┌────────────────┐
        │   Frontend     │
        └────────────────┘
```

## Data Flow Example: Create & Execute Query

```
User Input: "Show all active users"
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: CreateQueryRequest                                 │
│ { natural_language_query: "Show all active users" }         │
└─────────────────────────────────────────────────────────────┘
│
│ POST /queries
▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: Pydantic Validation                                 │
│ ✓ Length: 1-5000 chars                                      │
│ ✓ Not whitespace-only                                       │
└─────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: SQL Generation (LLM)                                │
│ 1. Two-stage schema selection                               │
│ 2. Find similar KB examples                                 │
│ 3. Generate SQL via GPT-4                                   │
│ Result: "SELECT * FROM users WHERE active = 1"              │
└─────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: Store in Database                                   │
│ INSERT INTO query_attempts (                                │
│   user_id, natural_language_query, generated_sql,           │
│   status, created_at, generated_at, generation_ms           │
│ )                                                            │
└─────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: Build QueryAttemptResponse                          │
│ {                                                            │
│   id: 42,                                                    │
│   natural_language_query: "Show all active users",          │
│   generated_sql: "SELECT * FROM users WHERE active = 1",    │
│   status: "not_executed",                                   │
│   created_at: "2025-10-28T12:00:00Z",                       │
│   generated_at: "2025-10-28T12:00:02Z",                     │
│   generation_ms: 2150                                       │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
│
│ 201 Created
▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: Display Query                                      │
│ - Show generated SQL                                         │
│ - Show generation time                                       │
│ - Enable "Execute" button                                    │
└─────────────────────────────────────────────────────────────┘
│
│ User clicks "Execute"
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: POST /queries/42/execute                           │
└─────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: Validate SQL (SELECT-only)                          │
│ ✓ No INSERT/UPDATE/DELETE/DROP                             │
│ ✓ Contains SELECT                                           │
└─────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: Execute on PostgreSQL                               │
│ - Connect with read-only user                               │
│ - Set 5-minute timeout                                      │
│ - Execute query                                             │
│ Result: 150 rows returned                                   │
└─────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: Update Database                                     │
│ UPDATE query_attempts SET                                   │
│   status = 'success',                                       │
│   executed_at = '2025-10-28T12:00:05Z',                     │
│   execution_ms = 342                                        │
│                                                              │
│ INSERT INTO query_results_manifest (...)                    │
└─────────────────────────────────────────────────────────────┘
│
▼
┌─────────────────────────────────────────────────────────────┐
│ Backend: Build ExecuteQueryResponse                          │
│ {                                                            │
│   id: 42,                                                    │
│   status: "success",                                        │
│   executed_at: "2025-10-28T12:00:05Z",                      │
│   execution_ms: 342,                                        │
│   results: {                                                │
│     total_rows: 150,                                        │
│     page_size: 500,                                         │
│     page_count: 1,                                          │
│     columns: ["id", "username", "email", "active"],         │
│     rows: [                                                 │
│       [1, "john_doe", "john@example.com", true],            │
│       [2, "jane_smith", "jane@example.com", true],          │
│       ...                                                   │
│     ]                                                       │
│   }                                                          │
│ }                                                            │
└─────────────────────────────────────────────────────────────┘
│
│ 200 OK
▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend: Display Results                                    │
│ - Show results table                                         │
│ - Show execution time                                        │
│ - Enable "Export CSV" button                                │
│ - Enable pagination if > 500 rows                           │
└─────────────────────────────────────────────────────────────┘
```

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      Error Types                             │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│ Validation Error │ (HTTP 422)
└────────┬─────────┘
         │
         ├─ Missing required field
         ├─ Invalid data type
         ├─ Length constraint violation
         └─ Custom validator failure
         │
         ▼
┌──────────────────────────────────────────┐
│ Pydantic ValidationError                 │
│ {                                        │
│   "detail": [                            │
│     {                                    │
│       "loc": ["body", "username"],       │
│       "msg": "field required",           │
│       "type": "value_error.missing"      │
│     }                                    │
│   ]                                      │
│ }                                        │
└──────────────────────────────────────────┘

┌──────────────────┐
│ Business Error   │ (HTTP 400)
└────────┬─────────┘
         │
         ├─ Query already executed
         ├─ Invalid SQL generated
         └─ Resource not in valid state
         │
         ▼
┌──────────────────────────────────────────┐
│ ErrorResponse                            │
│ {                                        │
│   "detail": "Query already executed",    │
│   "error_code": "QUERY_ALREADY_EXECUTED" │
│ }                                        │
└──────────────────────────────────────────┘

┌──────────────────┐
│ Auth Error       │ (HTTP 401/403)
└────────┬─────────┘
         │
         ├─ Invalid credentials
         ├─ Session expired
         ├─ Insufficient permissions
         └─ Account inactive
         │
         ▼
┌──────────────────────────────────────────┐
│ ErrorResponse                            │
│ {                                        │
│   "detail": "Invalid credentials",       │
│   "error_code": "AUTH_INVALID_CREDS"     │
│ }                                        │
└──────────────────────────────────────────┘

┌──────────────────┐
│ Not Found Error  │ (HTTP 404)
└────────┬─────────┘
         │
         └─ Resource doesn't exist
         │
         ▼
┌──────────────────────────────────────────┐
│ ErrorResponse                            │
│ {                                        │
│   "detail": "Query not found",           │
│   "error_code": "RESOURCE_NOT_FOUND"     │
│ }                                        │
└──────────────────────────────────────────┘

┌──────────────────┐
│ Server Error     │ (HTTP 500/503)
└────────┬─────────┘
         │
         ├─ Database connection failed
         ├─ LLM API unavailable
         └─ Unexpected exception
         │
         ▼
┌──────────────────────────────────────────┐
│ ErrorResponse                            │
│ {                                        │
│   "detail": "Service temporarily         │
│              unavailable",               │
│   "error_code": "SERVICE_UNAVAILABLE"    │
│ }                                        │
└──────────────────────────────────────────┘

Frontend Error Handling:

try {
  const response = await fetch("/api/queries");
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
    switch (error.status) {
      case 401:
        // Redirect to login
        break;
      case 403:
        // Show permission denied
        break;
      case 422:
        // Show validation errors
        break;
      default:
        // Show generic error
    }
  }
}
```

---

**Note:** These diagrams use ASCII art for universal compatibility. For rendered diagrams, consider using tools like Mermaid, PlantUML, or draw.io.

