# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SQL AI Agent is a full-stack application that translates natural language queries into SQL and executes them against a PostgreSQL database. The system uses OpenAI's LLM for SQL generation with a RAG-based knowledge base for improved accuracy.

**Stack:**
- Backend: FastAPI + SQLAlchemy (Python 3.9+)
- Frontend: React + TypeScript
- Database: SQLite (app data) + PostgreSQL (target queries)
- LLM: OpenAI GPT-4

## Development Commands

### Backend Server

```bash
# Start development server (with auto-reload)
python -m backend.app.main
# or
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# API docs available at:
# - http://localhost:8000/docs (Swagger)
# - http://localhost:8000/redoc (ReDoc)
```

### Database Management

```bash
# Initialize database with default users (admin/admin123, testuser/testpass123)
make db-init
# or
python3 scripts/init_db.py

# Initialize without default users
make db-init-clean

# Reset database (WARNING: deletes all data)
make db-reset

# Check migration status
make db-status

# Run pending migrations
make db-migrate

# Preview migrations (dry run)
make db-dry-run

# Open SQLite shell
make db-shell

# Generate TypeScript types from database schema
make generate-types
```

### Testing

```bash
# Run Python tests
make test
# or
pytest tests/ -v

# Run API integration tests
python test_api.py
# or
./test_api.sh

# Test specific endpoint
curl -X POST http://localhost:8000/api/queries \
  -H "Content-Type: application/json" \
  -d '{"natural_language_query": "Show all users"}'
```

### Cleanup

```bash
# Clean Python cache files and build artifacts
make clean
```

## Architecture

### Backend Structure

**Three-Layer Architecture:**
1. **API Layer** (`backend/app/api/`) - FastAPI route handlers
2. **Service Layer** (`backend/app/services/`) - Business logic
3. **Data Layer** (`backend/app/models/`) - SQLAlchemy ORM models

**Key Modules:**
- `backend/app/main.py` - FastAPI app initialization, middleware, CORS config
- `backend/app/config.py` - Pydantic settings from environment variables
- `backend/app/database.py` - SQLAlchemy engine, session management
- `backend/app/dependencies.py` - FastAPI dependencies (auth, db sessions)
- `backend/app/schemas/` - Pydantic DTOs for request/response validation
- `backend/app/models/` - SQLAlchemy models (User, Query, Session, etc.)
- `backend/app/services/` - Business logic services:
  - `auth_service.py` - Authentication, password hashing, JWT tokens
  - `query_service.py` - SQL generation, validation, execution workflow
- `backend/app/api/` - Route handlers:
  - `auth.py` - Login/logout endpoints
  - `queries.py` - Query submission, execution, history

### Frontend Structure

**Component-Based React Application:**
- `frontend/src/views/` - Page-level components (QueryInterfaceView)
- `frontend/src/components/` - Reusable UI components (Button, TextArea, Pagination, Toast, ErrorBoundary)
- `frontend/src/services/` - API client layer:
  - `apiClient.ts` - Base axios configuration with auth interceptors
  - `queryService.ts` - Query-related API calls
- `frontend/src/hooks/` - Custom React hooks
- `frontend/src/types/` - TypeScript type definitions:
  - `database.types.ts` - Auto-generated from database schema
  - `common.ts`, `models.ts`, `api.ts` - Application types
  - `utils.ts` - Type guards and utilities

### Database Architecture

**SQLite Application Database** (`sqlite.db`):
- `users` - User accounts with bcrypt password hashes, role-based access (admin/user)
- `sessions` - Session tracking for authentication with expiration
- `query_attempts` - History of natural language queries and generated SQL
- `query_results_manifest` - Metadata for query results (pagination, export)
- `schema_snapshots` - Cached PostgreSQL schema for LLM context
- `kb_examples_index` - Index of knowledge base SQL example files
- `metrics_rollup` - Weekly aggregated metrics

**Migration System:**
- SQL migrations in `migrations/*.sql` (timestamped)
- Migration runner: `python3 backend/app/migrations_runner.py`
- Managed via Makefile targets (`make db-migrate`, `make db-status`)

### Authentication Flow

1. User submits credentials to `POST /api/auth/login`
2. `AuthService` validates credentials and creates session
3. JWT token returned to client (stored in memory/localStorage)
4. Client includes token in `Authorization: Bearer <token>` header
5. `get_current_user` dependency validates token on protected routes
6. Role-based access: admins see all data, users see only their own queries

### Query Workflow

