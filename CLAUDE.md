# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SQL AI Agent - A production-ready text-to-SQL application that converts natural language questions into PostgreSQL queries using GPT-4 and Retrieval-Augmented Generation (RAG). The system features a two-stage SQL generation pipeline with intelligent table selection and context-aware chat capabilities.

**Architecture:** Three-tier (React frontend, FastAPI backend, dual databases)
**Target Database:** PostgreSQL (read-only)
**Application Database:** SQLite (users, sessions, query history, conversations)

## Development Commands

### Backend (Python)

```bash
# Database management (Makefile)
make db-init          # Initialize with default test users
make db-init-clean    # Initialize without default users
make db-reset         # Reset database (WARNING: deletes all data)
make db-migrate       # Run pending migrations
make db-status        # Show migration status
make db-shell         # Open SQLite shell
make generate-types   # Generate TypeScript types from Pydantic schemas

# Development server
python -m backend.app.main
# or with auto-reload
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Testing
make test                    # Run all tests (179 tests, 89% coverage)
pytest tests/ -v             # Verbose output
pytest tests/api/test_auth.py::TestAuthLogin::test_login_success -v  # Single test
pytest tests/ --cov=backend/app --cov-report=html  # Coverage report

# Code quality
black backend/               # Format
flake8 backend/              # Lint
mypy backend/                # Type check
make clean                   # Remove cache files
```

### Frontend (Node.js)

```bash
cd frontend

npm install                  # Install dependencies
npm run dev                  # Development server (http://localhost:5173)
npm run build                # Production build
npm run preview              # Preview production build
npm run lint                 # ESLint
npm run type-check           # TypeScript checking
```

## Core Architecture

### Two-Stage SQL Generation Pipeline

The system uses a sophisticated two-stage process to handle large database schemas (279 tables):

**Stage 1: Table Selection** (`LLMService.select_relevant_tables()`)
- Input: All table names (279) + user question + optional conversation history
- LLM: GPT-4 with temperature=0.0 (deterministic)
- Output: 5-10 most relevant tables
- Purpose: Reduce context size to fit token limits

**Stage 2: SQL Generation** (`LLMService.generate_sql()`)
- Input: Filtered schema + user question + top-3 similar KB examples + conversation history
- LLM: GPT-4 with configurable temperature (default 0.0)
- Output: PostgreSQL SELECT query
- Validation: SELECT-only enforcement, forbidden keyword detection

**Key Services Interaction:**
```
QueryService.create_query_attempt()
  ├─> SchemaService.get_table_names() → 279 tables
  ├─> LLMService.select_relevant_tables() → Stage 1
  ├─> SchemaService.filter_schema_by_tables() → Filtered schema
  ├─> LLMService.generate_embedding() → Embedding for RAG
  ├─> KnowledgeBaseService.find_similar_examples() → Top-3 examples
  │   └─> If similarity >= 0.85, return KB example directly
  └─> LLMService.generate_sql() → Stage 2
```

### RAG (Retrieval-Augmented Generation) System

**Knowledge Base:**
- Location: `data/knowledge_base/` (7 .sql example files)
- Embeddings: Persisted in `embeddings.json` (1536-dim vectors)
- Model: text-embedding-3-small
- Similarity: Cosine similarity, top-3 examples
- Threshold: 0.85 for direct KB match (bypasses LLM)

**Refresh Commands:**
```bash
# Generate new embeddings for KB examples
curl -X POST http://localhost:8000/api/admin/knowledge-base/embeddings/generate \
  -H "Authorization: Bearer <admin_token>"

# Reload KB without restart
curl -X POST http://localhost:8000/api/admin/knowledge-base/refresh \
  -H "Authorization: Bearer <admin_token>"
```

### Chat Conversation System

The chat system maintains conversation context across messages:

