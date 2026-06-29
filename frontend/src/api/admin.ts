import { get } from "./client";
import type { User, Prompt } from "../types";

export async function getUsers(skip = 0, limit = 100): Promise<User[]> {
  return get<User[]>(`/admin/users?skip=${skip}&limit=${limit}`);
}

export async function getAllPrompts(skip = 0, limit = 100): Promise<Prompt[]> {
  return get<Prompt[]>(`/admin/all-prompts?skip=${skip}&limit=${limit}`);
}
