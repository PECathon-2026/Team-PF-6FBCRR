export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface DOMElementDTO {
  id: string;
  tag: string;
  role?: string;
  text?: string;
  is_interactive: boolean;
  is_sensitive: boolean;
  sanitized_text?: string;
  bbox?: { x: number; y: number; width: number; height: number };
  attributes?: Record<string, string>;
}

export interface SensitiveSpanDTO {
  category: string;
  text?: string;
  confidence: number;
  detector: string;
  reason: string;
  replacement_token: string;
  element_id?: string;
  bbox?: { x: number; y: number; width: number; height: number };
}

export interface SanitizedObservationDTO {
  run_id: string;
  page_origin: string;
  page_title: string;
  elements: DOMElementDTO[];
  redactions_summary: Record<string, number>;
  provenance_hash: string;
  sanitized_screenshot_token?: string;
}

export interface ActionProposalDTO {
  action_type: string;
  element_id?: string;
  value?: string;
  secret_alias?: string;
  target_url?: string;
  reason: string;
}

export interface StepResponseDTO {
  step: number;
  action: ActionProposalDTO;
  risk_level: 'SAFE' | 'HIGH';
  risk_reason?: string;
  requires_approval: boolean;
  is_finished: boolean;
  message: string;
  observation: SanitizedObservationDTO;
}

export interface AuditEventDTO {
  event_id: string;
  timestamp: string;
  event_type: string;
  run_id: string;
  details: Record<string, any>;
}

export interface EvalScenarioResultDTO {
  scenario: string;
  name: string;
  task_success: boolean;
  steps: number;
  tp: number;
  fp: number;
  fn: number;
  recall: number;
  precision: number;
  detected_categories: string[];
}

export interface EvaluationReportDTO {
  timestamp: string;
  environment: Record<string, string>;
  metrics: {
    detection_recall: number;
    redaction_precision: number;
    leak_rate: number;
    observed_leaks: number;
    context_preservation: number;
    task_success_rate: number;
    tasks_completed: string;
    forced_canary_blocked: boolean;
    peak_rss_mb: number;
  };
  latencies_ms: {
    dom_collection: { p50: number; p95: number };
    privacy_sanitization: { p50: number; p95: number };
    model_gating_and_reasoning: { p50: number; p95: number };
    action_execution: { p50: number; p95: number };
  };
  scenarios: EvalScenarioResultDTO[];
}

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`);
    return res.json();
  },
  async getFixtures() {
    const res = await fetch(`${API_BASE}/api/fixtures`);
    return res.json();
  },
  async startSession(task: string, url?: string, scenario_key?: string, agent_type: string = 'mock') {
    const res = await fetch(`${API_BASE}/api/sessions/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task, url, scenario_key, agent_type }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async stepSession(sessionId: string) {
    const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/step`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async approveAction(sessionId: string, approved: boolean, reason?: string) {
    const res = await fetch(`${API_BASE}/api/sessions/${sessionId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ approved, reason }),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async getPrivacyPreview(runId: string) {
    const res = await fetch(`${API_BASE}/api/privacy/preview/${runId}`);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async getVaultSecrets() {
    const res = await fetch(`${API_BASE}/api/vault`);
    return res.json();
  },
  async addVaultSecret(alias: string, value: string, category: string) {
    const res = await fetch(`${API_BASE}/api/vault`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ alias, value, category }),
    });
    return res.json();
  },
  async deleteVaultSecret(alias: string) {
    const res = await fetch(`${API_BASE}/api/vault/${alias}`, {
      method: 'DELETE',
    });
    return res.json();
  },
  async getAuditEvents(limit: number = 100) {
    const res = await fetch(`${API_BASE}/api/audit?limit=${limit}`);
    return res.json();
  },
  async runEvaluation() {
    const res = await fetch(`${API_BASE}/api/evaluate`, {
      method: 'POST',
    });
    return res.json();
  },
  async getEvaluationResults(): Promise<EvaluationReportDTO> {
    const res = await fetch(`${API_BASE}/api/evaluation/latest`);
    if (!res.ok) throw new Error('Evaluation report not found');
    return res.json();
  }
};
