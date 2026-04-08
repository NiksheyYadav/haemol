import type { AnalysisResult, AboutStats, ExtractedParam, MetricsSnapshot, PrivacyPolicy, ReportRecord } from "@biomarkly/contracts";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

type ApiReport = {
  id: string;
  source_type: string;
  locale: string;
  sex: string;
  age: number;
  status: string;
  extraction_status: string;
  extraction_step: string;
  created_at: string;
  file_name?: string | null;
  raw_text?: string | null;
  extracted_params: Array<{
    id: string;
    name: string;
    canonical_name: string;
    category: string;
    value: number;
    unit: string;
    confidence: number;
    is_flagged: boolean;
    ref_range_key: string;
    raw_reference_range: string;
    reference_range: { min: number | null; max: number | null; unit: string; note?: string };
    delta_from_range: number | null;
    note?: string;
  }>;
  analysis_id?: string | null;
  error_message?: string | null;
};

type ApiAnalysis = {
  id: string;
  report_id: string;
  status: string;
  created_at: string;
  summary: string;
  conditions: Array<{
    condition: string;
    severity: "low" | "moderate" | "high";
    summary: string;
    explanation: string;
    probability: number;
    model_name: string;
    model_version: string;
  }>;
  abnormal_params: ApiReport["extracted_params"];
  specialist_models: Array<{
    model_name: string;
    model_version: string;
    probability: number;
    severity: "low" | "moderate" | "high";
    condition: string;
    explanation: string;
    top_features: string[];
  }>;
  recommendations: AnalysisResult["recommendations"];
  confidence_scores: Record<string, number>;
  detailed_report: {
    overview: string;
    key_findings: string[];
    parameter_findings: Array<{
      parameter_name: string;
      category: string;
      status: string;
      confidence: number;
      explanation: string;
      clinical_note: string;
    }>;
    follow_up: string;
  };
  audio_jobs: Array<{
    id: string;
    language: string;
    status: "pending" | "done" | "failed";
    audio_url?: string | null;
    fallback_text?: string | null;
    created_at: string;
  }>;
};

type ApiAbout = {
  models: Array<{ name: string; f1: number; version: string }>;
  pipeline: string[];
  training_data: Array<{ name: string; size: string }>;
};

type ApiPrivacy = {
  retention_days: number;
  training_requires_consent: boolean;
  encryption_at_rest: string;
  encryption_in_transit: string;
};

function mapParam(param: ApiReport["extracted_params"][number]): ExtractedParam {
  return {
    id: param.id,
    name: param.name,
    canonicalName: param.canonical_name,
    category: param.category,
    value: param.value,
    unit: param.unit,
    confidence: param.confidence,
    isFlagged: param.is_flagged,
    rawReferenceRange: param.raw_reference_range,
    referenceRange: param.reference_range,
    deltaFromRange: param.delta_from_range,
    note: param.note,
    refRangeKey: param.ref_range_key
  };
}

function mapReport(report: ApiReport): ReportRecord {
  return {
    id: report.id,
    sourceType: report.source_type as ReportRecord["sourceType"],
    createdAt: report.created_at,
    locale: report.locale as ReportRecord["locale"],
    sex: report.sex,
    age: report.age,
    consented: true,
    status: report.status as ReportRecord["status"],
    extractionStep: report.extraction_step as ReportRecord["extractionStep"],
    fileName: report.file_name,
    rawText: report.raw_text,
    extractedParams: report.extracted_params.map(mapParam),
    analysisId: report.analysis_id,
    errorMessage: report.error_message
  };
}

