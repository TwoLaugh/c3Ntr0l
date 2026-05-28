"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  Activity,
  CalendarDays,
  ClipboardCheck,
  ClipboardList,
  FolderKanban,
  Inbox,
  ListChecks,
  Repeat,
  Settings,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/components/auth-provider";

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

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !token) router.replace("/");
  }, [mounted, router, token]);

  if (!mounted || !token) return null;

  return (
    <div className="app-frame">
      <aside className="sidebar">
        <div className="brand">
          <Sparkles size={18} aria-hidden />
          <span>c3Ntr0l</span>
        </div>
        <nav className="nav-list">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            return (
              <Link className={active ? "nav-item active" : "nav-item"} href={item.href} key={item.href}>
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
    </div>
  );
}
