# Product Requirements Document (PRD) - SQL AI Agent - MVP

## 1. Product Overview

The SQL AI Agent is an intelligent database assistant that enables non-technical stakeholders and developers to query PostgreSQL databases using natural language. The MVP focuses on core functionality: translating user questions into SQL, displaying results, and learning from a simple set of curated examples.

### Core Capabilities

The system translates natural language questions into optimized SQL queries using GPT-4, leveraging a simple knowledge base of successful query patterns. Users review generated SQL with syntax highlighting before execution, ensuring transparency and building trust in the AI-generated queries.

### Target Users

- Non-technical stakeholders (business analysts, managers) who need data insights without SQL expertise
- Developers who want to accelerate query development and learn from successful patterns

### MVP Scope

This initial release delivers the essential query workflow within an 80-hour development timeline:

- Natural language to SQL translation
- Simple knowledge base (10-20 manually curated examples)
- Two-stage schema optimization for 50+ table databases
- SQL preview with syntax highlighting
- Query execution with basic error handling
- Simple results display with CSV export
- Basic authentication (2-3 users)
- Minimal admin tools (schema refresh only)

### Deployment Model

Local server deployment with read-only PostgreSQL access, supporting 5-10 concurrent users. SQLite manages application data (query history and user accounts).

## 2. User Problem

### Primary Pain Points

#### For Non-Technical Stakeholders

Business users cannot access data trapped in complex databases without either learning SQL (high time investment) or depending on technical teams (bottlenecks and delays). This dependency slows decision-making and limits data-driven insights.

Simple data questions require lengthy request cycles: submit ticket, clarify requirements, wait for results, request modifications, repeat. This iteration cycle wastes time and reduces business agility.

#### For Developers and Data Engineers

Technical users spend significant time writing similar SQL queries for stakeholder requests. They serve as intermediaries between business users and data, becoming bottlenecks when stakeholders need quick answers.

Databases with 50+ tables are difficult to navigate. Understanding table relationships requires extensive schema knowledge, slowing query development.

### Expected Impact

The SQL AI Agent eliminates SQL knowledge requirements and reduces data access latency. Non-technical users can explore data independently, while developers focus on higher-value work instead of routine query requests.

The transparent SQL preview builds user trust and creates informal learning opportunities, gradually improving organizational data literacy.

## 3. Functional Requirements

### 3.1 Natural Language Query Interface

Users input database questions in plain English through a simple web form. The interface supports multi-line input and displays the current processing status (generating SQL, executing query).

Example effective questions are displayed to guide new users. The interface is minimal and focused, avoiding complex chat history or conversation features in the MVP.

### 3.2 Knowledge Base - Simplified Approach

#### Storage Structure

Approved queries are stored as 10-20 .sql files in a folder. Each file contains SQL with simple comment metadata:

```sql
-- QUESTION: What were our top 10 customers by revenue last quarter?
-- TAGS: revenue, customers, quarterly

SELECT 
  c.customer_name,
  SUM(o.total_amount) as total_revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_date >= DATE_TRUNC('quarter', CURRENT_DATE - INTERVAL '3 months')
  AND o.order_date < DATE_TRUNC('quarter', CURRENT_DATE)
GROUP BY c.customer_id, c.customer_name
ORDER BY total_revenue DESC
LIMIT 10;
```

#### Loading and Search

All .sql files load at application startup. The system generates embeddings for each question using OpenAI text-embedding-3-small and stores them in memory.

When a user submits a question, the system performs simple cosine similarity search to find the 3 most similar examples and includes them in the LLM prompt.

#### Management

For MVP, the knowledge base is manually managed by editing .sql files directly on the server. No web-based admin interface for adding/editing queries. When files change, admin restarts the application or triggers a simple reload endpoint.

This simplified approach eliminates the need for complex CRUD interfaces, usage analytics, embedding regeneration workflows, and file management systems in the MVP.

### 3.3 Schema Management

#### JSON Schema Files

Database schema is pre-prepared in simple JSON format:

