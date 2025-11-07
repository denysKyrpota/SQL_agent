# Backend Implementation Plan

**Status**: 📋 Planning Complete
**Date**: 2025-11-05
**Estimated Time**: 16-24 hours
**Priority**: 🔥 High

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Architecture Overview](#architecture-overview)
3. [Implementation Tasks](#implementation-tasks)
4. [Service Layer Details](#service-layer-details)
5. [API Endpoints Details](#api-endpoints-details)
6. [Testing Strategy](#testing-strategy)
7. [Deployment Checklist](#deployment-checklist)

---

## Current State Analysis

### ✅ What's Implemented

**Infrastructure:**
- ✅ FastAPI application setup (`backend/app/main.py`)
- ✅ Database models (User, Session, QueryAttempt, etc.) in `backend/app/models/`
- ✅ Pydantic schemas/DTOs in `backend/app/schemas/`
- ✅ SQLite database with migrations system
- ✅ Authentication service with bcrypt + sessions (`auth_service.py`)
- ✅ CORS middleware and security headers
- ✅ Error handling infrastructure

**API Routes:**
- ✅ `POST /api/auth/login` - User login (COMPLETE)
- ✅ `POST /api/auth/logout` - User logout (COMPLETE)
- ✅ `POST /api/queries` - Create query (SKELETON ONLY)
- ⚠️ Other query endpoints - Return 501 Not Implemented

**Data:**
- ✅ Knowledge base SQL examples in `data/knowledge_base/` (7 files)
- ✅ PostgreSQL schema JSON files in `data/schema/` (5 files)

### ❌ What's Missing

**Services:**
- ❌ `LLMService` - OpenAI integration for SQL generation
- ❌ `SchemaService` - Load and filter PostgreSQL schema
- ❌ `KnowledgeBaseService` - Load examples, compute embeddings, similarity search
- ❌ `PostgresExecutionService` - Execute queries against target database
- ❌ `ExportService` - CSV export with streaming
- ⚠️ `QueryService` - Has skeleton, needs full implementation

**API Endpoints:**
- ❌ `POST /api/queries/{id}/execute` - Execute generated SQL
- ❌ `GET /api/queries/{id}/results` - Get paginated results
- ❌ `GET /api/queries/{id}/export` - Export CSV
- ❌ `GET /api/queries/{id}` - Get query details
- ❌ `GET /api/queries` - List queries with pagination
- ❌ `POST /api/queries/{id}/rerun` - Re-run historical query
- ❌ `POST /api/admin/schema/refresh` - Refresh schema cache
- ❌ `GET /api/health` - Health check

**Features:**
- ❌ Rate limiting (10 requests/minute per user)
- ❌ Query result pagination (500 rows per page)
- ❌ Query timeout handling (5 minutes)
- ❌ Retry logic for LLM calls (3 retries with exponential backoff)
- ❌ Metrics tracking

---

## Architecture Overview

### Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                     │
│  Routes: auth.py, queries.py, admin.py, health.py          │
│  - Request validation (Pydantic)                            │
│  - Authentication/authorization                              │
│  - Error handling                                           │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer (Business Logic)            │
│  Services:                                                   │
│  - AuthService (✅ COMPLETE)                                │
│  - QueryService (⚠️ SKELETON)                               │
│  - LLMService (❌ TODO)                                     │
│  - SchemaService (❌ TODO)                                  │
│  - KnowledgeBaseService (❌ TODO)                           │
│  - PostgresExecutionService (❌ TODO)                       │
│  - ExportService (❌ TODO)                                  │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer (SQLAlchemy)                    │
│  Models: User, Session, QueryAttempt, ResultsManifest, etc. │
│  - SQLite for app data                                      │
│  - PostgreSQL for query execution (read-only)               │
└─────────────────────────────────────────────────────────────┘
```

### Query Workflow

```
1. User submits natural language query
   POST /api/queries
   └─> QueryService.create_query_attempt()

2. Load PostgreSQL schema from cache
   └─> SchemaService.get_schema()

3. Stage 1: Schema Optimization (LLM)
   └─> LLMService.select_relevant_tables(schema, question)
   └─> Returns: ["users", "orders", "products"]

4. Load knowledge base examples
   └─> KnowledgeBaseService.find_similar_examples(question, top_k=3)
   └─> Uses embeddings + cosine similarity

5. Stage 2: SQL Generation (LLM)
   └─> LLMService.generate_sql(question, filtered_schema, examples)
   └─> Returns: "SELECT u.name, COUNT(o.id) FROM users u..."

6. Validate SQL (security check)
   └─> Ensure SELECT-only, no DDL/DML
   └─> Save to database with status='not_executed'

7. User clicks "Execute Query"
   POST /api/queries/{id}/execute
   └─> PostgresExecutionService.execute_query(sql)

8. Store results in ResultsManifest
   └─> Paginate at 500 rows per page
   └─> Return first page + metadata

9. User navigates pages or exports
   GET /api/queries/{id}/results?page=2
   GET /api/queries/{id}/export
```

---

## Implementation Tasks

### Task 1: LLM Service (Priority: 🔥 CRITICAL)

**File**: `backend/app/services/llm_service.py`

**Responsibilities:**
- Interface with OpenAI API (GPT-4)
- Two-stage SQL generation process
- Retry logic with exponential backoff
- Response validation and parsing

**Key Methods:**
```python
class LLMService:
    async def select_relevant_tables(schema: dict, question: str) -> list[str]:
        """Stage 1: Select relevant tables from schema"""

    async def generate_sql(question: str, filtered_schema: dict,
                          examples: list[str]) -> str:
        """Stage 2: Generate SQL using context"""

    async def _call_openai_with_retry(messages: list[dict],
                                      max_retries: int = 3) -> str:
        """Call OpenAI with exponential backoff"""
```

**Prompt Engineering:**
- **Stage 1 Prompt**: "Given this database schema, select only the tables relevant to answering this question: {question}"
- **Stage 2 Prompt**: "Generate a PostgreSQL SELECT query to answer: {question}. Use this schema: {schema}. Here are similar examples: {examples}"

**Configuration** (from `.env`):
- `OPENAI_API_KEY` - API key
- `OPENAI_MODEL` - Model name (default: gpt-4)
- `OPENAI_MAX_TOKENS` - Max response tokens (default: 1000)
- `OPENAI_TEMPERATURE` - Temperature (default: 0.0 for deterministic)

**Error Handling:**
- `RateLimitError` → Retry with exponential backoff
- `APIError` → Retry up to 3 times
- `InvalidResponseError` → Return `failed_generation` status
- After 3 retries → Raise `LLMServiceUnavailableError`

**Dependencies:**
```python
import openai
from openai import AsyncOpenAI, RateLimitError, APIError
```

**Estimated Time**: 4-5 hours

---

### Task 2: Schema Service (Priority: 🔥 HIGH)

**File**: `backend/app/services/schema_service.py`

**Responsibilities:**
- Load PostgreSQL schema from JSON files
- Cache schema in memory on startup
- Filter schema by selected tables
- Refresh schema on demand (admin endpoint)

**Key Methods:**
```python
class SchemaService:
    def __init__(self):
        self._schema_cache: dict | None = None

    def load_schema(self) -> dict:
        """Load schema from data/schema/all_in_one_schema_overview.json"""

    def get_schema(self) -> dict:
        """Get cached schema, load if not cached"""

    def filter_schema_by_tables(self, table_names: list[str]) -> dict:
        """Return schema with only specified tables"""

    def refresh_schema(self) -> dict:
        """Reload schema from disk, clear cache"""
```

**Schema JSON Structure** (from `all_in_one_schema_overview.json`):
```json
{
  "tables": [
    {
      "table_name": "users",
      "columns": [
        {"name": "id", "type": "integer", "nullable": false},
        {"name": "name", "type": "varchar(100)", "nullable": false}
      ],
      "primary_key": ["id"],
      "foreign_keys": [],
      "description": "User accounts"
    }
  ]
}
```

**Caching Strategy:**
- Load on application startup (`lifespan` in `main.py`)
- Store in memory (acceptable for MVP, ~1MB of data)
- Refresh via admin endpoint or periodic reload

**Estimated Time**: 2-3 hours

---

### Task 3: Knowledge Base Service (Priority: 🔥 HIGH)

**File**: `backend/app/services/knowledge_base_service.py`

**Responsibilities:**
- Load SQL example files from `data/knowledge_base/`
- Generate embeddings for examples (OpenAI embeddings API)
- Perform similarity search using cosine similarity
- Cache embeddings in memory

**Key Methods:**
```python
class KnowledgeBaseService:
    def __init__(self, llm_service: LLMService):
        self._examples_cache: list[KBExample] | None = None

    def load_examples(self) -> list[KBExample]:
        """Load all .sql files from knowledge_base/"""

    async def generate_embeddings(self, examples: list[KBExample]) -> None:
        """Generate embeddings using OpenAI embeddings API"""

    async def find_similar_examples(self, question: str,
                                   top_k: int = 3) -> list[KBExample]:
        """Find top K similar examples using cosine similarity"""

    def _cosine_similarity(self, vec1: list[float],
                          vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors"""
```

**KBExample Data Class:**
```python
@dataclass
class KBExample:
    filename: str
    question: str  # Extracted from filename or comment
    sql: str
    embedding: list[float] | None = None
```

**Embedding API:**
- Model: `text-embedding-ada-002` (1536 dimensions)
- Batch embeddings for all examples on startup
- Cache in memory (~7 examples × 1536 floats = ~40KB)

**SQL File Format** (from `data/knowledge_base/`):
```sql
-- Question: What activities finished today with truck license plates?
-- Description: Shows activities completed today with truck details
SELECT
    a.id,
    a.name,
    t.license_plate
FROM activities a
JOIN trucks t ON a.truck_id = t.id
WHERE DATE(a.finished_at) = CURRENT_DATE;
```

**Similarity Search:**
1. Generate embedding for user's question
2. Calculate cosine similarity with all cached examples
3. Return top 3 most similar examples

**Dependencies:**
```python
import numpy as np
from openai import AsyncOpenAI
```

**Estimated Time**: 4-5 hours

---

### Task 4: PostgreSQL Execution Service (Priority: 🔥 HIGH)

**File**: `backend/app/services/postgres_execution_service.py`

**Responsibilities:**
- Execute SELECT queries against target PostgreSQL database
- Enforce query timeout (30 seconds default)
- Validate SQL (SELECT-only, no DDL/DML)
- Return results with metadata
- Store results in ResultsManifest for pagination

**Key Methods:**
```python
class PostgresExecutionService:
    def __init__(self):
        self._engine: Engine | None = None

    def validate_sql(self, sql: str) -> None:
        """Ensure SQL is SELECT-only, raise ValueError if invalid"""

    async def execute_query(self, sql: str, timeout: int = 30) -> QueryResult:
        """Execute SQL with timeout, return results"""

    def _create_engine(self) -> Engine:
        """Create PostgreSQL engine from POSTGRES_URL"""
```

**QueryResult Data Class:**
```python
@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list[Any]]
    total_rows: int
    execution_ms: int
```

**SQL Validation:**
- Use `sqlparse` library to parse SQL
- Check first statement type is SELECT
- Reject: INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE
- Reject: Multiple statements (;)
- Example:
```python
import sqlparse

def validate_sql(sql: str) -> None:
    parsed = sqlparse.parse(sql)
    if len(parsed) != 1:
        raise ValueError("Only single statements allowed")

    stmt = parsed[0]
    if stmt.get_type() != 'SELECT':
        raise ValueError(f"Only SELECT queries allowed, got {stmt.get_type()}")
```

**Timeout Handling:**
- Use SQLAlchemy `execution_options(timeout=30)`
- Catch `TimeoutError` and return 408 Request Timeout
- Log slow queries (> 5 seconds)

**Connection Pooling:**
- Use SQLAlchemy connection pool
- Max 10 connections (MVP)
- Read-only user recommended

**Configuration:**
```python
from backend.app.config import get_settings
settings = get_settings()
postgres_url = settings.postgres_url
timeout = settings.postgres_timeout  # default: 30
```

**Dependencies:**
```python
from sqlalchemy import create_engine, text
import sqlparse
```

**Estimated Time**: 3-4 hours

---

### Task 5: CSV Export Service (Priority: 🟡 MEDIUM)

**File**: `backend/app/services/export_service.py`

**Responsibilities:**
- Export query results to CSV format
- Limit to 10,000 rows (configurable)
- Stream response to avoid memory issues
- Proper CSV escaping (quotes, commas, newlines)

**Key Methods:**
```python
class ExportService:
    def __init__(self):
        self.max_rows = 10000

    async def export_to_csv(self, query_id: int, db: Session) -> StreamingResponse:
        """Export query results as streaming CSV"""

    def _generate_csv_rows(self, columns: list[str],
                          rows: list[list[Any]]) -> Generator[str, None, None]:
        """Generate CSV rows as strings"""
```

**CSV Format:**
- UTF-8 encoding
- RFC 4180 compliant
- Headers: Column names
- Escape special characters: quotes, commas, newlines
- NULL values: empty string

**FastAPI Streaming Response:**
```python
from fastapi.responses import StreamingResponse
import csv
import io

def generate_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)  # Header
    for row in rows:
        writer.writerow(row)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

return StreamingResponse(
    generate_csv(),
    media_type="text/csv",
    headers={
        "Content-Disposition": f"attachment; filename=query_{query_id}.csv"
    }
)
```

**Error Handling:**
- If > 10,000 rows → Return 413 Payload Too Large
- Provide error message with row count

**Dependencies:**
```python
import csv
import io
from fastapi.responses import StreamingResponse
```

**Estimated Time**: 2-3 hours

---

### Task 6: Complete Query Service (Priority: 🔥 CRITICAL)

**File**: `backend/app/services/query_service.py` (UPDATE EXISTING)

**Current State**: Skeleton with TODOs
**Goal**: Integrate all services and implement full workflow

**Changes Needed:**

1. **Inject Dependencies:**
```python
class QueryService:
    def __init__(
        self,
        llm_service: LLMService,
        schema_service: SchemaService,
        kb_service: KnowledgeBaseService,
        pg_service: PostgresExecutionService
    ):
        self.llm = llm_service
        self.schema = schema_service
        self.kb = kb_service
        self.pg = pg_service
```

2. **Implement `_generate_sql()` Method:**
```python
async def _generate_sql(self, natural_language_query: str, user_id: int) -> str:
    # Stage 1: Schema optimization
    full_schema = self.schema.get_schema()
    relevant_tables = await self.llm.select_relevant_tables(
        schema=full_schema,
        question=natural_language_query
    )

    # Filter schema
    filtered_schema = self.schema.filter_schema_by_tables(relevant_tables)

    # Stage 2: Load examples
    examples = await self.kb.find_similar_examples(
        question=natural_language_query,
        top_k=3
    )

    # Stage 3: Generate SQL
    sql = await self.llm.generate_sql(
        question=natural_language_query,
        filtered_schema=filtered_schema,
        examples=[ex.sql for ex in examples]
    )

    # Validate SQL
    self.pg.validate_sql(sql)

    return sql
```

3. **Replace Placeholder Methods:**
- `_create_initial_attempt()` → Use actual SQLAlchemy insert
- `_update_attempt_success()` → Use actual SQLAlchemy update
- `_update_attempt_failure()` → Use actual SQLAlchemy update

4. **Add Query Execution Method:**
```python
async def execute_query(self, db: Session, query_id: int, user_id: int) -> QueryExecutionResponse:
    # Get query attempt
    query = db.query(QueryAttempt).filter(QueryAttempt.id == query_id).first()

    # Authorization check
    if query.user_id != user_id and not is_admin(user_id):
        raise HTTPException(403, "Not authorized")

    # Execute SQL
    result = await self.pg.execute_query(query.generated_sql)

    # Store in ResultsManifest
    manifest = self._store_results(db, query_id, result)

    # Update query status
    query.status = QueryStatus.SUCCESS
    query.executed_at = datetime.utcnow()
    query.execution_ms = result.execution_ms
    db.commit()

    return QueryExecutionResponse(...)
```

**Estimated Time**: 3-4 hours

---

### Task 7: Implement Query API Endpoints (Priority: 🔥 HIGH)

**File**: `backend/app/api/queries.py` (UPDATE EXISTING)

**Endpoints to Implement:**

#### 7.1 `POST /api/queries/{id}/execute`
```python
@router.post("/{id}/execute", response_model=QueryExecutionResponse)
async def execute_query(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return await query_service.execute_query(db, id, user.id)
```

#### 7.2 `GET /api/queries/{id}/results?page=1`
```python
@router.get("/{id}/results", response_model=QueryResultsPage)
async def get_query_results(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
):
    # Get ResultsManifest
    manifest = db.query(ResultsManifest).filter_by(query_id=id).first()

    # Authorization check
    query = db.query(QueryAttempt).get(id)
    if query.user_id != user.id and user.role != 'admin':
        raise HTTPException(403)

    # Calculate offset
    page_size = 500
    offset = (page - 1) * page_size

    # Get rows from JSON
    all_rows = json.loads(manifest.results_json)
    page_rows = all_rows[offset:offset + page_size]

    return QueryResultsPage(
        columns=json.loads(manifest.columns_json),
        rows=page_rows,
        total_rows=manifest.total_rows,
        page=page,
        page_size=page_size,
        total_pages=(manifest.total_rows + page_size - 1) // page_size
    )
```

#### 7.3 `GET /api/queries/{id}/export`
```python
@router.get("/{id}/export")
async def export_query_results(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    # Authorization check
    query = db.query(QueryAttempt).get(id)
    if query.user_id != user.id and user.role != 'admin':
        raise HTTPException(403)

    return await export_service.export_to_csv(id, db)
```

#### 7.4 `GET /api/queries?page=1&status=success`
```python
@router.get("", response_model=QueryListResponse)
async def list_queries(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
):
    # Build query
    query = db.query(QueryAttempt)

    # Filter by user (unless admin)
    if user.role != 'admin':
        query = query.filter(QueryAttempt.user_id == user.id)

    # Filter by status
    if status_filter:
        query = query.filter(QueryAttempt.status == status_filter)

    # Order by most recent
    query = query.order_by(QueryAttempt.created_at.desc())

    # Paginate
    total = query.count()
    queries = query.offset((page - 1) * page_size).limit(page_size).all()

    return QueryListResponse(
        queries=[QueryAttemptResponse.from_orm(q) for q in queries],
        total=total,
        page=page,
        page_size=page_size
    )
```

#### 7.5 `GET /api/queries/{id}`
```python
@router.get("/{id}", response_model=QueryAttemptResponse)
async def get_query(
    id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    query = db.query(QueryAttempt).get(id)
    if not query:
        raise HTTPException(404, "Query not found")

    # Authorization
    if query.user_id != user.id and user.role != 'admin':
        raise HTTPException(403)

    return QueryAttemptResponse.from_orm(query)
```

**Estimated Time**: 3-4 hours

---

### Task 8: Rate Limiting (Priority: 🟡 MEDIUM)

**File**: `backend/app/middleware/rate_limiter.py`

**Requirements:**
- 10 requests per minute per user for `/api/queries`
- Store request counts in memory (Redis for production)
- Return 429 Too Many Requests when exceeded

**Simple Implementation (In-Memory):**
```python
from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: defaultdict[int, list[datetime]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip for non-query endpoints
        if not request.url.path.startswith("/api/queries"):
            return await call_next(request)

        # Get user ID from request state (set by auth dependency)
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            return await call_next(request)

        # Clean old requests
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > cutoff
        ]

        # Check limit
        if len(self.requests[user_id]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Try again in 60 seconds."
            )

        # Record request
        self.requests[user_id].append(now)

        return await call_next(request)
```

**Register in `main.py`:**
```python
app.add_middleware(RateLimiter, requests_per_minute=10)
```

**Estimated Time**: 2 hours

---

### Task 9: Admin Endpoints (Priority: 🟢 LOW)

**File**: `backend/app/api/admin.py`

**Endpoints:**

#### 9.1 `POST /api/admin/schema/refresh`
```python
@router.post("/schema/refresh")
async def refresh_schema(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    # Check admin role
    if user.role != 'admin':
        raise HTTPException(403, "Admin access required")

    # Refresh schema
    schema = schema_service.refresh_schema()

    return {
        "message": "Schema refreshed successfully",
        "tables_count": len(schema.get("tables", []))
    }
```

#### 9.2 `GET /api/admin/metrics`
```python
@router.get("/metrics")
async def get_metrics(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    if user.role != 'admin':
        raise HTTPException(403)

    # Query metrics from database
    total_queries = db.query(QueryAttempt).count()
    successful = db.query(QueryAttempt).filter_by(status='success').count()
    failed = db.query(QueryAttempt).filter_by(status='failed_generation').count()

    return {
        "total_queries": total_queries,
        "successful": successful,
        "failed": failed,
        "success_rate": successful / total_queries if total_queries > 0 else 0
    }
```

**Estimated Time**: 2 hours

---

### Task 10: Health Check Endpoint (Priority: 🟢 LOW)

**File**: `backend/app/api/health.py`

```python
from fastapi import APIRouter, status
from backend.app.config import get_settings
from backend.app.database import engine

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns:
        - status: "healthy" | "degraded" | "unhealthy"
        - database: Connection status
        - openai: API key configured
    """
    settings = get_settings()

    # Check database
    db_status = "healthy"
    try:
        engine.execute("SELECT 1")
    except Exception:
        db_status = "unhealthy"

    # Check OpenAI config
    openai_configured = bool(settings.openai_api_key)

    overall_status = "healthy"
    if db_status == "unhealthy":
        overall_status = "unhealthy"
    elif not openai_configured:
        overall_status = "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "openai_configured": openai_configured,
        "version": "1.0.0"
    }
```

**Register in `main.py`:**
```python
from backend.app.api import health
app.include_router(health.router, prefix="/api")
```

**Estimated Time**: 1 hour

---

## Testing Strategy

### Unit Tests

**Test Files:**
- `tests/services/test_llm_service.py`
- `tests/services/test_schema_service.py`
- `tests/services/test_knowledge_base_service.py`
- `tests/services/test_postgres_execution_service.py`
- `tests/services/test_export_service.py`

**Example Test:**
```python
import pytest
from backend.app.services.schema_service import SchemaService

@pytest.fixture
def schema_service():
    return SchemaService()

def test_load_schema(schema_service):
    schema = schema_service.load_schema()
    assert "tables" in schema
    assert len(schema["tables"]) > 0

def test_filter_schema_by_tables(schema_service):
    schema_service.load_schema()
    filtered = schema_service.filter_schema_by_tables(["users", "orders"])
    assert len(filtered["tables"]) == 2
```

### Integration Tests

**Test File:** `tests/api/test_queries_integration.py`

```python
@pytest.mark.asyncio
async def test_full_query_workflow(client, auth_token):
    # 1. Create query
    response = client.post(
        "/api/queries",
        json={"natural_language_query": "Show all users"},
        headers={"Cookie": f"session_token={auth_token}"}
    )
    assert response.status_code == 201
    query_id = response.json()["id"]

    # 2. Execute query
    response = client.post(
        f"/api/queries/{query_id}/execute",
        headers={"Cookie": f"session_token={auth_token}"}
    )
    assert response.status_code == 200

    # 3. Get results
    response = client.get(
        f"/api/queries/{query_id}/results?page=1",
        headers={"Cookie": f"session_token={auth_token}"}
    )
    assert response.status_code == 200
    assert "rows" in response.json()
```

**Run Tests:**
```bash
pytest tests/ -v
pytest tests/ --cov=backend --cov-report=html
```

**Coverage Goal:** > 80%

---

## Deployment Checklist

### Before Deployment

- [ ] All services implemented and tested
- [ ] Environment variables configured in `.env`
- [ ] Database migrations applied (`make db-migrate`)
- [ ] OpenAI API key valid and funded
- [ ] PostgreSQL target database accessible (read-only user)
- [ ] Knowledge base SQL files loaded
- [ ] Schema JSON files up-to-date
- [ ] Health check endpoint returns "healthy"
- [ ] Rate limiting tested
- [ ] CSV export tested with large datasets
- [ ] Error handling tested (network errors, LLM failures, timeouts)

### Production Configuration

**Environment Variables:**
```bash
# Production values
ENVIRONMENT=production
DATABASE_URL=sqlite:///./data/app_data/app.db
POSTGRES_URL=postgresql://readonly:password@prod-db:5432/analytics
OPENAI_API_KEY=sk-prod-...
OPENAI_MODEL=gpt-4
SECRET_KEY=<generate-random-256-bit-key>
LOG_LEVEL=INFO
```

**Security:**
- [ ] Change `SECRET_KEY` to secure random value
- [ ] Use read-only PostgreSQL user
- [ ] Enable HTTPS in production
- [ ] Set `DATABASE_ECHO=false`
- [ ] Review CORS origins (remove localhost)
- [ ] Rate limiting enabled

**Monitoring:**
- [ ] Set up logging aggregation (e.g., CloudWatch, Datadog)
- [ ] Monitor `/api/health` endpoint
- [ ] Track OpenAI API usage and costs
- [ ] Set up alerts for high error rates

---

## Implementation Order (Recommended)

**Phase 1: Core Services (Days 1-2)**
1. ✅ Schema Service (2-3 hours)
2. ✅ LLM Service (4-5 hours)
3. ✅ Knowledge Base Service (4-5 hours)
4. ✅ Complete Query Service (3-4 hours)

**Phase 2: Execution & Export (Day 3)**
5. ✅ PostgreSQL Execution Service (3-4 hours)
6. ✅ CSV Export Service (2-3 hours)
7. ✅ Implement query endpoints (3-4 hours)

**Phase 3: Features & Polish (Day 4)**
8. ✅ Rate limiting (2 hours)
9. ✅ Admin endpoints (2 hours)
10. ✅ Health check (1 hour)
11. ✅ Integration tests (3-4 hours)

**Total Estimated Time:** 16-24 hours (2-3 days)

---

## Success Criteria

### Functional Requirements
- ✅ User can submit natural language query → SQL generated
- ✅ User can execute SQL → Results displayed
- ✅ User can paginate results → 500 rows per page
- ✅ User can export CSV → Download works
- ✅ Admin can refresh schema → Cache updated
- ✅ Rate limiting enforced → 10 req/min per user

### Non-Functional Requirements
- ✅ 95% of queries generate SQL in < 2 minutes
- ✅ Query execution timeout at 30 seconds
- ✅ CSV export works for up to 10,000 rows
- ✅ API responds to health checks
- ✅ Errors logged with context
- ✅ All endpoints have proper error handling

### Quality Gates
- ✅ Test coverage > 80%
- ✅ No console errors on happy path
- ✅ API documentation complete (`/docs`)
- ✅ Environment example file up-to-date
- ✅ CLAUDE.md updated with new commands

---

## Next Steps After Implementation

1. **Frontend Integration:**
   - Connect Query Interface View to real API endpoints
   - Remove mock data from frontend
   - Test full E2E workflow

2. **Performance Optimization:**
   - Add Redis for rate limiting (production)
   - Implement query result caching
   - Add database indexes for common queries

3. **Enhanced Features:**
   - Query history with search
   - Saved queries / favorites
   - Query templates
   - Scheduled queries (cron jobs)

4. **Monitoring & Analytics:**
   - Track query success rates
   - Monitor LLM costs
   - User analytics dashboard

---

**Document Version:** 1.0
**Last Updated:** 2025-11-05
**Author:** SQL AI Agent Team
**Status:** 📋 Ready for Implementation
