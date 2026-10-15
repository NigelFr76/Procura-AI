export interface CriterionScore {
  criterion_id: string;
  criterion_name: string;
  raw_value: number | string;
  normalized_score: number | string;
  weight: number | string;
  weighted_score: number | string;
  unit?: string;
  direction: 'HIGHER_IS_BETTER' | 'LOWER_IS_BETTER';
}

export interface VendorScore {
  vendor_id: string;
  vendor_name: string;
  rank: number;
  overall_score: number | string;
  financial_score: number | string;
  technical_score: number | string;
  risk_score: number | string;
  compliance_score?: number | string;
  is_eligible: boolean;
  disqualification_reason?: string | null;
  landed_cost: number | string;
  currency: string;
  criteria_scores?: Record<string, CriterionScore>;
  notes?: string[];
}

export interface Scorecard {
  evaluation_id: string;
  evaluated_at?: string;
  currency: string;
  scoring_fingerprint: string;
  ranking: VendorScore[];
  applied_weights?: Record<string, number>;
}

export interface DecisionExplanation {
  recommended_vendor_id: string;
  recommended_vendor_name: string;
  summary: string;
  key_advantages: string[];
  identified_trade_offs: string[];
  contingencies: string[];
  hallucination_audit_passed?: boolean;
}

export interface EvaluationState {
  thread_id: string;
  evaluation_id?: string;
  status: string;
  is_clarification_needed: boolean;
  clarification_questions?: string[];
  scorecard?: Scorecard | null;
  decision_explanation?: DecisionExplanation | null;
  interrupt?: any;
  approval_action?: string;
  approval_comments?: string;
  signature_hash?: string;
  decided_at?: string;
}

export interface DocumentUploadResponse {
  document_id: string;
  file_name: string;
  total_pages: number;
  sha256: string;
  has_injection_risk: boolean;
  security_warnings: string[];
  blocks_count: number;
  tables_count: number;
}

export interface BoundingBoxProof {
  term_name: string;
  extracted_value: string;
  unit: string;
  page_number: number;
  confidence: number;
  bbox: [number, number, number, number]; // [x0, y0, x1, y1] normalized 0-1
  source_quote: string;
}

export interface ScenarioDifferential {
  vendor_id: string;
  vendor_name: string;
  baseline_score: number | string;
  scenario_score: number | string;
  delta_score: number | string;
  baseline_rank: number;
  scenario_rank: number;
  delta_rank: number;
  baseline_cost: number | string;
  scenario_cost: number | string;
  delta_cost: number | string;
}

export interface ScenarioRunResult {
  scenario_id: string;
  scenario_name: string;
  baseline_evaluation_id: string;
  winner_displaced: boolean;
  new_winner_id: string;
  new_winner_name: string;
  baseline_winner_id: string;
  baseline_winner_name: string;
  differentials: ScenarioDifferential[];
  trade_off_analysis: string;
  recommendations: string[];
}

export interface NegotiationRound {
  round_number: number;
  buyer_target_price: number;
  seller_counteroffer: number;
  concession_amount: number;
  status: string;
  rationale?: string;
}

export interface NegotiationSimResult {
  vendor_id: string;
  vendor_name: string;
  initial_price: number;
  final_price: number;
  target_discount_pct: number;
  achieved_discount_pct: number;
  cost_floor: number;
  rounds: NegotiationRound[];
  outcome: 'ACCEPTED' | 'REJECTED' | 'COUNTEROFFER_FLOORED';
}

export interface SSEAgentEvent {
  event_type: string;
  thread_id: string;
  status?: string;
  node?: string;
  payload?: any;
  timestamp: string;
}