```json
{
  "tables": [
    {
      "name": "customers",
      "description": "Customer master data",
      "columns": [
        {"name": "customer_id", "type": "integer", "primary_key": true},
        {"name": "customer_name", "type": "varchar(255)"}
      ]
    }
  ],
  "relationships": [
    {
      "from_table": "orders",
      "from_column": "customer_id",
      "to_table": "customers",
      "to_column": "customer_id"
    }
  ]
}
```

#### Schema Caching

Complete schema loads into memory at startup for fast access. Admin can trigger manual refresh via simple API endpoint (no UI dashboard needed for MVP).

No scheduled refresh, no cache age indicators, no complex refresh workflows. These features are deferred to Phase 2.

#### Two-Stage Schema Optimization

Stage 1: Send table names and descriptions to GPT-4, which identifies 5-10 relevant tables

Stage 2: Send full schema details for selected tables plus 3 similar examples from knowledge base to generate SQL

This approach keeps token usage manageable for databases with 50+ tables.

### 3.4 SQL Generation and Preview

#### Generation Process

GPT-4 generates SQL using:
- User's natural language question
- Full schema for tables identified in Stage 1
- 3 most similar approved queries as examples
- Instructions for PostgreSQL-specific syntax and SELECT-only queries

Target: SQL generation completes within 2 minutes for most queries.

#### Display

Generated SQL displays with syntax highlighting using a simple client-side JavaScript library (Prism.js or Highlight.js). The interface includes:
- Formatted SQL with color-coded syntax
- Copy button for clipboard
- Simple "Execute Query" button

No complexity indicators, no table selection explanations, no similar query details in MVP. Focus on clarity and simplicity.

### 3.5 Query Execution

#### Database Connection

Read-only PostgreSQL connection with SELECT-only privileges. Simple connection pooling for 5-10 concurrent users.

#### Execution Process

User must click "Execute Query" to confirm execution. Query runs with a 5-minute timeout (configurable).

#### Error Handling - Simplified

Two broad error categories:

1. Generation Failed: LLM could not generate valid SQL
   - User-friendly message: "Unable to generate query. Try rephrasing your question."
   - Option to retry with modified question

2. Execution Failed: SQL failed to run
   - User-friendly message: "Query failed to execute. The generated SQL may be invalid."
   - Display basic error message from database
   - Option to retry with modified question

No fine-grained error categorization (syntax vs. execution vs. timeout vs. connection), no collapsible technical details, no comprehensive error analytics. Simple, clear feedback only.

### 3.6 Results Display and Export

#### Results Table

Query results display in a simple HTML table showing:
- First 500 rows
- Column headers
- Row count
- Basic pagination (Previous/Next buttons if more than 500 rows)

No configurable page sizes, no sortable columns, no infinite scroll. Simple and functional.

#### CSV Export

Export button downloads results as CSV (up to 10,000 rows). If results exceed 10,000 rows, user sees warning that export is truncated.

No streaming optimization, no configurable limits. Simple implementation sufficient for MVP.

### 3.7 Query History - Minimal Tracking

#### Storage

SQLite database stores basic query information:
- query_id
- user_id
- natural_language_query
- generated_sql
- status (success, failed_generation, failed_execution, not_executed)
- created_at
- executed_at

No execution time tracking, no row counts, no error categories, no detailed metadata. Just enough for basic history.

#### User Access

Users can view their own previous queries in a simple list (most recent first). Each entry shows:
- The question asked
- Status (executed successfully, failed, or not executed)
- Timestamp

Clicking an entry shows the generated SQL and allows re-running (which generates new SQL from the original question).

No filtering, no search, no date range selection, no detailed analytics. Basic history only.

#### Admin Access

For MVP, admin uses same history view as regular users. No cross-user analytics, no aggregate metrics, no usage dashboards. These are Phase 2 features.

### 3.8 User Authentication - Basic Only

#### Simple Login

Username and password authentication with bcrypt hashing. Session cookies with 8-hour expiration.

2-3 predefined accounts configured via environment variables at deployment. No user management interface.

#### Two Roles

User Role:
- Submit queries and view results
- Access own query history
- Export to CSV

Admin Role:
- All User capabilities
- Trigger schema cache refresh (via API endpoint, no UI)

