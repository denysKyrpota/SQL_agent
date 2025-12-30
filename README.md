# SQL AI Agent

A full-stack application that translates natural language queries into SQL and executes them against a PostgreSQL database. The system uses OpenAI's LLM for intelligent SQL generation with a RAG-based knowledge base for improved accuracy.

[![Tests](https://img.shields.io/badge/tests-179%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-89%25-brightgreen)](htmlcov/index.html)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.0%2B-61dafb)](https://reactjs.org/)

## 🚀 Features

### Core Functionality
- **Natural Language to SQL**: Convert plain English questions into SQL queries
- **Two-Stage SQL Generation**:
  - Stage 1: Table selection from schema
  - Stage 2: SQL generation with filtered schema + RAG examples
- **Query Execution**: Execute generated SQL against PostgreSQL with 30s timeout
- **Result Export**: Export query results to CSV (up to 10,000 rows)
- **Query History**: Track all queries with status, timing, and error details

### AI/ML Features
- **RAG-Based Knowledge Base**: Use similar SQL examples for better generation
- **Schema Optimization**: Select only relevant tables to reduce token usage
- **Retry Logic**: Automatic retry with exponential backoff for LLM failures
- **SQL Validation**: Ensure only SELECT queries, prevent SQL injection

### Authentication & Security
- **JWT Authentication**: Secure session management with bcrypt password hashing
- **Role-Based Access Control**: Admin and user roles
- **Session Management**: Configurable expiration, token revocation
- **CORS Protection**: Configured for allowed origins

## 🏗️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for SQLite (app data) and PostgreSQL (target queries)
- **OpenAI GPT-4** - LLM for SQL generation
- **Pydantic** - Data validation and serialization
- **bcrypt** - Password hashing
- **JWT** - Session token management

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type-safe development
- **Vite** - Fast build tool
- **Axios** - HTTP client with interceptors

### Database
- **SQLite** - Application data (users, sessions, query history)
- **PostgreSQL** - Target database for query execution

### Testing
- **pytest** - Test framework
- **pytest-cov** - Coverage reporting
- **pytest-asyncio** - Async test support
- **FastAPI TestClient** - API testing

## 📁 Project Structure

```
agent_sql/
├── backend/
│   └── app/
│       ├── api/              # FastAPI route handlers
│       │   ├── auth.py       # Login/logout endpoints
│       │   └── queries.py    # Query CRUD, execution, export
│       ├── models/           # SQLAlchemy ORM models
│       │   ├── user.py       # User, Session models
│       │   └── query.py      # QueryAttempt, QueryResultsManifest
│       ├── schemas/          # Pydantic DTOs
│       │   ├── auth.py       # Login request/response
│       │   ├── queries.py    # Query request/response
│       │   └── common.py     # Shared schemas
│       ├── services/         # Business logic layer
│       │   ├── auth_service.py              # Authentication
│       │   ├── query_service.py             # SQL generation workflow
│       │   ├── llm_service.py               # OpenAI integration
│       │   ├── knowledge_base_service.py    # RAG example loading
│       │   ├── schema_service.py            # PostgreSQL schema
│       │   ├── postgres_execution_service.py # Query execution
│       │   └── export_service.py            # CSV export
│       ├── config.py         # Pydantic settings
│       ├── database.py       # SQLAlchemy setup
│       ├── dependencies.py   # FastAPI dependencies
│       └── main.py          # App initialization
├── frontend/
│   └── src/
│       ├── views/           # Page-level components
│       ├── components/      # Reusable UI components
│       ├── services/        # API client layer
│       ├── hooks/           # Custom React hooks
│       └── types/           # TypeScript type definitions
├── tests/
│   ├── api/                 # API endpoint tests
│   ├── services/            # Service layer tests
│   └── conftest.py          # Pytest fixtures
├── migrations/              # SQL migrations
├── scripts/                 # Utility scripts
├── data/
│   ├── knowledge_base/      # SQL example files
│   └── schema/              # PostgreSQL schema snapshots
└── .env                     # Environment configuration
```

## ⚙️ Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 12+ (target database)
- OpenAI API key

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd agent_sql
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
```bash
DATABASE_URL=sqlite:///./sqlite.db
POSTGRES_URL=postgresql://user:pass@host:port/dbname
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
SECRET_KEY=your-secret-key-change-in-production
SESSION_EXPIRATION_HOURS=8
```

5. **Initialize database**
```bash
make db-init
# or
python scripts/init_db.py
```

This creates default users:
- Admin: `admin` / `admin123`
- User: `testuser` / `testpass123`

6. **Start backend server**
```bash
python -m backend.app.main
# or
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at:
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Start development server**
```bash
npm run dev
```

Frontend available at: http://localhost:5173

## 📊 Using Sample Data

This repository includes sample data to help you get started without connecting to a real PostgreSQL database.

### Sample Knowledge Base

The `data/knowledge_base/` directory contains sample SQL queries:
- `sample_employees_by_department.sql`
- `sample_orders_last_30_days.sql`
- `sample_product_inventory_status.sql`
- `sample_monthly_sales_summary.sql`

These demonstrate the expected format for knowledge base examples.

### Sample Schema

The `data/schema/` directory contains sample PostgreSQL schema files:
- `sample_tables.json` - List of available tables
- `sample_columns__data_types__and_nullable_status.json` - Column definitions
- `sample_primary_keys__system_catalog_version.json` - Primary key constraints
- `sample_foreign_key_relationships__source_→_target.json` - Foreign key relationships
- `sample_all_in_one_schema_overview__tables__columns__pks__fks__descriptions.json` - Complete schema

### Setting Up Your Own Data

**For Production Use:**

1. **Replace Sample Knowledge Base:**
   ```bash
   # Remove sample files
   rm data/knowledge_base/sample_*.sql

   # Add your own SQL examples
   cp your_examples/*.sql data/knowledge_base/
   ```

2. **Connect to Your PostgreSQL Database:**
   - Update `POSTGRES_URL` in `.env` with your database credentials
   - Generate schema snapshots:
     ```bash
     # Use the admin endpoint to refresh schema
     curl -X POST http://localhost:8000/api/admin/schema/refresh \
       -H "Authorization: Bearer <admin_token>"
     ```

3. **Generate Embeddings:**
   ```bash
   # Generate embeddings for your knowledge base examples
   curl -X POST http://localhost:8000/api/admin/knowledge-base/embeddings/generate \
     -H "Authorization: Bearer <admin_token>"
   ```

**Important Security Notes:**
- Never commit `.env` files with real credentials
- Never commit production schema files to public repositories
- Never commit production knowledge base SQL files containing business logic
- The `.gitignore` is configured to exclude real data:
  - `data/knowledge_base/*.sql` (except `sample_*.sql`)
  - `data/schema/*.json` (except `sample_*.json`)
  - `.env` and `.env.local`

## 🧪 Testing

### Run All Tests
```bash
make test
# or
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=backend/app --cov-report=html
# View report: open htmlcov/index.html
```

### Run Specific Tests
```bash
# API tests only
pytest tests/api/ -v

# Service tests only
pytest tests/services/ -v

# Single test file
pytest tests/api/test_auth.py -v

# Single test
pytest tests/api/test_auth.py::TestAuthLogin::test_login_success -v
```

### Test Coverage
Current coverage: **89%**

Key areas tested:
- ✅ Authentication (login, logout, sessions)
- ✅ Query generation (two-stage SQL generation)
- ✅ Query execution and result handling
- ✅ CSV export with size limits
- ✅ LLM service (prompt building, response parsing)
- ✅ Knowledge base loading
- ✅ Schema service
- ✅ Authorization and role-based access

## 📚 API Documentation

### Authentication

#### POST /api/auth/login
Login with username and password.

**Request:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "active": true
  },
  "session": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "expires_at": "2025-11-12T03:00:00Z"
  }
}
```

#### POST /api/auth/logout
Logout and revoke session.

**Headers:**
```
Authorization: Bearer <token>
```

### Queries

#### POST /api/queries
Submit natural language query and generate SQL.

**Request:**
```json
{
  "natural_language_query": "Show me all active users from the last 30 days"
}
```

**Response:**
```json
{
  "id": 42,
  "natural_language_query": "Show me all active users from the last 30 days",
  "generated_sql": "SELECT * FROM users WHERE active = true AND created_at >= NOW() - INTERVAL '30 days';",
  "status": "not_executed",
  "created_at": "2025-11-11T20:00:00Z",
  "generated_at": "2025-11-11T20:00:02Z",
  "generation_ms": 2150,
  "error_message": null
}
```

#### POST /api/queries/{id}/execute
Execute generated SQL against PostgreSQL.

**Response:**
```json
{
  "id": 42,
  "status": "success",
  "executed_at": "2025-11-11T20:00:05Z",
  "execution_ms": 150,
  "results": {
    "total_rows": 523,
    "page_size": 500,
    "page_count": 2,
    "columns": ["id", "username", "email", "created_at"],
    "rows": [[1, "alice", "alice@example.com", "2025-10-15"], ...]
  }
}
```

#### GET /api/queries/{id}/results?page=1
Get paginated results (500 rows per page).

#### GET /api/queries/{id}/export
Export results as CSV (max 10,000 rows).

#### GET /api/queries
List user's query history with pagination.

**Query Parameters:**
- `page` (default: 1)
- `page_size` (default: 20, max: 100)
- `status_filter` (optional: "success", "failed_generation", etc.)

#### POST /api/queries/{id}/rerun
Re-run historical query with fresh SQL generation.

## 🔧 Development

### Database Management

```bash
# Initialize database with default users
make db-init

# Initialize without default users
make db-init-clean

# Reset database (WARNING: deletes all data)
make db-reset

# Run migrations
make db-migrate

# Check migration status
make db-status

# Preview migrations (dry run)
make db-dry-run

# Open SQLite shell
make db-shell

# Generate TypeScript types from schema
make generate-types
```

### Adding a Migration

1. Create migration file:
```bash
touch migrations/20251111120000_add_user_preferences.sql
```

2. Write SQL:
```sql
-- migrations/20251111120000_add_user_preferences.sql
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    theme VARCHAR(20) DEFAULT 'light',
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

3. Run migration:
```bash
make db-migrate
```

### Code Quality

```bash
# Format code
black backend/
isort backend/

# Lint
flake8 backend/
pylint backend/

# Type checking
mypy backend/

# Clean Python cache
make clean
```

## 📊 Architecture

### Three-Layer Architecture

1. **API Layer** (`backend/app/api/`)
   - FastAPI route handlers
   - Request validation (Pydantic)
   - Response serialization
   - Error handling

2. **Service Layer** (`backend/app/services/`)
   - Business logic
   - External API calls (OpenAI)
   - Complex workflows
   - Transaction management

3. **Data Layer** (`backend/app/models/`)
   - SQLAlchemy ORM models
   - Database schema
   - Relationships

### SQL Generation Workflow

```
1. User submits natural language query
   ↓
2. QueryService retrieves schema snapshot
   ↓
3. LLMService Stage 1: Select relevant tables (max 10)
   ↓
4. Filter schema to selected tables only
   ↓
5. KnowledgeBaseService finds similar SQL examples (top 3)
   ↓
6. LLMService Stage 2: Generate SQL with context
   ↓
7. Validate SQL (SELECT-only, no DDL/DML)
   ↓
8. Return generated SQL to user
```

### Query Execution Flow

```
1. User requests execution of generated SQL
   ↓
2. PostgresExecutionService validates query
   ↓
3. Execute with 30-second timeout
   ↓
4. Store results in QueryResultsManifest
   ↓
5. Paginate results (500 rows per page)
   ↓
6. Return first page to user
```

## 🔐 Security

- **Password Hashing**: bcrypt with automatic salt generation
- **JWT Tokens**: Stateless authentication with expiration
- **SQL Injection Prevention**: Parameterized queries, SELECT-only validation
- **CORS**: Configured for specific origins
- **Session Revocation**: Logout invalidates tokens
- **Role-Based Access**: Admin can see all queries, users see only their own

## 🚧 Roadmap

- [ ] Frontend implementation completion
- [ ] Real-time query result streaming
- [ ] Query result caching
- [ ] Admin dashboard for metrics
- [ ] Query sharing and collaboration
- [ ] SQL query optimization suggestions
- [ ] Support for multiple PostgreSQL databases
- [ ] Scheduled queries
- [ ] Result visualization (charts, graphs)

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`make test`)
6. Commit your changes (`git commit -m 'feat: add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 🐛 Troubleshooting

### Backend Issues

**Database connection error:**
- Check `POSTGRES_URL` in `.env`
- Verify PostgreSQL is running
- Test connection: `psql $POSTGRES_URL`

**LLM generation slow:**
- Check `OPENAI_API_KEY` is valid
- Monitor OpenAI API status
- Consider using `gpt-3.5-turbo` for faster responses

**Migration errors:**
- Check migration history: `make db-status`
- Reset database: `make db-reset` (WARNING: deletes data)

### Frontend Issues

**API connection refused:**
- Verify backend is running on port 8000
- Check CORS configuration in `backend/app/main.py`

**Build errors:**
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (requires 16+)

## 📧 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation in `CLAUDE.md`
- Review API docs at http://localhost:8000/docs

---

Built with ❤️ using FastAPI, React, and OpenAI GPT-4
