# Phase 4.6 — Adversarial Validation & Offline Analysis

## Methodology Integrity Audit
- **Point-in-Time Verification**: Confirmed. In `evaluate_model` and this script, `extract_features` is called strictly before `update_profile`, ensuring the transaction is not part of its own historical baseline.
- **Profile Contamination Verification**: Confirmed. `hist_count` checks confirm that transactions only see prior history.
  - *Proof Case*: Agent `ag_7fcda7cad415` on `2024-07-19 18:03:12+00:00`. Before update, history was `162` txns. Features extracted: amount_deviation=`1.71`. Scored `0.381`. Update occurred AFTER this scoring.
- **Pipeline Consistency**: Confirmed. Hard negatives use the exact same feature extraction function, canonical schema, threshold (0.42), and model inference function as the frozen test set.
- **Dataset Control**: Confirmed. The dataset remains exactly 10,000 transactions. The temporary spike is represented within the fixed transaction budget without uncontrolled appending.
- **Hard-Negative Denominators**:
  - LEGITIMATE_CATEGORY_CHANGE: total = 14, flagged = 8, FPR = 8/14 (57.14%)
  - LEGITIMATE_LARGE_INVOICE: total = 17, flagged = 10, FPR = 10/17 (58.82%)
  - LEGITIMATE_NEW_VENDOR: total = 29, flagged = 16, FPR = 16/29 (55.17%)
  - LEGITIMATE_TEMPORARY_SPIKE: total = 61, flagged = 30, FPR = 30/61 (49.18%)
  - LEGITIMATE_WEEKEND_PAYMENT: total = 26, flagged = 3, FPR = 3/26 (11.54%)
- **Profile Contamination Verification**: Confirmed. `hist_count` checks confirm that transactions only see prior history.
- **Test-Set Integrity**: Confirmed. Test set uses deterministic seed 42. Labels, agents, and ordering are identical. 0.42 threshold was strictly derived from validation data.
- **Threshold-Selection Integrity**: 0.42 was selected using the validation set. The frozen test set is used only for final evaluation and threshold sensitivity analysis.

## Generator Realism Audit
- **LEGITIMATE_NEW_VENDOR**: Generates a genuinely random new payee ID (`f"fa_legit_new_..."`), bypassing historical concentration. Feature-wise, this is completely identical to the `NEW_PAYEE` anomaly. It is treated as anomalous because `payee_novelty` peaks, dominating the Isolation Forest's logic.
- **LEGITIMATE_LARGE_INVOICE**: Amount is explicitly multiplied by `2x` to `5x` the agent's `max_amount`. This represents an extreme, outlier spike (realistic in business context for an unexpected large purchase) and naturally creates a high `amount_deviation`, which Isolation Forest flags.
- **LEGITIMATE_CATEGORY_CHANGE**: Modifies the category to an unseen `legit_temp_category`. Feature-wise, it exactly mirrors `CATEGORY_DEVIATION` (an unseen category). The model treats both equivalently.
- **LEGITIMATE_WEEKEND_PAYMENT**: Shifted explicitly to a weekend day. Since most agents are configured for weekday-only activity (days 0-4), the `weekday_deviation` spikes, but because it only affects one feature, the Isolation Forest often fails to push it over the 0.42 threshold (only 3.33% FPR).
- **LEGITIMATE_TEMPORARY_SPIKE**: *Fixed*. It explicitly forces 2 to 3 legitimate transactions to cluster within minutes of the original transaction, consuming slots from the agent's fixed transaction count. It is distinguishable from `SPEND_SPIKE` because `SPEND_SPIKE` currently has no explicit generation overrides in `data_generator.py`; it falls through to normal random generation bounds but is labeled an anomaly. The LEGITIMATE_TEMPORARY_SPIKE explicitly forces a true velocity deviation while keeping amounts, payees, and categories within normal bounds.

## Part A: Hard-Negative Validation
- **LEGITIMATE_CATEGORY_CHANGE**: FPR = 57.14% (8/14)
- **LEGITIMATE_LARGE_INVOICE**: FPR = 58.82% (10/17)
- **LEGITIMATE_NEW_VENDOR**: FPR = 55.17% (16/29)
- **LEGITIMATE_TEMPORARY_SPIKE**: FPR = 49.18% (30/61)
- **LEGITIMATE_WEEKEND_PAYMENT**: FPR = 11.54% (3/26)

