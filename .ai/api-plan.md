# REST API Plan

## 1. Resources

The API is organized around the following main resources mapped to database tables:

- **Auth** - User authentication and session management (`users`, `sessions`)
- **Queries** - Natural language query attempts and execution (`query_attempts`, `query_results_manifest`)
- **Admin** - Administrative operations (`schema_snapshots`, `kb_examples_index`)

## 2. Endpoints

### 2.1 Authentication Endpoints

#### POST /auth/login
**Description**: Authenticate user and create session

**Request Payload**:
```json
{
  "username": "string (required, 1-255 chars)",
  "password": "string (required, 8-255 chars)"
}
```

**Response Payload** (200 OK):
```json
{
  "user": {
    "id": "integer",
    "username": "string",
    "role": "admin | user",
    "active": "boolean"
  },
  "session": {
    "token": "string",
    "expires_at": "ISO8601 timestamp"
  }
}
```

**Success Codes**:
- `200 OK` - Login successful, session cookie set with 8-hour expiration

**Error Codes**:
- `400 Bad Request` - Missing or invalid credentials format
- `401 Unauthorized` - Invalid username or password
- `403 Forbidden` - User account is inactive

**Notes**:
- Sets session cookie with `HttpOnly`, `Secure`, `SameSite=Strict` flags
- Session expires after 8 hours
- Password validated against bcrypt hash

---

#### POST /auth/logout
**Description**: Revoke current session and clear cookie

**Request Payload**: None (uses session cookie)

**Response Payload** (200 OK):
```json
{
  "message": "Logged out successfully"
}
```

**Success Codes**:
- `200 OK` - Session revoked, cookie cleared

**Error Codes**:
- `401 Unauthorized` - No valid session found

**Notes**:
- Marks session as revoked in database
- Clears session cookie

---

#### GET /auth/session
**Description**: Validate current session and return user info

**Request Payload**: None (uses session cookie)

**Response Payload** (200 OK):
```json
{
  "user": {
    "id": "integer",
    "username": "string",
    "role": "admin | user",
    "active": "boolean"
  },
  "session": {
    "expires_at": "ISO8601 timestamp"
  }
}
```

**Success Codes**:
- `200 OK` - Session valid

**Error Codes**:
- `401 Unauthorized` - Session expired, revoked, or invalid

---

### 2.2 Query Workflow Endpoints

#### POST /queries
**Description**: Submit natural language query and generate SQL (Stage 1 & 2)

**Request Payload**:
```json
{
  "natural_language_query": "string (required, 1-5000 chars)"
}
```

**Response Payload** (201 Created):
```json
{
  "id": "integer",
  "natural_language_query": "string",
  "generated_sql": "string | null",
  "status": "not_executed | failed_generation",
  "created_at": "ISO8601 timestamp",
  "generated_at": "ISO8601 timestamp | null",
  "generation_ms": "integer | null",
  "error_message": "string | null"
}
```

**Success Codes**:
- `201 Created` - Query attempt created, SQL generated successfully or generation failed

**Error Codes**:
- `400 Bad Request` - Empty query or validation failed
- `401 Unauthorized` - Not authenticated
- `429 Too Many Requests` - Rate limit exceeded
- `503 Service Unavailable` - LLM service unavailable after retries

**Notes**:
- Automatically performs two-stage schema optimization
- Finds 3 most similar knowledge base examples via cosine similarity
- Returns both successful SQL generation and generation failures (status distinguishes)
- Retries LLM API calls up to 3 times on failure
- Target: <2 minutes for 95% of queries

---

#### GET /queries/{id}
**Description**: Retrieve specific query attempt details

**Path Parameters**:
- `id`: integer (query_attempts.id)

**Response Payload** (200 OK):
```json
{
  "id": "integer",
  "natural_language_query": "string",
  "generated_sql": "string | null",
  "status": "not_executed | failed_generation | failed_execution | success | timeout",
  "created_at": "ISO8601 timestamp",
  "generated_at": "ISO8601 timestamp | null",
  "executed_at": "ISO8601 timestamp | null",
  "generation_ms": "integer | null",
  "execution_ms": "integer | null",
  "original_attempt_id": "integer | null",
  "error_message": "string | null"
}
```

**Success Codes**:
- `200 OK` - Query found

**Error Codes**:
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - User cannot access this query (not owner, not admin)
- `404 Not Found` - Query ID does not exist

**Notes**:
- Non-admin users can only access their own queries
- Admin users can access all queries

---

#### GET /queries
**Description**: List user's query history with pagination

