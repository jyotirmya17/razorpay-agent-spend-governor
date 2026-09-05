# Agent Spend Governor — Architecture (Phase 4.7)

## System Overview

The Agent Spend Governor is a defense layer between autonomous AI agents and RazorpayX payouts.

> **Core Thesis**: "An authorized transaction can still be risky if the agent'\''s behavior changes or the payment decision originated from untrusted content."

---

## Decision Pipeline

```
Incoming Payout Intent
        |
        v
POST /v1/payouts  (single orchestration entry point)
        |
        v
Policy + Idempotency Check
        |
        +--- violation --> BLOCK (authoritative; stops here)
        |
        v
Point-in-Time Behavioral Profile
(historical transactions strictly before T)
        |
        v
Feature Extraction (12 canonical features)
        |
        v
IsolationForest Behavioral Model
        |
        v
Provenance Evaluation
(source_type, source_trust, payment_intent_origin)
        |
        v
Risk Decision Engine
        |
        +--- BLOCK --> Stop (policy violation only)
        |
        +--- FLAG  --> Hold / Review state
        |             (no Razorpay call; structurally prevented)
        |
        +--- ALLOW --> ExecutionService
                              |
                              v
                        RazorpayX Test Mode
                              |
                              v
                           Audit Trail
```

---

## Decision Precedence

Strictly ordered; each level cannot override a higher level:

1. **Policy violation** → `BLOCK` (authoritative; mandate checks)
2. **Model failure** (None / NaN / inf) → `FLAG` (fail-safe; never ALLOW)
3. **Behavioral block** (disabled in Phase 4.6) → N/A
4. **Behavioral FLAG** (score ≥ 0.42) → `FLAG`
5. **Provenance FLAG** (UNTRUSTED or UNKNOWN) → `FLAG`
6. **Otherwise** → `ALLOW`

Reason codes from behavioral and provenance evaluation are **always aggregated**. A transaction that is both behaviorally anomalous and from an untrusted source will carry both reason codes.

---

## Components

### 1. Policy Engine (`policy/engine.py`)
- Mandate existence, status, expiry
- Per-transaction cap, daily cap, weekly cap
- Category and payee allowlists
- Idempotency check (conflict detection, stale-pending handling)
- Uses PostgreSQL `SELECT ... FOR UPDATE` for concurrency-safe usage tracking

### 2. Idempotency (`policy/idempotency.py`)
- Same key + same payload → `IDEMPOTENT_REPLAY`
- Same key + different payload → `IDEMPOTENCY_KEY_CONFLICT` (HTTP 409)
- Stale PENDING records → reuse slot
- UNKNOWN_IN_PROGRESS → bounded wait, not automatic failure

### 3. Behavioral Risk (`gateway/risk/`)
- **Profiles** (`profiles.py`): incremental agent behavioral profiles built in temporal order
- **Features** (`features.py`): 12 canonical point-in-time features
- **Model** (`anomaly_model.py`): `IsolationForest(n_estimators=100, contamination="auto", random_state=42)` — version `behavioral_iforest_v1`
- **Orchestrator** (`orchestrator.py`): wires profile → features → model → provenance → decision

### 4. Provenance (`gateway/risk/provenance.py`)
- Source types: `TRUSTED_TASK`, `TRUSTED_SYSTEM`, `INTERNAL_TOOL`, `EXTERNAL_CONTENT`, `USER_INPUT`
- Trust levels: `TRUSTED` (no penalty), `UNTRUSTED` (FLAG), `UNKNOWN` (FLAG)
- Missing provenance defaults to `UNKNOWN` — **never implicitly TRUSTED**
- Reason codes: `PROVENANCE_UNTRUSTED_SOURCE`, `PROVENANCE_UNKNOWN_SOURCE`, `PROVENANCE_PAYMENT_INTENT_FROM_EXTERNAL_CONTENT`

### 5. Decision Engine (`gateway/risk/decision.py`)
- Accepts: policy result, behavioral score, provenance reasons
- Outputs: `ALLOW`, `FLAG`, or `BLOCK` with aggregated reason codes
- NaN / inf behavioral score → `FLAG` via `math.isfinite()` fail-safe (never ALLOW)

### 6. Execution State Machine (`execution/service.py`)
- States: `AUTHORIZED → EXECUTING → SUCCEEDED | FAILED | UNKNOWN`
- `UNKNOWN` retains reserved spend (safe for later reconciliation)
- Reconciliation via webhook or manual call

### 7. Audit Trail (`gateway/core/audit.py`)
- Append-only, tamper-evident hash chain
- Each event: `event_id (UUID)`, `sequence_id (PK, monotonic)`, `event_type`, `entity_id`, `payload`, `previous_event_hash`, `event_hash`
- Hash: `SHA256(previous_event_hash || canonical_payload)`
- Chain ordering: strictly by `sequence_id`, not timestamp
- Concurrency: `pg_advisory_xact_lock` acquires a transaction-scoped exclusive advisory lock
  before reading the chain tail — serializes concurrent appends even when the table is empty
  (the critical case that `SELECT ... FOR UPDATE` cannot handle: it locks zero rows)
- Advisory lock is automatically released on commit or rollback
- Audit-chain lock is never held across external Razorpay calls

### 8. Webhooks (`gateway/api/webhooks.py`)
- HMAC-SHA256 signature verification
- Event deduplication by Razorpay event ID
- Payout ID as primary correlation; reference ID as fallback
- Terminal state safety (SUCCEEDED/FAILED are idempotent)

---

## Failure Paths

| Condition | Result |
|-----------|--------|
| Policy violation | BLOCK, transaction stays AUTHORIZED, audit logged |
| Model failure (exception) | FLAG, `BEHAVIOR_EVALUATION_FAILED`, no Razorpay call |
| Untrusted provenance | FLAG, `PROVENANCE_UNTRUSTED_SOURCE`, no Razorpay call |
| Missing provenance | FLAG, `PROVENANCE_UNKNOWN_SOURCE`, no Razorpay call |
| Razorpay timeout | UNKNOWN, spend reserved, reconcile later |
| Razorpay explicit failure | FAILED, spend released |
| Idempotency conflict | HTTP 409, `IDEMPOTENCY_KEY_CONFLICT` |
| Stale PENDING | Retry allowed after bounded wait |

---

- IsolationForest **does not outperform** the Simple Rules baseline on expected cost (`7950` vs. `6890`) or F1 score (`0.214` vs. `0.338`)
- Known-agent FPR = `8.59%`; Unseen-agent FPR = `28.83%`
- Hard-negative FPRs: `LEGITIMATE_LARGE_INVOICE` = `78.95%`, `LEGITIMATE_NEW_VENDOR` = `60.00%`
- **Behavioral blocking is DISABLED** due to high legitimate-activity FPR
- Behavioral ML is used as a FLAG/REVIEW signal only
- Evaluation is on a synthetic dataset (seed=42); not real production data

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/payouts` | Single orchestration entry point |
| GET | `/v1/transactions/{id}` | Transaction state |
| GET | `/v1/agents/{id}` | Agent information |
| GET | `/v1/audit/{transaction_id}` | Tamper-evident audit timeline |
| GET | `/v1/risk/{transaction_id}` | Risk summary and provenance |
| POST | `/v1/webhooks/razorpay` | Razorpay webhook handler |
