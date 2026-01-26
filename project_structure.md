# SQL AI Agent - Project File Structure

## Root Directory Structure

```
agent_sql_public/
├── README.md
├── CLAUDE.md                      # Claude Code instructions
├── QUICK_START.md
├── TESTING.md
├── README_MIGRATIONS.md
├── .gitignore
├── .env.example
├── .env
├── Makefile                       # Database and development commands
├── pytest.ini
├── requirements.txt
├── backend/
├── frontend/
├── data/
├── docs/
├── scripts/
├── tests/                         # All tests (root level)
└── migrations/                    # SQL migration files
```

## Backend Directory (`backend/`)

```
backend/
└── app/
    ├── __init__.py
    ├── main.py                    # FastAPI application entry point
    ├── config.py                  # Settings (Pydantic BaseSettings)
    ├── database.py                # SQLite and PostgreSQL connections
    ├── dependencies.py            # FastAPI dependencies (auth, db sessions)
    ├── migrations_runner.py       # Migration execution logic
    │
    ├── models/                    # SQLAlchemy models
    │   ├── __init__.py
    │   ├── base.py                # Base model with common fields
    │   ├── user.py                # User authentication model
    │   ├── query.py               # Query attempts, results manifest
    │   ├── chat.py                # Conversations and messages
    │   ├── knowledge.py           # Knowledge base examples
    │   └── metrics.py             # Performance metrics
    │
    ├── schemas/                   # Pydantic schemas for API
    │   ├── __init__.py
    │   ├── auth.py                # Login, token, user schemas
    │   ├── queries.py             # Query request/response schemas
    │   ├── chat.py                # Chat/conversation schemas
    │   ├── admin.py               # Admin operation schemas
    │   ├── common.py              # Shared schemas (pagination, etc.)
    │   └── health.py              # Health check schemas
    │
    ├── api/                       # API route handlers
    │   ├── __init__.py
    │   ├── auth.py                # Authentication endpoints
    │   ├── queries.py             # Query submission and execution
    │   ├── chat.py                # Chat conversation endpoints
    │   └── admin.py               # Admin functions (schema/KB refresh)
    │
    ├── services/                  # Business logic services
    │   ├── __init__.py
    │   ├── auth_service.py        # Authentication and session logic
    │   ├── llm_service.py         # OpenAI/Azure OpenAI integration
    │   ├── knowledge_base_service.py  # RAG and KB management
    │   ├── schema_service.py      # Database schema caching/filtering
    │   ├── query_service.py       # Two-stage SQL generation
    │   ├── chat_service.py        # Conversation management
    │   ├── postgres_execution_service.py  # SQL execution
    │   └── export_service.py      # CSV export functionality
    │
    └── core/                      # Core utilities (if present)
        ├── __init__.py
        ├── security.py            # JWT token handling, password hashing
        └── exceptions.py          # Custom exception classes
```

## Frontend Directory (`frontend/`)