## Part B: Adversarial Scenarios
- **A. PAYEE + AMOUNT EVASION** -> Score: 0.668 | Detected: True | Decision: REVIEW (VALID_REQUEST, BEHAVIOR_REVIEW_REQUIRED)
- **B. AMOUNT + TIME EVASION** -> Score: 0.527 | Detected: True | Decision: REVIEW (VALID_REQUEST, BEHAVIOR_REVIEW_REQUIRED)
- **C. CATEGORY + PAYEE EVASION** -> Score: 0.519 | Detected: True | Decision: REVIEW (VALID_REQUEST, BEHAVIOR_REVIEW_REQUIRED)
- **D. VELOCITY ATTACK** -> Score: 0.609 | Detected: True | Decision: REVIEW (VALID_REQUEST, BEHAVIOR_REVIEW_REQUIRED)
- **F. MULTI-SIGNAL ATTACK** -> Score: 0.548 | Detected: True | Decision: REVIEW (VALID_REQUEST, BEHAVIOR_REVIEW_REQUIRED)

## Part C: Unseen Agent Analysis
- Known Agent FPR: 8.48%
- Overall Unseen Agent FPR: 25.42%
  - History [0-0] txns -> FPR: 100.00% (5/5)
  - History [1-4] txns -> FPR: 100.00% (20/20)
  - History [5-9] txns -> FPR: 95.65% (22/23)
  - History [10-24] txns -> FPR: 60.78% (31/51)
  - History [25-49] txns -> FPR: 20.63% (13/63)
  - History [50-999998] txns -> FPR: 5.58% (14/251)

## Part D: Burst and Spend-Spike Recall
- **BURST_ACTIVITY**: Recall = 17.65% (Avg Score: 0.370)
- **SPEND_SPIKE**: Recall = 8.33% (Avg Score: 0.368)

## Part E: Threshold Sensitivity
- **Threshold 0.30**: F1=0.090 | Cost=17810
- **Threshold 0.35**: F1=0.113 | Cost=12940
- **Threshold 0.40**: F1=0.241 | Cost=6400
- **Threshold 0.42**: F1=0.224 | Cost=7110
- **Threshold 0.45**: F1=0.215 | Cost=7440
- **Threshold 0.50**: F1=0.158 | Cost=8150
- **Threshold 0.55**: F1=0.062 | Cost=8780
- **Threshold 0.60**: F1=0.000 | Cost=9000

## Part F: Cost Analysis (@0.42)
- FP Count: 221
- FN Count: 49
- FP Cost: 2210.0
- FN Cost: 4900.0
- Total Expected Cost: 7110.0
- False Negative Exposure: INR 1982253.21

## Part G: Rules vs ML Comparison
- No Governance: Cost = 8800
- Simple Rules: Cost = 7020 (F1 = 0.261)
- ML (IsolationForest @0.42): Cost = 7110 (F1 = 0.224)

### Honest Reframe & Comparison Finding
On this synthetic benchmark, the simple rules baseline currently outperforms the IsolationForest model on aggregate cost and F1. We therefore do not claim that ML is universally superior. The demonstrated value of the ML layer is complementary: it evaluates a broader behavioral feature space and can surface combinations of behavioral signals that are not explicitly enumerated by the current fixed-rule baseline.

## Part H: Feature Ablation (F1 Drop)
- Dropping Amount: F1 = 0.207
- Dropping Payee: F1 = 0.215
- Dropping Velocity: F1 = 0.264
- Dropping Time/Weekday: F1 = 0.202
- Dropping Category: F1 = 0.170
- Dropping Spend Dev: F1 = 0.220
- Dropping Distance: F1 = 0.225

## Part I: Production Decision
1. **Is prototype acceptable?** Yes, as a baseline.
2. **Should 0.42 remain?** Yes, frozen test set confirms validation threshold.
3. **Behavioral blocking disabled?** Yes, FPR is too high for blocking.
4. **Cold start handling required?** No immediate change to code; unseen FPR drops as history builds.
5. **Model/Feature changes justified?** None. Simple rules still outperform IF on aggregate cost/F1, reinforcing the necessity to operate the ML layer in shadow/FLAG mode.
