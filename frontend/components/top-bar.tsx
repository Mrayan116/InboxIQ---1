"use client";

import { Search, Menu, HelpCircle, Settings } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

export function TopBar() {
  const router = useRouter();
  const [query, setQuery] = useState("");

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (query.trim()) {
      // Natural-language inbox search is on the roadmap (RAG over email
      // embeddings) -- for now this routes into the inbox list, which is
      // enough to keep the search bar functional rather than decorative.
      router.push(`/inbox?q=${encodeURIComponent(query.trim())}`);
    }
  }

  return (
    <header className="flex items-center gap-4 h-16 px-4 bg-bg">
      <button className="p-2.5 rounded-full hover:bg-hover transition-colors shrink-0" aria-label="Menu">
        <Menu size={20} className="text-ink/70" />
      </button>

      <form onSubmit={handleSearch} className="flex-1 max-w-2xl">
        <div className="flex items-center gap-3 bg-hover rounded-full px-4 h-12 focus-within:bg-surface focus-within:shadow-[0_1px_3px_0_rgba(60,64,67,0.3)] transition-all">
          <Search size={20} className="text-muted shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search mail"
            className="flex-1 bg-transparent outline-none text-sm text-ink placeholder:text-muted"
          />
        </div>
      </form>

      <div className="flex items-center gap-1 ml-auto shrink-0">
        <button className="p-2.5 rounded-full hover:bg-hover transition-colors" aria-label="Help">
          <HelpCircle size={20} className="text-ink/70" />
        </button>
        <button className="p-2.5 rounded-full hover:bg-hover transition-colors" aria-label="Settings">
          <Settings size={20} className="text-ink/70" />
        </button>
        <div className="h-8 w-8 rounded-full bg-accent-soft text-accent flex items-center justify-center text-sm font-medium ml-1">
          U
        </div>
      </div>
    </header>
  );
}
