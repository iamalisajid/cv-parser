import {
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import { AuthContext, type User } from "./auth-context";

const TOKEN_KEY = "cv_parser_token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const saveToken = (t: string) => {
    localStorage.setItem(TOKEN_KEY, t);
    setToken(t);
  };

  const clearToken = () => {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  };

  const fetchMe = useCallback(async (t: string) => {
    try {
      const res = await fetch("/api/auth/me", {
        headers: { Authorization: `Bearer ${t}` },
      });
      if (!res.ok) throw new Error("unauthorized");
      const data = await res.json();
      setUser(data);
      setToken(t);
    } catch {
      clearToken();
    }
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      fetchMe(stored).finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [fetchMe]);

  const login = async (credential: string) => {
    const res = await fetch("/api/auth/google", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ credential }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(err.detail ?? "Login failed");
    }
    const data = await res.json();
    saveToken(data.token);
    setUser(data.user);
  };

  const logout = () => clearToken();

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
