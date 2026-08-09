"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function AuthCompletePage() {
  const router = useRouter();
  const params = useSearchParams();

  useEffect(() => {
    const token = params.get("token");
    if (token) {
      localStorage.setItem("inboxiq_token", token);
      router.replace("/inbox");
    } else {
      router.replace("/?error=auth_failed");
    }
  }, [params, router]);

  return (
    <main className="min-h-screen flex items-center justify-center bg-bg">
      <p className="text-muted font-mono text-sm">Connecting your inbox…</p>
    </main>
  );
}
