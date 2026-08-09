import clsx from "clsx";
import type { Priority } from "@/lib/api";

const LABELS: Record<Priority, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

const DOT_COLOR: Record<Priority, string> = {
  critical: "bg-priority-critical",
  high: "bg-priority-high",
  medium: "bg-priority-medium",
  low: "bg-priority-low",
};

export function PriorityBadge({ priority }: { priority: Priority | null }) {
  if (!priority) return null;
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted">
      <span className={clsx("h-1.5 w-1.5 rounded-full", DOT_COLOR[priority])} />
      {LABELS[priority]}
    </span>
  );
}

export function prioritySpineClass(priority: Priority | null): string {
  return `priority-spine priority-spine--${priority ?? "none"}`;
}

export type Category = "important" | "requires_action" | "informational" | "newsletter_marketing" | "low_value";

const CATEGORY_LABELS: Record<Category, string> = {
  important: "Important",
  requires_action: "Requires action",
  informational: "Informational",
  newsletter_marketing: "Newsletter",
  low_value: "Low value",
};

const CATEGORY_STYLE: Record<Category, string> = {
  important: "bg-accent-soft text-accent",
  requires_action: "bg-[#FEF7E0] text-[#994F00]",
  informational: "bg-hover text-muted",
  newsletter_marketing: "bg-hover text-muted",
  low_value: "bg-hover text-muted/70",
};

export function CategoryBadge({ category }: { category: Category | null }) {
  if (!category) return null;
  return (
    <span className={clsx("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", CATEGORY_STYLE[category])}>
      {CATEGORY_LABELS[category]}
    </span>
  );
}

/** Small horizontal meter -- importance is a magnitude, so a bar reads faster than a bare number. */
export function ImportanceScore({ score }: { score: number | null }) {
  if (score === null) return null;
  const color = score >= 70 ? "bg-priority-critical" : score >= 40 ? "bg-priority-medium" : "bg-priority-low";
  return (
    <div className="flex items-center gap-2 w-full max-w-[120px]">
      <div className="flex-1 h-1.5 rounded-full bg-border overflow-hidden">
        <div className={clsx("h-full rounded-full", color)} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs text-muted shrink-0">{score}%</span>
    </div>
  );
}
