"use client";

import { useEffect, useState } from "react";
import { RotateCcw } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { AIAction, apiRequest } from "@/lib/api";

export default function AIActivityPage() {
  const { token } = useAuth();
  const [actions, setActions] = useState<AIAction[]>([]);
  const [notice, setNotice] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    setActions(await apiRequest<AIAction[]>("/api/v1/ai-actions", { token }));
  }

  async function undo(actionId: string) {
    if (!token) return;
    const response = await apiRequest<{ undone: boolean; message: string }>(`/api/v1/ai-actions/${actionId}/undo`, {
      method: "POST",
      token,
    });
    setNotice(response.message);
    await load();
  }

  useEffect(() => {
    void load();
  }, [token]);

  return (
    <AppShell>
      <h1 className="page-title">AI Activity</h1>
      {notice ? <p className="notice">{notice}</p> : null}
      <div className="panel">
        {actions.length ? (
          actions.map((action) => (
            <div className="row item-row" key={action.id}>
              <div className="item-body">
                <div className="item-heading">
                  <strong>{action.action_type}</strong>
                  <div className="badge-row">
                    <span className="badge">{action.source_type}</span>
                    <span className="badge">{action.target_type}</span>
                    {action.reversible ? <span className="badge soft">reversible</span> : null}
                  </div>
                </div>
                <div className="muted">{new Date(action.created_at).toLocaleString()}</div>
                {action.reason ? <div>{action.reason}</div> : null}
              </div>
              {action.reversible ? (
                <button onClick={() => undo(action.id)} title="Undo" type="button">
                  <RotateCcw size={16} aria-hidden />
                </button>
              ) : null}
            </div>
          ))
        ) : (
          <div className="row muted">No AI actions logged.</div>
        )}
      </div>
    </AppShell>
  );
}
