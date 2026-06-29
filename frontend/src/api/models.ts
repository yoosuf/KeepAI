import { get, post, del } from "./client";
import type { ModelListResponse } from "../types";

export async function listModels(): Promise<ModelListResponse> {
  return get<ModelListResponse>("/models");
}

export async function pullModel(name: string): Promise<{ status: string }> {
  return post<{ status: string }>("/models/pull", { name });
}

export async function deleteModel(name: string): Promise<{ status: string }> {
  return del<{ status: string }>(`/models/${encodeURIComponent(name)}`);
}
