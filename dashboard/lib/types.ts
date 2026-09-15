export type DecisionType = "ALLOW" | "REVIEW" | "DENY" | "IDEMPOTENT_REPLAY" | "UNKNOWN" | "SUCCEEDED";

export type SourceTrust = "TRUSTED" | "UNTRUSTED" | "UNKNOWN";

export interface HealthComponent {
  status: string;
  [key: string]: any;
}

export interface SystemHealth {
  status: string;
  timestamp: string;
  components: {
    api: HealthComponent;
    postgres: HealthComponent;
    risk_engine: HealthComponent;
    razorpayx: HealthComponent;
    audit_chain: {
      status: string;
      valid: boolean;
      events_count: number;
    };
  };
}

export interface OverviewStats {
  total_agents: number;
  active_mandates: number;
  governed_amount_paise: number;
  governed_amount_inr: number;
  total_transactions: number;
  decisions: {
    ALLOW: number;
    REVIEW: number;
    DENY: number;
    IDEMPOTENT_REPLAY: number;
  };
}

export interface TransactionSummary {
  txn_id: string;
  agent_id: string;
  payee_id: string;
  category: string;
  amount: number;
  amount_inr: number;
  timestamp: string;
  status: string;
  decision: DecisionType;
  anomaly_score?: number | null;
  provenance_trust?: SourceTrust | null;
  razorpay_payout_id?: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface FullTransactionInvestigation {
  request: {
    txn_id: string;
    agent_id: string;
    agent_name: string;
    payee_id: string;
    category: string;
    amount: number;
    amount_inr: number;
    timestamp: string;
  };
  policy: {
    mandate_id?: string | null;
    mandate_status?: string | null;
    txn_cap?: number | null;
    daily_cap?: number | null;
    weekly_cap?: number | null;
    allowed_categories: string[];
    allowed_payees?: string[] | null;
    policy_allowed: boolean;
    policy_reason?: string | null;
  };
  behavior: {
    anomaly_score?: number | null;
    model_version: string;
    canonical_features: Record<string, number>;
    behavior_reasons: string[];
  };
  provenance: {
    source_type: string;
    source_id: string;
    source_trust: SourceTrust;
    payment_intent_origin: string;
    provenance_reasons: string[];
  };
  decision: {
    decision: DecisionType;
    reason_codes: string[];
    anomaly_score?: number | null;
    timestamp: string;
  };
  execution: {
    status: string;
    razorpay_payout_id?: string | null;
  };
  audit: Array<{
    sequence_id: number;
    event_id: string;
    event_type: string;
    timestamp: string;
    event_hash: string;
    previous_event_hash: string;
  }>;
}

export interface AgentSummary {
  agent_id: string;
  name: string;
  status: string;
  mandate_id?: string | null;
  mandate_status: string;
  daily_cap: number;
  daily_cap_inr: number;
  daily_usage: number;
  daily_usage_inr: number;
  weekly_cap: number;
  weekly_cap_inr: number;
  weekly_usage: number;
  weekly_usage_inr: number;
  utilization_pct: number;
  transaction_count: number;
}

export interface AgentDetail extends AgentSummary {
  mandate?: {
    mandate_id: string;
    version: number;
    effective_from: string;
    expires_at: string;
    daily_cap: number;
    weekly_cap: number;
    txn_cap: number;
    allowed_categories: string[];
    status: string;
  } | null;
  recent_transactions: Array<{
    txn_id: string;
    amount_inr: number;
    payee_id: string;
    category: string;
    status: string;
    decision: DecisionType;
    timestamp: string;
  }>;
}

export interface MandateSummary {
  mandate_id: string;
  agent_id: string;
  version: number;
  status: string;
  daily_cap: number;
  daily_cap_inr: number;
  weekly_cap: number;
  weekly_cap_inr: number;
  txn_cap: number;
  txn_cap_inr: number;
  allowed_categories: string[];
  allowed_payees?: string[] | null;
  effective_from: string;
  expires_at: string;
  daily_usage: number;
  daily_usage_inr: number;
  utilization_pct: number;
}

export interface RiskOverview {
  total_evaluations: number;
  decisions: Record<string, number>;
  provenance_flags_count: number;
  score_buckets: {
    low_risk_lt_03: number;
    moderate_03_05: number;
    elevated_05_07: number;
    high_risk_gte_07: number;
  };
  reason_code_frequencies: Array<{ reason: string; count: number }>;
}

export interface AuditEventItem {
  sequence_id: number;
  event_id: string;
  entity_id: string;
  event_type: string;
  timestamp: string;
  previous_event_hash: string;
  event_hash: string;
}

export interface AuditVerificationResult {
  valid: boolean;
  events_checked: number;
  failed_sequence_id?: number;
  failed_event_id?: string;
  reason?: string;
  first_sequence_id?: number;
  last_sequence_id?: number;
  timestamp?: string;
  message?: string;
}

export interface DemoScenarioResult {
  scenario_id: string;
  scenario_name: string;
  description: string;
  expected_decision: string;
  actual_decision: string;
  matched_expected: boolean;
  transaction_id: string;
  agent_id: string;
  reason_codes: string[];
  execution_status: string;
  razorpay_payout_id?: string | null;
  audit_events_created?: number;
  audit_events_count?: number;
  execution_occurred: boolean;
}