```
frontend/
├── public/
│   ├── index.html
│   └── vite.svg
│
├── src/
│   ├── main.tsx                   # React app entry point (Vite)
│   ├── App.tsx                    # Main app component
│   ├── index.css                  # Global styles
│   ├── vite-env.d.ts              # Vite type declarations
│   │
│   ├── components/                # Reusable UI components
│   │   ├── AppHeader/
│   │   │   └── index.tsx          # Application header with navigation
│   │   │
│   │   ├── Button/
│   │   │   └── index.tsx          # Reusable button component
│   │   │
│   │   ├── TextArea/
│   │   │   ├── index.tsx          # Custom textarea component
│   │   │   └── TextArea.module.css.d.ts
│   │   │
│   │   ├── ChatPanel/
│   │   │   ├── ChatPanel.tsx      # Chat conversation UI (right sidebar)
│   │   │   └── index.ts
│   │   │
│   │   ├── MessageBubble/
│   │   │   ├── MessageBubble.tsx  # Individual chat message display
│   │   │   └── index.ts
│   │   │
│   │   ├── Pagination/
│   │   │   └── index.tsx          # Results pagination controls
│   │   │
│   │   ├── Toast/
│   │   │   └── index.tsx          # Toast notification component
│   │   │
│   │   ├── ProtectedRoute/
│   │   │   └── index.tsx          # Route protection wrapper
│   │   │
│   │   └── ErrorBoundary/
│   │       └── index.tsx          # Error boundary for React errors
│   │
│   ├── views/                     # Page-level view components
│   │   ├── LoginView/
│   │   │   ├── index.tsx          # Login page
│   │   │   └── LoginView.module.css.d.ts
│   │   │
│   │   ├── QueryInterfaceView/
│   │   │   ├── index.tsx          # Main query interface orchestrator
│   │   │   ├── QueryInterfaceView.module.css.d.ts
│   │   │   ├── types.ts           # View-specific types
│   │   │   ├── components/
│   │   │   │   ├── QueryForm/
│   │   │   │   │   ├── index.tsx           # Natural language query input
│   │   │   │   │   ├── CharacterCount.tsx  # Input character counter
│   │   │   │   │   ├── ExampleQuestions.tsx # Example queries sidebar
│   │   │   │   │   └── QueryForm.module.css.d.ts
│   │   │   │   │
│   │   │   │   ├── SqlPreviewSection/
│   │   │   │   │   ├── index.tsx           # SQL display container
│   │   │   │   │   └── SqlPreview.tsx      # Syntax-highlighted SQL
│   │   │   │   │
│   │   │   │   ├── ResultsSection/
│   │   │   │   │   ├── index.tsx           # Results container
│   │   │   │   │   ├── ResultsTable.tsx    # Data table display
│   │   │   │   │   └── PerformanceMetrics.tsx  # Query performance stats
│   │   │   │   │
│   │   │   │   ├── ErrorAlert/
│   │   │   │   │   └── index.tsx           # Error message display
│   │   │   │   │
│   │   │   │   └── LoadingIndicator/
│   │   │   │       └── index.tsx           # Loading spinner
│   │   │   │
│   │   │   └── utils/
│   │   │       ├── errorMessages.ts        # Error message formatting
│   │   │       └── validation.ts           # Input validation
│   │   │
│   │   └── QueryHistoryView/
│   │       ├── index.tsx          # Query history page
│   │       ├── components/
│   │       │   ├── QueryFilters.tsx        # History filters
│   │       │   └── QueryHistoryTable.tsx   # History table
│   │       └── utils/
│   │           ├── dateUtils.ts            # Date formatting
│   │           └── statusUtils.tsx         # Status rendering
│   │
│   ├── context/                   # React context providers
│   │   └── AuthContext.tsx        # Global authentication state
│   │
│   ├── hooks/                     # Custom React hooks
│   │   └── useAuth.ts             # Authentication hook
│   │
│   ├── services/                  # API service functions
│   │   ├── index.ts               # Service exports
│   │   ├── apiClient.ts           # Axios client with interceptors
│   │   ├── authService.ts         # Authentication API calls
│   │   ├── queryService.ts        # Query-related API calls
│   │   ├── chatService.ts         # Chat/conversation API calls
│   │   └── adminService.ts        # Admin API calls
│   │
│   └── types/                     # TypeScript type definitions
│       ├── index.ts               # Type exports
│       ├── api.ts                 # API request/response types
│       ├── models.ts              # Data model types
│       ├── common.ts              # Shared types
│       ├── utils.ts               # Utility types
│       ├── database.types.ts      # Generated from backend schemas
│       └── css-modules.d.ts       # CSS module declarations
│
├── package.json
├── package-lock.json
├── tsconfig.json                  # TypeScript configuration
├── tsconfig.node.json
├── vite.config.ts                 # Vite build configuration
├── eslint.config.js               # ESLint configuration
└── .gitignore
```

## Data Directory (`data/`)

```
data/
├── README.md                      # Data directory documentation
│
├── knowledge_base/                # SQL example files for RAG
│   ├── activities_finished_today_with_truck_license_plate.sql
│   ├── current_drivers_status.sql
│   ├── current_year_delayed_activities_more_than_3_hours.sql
│   ├── deactivated_created_customers.sql
│   ├── driver_student_language_level.sql
│   ├── drivers_with_current_availability.sql
│   ├── drivers_with_expired_certificates.sql
│   └── embeddings.json            # Pre-computed embeddings (1536-dim)
│
├── schema/                        # PostgreSQL schema cache
│   └── [schema snapshots in JSON format]
│
├── app_data/                      # Application database
│   └── sqlite.db                  # SQLite database (created at runtime)
│
└── exports/                       # CSV export storage
    └── [generated CSV files]
```

## Tests Directory (`tests/`)

Located at **root level**, not inside backend.

```
tests/
├── __init__.py
├── conftest.py                    # Pytest configuration and fixtures
│
├── api/                           # API endpoint tests
│   ├── __init__.py
│   ├── test_auth.py               # Authentication endpoint tests
│   └── test_queries.py            # Query endpoint tests
│
└── services/                      # Service layer tests
    ├── __init__.py
    ├── test_auth_service.py       # Auth service tests
    ├── test_llm_service.py        # LLM service tests (mocked)
    ├── test_knowledge_base_service.py  # KB service tests
    ├── test_schema_service.py     # Schema service tests
    ├── test_query_service.py      # Query service tests
    ├── test_postgres_execution_service.py  # Execution tests
    └── test_export_service.py     # Export service tests
```

**Test Coverage:** 89% (179 tests passing)

## Migrations Directory (`migrations/`)

Located at **root level**. Uses custom SQL migration system (not Alembic).

```
migrations/
├── 20251026155227_initial_schema.sql
├── 20251107202924_add_results_json_columns.sql
├── 20251207000000_add_chat_tables.sql
└── 20251207000001_rename_message_metadata.sql
```

**Migration format:**
```sql
-- UP
[SQL statements for applying migration]

-- DOWN
[SQL statements for reverting migration]
```

## Scripts Directory (`scripts/`)

