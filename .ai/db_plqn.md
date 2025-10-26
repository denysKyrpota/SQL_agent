1. List of tables with their columns, data types, and constraints

- users
    - id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
    - username TEXT NOT NULL UNIQUE
    - password_hash TEXT NOT NULL
    - role TEXT NOT NULL CHECK (role IN ('admin','user'))
    - active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1))
    - created_at TEXT NOT NULL DEFAULT (datetime('now'))
- sessions
    - id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
    - user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE
    - token TEXT NOT NULL UNIQUE
    - created_at TEXT NOT NULL DEFAULT (datetime('now'))
    - expires_at TEXT NOT NULL
    - revoked INTEGER NOT NULL DEFAULT 0 CHECK (revoked IN (0,1))
- query_attempts
    - id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
    - user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT
    - natural_language_query TEXT NOT NULL
    - generated_sql TEXT
    - status TEXT NOT NULL CHECK (status IN ('not_executed','failed_generation','failed_execution','success','timeout'))
    - created_at TEXT NOT NULL DEFAULT (datetime('now'))
    - generated_at TEXT
    - executed_at TEXT
    - generation_ms INTEGER
    - execution_ms INTEGER
    - original_attempt_id INTEGER REFERENCES query_attempts(id) ON DELETE SET NULL
- query_results_manifest
    - attempt_id INTEGER PRIMARY KEY NOT NULL REFERENCES query_attempts(id) ON DELETE CASCADE
    - total_rows INTEGER
    - page_size INTEGER NOT NULL DEFAULT 500
    - page_count INTEGER
    - export_row_limit INTEGER NOT NULL DEFAULT 10000
    - export_truncated INTEGER NOT NULL DEFAULT 0 CHECK (export_truncated IN (0,1))
    - export_file_path TEXT
    - created_at TEXT NOT NULL DEFAULT (datetime('now'))
- schema_snapshots
    - id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
    - loaded_at TEXT NOT NULL DEFAULT (datetime('now'))
    - source_hash TEXT NOT NULL
    - table_count INTEGER NOT NULL
    - column_count INTEGER NOT NULL
    - tables_json TEXT NOT NULL
- kb_examples_index
    - id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
    - file_path TEXT NOT NULL UNIQUE
    - question_text TEXT NOT NULL
    - tags TEXT
    - last_loaded_at TEXT NOT NULL DEFAULT (datetime('now'))
    - embedding BLOB
- metrics_rollup (minimal, optional)
    - id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL
    - week_start TEXT NOT NULL
    - user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
    - attempts_count INTEGER NOT NULL DEFAULT 0
    - executed_count INTEGER NOT NULL DEFAULT 0
    - success_count INTEGER NOT NULL DEFAULT 0

2. Relationships between tables

- users 1-to-many query_attempts via user_id; restrict deletion to preserve audit history of attempts
- query_attempts 1-to-1 query_results_manifest via attempt_id as primary key to manifest metadata only; results themselves are not stored in SQLite for MVP
- query_attempts optional self-reference via original_attempt_id to represent retries or re-runs lineage; null when original
- sessions many-to-1 users via user_id; session rows support 8-hour expiration semantics and revocation flags
- schema_snapshots is standalone temporal history for schema cache reloads and audit; no foreign keys
- kb_examples_index is standalone index mapping on-disk .sql files to searchable metadata; no foreign keys
- metrics_rollup optionally references users for simple weekly counts to support basic success metrics without heavy analytics

3. Indexes

- users
    - CREATE UNIQUE INDEX idx_users_username ON users(username);
- sessions
    - CREATE UNIQUE INDEX idx_sessions_token ON sessions(token);
    - CREATE INDEX idx_sessions_user_expires ON sessions(user_id, expires_at);
- query_attempts
    - CREATE INDEX idx_query_attempts_user_created ON query_attempts(user_id, created_at DESC);
    - CREATE INDEX idx_query_attempts_status_created ON query_attempts(status, created_at DESC);
    - CREATE INDEX idx_query_attempts_original ON query_attempts(original_attempt_id);
- query_results_manifest
    - PRIMARY KEY on attempt_id already covers lookups; no extra index required
- schema_snapshots
    - CREATE INDEX idx_schema_snapshots_loaded_at ON schema_snapshots(loaded_at DESC);
    - CREATE UNIQUE INDEX idx_schema_snapshots_source_hash ON schema_snapshots(source_hash);
- kb_examples_index
    - CREATE UNIQUE INDEX idx_kb_examples_file_path ON kb_examples_index(file_path);
    - CREATE INDEX idx_kb_examples_tags ON kb_examples_index(tags);
    - CREATE INDEX idx_kb_examples_loaded_at ON kb_examples_index(last_loaded_at DESC);
- metrics_rollup
    - CREATE INDEX idx_metrics_week_user ON metrics_rollup(week_start, user_id);

4. SQLite policies (if applicable)

- Row-level security model: enforce application-scoped filtering by user_id for non-admins; admins can view all records. Implement in application layer by always binding the authenticated user’s id in WHERE clauses on query_attempts and any derived user-scoped reads, since SQLite has no native RLS. Example policy: non-admin users may only SELECT from query_attempts where user_id = current_user_id; admin bypasses filter. Similar scoping applies to query_results_manifest via join on attempt’s user_id. Enable PRAGMA foreign_keys = ON at connection start.
- Write-safety policy: generated SQL sent to PostgreSQL must be validated server-side to reject any non-SELECT statements before execution; store status as failed_generation or failed_execution accordingly. This is enforced in the application, not SQLite.

5. Additional notes or explanations about design decisions

- Authentication: store bcrypt hashes in users.password_hash; sessions table supports 8-hour session expiration and logout via revoked flag. Although tech stack suggests JWT, the PRD specifies session cookies; schema supports server-tracked sessions to align with MVP.
- History scope: per PRD, users see only their own history; this is enforced by app-level filters, not DB-native RLS. Admin UI is minimal and shares the same views, so no cross-user analytics tables are included.
- Results storage: large result sets are not persisted in SQLite; only a manifest describing pagination and export truncation is stored to keep the DB small and performant for 5–10 concurrent users. CSV exports reference export_file_path when created.
- Schema cache: snapshots persist full tables_json plus counts and a source_hash for auditability and manual refresh, enabling traceability across reloads.
- Knowledge base: examples are maintained as .sql files on disk; kb_examples_index keeps lightweight metadata and optional embedding BLOB for future use, even if embeddings primarily reside in memory for MVP.
- Status normalization: query_attempts.status enumerates the minimal states required by the PRD, including timeout, and pairs with timing columns generation_ms and execution_ms to support basic performance visibility.
- Deletion rules: ON DELETE RESTRICT on users in query_attempts preserves historical audit; sessions and metrics can cascade with user deletion if ever needed, but default is to retain attempts.
- Performance: descending created_at indexes support most-recent-first history; composite indexes on (user_id, created_at) and (status, created_at) optimize listing and lightweight metrics.

