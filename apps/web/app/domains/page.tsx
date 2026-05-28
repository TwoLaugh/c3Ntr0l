"use client";

import { FormEvent, useEffect, useState } from "react";
import { Plus } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { apiRequest, Domain } from "@/lib/api";

export default function DomainsPage() {
  const { token } = useAuth();
  const [domains, setDomains] = useState<Domain[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [weight, setWeight] = useState("1.0");

  async function load() {
    if (!token) return;
    setDomains(await apiRequest<Domain[]>("/api/v1/domains", { token }));
  }

  async function create(event: FormEvent) {
    event.preventDefault();
    if (!token || !name.trim()) return;
    await apiRequest<Domain>("/api/v1/domains", {
      method: "POST",
      token,
      body: JSON.stringify({ name, description: description || null, weight }),
    });
    setName("");
    setDescription("");
    await load();
  }

  async function toggle(domain: Domain) {
    if (!token) return;
    await apiRequest<Domain>(`/api/v1/domains/${domain.id}`, {
      method: "PATCH",
      token,
      body: JSON.stringify({ active: !domain.active }),
    });
    await load();
  }

  useEffect(() => {
    void load();
  }, [token]);

  return (
    <AppShell>
      <h1 className="page-title">Domains</h1>
      <form className="admin-form" onSubmit={create}>
        <input className="field" onChange={(event) => setName(event.target.value)} placeholder="Name" value={name} />
        <input className="field" onChange={(event) => setDescription(event.target.value)} placeholder="Description" value={description} />
        <input className="field" onChange={(event) => setWeight(event.target.value)} placeholder="Weight" value={weight} />
        <button className="primary-button" type="submit" title="Add domain">
          <Plus size={16} aria-hidden />
        </button>
      </form>
      <div className="panel">
        {domains.map((domain) => (
          <div className="row item-row" key={domain.id}>
            <div>
              <strong>{domain.name}</strong>
              <div className="muted">{domain.description ?? "No description"}</div>
              <div className="badge-row">
                <span className="badge">weight {String(domain.weight)}</span>
                <span className="badge">{domain.project_count} projects</span>
                <span className={`badge ${domain.active ? "soft" : ""}`}>{domain.active ? "active" : "inactive"}</span>
              </div>
            </div>
            <button onClick={() => toggle(domain)} type="button">
              {domain.active ? "Pause" : "Activate"}
            </button>
          </div>
        ))}
        {!domains.length ? <div className="row muted">No domains yet.</div> : null}
      </div>
    </AppShell>
  );
}
