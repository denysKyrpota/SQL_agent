# SQL AI Agent MVP - Project File Structure

## Root Directory Structure

```
sql-ai-agent/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── backend/
├── frontend/
├── data/
├── docs/
└── scripts/
```

## Backend Directory (`backend/`)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application entry point
│   ├── config.py                   # Configuration and environment variables
│   ├── database.py                 # Database connections and setup
│   ├── dependencies.py             # FastAPI dependencies (auth, db sessions)
│   │
│   ├── models/                     # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py                 # User model for authentication
│   │   └── query_history.py        # Query history model
│   │
│   ├── schemas/                    # Pydantic schemas for API
│   │   ├── __init__.py
│   │   ├── auth.py                 # Login, token schemas
│   │   ├── query.py                # Query request/response schemas
│   │   └── history.py              # History schemas
│   │
│   ├── api/                        # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py                 # Authentication endpoints
│   │   ├── query.py                # Query submission and execution
│   │   ├── history.py              # Query history endpoints
│   │   └── admin.py                # Admin functions (schema refresh)
│   │
│   ├── services/                   # Business logic services
│   │   ├── __init__.py
│   │   ├── auth_service.py         # Authentication logic
│   │   ├── llm_service.py          # OpenAI integration
│   │   ├── knowledge_base.py       # Knowledge base management
│   │   ├── schema_service.py       # Database schema handling
│   │   ├── query_service.py        # Query generation and execution
│   │   └── export_service.py       # CSV export functionality
│   │
│   ├── core/                       # Core utilities
│   │   ├── __init__.py
│   │   ├── security.py             # JWT token handling, password hashing
│   │   ├── exceptions.py           # Custom exception classes
│   │   └── logging.py              # Logging configuration
│   │
│   └── utils/                      # Utility functions
│       ├── __init__.py
│       ├── embeddings.py           # Embedding generation and similarity
│       ├── sql_validator.py        # SQL validation (SELECT-only)
│       └── file_utils.py           # File operations for knowledge base
│
├── tests/                          # Backend tests
│   ├── __init__.py
│   ├── conftest.py                 # Pytest configuration
│   ├── test_auth.py
│   ├── test_query.py
│   └── test_services/
│       ├── test_llm_service.py
│       └── test_query_service.py
│
└── alembic/                        # Database migrations
    ├── versions/
    ├── env.py
    └── script.py.mako
