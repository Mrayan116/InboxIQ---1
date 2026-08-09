"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Archive, Trash2, MailOpen, Sparkles, Wand2 } from "lucide-react";
import { api, type EmailDetail, type SmartReplyOption } from "@/lib/api";
import { PriorityBadge, CategoryBadge, ImportanceScore, prioritySpineClass } from "@/components/priority-badge";

type SummaryTab = "short" | "detailed" | "bullets";

export default function EmailDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [email, setEmail] = useState<EmailDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [summaryTab, setSummaryTab] = useState<SummaryTab>("short");

  const [replies, setReplies] = useState<SmartReplyOption[] | null>(null);
  const [loadingReplies, setLoadingReplies] = useState(false);
  const [replyError, setReplyError] = useState<string | null>(null);
  const [selectedDraft, setSelectedDraft] = useState<string | null>(null);

  const [simplified, setSimplified] = useState<string | null>(null);
  const [loadingSimplify, setLoadingSimplify] = useState(false);

  useEffect(() => {
    api
      .getEmail(id)
      .then(setEmail)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load email"));
  }, [id]);

  async function handleGenerateReplies() {
    setLoadingReplies(true);
    setReplyError(null);
    try {
      const result = await api.getSmartReplies(id);
      setReplies(result.options);
    } catch (e) {
      setReplyError(e instanceof Error ? e.message : "Failed to generate replies. Try again.");
    } finally {
      setLoadingReplies(false);
    }
  }

  async function handleSimplify() {
    if (!email) return;
    setLoadingSimplify(true);
    try {
      const result = await api.simplify(email.body_text);
      setSimplified(result.simplified);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to simplify email");
    } finally {
      setLoadingSimplify(false);
    }
  }

  if (error) {
    return <div className="p-6 text-sm text-danger">{error}</div>;
  }
  if (!email) {
    return <p className="p-6 text-sm text-muted">Loading…</p>;
  }

  return (
    <div className="flex h-full">
      <div className="flex-1 min-w-0 flex flex-col">
        {/* Gmail-style icon toolbar */}
        <div className="flex items-center gap-1 border-b border-border px-3 py-2">
          <button onClick={() => router.back()} className="p-2 rounded-full hover:bg-hover transition-colors" aria-label="Back">
            <ArrowLeft size={18} className="text-ink/70" />
          </button>
          <div className="w-px h-6 bg-border mx-1" />
          <button className="p-2 rounded-full hover:bg-hover transition-colors" aria-label="Archive">
            <Archive size={18} className="text-ink/70" />
          </button>
          <button className="p-2 rounded-full hover:bg-hover transition-colors" aria-label="Delete">
            <Trash2 size={18} className="text-ink/70" />
          </button>
          <button className="p-2 rounded-full hover:bg-hover transition-colors" aria-label="Mark as unread">
            <MailOpen size={18} className="text-ink/70" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto">
          <header className={`${prioritySpineClass(email.priority)} px-8 py-6`}>
            <h1 className="text-xl text-ink mb-3">{email.subject || "(no subject)"}</h1>
            <div className="flex items-center gap-3 text-sm text-muted flex-wrap">
              <div className="h-8 w-8 rounded-full bg-accent-soft text-accent flex items-center justify-center text-xs font-medium">
                {email.sender[0]?.toUpperCase() ?? "?"}
              </div>
              <span className="text-ink">{email.sender}</span>
              <span>·</span>
              <span className="text-xs">{new Date(email.received_at).toLocaleString()}</span>
              <PriorityBadge priority={email.priority} />
              <CategoryBadge category={email.category} />
            </div>
            {email.importance_score !== null && (
              <div className="mt-3 max-w-xs">
                <ImportanceScore score={email.importance_score} />
              </div>
            )}

            {email.is_phishing_suspected && (
              <div className="mt-4 rounded-lg border border-danger/30 bg-danger-soft px-4 py-3">
                <p className="text-sm font-medium text-danger mb-1">⚠ This email looks suspicious</p>
                <p className="text-sm text-ink/80">{email.phishing_reason}</p>
              </div>
            )}
          </header>

          <div className="px-8 py-6">
            {simplified ? (
              <>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-muted uppercase tracking-wide font-medium">Simplified</span>
                  <button onClick={() => setSimplified(null)} className="text-xs text-accent hover:underline">
                    Show original
                  </button>
                </div>
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{simplified}</p>
              </>
            ) : (
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{email.body_text}</p>
            )}

            <button
              onClick={handleSimplify}
              disabled={loadingSimplify}
              className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-accent hover:underline disabled:opacity-50"
            >
              <Wand2 size={14} />
              {loadingSimplify ? "Simplifying…" : simplified ? "Re-simplify" : "Simplify this email"}
            </button>
          </div>
        </div>
      </div>

      {/* AI insight rail */}
      <aside className="w-96 shrink-0 border-l border-border overflow-y-auto">
        <section className="border-b border-border px-5 py-5">
          <h2 className="text-sm font-medium text-ink mb-3 flex items-center gap-1.5">
            <Sparkles size={15} className="text-accent" />
            Summary
          </h2>
          <div className="flex gap-1 mb-3">
            {(["short", "detailed", "bullets"] as SummaryTab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setSummaryTab(tab)}
                className={`text-xs font-medium px-3 py-1 rounded-full transition-colors ${
                  summaryTab === tab ? "bg-accent-soft text-accent" : "text-muted hover:bg-hover"
                }`}
              >
                {tab === "short" ? "15-sec" : tab === "detailed" ? "Detailed" : "Bullets"}
              </button>
            ))}
          </div>
          {summaryTab === "short" && <p className="text-sm leading-relaxed text-ink">{email.ai_summary_short}</p>}
          {summaryTab === "detailed" && <p className="text-sm leading-relaxed text-ink">{email.ai_summary_detailed}</p>}
          {summaryTab === "bullets" && (
            <ul className="text-sm space-y-1.5 list-disc list-inside text-ink">
              {email.ai_summary_bullets?.map((b, i) => <li key={i}>{b}</li>)}
            </ul>
          )}
          {email.priority_reason && (
            <p className="text-xs text-muted mt-3 pt-3 border-t border-border">
              <span className="font-medium">Why this priority: </span>
              {email.priority_reason}
            </p>
          )}
        </section>

        {(email.importance_positive_signals?.length || email.importance_negative_signals?.length) ? (
          <section className="border-b border-border px-5 py-5">
            <h2 className="text-sm font-medium text-ink mb-3">Why this score</h2>
            <ul className="text-sm space-y-1">
              {email.importance_positive_signals?.map((s, i) => (
                <li key={`pos-${i}`} className="flex gap-2">
                  <span className="text-priority-critical shrink-0">+</span>
                  <span className="text-ink/80">{s}</span>
                </li>
              ))}
              {email.importance_negative_signals?.map((s, i) => (
                <li key={`neg-${i}`} className="flex gap-2">
                  <span className="text-muted shrink-0">−</span>
                  <span className="text-muted">{s}</span>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        <section className="px-5 py-5">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-ink">Smart replies</h2>
            {!replies && (
              <button
                onClick={handleGenerateReplies}
                disabled={loadingReplies}
                className="text-xs font-medium text-accent hover:underline disabled:opacity-50"
              >
                {loadingReplies ? "Generating…" : "Generate"}
              </button>
            )}
          </div>

          {replyError && (
            <div className="mb-3 rounded-lg border border-danger/30 bg-danger-soft px-3 py-2 text-xs text-danger flex items-center justify-between gap-2">
              <span>{replyError}</span>
              <button onClick={handleGenerateReplies} className="font-medium hover:underline shrink-0">
                Retry
              </button>
            </div>
          )}

          {replies?.map((option) => (
            <div key={option.style} className="mb-3 rounded-lg border border-border p-3">
              <p className="text-xs uppercase tracking-wide text-muted mb-1.5 font-medium">{option.style}</p>
              <p className="text-sm leading-relaxed mb-2 whitespace-pre-wrap text-ink">{option.body}</p>
              <button
                onClick={() => setSelectedDraft(option.body)}
                className="text-xs font-medium text-accent hover:underline"
              >
                Use this draft
              </button>
            </div>
          ))}

          {selectedDraft && (
            <div className="mt-2 rounded-lg border border-accent/30 bg-accent-soft p-3">
              <p className="text-xs font-medium text-accent mb-1">Draft ready</p>
              <p className="text-xs text-ink/70">
                Edit and send from your compose window — InboxIQ never sends on its own.
              </p>
            </div>
          )}
        </section>
      </aside>
    </div>
  );
}
