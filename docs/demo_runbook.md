# Agent Spend Governor — Demo Runbook (Phase 4.7)

A deterministic, evaluator-ready 5-minute demonstration of the Agent Spend Governor.

---

## Prerequisites

1. PostgreSQL running (`docker-compose up -d`)
2. `.env` configured with RazorpayX Test Mode credentials
3. Demo fixtures seeded: `python scripts/seed_demo.py`
4. Governor running: `uvicorn gateway.main:app --reload`

---

## Demo Flow

### 0:00 — Problem Statement (30 sec)

> Autonomous AI agents can be authorized to make payments — but they can still be risky.
> Risk arises not just from the amount or payee, but from _who_ made the decision,
> _how_ the agent is behaving, and _where_ the payment instruction came from.
>
> The Governor adds a defense layer around every payout. It evaluates policy,
> behavior, and provenance — and blocks or flags anomalies before Razorpay is ever called.

---

### 0:30 — Architecture Overview (30 sec)

Show `docs/architecture.md` or the pipeline diagram:

```
Agent -> Policy -> Behavior -> Provenance -> Decision -> [RazorpayX or STOP]
```

Key design points:
- BLOCK and FLAG are **structurally prevented** from reaching Razorpay
- Missing provenance is **UNKNOWN by default**, never implicitly trusted
- Audit chain is tamper-evident (SHA-256 hash chain)

---

### 1:00 — Demo 1: Normal Authorized Payout (ALLOW)

**Agent**: `demo_normal_agent`
**Why this matters**: Shows the full ALLOW path including a real RazorpayX Test Mode call.

```bash
curl -X POST http://localhost:8000/v1/payouts \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"demo_normal_agent","request_id":"req_demo_1","idempotency_key":"demo_key_1","payee_id":"<FUND_ACCOUNT_ID>","category":"cloud","amount":100,"provenance":{"source_type":"TRUSTED_TASK","source_id":"task_monthly_infra","source_trust":"TRUSTED","payment_intent_origin":"AGENT_TOOL"}}'
```

Expected:
```json
{"decision": "ALLOW", "status": "SUCCEEDED", "razorpay_payout_id": "pout_..."}
```

Then check the audit timeline:
```bash
curl http://localhost:8000/v1/audit/demo_key_1
```

---

### 2:00 — Demo 2: Policy Violation (BLOCK)

**Agent**: `demo_policy_agent` (txn_cap = 0.50 INR = 50 paise)
**Why this matters**: Mandate enforcement is authoritative. Behavioral ML cannot override it.

```bash
curl -X POST http://localhost:8000/v1/payouts \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"demo_policy_agent","request_id":"req_demo_2","idempotency_key":"demo_key_2","payee_id":"ven_test","category":"cloud","amount":10000,"provenance":{"source_type":"TRUSTED_TASK","source_id":"task_1","source_trust":"TRUSTED","payment_intent_origin":"AGENT_TOOL"}}'
```

Expected:
```json
{"decision": "BLOCK", "reason_codes": ["AMOUNT_EXCEEDS_TXN_CAP", ...]}
```

Razorpay is **not called**. Audit shows `razorpay.payout_not_created`.

---

### 2:30 — Demo 3: Behavioral Anomaly (FLAG)

**Agent**: `demo_behavior_agent` (no transaction history; cold-start)
**Why this matters**: Even a policy-authorized request can be flagged for unusual behavior.

```bash
curl -X POST http://localhost:8000/v1/payouts \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"demo_behavior_agent","request_id":"req_demo_3","idempotency_key":"demo_key_3","payee_id":"brand_new_vendor","category":"software","amount":450000,"provenance":{"source_type":"TRUSTED_TASK","source_id":"task_1","source_trust":"TRUSTED","payment_intent_origin":"AGENT_TOOL"}}'
```

Expected:
```json
{"decision": "FLAG", "reason_codes": ["AUTHORIZED", "BEHAVIOR_REVIEW_REQUIRED"], "anomaly_score": 0.7x}
```

---

