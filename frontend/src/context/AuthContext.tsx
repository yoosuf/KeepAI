import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";
import { getToken, setToken, clearToken } from "../api/client";
import { login as apiLogin, register as apiRegister } from "../api/auth";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, password: string, role?: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setTokenState] = useState<string | null>(getToken());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split(".")[1] || ""));
        setUser({
          id: payload.user_id ?? 0,
          email: payload.sub ?? "",
          is_active: true,
        });
      } catch {
        clearToken();
        setTokenState(null);
      }
    }
    setLoading(false);
  }, [token]);

  const login = useCallback(async (username: string, password: string) => {
    const result = await apiLogin(username, password);
    setToken(result.access_token);
    setTokenState(result.access_token);
  }, []);

  const register = useCallback(
    async (email: string, password: string, role = "user") => {
      await apiRegister(email, password, role);
    },
    []
  );

  const logout = useCallback(() => {
    clearToken();
    setTokenState(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        isAuthenticated: !!token,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