**Architecture:**
- Database: `conversations` (1) → `messages` (N)
- Messages link to `query_attempts` when SQL is generated
- Full conversation history passed to LLM for context-aware generation
- Supports editing (creates branches) and regeneration (creates siblings)
- Context window: MAX_CONTEXT_MESSAGES = 10

**Key Flow:**
```
ChatService.send_message()
  ├─> Create/retrieve conversation
  ├─> Store user message
  ├─> Build conversation history (last 10 messages)
  ├─> LLMService.select_relevant_tables(conversation_history=history)
  ├─> LLMService.generate_sql(conversation_history=history)
  ├─> Create query_attempt linked to assistant message
  └─> Return both user and assistant messages
```

### Database Schema

**SQLite (Application Data):**
- `users` - Authentication (bcrypt passwords, role-based access)
- `sessions` - 8-hour expiration, revokable tokens
- `query_attempts` - Complete lifecycle tracking (not_executed → success/failed)
- `query_results_manifest` - JSON storage, 500 rows/page, 10K export limit
- `conversations` + `messages` - Chat threads with query linking

**PostgreSQL (Target Database):**
- Read-only access
- 279 tables total
- Schema loaded from JSON snapshots in `data/schema/`
- Execution timeout: 30 seconds

## Important Code Patterns

### Service Layer Communication

All business logic lives in services (`backend/app/services/`), not API routes:

```python
# Good: API route delegates to service
@router.post("/queries")
async def create_query(request: QueryRequest, db: Session = Depends(get_db)):
    return await query_service.create_query_attempt(db, request)

# Bad: Business logic in API route
@router.post("/queries")
async def create_query(request: QueryRequest, db: Session = Depends(get_db)):
    # Don't put LLM calls, schema filtering, etc. here
```

### Async/Await Consistency

**Critical:** Always await async functions, especially:
- `LLMService.select_relevant_tables()` - Returns coroutine
- `LLMService.generate_sql()` - Returns coroutine
- `LLMService.generate_embedding()` - Returns coroutine
- `KnowledgeBaseService.find_similar_examples()` - Returns tuple[list[KBExample], float]

```python
# Correct
similar_kb_examples, max_sim = await kb.find_similar_examples(question)
sql_examples = [ex.sql for ex in similar_kb_examples]

# Wrong - creates coroutine object instead of data
similar_kb_examples = kb.find_similar_examples(question)  # Missing await!
```

### Parameter Naming Conventions

**LLMService method signatures:**
- `select_relevant_tables(table_names=...)` - NOT `all_table_names`
- `generate_sql(schema_text=...)` - NOT `schema`

```python
# Correct
selected_tables = await llm.select_relevant_tables(
    table_names=all_tables,  # table_names parameter
    question=user_question
)

filtered_schema = schema.filter_schema_by_tables(selected_tables)

sql = await llm.generate_sql(
    schema_text=filtered_schema,  # schema_text parameter
    question=user_question,
    examples=sql_examples
)
```

### Frontend Prop Synchronization

**React pattern:** When passing state as prop that changes after initial render, sync with useEffect:

```typescript
// ChatPanel - syncs parent's conversationId prop with internal state
useEffect(() => {
  if (initialConversationId !== undefined && initialConversationId !== conversationId) {
    setConversationId(initialConversationId);
  }
}, [initialConversationId]);
```

## Configuration

**Environment Variables (.env):**
```bash
# Database
DATABASE_URL=sqlite:///./data/app_data/sqlite.db
POSTGRES_URL=postgresql://user:pass@host:port/dbname

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
RAG_SIMILARITY_THRESHOLD=0.85

# Azure OpenAI (Optional - if set, will use Azure instead of OpenAI)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=your-embedding-deployment

# Auth
SECRET_KEY=change-in-production
SESSION_EXPIRATION_HOURS=8

# Performance
POSTGRES_TIMEOUT=30
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.0
```

**Settings managed via Pydantic:** See `backend/app/config.py`

## Testing Strategy

