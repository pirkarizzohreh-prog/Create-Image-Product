"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { ReviewItem } from "@/lib/types";
import BeforeAfter from "@/components/BeforeAfter";

export default function ReviewQueuePage() {
  const [items, setItems] = useState<ReviewItem[] | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState<Record<string, string>>({});

  async function load() {
    const data = await api.get<{ results: ReviewItem[] } | ReviewItem[]>("/api/review/?decision=pending");
    setItems(Array.isArray(data) ? data : data.results);
  }

  useEffect(() => {
    load();
  }, []);

  async function approve(item: ReviewItem) {
    setBusyId(item.id);
    try {
      await api.post(`/api/review/${item.id}/approve/`);
      await load();
    } finally {
      setBusyId(null);
    }
  }

  async function reject(item: ReviewItem) {
    const reason = rejectReason[item.id];
    if (!reason) {
      alert("Please enter a rejection reason.");
      return;
    }
    setBusyId(item.id);
    try {
      await api.post(`/api/review/${item.id}/reject/`, { reason });
      await load();
    } finally {
      setBusyId(null);
    }
  }

  async function rerun(item: ReviewItem) {
    setBusyId(item.id);
    try {
      await api.post(`/api/review/${item.id}/rerun/`, {});
      await load();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Review Queue</h1>
      <p className="mt-1 text-sm text-slate-500">
        Images flagged by automated quality control, or that failed a pipeline stage.
      </p>

      <div className="mt-6 space-y-6">
        {items === null && <p className="text-slate-400">Loading&hellip;</p>}
        {items?.length === 0 && <p className="text-slate-400">Nothing waiting for review. 🎉</p>}
        {items?.map((item) => (
          <div key={item.id} className="card grid gap-6 p-6 lg:grid-cols-3">
            <div className="lg:col-span-1">
              <BeforeAfter beforeUrl={item.job_detail.source_url} afterUrl={item.job_detail.output_url} />
            </div>

            <div className="lg:col-span-2 space-y-4">
              <div>
                <p className="text-sm font-medium text-slate-900">{item.job_detail.image_original_filename}</p>
                <p className="text-xs text-slate-500">
                  Mode: {item.job_detail.mode} &middot; Attempt #{item.job_detail.attempt}
                </p>
              </div>

              {item.reasons.length > 0 && (
                <div className="rounded-md bg-amber-50 p-3">
                  <p className="text-xs font-semibold text-amber-800">Flagged for:</p>
                  <ul className="mt-1 list-disc pl-5 text-xs text-amber-800">
                    {item.reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="flex flex-wrap items-center gap-2">
                <button onClick={() => approve(item)} disabled={busyId === item.id} className="btn-primary">
                  Approve as-is
                </button>
                <button onClick={() => rerun(item)} disabled={busyId === item.id} className="btn-secondary">
                  Re-run pipeline
                </button>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <input
                  type="text"
                  placeholder="Rejection reason"
                  className="input max-w-xs"
                  value={rejectReason[item.id] ?? ""}
                  onChange={(e) => setRejectReason((prev) => ({ ...prev, [item.id]: e.target.value }))}
                />
                <button onClick={() => reject(item)} disabled={busyId === item.id} className="btn-danger">
                  Reject
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
