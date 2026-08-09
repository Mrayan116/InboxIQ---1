"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/sidebar";
import { TopBar } from "@/components/top-bar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [checked, setChecked] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("inboxiq_token");
    if (!token) {
      router.replace("/");
      return;
    }
    setChecked(true);
  }, [router]);

  if (!checked) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-bg">
        <p className="text-muted text-sm">Loading…</p>
      </main>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-bg">
      <TopBar />
      <div className="flex flex-1 min-h-0">
        <Sidebar />
        <div className="flex-1 min-w-0 bg-surface rounded-tl-2xl overflow-hidden border-l border-t border-border">
          {children}
        </div>
      </div>
    </div>
  );
}
