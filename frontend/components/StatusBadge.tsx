import type { JobStatus } from "@/lib/types";

const STYLES: Record<JobStatus, string> = {
  queued: "bg-slate-100 text-slate-700",
  processing: "bg-blue-100 text-blue-700",
  needs_review: "bg-amber-100 text-amber-800",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  rejected: "bg-red-100 text-red-700",
};

const LABELS: Record<JobStatus, string> = {
  queued: "Queued",
  processing: "Processing",
  needs_review: "Needs Review",
  completed: "Completed",
  failed: "Failed",
  rejected: "Rejected",
};

export default function StatusBadge({ status }: { status: JobStatus }) {
  return <span className={`badge ${STYLES[status]}`}>{LABELS[status]}</span>;
}
