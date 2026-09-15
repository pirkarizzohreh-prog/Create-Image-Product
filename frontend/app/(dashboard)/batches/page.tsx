"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Batch } from "@/lib/types";

export default function BatchesPage() {
  const [batches, setBatches] = useState<Batch[] | null>(null);

  useEffect(() => {
    api.get<{ results: Batch[] } | Batch[]>("/api/batches/").then((data) => {
      setBatches(Array.isArray(data) ? data : data.results);
    });
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Batches</h1>
        <Link href="/upload" className="btn-primary">New upload</Link>
      </div>

      <div className="mt-6 overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50 text-left text-xs font-medium uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Name</th>
              <th className="px-4 py-3">Mode</th>
              <th className="px-4 py-3">Images</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {batches === null && (
              <tr><td className="px-4 py-6 text-slate-400" colSpan={5}>Loading&hellip;</td></tr>
            )}
            {batches?.length === 0 && (
              <tr><td className="px-4 py-6 text-slate-400" colSpan={5}>No batches yet. Start by uploading images.</td></tr>
            )}
            {batches?.map((b) => (
              <tr key={b.id} className="hover:bg-slate-50">
                <td className="px-4 py-3">
                  <Link href={`/results/${b.id}`} className="font-medium text-brand-700 hover:underline">
                    {b.name}
                  </Link>
                </td>
                <td className="px-4 py-3 text-slate-600">{b.default_mode === "recreate_studio" ? "Recreate Studio" : "Enhance Only"}</td>
                <td className="px-4 py-3 text-slate-600">{b.image_count ?? "—"}</td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {b.status_counts &&
                      Object.entries(b.status_counts).map(([status, count]) => (
                        <span key={status} className="badge bg-slate-100 text-slate-600">
                          {status}: {count}
                        </span>
                      ))}
                  </div>
                </td>
                <td className="px-4 py-3 text-slate-500">{new Date(b.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