**Query Parameters**:
- `page`: integer (default: 1, min: 1)
- `page_size`: integer (default: 20, min: 1, max: 100)
- `status`: string (optional filter: "success", "failed_generation", "failed_execution", "timeout", "not_executed")

**Response Payload** (200 OK):
```json
{
  "queries": [
    {
      "id": "integer",
      "natural_language_query": "string",
      "status": "string",
      "created_at": "ISO8601 timestamp",
      "executed_at": "ISO8601 timestamp | null"
    }
  ],
  "pagination": {
    "page": "integer",
    "page_size": "integer",
    "total_count": "integer",
    "total_pages": "integer"
  }
}
```

**Success Codes**:
- `200 OK` - List returned (may be empty)

**Error Codes**:
- `400 Bad Request` - Invalid pagination parameters
- `401 Unauthorized` - Not authenticated

**Notes**:
- Returns queries in reverse chronological order (newest first)
- Non-admin users see only their own queries
- Admin users see all queries by default; can filter by user_id
- Uses index `idx_query_attempts_user_created` for performance

---

#### POST /queries/{id}/execute
**Description**: Execute generated SQL against PostgreSQL database

**Path Parameters**:
- `id`: integer (query_attempts.id)

**Request Payload**: None

**Response Payload** (200 OK):
```json
{
  "id": "integer",
  "status": "success | failed_execution | timeout",
  "executed_at": "ISO8601 timestamp",
  "execution_ms": "integer",
  "results": {
    "total_rows": "integer",
    "page_size": "integer",
    "page_count": "integer",
    "columns": ["string"],
    "rows": [["mixed"]]
  },
  "error_message": "string | null"
}
```

**Success Codes**:
- `200 OK` - Execution completed (includes both success and execution failures)

**Error Codes**:
- `400 Bad Request` - Query not in executable state (already executed, no SQL generated)
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - User cannot execute this query (not owner, not admin)
- `404 Not Found` - Query ID does not exist

**Notes**:
- Validates SQL contains only SELECT statements before execution
- 5-minute timeout for query execution
- Returns first 500 rows in response
- Creates `query_results_manifest` entry if successful
- Uses read-only PostgreSQL connection
- Target: <60 seconds execution for 90% of queries

---

#### GET /queries/{id}/results
**Description**: Retrieve paginated query results

**Path Parameters**:
- `id`: integer (query_attempts.id)

**Query Parameters**:
- `page`: integer (default: 1, min: 1)

**Response Payload** (200 OK):
```json
{
  "attempt_id": "integer",
  "total_rows": "integer",
  "page_size": "integer (500)",
  "page_count": "integer",
  "current_page": "integer",
  "columns": ["string"],
  "rows": [["mixed"]]
}
```

**Success Codes**:
- `200 OK` - Results page returned

**Error Codes**:
- `400 Bad Request` - Invalid page number
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - User cannot access these results
- `404 Not Found` - Query not found or not executed successfully

**Notes**:
- Returns 500 rows per page
- Results not stored in SQLite, fetched from PostgreSQL on demand
- Uses `query_results_manifest` for metadata only

---

#### GET /queries/{id}/export
**Description**: Export query results as CSV file

**Path Parameters**:
- `id`: integer (query_attempts.id)

**Response**:
- Content-Type: `text/csv`
- Content-Disposition: `attachment; filename="query_{id}_{timestamp}.csv"`

**Success Codes**:
- `200 OK` - CSV file download

**Error Codes**:
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - User cannot export these results
- `404 Not Found` - Query not found or not executed successfully
- `413 Payload Too Large` - Results exceed 10,000 row limit (returns warning in response)

**Notes**:
- Exports up to 10,000 rows maximum
- Sets `export_truncated = 1` in manifest if results exceed limit
- Generates CSV on-the-fly, not cached
- Includes UTF-8 BOM for Excel compatibility
- Properly escapes special characters (quotes, commas, newlines)

---

#### POST /queries/{id}/rerun
**Description**: Re-run historical query (generates new SQL from original question)

**Path Parameters**:
- `id`: integer (original query_attempts.id)

**Request Payload**: None

**Response Payload** (201 Created):
```json
{
  "id": "integer (new attempt ID)",
  "original_attempt_id": "integer",
  "natural_language_query": "string",
  "generated_sql": "string | null",
  "status": "not_executed | failed_generation",
  "created_at": "ISO8601 timestamp",
  "generated_at": "ISO8601 timestamp | null",
  "generation_ms": "integer | null"
}
```

**Success Codes**:
- `201 Created` - New query attempt created

**Error Codes**:
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - User cannot access original query
- `404 Not Found` - Original query not found

