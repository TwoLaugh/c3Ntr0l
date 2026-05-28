"use client";

import { FormEvent, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { apiRequest } from "@/lib/api";

export default function InboxPage() {
  const { token } = useAuth();
  const [rawText, setRawText] = useState("");
  const [result, setResult] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!token || !rawText.trim()) return;
    const response = await apiRequest<{ confirmation: string | null }>("/api/v1/inbox/messages", {
      method: "POST",
      token,
      body: JSON.stringify({ raw_text: rawText }),
    });
    setResult(response.confirmation ?? "Stored.");
    setRawText("");
  }

  return (
    <AppShell>
      <h1 className="page-title">Inbox</h1>
      <form className="stack" onSubmit={submit}>
        <textarea className="textarea" onChange={(event) => setRawText(event.target.value)} value={rawText} />
        <button className="primary-button" type="submit">
          Send
        </button>
      </form>
      {result ? <p className="muted">{result}</p> : null}
    </AppShell>
  );
}
