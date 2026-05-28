"use client";

import { FormEvent, useEffect, useState } from "react";
import { Archive, Plus, WandSparkles } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { apiRequest, Domain, Routine } from "@/lib/api";

export default function RoutinesPage() {
  const { token } = useAuth();
  const [routines, setRoutines] = useState<Routine[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [title, setTitle] = useState("");
  const [domainId, setDomainId] = useState("");
  const [rule, setRule] = useState("FREQ=DAILY");
  const [notice, setNotice] = useState<string | null>(null);

  async function load() {
    if (!token) return;
    const [nextRoutines, nextDomains] = await Promise.all([
      apiRequest<Routine[]>("/api/v1/routines", { token }),
      apiRequest<Domain[]>("/api/v1/domains", { token }),
    ]);
    setRoutines(nextRoutines);
    setDomains(nextDomains);
  }

  async function create(event: FormEvent) {
    event.preventDefault();
    if (!token || !title.trim()) return;
    await apiRequest<Routine>("/api/v1/routines", {
      method: "POST",
      token,
      body: JSON.stringify({ title, domain_id: domainId || null, recurrence_rule: rule }),
    });
    setTitle("");
    await load();
  }

  async function archive(routineId: string) {
    if (!token) return;
    await apiRequest<Routine>(`/api/v1/routines/${routineId}/archive`, { method: "POST", token });
    await load();
  }

  async function generate(routineId: string) {
    if (!token) return;
    const today = new Date().toISOString().slice(0, 10);
    const result = await apiRequest<{ instances: unknown[] }>(
      `/api/v1/routines/${routineId}/instances/generate?start_date=${today}&end_date=${today}`,
      { method: "POST", token },
    );
    setNotice(`Generated ${result.instances.length} instance(s).`);
  }

  useEffect(() => {
    void load();
  }, [token]);

  return (
    <AppShell>
      <h1 className="page-title">Routines</h1>
      <form className="admin-form" onSubmit={create}>
        <input className="field" onChange={(event) => setTitle(event.target.value)} placeholder="Title" value={title} />
        <select className="field" onChange={(event) => setDomainId(event.target.value)} value={domainId}>
          <option value="">No domain</option>
          {domains.map((domain) => (
            <option key={domain.id} value={domain.id}>
              {domain.name}
            </option>
          ))}
        </select>
        <input className="field" onChange={(event) => setRule(event.target.value)} value={rule} />
        <button className="primary-button" title="Add routine" type="submit">
          <Plus size={16} aria-hidden />
        </button>
      </form>
      {notice ? <p className="notice">{notice}</p> : null}
      <div className="panel">
        {routines.map((routine) => (
          <div className="row item-row" key={routine.id}>
            <div>
              <strong>{routine.title}</strong>
              <div className="muted">{routine.notes ?? routine.recurrence_rule}</div>
              <div className="badge-row">
                <span className="badge">{routine.active ? "active" : "inactive"}</span>
                <span className="badge">{domainName(domains, routine.domain_id)}</span>
              </div>
            </div>
            <div className="button-row compact">
              <button onClick={() => generate(routine.id)} title="Generate today" type="button">
                <WandSparkles size={16} aria-hidden />
              </button>
              <button onClick={() => archive(routine.id)} title="Archive" type="button">
                <Archive size={16} aria-hidden />
              </button>
            </div>
          </div>
        ))}
        {!routines.length ? <div className="row muted">No routines yet.</div> : null}
      </div>
    </AppShell>
  );
}

function domainName(domains: Domain[], domainId: string | null) {
  return domains.find((domain) => domain.id === domainId)?.name ?? "No domain";
}