function mapAnalysis(analysis: ApiAnalysis): AnalysisResult {
  return {
    id: analysis.id,
    reportId: analysis.report_id,
    createdAt: analysis.created_at,
    conditions: analysis.conditions.map((condition) => ({
      condition: condition.condition,
      severity: condition.severity,
      summary: condition.summary,
      explanation: condition.explanation,
      probability: condition.probability,
      modelName: condition.model_name,
      modelVersion: condition.model_version
    })),
    abnormalParams: analysis.abnormal_params.map(mapParam),
    specialistModels: analysis.specialist_models.map((model) => ({
      modelName: model.model_name,
      modelVersion: model.model_version,
      probability: model.probability,
      severity: model.severity,
      condition: model.condition,
      explanation: model.explanation,
      topFeatures: model.top_features
    })),
    recommendations: analysis.recommendations,
    confidenceScores: analysis.confidence_scores,
    summary: analysis.summary,
    detailedReport: {
      overview: analysis.detailed_report.overview,
      keyFindings: analysis.detailed_report.key_findings,
      parameterFindings: analysis.detailed_report.parameter_findings.map((item) => ({
        parameterName: item.parameter_name,
        category: item.category,
        status: item.status,
        confidence: item.confidence,
        explanation: item.explanation,
        clinicalNote: item.clinical_note
      })),
      followUp: analysis.detailed_report.follow_up
    },
    audioJobs: analysis.audio_jobs.map((job) => ({
      id: job.id,
      language: job.language,
      status: job.status,
      audioUrl: job.audio_url,
      fallbackText: job.fallback_text,
      createdAt: job.created_at
    }))
  };
}

export async function createFileReport(formData: FormData): Promise<ReportRecord> {
  const report = await request<ApiReport>("/reports", { method: "POST", body: formData });
  return mapReport(report);
}

export async function createTextReport(payload: Record<string, unknown>): Promise<ReportRecord> {
  const report = await request<ApiReport>("/reports", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return mapReport(report);
}

export async function getReport(reportId: string): Promise<ReportRecord> {
  const report = await request<ApiReport>(`/reports/${reportId}`);
  return mapReport(report);
}

export async function patchReport(reportId: string, payload: Record<string, unknown>): Promise<ReportRecord> {
  const report = await request<ApiReport>(`/reports/${reportId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return mapReport(report);
}

export async function analyzeReport(reportId: string): Promise<{ analysis_id: string }> {
  return request<{ analysis_id: string }>(`/reports/${reportId}/analyze`, { method: "POST" });
}

export async function getAnalysis(analysisId: string): Promise<AnalysisResult> {
  const analysis = await request<ApiAnalysis>(`/analyses/${analysisId}`);
  return mapAnalysis(analysis);
}

export async function requestAudio(analysisId: string, language: string): Promise<{ audio_job_id: string }> {
  return request<{ audio_job_id: string }>(`/analyses/${analysisId}/audio`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ language })
  });
}

export async function getAudio(analysisId: string, language: string): Promise<{ status: string; audio_url: string | null; fallback_text: string | null }> {
  return request<{ status: string; audio_url: string | null; fallback_text: string | null }>(`/analyses/${analysisId}/audio/${language}`);
}

export async function submitFeedback(analysisId: string, payload: { sentiment: "up" | "down"; text?: string }): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/analyses/${analysisId}/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function getAbout(): Promise<AboutStats> {
  const about = await request<ApiAbout>("/about");
  return {
    models: about.models,
    pipeline: about.pipeline,
    trainingData: about.training_data
  };
}

export async function getPrivacy(): Promise<PrivacyPolicy> {
  const privacy = await request<ApiPrivacy>("/about/privacy");
  return {
    retentionDays: privacy.retention_days,
    trainingRequiresConsent: privacy.training_requires_consent,
    encryptionAtRest: privacy.encryption_at_rest,
    encryptionInTransit: privacy.encryption_in_transit
  };
}

export async function sendEvent(payload: Record<string, unknown>): Promise<void> {
  await request<void>("/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}

export async function getMetrics(token: string): Promise<MetricsSnapshot> {
  return request<MetricsSnapshot>("/admin/metrics", {
    headers: { Authorization: `Bearer ${token}` }
  });
}
