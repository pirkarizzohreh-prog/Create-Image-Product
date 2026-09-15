"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { JobStatus, JobSummary } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";

const STATUS_FILTERS: { value: JobStatus | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "queued", label: "Queued" },
  { value: "processing", label: "Processing" },
  { value: "needs_review", label: "Needs Review" },
  { value: "completed", label: "Completed" },
  { value: "failed", label: "Failed" },
  { value: "rejected", label: "Rejected" },
];

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobSummary[] | null>(null);
  const [filter, setFilter] = useState<JobStatus | "all">("all");

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const qs = filter === "all" ? "" : `?status=${filter}`;
      const data = await api.get<{ results: JobSummary[] } | JobSummary[]>(`/api/jobs/${qs}`);
      if (!cancelled) setJobs(Array.isArray(data) ? data : data.results);
    }

    load();
    const interval = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [filter]);

  return (
    <div>
      <h1 className="text-2xl font-semibold text-slate-900">Jobs &amp; Progress</h1>
      <p className="mt-1 text-sm text-slate-500">Live status of every processing job. Refreshes automatically.</p>

      <div className="mt-4 flex flex-wrap gap-2">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              filter === f.value ? "bg-brand-600 text-white" : "bg-white text-slate-600 border border-slate-300"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      <div className="mt-6 overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Job</th>
              <th className="px-4 py-3">Mode</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">QC</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {jobs === null && <tr><td className="px-4 py-6 text-slate-400" colSpan={5}>Loading&hellip;</td></tr>}
            {jobs?.length === 0 && <tr><td className="px-4 py-6 text-slate-400" colSpan={5}>No jobs found.</td></tr>}
            {jobs?.map((j) => (
              <tr key={j.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <Link href={`/jobs/${j.id}`} className="font-mono text-xs text-brand-700 hover:underline">
                    {j.id.slice(0, 8)}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">{j.mode === "recreate_studio" ? "Recreate Studio" : "Enhance Only"}</td>
                <td className="px-4 py-3"><StatusBadge status={j.status} /></td>
                <td className="px-4 py-3 text-slate-500">
                  {j.qc_passed === null ? "—" : j.qc_passed ? "Passed" : "Flagged"}
                </td>
                <td className="px-4 py-3 text-slate-500">{new Date(j.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
