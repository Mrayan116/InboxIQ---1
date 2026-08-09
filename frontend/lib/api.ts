/**
 * Thin API client. Every backend call goes through `apiFetch` so auth
 * header injection and error handling live in one place instead of being
 * copy-pasted into every component that needs data.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("inboxiq_token");
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new ApiError(res.status, body || res.statusText);
  }

  return res.json() as Promise<T>;
}

// --- Types matching backend/app/schemas/api.py ---

export type Priority = "critical" | "high" | "medium" | "low";
export type Category = "important" | "requires_action" | "informational" | "newsletter_marketing" | "low_value";

export interface EmailListItem {
  id: string;
  sender: string;
  subject: string;
  snippet: string;
  received_at: string;
  priority: Priority | null;
  category: Category | null;
  importance_score: number | null;
  ai_summary_short: string | null;
  is_phishing_suspected: boolean;
}

export interface EmailDetail extends EmailListItem {
  body_text: string;
  ai_summary_detailed: string | null;
  ai_summary_bullets: string[] | null;
  priority_reason: string | null;
  phishing_reason: string | null;
  importance_positive_signals: string[] | null;
  importance_negative_signals: string[] | null;
}

export interface ActionItem {
  id: string;
  description: string;
  due_date: string | null;
  is_completed: boolean;
  email_message_id: string;
}

export interface SmartReplyOption {
  style: string;
  body: string;
}

export interface ToneAnalysisResult {
  detected_tone: string;
  concerns: string[];
  suggestions: string[];
  overall_assessment: string;
}

// --- Endpoints ---

export const api = {
  listEmails: (priority?: Priority, category?: Category) => {
    const qs = new URLSearchParams();
    if (priority) qs.set("priority", priority);
    if (category) qs.set("category", category);
    const query = qs.toString();
    return apiFetch<EmailListItem[]>(`/emails${query ? `?${query}` : ""}`);
  },

  getEmail: (id: string) => apiFetch<EmailDetail>(`/emails/${id}`),

  triggerSync: () => apiFetch<{ task_id: string; status: string }>("/emails/sync", { method: "POST" }),

  getSyncStatus: (taskId: string) =>
    apiFetch<{ task_id: string; state: string; meta?: { phase: string; total?: number }; result?: { new_messages: number } }>(
      `/emails/sync/status/${taskId}`
    ),

  getSmartReplies: (id: string) =>
    apiFetch<{ options: SmartReplyOption[] }>(`/emails/${id}/smart-replies`, { method: "POST" }),

  checkTone: (draft_body: string) =>
    apiFetch<ToneAnalysisResult>("/emails/tone-check", {
      method: "POST",
      body: JSON.stringify({ draft_body }),
    }),

  simplify: (body: string) =>
    apiFetch<{ simplified: string }>("/emails/simplify", {
      method: "POST",
      body: JSON.stringify({ body }),
    }),

  listActionItems: () => apiFetch<ActionItem[]>("/action-items"),

  completeActionItem: (id: string) =>
    apiFetch<ActionItem>(`/action-items/${id}/complete`, { method: "POST" }),
};