**Notes**:
- Creates new `query_attempts` entry with `original_attempt_id` reference
- Re-runs full SQL generation process (not cached)
- User must explicitly execute the new query

---

### 2.3 Admin Endpoints

#### POST /admin/schema/refresh
**Description**: Reload PostgreSQL schema from JSON files

**Request Payload**: None

**Response Payload** (200 OK):
```json
{
  "message": "Schema refreshed successfully",
  "snapshot": {
    "id": "integer",
    "loaded_at": "ISO8601 timestamp",
    "source_hash": "string",
    "table_count": "integer",
    "column_count": "integer"
  }
}
```

**Success Codes**:
- `200 OK` - Schema refreshed

**Error Codes**:
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - User does not have admin role
- `422 Unprocessable Entity` - Invalid schema JSON format
- `500 Internal Server Error` - Failed to load schema files

**Notes**:
- Requires admin role
- Reloads schema JSON from disk
- Creates new `schema_snapshots` entry
- Updates in-memory schema cache
- Application continues running during refresh
- Validates schema structure before applying

---

#### POST /admin/kb/reload
**Description**: Reload knowledge base examples from .sql files

**Request Payload**: None

**Response Payload** (200 OK):
```json
{
  "message": "Knowledge base reloaded successfully",
  "stats": {
    "files_loaded": "integer",
    "embeddings_generated": "integer",
    "load_time_ms": "integer"
  }
}
```

**Success Codes**:
- `200 OK` - Knowledge base reloaded

**Error Codes**:
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - User does not have admin role
- `422 Unprocessable Entity` - Invalid .sql file format
- `500 Internal Server Error` - Failed to load files or generate embeddings

**Notes**:
- Requires admin role
- Scans knowledge base directory for .sql files
- Parses QUESTION and TAGS metadata from comments
- Generates embeddings using OpenAI text-embedding-3-small
- Updates `kb_examples_index` table
- Updates in-memory embedding cache
- Application continues running during reload

---

#### GET /admin/metrics
**Description**: Retrieve basic usage metrics (MVP version)

**Query Parameters**:
- `weeks`: integer (default: 4, min: 1, max: 52)

**Response Payload** (200 OK):
```json
{
  "metrics": [
    {
      "week_start": "ISO8601 date",
      "user_id": "integer | null",
      "username": "string | null",
      "attempts_count": "integer",
      "executed_count": "integer",
      "success_count": "integer"
    }
  ],
  "summary": {
    "total_attempts": "integer",
    "total_executed": "integer",
    "total_success": "integer",
    "success_rate": "float (0-1)",
    "acceptance_rate": "float (0-1)"
  }
}
```

**Success Codes**:
- `200 OK` - Metrics returned

**Error Codes**:
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - User does not have admin role

**Notes**:
- Requires admin role
- Reads from `metrics_rollup` table if populated
- Falls back to aggregating from `query_attempts` if rollup not maintained
- Simple weekly aggregations only (no complex analytics)

---

### 2.4 System Endpoints

#### GET /health
**Description**: Health check endpoint for monitoring

**Request Payload**: None

**Response Payload** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "ISO8601 timestamp",
  "services": {
    "database": "up | down",
    "postgresql": "up | down",
    "llm_api": "up | down"
  }
}
```

**Success Codes**:
- `200 OK` - System healthy
- `503 Service Unavailable` - System degraded or unhealthy

**Notes**:
- Does not require authentication
- Checks SQLite and PostgreSQL connectivity
- Does not check OpenAI API (expensive, not critical for health)

---

## 3. Authentication and Authorization

### 3.1 Authentication Mechanism

**Session-Based Authentication with Cookies**:
- Despite tech stack mention of JWT, PRD specifies session cookies and database schema includes `sessions` table
- Server-side session tracking with 8-hour expiration
- Bcrypt password hashing (cost factor 12)

### 3.2 Session Cookie Configuration

```
Cookie Name: session_token
Attributes:
  - HttpOnly: true (prevents XSS)
  - Secure: true (HTTPS only in production)
  - SameSite: Strict (CSRF protection)
  - Max-Age: 28800 (8 hours)
  - Path: /
