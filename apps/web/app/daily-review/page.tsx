"use client";

import { FormEvent, useEffect, useState } from "react";
import { Send } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { apiRequest, DailyReviewPrompt } from "@/lib/api";

export default function DailyReviewPage() {
  const { token } = useAuth();
  const [prompt, setPrompt] = useState<DailyReviewPrompt | null>(null);
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [energyLevel, setEnergyLevel] = useState("");
  const [loadFit, setLoadFit] = useState("");
  const [mood, setMood] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const today = new Date().toISOString().slice(0, 10);

  async function load() {
    if (!token) return;
    setPrompt(await apiRequest<DailyReviewPrompt>(`/api/v1/reviews/daily/${today}/prompt`, { token }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    await apiRequest(`/api/v1/reviews/daily/${today}`, {
      method: "POST",
      token,
      body: JSON.stringify({
        responses,
        energy_level: energyLevel || null,
        load_fit: loadFit || null,
        mood: mood || null,
      }),
    });
    setStatus("Review saved.");
  }

  useEffect(() => {
    void load();
  }, [token]);

  return (
    <AppShell>
      <h1 className="page-title">Daily Review</h1>
      <form className="stack" onSubmit={submit}>
        <div className="form-grid three">
          <label>
            <span className="label">Energy</span>
            <select className="field" onChange={(event) => setEnergyLevel(event.target.value)} value={energyLevel}>
              <option value="">Unset</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
          <label>
            <span className="label">Load fit</span>
            <input className="field" onChange={(event) => setLoadFit(event.target.value)} value={loadFit} />
          </label>
          <label>
            <span className="label">Mood</span>
            <input className="field" onChange={(event) => setMood(event.target.value)} value={mood} />
          </label>
        </div>
        <div className="panel">
          {prompt?.prompts.length ? (
            prompt.prompts.map((item) => (
              <label className="row stack" key={item.plan_item_id}>
                <span>
                  <strong>{item.title}</strong>
                  <span className="badge-row inline">
                    <span className="badge">{item.prompt_type}</span>
                    <span className="badge">score {item.importance_score}</span>
                  </span>
                </span>
                <span className="muted">{item.question}</span>
                <textarea
                  className="textarea compact-textarea"
                  onChange={(event) => setResponses((current) => ({ ...current, [item.plan_item_id]: event.target.value }))}
                  value={responses[item.plan_item_id] ?? ""}
                />
              </label>
            ))
          ) : (
            <div className="row muted">No task-aware review prompts for today.</div>
          )}
        </div>
        {prompt?.quick_checks.length ? (
          <div className="panel">
            {prompt.quick_checks.map((check) => (
              <div className="row muted" key={check}>
                {check}
              </div>
            ))}
          </div>
        ) : null}
        <button className="primary-button icon-button-text" type="submit">
          <Send size={16} aria-hidden />
          Save review
        </button>
      </form>
      {status ? <p className="notice">{status}</p> : null}
    </AppShell>
  );
}
