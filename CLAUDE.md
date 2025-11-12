# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A full-stack SQL AI Agent that translates natural language queries into SQL and executes them against a PostgreSQL database. The system uses OpenAI's LLM with a two-stage SQL generation process and RAG-based knowledge base for improved accuracy.

**Key Stats:** 179 passing tests, 89% coverage, React 18 + FastAPI + PostgreSQL + OpenAI GPT-4

## Common Commands

### Backend Development

```bash
# Start backend server (port 8000)
python -m backend.app.main
# or with uvicorn directly
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Initialize database with default users (admin/admin123, testuser/testpass123)
python scripts/init_db.py
# or
make db-init

# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=backend/app --cov-report=html

# Run specific test file
pytest tests/api/test_auth.py -v

# Run single test
pytest tests/api/test_auth.py::TestAuthLogin::test_login_success -v

# Run tests without coverage (faster)
python -m pytest tests/ -v --no-cov
```

### Frontend Development

```bash
cd frontend

# Start dev server (port 3000, proxies /api to localhost:8000)
npm run dev

# Type check
npm run type-check

# Lint
npm run lint

# Build for production
npm run build
```

### Database Management

```bash
# Run migrations
make db-migrate

# Check migration status
make db-status

# Reset database (WARNING: deletes all data)
make db-reset

# Open SQLite shell
make db-shell

# Generate TypeScript types from schema
make generate-types
```

## Architecture

### Three-Layer Backend Architecture

The backend follows a strict separation of concerns:

1. **API Layer** (`backend/app/api/`)
   - FastAPI route handlers
   - Request/response validation via Pydantic schemas
   - Authentication and authorization enforcement
   - Minimal business logic - delegates to services

2. **Service Layer** (`backend/app/services/`)
   - All business logic lives here
   - Orchestrates complex workflows
   - Handles external API calls (OpenAI)
   - Transaction management

3. **Data Layer** (`backend/app/models/`)
   - SQLAlchemy ORM models
   - Database schema definitions
   - Relationships and constraints

**Critical:** Never put business logic in API handlers. Always delegate to service layer.

### Two-Stage SQL Generation Process

The core SQL generation workflow is implemented in `backend/app/services/query_service.py` and `backend/app/services/llm_service.py`:

**Stage 1: Schema Optimization** (`LLMService.select_relevant_tables()`)
- Problem: PostgreSQL schema has 279 tables - too large for LLM context
- Solution: Use LLM to select only relevant tables (max 10) based on question
- Input: All table names + user question
- Output: List of 5-10 relevant table names
- Implementation: `backend/app/services/llm_service.py:39-106`

**Stage 2: SQL Generation** (`LLMService.generate_sql()`)
- Use filtered schema from Stage 1
- Load similar SQL examples from knowledge base (top 3)
- Generate SQL with full context (schema + examples)
- Validate SQL (SELECT-only, no DDL/DML)
- Implementation: `backend/app/services/llm_service.py:151-214`

**Complete Workflow:**
```
User submits question
  → QueryService.create_query_attempt()
  → SchemaService.get_table_names()
  → LLMService.select_relevant_tables() [Stage 1]
  → SchemaService.filter_schema_by_tables()
  → KnowledgeBaseService.find_similar_examples()
  → LLMService.generate_sql() [Stage 2]
  → Validate SQL
  → Store in database
  → Return to user
```

### Query Execution Flow

Implemented in `backend/app/services/postgres_execution_service.py`:

```
User requests execution
  → PostgresExecutionService.execute_query()
  → Validate query (must be generated, not executed, SELECT-only)
  → Execute with 30-second timeout
  → Store results in QueryResultsManifest (JSON)
  → Paginate results (500 rows per page)
  → Return first page
```

**Important:** Results are stored in `QueryResultsManifest` model as JSON, not in separate tables. This allows efficient pagination without re-querying PostgreSQL.

### Database Architecture

**Two Databases:**
1. **SQLite** (`sqlite.db`) - Application data
   - Users, sessions (JWT auth)
   - Query attempts and results
   - Managed via migrations in `migrations/`

2. **PostgreSQL** (configured via `POSTGRES_URL`) - Target database
   - User's data to query
   - Read-only SELECT queries
   - Schema cached in `data/schema/` JSON files

### Authentication Flow

Implemented in `backend/app/services/auth_service.py`:

1. Login: POST `/api/auth/login` with username/password
2. Verify password with bcrypt
3. Create Session record with JWT token
4. Return token + user info
5. Frontend stores token and adds to Authorization header
6. `get_current_user` dependency validates token on protected routes
7. Logout: POST `/api/auth/logout` revokes session

**Session Management:**
- JWT tokens stored in Session table
- Configurable expiration (default 8 hours)
- Token revocation on logout
- Role-based access: admin sees all queries, users see only their own

### Knowledge Base System

Located in `data/knowledge_base/*.sql`:

- SQL examples for RAG-based generation
- Used in Stage 2 to provide context
- Currently: Simple keyword matching (TODO: embeddings)
- Service: `backend/app/services/knowledge_base_service.py`

When adding new example queries:
1. Create `.sql` file in `data/knowledge_base/`
2. Use descriptive filename (becomes query description)
3. Write clean, well-formatted SQL
4. Restart backend to reload examples

## Frontend Architecture

### Component Structure

- **Views** (`frontend/src/views/`) - Page-level components with routing
  - `QueryInterfaceView/` - Main SQL generation and execution interface
  - `QueryHistoryView/` - Historical query list with filtering
  - `LoginView/` - Authentication

- **Components** (`frontend/src/components/`) - Reusable UI components
  - Button, TextArea, Toast, Pagination, etc.
  - Each component in own directory with index.tsx