```

### 3.3 Session Lifecycle

1. **Login** (POST /auth/login):
   - Validate credentials against users table
   - Generate cryptographically secure random token
   - Create sessions entry with 8-hour expiration
   - Set session cookie

2. **Request Authentication** (middleware on protected routes):
   - Extract token from cookie
   - Query sessions table
   - Validate: not revoked, not expired, user active
   - Attach user info to request context

3. **Logout** (POST /auth/logout):
   - Mark session as revoked (revoked = 1)
   - Clear session cookie

4. **Expiration**:
   - Session expires after 8 hours from created_at
   - Expired sessions redirect to login with 401
   - No session extension in MVP

### 3.4 Authorization Rules

**Role-Based Access Control (RBAC)**:

**User Role Permissions**:
- Submit and execute queries
- View own query history
- Export own query results
- View own query details
- Re-run own queries

**Admin Role Permissions**:
- All User permissions
- View all users' query history
- Trigger schema refresh
- Trigger knowledge base reload
- View system metrics

**Enforcement**:
- Implemented at application layer (SQLite has no native RLS)
- Non-admin users: all `query_attempts` queries filtered by `WHERE user_id = current_user_id`
- Admin users: bypass user_id filter, can access all records
- Uses indexes `idx_query_attempts_user_created` for efficient filtering

### 3.5 Rate Limiting

**Query Submission**:
- 10 requests per minute per user
- 429 Too Many Requests response when exceeded
- Sliding window algorithm

**Authentication**:
- 5 login attempts per 15 minutes per IP
- 429 Too Many Requests response when exceeded
- Prevents brute force attacks

## 4. Validation and Business Logic

### 4.1 Input Validation

#### Users Resource
- `username`: 1-255 chars, alphanumeric + underscore only, unique
- `password`: 8-255 chars minimum (enforced at registration, not in MVP)
- `role`: Must be exactly 'admin' or 'user'
- `active`: Must be 0 or 1 (boolean)

#### Query Attempts Resource
- `natural_language_query`: 1-5000 chars, cannot be only whitespace
- `generated_sql`: Validated to contain only SELECT statements
- `status`: Must be one of: 'not_executed', 'failed_generation', 'failed_execution', 'success', 'timeout'

#### Sessions Resource
- `token`: 64-character random hex string, unique
- `expires_at`: Must be future timestamp, max 8 hours from created_at
- `revoked`: Must be 0 or 1 (boolean)

#### Query Results Manifest
- `page_size`: Fixed at 500 (not user-configurable in MVP)
- `export_row_limit`: Fixed at 10,000
- `export_truncated`: Must be 0 or 1 (boolean)

### 4.2 Business Logic Implementation

#### SQL Generation Workflow

**Stage 1: Table Selection**
1. Load schema from memory cache
2. Send table names and descriptions to GPT-4
3. GPT-4 identifies 5-10 relevant tables
4. Store start time for `generation_ms`

**Stage 2: SQL Generation**
1. Load full schema for selected tables
2. Perform cosine similarity search on user question
3. Retrieve top 3 most similar knowledge base examples
4. Send to GPT-4:
   - User's natural language question
   - Full schema for selected tables
   - 3 similar examples
   - Instructions for PostgreSQL syntax
   - Instruction for SELECT-only queries
5. Receive generated SQL
6. Calculate and store `generation_ms`

**Status Handling**:
- If generation succeeds: `status = 'not_executed'`, `generated_sql` populated
- If generation fails: `status = 'failed_generation'`, `generated_sql = NULL`

#### SQL Validation

**SELECT-Only Enforcement**:
```python
def validate_select_only(sql: str) -> bool:
    # Case-insensitive check for dangerous keywords
    dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 
                          'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE']
    sql_upper = sql.upper()
    
    # Remove comments and string literals
    cleaned_sql = remove_comments_and_strings(sql_upper)
    
    for keyword in dangerous_keywords:
        if re.search(r'\b' + keyword + r'\b', cleaned_sql):
            return False
    
    # Must contain SELECT
    if not re.search(r'\bSELECT\b', cleaned_sql):
        return False
        
    return True
