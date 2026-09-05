# Phase 6 — Test Matrix & Defense Specifications
**Razorpay Agent Spend Governor**

This document establishes the comprehensive Phase 6 test matrix for adversarial end-to-end validation, failure injection, and reliability hardening.

---

## Matrix Categories & Measured Coverage Specifications

### Category A: Normal Flow & Execution
| Test ID | Scenario | Expected Decision | Razorpay Call | DB Invariant | Execution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A1** | Normal Authorized Payout | ALLOW | YES (1 call) | Status = SUCCEEDED / PENDING | EXECUTED AND PASSED |
| **A2** | Successful RazorpayX Test Mode Execution | ALLOW | YES (1 call) | `razorpay_payout_id` stored | EXECUTED AND PASSED |
| **A3** | Local State Update Accuracy | ALLOW | YES (1 call) | Usage updated, transaction recorded | EXECUTED AND PASSED |
| **A4** | Audit Lifecycle Recording | ALLOW | YES (1 call) | Genesis -> Event SHA-256 chain | EXECUTED AND PASSED |

### Category B: Policy Engine Defense
| Test ID | Scenario | Expected Decision | Razorpay Call | DB Invariant | Execution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **B1** | Revoked Mandate | BLOCK | NO | Transaction NOT created / BLOCKED | EXECUTED AND PASSED |
| **B2** | Expired Mandate | BLOCK | NO | Transaction NOT created / BLOCKED | EXECUTED AND PASSED |
| **B3** | Transaction Cap Exceeded | BLOCK | NO | Transaction NOT created / BLOCKED | EXECUTED AND PASSED |
| **B4** | Daily Cap Exceeded | BLOCK | NO | Usage unchanged | EXECUTED AND PASSED |
| **B5** | Weekly Cap Exceeded | BLOCK | NO | Usage unchanged | EXECUTED AND PASSED |
| **B6** | Disallowed Category | BLOCK | NO | Transaction NOT created / BLOCKED | EXECUTED AND PASSED |
| **B7** | Unauthorized Agent | BLOCK | NO | Transaction NOT created / BLOCKED | EXECUTED AND PASSED |
| **B8** | Inactive Agent | BLOCK | NO | Transaction NOT created / BLOCKED | EXECUTED AND PASSED |
| **B9** | Blacklisted Payee | BLOCK | NO | Transaction NOT created / BLOCKED | EXECUTED AND PASSED |
| **B10** | Policy Violation + Anomaly | BLOCK | NO | Precedence: Policy BLOCK overrides | EXECUTED AND PASSED |

### Category C: Behavioral Anomaly Defense
| Test ID | Scenario | Expected Decision | Razorpay Call | DB Invariant | Execution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **C1** | High Anomaly Score (> 0.42) | FLAG | NO | Execution stopped | EXECUTED AND PASSED |
| **C2** | Score Just Below Threshold (0.419) | ALLOW | YES (if policy passes) | Execution proceeds | EXECUTED AND PASSED |
| **C3** | Score Exactly at Threshold (0.420) | FLAG | NO | Score >= 0.42 triggers FLAG | EXECUTED AND PASSED |
| **C4** | Invalid Model Output (Out of range) | FLAG | NO | Fail-safe FLAG enforced | EXECUTED AND PASSED |
| **C5** | NaN Anomaly Score | FLAG | NO | Fail-safe FLAG enforced | EXECUTED AND PASSED |
| **C6** | Infinity Anomaly Score | FLAG | NO | Fail-safe FLAG enforced | EXECUTED AND PASSED |
| **C7** | Anomaly Model Unavailable | FLAG | NO | Fail-safe FLAG enforced | EXECUTED AND PASSED |
| **C8** | Model Exception During Predict | FLAG | NO | Fail-safe FLAG enforced | EXECUTED AND PASSED |
| **C9** | Unusual Amount (High Z-Score) | FLAG | NO | Execution stopped | EXECUTED AND PASSED |
| **C10** | Unusual Payee (Novel Payee) | FLAG | NO | Execution stopped | EXECUTED AND PASSED |
| **C11** | Unusual Category | FLAG / BLOCK | NO | Execution stopped | EXECUTED AND PASSED |
| **C12** | Unusual Time (Off-hours) | FLAG | NO | Execution stopped | EXECUTED AND PASSED |
| **C13** | Velocity Burst | FLAG | NO | Execution stopped | EXECUTED AND PASSED |