No account management, no password changes, no user creation interface. Manual configuration only for MVP.

### 3.9 Admin Functions - Minimal

#### Schema Refresh Only

Admin can trigger schema reload via simple API endpoint (e.g., POST /admin/refresh-schema). No UI button, no dashboard, no status indicators.

Expected usage: Admin manually calls endpoint when schema changes, or restarts application.

#### No Knowledge Base Management UI

Admins manually edit .sql files on the server to add/modify knowledge base entries. No web interface for this in MVP.

#### No Analytics Dashboard

No system health monitoring, no usage analytics, no error trend analysis in MVP. These are complex features deferred to Phase 2.

## 4. Product Boundaries

### In Scope for MVP

Core Functionality:
- Natural language to SQL translation using GPT-4
- Two-stage schema optimization
- Simple knowledge base (10-20 examples, file-based)
- SQL preview with syntax highlighting
- Query execution with 5-minute timeout
- Basic results table (500 rows)
- CSV export (10,000 row limit)
- Simple query history (user's own queries only)
- Basic error messages (2 categories)
- Simple authentication (2-3 users, 2 roles)
- Schema refresh via API endpoint

Technical Scope:
- PostgreSQL only
- Read-only database access
- Local server deployment
- Web interface (React with FastAPI backend)
- SQLite for application data
- Support for 5-10 concurrent users

### Explicitly Out of Scope for MVP

Knowledge Base:
- Web UI for adding/editing queries
- Usage analytics for approved queries
- Dynamic embedding regeneration
- Automatic query curation
- Complex file management

Error Handling and Logging:
- Fine-grained error categorization (4+ types)
- Collapsible technical details
- Comprehensive error analytics
- System log exports
- Error trend dashboards

Admin Features:
- Schema refresh UI with status indicators
- Cache age monitoring
- Cross-user query history
- Usage analytics dashboard
- System health monitoring
- User account management interface
- Detailed query metadata tracking

User Experience:
- Query modification before retry (just re-enter question)
- Similar queries used display
- Table selection reasoning
- Advanced pagination (configurable page size, sorting)
- Query examples beyond static text
- Session extension warnings
- Dark mode

Advanced Features:
- Scheduled schema refresh
- Query performance optimization
- Multiple database connections
- Write operations
- Query scheduling
- Data visualizations
- Mobile applications

### Phase 2 Considerations

After MVP validation with real users, consider adding:
- Admin web UI for knowledge base management
- Usage analytics to identify which examples are most helpful
- Fine-grained error handling with technical details
- Enhanced query history with filtering and search
- User account management interface
- System health dashboard
- Improved results pagination and sorting

## 5. User Stories

### Authentication and Access

#### US-001: User Login
Title: Authenticate to Access System
Description: As a user, I want to log in with my username and password so that I can securely access the SQL AI Agent.
Acceptance Criteria:
- Login page displays username and password fields
- User can submit credentials via form submission
- Successful login redirects to main query interface
- Failed login displays simple error message
- Session persists for 8 hours

#### US-002: User Logout
Title: End Session
Description: As a user, I want to log out so that others cannot access my account.
Acceptance Criteria:
- Logout button is visible on all pages
- Clicking logout clears session and redirects to login
- User must log in again to access system

### Core Query Workflow

#### US-003: Submit Natural Language Query
Title: Ask Database Question
Description: As a user, I want to type my database question in natural language so that I can get data without learning SQL.
Acceptance Criteria:
- Text input field accepts multi-line questions
- Submit button is enabled when input is not empty
- System displays "Generating SQL..." status after submission
- Previous question remains visible during processing

#### US-004: View Generated SQL
Title: Preview SQL Before Execution
Description: As a user, I want to see the generated SQL with syntax highlighting so that I can verify it matches my intent.
Acceptance Criteria:
- Generated SQL displays with syntax highlighting (keywords, strings color-coded)
- SQL is formatted with proper indentation
- Copy button allows copying SQL to clipboard
- "Execute Query" button is prominently displayed

#### US-005: Execute Confirmed Query
Title: Run SQL Against Database
Description: As a user, I want to explicitly confirm execution so that I control when queries run.
Acceptance Criteria:
- Execute button is clearly labeled
- Clicking execute shows "Running query..." status
- User cannot submit new queries while execution is running
- Execution completes within 5 minutes or times out

#### US-006: View Query Results
Title: See Query Output
Description: As a user, I want to view query results in a table format so that I understand the data returned.
Acceptance Criteria:
- Results display in HTML table with column headers
- First 500 rows are shown
- Total row count is displayed
- If more than 500 rows, pagination controls appear
- Empty results show "No rows returned" message

#### US-007: Navigate Result Pages
Title: Browse Multiple Pages
Description: As a user, I want to view additional results beyond the first 500 rows.
Acceptance Criteria:
- "Next" button appears if more than 500 rows
- "Previous" button appears on pages after the first
- Current page and total rows are displayed
- Navigation maintains table formatting

#### US-008: Export Results to CSV
Title: Download Results
Description: As a user, I want to export results to CSV so that I can analyze them in Excel.
Acceptance Criteria:
- Export button is visible when results are displayed
- Export downloads CSV file with timestamp in filename
- Export includes up to 10,000 rows
- Warning displays if results exceed 10,000 rows
- CSV properly handles special characters

#### US-009: Retry After Failure
Title: Rephrase Question
Description: As a user, I want to retry my query after an error so that I can rephrase and get results.
Acceptance Criteria:
- "Try Again" button displays when query fails
- User can enter new question
- Previous error message clears when new query is submitted
- Retry creates new attempt in history

### Error Handling

#### US-010: Receive Clear Error Messages
Title: Understand Query Failures
Description: As a user, I want clear error messages so that I know what went wrong.
Acceptance Criteria:
- Generation failures show "Unable to generate query. Try rephrasing your question."
- Execution failures show "Query failed to execute. The generated SQL may be invalid."
- Timeout shows "Query took too long to execute. Try narrowing your search."
- Error messages are displayed prominently
- User can retry after seeing error

#### US-011: Handle Query Timeouts
Title: Manage Long-Running Queries
Description: As a user, I want to be notified when my query times out so that I can refine it.
Acceptance Criteria:
- Timeout occurs after 5 minutes
- Error message explains query exceeded time limit
- User can submit a new, more specific query
- Timeout does not crash the application

### Query History

#### US-012: View Own Query History
Title: Review Past Questions
Description: As a user, I want to view my previous queries so that I can reference past work.
Acceptance Criteria:
- History page lists user's queries in reverse chronological order (newest first)
- Each entry shows the natural language question and status (success/failed)
- User can click entry to view generated SQL
- Timestamp is displayed for each query

#### US-013: Re-run Historical Query
Title: Execute Previous Query Again
Description: As a user, I want to re-run a query from my history so that I can get updated results.
Acceptance Criteria:
- "Re-run" button appears for each historical query
- Clicking re-run processes the original question (generates new SQL)
- User sees new generated SQL before execution
- Re-run creates new entry in history

### Schema Management

#### US-014: Admin Schema Refresh
Title: Update Schema After Changes
Description: As an admin, I want to refresh the schema cache so that new tables or columns are available.
Acceptance Criteria:
- Admin can call POST /admin/refresh-schema endpoint
- Endpoint reloads schema JSON from disk
- Success response confirms refresh completed
- Error response if schema files are invalid
- Application continues running during refresh

### Edge Cases

#### US-015: Handle Empty Input
Title: Validate Query Submission
Description: As a user, I want clear feedback when I try to submit an empty query.
Acceptance Criteria:
- Submit button is disabled when input is empty
- Submitting only whitespace shows error message
- Error explains input is required

#### US-016: Handle Large Result Sets
Title: Manage Queries Returning Many Rows
Description: As a user, I want guidance when my query returns many rows.
Acceptance Criteria:
- If results exceed 500 rows, pagination controls appear
- If results exceed 10,000 rows, CSV export shows truncation warning
- Message suggests refining query if results are very large

#### US-017: Handle Non-SELECT SQL
Title: Prevent Write Operations
Description: As a user, I want the system to prevent write operations for safety.
Acceptance Criteria:
- System detects INSERT, UPDATE, DELETE, DROP, ALTER in generated SQL
- Query is rejected with error message
- Error explains only SELECT queries are allowed
- User can rephrase question

#### US-018: Handle Session Expiration
Title: Manage Idle Timeout
Description: As a user, I want to be redirected to login when my session expires.
Acceptance Criteria:
- Session expires after 8 hours of inactivity
- Expired session redirects to login page
- Message explains session has expired
- User can log in again to continue

#### US-019: Handle API Failures
Title: Manage LLM Service Outages
Description: As a user, I want clear feedback when the LLM service is unavailable.
Acceptance Criteria:
- API errors display "Service temporarily unavailable. Please try again."
- System retries API calls up to 3 times
- User can retry after all retries are exhausted
- Application remains functional for other users

#### US-020: Handle Concurrent Users
Title: Support Multiple Users
Description: As one of multiple users, I want my queries to process independently.
Acceptance Criteria:
- System supports 5-10 concurrent users
- One user's query does not block other users
- Each user sees only their own results
- Database connection pool manages concurrent access

### User Experience

#### US-021: View Query Examples
Title: Learn Effective Patterns
Description: As a new user, I want to see example questions so that I understand how to use the system.
Acceptance Criteria:
- Help text displays 5-10 example questions
- Examples are relevant to the actual database
- Examples show different query types (filtering, aggregation, joins)
- User can copy examples to input field

#### US-022: Copy Generated SQL
Title: Reuse SQL Elsewhere
Description: As a developer, I want to copy generated SQL so that I can use it in other tools.
Acceptance Criteria:
- Copy button is visible next to SQL
- Clicking copy button copies SQL to clipboard
- Brief confirmation message shows after copy
- Copied SQL includes formatting

#### US-023: View Execution Time
Title: Understand Performance
Description: As a user, I want to see how long my query took so that I understand performance.
Acceptance Criteria:
- Execution time displays after query completes
- Time is shown in seconds
- SQL generation time is shown separately
- Performance indicator shows if query was fast or slow

## 6. Success Metrics

### Primary Success Metric

Query Accuracy Rate: 80% Target
- Definition: Percentage of knowledge base queries that, when re-executed with 3 natural language variations, produce working SQL
- Measurement: Monthly manual testing with small variation set
- Success Threshold: Maintain 80% accuracy
- Focus on core functionality quality over extensive automated testing

### Secondary Metrics

User Acceptance Rate: 70% Target
- Percentage of generated SQL that users actually execute
- Indicates user confidence in generated SQL
- Tracked automatically in query history

Query Success Rate: 85% Target
- Percentage of executed queries that complete without errors
- Measures overall system reliability
- Simple success/failure tracking only

Response Time
- SQL generation: <2 minutes for 95% of queries
- Query execution: <60 seconds for 90% of queries
- Track basic timing, no detailed percentile analysis

User Adoption
- Active users per week (target: reach 5 regular users)
- Queries per user per week (target: 3-5)
- Simple counts, no complex engagement metrics

### Measurement Infrastructure

Basic Query Tracking
- SQLite database logs all attempts with status
- Simple weekly count queries for metrics
- No automated dashboards or real-time monitoring

Manual Testing
- Monthly test of knowledge base variations
- Admin manually tracks accuracy rate
- Documented test procedure for consistency

### Success Criteria for MVP Launch

MVP is ready for broader use when:

1. 80% query accuracy maintained for 2 weeks
2. 10-20 approved queries in knowledge base
3. 3-5 users submitting queries successfully
4. No critical bugs for 1 week
5. Average SQL generation under 2 minutes
6. System handles 5 concurrent users
7. Basic error handling works correctly
8. CSV export functions properly

### Review Process

Weekly Check:
- Admin reviews query history for patterns
- Identifies failures to inform knowledge base updates
- Monitors basic usage numbers

Monthly Review:
- Run accuracy tests on knowledge base
- Calculate basic metrics (acceptance rate, success rate)
- Decide on knowledge base additions
- Assess need for Phase 2 features based on usage