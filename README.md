# SQL AI Agent

A production-ready text-to-SQL application that converts natural language questions into PostgreSQL queries using GPT-4 and Retrieval-Augmented Generation (RAG).

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)
![React](https://img.shields.io/badge/React-18.2+-61dafb.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)
![Test Coverage](https://img.shields.io/badge/coverage-89%25-brightgreen.svg)

## Features

- 🤖 **Intelligent SQL Generation** - Two-stage pipeline for accurate query generation from natural language
- 💬 **Conversational Interface** - Chat-based UI with context-aware refinements
- 📚 **RAG System** - Knowledge base with semantic search for improved query quality
- 🔒 **Secure Authentication** - Session-based auth with role-based access control
- 📊 **Query History** - Track and re-run previous queries
- 🎯 **Smart Schema Filtering** - Handles large databases (279+ tables) efficiently
- 🔄 **Real-time Execution** - Execute generated SQL and view results instantly
- 📥 **CSV Export** - Export query results with configurable limits
- ☁️ **Azure OpenAI Support** - Works with both OpenAI and Azure OpenAI

## Architecture

**Stack:**
- **Frontend:** React 18 + TypeScript + Vite
- **Backend:** FastAPI + Python 3.11+
- **Databases:**
  - SQLite (application data: users, sessions, query history)
  - PostgreSQL (target database for queries - read-only)
- **AI/ML:** OpenAI GPT-4 or Azure OpenAI

**Key Components:**

```
┌─────────────────┐
│  React Frontend │
│   (TypeScript)  │
└────────┬────────┘
         │ HTTP/REST
┌────────▼────────┐
│  FastAPI Backend│
│    (Python)     │
├─────────────────┤
│  Two-Stage SQL  │
│   Generation    │
│  ┌───────────┐  │
│  │  Stage 1  │  │  Select relevant tables (5-10 from 279)
│  │  Table    │  │
│  │ Selection │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │  Stage 2  │  │  Generate SQL with filtered schema
│  │    SQL    │  │  + RAG examples
│  │ Generation│  │
│  └───────────┘  │
└────────┬────────┘
         │
    ┌────▼─────┐
    │PostgreSQL│ (Read-only)
    └──────────┘
```

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **PostgreSQL** (your target database)
- **OpenAI API key** or **Azure OpenAI** credentials

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/denysKyrpota/SQL_agent.git
cd SQL_agent
```

### 2. Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Required: DATABASE_URL, POSTGRES_URL, OPENAI_API_KEY or Azure credentials

# Initialize database
make db-init
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Start Backend Server

```bash
# From project root
python -m backend.app.main

# Or with auto-reload
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Access the Application

- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs
- **Default Login:** Use credentials created by `make db-init` (see setup instructions)

## Configuration

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_URL=sqlite:///./data/app_data/sqlite.db
POSTGRES_URL=postgresql://user:password@localhost:5432/your_database

# OpenAI Configuration (Standard)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_TEMPERATURE=0.0

# OR Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Authentication
SECRET_KEY=your-secret-key-here-change-in-production
SESSION_EXPIRATION_HOURS=8

# RAG Settings
RAG_SIMILARITY_THRESHOLD=0.85

# Performance
POSTGRES_TIMEOUT=30
OPENAI_MAX_TOKENS=1000
```

## Data Setup

### Create Your Data Folder

The `data/` folder contains sensitive information and is not in version control. Use the example structure:

```bash
# Copy example structure
cp -r data_example data

# Add your SQL examples to data/knowledge_base/
# Each file should contain one SQL query with title/description
```

### Knowledge Base Format

Create `.sql` files in `data/knowledge_base/`:

```sql
-- Title: Get active users from last 30 days
-- Description: Retrieve users who logged in within the past month

SELECT
    user_id,
    username,
    email,
    last_login
FROM users
WHERE
    last_login >= CURRENT_DATE - INTERVAL '30 days'
    AND status = 'active'
ORDER BY last_login DESC;
```

### Generate Embeddings

After adding knowledge base examples:

```bash
# Start the server, then:
curl -X POST http://localhost:8000/api/admin/knowledge-base/embeddings/generate \
  -H "Authorization: Bearer <admin_token>"
```

## Usage

### 1. Login

Access http://localhost:5173 and login with your credentials.

### 2. Ask Questions in Natural Language

```
"Show me all active users from the last 30 days"
"What are the top 10 products by revenue this year?"
"List customers who made purchases over $1000"
```

### 3. Review Generated SQL

The system will:
1. Select relevant tables from your schema
2. Find similar examples from knowledge base
3. Generate optimized SQL query
4. Display the query for review

### 4. Execute and View Results

- Click "Execute" to run the query
- View paginated results (500 rows per page)
- Export to CSV (up to 10,000 rows)

### 5. Refine in Chat

Continue the conversation:
```
"Add a WHERE clause for active users only"
"Sort by date descending"
"Show only top 10 results"
```

## Development

### Database Management

```bash
make db-init          # Initialize with default users
make db-init-clean    # Initialize without default users
make db-reset         # Reset database (deletes all data)
make db-migrate       # Run pending migrations
make db-status        # Show migration status
make db-shell         # Open SQLite shell
```

### Type Generation

After modifying Pydantic schemas:

```bash
make generate-types   # Generate TypeScript types
```

### Testing

```bash
# Run all tests
make test

# Run with coverage
pytest tests/ --cov=backend/app --cov-report=html

# Run specific test
pytest tests/api/test_auth.py::TestAuthLogin::test_login_success -v
```

**Test Coverage:** 89% (179 tests)

### Code Quality

```bash
# Format code
black backend/

# Lint
flake8 backend/

# Type check
mypy backend/
```

## Project Structure

```
SQL_agent/
├── backend/
│   └── app/
│       ├── api/              # API route handlers
│       ├── models/           # SQLAlchemy models
│       ├── schemas/          # Pydantic schemas
│       ├── services/         # Business logic
│       └── main.py           # FastAPI app
├── frontend/
│   └── src/
│       ├── components/       # React components
│       ├── views/            # Page-level views
│       ├── services/         # API clients
│       └── types/            # TypeScript types
├── data/                     # Your data (not in git)
│   ├── knowledge_base/       # SQL examples + embeddings
│   ├── schema/               # PostgreSQL schema cache
│   └── app_data/             # SQLite database
├── data_example/             # Example data structure
├── migrations/               # SQL migration files
├── tests/                    # Test suite
└── scripts/                  # Utility scripts
```

See [project_structure.md](project_structure.md) for detailed structure.

## How It Works

### Two-Stage SQL Generation

**Stage 1: Table Selection**
- Input: All table names + user question
- LLM selects 5-10 most relevant tables
- Reduces context size for efficient processing

**Stage 2: SQL Generation**
- Input: Filtered schema + question + RAG examples
- Finds top-3 similar queries from knowledge base
- Generates optimized PostgreSQL query
- If similarity > 0.85, returns KB example directly

### RAG System

1. User question → embedding (1536-dim vector)
2. Cosine similarity search against knowledge base
3. Top-3 most similar examples added to context
4. LLM uses examples to generate accurate SQL

### Chat Context

- Maintains full conversation history
- LLM receives previous Q&A for context
- Enables refinements: "add WHERE", "top 10", etc.
- Supports editing (creates branches) and regeneration

## API Documentation

Interactive API documentation available at:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

```bash
# Authentication
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me

# Queries
POST   /api/queries              # Create query attempt
POST   /api/queries/{id}/execute # Execute query
GET    /api/queries/{id}         # Get query details
GET    /api/queries              # List query history

# Chat
POST   /api/chat/messages        # Send chat message
GET    /api/conversations/{id}   # Get conversation

# Admin
POST   /api/admin/schema/refresh
POST   /api/admin/knowledge-base/refresh
POST   /api/admin/knowledge-base/embeddings/generate
```

## Deployment

### Environment Variables

Ensure all production credentials are set:
- Change `SECRET_KEY` to a secure random value
- Use production database URLs
- Set appropriate CORS origins
- Configure session expiration

### Database

```bash
# Run migrations
make db-migrate

# Create admin user (if not using db-init)
python scripts/init_db.py --no-defaults
```

### Frontend Build

```bash
cd frontend
npm run build
# Deploy dist/ folder to your hosting service
```

## Troubleshooting

### Server Won't Start

```bash
# Check dependencies
pip list | grep fastapi

# Reinstall
pip install -r requirements.txt
```

### Database Errors

```bash
# Check migration status
make db-status

# Reset database (WARNING: deletes all data)
make db-reset
make db-init
```

### OpenAI API Issues

- Verify API key in `.env`
- Check rate limits and quotas
- For Azure: ensure endpoint, key, and deployment are correct

### Frontend Build Errors

```bash
# Clear cache
rm -rf node_modules package-lock.json
npm install

# Type check
npm run type-check
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow existing code patterns (see [CLAUDE.md](CLAUDE.md))
- Add tests for new features
- Run `make test` before committing
- Use `black` for Python formatting
- Update TypeScript types after schema changes

## Security

- ⚠️ **Never commit the `data/` folder** - contains sensitive business data
- ⚠️ **Never commit `.env` file** - contains API keys and secrets
- ⚠️ Change default passwords in production
- ⚠️ Use HTTPS in production
- ⚠️ Review generated SQL before execution (SELECT-only enforced)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [React](https://react.dev/) and [Vite](https://vitejs.dev/)
- AI capabilities by [OpenAI](https://openai.com/)

## Support

For issues and questions:
- Check [CLAUDE.md](CLAUDE.md) for development guidance
- Review [TESTING.md](TESTING.md) for testing procedures
- Open an issue on GitHub

---

**Built with ❤️ for seamless text-to-SQL conversion**