- **Services** (`frontend/src/services/`) - API client layer
  - `apiClient.ts` - Axios instance with auth interceptors
  - `authService.ts`, `queryService.ts`, `adminService.ts`
  - All API calls go through services, never direct fetch/axios in components

- **Types** (`frontend/src/types/`) - TypeScript definitions
  - Generated from backend schemas via `make generate-types`
  - Keep in sync with backend Pydantic models

### API Integration

All API communication uses the centralized `apiClient` (Axios instance):

```typescript
// frontend/src/services/apiClient.ts exports configured axios
// - Automatically adds Authorization header from AuthContext
// - Handles 401 errors (redirects to login)
// - Base URL: http://localhost:8000 or /api (proxied)
```

**Pattern:**
1. AuthContext provides authentication state
2. ProtectedRoute wraps authenticated views
3. Services use apiClient for all API calls
4. apiClient interceptor adds auth token
5. On 401, clear auth and redirect to login

## Testing

### Test Organization

```
tests/
├── api/              # API endpoint tests (FastAPI TestClient)
│   ├── test_auth.py  # Login, logout, session validation
│   └── test_queries.py  # Query CRUD, execution, export
└── services/         # Service layer unit tests
    ├── test_query_service.py
    ├── test_llm_service.py
    ├── test_knowledge_base_service.py
    └── ...
```

### Testing Patterns

**Use fixtures from `conftest.py`:**
- `db_session` - Clean database for each test
- `test_user` - Pre-created test user
- `admin_user` - Pre-created admin user
- `auth_headers_user` - Authorization headers for test user
- `mock_llm_service` - Mocked LLM for fast tests

**API Testing:**
```python
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
response = client.post("/api/auth/login", json={"username": "...", "password": "..."})
assert response.status_code == 200
```

**Service Testing:**
```python
@pytest.mark.asyncio
async def test_generate_sql(mock_llm_service):
    result = await mock_llm_service.generate_sql(...)
    assert result.startswith("SELECT")
```

### Key Test Coverage Areas

- Authentication flow (login, logout, token validation)
- Two-stage SQL generation (table selection + SQL generation)
- Query execution with timeout and validation
- CSV export with row limits (10,000 max)
- Knowledge base loading and example retrieval
- Role-based access control (admin vs user)

## Environment Configuration

Copy `.env.example` to `.env` and configure:

**Required:**
- `OPENAI_API_KEY` - Get from https://platform.openai.com/api-keys
- `POSTGRES_URL` - Target database for queries (postgresql://...)

**Optional but Important:**
- `SECRET_KEY` - Change in production (use `openssl rand -hex 32`)
- `SESSION_EXPIRATION_HOURS` - Default 8 hours
- `OPENAI_MODEL` - Default gpt-4 (can use gpt-3.5-turbo for cost)
- `DATABASE_ECHO` - Set `true` to log all SQL queries

## Code Style and Patterns

### Backend (Python)

- Use type hints everywhere
- Async/await for I/O operations (OpenAI, database)
- Pydantic for all DTOs and validation
- Dependency injection via FastAPI dependencies
- Comprehensive logging with structured extra fields
- Exception handling: Raise HTTPException in API layer, custom exceptions in services

### Frontend (TypeScript)

- Functional components with hooks
- CSS Modules for styling (`.module.css`)
- No inline styles except for dynamic values
- Props interfaces defined in component file or separate `types.ts`
- Custom hooks in `hooks/` directory
- Error boundaries for graceful failure

## Common Workflows

### Adding a New API Endpoint

1. Define Pydantic schemas in `backend/app/schemas/`
2. Implement business logic in `backend/app/services/`
3. Create route handler in `backend/app/api/`
4. Register router in `backend/app/main.py`
5. Write tests in `tests/api/`
6. Update frontend types: `make generate-types`
7. Create service function in `frontend/src/services/`
8. Use in component

### Adding a Database Migration

1. Create migration file: `touch migrations/YYYYMMDDHHMMSS_description.sql`
2. Write SQL (CREATE TABLE, ALTER TABLE, etc.)
3. Run migration: `make db-migrate`
4. Update SQLAlchemy models in `backend/app/models/`
5. Generate TypeScript types: `make generate-types`

### Debugging SQL Generation Issues

1. Check OpenAI API key is valid
2. Enable SQL logging: `DATABASE_ECHO=true` in `.env`
3. Look at LLM prompts in logs (INFO level)
4. Check knowledge base examples loaded correctly
5. Verify schema snapshot is up to date
6. Test with simpler questions first
7. Check token usage in logs (may hit limits)

## Important Constraints

- **SQL Safety:** Only SELECT queries allowed - validated in multiple places
- **Export Limits:** CSV export capped at 10,000 rows
- **Timeout:** PostgreSQL queries timeout after 30 seconds
- **Pagination:** Results paginated at 500 rows per page
- **Table Selection:** Max 10 tables selected in Stage 1
- **KB Examples:** Top 3 examples used in Stage 2

## API Documentation

When backend is running:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Troubleshooting

**"OpenAI API key not configured"**
- Add `OPENAI_API_KEY=sk-...` to `.env`

**"LLM did not return valid table names"**
- Stage 1 failed - LLM response format unexpected
- Check logs for raw LLM response
- Simplify question or add more context

**"Query execution failed: timeout"**
- Query took >30 seconds
- Optimize query or increase `POSTGRES_TIMEOUT`

**Frontend can't reach API**
- Verify backend running on port 8000
- Check CORS settings in `backend/app/main.py`
- Verify proxy config in `frontend/vite.config.ts`

**Tests failing with database errors**
- Run `make db-init` to reset test database
- Check migrations are up to date: `make db-status`
