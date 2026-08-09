"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Check } from "lucide-react";
import { api, type ActionItem } from "@/lib/api";

function formatDue(iso: string | null): string {
  if (!iso) return "No deadline";
  const date = new Date(iso);
  const overdue = date < new Date();
  const label = date.toLocaleDateString([], { month: "short", day: "numeric" });
  return overdue ? `Overdue · ${label}` : label;
}

export default function ActionItemsPage() {
  const router = useRouter();
  const [items, setItems] = useState<ActionItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listActionItems()
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load action items"));
  }, []);

  async function handleComplete(itemId: string) {
    setItems((prev) => prev?.filter((i) => i.id !== itemId) ?? null);
    try {
      await api.completeActionItem(itemId);
    } catch {
      api.listActionItems().then(setItems);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <header className="border-b border-border px-5 py-4">
        <h1 className="font-medium text-lg text-ink">Action items</h1>
        <p className="text-sm text-muted mt-0.5">Tasks InboxIQ found across your inbox</p>
      </header>

      <div className="flex-1 overflow-y-auto p-5">
        {error && <p className="text-sm text-danger mb-4">{error}</p>}
        {items === null && !error && <p className="text-sm text-muted">Loading…</p>}

        {items?.length === 0 && (
          <div className="text-center py-16">
            <p className="font-medium text-lg text-ink mb-1">All caught up</p>
            <p className="text-muted text-sm">No open action items right now.</p>
          </div>
        )}

        <div className="max-w-2xl space-y-2">
          {items?.map((item) => (
            <div
              key={item.id}
              className="flex items-start gap-3 rounded-lg border border-border px-4 py-3 hover:shadow-[0_1px_2px_0_rgba(60,64,67,0.3)] transition-shadow"
            >
              <button
                onClick={() => handleComplete(item.id)}
                aria-label="Mark complete"
                className="mt-0.5 h-5 w-5 shrink-0 rounded-full border-2 border-border hover:border-accent hover:bg-accent-soft transition-colors flex items-center justify-center group"
              >
                <Check size={12} className="text-accent opacity-0 group-hover:opacity-100" />
              </button>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-ink">{item.description}</p>
                <button
                  onClick={() => router.push(`/inbox/${item.email_message_id}`)}
                  className="text-xs text-muted hover:text-accent mt-1"
                >
                  {formatDue(item.due_date)} · View email →
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
