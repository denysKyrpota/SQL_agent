/**
 * Chat Service - API client for conversational SQL generation
 */

import { apiClient } from './apiClient';

/**
 * Chat-related types
 */
export interface Conversation {
  id: number;
  user_id: number;
  title: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant' | 'system';
  content: string;
  query_attempt_id: number | null;
  parent_message_id: number | null;
  is_edited: boolean;
  is_regenerated: boolean;
  created_at: string;
  metadata: Record<string, any> | null;
}

export interface SendMessageRequest {
  content: string;
  conversation_id?: number;
}

export interface SendMessageResponse {
  conversation_id: number;
  user_message: Message;
  assistant_message: Message;
}

export interface ConversationListResponse {
  conversations: Conversation[];
  pagination: {
    page: number;
    page_size: number;
    total_count: number;
    total_pages: number;
  };
}

export interface ConversationMessagesResponse {
  conversation_id: number;
  messages: Message[];
}

/**
 * Chat Service
 */
export const chatService = {
  /**
   * Create a new conversation
   */
  createConversation: async (title?: string): Promise<Conversation> => {
    return apiClient.post<Conversation>('/chat/conversations', {
      title,
    });
  },

  /**
   * List user's conversations with pagination
   */
  listConversations: async (
    page: number = 1,
    pageSize: number = 20
  ): Promise<ConversationListResponse> => {
    return apiClient.get<ConversationListResponse>(
      `/chat/conversations?page=${page}&page_size=${pageSize}`
    );
  },

  /**
   * Get all messages in a conversation
   */
  getConversationMessages: async (
    conversationId: number
  ): Promise<ConversationMessagesResponse> => {
    return apiClient.get<ConversationMessagesResponse>(
      `/chat/conversations/${conversationId}/messages`
    );
  },

  /**
   * Send a message and receive AI response
   */
  sendMessage: async (
    request: SendMessageRequest
  ): Promise<SendMessageResponse> => {
    return apiClient.post<SendMessageResponse>('/chat/messages', request);
  },

  /**
   * Regenerate an assistant message
   */
  regenerateMessage: async (messageId: number): Promise<Message> => {
    return apiClient.put<Message>(`/chat/messages/${messageId}/regenerate`, {});
  },

  /**
   * Edit a user message
   */
  editMessage: async (messageId: number, content: string): Promise<Message> => {
    return apiClient.put<Message>(`/chat/messages/${messageId}`, {
      content,
    });
  },
};

export default chatService;
