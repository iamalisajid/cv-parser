import { createContext, useContext } from "react";

export interface User {
  email: string;
  name: string;
  picture: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (credential: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
