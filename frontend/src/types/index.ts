export interface User {
  id: number;
  email: string;
  is_active: boolean;
  role?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Prompt {
  id: number;
  user_id: number | null;
  prompt_text: string;
  response_text: string | null;
  model_name: string;
  processing_time_ms: number | null;
  meta_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string | null;
}

export interface PaginatedPrompts {
  items: Prompt[];
  total: number;
  skip: number;
  limit: number;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatRequest {
  messages: ChatMessage[];
  model_name?: string;
  system_prompt?: string;
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
}

export interface ChatResponse {
  response_text: string;
  processing_time_ms: number;
  model_name: string;
}

export interface ModelInfo {
  name: string;
  size: number;
  digest?: string;
  modified_at?: string;
  details?: Record<string, unknown>;
}

export interface ModelListResponse {
  models: ModelInfo[];
}

// Conversation Threads
export interface Conversation {
  id: number;
  user_id: number;
  title: string | null;
  model_name: string;
  system_prompt: string | null;
  created_at: string;
  updated_at: string;
  messages: ConversationMessage[];
}

export interface ConversationSummary {
  id: number;
  title: string | null;
  model_name: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: number;
  role: string;
  content: string;
  meta_data?: Record<string, unknown>;
  created_at: string;
}

// API Keys
export interface ApiKey {
  id: number;
  name: string;
  key_preview: string;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
  expires_at: string | null;
}

export interface ApiKeyCreateResponse {
  id: number;
  name: string;
  key_preview: string;
  full_key: string;
  created_at: string;
}

// Documents
export interface Document {
  id: number;
  filename: string;
  content_type: string | null;
  file_size: number | null;
  created_at: string;
}

export interface SearchResult {
  chunk_id: number;
  document_id: number;
  filename: string;
  content: string;
  score: number;
}

// Analytics
export interface UsageStats {
  total_requests: number;
  total_processing_time_ms: number;
  avg_processing_time_ms: number;
  requests_by_model: Record<string, number>;
  requests_by_action: Record<string, number>;
  requests_today: number;
}

export interface UserUsageStats {
  user_id: number;
  email: string;
  total_requests: number;
  total_processing_time_ms: number;
}
