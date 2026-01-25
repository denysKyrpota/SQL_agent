/**
 * ChatPanel Component
 *
 * Main chat interface for conversational SQL generation
 * Features:
 * - Message history display
 * - Send new messages
 * - Edit/regenerate messages
 * - Execute generated queries
 */

import React, { useState, useEffect, useRef } from 'react';
import { chatService, Message } from '@/services/chatService';
import MessageBubble from '@/components/MessageBubble';
import TextArea from '@/components/TextArea';
import Button from '@/components/Button';
import styles from './ChatPanel.module.css';

interface ChatPanelProps {
  conversationId?: number;
  onQueryExecute?: (queryAttemptId: number) => void;
  onConversationChange?: (conversationId: number) => void;
  className?: string;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  conversationId: initialConversationId,
  onQueryExecute,
  onConversationChange,
  className,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<number | undefined>(
    initialConversationId
  );
  const [regeneratingMessageId, setRegeneratingMessageId] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Sync internal conversationId with prop
  useEffect(() => {
    if (initialConversationId !== undefined && initialConversationId !== conversationId) {
      setConversationId(initialConversationId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialConversationId]);

  // Load conversation messages
  useEffect(() => {
    if (conversationId) {
      loadMessages();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadMessages = async () => {
    if (!conversationId) return;

    try {
      const response = await chatService.getConversationMessages(conversationId);
      setMessages(response.messages);
    } catch (error) {
      console.error('Failed to load messages:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const messageContent = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await chatService.sendMessage({
        content: messageContent,
        conversation_id: conversationId,
      });

      // Update conversation ID if it's a new conversation
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
        onConversationChange?.(response.conversation_id);
      }

      // Add both user and assistant messages
      setMessages((prev) => [
        ...prev,
        response.user_message,
        response.assistant_message,
      ]);
    } catch (error) {
      console.error('Failed to send message:', error);
      // TODO: Show error toast
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegenerateMessage = async (messageId: number) => {
    setRegeneratingMessageId(messageId);

    try {
      const newMessage = await chatService.regenerateMessage(messageId);

      // Add the new message to the end
      setMessages((prev) => [...prev, newMessage]);
    } catch (error) {
      console.error('Failed to regenerate message:', error);
      // TODO: Show error toast
    } finally {
      setRegeneratingMessageId(null);
    }
  };

  const handleEditMessage = (messageId: number) => {
    // Find the message to edit
    const messageToEdit = messages.find((m) => m.id === messageId);
    if (!messageToEdit) return;

    // Set input value to the message content
    setInputValue(messageToEdit.content);

    // TODO: In a more complete implementation, we would:
    // 1. Show an "Editing" indicator
    // 2. On send, call chatService.editMessage() instead of sendMessage
    // 3. Update the message list appropriately
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className={`${styles.chatPanel} ${className || ''}`}>
      {/* Messages container */}
      <div className={styles.messagesContainer}>
        {messages.length === 0 ? (
          <div className={styles.emptyState}>
            <div className={styles.emptyStateIcon}>💬</div>
            <h3 className={styles.emptyStateTitle}>Start a conversation</h3>
            <p className={styles.emptyStateText}>
              Ask me anything about your data, and I'll generate SQL queries to help you find answers.
            </p>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onExecuteQuery={onQueryExecute}
                onEditMessage={handleEditMessage}
                onRegenerateMessage={handleRegenerateMessage}
                isRegenerating={regeneratingMessageId === message.id}
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input container */}
      <div className={styles.inputContainer}>
        <TextArea
          value={inputValue}
          onChange={setInputValue}
          onKeyDown={handleKeyPress}
          placeholder="Ask a question about your data..."
          rows={3}
          disabled={isLoading}
          className={styles.messageInput}
        />
        <div className={styles.inputActions}>
          <div className={styles.inputHint}>
            Press Enter to send, Shift+Enter for new line
          </div>
          <Button
            variant="primary"
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            loading={isLoading}
          >
            {isLoading ? 'Generating...' : 'Send'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;
