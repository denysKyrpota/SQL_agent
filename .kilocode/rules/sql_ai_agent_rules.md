# AI Rules for SQL AI Agent MVP

## FRONTEND

### Guidelines for REACT

#### REACT_ESSENTIAL_STANDARDS

- Use functional components with basic hooks (useState, useEffect, useContext) for simplicity
- Implement simple, focused components that follow single responsibility principle
- Use conditional rendering for showing/hiding query status, results, and error messages
- Apply appropriate prop types or basic TypeScript interfaces for component safety
- Keep form state local to components where possible, using controlled components for the query form
- Prioritize readability over complex optimizations in the MVP phase
- Create custom hooks for reusable logic (query submission, authentication, etc.)
- Implement basic error boundaries for critical components (query form, results display)

#### REACT_ROUTER_ESSENTIALS

- Use simple BrowserRouter configuration with basic routes (login, main query, history)
- Implement protected routes for authenticated user areas
- Use useNavigate for programmatic navigation after form submissions
- Keep routing structure flat and straightforward for the MVP's limited page needs

#### STATE_MANAGEMENT

- Use React Context for global state when needed (user authentication, shared settings)
- Keep component state local when possible to minimize complexity
- Implement a simple state pattern for the query workflow (input → processing → results/error)
- Consider React Query only for specific features requiring advanced data fetching patterns

## BACKEND

### Guidelines for FASTAPI

#### API_DESIGN

- Create RESTful endpoints following FastAPI best practices
- Implement proper request validation using Pydantic models
- Use dependency injection for authentication and database connections
- Add appropriate error handling with clear status codes and messages
- Document API endpoints using FastAPI's built-in OpenAPI support
- Implement basic rate limiting for query endpoints
- Use async handlers for database and LLM operations to maintain responsiveness

#### SECURITY

- Implement JWT authentication with secure cookie storage
- Enforce HTTPS in production environments
- Sanitize all user input before processing
- Apply principle of least privilege for database connections (read-only)
- Validate generated SQL to prevent injection attacks
- Implement basic CORS configuration for the frontend

## AI/ML IMPLEMENTATION

#### LLM_INTEGRATION

- Implement robust error handling for OpenAI API calls with retries
- Create clear, consistent prompt templates for the two-stage schema approach
- Cache embeddings in memory to improve performance
- Implement token usage monitoring to control costs
- Add fallback mechanisms for API outages
- Validate generated SQL for SELECT-only operations before execution
- Keep a simple logging system for prompt performance analysis

#### KNOWLEDGE_BASE

- Maintain clear file naming conventions for .sql example files
- Implement efficient embedding generation and cosine similarity search
- Create a simple schema for question metadata (tags, description)
- Add basic versioning for schema and example updates
- Establish a clear refresh mechanism for knowledge base changes

## DATABASE

#### SQL_EXECUTION

- Implement connection pooling for concurrent query execution
- Add timeout configuration to prevent long-running queries
- Configure read-only permissions at the database level
- Implement basic query execution metrics (duration, row count)
- Add transaction management for consistent query execution

## DEVELOPMENT PRACTICES

#### MVP_FOCUS

- Prioritize core functionality over UI polish
- Follow simple, consistent code style with linting
- Add basic unit tests for critical paths (query generation, SQL validation)
- Document code with clear, concise comments for maintainability
- Create simple deployment documentation for local server setup
- Use environment variables for configuration management
- Commit code using conventional commit messages