```
scripts/
├── init_db.py                     # Database initialization with users
├── create_migration.py            # Create new migration file
├── generate_types.py              # Generate TS types from Pydantic
├── generate_embeddings.py         # Generate KB embeddings
├── test_postgres_connection.py    # Test PostgreSQL connectivity
├── test_postgres_simple.py        # Simple PostgreSQL tests
└── test_rag.py                    # Test RAG system
```

## Documentation Directory (`docs/`)

```
docs/
├── [Project documentation files]
```

## Key Configuration Files

### Root Level Files

**`Makefile`** - Development commands
```makefile
db-init          # Initialize with default users
db-init-clean    # Initialize without default users
db-reset         # Reset database (deletes all data)
db-migrate       # Run pending migrations
db-status        # Show migration status
db-shell         # Open SQLite shell
generate-types   # Generate TypeScript types
test             # Run all tests
clean            # Remove cache files
```

**`.env.example`**
```env
# Database Configuration
DATABASE_URL=sqlite:///./data/app_data/sqlite.db
POSTGRES_URL=postgresql://user:password@host:port/dbname

# OpenAI Configuration (Standard)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.0

# Azure OpenAI Configuration (Optional)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-azure-api-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=your-embedding-deployment

# Authentication
SECRET_KEY=your-secret-key-here
SESSION_EXPIRATION_HOURS=8

# RAG Configuration
RAG_SIMILARITY_THRESHOLD=0.85

# PostgreSQL Execution
POSTGRES_TIMEOUT=30
```

**`requirements.txt`**
```txt
fastapi==0.115.4
uvicorn[standard]==0.32.0
sqlalchemy==2.0.36
psycopg2-binary==2.9.10
openai==1.54.4
numpy==1.26.4
scipy==1.14.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
pydantic==2.10.2
pydantic-settings==2.6.1
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==6.0.0
httpx==0.27.2
```

**`pytest.ini`**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
```

## Key Architecture Patterns

### 1. **Two-Tier Database System**
- **SQLite** (`data/app_data/sqlite.db`): Application data (users, sessions, conversations, query history)
- **PostgreSQL** (external): Target database for user queries (read-only access)

### 2. **Two-Stage SQL Generation**
```
QueryService.create_query_attempt()
  ├─> Stage 1: LLMService.select_relevant_tables() → 5-10 tables from 279
  ├─> Stage 2: LLMService.generate_sql() → SQL query
  └─> PostgresExecutionService.execute_query() → Results
```

### 3. **RAG System**
- Knowledge base: 7 `.sql` example files
- Embeddings: Pre-computed (1536-dim vectors) in `embeddings.json`
- Similarity threshold: 0.85 for direct KB match (bypasses LLM)

### 4. **Chat Conversation System**
- Database: `conversations` (1) → `messages` (N)
- Messages link to `query_attempts` when SQL is generated
- Full conversation history passed to LLM for context

### 5. **Frontend Architecture**
- **TypeScript + React + Vite**
- Views-based routing (not pages)
- Context API for auth state
- Axios-based API client with interceptors
- CSS Modules for styling

### 6. **Service Layer Pattern**
All business logic in `backend/app/services/`, not in API routes.
API routes delegate to services for clean separation of concerns.

### 7. **Type Safety**
- Backend: Pydantic schemas
- Frontend: TypeScript types generated from Pydantic via `make generate-types`

## Development Workflow

### Backend Development
```bash
# Start development server
python -m backend.app.main
# or with auto-reload
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
make test                    # All tests with coverage
pytest tests/ -v             # Verbose output
pytest tests/api/test_auth.py::TestAuthLogin::test_login_success -v  # Single test
```

### Frontend Development
```bash
cd frontend
npm install                  # Install dependencies
npm run dev                  # Dev server (http://localhost:5173)
npm run build                # Production build
npm run type-check           # TypeScript checking
npm run lint                 # ESLint
```

### Database Management
```bash
make db-init                 # Initialize with default test users
make db-migrate              # Run pending migrations
make db-status               # Check migration status
make db-shell                # SQLite CLI
```

### Type Generation
```bash
make generate-types          # Generate frontend/src/types/database.types.ts
```

## Key Design Principles

### 1. **Separation of Concerns**
- API routes handle HTTP only
- Services contain all business logic
- Models define data structure
- Schemas validate API contracts

### 2. **Type Safety End-to-End**
- Pydantic schemas in backend
- Generated TypeScript types in frontend
- Consistent contracts across stack

### 3. **Testing Strategy**
- Service layer testing with mocked dependencies
- API endpoint testing with test client
- 89% code coverage target

### 4. **Security Focus**
- JWT-based authentication
- Session management with expiration
- SQL injection prevention (SELECT-only validation)
- Password hashing with bcrypt

### 5. **Scalability Preparation**
- Modular service architecture
- Stateless API design
- Efficient schema caching
- RAG system for improved query quality

### 6. **Developer Experience**
- Makefile for common tasks
- Comprehensive documentation in CLAUDE.md
- Clear project structure
- Type generation automation

This structure supports a production-ready text-to-SQL application with robust architecture, comprehensive testing, and clear separation of concerns.
