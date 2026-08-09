"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import clsx from "clsx";
import { Star, Archive, Trash2, RefreshCw } from "lucide-react";
import { api, type EmailListItem, type Priority, type Category } from "@/lib/api";
import { PriorityBadge, CategoryBadge, ImportanceScore, prioritySpineClass } from "@/components/priority-badge";

function formatTime(iso: string): string {
  const date = new Date(iso);
  const now = new Date();
  const sameDay = date.toDateString() === now.toDateString();
  return sameDay
    ? date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
    : date.toLocaleDateString([], { month: "short", day: "numeric" });
}

export default function InboxPage() {
  const params = useSearchParams();
  const router = useRouter();
  const priority = (params.get("priority") as Priority | null) ?? undefined;
  const category = (params.get("category") as Category | null) ?? undefined;
  const searchQuery = params.get("q");

  const [emails, setEmails] = useState<EmailListItem[] | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [syncStatus, setSyncStatus] = useState<string | null>(null); // null = not syncing
  const [error, setError] = useState<string | null>(null);
  const [starred, setStarred] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    try {
      setError(null);
      const data = await api.listEmails(priority, category);
      setEmails(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load inbox");
    }
  }, [priority, category]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleRefresh() {
    setRefreshing(true);
    try {
      await load();
    } finally {
      setRefreshing(false);
    }
  }

  async function handleSync() {
    setSyncStatus("queued");
    try {
      const { task_id } = await api.triggerSync();

      const poll = async () => {
        const status = await api.getSyncStatus(task_id);

        if (status.state === "PROGRESS" && status.meta) {
          setSyncStatus(
            status.meta.phase === "analyzing"
              ? `Analyzing ${status.meta.total ?? ""} email${status.meta.total === 1 ? "" : "s"}…`
              : "Fetching new mail…"
          );
          setTimeout(poll, 1200);
        } else if (status.state === "SUCCESS") {
          setSyncStatus(null);
          await load();
        } else if (status.state === "FAILURE") {
          setSyncStatus(null);
          setError(status.error || "Sync failed");
        } else {
          setTimeout(poll, 1000);
        }
      };

      poll();
    } catch (e) {
      setSyncStatus(null);
      setError(e instanceof Error ? e.message : "Failed to start sync");
    }
  }

  function toggleStar(e: React.MouseEvent, id: string) {
    e.stopPropagation();
    setStarred((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  const filtered = searchQuery
    ? emails?.filter(
        (e) =>
          e.subject.toLowerCase().includes(searchQuery.toLowerCase()) ||
          e.sender.toLowerCase().includes(searchQuery.toLowerCase()) ||
          e.snippet.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : emails;

  return (
    <div className="flex flex-col h-full">
      <header className="flex items-center justify-between border-b border-border px-5 py-3">
        <div className="flex items-center gap-3">
          <h1 className="font-medium text-lg text-ink">
            {searchQuery
              ? `Search: "${searchQuery}"`
              : priority
                ? `${priority[0].toUpperCase()}${priority.slice(1)} priority`
                : category
                  ? category.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())
                  : "Inbox"}
          </h1>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            title="Refresh"
            className="p-2 rounded-full hover:bg-hover transition-colors disabled:opacity-50"
          >
            <RefreshCw size={16} className={clsx("text-muted", refreshing && "animate-spin")} />
          </button>
        </div>
        <button
          onClick={handleSync}
          disabled={syncStatus !== null}
          className="text-sm font-medium rounded-full bg-accent hover:bg-accent-hover text-white px-4 py-2 transition-colors disabled:opacity-50"
        >
          {syncStatus ?? "Sync inbox"}
        </button>
      </header>

      <div className="flex-1 overflow-y-auto">
        {error && (
          <div className="m-5 rounded-lg border border-danger/30 bg-danger-soft px-4 py-3 text-sm text-danger">
            {error}
          </div>
        )}

        {emails === null && !error && <p className="p-5 text-sm text-muted">Loading…</p>}

        {filtered?.length === 0 && (
          <div className="p-16 text-center">
            <p className="font-medium text-lg text-ink mb-1">
              {searchQuery ? "No matching emails" : "Nothing here yet"}
            </p>
            <p className="text-muted text-sm">
              {searchQuery
                ? "Try a different search term."
                : 'Click "Sync inbox" above to pull in recent email and run AI analysis.'}
            </p>
          </div>
        )}

        {filtered?.map((email) => (
          <div
            key={email.id}
            onClick={() => router.push(`/inbox/${email.id}`)}
            className={clsx(
              prioritySpineClass(email.priority),
              "group flex items-center gap-3 border-b border-border px-4 py-2.5 hover:shadow-[0_1px_2px_0_rgba(60,64,67,0.3),0_1px_3px_1px_rgba(60,64,67,0.15)] hover:bg-surface hover:z-10 relative cursor-pointer transition-shadow"
            )}
          >
            <input
              type="checkbox"
              onClick={(e) => e.stopPropagation()}
              className="h-4 w-4 rounded border-border shrink-0 accent-accent"
            />
            <button onClick={(e) => toggleStar(e, email.id)} className="shrink-0" aria-label="Star">
              <Star
                size={18}
                className={starred.has(email.id) ? "fill-star text-star" : "text-muted/50 hover:text-muted"}
              />
            </button>

            <div className="w-44 shrink-0 flex items-center gap-2">
              <span className="text-sm truncate font-medium text-ink">{email.sender}</span>
              {email.is_phishing_suspected && (
                <span title="Suspicious email" className="text-xs text-danger shrink-0">⚠</span>
              )}
            </div>

            <div className="flex-1 min-w-0 flex items-center gap-2">
              <span className="text-sm text-ink truncate shrink-0 max-w-[40%]">
                {email.subject || "(no subject)"}
              </span>
              <span className="text-sm text-muted truncate">
                — {email.ai_summary_short || email.snippet}
              </span>
            </div>

            <div className="shrink-0 flex items-center gap-2">
              <CategoryBadge category={email.category} />
              <PriorityBadge priority={email.priority} />
            </div>

            <div className="w-24 shrink-0">
              <ImportanceScore score={email.importance_score} />
            </div>

            {/* Gmail reveals archive/delete icons on hover, replacing the date */}
            <div className="w-16 shrink-0 text-right relative h-5">
              <span className="text-xs text-muted absolute right-0 top-0 group-hover:opacity-0 transition-opacity">
                {formatTime(email.received_at)}
              </span>
              <div className="absolute right-0 top-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button onClick={(e) => e.stopPropagation()} className="p-1 rounded-full hover:bg-hover" aria-label="Archive">
                  <Archive size={15} className="text-muted" />
                </button>
                <button onClick={(e) => e.stopPropagation()} className="p-1 rounded-full hover:bg-hover" aria-label="Delete">
                  <Trash2 size={15} className="text-muted" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
