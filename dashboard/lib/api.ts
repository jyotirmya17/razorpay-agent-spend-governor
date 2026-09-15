import {
  SystemHealth,
  OverviewStats,
  PaginatedResponse,
  TransactionSummary,
  FullTransactionInvestigation,
  AgentSummary,
  AgentDetail,
  MandateSummary,
  RiskOverview,
  AuditEventItem,
  AuditVerificationResult,
  DemoScenarioResult,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function fetchJSON<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status} ${res.statusText}`;
    try {
      const errBody = await res.json();
      if (errBody.detail) {
        errorDetail = typeof errBody.detail === "string" ? errBody.detail : JSON.stringify(errBody.detail);
      } else if (errBody.error?.message) {
        errorDetail = errBody.error.message;
      }
    } catch {
      // Ignore JSON parse error for error fallback
    }
    throw new Error(errorDetail);
  }

  return res.json() as Promise<T>;
}

export const api = {
  getHealth: (): Promise<SystemHealth> => fetchJSON<SystemHealth>("/v1/health"),
  getOverviewStats: (): Promise<OverviewStats> => fetchJSON<OverviewStats>("/v1/overview/stats"),
  
  getTransactions: (params?: {
    page?: number;
    page_size?: number;
    decision?: string;
    agent_id?: string;
    search?: string;
  }): Promise<PaginatedResponse<TransactionSummary>> => {
    const searchParams = new URLSearchParams();
    if (params?.page) searchParams.set("page", params.page.toString());
    if (params?.page_size) searchParams.set("page_size", params.page_size.toString());
    if (params?.decision) searchParams.set("decision", params.decision);
    if (params?.agent_id) searchParams.set("agent_id", params.agent_id);
    if (params?.search) searchParams.set("search", params.search);

    const query = searchParams.toString();
    return fetchJSON<PaginatedResponse<TransactionSummary>>(`/v1/transactions${query ? `?${query}` : ""}`);
  },

  getTransactionFull: (txnId: string): Promise<FullTransactionInvestigation> =>
    fetchJSON<FullTransactionInvestigation>(`/v1/transactions/${encodeURIComponent(txnId)}/full`),

  getAgents: (): Promise<AgentSummary[]> => fetchJSON<AgentSummary[]>("/v1/agents"),

  getAgentDetail: (agentId: string): Promise<AgentDetail> =>
    fetchJSON<AgentDetail>(`/v1/agents/${encodeURIComponent(agentId)}/detail`),

  getMandates: (): Promise<MandateSummary[]> => fetchJSON<MandateSummary[]>("/v1/mandates"),

  revokeMandate: (mandateId: string): Promise<{ mandate_id: string; status: string; revoked_at: string }> =>
    fetchJSON<{ mandate_id: string; status: string; revoked_at: string }>(
      `/v1/mandates/${encodeURIComponent(mandateId)}/revoke`,
      { method: "POST" }
    ),

  getRiskOverview: (): Promise<RiskOverview> => fetchJSON<RiskOverview>("/v1/risk/overview"),

  getAuditEvents: (page: number = 1, pageSize: number = 20): Promise<PaginatedResponse<AuditEventItem>> =>
    fetchJSON<PaginatedResponse<AuditEventItem>>(`/v1/audit/events?page=${page}&page_size=${pageSize}`),

  verifyAuditChain: (): Promise<AuditVerificationResult> =>
    fetchJSON<AuditVerificationResult>("/v1/audit/verify", { method: "POST" }),

  runDemoScenario: (scenarioId: string): Promise<DemoScenarioResult> =>
    fetchJSON<DemoScenarioResult>(`/v1/demo/scenario/${scenarioId}`, { method: "POST" }),

  deactivateAgent: (agentId: string, adminToken: string): Promise<{ agent_id: string; is_active: boolean; message: string }> =>
    fetchJSON<{ agent_id: string; is_active: boolean; message: string }>(
      `/v1/agents/${encodeURIComponent(agentId)}`,
      { 
        method: "DELETE",
        headers: { "X-Admin-Token": adminToken }
      }
    ),
};
