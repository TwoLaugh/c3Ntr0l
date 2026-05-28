"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest, AuthResponse } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";

export default function LoginPage() {
  const router = useRouter();
  const { setToken } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await apiRequest<AuthResponse>("/api/v1/auth/dev", {
        method: "POST",
      });
      setToken(response.access_token);
      router.push("/today");
    } catch {
      setError("Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-screen">
      <form className="login-box panel" onSubmit={submit}>
        <div className="row">
          <h1 className="page-title">c3Ntr0l</h1>
          <p className="muted">Local dev sign-in</p>
        </div>
        <div className="row stack">
          <button className="primary-button" disabled={loading} type="submit">
            {loading ? "Signing in" : "Continue"}
          </button>
          {error ? <p className="muted">{error}</p> : null}
        </div>
      </form>
    </main>
  );
}
