// Mirrors backend Pydantic schemas (app/schemas/*). Single source of truth is
// the OpenAPI spec at /docs — regenerate here if the backend contract changes.

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  id: string;
  email: string;
  is_active: boolean;
  created_at: string;
}

export type AnalysisStatus = "pending" | "running" | "completed" | "failed";
export type Severity = "critical" | "high" | "medium" | "low";

export interface AnalysisAccepted {
  analysis_id: string;
  log_file_id: string;
  status: AnalysisStatus;
}

export interface Analysis {
  id: string;
  log_file_id: string;
  status: AnalysisStatus;
  error_message: string | null;
  total_lines: number;
  parsed_lines: number;
  error_lines: number;
  group_count: number;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface AnalysisListItem extends Analysis {
  filename: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface InsightPayload {
  error_type: string;
  severity: Severity;
  root_cause: string;
  possible_reasons: string[];
  explanation: string;
  suggested_fix: string;
  recommended_commands: string[];
  confidence: number;
}

export interface Insight {
  payload: InsightPayload;
  model: string;
  from_cache: boolean;
}

export interface ErrorGroup {
  id: string;
  fingerprint: string;
  template: string;
  level: string;
  severity: Severity;
  count: number;
  first_seen: string | null;
  last_seen: string | null;
  sample_lines: string[] | null;
  insight: Insight | null;
}

export interface SimilarIncident {
  group_id: string;
  analysis_id: string;
  template: string;
  severity: string;
  score: number;
}

export interface SimilarResponse {
  enabled: boolean;
  items: SimilarIncident[];
}

export interface ApiError {
  error: { code: string; message: string };
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations: { start_line: number; end_line: number }[] | null;
  created_at: string;
}

export interface ChatHistory {
  conversation_id: string;
  items: ChatMessage[];
}

export interface Report {
  id: string;
  analysis_id: string;
  title: string;
  markdown: string;
  created_at: string;
}

export interface TimelineEvent {
  group_id: string;
  label: string;
  severity: string;
  count: number;
  first_seen: string | null;
  last_seen: string | null;
  is_first_failure: boolean;
}

export interface InvestigationStep {
  seq: number;
  agent: string;
  action: string;
  content: Record<string, unknown>;
}

export interface Investigation {
  id: string;
  analysis_id: string;
  status: string;
  conclusion: string | null;
  confidence: number;
  verified: boolean;
  total_steps: number;
  steps: InvestigationStep[];
}
