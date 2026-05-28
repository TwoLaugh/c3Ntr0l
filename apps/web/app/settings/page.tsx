"use client";

import { FormEvent, useEffect, useState } from "react";
import { Save } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { apiRequest, LearnedCapabilityProfile, UserProfile } from "@/lib/api";

export default function SettingsPage() {
  const { token } = useAuth();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [learned, setLearned] = useState<LearnedCapabilityProfile | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    const [nextProfile, nextLearned] = await Promise.all([
      apiRequest<UserProfile>("/api/v1/profile", { token }),
      apiRequest<LearnedCapabilityProfile>("/api/v1/profile/learned-capability", { token }),
    ]);
    setProfile(nextProfile);
    setLearned(nextLearned);
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!token || !profile) return;
    setProfile(
      await apiRequest<UserProfile>("/api/v1/profile", {
        method: "PATCH",
        token,
        body: JSON.stringify({
          timezone: profile.timezone,
          default_tone: profile.default_tone,
          preferred_day_view: profile.preferred_day_view,
          wake_time: profile.wake_time || null,
          sleep_time: profile.sleep_time || null,
          planning_style: profile.planning_style || null,
          review_style: profile.review_style || null,
          ai_change_visibility: profile.ai_change_visibility,
        }),
      }),
    );
    setNotice("Settings saved.");
  }

  useEffect(() => {
    void load();
  }, [token]);

  return (
    <AppShell>
      <h1 className="page-title">Settings</h1>
      {profile ? (
        <form className="stack" onSubmit={save}>
          <section className="panel settings-panel">
            <label>
              <span className="label">Timezone</span>
              <input className="field" onChange={(event) => setProfile({ ...profile, timezone: event.target.value })} value={profile.timezone} />
            </label>
            <label>
              <span className="label">Assistant tone</span>
              <select className="field" onChange={(event) => setProfile({ ...profile, default_tone: event.target.value as UserProfile["default_tone"] })} value={profile.default_tone}>
                <option value="terse">Terse</option>
                <option value="warm">Warm</option>
                <option value="direct">Direct</option>
              </select>
            </label>
            <label>
              <span className="label">Default day view</span>
              <select className="field" onChange={(event) => setProfile({ ...profile, preferred_day_view: event.target.value as UserProfile["preferred_day_view"] })} value={profile.preferred_day_view}>
                <option value="timeline">Timeline</option>
                <option value="list">List</option>
              </select>
            </label>
            <label>
              <span className="label">AI change visibility</span>
              <select className="field" onChange={(event) => setProfile({ ...profile, ai_change_visibility: event.target.value as UserProfile["ai_change_visibility"] })} value={profile.ai_change_visibility}>
                <option value="quiet">Quiet</option>
                <option value="digest">Digest</option>
                <option value="prompt">Prompt</option>
              </select>
            </label>
            <label>
              <span className="label">Wake</span>
              <input className="field" onChange={(event) => setProfile({ ...profile, wake_time: event.target.value })} type="time" value={profile.wake_time ?? ""} />
            </label>
            <label>
              <span className="label">Sleep</span>
              <input className="field" onChange={(event) => setProfile({ ...profile, sleep_time: event.target.value })} type="time" value={profile.sleep_time ?? ""} />
            </label>
            <label className="wide-field">
              <span className="label">Planning style</span>
              <textarea className="textarea compact-textarea" onChange={(event) => setProfile({ ...profile, planning_style: event.target.value })} value={profile.planning_style ?? ""} />
            </label>
            <label className="wide-field">
              <span className="label">Review style</span>
              <textarea className="textarea compact-textarea" onChange={(event) => setProfile({ ...profile, review_style: event.target.value })} value={profile.review_style ?? ""} />
            </label>
          </section>
          <button className="primary-button icon-button-text" type="submit">
            <Save size={16} aria-hidden />
            Save settings
          </button>
        </form>
      ) : (
        <button className="secondary-button" onClick={load} type="button">
          Load settings
        </button>
      )}
      {notice ? <p className="notice">{notice}</p> : null}
      {learned ? (
        <section className="panel stats-panel">
          <div className="row">
            <strong>Learned capability</strong>
          </div>
          <div className="stats-grid">
            <Stat label="Weekday focus" value={learned.weekday_focus_minutes_typical} suffix="min" />
            <Stat label="Weekend focus" value={learned.weekend_focus_minutes_typical} suffix="min" />
            <Stat label="14d completion" value={learned.plan_completion_rate_14d} />
            <Stat label="Confidence" value={learned.confidence_score} />
          </div>
        </section>
      ) : null}
    </AppShell>
  );
}

function Stat({ label, value, suffix = "" }: { label: string; value: number | null; suffix?: string }) {
  return (
    <div className="stat">
      <span className="muted">{label}</span>
      <strong>{value === null ? "n/a" : `${value}${suffix}`}</strong>
    </div>
  );
}
