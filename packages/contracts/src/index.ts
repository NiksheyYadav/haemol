export type Locale = "en" | "hi";
export type SourceType = "file" | "text" | "manual";
export type ReportStatus = "pending" | "processing" | "ready" | "error" | "deleted";
export type ExtractionStep = "queued" | "parsing" | "ocr" | "nlp_extraction" | "done" | "failed";
export type AudioJobStatus = "pending" | "done" | "failed";
export type FeedbackSentiment = "up" | "down";
export type AnalysisSeverity = "low" | "moderate" | "high";

export interface ReferenceRange {
  min: number | null;
  max: number | null;
  unit: string;
  note?: string;
}

export interface ExtractedParam {
  id: string;
  name: string;
  canonicalName: string;
  category: string;
  value: number;
  unit: string;
  confidence: number;
  isFlagged: boolean;
  refRangeKey?: string;
  rawReferenceRange: string;
  referenceRange: ReferenceRange;
  deltaFromRange: number | null;
  note?: string;
}

export interface AnalysisCondition {
  condition: string;
  severity: AnalysisSeverity;
  summary: string;
  explanation: string;
  probability: number;
  modelName: string;
  modelVersion: string;
}

export interface SpecialistModelResult {
  modelName: string;
  modelVersion: string;
  probability: number;
  severity: AnalysisSeverity;
  condition: string;
  explanation: string;
  topFeatures: string[];
}

export interface RecommendationLink {
  label: string;
  href: string;
}

export interface RecommendationItem {
  text: string;
  caveat: string;
  sources: RecommendationLink[];
}

export interface DetailedParamFinding {
  parameterName: string;
  category: string;
  status: string;
  confidence: number;
  explanation: string;
  clinicalNote: string;
}

export interface DetailedReport {
  overview: string;
  keyFindings: string[];
  parameterFindings: DetailedParamFinding[];
  followUp: string;
}

export interface AudioJobSummary {
  id: string;
  language: string;
  status: AudioJobStatus;
  audioUrl?: string | null;
  fallbackText?: string | null;
  createdAt: string;
}

export interface AnalysisResult {
  id: string;
  reportId: string;
  createdAt: string;
  conditions: AnalysisCondition[];
  abnormalParams: ExtractedParam[];
  specialistModels: SpecialistModelResult[];
  recommendations: RecommendationItem[];
  confidenceScores: Record<string, number>;
  summary: string;
  detailedReport: DetailedReport;
  audioJobs: AudioJobSummary[];
}

export interface ReportRecord {
  id: string;
  sourceType: SourceType;
  createdAt: string;
  locale: Locale;
  sex: string;
  age: number;
  consented: boolean;
  status: ReportStatus;
  extractionStep: ExtractionStep;
  fileName?: string | null;
  rawText?: string | null;
  extractedParams: ExtractedParam[];
  analysisId?: string | null;
  errorMessage?: string | null;
}

export interface AboutStats {
  models: Array<{ name: string; f1: number; version: string }>;
  pipeline: string[];
  trainingData: Array<{ name: string; size: string }>;
}

export interface PrivacyPolicy {
  retentionDays: number;
  trainingRequiresConsent: boolean;
  encryptionAtRest: string;
  encryptionInTransit: string;
}

export interface MetricsSnapshot {
  extractionSuccessRate: number;
  avgAnalysisLatencyMs: number;
  errorRateByType: Record<string, number>;
  audioUsageByLanguage: Record<string, number>;
  feedbackScore7d: number;
}
