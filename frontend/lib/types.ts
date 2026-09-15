export type Role = "uploader" | "reviewer" | "admin";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  date_joined: string;
}

export type ProcessingMode = "recreate_studio" | "enhance_only";

export type JobStatus = "queued" | "processing" | "needs_review" | "completed" | "failed" | "rejected";

export interface Batch {
  id: string;
  name: string;
  owner: string;
  owner_email?: string;
  default_mode: ProcessingMode;
  output_size_px: number | null;
  padding_percent: number | null;
  output_format: string | null;
  prompt_template: string | null;
  image_count?: number;
  status_counts?: Record<string, number>;
  created_at: string;
  updated_at?: string;
}

export interface JobSummary {
  id: string;
  status: JobStatus;
  mode: ProcessingMode;
  qc_passed: boolean | null;
  output_url: string | null;
  created_at: string;
  finished_at: string | null;
}

export interface JobStageLog {
  id: string;
  stage: string;
  status: "running" | "success" | "skipped" | "failed";
  started_at: string;
  finished_at: string | null;
  duration_ms: number | null;
  detail: Record<string, unknown>;
  error_message: string;
}

export interface JobDetail {
  id: string;
  image: string;
  image_original_filename: string;
  batch_id: string;
  status: JobStatus;
  mode: ProcessingMode;
  params: Record<string, unknown>;
  output_url: string | null;
  output_width: number | null;
  output_height: number | null;
  qc_passed: boolean | null;
  qc_report: { passed: boolean; reasons: string[]; checks: Record<string, any> };
  error_message: string;
  started_at: string | null;
  finished_at: string | null;
  attempt: number;
  stage_logs: JobStageLog[];
  source_url: string | null;
  created_at: string;
}

export interface ProductImage {
  id: string;
  batch: string;
  source_url: string | null;
  original_filename: string;
  sku: string;
  product_name: string;
  category: string;
  processing_mode: ProcessingMode | null;
  effective_mode: ProcessingMode;
  latest_job: JobSummary | null;
  created_at: string;
}

export interface ReviewItem {
  id: string;
  job: string;
  job_detail: JobDetail;
  reasons: string[];
  decision: "pending" | "approved" | "rejected" | "replaced" | "rerun";
  decision_notes: string;
  reviewed_by_email?: string;
  reviewed_at: string | null;
  created_at: string;
}

export interface PipelineSettings {
  id: string;
  is_active: boolean;
  output_size_px: number;
  padding_percent: number;
  output_format: "WEBP" | "PNG" | "JPEG";
  output_quality: number;
  qc_background_whiteness_tolerance: number;
  qc_centering_tolerance_percent: number;
  qc_min_product_coverage_percent: number;
  qc_max_product_coverage_percent: number;
  qc_identity_similarity_threshold: number;
}

export interface PromptTemplate {
  id: string;
  name: string;
  category: string;
  template_text: string;
  is_default: boolean;
  created_at: string;
}

export interface StorageSettings {
  id: string;
  is_active: boolean;
  provider: "s3" | "r2" | "local";
  bucket_name: string;
  region: string;
  endpoint_url: string;
  path_prefix: string;
  signed_url_ttl_seconds: number;
}
