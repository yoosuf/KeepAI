const API_BASE = "/api/v1";

let _token: string | null = null;

export function setToken(token: string | null) {
  _token = token;
  if (token) {
    localStorage.setItem("keepai_token", token);
  } else {
    localStorage.removeItem("keepai_token");
  }
}

export function getToken(): string | null {
  if (!_token) {
    _token = localStorage.getItem("keepai_token");
  }
  return _token;
}

export function clearToken() {
  _token = null;
  localStorage.removeItem("keepai_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed with status ${res.status}`);
  }

  return res.json();
}

export function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

export function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export function postForm<T>(path: string, formData: URLSearchParams): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: formData,
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });
}

export function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: "DELETE" });
}

export function upload<T>(path: string, formData: FormData): Promise<T> {
  return request<T>(path, {
    method: "POST",
    body: formData,
  });
}

// Export for use in WebSocket chat
export { request }; // for custom fetch needs