```

## Frontend Directory (`frontend/`)

```
frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
│
├── src/
│   ├── index.js                    # React app entry point
│   ├── App.js                      # Main app component
│   ├── index.css                   # Global styles
│   │
│   ├── components/                 # Reusable UI components
│   │   ├── Layout/
│   │   │   ├── Header.js           # Navigation header
│   │   │   ├── Sidebar.js          # Navigation sidebar (if needed)
│   │   │   └── Layout.js           # Main layout wrapper
│   │   │
│   │   ├── Auth/
│   │   │   ├── LoginForm.js        # Login form component
│   │   │   └── ProtectedRoute.js   # Route protection wrapper
│   │   │
│   │   ├── Query/
│   │   │   ├── QueryInput.js       # Natural language query input
│   │   │   ├── QueryExamples.js    # Example queries display
│   │   │   ├── SqlPreview.js       # SQL syntax highlighting display
│   │   │   ├── QueryStatus.js      # Processing status display
│   │   │   └── ExecuteButton.js    # Query execution button
│   │   │
│   │   ├── Results/
│   │   │   ├── ResultsTable.js     # Query results display
│   │   │   ├── Pagination.js       # Results pagination
│   │   │   ├── ExportButton.js     # CSV export functionality
│   │   │   └── ErrorMessage.js     # Error display component
│   │   │
│   │   ├── History/
│   │   │   ├── HistoryList.js      # Query history list
│   │   │   ├── HistoryItem.js      # Individual history entry
│   │   │   └── RerunButton.js      # Re-run query functionality
│   │   │
│   │   └── Common/
│   │       ├── LoadingSpinner.js   # Loading indicator
│   │       ├── Button.js           # Reusable button component
│   │       └── Modal.js            # Modal dialog component
│   │
│   ├── pages/                      # Page components
│   │   ├── LoginPage.js            # Login page
│   │   ├── QueryPage.js            # Main query interface
│   │   └── HistoryPage.js          # Query history page
│   │
│   ├── hooks/                      # Custom React hooks
│   │   ├── useAuth.js              # Authentication hook
│   │   ├── useQuery.js             # Query submission hook
│   │   └── useApi.js               # API communication hook
│   │
│   ├── services/                   # API service functions
│   │   ├── api.js                  # Base API configuration
│   │   ├── authService.js          # Authentication API calls
│   │   ├── queryService.js         # Query-related API calls
│   │   └── historyService.js       # History API calls
│   │
│   ├── context/                    # React context providers
│   │   ├── AuthContext.js          # Authentication context
│   │   └── QueryContext.js         # Query state context
│   │
│   ├── utils/                      # Frontend utilities
│   │   ├── constants.js            # App constants
│   │   ├── helpers.js              # Helper functions
│   │   └── storage.js              # Local storage utilities
│   │
│   └── styles/                     # CSS modules/styled components
│       ├── components/
│       ├── pages/
│       └── globals.css
│
├── package.json
├── package-lock.json
└── .gitignore
```

## Data Directory (`data/`)

```
data/
├── knowledge_base/                 # SQL example files
│   ├── customers_revenue.sql       # Example: customer revenue queries
│   ├── sales_analysis.sql          # Example: sales analysis queries
│   ├── user_activity.sql           # Example: user activity queries
│   └── ...                        # 10-20 more example files
│
├── schema/                         # Database schema definitions
│   ├── database_schema.json        # Main database schema
│   └── schema_backup.json          # Schema backup
│
├── app_data/                       # Application database
│   └── app.db                      # SQLite database (created at runtime)
│
└── exports/                        # CSV export storage (optional)
    └── .gitkeep
```

## Documentation Directory (`docs/`)

```
docs/
├── README.md                       # Project overview
├── setup.md                       # Setup and installation guide
├── api.md                         # API documentation
├── deployment.md                  # Deployment instructions
├── knowledge_base.md              # Knowledge base management
└── troubleshooting.md             # Common issues and solutions
```

## Scripts Directory (`scripts/`)

```
scripts/
├── setup_dev.sh                   # Development environment setup
├── run_tests.sh                   # Test execution script
├── build_docker.sh               # Docker build script
├── init_db.py                     # Database initialization
└── load_knowledge_base.py         # Knowledge base loading script
```

## Key Configuration Files

### Root Level Files

**`.env.example`**
```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/production_db
SQLITE_URL=sqlite:///./data/app_data/app.db

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Authentication
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_HOURS=8

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
MAX_CONCURRENT_USERS=10

# Admin Users (format: username:password_hash)
ADMIN_USERS=admin:$2b$12$example_hash
REGULAR_USERS=user1:$2b$12$example_hash,user2:$2b$12$example_hash
```

**`requirements.txt`**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
openai==1.3.5
numpy==1.24.3
scipy==1.11.4
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
pydantic==2.5.0
pydantic-settings==2.1.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

**`docker-compose.yml`**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/sql_ai_agent
      - SQLITE_URL=sqlite:///./data/app_data/app.db
    volumes:
      - ./data:/app/data
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - web

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: sql_ai_agent
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## Key Design Principles

### 1. **Separation of Concerns**
- Clear separation between API logic, business logic, and data access
- Frontend components are focused and reusable
- Services handle all business logic

### 2. **Scalability Preparation**
- Modular architecture supports Phase 2 expansion
- Clean API design allows for easy feature addition
- Component-based frontend supports complex UI additions

### 3. **Security Focus**
- Authentication handled centrally
- SQL validation prevents injection attacks
- Environment-based configuration

### 4. **Development Efficiency**
- Clear file organization for quick navigation
- Comprehensive testing structure
- Docker support for consistent deployment

### 5. **MVP Requirements Alignment**
- File structure supports all PRD requirements
- Simple enough for 80-hour development timeline
- Room for Phase 2 complexity without major refactoring

This structure provides a solid foundation for the MVP while maintaining the flexibility needed for future enhancements outlined in the PRD.