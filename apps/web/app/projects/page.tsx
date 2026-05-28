"use client";

import { FormEvent, useEffect, useState } from "react";
import { Archive, Plus } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { apiRequest, Domain, Project } from "@/lib/api";

export default function ProjectsPage() {
  const { token } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [title, setTitle] = useState("");
  const [domainId, setDomainId] = useState("");
  const [outcome, setOutcome] = useState("");

  async function load() {
    if (!token) return;
    const [nextProjects, nextDomains] = await Promise.all([
      apiRequest<Project[]>("/api/v1/projects", { token }),
      apiRequest<Domain[]>("/api/v1/domains", { token }),
    ]);
    setProjects(nextProjects);
    setDomains(nextDomains);
  }

  async function create(event: FormEvent) {
    event.preventDefault();
    if (!token || !title.trim()) return;
    await apiRequest<Project>("/api/v1/projects", {
      method: "POST",
      token,
      body: JSON.stringify({ title, domain_id: domainId || null, desired_outcome: outcome || null }),
    });
    setTitle("");
    setOutcome("");
    await load();
  }

  async function archive(projectId: string) {
    if (!token) return;
    await apiRequest<Project>(`/api/v1/projects/${projectId}/archive`, { method: "POST", token });
    await load();
  }

  useEffect(() => {
    void load();
  }, [token]);

  return (
    <AppShell>
      <h1 className="page-title">Projects</h1>
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
        <input className="field" onChange={(event) => setOutcome(event.target.value)} placeholder="Desired outcome" value={outcome} />
        <button className="primary-button" title="Add project" type="submit">
          <Plus size={16} aria-hidden />
        </button>
      </form>
      <div className="panel">
        {projects.map((project) => (
          <div className="row item-row" key={project.id}>
            <div>
              <strong>{project.title}</strong>
              <div className="muted">{project.desired_outcome ?? "No outcome set"}</div>
              <div className="badge-row">
                <span className="badge">{project.status}</span>
                <span className="badge">{domainName(domains, project.domain_id)}</span>
              </div>
            </div>
            <button onClick={() => archive(project.id)} title="Archive" type="button">
              <Archive size={16} aria-hidden />
            </button>
          </div>
        ))}
        {!projects.length ? <div className="row muted">No projects yet.</div> : null}
      </div>
    </AppShell>
  );
}

function domainName(domains: Domain[], domainId: string | null) {
  return domains.find((domain) => domain.id === domainId)?.name ?? "No domain";
}
