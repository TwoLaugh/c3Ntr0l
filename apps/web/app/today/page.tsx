"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { apiRequest, TodayPlan } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";

export default function TodayPage() {
  const { token } = useAuth();
  const [plan, setPlan] = useState<TodayPlan | null>(null);

  async function load() {
    if (!token) return;
    setPlan(await apiRequest<TodayPlan>("/api/v1/today", { token }));
  }

  async function regenerate() {
    if (!token) return;
    setPlan(await apiRequest<TodayPlan>("/api/v1/today/regenerate", { method: "POST", token }));
  }

  useEffect(() => {
    void load();
  }, [token]);

  return (
    <AppShell>
      <div className="toolbar">
        <h1 className="page-title">Today</h1>
        <button className="secondary-button" onClick={regenerate} type="button">
          Regenerate
        </button>
      </div>
      <div className="panel">
        {plan?.items.length ? (
          plan.items.map((item) => (
            <div className="row" key={item.id}>
              <strong>{item.title_snapshot}</strong>
              <div className="muted">{item.reason_selected ?? item.status}</div>
            </div>
          ))
        ) : (
          <div className="row muted">No plan items.</div>
        )}
      </div>
    </AppShell>
  );
}
