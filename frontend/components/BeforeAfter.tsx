"use client";

import { useState } from "react";

export default function BeforeAfter({ beforeUrl, afterUrl }: { beforeUrl: string | null; afterUrl: string | null }) {
  const [showAfter, setShowAfter] = useState(true);

  if (!beforeUrl && !afterUrl) {
    return <div className="flex h-64 items-center justify-center text-sm text-slate-400">No preview available yet.</div>;
  }

  const src = showAfter ? afterUrl || beforeUrl : beforeUrl || afterUrl;

  return (
    <div>
      <div className="flex items-center justify-center rounded-md border border-slate-200 bg-[conic-gradient(#f1f5f9_90deg,#fff_90deg,#fff_180deg,#f1f5f9_180deg,#f1f5f9_270deg,#fff_270deg)] bg-[length:20px_20px] p-4">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={src ?? undefined} alt="Product preview" className="max-h-96 max-w-full object-contain" />
      </div>
      <div className="mt-3 flex justify-center gap-2">
        <button
          onClick={() => setShowAfter(false)}
          disabled={!beforeUrl}
          className={`btn-secondary py-1 text-xs ${!showAfter ? "ring-1 ring-brand-500" : ""}`}
        >
          Before
        </button>
        <button
          onClick={() => setShowAfter(true)}
          disabled={!afterUrl}
          className={`btn-secondary py-1 text-xs ${showAfter ? "ring-1 ring-brand-500" : ""}`}
        >
          After
        </button>
      </div>
    </div>
  );
}
