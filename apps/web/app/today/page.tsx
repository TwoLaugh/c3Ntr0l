"use client";

import { useEffect, useMemo, useState } from "react";
import { Check, List, MoveRight, RefreshCw, SkipForward, TimerReset } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { apiRequest, TodayPlan } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";

type ViewMode = "timeline" | "list";

export default function TodayPage() {
  const { token } = useAuth();
  const [plan, setPlan] = useState<TodayPlan | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("timeline");
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const sortedItems = useMemo(() => [...(plan?.items ?? [])].sort((a, b) => a.position - b.position), [plan]);

  async function load() {
    if (!token) return;
    setError(null);
    try {
      const nextPlan = await apiRequest<TodayPlan>("/api/v1/today", { token });
      setPlan(nextPlan);
      setViewMode(nextPlan.default_view_mode === "list" ? "list" : "timeline");
    } catch {
      setError("Could not load today's plan.");
    }
  }

  async function regenerate() {
    if (!token) return;
    setError(null);
    const nextPlan = await apiRequest<TodayPlan>("/api/v1/today/regenerate", { method: "POST", token });
    setPlan(nextPlan);
  }

  async function itemAction(itemId: string, action: "complete" | "partial" | "skip" | "move") {
    if (!token) return;
    setBusyId(itemId);
    try {
      if (action === "complete") {
        await apiRequest(`/api/v1/today/items/${itemId}/complete`, { method: "POST", token, body: JSON.stringify({}) });
      }
      if (action === "partial") {
        const amount = window.prompt("What got done?") ?? "";
        const note = window.prompt("Any note for the review?") ?? "";
        await apiRequest(`/api/v1/today/items/${itemId}/partial`, {
          method: "POST",
          token,
          body: JSON.stringify({ amount_done: amount || null, note: note || null }),
        });
      }
      if (action === "skip") {
        const note = window.prompt("Why skip this?") ?? "";
        await apiRequest(`/api/v1/today/items/${itemId}/skip`, {
          method: "POST",
          token,
          body: JSON.stringify({ note: note || null }),
        });
      }
      if (action === "move") {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        await apiRequest(`/api/v1/today/items/${itemId}/move`, {
          method: "POST",
          token,
          body: JSON.stringify({ target_plan_date: tomorrow.toISOString().slice(0, 10), note: "Moved from Today web UI" }),
        });
      }
      await load();
    } catch {
      setError("Could not update that item.");
    } finally {
      setBusyId(null);
    }
  }

  useEffect(() => {
    void load();
  }, [token]);

  return (
    <AppShell>
      <div className="toolbar spread">
        <div>
          <h1 className="page-title">Today</h1>
          {plan?.summary ? <div className="muted">{plan.summary}</div> : null}
        </div>
        <div className="button-row">
          <div className="segmented" aria-label="Today view">
            <button className={viewMode === "timeline" ? "active" : ""} onClick={() => setViewMode("timeline")} type="button">
              <TimerReset size={16} aria-hidden />
              Timeline
            </button>
            <button className={viewMode === "list" ? "active" : ""} onClick={() => setViewMode("list")} type="button">
              <List size={16} aria-hidden />
              List
            </button>
          </div>
          <button className="secondary-button icon-button-text" onClick={regenerate} type="button">
            <RefreshCw size={16} aria-hidden />
            Regenerate
          </button>
        </div>
      </div>
      {error ? <p className="notice">{error}</p> : null}
      <div className={viewMode === "timeline" ? "timeline" : "panel"}>
        {sortedItems.length ? (
          sortedItems.map((item) => (
            <div className={viewMode === "timeline" ? "timeline-item" : "row item-row"} key={item.id}>
              {viewMode === "timeline" ? (
                <div className="time-cell">
                  <strong>{formatTimeRange(item.suggested_start, item.suggested_end)}</strong>
                  <span>{formatTimeRange(item.do_window_start, item.do_window_end)}</span>
                </div>
              ) : null}
              <div className="item-body">
                <div className="item-heading">
                  <strong>{item.title_snapshot}</strong>
                  <div className="badge-row">
                    <span className={`badge ${item.status}`}>{item.status}</span>
                    <span className="badge">{item.block_type}</span>
                    {item.is_optional ? <span className="badge soft">optional</span> : null}
                    {item.is_fixed_time ? <span className="badge fixed">fixed</span> : null}
                  </div>
                </div>
                {item.reason_selected ? <div className="muted">{item.reason_selected}</div> : null}
                <div className="button-row compact">
                  <button disabled={busyId === item.id} onClick={() => itemAction(item.id, "complete")} title="Complete" type="button">
                    <Check size={16} aria-hidden />
                  </button>
                  <button disabled={busyId === item.id} onClick={() => itemAction(item.id, "partial")} title="Partial" type="button">
                    <TimerReset size={16} aria-hidden />
                  </button>
                  <button disabled={busyId === item.id} onClick={() => itemAction(item.id, "skip")} title="Skip" type="button">
                    <SkipForward size={16} aria-hidden />
                  </button>
                  <button disabled={busyId === item.id} onClick={() => itemAction(item.id, "move")} title="Move tomorrow" type="button">
                    <MoveRight size={16} aria-hidden />
                  </button>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="row muted">No plan items.</div>
        )}
      </div>
    </AppShell>
  );
}

function formatTimeRange(start: string | null, end: string | null) {
  if (!start && !end) return "Flexible";
  const startText = start ? new Date(start).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "?";
  const endText = end ? new Date(end).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "?";
  return `${startText} - ${endText}`;
}
