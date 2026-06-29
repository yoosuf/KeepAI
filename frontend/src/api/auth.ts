import { post, postForm } from "./client";
import type { Token, User } from "../types";

export async function login(username: string, password: string): Promise<Token> {
  const formData = new URLSearchParams();
  formData.append("username", username);
  formData.append("password", password);
  return postForm<Token>("/auth/login", formData);
}

export async function register(
  email: string,
  password: string,
  role: string = "user"
): Promise<User> {
  return post<User>("/auth/register", { email, password, role });
}