### 3:15 — Demo 4: Provenance Anomaly (FLAG) — Critical Differentiator

**Agent**: `demo_provenance_agent`
**Why this matters**: This is the _core thesis_. A behaviorally normal agent, making a normal amount payment to a known vendor, gets **flagged** because the payment instruction came from untrusted external content.

```bash
curl -X POST http://localhost:8000/v1/payouts \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"demo_provenance_agent","request_id":"req_demo_4","idempotency_key":"demo_key_4","payee_id":"ven_test","category":"cloud","amount":1000,"provenance":{"source_type":"EXTERNAL_CONTENT","source_id":"scraped_email_123","source_trust":"UNTRUSTED","payment_intent_origin":"EXTERNAL_CONTENT"}}'
```

Expected:
```json
{"decision": "FLAG", "reason_codes": ["AUTHORIZED", "BEHAVIOR_LOW_RISK", "PROVENANCE_PAYMENT_INTENT_FROM_EXTERNAL_CONTENT", "PROVENANCE_UNTRUSTED_SOURCE"]}
```

This cannot be detected by a traditional fraud model — the amount, payee, and behavior are all normal.

---

### 4:00 — Demo 5: Idempotent Retry

Retry `demo_key_1` (the successful Demo 1 payout):

```bash
curl -X POST http://localhost:8000/v1/payouts \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"demo_normal_agent","request_id":"req_demo_1_retry","idempotency_key":"demo_key_1","payee_id":"<FUND_ACCOUNT_ID>","category":"cloud","amount":100,"provenance":{"source_type":"TRUSTED_TASK","source_id":"task_monthly_infra","source_trust":"TRUSTED","payment_intent_origin":"AGENT_TOOL"}}'
```

Expected:
```json
{"decision": "IDEMPOTENT_REPLAY", "status": "SUCCEEDED", "razorpay_payout_id": "pout_..."}
```

Razorpay payout count: **1** (not 2).

---

### 4:30 — Demo 6: Mandate Revocation

```bash
# Directly update DB: revoke demo_revocation_agent mandate
# Then send new payout request with idempotency_key demo_key_revoc

curl -X POST http://localhost:8000/v1/payouts \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"demo_revocation_agent","request_id":"req_demo_revoc","idempotency_key":"demo_key_revoc","payee_id":"ven_test","category":"cloud","amount":1000,"provenance":{"source_type":"TRUSTED_TASK","source_id":"task_1","source_trust":"TRUSTED","payment_intent_origin":"AGENT_TOOL"}}'
```

Expected (after revocation):
```json
{"decision": "BLOCK", "reason_codes": ["MANDATE_NOT_FOUND_OR_REVOKED"]}
```

No stale in-memory cache — policy always reads fresh from PostgreSQL.

---

### 4:45 — Demo 7: Audit Trail

Show `GET /v1/audit/demo_key_1`:

```json
{
  "events": [
    {"event_type": "governor.policy_evaluated", ...},
    {"event_type": "governor.behavior_evaluated", ...},
    {"event_type": "governor.provenance_evaluated", ...},
    {"event_type": "governor.decision_made", "decision": "ALLOW", ...},
    {"event_type": "razorpay.payout_created", "status": "SUCCEEDED", ...}
  ]
}
```

Then run the verifier:
```bash
python scripts/verify_audit_chain.py
# AUDIT CHAIN VALID (N events verified)
```

Tamper with the DB and re-run to demonstrate `AUDIT CHAIN INVALID`.

---

### 5:00 — Closing Thesis

> The Governor is not just a transaction anomaly detector.
> Traditional fraud models look at _what_ is being paid and _to whom_.
> The Governor also asks _who made the decision_ and _where did the instruction come from_.
>
> An autonomous AI agent receiving a spoofed payment instruction through external content
> can look completely normal from a transaction-features perspective.
> Only provenance-aware evaluation catches this class of attack.

---

## Security Notes

- Only RazorpayX **Test Mode** is used
- Credentials are loaded from `.env` — never hardcoded
- No live credentials appear in any demo output
- Audit trail is append-only and tamper-evident
