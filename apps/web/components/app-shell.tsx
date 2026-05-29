"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import {
  Activity,
  CalendarDays,
  Check,
  ClipboardCheck,
  ClipboardList,
  FolderKanban,
  Inbox,
  ListChecks,
  Menu,
  MessageCircle,
  Repeat,
  Send,
  Settings,
  Sparkles,
  X,
} from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { apiRequest, ProposedChange, ProposedChangeDecision } from "@/lib/api";

const navItems = [
  { href: "/today", label: "Today", icon: CalendarDays },
  { href: "/inbox", label: "Inbox", icon: Inbox },
  { href: "/weekly-review", label: "Week", icon: ClipboardList },
  { href: "/daily-review", label: "Review", icon: ClipboardCheck },
  { href: "/tasks", label: "Tasks", icon: ListChecks },
  { href: "/domains", label: "Domains", icon: ListChecks },
  { href: "/projects", label: "Projects", icon: FolderKanban },
  { href: "/routines", label: "Routines", icon: Repeat },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/ai-activity", label: "AI", icon: Activity },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { token, clearAuth } = useAuth();
  const [mounted, setMounted] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [inboxOpen, setInboxOpen] = useState(false);
  const [rawText, setRawText] = useState("");
  const [assistantMessage, setAssistantMessage] = useState<string | null>(null);
  const [assistantError, setAssistantError] = useState<string | null>(null);
  const [pendingProposal, setPendingProposal] = useState<ProposedChange | null>(null);
  const [sending, setSending] = useState(false);
  const [deciding, setDeciding] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !token) router.replace("/");
  }, [mounted, router, token]);

  if (!mounted || !token) return null;

  async function submitInbox(event: FormEvent) {
    event.preventDefault();
    if (!token || !rawText.trim()) return;
    setSending(true);
    setAssistantError(null);
    setAssistantMessage(null);
    setPendingProposal(null);
    try {
      const response = await apiRequest<{
        confirmation: string | null;
        processing_status: string;
        actions: Array<{ message?: string | null; action_type: string; target_type?: string | null; target_id?: string | null }>;
      }>("/api/v1/inbox/messages", {
        method: "POST",
        token,
        body: JSON.stringify({ raw_text: rawText }),
      });
      setAssistantMessage(response.confirmation ?? response.actions[0]?.message ?? response.processing_status);
      const proposalAction = response.actions.find((action) => action.target_type === "proposed_change" && action.target_id);
      if (proposalAction?.target_id) {
        const proposal = await apiRequest<ProposedChange>(`/api/v1/proposed-changes/${proposalAction.target_id}`, { token });
        setPendingProposal(proposal);
      }
      setRawText("");
      if (pathname === "/today") router.refresh();
    } catch {
      setAssistantError("Inbox request failed.");
    } finally {
      setSending(false);
    }
  }

  async function decideProposal(decision: "accept" | "reject") {
    if (!token || !pendingProposal) return;
    setDeciding(true);
    setAssistantError(null);
    try {
      const response = await apiRequest<ProposedChangeDecision>(`/api/v1/proposed-changes/${pendingProposal.id}/${decision}`, {
        method: "POST",
        token,
      });
      setPendingProposal(response.proposed_change);
      setAssistantMessage(response.message);
      if (pathname === "/today") router.refresh();
    } catch {
      setAssistantError("Could not update the proposed change.");
    } finally {
      setDeciding(false);
    }
  }

  return (
    <div className="app-frame">
      {menuOpen ? <button aria-label="Close menu backdrop" className="menu-backdrop" onClick={() => setMenuOpen(false)} type="button" /> : null}
      <header className="topbar">
        <div className="brand">
          <Sparkles size={18} aria-hidden />
          <span>c3Ntr0l</span>
        </div>
        <button className="topbar-button" onClick={() => setMenuOpen(true)} type="button" aria-label="Open menu">
          <Menu size={20} aria-hidden />
        </button>
      </header>
      <aside className={menuOpen ? "sidebar open" : "sidebar"}>
        <div className="drawer-head">
          <div className="brand">
            <Sparkles size={18} aria-hidden />
            <span>c3Ntr0l</span>
          </div>
          <button className="topbar-button" onClick={() => setMenuOpen(false)} type="button" aria-label="Close menu">
            <X size={18} aria-hidden />
          </button>
        </div>
        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link className={active ? "nav-item active" : "nav-item"} href={item.href} key={item.href} onClick={() => setMenuOpen(false)}>
                <Icon size={18} aria-hidden />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <button className="ghost-button" onClick={clearAuth} type="button">
          Sign out
        </button>
      </aside>
      <main className="workspace">{children}</main>
      <button className="assistant-fab" onClick={() => setInboxOpen(true)} type="button" aria-label="Open inbox">
        <MessageCircle size={22} aria-hidden />
      </button>
      {inboxOpen ? (
        <div className="assistant-overlay" role="dialog" aria-modal="true" aria-label="Inbox">
          <div className="assistant-sheet">
            <div className="assistant-head">
              <strong>Inbox</strong>
              <button onClick={() => setInboxOpen(false)} type="button" aria-label="Close inbox">
                <X size={18} aria-hidden />
              </button>
            </div>
            <form className="assistant-form" onSubmit={submitInbox}>
              <textarea
                className="textarea assistant-textarea"
                disabled={sending}
                onChange={(event) => setRawText(event.target.value)}
                value={rawText}
              />
              <button className="primary-button icon-button-text" disabled={sending || !rawText.trim()} type="submit">
                <Send size={16} aria-hidden />
                {sending ? "Sending" : "Send"}
              </button>
            </form>
            {assistantMessage ? <div className="notice">{assistantMessage}</div> : null}
            {pendingProposal ? (
              <div className="proposal-card">
                <div>
                  <strong>{pendingProposal.title}</strong>
                  {pendingProposal.rationale ? <p>{pendingProposal.rationale}</p> : null}
                  <span className={`badge ${pendingProposal.status}`}>{pendingProposal.status}</span>
                </div>
                {pendingProposal.status === "pending" ? (
                  <div className="button-row">
                    <button className="primary-button icon-button-text" disabled={deciding} onClick={() => decideProposal("accept")} type="button">
                      <Check size={16} aria-hidden />
                      Accept
                    </button>
                    <button className="secondary-button" disabled={deciding} onClick={() => decideProposal("reject")} type="button">
                      Reject
                    </button>
                  </div>
                ) : null}
              </div>
            ) : null}
            {assistantError ? <div className="notice">{assistantError}</div> : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}
