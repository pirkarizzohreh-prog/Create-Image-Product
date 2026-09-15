"use client";

import { FormEvent, useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { PipelineSettings, PromptTemplate, StorageSettings } from "@/lib/types";

export default function AdminSettingsPage() {
  const [pipeline, setPipeline] = useState<PipelineSettings | null>(null);
  const [storage, setStorage] = useState<StorageSettings | null>(null);
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const [newTemplate, setNewTemplate] = useState({ name: "", category: "", template_text: "" });

  async function loadAll() {
    const [p, s, t] = await Promise.all([
      api.get<PipelineSettings>("/api/admin/pipeline-settings/"),
      api.get<StorageSettings>("/api/admin/storage-settings/"),
      api.get<{ results: PromptTemplate[] } | PromptTemplate[]>("/api/admin/prompt-templates/"),
    ]);
    setPipeline(p);
    setStorage(s);
    setTemplates(Array.isArray(t) ? t : t.results);
  }

  useEffect(() => {
    loadAll();
  }, []);

  async function savePipeline(e: FormEvent) {
    e.preventDefault();
    if (!pipeline) return;
    const updated = await api.put<PipelineSettings>("/api/admin/pipeline-settings/", pipeline);
    setPipeline(updated);
    flashSaved("Pipeline defaults saved.");
  }

  async function saveStorage(e: FormEvent) {
    e.preventDefault();
    if (!storage) return;
    const updated = await api.put<StorageSettings>("/api/admin/storage-settings/", storage);
    setStorage(updated);
    flashSaved("Storage settings saved.");
  }

  async function createTemplate(e: FormEvent) {
    e.preventDefault();
    await api.post("/api/admin/prompt-templates/", newTemplate);
    setNewTemplate({ name: "", category: "", template_text: "" });
    await loadAll();
    flashSaved("Prompt template created.");
  }

  async function setDefaultTemplate(id: string) {
    await api.patch(`/api/admin/prompt-templates/${id}/`, { is_default: true });
    await loadAll();
  }

  function flashSaved(msg: string) {
    setSavedMessage(msg);
    setTimeout(() => setSavedMessage(null), 2500);
  }

  if (!pipeline || !storage) return <div className="text-slate-400">Loading&hellip;</div>;

  return (
    <div className="max-w-3xl space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Admin Settings</h1>
        <p className="mt-1 text-sm text-slate-500">Defaults applied to new batches unless overridden per batch.</p>
        {savedMessage && <p className="mt-2 text-sm text-green-600">{savedMessage}</p>}
      </div>

      <form onSubmit={savePipeline} className="card space-y-4 p-6">
        <h2 className="text-sm font-semibold text-slate-700">Pipeline defaults</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Output size (px)">
            <input
              type="number"
              className="input"
              value={pipeline.output_size_px}
              onChange={(e) => setPipeline({ ...pipeline, output_size_px: Number(e.target.value) })}
            />
          </Field>
          <Field label="Padding (%)">
            <input
              type="number"
              step="0.1"
              className="input"
              value={pipeline.padding_percent}
              onChange={(e) => setPipeline({ ...pipeline, padding_percent: Number(e.target.value) })}
            />
          </Field>
          <Field label="Output format">
            <select
              className="input"
              value={pipeline.output_format}
              onChange={(e) => setPipeline({ ...pipeline, output_format: e.target.value as PipelineSettings["output_format"] })}
            >
              <option value="WEBP">WebP</option>
              <option value="PNG">PNG</option>
              <option value="JPEG">JPEG</option>
            </select>
          </Field>
          <Field label="Output quality">
            <input
              type="number"
              min={1}
              max={100}
              className="input"
              value={pipeline.output_quality}
              onChange={(e) => setPipeline({ ...pipeline, output_quality: Number(e.target.value) })}
            />
          </Field>
        </div>

        <h3 className="pt-2 text-sm font-semibold text-slate-700">QC thresholds</h3>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Background whiteness tolerance">
            <input
              type="number"
              step="0.1"
              className="input"
              value={pipeline.qc_background_whiteness_tolerance}
              onChange={(e) => setPipeline({ ...pipeline, qc_background_whiteness_tolerance: Number(e.target.value) })}
            />
          </Field>
          <Field label="Centering tolerance (%)">
            <input
              type="number"
              step="0.1"
              className="input"
              value={pipeline.qc_centering_tolerance_percent}
              onChange={(e) => setPipeline({ ...pipeline, qc_centering_tolerance_percent: Number(e.target.value) })}
            />
          </Field>
          <Field label="Min product coverage (%)">
            <input
              type="number"
              step="0.1"
              className="input"
              value={pipeline.qc_min_product_coverage_percent}
              onChange={(e) => setPipeline({ ...pipeline, qc_min_product_coverage_percent: Number(e.target.value) })}
            />
          </Field>
          <Field label="Max product coverage (%)">
            <input
              type="number"
              step="0.1"
              className="input"
              value={pipeline.qc_max_product_coverage_percent}
              onChange={(e) => setPipeline({ ...pipeline, qc_max_product_coverage_percent: Number(e.target.value) })}
            />
          </Field>
          <Field label="Identity similarity threshold (0-1)">
            <input
              type="number"
              step="0.01"
              min={0}
              max={1}
              className="input"
              value={pipeline.qc_identity_similarity_threshold}
              onChange={(e) => setPipeline({ ...pipeline, qc_identity_similarity_threshold: Number(e.target.value) })}
            />
          </Field>
        </div>

        <button type="submit" className="btn-primary">Save pipeline defaults</button>
      </form>

      <form onSubmit={saveStorage} className="card space-y-4 p-6">
        <h2 className="text-sm font-semibold text-slate-700">Storage settings</h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Provider">
            <select
              className="input"
              value={storage.provider}
              onChange={(e) => setStorage({ ...storage, provider: e.target.value as StorageSettings["provider"] })}
            >
              <option value="s3">AWS S3</option>
              <option value="r2">Cloudflare R2</option>
              <option value="local">Local filesystem (dev only)</option>
            </select>
          </Field>
          <Field label="Bucket name">
            <input className="input" value={storage.bucket_name} onChange={(e) => setStorage({ ...storage, bucket_name: e.target.value })} />
          </Field>
          <Field label="Region">
            <input className="input" value={storage.region} onChange={(e) => setStorage({ ...storage, region: e.target.value })} />
          </Field>
          <Field label="Endpoint URL (R2 / custom S3)">
            <input className="input" value={storage.endpoint_url} onChange={(e) => setStorage({ ...storage, endpoint_url: e.target.value })} />
          </Field>
          <Field label="Path prefix">
            <input className="input" value={storage.path_prefix} onChange={(e) => setStorage({ ...storage, path_prefix: e.target.value })} />
          </Field>
          <Field label="Signed URL TTL (seconds)">
            <input
              type="number"
              className="input"
              value={storage.signed_url_ttl_seconds}
              onChange={(e) => setStorage({ ...storage, signed_url_ttl_seconds: Number(e.target.value) })}
            />
          </Field>
        </div>
        <p className="text-xs text-slate-500">Credentials (access key/secret) are configured via environment variables, not here.</p>
        <button type="submit" className="btn-primary">Save storage settings</button>
      </form>

      <div className="card space-y-4 p-6">
        <h2 className="text-sm font-semibold text-slate-700">AI prompt templates</h2>
        <ul className="space-y-2">
          {templates.map((t) => (
            <li key={t.id} className="rounded-md border border-slate-200 p-3 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-900">
                  {t.name} {t.category && <span className="text-xs text-slate-400">({t.category})</span>}
                </span>
                {t.is_default ? (
                  <span className="badge bg-brand-100 text-brand-700">Default</span>
                ) : (
                  <button onClick={() => setDefaultTemplate(t.id)} className="text-xs text-brand-700 hover:underline">
                    Set as default
                  </button>
                )}
              </div>
              <p className="mt-1 whitespace-pre-wrap text-xs text-slate-500">{t.template_text}</p>
            </li>
          ))}
        </ul>

        <form onSubmit={createTemplate} className="space-y-3 border-t border-slate-100 pt-4">
          <h3 className="text-sm font-semibold text-slate-700">New template</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            <input
              placeholder="Name"
              className="input"
              required
              value={newTemplate.name}
              onChange={(e) => setNewTemplate({ ...newTemplate, name: e.target.value })}
            />
            <input
              placeholder="Category (optional)"
              className="input"
              value={newTemplate.category}
              onChange={(e) => setNewTemplate({ ...newTemplate, category: e.target.value })}
            />
          </div>
          <textarea
            placeholder="Prompt text"
            required
            rows={4}
            className="input"
            value={newTemplate.template_text}
            onChange={(e) => setNewTemplate({ ...newTemplate, template_text: e.target.value })}
          />
          <button type="submit" className="btn-secondary">Add template</button>
        </form>
      </div>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="label">{label}</span>
      {children}
    </label>
  );
}
