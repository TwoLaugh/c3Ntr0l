"use client";

import { useEffect, useState } from "react";
import { CalendarPlus, CheckCircle, RefreshCw } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { apiRequest, WeeklyPlan } from "@/lib/api";

export default function WeeklyReviewPage() {
  const { token } = useAuth();
  const [plan, setPlan] = useState<WeeklyPlan | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    try {
      setPlan(await apiRequest<WeeklyPlan>("/api/v1/weekly-planning/current", { token }));
      setError(null);
    } catch {
      setError("No weekly plan yet.");
      setPlan(null);
    }
  }

  async function generate() {
    if (!token) return;
    setPlan(await apiRequest<WeeklyPlan>("/api/v1/weekly-planning/generate", { method: "POST", token }));
    setError(null);
  }

  async function accept() {
    if (!token || !plan) return;
    setPlan(await apiRequest<WeeklyPlan>(`/api/v1/weekly-planning/${plan.id}/accept`, { method: "POST", token }));
  }

  async function regenerateDay(planDate: string) {
    if (!token || !plan) return;
    setPlan(
      await apiRequest<WeeklyPlan>(`/api/v1/weekly-planning/${plan.id}/regenerate-day?plan_date=${planDate}`, {
        method: "POST",
        token,
      }),
    );
  }

  useEffect(() => {
    void load();
  }, [token]);

  return (
    <AppShell>
      <div className="toolbar spread">
        <div>
          <h1 className="page-title">Week</h1>
          {plan ? <div className="muted">Week starting {plan.week_start_date}</div> : null}
        </div>
        <div className="button-row">
          <button className="secondary-button icon-button-text" onClick={generate} type="button">
            <CalendarPlus size={16} aria-hidden />
            Generate
          </button>
          {plan ? (
            <button className="primary-button icon-button-text" onClick={accept} type="button">
              <CheckCircle size={16} aria-hidden />
              Accept
            </button>
          ) : null}
        </div>
      </div>
      {error ? <p className="notice">{error}</p> : null}
      {plan ? (
        <div className="stack">
          <section className="panel">
            <div className="row">
              <strong>{plan.status}</strong>
              <div className="muted">{plan.summary ?? "No summary yet."}</div>
              {plan.focus_notes ? <div>{plan.focus_notes}</div> : null}
            </div>
          </section>
          <div className="week-grid">
            {plan.daily_plans.map((day) => (
              <section className="panel day-panel" key={day.id}>
                <div className="row day-heading">
                  <strong>{new Date(`${day.plan_date}T00:00:00`).toLocaleDateString([], { weekday: "short", day: "numeric" })}</strong>
                  <button onClick={() => regenerateDay(day.plan_date)} title="Regenerate day" type="button">
                    <RefreshCw size={15} aria-hidden />
                  </button>
                </div>
                {day.items.length ? (
                  day.items.map((item) => (
                    <div className="row mini-row" key={item.id}>
                      <strong>{item.title_snapshot}</strong>
                      <div className="muted">{item.block_type}</div>
                    </div>
                  ))
                ) : (
                  <div className="row muted">No planned items.</div>
                )}
              </section>
            ))}
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