1. User submits natural language query via `POST /api/queries`
2. `QueryService` retrieves schema snapshot and knowledge base examples
3. OpenAI LLM generates SQL with RAG context
4. SQL validated (SELECT-only, no DDL/DML)
5. Query executed against PostgreSQL target database
6. Results paginated and stored in manifest
7. User can download results as CSV via export endpoint

### Type Synchronization

**Backend → Frontend:**
1. Database schema defined in SQLAlchemy models
2. `scripts/generate_types.py` reads schema
3. TypeScript types generated in `frontend/src/types/database.types.ts`
4. Run `make generate-types` after schema changes

**Pydantic DTOs Mirror TypeScript Types:**
- `backend/app/schemas/` defines request/response DTOs
- `frontend/src/types/api.ts` defines matching TypeScript interfaces
- Keep these in sync manually when adding new endpoints

## Environment Configuration

Copy `.env.example` to `.env` and configure:

```bash
# SQLite for app data
DATABASE_URL=sqlite:///./sqlite.db

# PostgreSQL for query execution (target database)
POSTGRES_URL=postgresql://user:pass@host:port/db

# OpenAI API key (required for SQL generation)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# JWT secret (change in production!)
SECRET_KEY=change-this-secret-key-in-production

# Session expiration
SESSION_EXPIRATION_HOURS=8
```

## Key Design Patterns

### Dependency Injection

FastAPI dependencies used for:
- Database sessions: `db: Session = Depends(get_db)`
- Current user: `user: User = Depends(get_current_user)`
- Settings: `settings: Settings = Depends(get_settings)`

### Service Layer Pattern

Business logic isolated in service classes:
- API routes are thin, delegate to services
- Services handle complex logic, transactions, external APIs
- Services are stateless, receive dependencies as parameters

### Schema Validation

All API endpoints use Pydantic schemas:
- Request validation with field constraints
- Response serialization with `from_attributes=True` for ORM models
- Custom validators for business rules

### Error Handling

- Pydantic validation errors → 422 Unprocessable Entity
- ValueError exceptions → 400 Bad Request (custom handler)
- Authentication failures → 401 Unauthorized
- Authorization failures → 403 Forbidden
- Service errors logged with context

### Security

- Passwords hashed with bcrypt (never stored plaintext)
- JWT tokens for stateless authentication
- SQL injection prevention: parameterized queries only, SELECT-only validation
- CORS configured for localhost:3000 and localhost:5173
- Security headers added via middleware (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection)

## Common Development Tasks

### Adding a New Endpoint

1. Define Pydantic request/response schemas in `backend/app/schemas/`
2. Add route handler in `backend/app/api/`
3. Implement business logic in `backend/app/services/`
4. Register router in `backend/app/main.py`
5. Add matching TypeScript types in `frontend/src/types/api.ts`
6. Create API service function in `frontend/src/services/`
7. Test with `curl` or `test_api.py`

### Adding a Database Table

1. Create SQLAlchemy model in `backend/app/models/`
2. Create SQL migration in `migrations/YYYYMMDDHHMMSS_description.sql`
3. Run `make db-migrate` to apply migration
4. Run `make generate-types` to update TypeScript types
5. Add corresponding Pydantic schema in `backend/app/schemas/`
6. Update service layer to interact with new model

### Working with Migrations

- Migrations are SQL files, not auto-generated
- Naming: `YYYYMMDDHHMMSS_description.sql`
- Each migration tracked in `migration_history` table
- Use `make db-status` to see which migrations are applied
- Use `make db-dry-run` to preview pending migrations
- Never edit applied migrations; create new ones instead

### Debugging

**Backend:**
- Set `DATABASE_ECHO=true` in `.env` to see SQL queries
- Check logs in console (configured in `main.py`)
- Use FastAPI docs at `/docs` for interactive testing

**Frontend:**
- API calls logged via axios interceptors
- Use browser DevTools Network tab
- Toast notifications show user-facing errors

## Project Status

The project is in active development with core functionality implemented:

**Completed:**
- ✅ Database schema and migrations system
- ✅ SQLAlchemy ORM models
- ✅ Authentication with JWT tokens
- ✅ Pydantic DTOs and TypeScript types
- ✅ FastAPI app with CORS and middleware
- ✅ Query submission API endpoint
- ✅ Frontend Query Interface View with form and results display
- ✅ API integration layer with axios client

**In Progress / TODO:**
- LLM integration with OpenAI (service stub exists)
- Knowledge base loading and RAG implementation
- PostgreSQL query execution
- CSV export functionality
- Admin endpoints for schema refresh
- Query history view in frontend

See git commit history and `.ai/*.md` files for detailed implementation plans.