### Category D: Provenance Defense
| Test ID | Scenario | Expected Decision | Razorpay Call | DB Invariant | Execution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **D1** | Valid Trusted Provenance | ALLOW (if score < 0.42) | YES | Provenance status = TRUSTED | EXECUTED AND PASSED |
| **D2** | Missing Provenance | FLAG | NO | Provenance status = UNTRUSTED | EXECUTED AND PASSED |
| **D3** | UNKNOWN Provenance Source | FLAG | NO | Provenance status = UNTRUSTED | EXECUTED AND PASSED |
| **D4** | UNTRUSTED Source (External) | FLAG | NO | Provenance status = UNTRUSTED | EXECUTED AND PASSED |
| **D5** | Payment Intent from Ext. Content | FLAG | NO | Provenance status = UNTRUSTED | EXECUTED AND PASSED |
| **D6** | Invalid Signature | FLAG | NO | Signature verification failed | EXECUTED AND PASSED |
| **D7** | Expired Timestamp (> 300s) | FLAG | NO | Timestamp freshness failed | EXECUTED AND PASSED |
| **D8** | Payload Hash Mismatch | FLAG | NO | SHA-256 payload mismatch | EXECUTED AND PASSED |
| **D9** | Provenance + Behavioral Anomaly | FLAG | NO | Aggregated risk reasons | EXECUTED AND PASSED |

### Category E: Idempotency Controls
| Test ID | Scenario | Expected Decision | Razorpay Call | DB Invariant | Execution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **E1** | Same Key + Same Payload | REPLAY | NO (returns cached) | Single transaction record | EXECUTED AND PASSED |
| **E2** | Same Key + Modified Payload | REJECT / 409 | NO | Conflict error returned | EXECUTED AND PASSED |
| **E3** | Concurrent Identical Requests | REPLAY / WAIT | NO second call | Exactly 1 logical payout | EXECUTED AND PASSED |
| **E4** | Concurrent Same-Key Requests | REPLAY / WAIT | NO second call | Single reservation | EXECUTED AND PASSED |
| **E5** | Retry After Successful Execution | REPLAY | NO second call | Returns existing `razorpay_payout_id` | EXECUTED AND PASSED |
| **E6** | Retry After Known Failure | RE-EVALUATE / FAILED | According to rules | Existing failure status | EXECUTED AND PASSED |
| **E7** | Retry After UNKNOWN State | RE-EVALUATE / LOCK | NO unsafe duplicate | Reconciliation state retained | EXECUTED AND PASSED |

### Category F: Concurrency Controls (PostgreSQL Verified)
| Test ID | Scenario | Expected Decision | Razorpay Call | DB Invariant | Execution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F1** | Simultaneous Txn-Cap Requests | ALLOW / BLOCK | Single call | Total spend <= cap | EXECUTED AND PASSED |
| **F2** | Simultaneous Daily-Cap Requests | ALLOW / BLOCK | Up to daily cap | Daily sum <= cap | EXECUTED AND PASSED |
| **F3** | Simultaneous Weekly-Cap Requests | ALLOW / BLOCK | Up to weekly cap | Weekly sum <= cap | EXECUTED AND PASSED |
| **F4** | Simultaneous Duplicate Requests | 1 ALLOW + REPLAYs | Single call | Single payout created | EXECUTED AND PASSED |
| **F5** | Simultaneous Different Requests | Serialized evaluation | Gated calls | Database usage monotonic | EXECUTED AND PASSED |
| **F6** | Concurrent Audit Appends (PG) | N/A | N/A | Monotonic sequence IDs | EXECUTED AND PASSED |

### Category G: Razorpay Failure Injection
| Test ID | Scenario | Expected Outcome | Execution Status | Retry Behavior | Execution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **G1** | HTTP 400 (Bad Request) | FAILED | FAILED | No retry | EXECUTED AND PASSED |
| **G2** | HTTP 422 (Unprocessable) | FAILED | FAILED | No retry | EXECUTED AND PASSED |
| **G3** | HTTP 429 (Rate Limit) | RETRY / FAILED | PENDING / FAILED | Backoff retry up to limit | EXECUTED AND PASSED |
| **G4** | Repeated 429 Exhaustion | FAILED | FAILED | Retries exhausted | EXECUTED AND PASSED |
| **G5** | HTTP 500 (Server Error) | RETRY / FAILED | PENDING / FAILED | Retry up to limit | EXECUTED AND PASSED |
| **G6** | Repeated 5xx Exhaustion | FAILED | FAILED | Retries exhausted | EXECUTED AND PASSED |
| **G7** | Network Exception | UNKNOWN / FAILED | UNKNOWN / PENDING | Safety lock retained | EXECUTED AND PASSED |
| **G8** | Gateway Timeout | UNKNOWN | UNKNOWN | Safety lock (No auto duplicate) | EXECUTED AND PASSED |
| **G9** | Missing Payout ID Response | FAILED / UNKNOWN | FAILED / UNKNOWN | Malformed response handling | EXECUTED AND PASSED |
| **G10** | Malformed JSON Response | FAILED / UNKNOWN | FAILED / UNKNOWN | Parse error handling | EXECUTED AND PASSED |

