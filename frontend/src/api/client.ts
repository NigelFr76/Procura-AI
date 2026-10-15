import axios from 'axios';
import {
  EvaluationState,
  ScenarioRunResult,
  NegotiationSimResult,
  DocumentUploadResponse,
  SSEAgentEvent,
  AuditRecord,
  AuditVerificationResult,
} from '../types/procurement';

const API_BASE = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // Evaluations
  startEvaluation: async (payload: {
    text: string;
    budget_ceiling?: number;
    target_delivery_date?: string;
    currency?: string;
    required_certifications?: string[];
    candidate_vendors?: any[];
    compliance_rules?: any[];
    quotations?: any[];
    scoring_policy?: any;
    thread_id?: string;
  }): Promise<EvaluationState> => {
    const res = await apiClient.post<EvaluationState>('/evaluations', payload);
    return res.data;
  },

  getEvaluationStatus: async (threadId: string): Promise<EvaluationState> => {
    const res = await apiClient.get<EvaluationState>(`/evaluations/${threadId}`);
    return res.data;
  },

  submitApproval: async (
    threadId: string,
    action: 'APPROVED' | 'REJECTED' | 'MODIFICATION_REQUESTED',
    comments: string
  ): Promise<any> => {
    const res = await apiClient.post(`/evaluations/${threadId}/approval`, {
      action,
      comments,
    });
    return res.data;
  },

  // Scenarios
  simulateScenario: async (payload: {
    scenario_name: string;
    description?: string;
    baseline_evaluation_id?: string;
    baseline_scorecard: any;
    criteria_weights_override?: Record<string, number>;
    landed_cost_adjustments?: Record<string, number>;
    excluded_vendor_ids?: string[];
  }): Promise<ScenarioRunResult> => {
    const res = await apiClient.post<ScenarioRunResult>('/scenarios/simulate', payload);
    return res.data;
  },

  // Negotiations
  simulateNegotiation: async (payload: {
    vendor_id: string;
    vendor_name: string;
    baseline_quoted_price: number;
    target_discount_pct: number;
    max_rounds?: number;
    concession_strategy?: 'AGGRESSIVE' | 'BALANCED' | 'CONSERVATIVE';
    cost_floor_margin?: number;
  }): Promise<NegotiationSimResult> => {
    const res = await apiClient.post<NegotiationSimResult>('/negotiations/simulate', payload);
    return res.data;
  },

  // Documents
  uploadDocument: async (file: File): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await apiClient.post<DocumentUploadResponse>('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  // Audit Ledger & Integrity
  getAuditLogs: async (): Promise<AuditRecord[]> => {
    const res = await apiClient.get<AuditRecord[]>('/audit/logs');
    return res.data;
  },

  verifyAuditLedger: async (): Promise<AuditVerificationResult> => {
    const res = await apiClient.get<AuditVerificationResult>('/audit/verify');
    return res.data;
  },

  // SSE Stream
  subscribeToSSE: (
    threadId: string,
    onMessage: (event: SSEAgentEvent) => void,
    onError?: (error: any) => void
  ): (() => void) => {
    const eventSource = new EventSource(`${API_BASE}/events/stream/${threadId}`);

    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        onMessage(parsed);
      } catch (err) {
        console.error('Failed to parse SSE event data', err);
      }
    };

    eventSource.onerror = (err) => {
      if (onError) onError(err);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  },
};

