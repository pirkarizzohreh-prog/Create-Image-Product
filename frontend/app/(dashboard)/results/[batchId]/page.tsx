"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import type { Batch, ProductImage } from "@/lib/types";
import StatusBadge from "@/components/StatusBadge";

export default function ResultsPage() {
  const params = useParams<{ batchId: string }>();
  const [batch, setBatch] = useState<Batch | null>(null);
  const [images, setImages] = useState<ProductImage[] | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const [b, imgs] = await Promise.all([
        api.get<Batch>(`/api/batches/${params.batchId}/`),
        api.get<{ results: ProductImage[] } | ProductImage[]>(`/api/images/?batch=${params.batchId}`),
      ]);
      if (!cancelled) {
        setBatch(b);
        setImages(Array.isArray(imgs) ? imgs : imgs.results);
      }
    }
    load();
    const interval = setInterval(load, 5000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [params.batchId]);

  async function handleDownloadAll() {
    setDownloading(true);
    try {
      const res = await api.post<{ url: string }>(`/api/batches/${params.batchId}/download/`);
      window.location.href = res.url;
    } catch {
      alert("No completed outputs are ready to download yet.");
    } finally {
      setDownloading(false);
    }
  }

  const filtered = images?.filter((img) => filter === "all" || img.latest_job?.status === filter) ?? [];

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">{batch?.name ?? "Batch"}</h1>
          <p className="mt-1 text-sm text-slate-500">{images?.length ?? 0} image(s) in this batch.</p>
        </div>
        <button onClick={handleDownloadAll} disabled={downloading} className="btn-primary">
          {downloading ? "Preparing ZIP..." : "Download all (ZIP)"}
        </button>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        {["all", "queued", "processing", "needs_review", "completed", "failed", "rejected"].map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              filter === s ? "bg-brand-600 text-white" : "bg-white text-slate-600 border border-slate-300"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
        {images === null && <p className="text-slate-400">Loading&hellip;</p>}
        {images !== null && filtered.length === 0 && <p className="text-slate-400">No images match this filter.</p>}
        {filtered.map((img) => (
          <Link
            key={img.id}
            href={img.latest_job ? `/jobs/${img.latest_job.id}` : "#"}
            className="card overflow-hidden hover:shadow-md"
          >
            <div className="flex h-40 items-center justify-center bg-slate-50">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={img.latest_job?.output_url || img.source_url || undefined}
                alt={img.original_filename}
                className="h-full w-full object-contain"
              />
            </div>
            <div className="space-y-1 p-3">
              <p className="truncate text-xs text-slate-600">{img.original_filename}</p>
              {img.latest_job && <StatusBadge status={img.latest_job.status} />}
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
