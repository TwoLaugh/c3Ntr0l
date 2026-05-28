"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { apiRequest } from "@/lib/api";

export default function InboxPage() {
  const { token } = useAuth();
  const [rawText, setRawText] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<InboxMessage[]>([]);

  async function loadMessages() {
    if (!token) return;
    setMessages(await apiRequest<InboxMessage[]>("/api/v1/inbox/messages", { token }));
  }

  useEffect(() => {
    void loadMessages();
  }, [token]);

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
      await loadMessages();
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
      <div className="chat-list">
        {messages.map((message) => (
          <div className="chat-turn" key={message.id}>
            <div className="chat-bubble user-bubble">{message.raw_text}</div>
            <div className="chat-bubble assistant-bubble">{assistantText(message)}</div>
          </div>
        ))}
      </div>
    </AppShell>
  );
}

type InboxMessage = {
  id: string;
  raw_text: string;
  processing_status: string;
  parsed_intents: {
    confirmation?: string | null;
    clarification_question?: string | null;
    intents?: Array<{ no_op_reason?: string | null; title?: string | null; intent_type?: string }>;
  } | null;
};

function assistantText(message: InboxMessage) {
  if (message.parsed_intents?.clarification_question) return message.parsed_intents.clarification_question;
  if (message.parsed_intents?.confirmation) return message.parsed_intents.confirmation;
  const firstIntent = message.parsed_intents?.intents?.[0];
  if (firstIntent?.no_op_reason) return firstIntent.no_op_reason;
  if (firstIntent?.title && firstIntent.intent_type === "create_task") return `Created task: ${firstIntent.title}`;
  if (firstIntent?.title && firstIntent.intent_type === "create_routine") return `Created routine: ${firstIntent.title}`;
  if (message.processing_status === "unsupported") return "Stored, but I could not apply it safely.";
  return message.processing_status;
}
