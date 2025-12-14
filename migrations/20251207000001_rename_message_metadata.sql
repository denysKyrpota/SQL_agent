-- Migration: Rename metadata column to message_metadata to avoid SQLAlchemy conflict
-- Created: 2025-12-07

-- SQLite doesn't support RENAME COLUMN directly in older versions
-- So we'll use ALTER TABLE ... RENAME COLUMN which is supported in SQLite 3.25+
ALTER TABLE messages RENAME COLUMN metadata TO message_metadata;
