import { get, post } from "./client";
import type { PaginatedPrompts, Prompt, ChatRequest, ChatResponse } from "../types";

export async function getPrompts(
  skip = 0,
  limit = 20
): Promise<PaginatedPrompts> {
  return get<PaginatedPrompts>(`/prompts?skip=${skip}&limit=${limit}`);
}

export async function getPrompt(id: number): Promise<Prompt> {
  return get<Prompt>(`/prompts/${id}`);
}

export async function createPrompt(
  promptText: string,
  options?: {
    modelName?: string;
    systemPrompt?: string;
    temperature?: number;
    topP?: number;
    maxTokens?: number;
  }
): Promise<Prompt> {
  return post<Prompt>("/prompts", {
    prompt_text: promptText,
    ...(options?.modelName && { model_name: options.modelName }),
    ...(options?.systemPrompt && { system_prompt: options.systemPrompt }),
    ...(options?.temperature !== undefined && { temperature: options.temperature }),
    ...(options?.topP !== undefined && { top_p: options.topP }),
    ...(options?.maxTokens !== undefined && { max_tokens: options.maxTokens }),
  });
}

export async function chat(
  messages: ChatRequest["messages"],
  options?: {
    modelName?: string;
    systemPrompt?: string;
    temperature?: number;
    topP?: number;
    maxTokens?: number;
  }
): Promise<ChatResponse> {
  return post<ChatResponse>("/chat", {
    messages,
    ...(options?.modelName && { model_name: options.modelName }),
    ...(options?.systemPrompt && { system_prompt: options.systemPrompt }),
    ...(options?.temperature !== undefined && { temperature: options.temperature }),
    ...(options?.topP !== undefined && { top_p: options.topP }),
    ...(options?.maxTokens !== undefined && { max_tokens: options.maxTokens }),
  });
}

export async function extractInvoice(
  textContent: string,
  modelName?: string
): Promise<Record<string, unknown>> {
  return post<Record<string, unknown>>("/extract-invoice", {
    text_content: textContent,
    ...(modelName && { model_name: modelName }),
  });
}