**Coverage: 89% (179 tests passing)**

```bash
# Test categories
tests/api/           # API endpoint tests (auth, queries, chat, admin)
tests/services/      # Service layer tests (query, llm, kb, schema, postgres, export)
```

**Key fixtures (conftest.py):**
- `test_db` - In-memory SQLite database (function-scoped isolation)
- `client` - FastAPI TestClient with test DB
- `authenticated_client` - Pre-authenticated test user
- `admin_client` - Admin user for protected endpoints
- `sample_query_attempt`, `executed_query_with_results`, `failed_query` - Query fixtures

**Mock patterns:**
```python
# Mock OpenAI to avoid rate limits and costs
@pytest.fixture
def mock_openai(monkeypatch):
    async def mock_select_tables(*args, **kwargs):
        return ["table1", "table2"]

    async def mock_generate_sql(*args, **kwargs):
        return "SELECT * FROM table1;"

    monkeypatch.setattr(LLMService, "select_relevant_tables", mock_select_tables)
    monkeypatch.setattr(LLMService, "generate_sql", mock_generate_sql)
```

## Database Migrations

**Creating migrations:**
```bash
# Create new migration
python scripts/create_migration.py "Add new column to users"
# Creates: migrations/008_add_new_column_to_users.sql

# Run migrations
make db-migrate

# Check status
make db-status
```

**Migration format:**
```sql
-- migrations/008_example.sql
-- UP
ALTER TABLE users ADD COLUMN new_field TEXT;

-- DOWN
ALTER TABLE users DROP COLUMN new_field;
```

## Admin Endpoints

```bash
# Refresh schema cache (reload from PostgreSQL)
POST /api/admin/schema/refresh

# Reload knowledge base examples
POST /api/admin/knowledge-base/refresh

# Generate embeddings for KB examples
POST /api/admin/knowledge-base/embeddings/generate
```

All admin endpoints require admin role authentication.

## Common Workflows

### Adding a New API Endpoint

1. Define Pydantic schemas in `backend/app/schemas/`
2. Create route handler in `backend/app/api/`
3. Implement business logic in `backend/app/services/`
4. Add tests in `tests/api/` and `tests/services/`
5. Run `make generate-types` to update TypeScript types
6. Implement frontend service method in `frontend/src/services/`
7. Update UI components as needed

### Adding New Knowledge Base Examples

1. Create `.sql` file in `data/knowledge_base/`
2. Format: `-- Title: <title>\n-- Description: <desc>\n<SQL>`
3. Generate embeddings: `POST /api/admin/knowledge-base/embeddings/generate`
4. Restart backend to load new examples

### Debugging SQL Generation Issues

**Check logs for:**
- Stage 1 selected tables (should be 5-10)
- Stage 2 filtered schema size (check token count)
- KB similarity scores (>0.85 means direct match)
- LLM responses and validation errors

**Common issues:**
- Wrong tables selected → Improve table selection prompt
- Forbidden keywords detected → Check `_extract_sql_from_response()` validation
- Timeout → Reduce `POSTGRES_TIMEOUT` or optimize query
- Rate limit → Retry logic built-in (exponential backoff)

## Architecture Decision Records

**Why two-stage SQL generation?**
- Token limits: 279 tables exceed GPT-4 context window
- Solution: Stage 1 selects relevant tables, Stage 2 generates SQL with focused schema

**Why SQLite + PostgreSQL dual databases?**
- PostgreSQL: Target database for user queries (read-only)
- SQLite: Simpler for app data (users, sessions, history)
- Separation of concerns: App logic vs. user data

**Why persist embeddings in JSON?**
- Avoid OpenAI API costs on every server restart
- Fast startup: Load pre-computed embeddings
- Manual refresh when KB changes

**Why conversation history in LLM calls?**
- Context-aware refinements: "add WHERE clause", "show only top 10"
- Natural conversation flow without repeating full question
- Enables iterative query development
