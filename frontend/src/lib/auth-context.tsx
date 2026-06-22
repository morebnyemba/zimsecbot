"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { apiFetch, isAuthenticated, login as apiLogin, logout as apiLogout } from "./api";

export type Role = "student" | "content_admin" | "superadmin" | "support" | "school_admin";

export type CurrentUser = {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
};

type AuthContextValue = {
  user: CurrentUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    if (!isAuthenticated()) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await apiFetch<CurrentUser>("/api/v1/auth/me/");
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time session check on mount
    loadUser();
  }, [loadUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      await apiLogin(email, password);
      await loadUser();
    },
    [loadUser],
  );

  const logout = useCallback(() => {
    apiLogout();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
}
