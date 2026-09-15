"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import type { JobDetail } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";
import BeforeAfter from "@/components/BeforeAfter";

const STAGE_LABELS: Record<string, string> = {
  ingest: "Ingest & Validate",
  enhance: "Quality Enhancement",
  ai_recreate: "AI Studio Recreation",
  remove_background: "Background Removal",
  compose_white: "Composite on White",
  square_center_pad: "Square / Center / Pad",
  export: "Export",
  qc: "Quality Control",
};

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const data = await api.get<JobDetail>(`/api/jobs/${params.id}/`);
      if (!cancelled) setJob(data);
    }
    load();
    const interval = setInterval(load, 4000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [params.id]);

  async function handleRetry() {
    setRetrying(true);
    try {
      const newJob = await api.post<JobDetail>(`/api/jobs/${params.id}/retry/`);
      window.location.href = `/jobs/${newJob.id}`;
    } finally {
      setRetrying(false);
    }
  }

  if (!job) return <div className="text-slate-400">Loading&hellip;</div>;

  const canRetry = ["failed", "rejected", "needs_review"].includes(job.status);

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">{job.image_original_filename}</h1>
          <p className="mt-1 flex items-center gap-2 text-sm text-slate-500">
            <StatusBadge status={job.status} />
            <span>Attempt #{job.attempt}</span>
            <span>&middot; {job.mode === "recreate_studio" ? "Recreate Studio" : "Enhance Only"}</span>
          </p>
        </div>
        {canRetry && (
          <button onClick={handleRetry} disabled={retrying} className="btn-primary">
            {retrying ? "Queuing retry..." : "Retry job"}
          </button>
        )}
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <div className="card p-6">
          <h2 className="text-sm font-semibold text-slate-700">Preview</h2>
          <div className="mt-3">
            <BeforeAfter beforeUrl={job.source_url} afterUrl={job.output_url} />
          </div>
          {job.output_url && (
            <a href={job.output_url} download className="btn-secondary mt-4 w-full">
              Download output
            </a>
          )}
        </div>

        <div className="space-y-6">
          <div className="card p-6">
            <h2 className="text-sm font-semibold text-slate-700">Pipeline stages</h2>
            <ul className="mt-3 space-y-2">
              {job.stage_logs.map((log) => (
                <li key={log.id} className="flex items-center justify-between rounded-md border border-slate-100 px-3 py-2 text-sm">
                  <span className="text-slate-700">{STAGE_LABELS[log.stage] ?? log.stage}</span>
                  <span className="flex items-center gap-2">
                    {log.duration_ms !== null && <span className="text-xs text-slate-400">{log.duration_ms}ms</span>}
                    <span
                      className={`badge ${
                        log.status === "success"
                          ? "bg-green-100 text-green-700"
                          : log.status === "failed"
                          ? "bg-red-100 text-red-700"
                          : log.status === "skipped"
                          ? "bg-slate-100 text-slate-500"
                          : "bg-blue-100 text-blue-700"
                      }`}
                    >
                      {log.status}
                    </span>
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {job.qc_report?.checks && (
            <div className="card p-6">
              <h2 className="text-sm font-semibold text-slate-700">Quality control report</h2>
              {job.qc_report.reasons?.length > 0 && (
                <ul className="mt-2 list-disc pl-5 text-sm text-amber-700">
                  {job.qc_report.reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              )}
              <dl className="mt-3 space-y-2 text-xs">
                {Object.entries(job.qc_report.checks).map(([name, check]: [string, any]) => (
                  <div key={name} className="flex items-center justify-between border-t border-slate-100 pt-2">
                    <dt className="capitalize text-slate-600">{name.replace(/_/g, " ")}</dt>
                    <dd className={check.passed ? "text-green-600" : "text-red-600"}>
                      {check.passed ? "Pass" : "Fail"}
                    </dd>
                  </div>
                ))}
              </dl>
            </div>
          )}

          {job.error_message && (
            <div className="card border-red-200 bg-red-50 p-6">
              <h2 className="text-sm font-semibold text-red-700">Error</h2>
              <p className="mt-2 text-sm text-red-700">{job.error_message}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
