"use client";

import { FormEvent, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { apiRequest } from "@/lib/api";

export default function InboxPage() {
  const { token } = useAuth();
  const [rawText, setRawText] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setResult(null);
    if (!rawText.trim()) return;
    if (!token) {
      setError("No active session. Sign in again.");
      return;
    }

    setLoading(true);
    try {
      const response = await apiRequest<{ confirmation: string | null; processing_status: string }>(
        "/api/v1/inbox/messages",
        {
          method: "POST",
          token,
          body: JSON.stringify({ raw_text: rawText }),
        },
      );
      setResult(response.confirmation ?? `Stored: ${response.processing_status}`);
      setRawText("");
    } catch (caught) {
      const detail = caught && typeof caught === "object" && "detail" in caught ? caught.detail : null;
      setError(typeof detail === "string" ? detail : "Inbox request failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <h1 className="page-title">Inbox</h1>
      <form className="stack" onSubmit={submit}>
        <textarea className="textarea" disabled={loading} onChange={(event) => setRawText(event.target.value)} value={rawText} />
        <button className="primary-button" disabled={loading || !rawText.trim()} type="submit">
          {loading ? "Thinking" : "Send"}
        </button>
      </form>
      {result ? <p className="muted">{result}</p> : null}
      {error ? <p className="muted">{error}</p> : null}
    </AppShell>
  );
}
