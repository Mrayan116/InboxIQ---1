const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function LandingPage() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-bg px-6">
      <div className="max-w-md w-full text-center">
        <div className="mb-8 flex items-center justify-center gap-2">
          <div className="h-10 w-10 rounded-full bg-accent flex items-center justify-center text-white font-medium">
            IQ
          </div>
          <span className="font-medium text-2xl tracking-tight text-ink">InboxIQ</span>
        </div>
        <h1 className="text-2xl font-medium leading-snug mb-3 text-ink">
          Understand your inbox in seconds, not hours.
        </h1>
        <p className="text-muted mb-8 leading-relaxed">
          Summaries, priority sorting, and draft replies for your Gmail —
          nothing sends without you clicking send.
        </p>
        <a
          href={`${API_BASE}/auth/google/login`}
          className="inline-flex items-center justify-center gap-2 rounded-full bg-accent hover:bg-accent-hover text-white font-medium px-5 py-3 transition-colors w-full shadow-[0_1px_2px_0_rgba(60,64,67,0.3)]"
        >
          Connect Gmail to get started
        </a>
        <p className="text-xs text-muted mt-4">Read-only by default. Sending always requires your click.</p>
      </div>
    </main>
  );
}