```

**Validation Point**:
- Executed before query execution in POST /queries/{id}/execute
- If validation fails: set `status = 'failed_generation'`, return 400 error
- Prevents SQL injection and accidental writes

#### Query Execution Logic

**PostgreSQL Connection**:
- Read-only database user with SELECT-only privileges (database-level enforcement)
- Connection pooling for 5-10 concurrent users
- 5-minute query timeout (configurable)

**Execution Flow**:
1. Validate query exists and has generated SQL
2. Validate SQL is SELECT-only
3. Store execution start time
4. Execute against PostgreSQL with timeout
5. Handle result:
   - **Success**: 
     - `status = 'success'`
     - Create `query_results_manifest` entry
     - Calculate and store `execution_ms`
     - Store `executed_at` timestamp
   - **Execution Error**:
     - `status = 'failed_execution'`
     - Store error message
     - Store `executed_at` timestamp
   - **Timeout**:
     - `status = 'timeout'`
     - Store `executed_at` timestamp

#### Result Pagination

**Fixed Page Size**:
- 500 rows per page (not configurable in MVP)
- Results fetched on-demand from PostgreSQL (not cached)
- Uses LIMIT/OFFSET for pagination

**Metadata Storage**:
- `query_results_manifest.total_rows`: Total result count
- `query_results_manifest.page_count`: Calculated as `ceil(total_rows / 500)`
- `query_results_manifest.page_size`: Always 500

#### CSV Export Logic

**Export Process**:
1. Validate user can access query results
2. Fetch up to 10,000 rows from PostgreSQL
3. Generate CSV with:
   - UTF-8 BOM for Excel compatibility
   - Proper escaping (quotes, commas, newlines)
   - Column headers in first row
4. If `total_rows > 10,000`:
   - Set `export_truncated = 1` in manifest
   - Include warning in response headers
5. Stream CSV as file download

**File Naming**:
- Format: `query_{attempt_id}_{timestamp}.csv`
- Example: `query_42_20250126_150730.csv`

#### Error Handling Categories

**Two Broad Categories (per PRD)**:

1. **Generation Failed** (`failed_generation`):
   - LLM API unavailable after 3 retries
   - LLM returned invalid/empty response
   - Generated SQL failed SELECT-only validation
   - User Message: "Unable to generate query. Try rephrasing your question."

2. **Execution Failed** (`failed_execution`):
   - PostgreSQL syntax error
   - Runtime error (invalid table/column reference)
   - Permission denied
   - Connection error
   - User Message: "Query failed to execute. The generated SQL may be invalid."
   - Include basic database error message

**Timeout Handling** (`timeout`):
- Separate status for queries exceeding 5-minute limit
- User Message: "Query took too long to execute. Try narrowing your search."

#### Re-run Logic

**Creating Retry Lineage**:
1. Load original query attempt
2. Create new query_attempts entry with:
   - `natural_language_query`: Copy from original
   - `original_attempt_id`: Reference to original query ID
   - `status`: 'not_executed' (or 'failed_generation' if generation fails)
3. Run full SQL generation workflow (not cached)
4. User must explicitly execute new attempt

**Lineage Tracking**:
- Enables tracing query refinement history
- `original_attempt_id = NULL` for original queries
- `original_attempt_id != NULL` for re-runs

#### Knowledge Base Search

**Cosine Similarity Algorithm**:
1. Generate embedding for user's question using OpenAI text-embedding-3-small
2. Load all knowledge base embeddings from memory
3. Calculate cosine similarity:
   ```
   similarity = dot(query_embedding, kb_embedding) / 
                (norm(query_embedding) * norm(kb_embedding))
   ```
4. Sort by similarity descending
5. Return top 3 examples with similarity > 0.7 threshold

**Embedding Cache**:
- All knowledge base embeddings loaded into memory at startup
- Updated when admin triggers reload via POST /admin/kb/reload
- Not persisted across restarts (regenerated from BLOB in kb_examples_index)

### 4.3 Concurrency Control

**Database Connection Pools**:
- SQLite: Single connection with write serialization (PRAGMA journal_mode=WAL)
- PostgreSQL: Connection pool of 10 connections for read queries

**Query Execution**:
- Each user's query runs independently
- No blocking between users
- Timeout prevents resource exhaustion

**Session Management**:
- Multiple sessions per user allowed (no single-session enforcement)
- Expired sessions automatically filtered by query

### 4.4 Performance Optimizations

**Index Usage**:
- `idx_query_attempts_user_created`: Fast user history retrieval
- `idx_query_attempts_status_created`: Admin status filtering
- `idx_sessions_user_expires`: Session validation
- `idx_kb_examples_file_path`: Knowledge base lookups

**Caching Strategy**:
- Schema: Loaded into memory at startup, refreshed on demand
- Knowledge base embeddings: Loaded into memory, refreshed on demand
- Query results: Not cached (fetched on-demand from PostgreSQL)

**Query Optimization**:
- Two-stage schema limits LLM token usage
- Connection pooling reduces overhead
- Descending indexes support recent-first sorting

### 4.5 Data Retention

**Query History**:
- Retained indefinitely (no automatic cleanup)
- `ON DELETE RESTRICT` on users preserves audit trail
- Manual cleanup if needed (admin database access)

**Sessions**:
- Expired sessions retained in database
- Can be periodically cleaned via scheduled job (not in MVP)

**Export Files**:
- CSV exports not stored (generated on-demand)
- `export_file_path` in manifest reserved for future file caching