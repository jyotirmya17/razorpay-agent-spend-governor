# Phase 6 — Traceability & Subsystem Invariants Matrix
**Razorpay Agent Spend Governor**

This traceability matrix maps every adversarial test scenario across the governance subsystems and defines the exact measured statuses.

---

## Traceability Mapping

| Test ID | Input / Attack Vector | Target Subsystem | Expected Decision | Razorpay Call | DB Invariant | Audit Invariant | Measured Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A1** | Valid normal payout | Full Pipeline | ALLOW | YES (1 call) | Status = SUCCEEDED / PENDING | ALLOW event recorded | EXECUTED AND PASSED |
| **A2** | Test mode execution | RazorpayX Client | ALLOW | YES (1 call) | `razorpay_payout_id` stored | Execution result logged | EXECUTED AND PASSED |
| **A3** | State update check | Mandate / Ledger | ALLOW | YES (1 call) | Usage updated accurately | State transition logged | EXECUTED AND PASSED |
| **A4** | Audit lifecycle check | Audit Trail | ALLOW | YES (1 call) | Ledger & Txn aligned | SHA-256 chain updated | EXECUTED AND PASSED |
| **B1** | Revoked mandate payload | Mandate Engine | BLOCK | NO | Usage unchanged | `MANDATE_NOT_FOUND_OR_REVOKED` | EXECUTED AND PASSED |
| **B2** | Expired mandate payload | Mandate Engine | BLOCK | NO | Usage unchanged | `MANDATE_EXPIRED` logged | EXECUTED AND PASSED |
| **B3** | Amount > Txn cap | Mandate Engine | BLOCK | NO | Usage unchanged | `AMOUNT_EXCEEDS_TXN_CAP` logged | EXECUTED AND PASSED |
| **B4** | Cumulative daily > cap | Mandate Engine | BLOCK | NO | Daily usage unchanged | `DAILY_CAP_EXCEEDED` logged | EXECUTED AND PASSED |
| **B5** | Cumulative weekly > cap | Mandate Engine | BLOCK | NO | Weekly usage unchanged | `WEEKLY_CAP_EXCEEDED` logged | EXECUTED AND PASSED |
| **B6** | Disallowed category | Mandate Engine | BLOCK | NO | Usage unchanged | `CATEGORY_NOT_ALLOWED` logged | EXECUTED AND PASSED |
| **B7** | Unknown agent ID | Policy Engine | BLOCK | NO | No records created | `AGENT_UNKNOWN` logged | EXECUTED AND PASSED |
| **B8** | Inactive agent ID | Policy Engine | BLOCK | NO | No records created | `AGENT_REVOKED` logged | EXECUTED AND PASSED |
| **B9** | Blacklisted payee | Policy Engine | BLOCK | NO | No records created | `PAYEE_NOT_ALLOWED` logged | EXECUTED AND PASSED |
| **B10** | Policy fail + Anomaly | Policy & Risk Engine | BLOCK | NO | Precedence: BLOCK overrides | Policy & risk codes saved | EXECUTED AND PASSED |
| **C1** | High anomaly score (> 0.42) | Behavioral Model | FLAG | NO | Transaction NOT executed | `BEHAVIORAL_ANOMALY_HIGH_RISK` | EXECUTED AND PASSED |
| **C2** | Score = 0.419 (< 0.42) | Behavioral Model | ALLOW | YES (if policy pass) | Execution proceeds | Score logged < 0.42 | EXECUTED AND PASSED |
| **C3** | Score = 0.420 (>= 0.42) | Behavioral Model | FLAG | NO | Execution stopped | Score logged >= 0.42 | EXECUTED AND PASSED |
| **C4** | Out-of-range model output | Risk Orchestrator | FLAG | NO | Fail-safe FLAG enforced | `INVALID_MODEL_OUTPUT` | EXECUTED AND PASSED |
| **C5** | NaN model output | Risk Orchestrator | FLAG | NO | Fail-safe FLAG enforced | `INVALID_MODEL_OUTPUT` | EXECUTED AND PASSED |
| **C6** | Infinity model output | Risk Orchestrator | FLAG | NO | Fail-safe FLAG enforced | `INVALID_MODEL_OUTPUT` | EXECUTED AND PASSED |
| **C7** | Model uninitialized/absent | Risk Orchestrator | FLAG | NO | Fail-safe FLAG enforced | `MODEL_UNAVAILABLE` | EXECUTED AND PASSED |
| **C8** | Model exception during predict | Risk Orchestrator | FLAG | NO | Fail-safe FLAG enforced | `MODEL_EXCEPTION` | EXECUTED AND PASSED |
| **C9** | Large amount spike | Feature & Anomaly | FLAG | NO | Transaction NOT executed | High amount Z-score logged | EXECUTED AND PASSED |
| **C10** | Unseen payee ID | Feature & Anomaly | FLAG | NO | Transaction NOT executed | Novel payee feature flagged | EXECUTED AND PASSED |
| **C11** | High risk category | Policy / Feature | FLAG / BLOCK | NO | Transaction NOT executed | Anomaly / policy reason | EXECUTED AND PASSED |
| **C12** | Off-hours high value | Policy / Feature | FLAG | NO | Transaction NOT executed | Off-hours feature flagged | EXECUTED AND PASSED |
| **C13** | Rapid velocity burst | Feature & Anomaly | FLAG | NO | Transaction NOT executed | Velocity feature flagged | EXECUTED AND PASSED |
| **D1** | Valid signed provenance | Provenance Verifier | ALLOW | YES (if score < 0.42) | Provenance status = TRUSTED | Signature verified | EXECUTED AND PASSED |
| **D2** | Omitted provenance header | Provenance Verifier | FLAG | NO | Provenance = UNTRUSTED | `PROVENANCE_MISSING` | EXECUTED AND PASSED |
| **D3** | Source = UNKNOWN | Provenance Verifier | FLAG | NO | Provenance = UNTRUSTED | `PROVENANCE_UNKNOWN_SOURCE` | EXECUTED AND PASSED |
| **D4** | Source = UNTRUSTED | Provenance Verifier | FLAG | NO | Provenance = UNTRUSTED | `PROVENANCE_UNTRUSTED` | EXECUTED AND PASSED |
| **D5** | Intent from ext content | Provenance Verifier | FLAG | NO | Provenance = UNTRUSTED | `PROVENANCE_EXTERNAL_CONTENT` | EXECUTED AND PASSED |
| **D6** | Tampered signature | Provenance Verifier | FLAG | NO | Provenance = UNTRUSTED | `PROVENANCE_INVALID_SIGNATURE` | EXECUTED AND PASSED |
| **D7** | Timestamp > 300s old | Provenance Verifier | FLAG | NO | Provenance = UNTRUSTED | `PROVENANCE_EXPIRED_TIMESTAMP` | EXECUTED AND PASSED |
| **D8** | Payload hash modified | Provenance Verifier | FLAG | NO | Provenance = UNTRUSTED | `PROVENANCE_HASH_MISMATCH` | EXECUTED AND PASSED |
| **D9** | Untrusted prov + Anomaly | Provenance & Risk | FLAG | NO | Provenance = UNTRUSTED | Both reasons logged | EXECUTED AND PASSED |
| **E1** | Duplicate key + payload | Idempotency Engine | REPLAY | NO (second call) | 1 Transaction record | Idempotent replay logged | EXECUTED AND PASSED |
| **E2** | Duplicate key + diff payload | Idempotency Engine | REJECT (409) | NO | Original txn intact | Conflict error logged | EXECUTED AND PASSED |
| **E3** | Parallel identical requests | Idempotency Engine | REPLAY / LOCK | NO (second call) | 1 Payout created | Lock wait & replay | EXECUTED AND PASSED |
| **E4** | Parallel same-key requests | Idempotency Engine | REPLAY / LOCK | NO (second call) | 1 Reservation | Lock wait & replay | EXECUTED AND PASSED |
| **E5** | Replay after success | Idempotency Engine | REPLAY | NO (second call) | Existing payout ID returned | Cached result returned | EXECUTED AND PASSED |
| **E6** | Retry after failure | Idempotency Engine | FAILED / RE-EVAL | According to rule | Original failure status | Retry status logged | EXECUTED AND PASSED |
| **E7** | Retry after UNKNOWN | Idempotency Engine | UNKNOWN / RE-EVAL | NO unsafe retry | UNKNOWN status locked | Reconciliation state | EXECUTED AND PASSED |
| **F1** | Concurrent cap requests | Concurrency Engine | ALLOW / BLOCK | Single call | Spend <= cap | Cap enforcement logged | EXECUTED AND PASSED |
| **F2** | Concurrent daily cap | Concurrency Engine | ALLOW / BLOCK | Up to cap | Daily spend <= cap | Daily cap enforced | EXECUTED AND PASSED |
| **F3** | Concurrent weekly cap | Concurrency Engine | ALLOW / BLOCK | Up to cap | Weekly spend <= cap | Weekly cap enforced | EXECUTED AND PASSED |
| **F4** | Concurrent duplicates | Concurrency Engine | 1 ALLOW + REPLAYs | Single call | Single payout created | Replay logged | EXECUTED AND PASSED |
| **F5** | Concurrent diff requests | Concurrency Engine | Serialized | Gated calls | Monotonic usage | Lock serialization | EXECUTED AND PASSED |
| **F6** | Concurrent PG audit appends | Audit Trail (PG) | N/A | N/A | Strict monotonic sequence IDs | Single continuous chain | EXECUTED AND PASSED |
| **G1** | Razorpay HTTP 400 | RazorpayX Client | FAILED | 1 Call | Status = FAILED | Failure logged | EXECUTED AND PASSED |
| **G2** | Razorpay HTTP 422 | RazorpayX Client | FAILED | 1 Call | Status = FAILED | Failure logged | EXECUTED AND PASSED |
| **G3** | Razorpay HTTP 429 | RazorpayX Client | RETRY / FAILED | Gated retries | Retry logged | Rate limit logged | EXECUTED AND PASSED |
| **G4** | Repeated 429 exhaustion | RazorpayX Client | FAILED | Retries exhausted | Status = FAILED | Exhaustion logged | EXECUTED AND PASSED |
| **G5** | Razorpay HTTP 500 | RazorpayX Client | RETRY / FAILED | Gated retries | Retry logged | Server error logged | EXECUTED AND PASSED |
| **G6** | Repeated 5xx exhaustion | RazorpayX Client | FAILED | Retries exhausted | Status = FAILED | Exhaustion logged | EXECUTED AND PASSED |
| **G7** | Network exception | RazorpayX Client | UNKNOWN / FAILED | 1 Attempt | UNKNOWN / PENDING | Network error logged | EXECUTED AND PASSED |
| **G8** | Gateway timeout | RazorpayX Client | UNKNOWN | 1 Attempt | UNKNOWN (No auto duplicate) | Timeout logged | EXECUTED AND PASSED |
| **G9** | Missing payout ID in resp | RazorpayX Client | FAILED / UNKNOWN | 1 Attempt | FAILED / UNKNOWN | Malformed response logged | EXECUTED AND PASSED |
| **G10** | Malformed JSON response | RazorpayX Client | FAILED / UNKNOWN | 1 Attempt | FAILED / UNKNOWN | Parse error logged | EXECUTED AND PASSED |
| **H1** | `payout.queued` webhook | Webhook Engine | Processed | N/A | Status = QUEUED | Webhook logged | EXECUTED AND PASSED |
| **H2** | `payout.initiated` webhook | Webhook Engine | Processed | N/A | Status = INITIATED | Webhook logged | EXECUTED AND PASSED |
| **H3** | `payout.processed` webhook | Webhook Engine | Processed | N/A | Status = PROCESSED / SUCCEEDED | Webhook logged | EXECUTED AND PASSED |
| **H4** | `payout.reversed` webhook | Webhook Engine | Processed | N/A | Status = REVERSED | Reversal logged | EXECUTED AND PASSED |
| **H5** | `transaction.created` | Webhook Engine | Processed | N/A | Event recorded | Webhook logged | EXECUTED AND PASSED |
| **H6** | Duplicate webhook event | Webhook Engine | Ignored | N/A | Status unchanged | Duplicate ignored | EXECUTED AND PASSED |
| **H7** | Reordered webhooks | Webhook Engine | State protected | N/A | Highest status preserved | Out-of-order logged | EXECUTED AND PASSED |
| **H8** | Invalid HMAC signature | Webhook Engine | Rejected (401) | N/A | Status unchanged | Unauthorized logged | EXECUTED AND PASSED |
| **H9** | Unknown payout ID | Webhook Engine | Ignored (404/200) | N/A | Status unchanged | Unknown ID logged | EXECUTED AND PASSED |
| **H10** | Reference-ID Fallback | Query fallback | Status reconciled | Reference match logged | NOT EXECUTED |
| **I1** | Valid audit chain | Audit Verifier | Pass | N/A | Chain intact | `valid = True` | EXECUTED AND PASSED |
| **I2** | Modified event payload | Audit Verifier | Fail | N/A | Tampered payload | `valid = False` (Payload) | EXECUTED AND PASSED |
| **I3** | Modified previous hash | Audit Verifier | Fail | N/A | Tampered prev hash | `valid = False` (Prev hash) | EXECUTED AND PASSED |
| **I4** | Modified event hash | Audit Verifier | Fail | N/A | Tampered hash | `valid = False` (Hash) | EXECUTED AND PASSED |
| **I5** | Modified sequence ID | Audit Verifier | Fail | N/A | Sequence gap | `valid = False` (Sequence) | EXECUTED AND PASSED |
| **I6** | Deleted audit event | Audit Verifier | Fail | N/A | Chain broken | `valid = False` (Deleted) | EXECUTED AND PASSED |
| **I7** | Inserted audit event | Audit Verifier | Fail | N/A | Hash mismatch | `valid = False` (Inserted) | EXECUTED AND PASSED |
| **I8** | Duplicate sequence ID | Audit Verifier | Fail | N/A | Duplicate sequence | `valid = False` (Duplicate) | EXECUTED AND PASSED |
| **I9** | Concurrent PG appends | Audit Trail (PG) | Pass | N/A | Continuous sequence | `valid = True` | EXECUTED AND PASSED |
| **I10** | Corruption detail check | Audit Verifier | Fail | N/A | Specific index logged | `valid = False` | EXECUTED AND PASSED |
| **J1** | Negative amount (-100) | FastAPI Validation | Rejected (422) | NO | Database untouched | Request rejected | EXECUTED AND PASSED |
| **J2** | Zero amount (0) | FastAPI Validation | Rejected (422) | NO | Database untouched | Request rejected | EXECUTED AND PASSED |
| **J3** | Max int amount | Policy / Validation | BLOCK / 422 | NO | Database untouched | Request blocked/rejected | EXECUTED AND PASSED |
| **J4** | Currency = "XYZ" | FastAPI Validation | Rejected (422) | NO | Database untouched | Request rejected | EXECUTED AND PASSED |
| **J5** | Agent ID malformed | Policy Engine | BLOCK / 422 | NO | Database untouched | Agent unauthorized | EXECUTED AND PASSED |
| **J6** | Mandate ID malformed | Policy Engine | BLOCK / 422 | NO | Database untouched | Mandate invalid | EXECUTED AND PASSED |
| **J7** | Missing idempotency key | FastAPI Validation | Rejected (422) | NO | Database untouched | Request rejected | EXECUTED AND PASSED |
| **J8** | Long key (> 255 chars) | FastAPI Validation | Rejected (422) | NO | Database untouched | Request rejected | EXECUTED AND PASSED |
| **J9** | Extra payload fields | FastAPI Validation | Handled (200) | According to policy | Extra fields stripped | Request processed safely | EXECUTED AND PASSED |
| **J10** | Invalid ISO timestamp | FastAPI Validation | Rejected (422) | NO | Database untouched | Request rejected | EXECUTED AND PASSED |
| **J11** | SQLi string in payee | Policy Engine | BLOCK / ALLOW | NO / YES | Parameterized safely | No injection possible | EXECUTED AND PASSED |
| **J12** | XSS string in payee | Policy Engine | BLOCK / ALLOW | NO / YES | Escaped safely | No execution vector | EXECUTED AND PASSED |
| **J13** | Unicode in agent ID | Policy Engine | Handled / BLOCK | NO / YES | UTF-8 handled | Handled safely | EXECUTED AND PASSED |
| **J14** | Special chars in payee | Policy Engine | Handled / BLOCK | NO / YES | Escaped safely | Handled safely | EXECUTED AND PASSED |
| **J15** | Malformed JSON string | FastAPI Parsing | Rejected (400) | NO | Database untouched | JSON decode error | EXECUTED AND PASSED |
