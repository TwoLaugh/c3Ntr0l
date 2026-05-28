"use client";

import { FormEvent, useEffect, useState } from "react";
import { Archive, Plus } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";
import { apiRequest, Domain, Project, Task } from "@/lib/api";

export default function TasksPage() {
  const { token } = useAuth();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [domains, setDomains] = useState<Domain[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [title, setTitle] = useState("");
  const [domainId, setDomainId] = useState("");
  const [projectId, setProjectId] = useState("");
  const [priority, setPriority] = useState("normal");

  async function load() {
    if (!token) return;
    const [nextTasks, nextDomains, nextProjects] = await Promise.all([
      apiRequest<Task[]>("/api/v1/tasks", { token }),
      apiRequest<Domain[]>("/api/v1/domains", { token }),
      apiRequest<Project[]>("/api/v1/projects", { token }),
    ]);
    setTasks(nextTasks);
    setDomains(nextDomains);
    setProjects(nextProjects);
  }

  async function create(event: FormEvent) {
    event.preventDefault();
    if (!token || !title.trim()) return;
    await apiRequest<Task>("/api/v1/tasks", {
      method: "POST",
      token,
      body: JSON.stringify({ title, domain_id: domainId || null, project_id: projectId || null, priority }),
    });
    setTitle("");
    await load();
  }

  async function archive(taskId: string) {
    if (!token) return;
    await apiRequest<Task>(`/api/v1/tasks/${taskId}/archive`, { method: "POST", token });
    await load();
  }

  useEffect(() => {
    void load();
  }, [token]);

  return (
    <AppShell>
      <h1 className="page-title">Tasks</h1>
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
        <select className="field" onChange={(event) => setProjectId(event.target.value)} value={projectId}>
          <option value="">No project</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.title}
            </option>
          ))}
        </select>
        <select className="field" onChange={(event) => setPriority(event.target.value)} value={priority}>
          <option value="low">Low</option>
          <option value="normal">Normal</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </select>
        <button className="primary-button" title="Add task" type="submit">
          <Plus size={16} aria-hidden />
        </button>
      </form>
      <div className="panel">
        {tasks.map((task) => (
          <div className="row item-row" key={task.id}>
            <div>
              <strong>{task.title}</strong>
              <div className="muted">{task.notes ?? "No notes"}</div>
              <div className="badge-row">
                <span className="badge">{task.status}</span>
                <span className="badge">{task.priority}</span>
                <span className="badge">{nameFor(domains, task.domain_id, "No domain")}</span>
                <span className="badge">{nameFor(projects, task.project_id, "No project")}</span>
              </div>
            </div>
            <button onClick={() => archive(task.id)} title="Archive" type="button">
              <Archive size={16} aria-hidden />
            </button>
          </div>
        ))}
        {!tasks.length ? <div className="row muted">No tasks yet.</div> : null}
      </div>
    </AppShell>
  );
}

function nameFor(items: Array<{ id: string; name?: string; title?: string }>, id: string | null, fallback: string) {
  const item = items.find((candidate) => candidate.id === id);
  return item?.name ?? item?.title ?? fallback;
}