### Category H: Webhook & Reconciliation
| Test ID | Scenario | Expected Outcome | Transaction Status | Audit Trail | Execution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **H1** | `payout.queued` Webhook | Processed | QUEUED / PROCESSING | Webhook event logged | EXECUTED AND PASSED |
| **H2** | `payout.initiated` Webhook | Processed | INITIATED / PROCESSING | Webhook event logged | EXECUTED AND PASSED |
| **H3** | `payout.processed` Webhook | Processed | PROCESSED / SUCCEEDED | Webhook event logged | EXECUTED AND PASSED |
| **H4** | `payout.reversed` Webhook | Processed | REVERSED | Reversal logged | EXECUTED AND PASSED |
| **H5** | `transaction.created` Webhook | Processed | RECORDED | Webhook event logged | EXECUTED AND PASSED |
| **H6** | Duplicate Webhook | Idempotent Ignore | Unchanged | Duplicate event logged | EXECUTED AND PASSED |
| **H7** | Reordered Webhooks | Terminal Protection | Highest state preserved | Reordering handled | EXECUTED AND PASSED |
| **H8** | Invalid HMAC Signature | Rejected (401) | Unchanged | Unauthorized signature | EXECUTED AND PASSED |
| **H9** | Unknown Payout ID | Ignored / Logged | Unchanged | Unknown payout ID logged | EXECUTED AND PASSED |
| **H10** | Reference-ID Fallback | Query fallback | Status reconciled | Reference match logged | NOT EXECUTED |

### Category I: Cryptographic Audit Security
| Test ID | Scenario | Expected Outcome | Verifier Result | Chain Integrity | Execution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **I1** | Valid Audit Chain | Pass | `valid = True` | Chain intact | EXECUTED AND PASSED |
| **I2** | Modified Event Payload | Fail | `valid = False` | Tamper detected (Payload mismatch) | EXECUTED AND PASSED |
| **I3** | Modified Previous Hash | Fail | `valid = False` | Tamper detected (Prev hash mismatch) | EXECUTED AND PASSED |
| **I4** | Modified Event Hash | Fail | `valid = False` | Tamper detected (Hash mismatch) | EXECUTED AND PASSED |
| **I5** | Modified Sequence ID | Fail | `valid = False` | Tamper detected (Sequence broken) | EXECUTED AND PASSED |
| **I6** | Deleted Event | Fail | `valid = False` | Tamper detected (Chain gap) | EXECUTED AND PASSED |
| **I7** | Inserted Event | Fail | `valid = False` | Tamper detected (Hash mismatch) | EXECUTED AND PASSED |
| **I8** | Duplicate Sequence ID | Fail | `valid = False` | Tamper detected (Duplicate sequence) | EXECUTED AND PASSED |
| **I9** | Concurrent PG Appends | Pass | `valid = True` | Serialized sequence & hashes | EXECUTED AND PASSED |
| **I10** | Corruption Detail Check | Fail | `valid = False` | Specific index logged | EXECUTED AND PASSED |

### Category J: Input Security & Boundary Defense
| Test ID | Scenario | Expected Outcome | HTTP Status | Validation Error | Execution Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **J1** | Negative Amount | Rejected | 422 | Amount must be positive | EXECUTED AND PASSED |
| **J2** | Zero Amount | Rejected | 422 | Amount must be > 0 | EXECUTED AND PASSED |
| **J3** | Extremely Large Amount | Blocked / Rejected | 200 (BLOCK) / 422 | Exceeds max cap | EXECUTED AND PASSED |
| **J4** | Malformed Currency | Rejected / Handled | 422 / 200 | Currency validation | EXECUTED AND PASSED |
| **J5** | Malformed Agent ID | Rejected / Blocked | 422 / 200 (BLOCK) | Agent validation | EXECUTED AND PASSED |
| **J6** | Malformed Mandate ID | Rejected / Blocked | 422 / 200 (BLOCK) | Mandate validation | EXECUTED AND PASSED |
| **J7** | Empty / Missing Key | Rejected | 422 | Key required | EXECUTED AND PASSED |
| **J8** | Extremely Long Key (> 255) | Handled / Rejected | 200 / 422 | Key length handling | EXECUTED AND PASSED |
| **J9** | Unexpected Payload Fields | Handled | 200 | Extra fields stripped | EXECUTED AND PASSED |
| **J10** | Malformed Timestamp | Rejected | 422 | ISO 8601 validation | EXECUTED AND PASSED |
| **J11** | SQL-Injection Input Strings | Handled Safely | 200 | Parameterized safely | EXECUTED AND PASSED |
| **J12** | XSS-like Input Strings | Handled Safely | 200 | Escaped safely | EXECUTED AND PASSED |
| **J13** | Unicode Identifiers | Handled | 200 | UTF-8 parsed | EXECUTED AND PASSED |
| **J14** | Special Character Identifiers | Handled | 200 | Escaped safely | EXECUTED AND PASSED |
| **J15** | Malformed JSON Payload | Rejected | 400 | JSON decode error | EXECUTED AND PASSED |
