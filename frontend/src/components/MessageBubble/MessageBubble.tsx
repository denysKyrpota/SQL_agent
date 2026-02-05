/**
 * MessageBubble Component
 *
 * Displays individual chat messages with:
 * - User/assistant role styling
 * - SQL code blocks with syntax highlighting
 * - Execute button for generated queries
 * - Copy button for SQL queries
 * - Edit/regenerate actions
 */

import React, { useState } from 'react';
import { Message } from '@/services/chatService';
import Button from '@/components/Button';
import styles from './MessageBubble.module.css';

interface MessageBubbleProps {
  message: Message;
  onExecuteQuery?: (queryAttemptId: number) => void;
  onEditMessage?: (messageId: number) => void;
  onRegenerateMessage?: (messageId: number) => void;
  isRegenerating?: boolean;
}

/**
 * Extract SQL from markdown code block
 * Handles various line endings (\n, \r\n) and whitespace variations
 */
function extractSQL(content: string): string | null {
  // More flexible regex that handles different line endings and whitespace
  const sqlBlockRegex = /```sql\s*([\s\S]*?)\s*```/;
  const match = content.match(sqlBlockRegex);
  return match ? match[1].trim() : null;
}

/**
 * Render message content with SQL code blocks
 */
function renderContent(content: string, role: Message['role']): React.ReactNode {
  if (role === 'user') {
    return <p className={styles.messageText}>{content}</p>;
  }

  // For assistant messages, check if there's a SQL code block
  // Flexible regex that handles different line endings and whitespace
  const sqlBlockRegex = /```sql\s*([\s\S]*?)\s*```/;
  const match = content.match(sqlBlockRegex);

  if (!match) {
    return <p className={styles.messageText}>{content}</p>;
  }

  // Split content into parts
  const beforeSQL = content.substring(0, match.index);
  const sqlCode = match[1].trim();
  const afterSQL = content.substring(match.index! + match[0].length);

  return (
    <>
      {beforeSQL && <p className={styles.messageText}>{beforeSQL}</p>}
      <div className={styles.codeBlock}>
        <div className={styles.codeHeader}>
          <span className={styles.codeLabel}>SQL Query</span>
        </div>
        <pre className={styles.codeContent}>
          <code>{sqlCode}</code>
        </pre>
      </div>
      {afterSQL && <p className={styles.messageText}>{afterSQL}</p>}
    </>
  );
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onExecuteQuery,
  onEditMessage,
  onRegenerateMessage,
  isRegenerating = false,
}) => {
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const hasSQL = message.query_attempt_id !== null;
  const [copySuccess, setCopySuccess] = useState(false);

  const handleExecute = () => {
    if (hasSQL && onExecuteQuery) {
      onExecuteQuery(message.query_attempt_id!);
    }
  };

  const handleEdit = () => {
    if (onEditMessage) {
      onEditMessage(message.id);
    }
  };

  const handleRegenerate = () => {
    if (onRegenerateMessage) {
      onRegenerateMessage(message.id);
    }
  };

  const handleCopy = async () => {
    const sql = extractSQL(message.content);
    if (!sql) return;

    try {
      // Try modern clipboard API first (requires HTTPS or localhost)
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(sql);
      } else {
        // Fallback for HTTP: use textarea + execCommand
        const textArea = document.createElement('textarea');
        textArea.value = sql;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
      }
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (error) {
      console.error('Failed to copy SQL:', error);
    }
  };

  return (
    <div className={`${styles.messageContainer} ${isUser ? styles.userMessage : styles.assistantMessage}`}>
      <div className={styles.messageBubble}>
        <div className={styles.messageHeader}>
          <span className={styles.messageRole}>
            {isUser ? 'You' : 'Assistant'}
          </span>
          <span className={styles.messageTime}>
            {new Date(message.created_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>

        <div className={styles.messageContent}>
          {renderContent(message.content, message.role)}
        </div>

        {/* Actions */}
        <div className={styles.messageActions}>
          {isUser && onEditMessage && (
            <Button
              variant="ghost"
              size="small"
              onClick={handleEdit}
              className={styles.actionButton}
            >
              Edit
            </Button>
          )}

          {isAssistant && onRegenerateMessage && (
            <Button
              variant="ghost"
              size="small"
              onClick={handleRegenerate}
              disabled={isRegenerating}
              className={styles.actionButton}
            >
              {isRegenerating ? (
                <span className={styles.regeneratingContent}>
                  <span className={styles.smallSpinner} />
                  Regenerating...
                </span>
              ) : (
                'Regenerate'
              )}
            </Button>
          )}

          {hasSQL && onExecuteQuery && (
            <Button
              variant="primary"
              size="small"
              onClick={handleExecute}
              className={styles.actionButton}
            >
              Execute Query
            </Button>
          )}

          {hasSQL && (
            <Button
              variant="secondary"
              size="small"
              onClick={handleCopy}
              className={styles.actionButton}
            >
              {copySuccess ? 'Copied!' : 'Copy SQL'}
            </Button>
          )}
        </div>

        {/* Metadata badges */}
        {(message.is_edited || message.is_regenerated) && (
          <div className={styles.messageBadges}>
            {message.is_edited && (
              <span className={styles.badge}>Edited</span>
            )}
            {message.is_regenerated && (
              <span className={styles.badge}>Regenerated</span>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default MessageBubble;
