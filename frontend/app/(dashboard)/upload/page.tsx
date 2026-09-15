"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import type { Batch, ProcessingMode } from "@/lib/types";
import UploadDropzone from "@/components/UploadDropzone";

export default function UploadPage() {
  const router = useRouter();
  const [batchName, setBatchName] = useState("");
  const [mode, setMode] = useState<ProcessingMode>("enhance_only");
  const [outputSize, setOutputSize] = useState("");
  const [padding, setPadding] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (files.length === 0) {
      setError("Add at least one image to upload.");
      return;
    }
    setSubmitting(true);
    try {
      setProgress("Creating batch...");
      const batch = await api.post<Batch>("/api/batches/", {
        name: batchName || `Batch ${new Date().toLocaleString()}`,
        default_mode: mode,
        output_size_px: outputSize ? Number(outputSize) : null,
        padding_percent: padding ? Number(padding) : null,
      });

      setProgress(`Uploading ${files.length} image(s)...`);
      const form = new FormData();
      form.append("batch", batch.id);
      files.forEach((f) => form.append("files", f));
      await api.postForm(`/api/images/`, form);

      setProgress("Done — redirecting to job progress...");
      router.push(`/results/${batch.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? "Upload failed. Please check your files and try again." : "Unexpected error.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-semibold text-slate-900">Upload Product Photos</h1>
      <p className="mt-1 text-sm text-slate-500">
        Upload single or bulk raw photos. Each image is queued for automated processing as soon as you submit.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-6">
        <div className="card space-y-4 p-6">
          <div>
            <label className="label" htmlFor="batchName">Batch name</label>
            <input
              id="batchName"
              className="input"
              placeholder="e.g. Fall Catalog Drop 1"
              value={batchName}
              onChange={(e) => setBatchName(e.target.value)}
            />
          </div>

          <div>
            <span className="label">Processing mode</span>
            <div className="grid gap-3 sm:grid-cols-2">
              <label
                className={`cursor-pointer rounded-md border p-4 text-sm ${
                  mode === "recreate_studio" ? "border-brand-500 ring-1 ring-brand-500" : "border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  name="mode"
                  value="recreate_studio"
                  checked={mode === "recreate_studio"}
                  onChange={() => setMode("recreate_studio")}
                  className="sr-only"
                />
                <p className="font-medium text-slate-900">Recreate Studio Mode</p>
                <p className="mt-1 text-xs text-slate-500">
                  AI rebuilds the product as a professional front-facing studio photo, preserving shape/color/texture.
                </p>
              </label>
              <label
                className={`cursor-pointer rounded-md border p-4 text-sm ${
                  mode === "enhance_only" ? "border-brand-500 ring-1 ring-brand-500" : "border-slate-300"
                }`}
              >
                <input
                  type="radio"
                  name="mode"
                  value="enhance_only"
                  checked={mode === "enhance_only"}
                  onChange={() => setMode("enhance_only")}
                  className="sr-only"
                />
                <p className="font-medium text-slate-900">Enhance Only Mode</p>
                <p className="mt-1 text-xs text-slate-500">
                  Preserves the original photo; only improves quality, removes background, whitens, squares & centers.
                </p>
              </label>
            </div>
          </div>

          <details className="text-sm">
            <summary className="cursor-pointer font-medium text-slate-700">Advanced overrides (optional)</summary>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              <div>
                <label className="label" htmlFor="outputSize">Output size (px)</label>
                <input
                  id="outputSize"
                  type="number"
                  min={200}
                  className="input"
                  placeholder="Admin default"
                  value={outputSize}
                  onChange={(e) => setOutputSize(e.target.value)}
                />
              </div>
              <div>
                <label className="label" htmlFor="padding">Padding (%)</label>
                <input
                  id="padding"
                  type="number"
                  min={0}
                  max={40}
                  className="input"
                  placeholder="Admin default"
                  value={padding}
                  onChange={(e) => setPadding(e.target.value)}
                />
              </div>
            </div>
          </details>
        </div>

        <div className="card p-6">
          <UploadDropzone files={files} onChange={setFiles} />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {progress && submitting && <p className="text-sm text-slate-500">{progress}</p>}

        <button type="submit" disabled={submitting} className="btn-primary">
          {submitting ? "Uploading..." : `Upload ${files.length || ""} image${files.length === 1 ? "" : "s"}`}
        </button>
      </form>
    </div>
  );
}
