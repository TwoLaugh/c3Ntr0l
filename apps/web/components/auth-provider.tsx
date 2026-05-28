"use client";

import { createContext, useContext, useEffect, useMemo, useState } from "react";

type AuthContextValue = {
  token: string | null;
  setToken: (token: string) => void;
  clearAuth: () => void;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setTokenState] = useState<string | null>(null);

  useEffect(() => {
    setTokenState(window.localStorage.getItem("c3ntr0l_token"));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      token,
      setToken(nextToken) {
        window.localStorage.setItem("c3ntr0l_token", nextToken);
        setTokenState(nextToken);
      },
      clearAuth() {
        window.localStorage.removeItem("c3ntr0l_token");
        setTokenState(null);
      },
    }),
    [token],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
