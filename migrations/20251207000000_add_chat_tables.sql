-- Migration: Add chat tables for conversational SQL generation
-- Created: 2025-12-07

-- Conversations table: stores conversation threads for each user
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,  -- Optional title (e.g., first message preview)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,  -- Soft delete flag
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Messages table: stores individual chat messages in conversations
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    query_attempt_id INTEGER,  -- Links to QueryAttempt if SQL was generated
    parent_message_id INTEGER,  -- For edited messages (points to original)
    is_edited BOOLEAN DEFAULT 0,
    is_regenerated BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message_metadata TEXT,  -- JSON field for additional data (token count, model, etc.)
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    FOREIGN KEY (query_attempt_id) REFERENCES query_attempts(id) ON DELETE SET NULL,
    FOREIGN KEY (parent_message_id) REFERENCES messages(id) ON DELETE SET NULL
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_query_attempt_id ON messages(query_attempt_id);

-- Trigger to update conversations.updated_at when new message is added
CREATE TRIGGER IF NOT EXISTS update_conversation_timestamp
AFTER INSERT ON messages
BEGIN
    UPDATE conversations
    SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.conversation_id;
END;
