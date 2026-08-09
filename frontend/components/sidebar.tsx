"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import clsx from "clsx";
import {
  Inbox,
  AlertCircle,
  Flame,
  ListChecks,
  Star,
  FileWarning,
  Megaphone,
  Info,
  Edit,
} from "lucide-react";

const NAV_ITEMS = [
  { href: "/inbox", label: "Inbox", icon: Inbox },
  { href: "/inbox?priority=critical", label: "Critical", icon: AlertCircle },
  { href: "/inbox?priority=high", label: "High priority", icon: Flame },
  { href: "/action-items", label: "Action items", icon: ListChecks },
];

const CATEGORY_ITEMS = [
  { href: "/inbox?category=requires_action", label: "Requires action", icon: ListChecks },
  { href: "/inbox?category=important", label: "Important", icon: Star },
  { href: "/inbox?category=informational", label: "Informational", icon: Info },
  { href: "/inbox?category=newsletter_marketing", label: "Newsletters", icon: Megaphone },
  { href: "/inbox?category=low_value", label: "Low value", icon: FileWarning },
];

function useIsActive() {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  return (href: string) => {
    const [path, query] = href.split("?");
    if (pathname !== path) return false;
    if (!query) return searchParams.toString() === "";
    const target = new URLSearchParams(query);
    for (const [key, value] of target.entries()) {
      if (searchParams.get(key) !== value) return false;
    }
    return true;
  };
}

function NavLink({
  href,
  label,
  icon: Icon,
  isActive,
}: {
  href: string;
  label: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  isActive: boolean;
}) {
  return (
    <Link
      href={href}
      className={clsx(
        "flex items-center gap-4 rounded-full pl-4 pr-5 py-2 text-sm transition-colors",
        isActive ? "bg-selected text-ink font-medium" : "text-ink/80 hover:bg-hover"
      )}
    >
      <Icon size={18} className={isActive ? "text-accent" : "text-muted"} />
      {label}
    </Link>
  );
}

export function Sidebar() {
  const isActive = useIsActive();

  return (
    <aside className="w-64 shrink-0 bg-bg h-full flex flex-col overflow-y-auto">
      <div className="flex items-center gap-2 px-6 py-5">
        <div className="h-8 w-8 rounded-full bg-accent flex items-center justify-center text-white font-medium text-sm">
          IQ
        </div>
        <span className="font-medium text-xl tracking-tight text-ink">InboxIQ</span>
      </div>

      <div className="px-3 pb-3">
        <button
          title="Compose (coming soon)"
          className="flex items-center gap-3 rounded-2xl bg-compose text-compose-text pl-4 pr-6 py-3.5 shadow-[0_1px_2px_0_rgba(60,64,67,0.3),0_1px_3px_1px_rgba(60,64,67,0.15)] hover:shadow-[0_1px_3px_0_rgba(60,64,67,0.3),0_4px_8px_3px_rgba(60,64,67,0.15)] transition-shadow font-medium text-sm"
        >
          <Edit size={20} />
          Compose
        </button>
      </div>

      <nav className="flex flex-col gap-0.5 px-3">
        {NAV_ITEMS.map((item) => (
          <NavLink key={item.href} {...item} isActive={isActive(item.href)} />
        ))}
      </nav>

      <div className="px-6 pt-6 pb-1 text-xs font-medium text-muted uppercase tracking-wide">Categories</div>
      <nav className="flex flex-col gap-0.5 px-3">
        {CATEGORY_ITEMS.map((item) => (
          <NavLink key={item.href} {...item} isActive={isActive(item.href)} />
        ))}
      </nav>

      <div className="mt-auto px-6 py-4 text-xs text-muted">
        Every reply needs your approval before it sends.
      </div>
    </aside>
  );
}
