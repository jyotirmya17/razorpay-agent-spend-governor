from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import math

@dataclass
class RiskConfig:
    flag_threshold: float = 0.42  # From Phase 4.4 validation
    block_threshold: Optional[float] = None
    behavioral_blocking_enabled: bool = False

def make_risk_decision(
    policy_allowed: bool,
    policy_reason: str,
    anomaly_score: Optional[float],
    model_version: Optional[str],
    config: RiskConfig = RiskConfig(),
    provenance_reasons: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Combined Risk Decision Engine — Phase 4.7.

    Decision precedence (strictly ordered):
      1. Policy violation          -> DENY  (authoritative; cannot be overridden)
      2. Model failure             -> REVIEW   (fail-safe; never ALLOW)
      3. Behavioral DENY (if enabled) -> DENY
      4. Behavioral REVIEW           -> REVIEW
      5. Provenance risk           -> REVIEW   (aggregated with any behavioral reasons)
      6. Otherwise                 -> ALLOW

    Reason codes from behavioral and provenance evaluation are always aggregated.
    Multiple REVIEW conditions all contribute their reason codes.
    Policy DENY is never downgraded by low behavioral/provenance risk.
    """
    now = datetime.now(timezone.utc).isoformat()
    provenance_reasons = provenance_reasons or []

    reasons: List[str] = [policy_reason]

    # 1. Deterministic Policy Violation -> DENY (cannot be downgraded)
    if not policy_allowed:
        return {
            "decision": "DENY",
            "reason_codes": reasons,
            "anomaly_score": anomaly_score,
            "model_version": model_version,
            "policy_result": policy_allowed,
            "timestamp": now,
        }

    # Policy passed. Evaluate behavioral risk.

    # 2. Invalid or missing behavioral score -> REVIEW (fail-safe; never ALLOW)
    if anomaly_score is None or not math.isfinite(anomaly_score) or anomaly_score < 0.0 or anomaly_score > 1.0:
        reasons.append("BEHAVIOR_EVALUATION_FAILED")
        reasons.extend(provenance_reasons)  # still aggregate provenance
        
        # Provenance risk alone -> DENY (overrides the REVIEW fail-safe)
        if provenance_reasons:
            return {
                "decision": "DENY",
                "reason_codes": reasons,
                "anomaly_score": anomaly_score,
                "model_version": model_version,
                "policy_result": policy_allowed,
                "timestamp": now,
            }
            
        return {
            "decision": "REVIEW",
            "reason_codes": reasons,
            "anomaly_score": anomaly_score,
            "model_version": model_version,
            "policy_result": policy_allowed,
            "timestamp": now,
        }

    # 3. Behavioral DENY (only if explicitly enabled and block_threshold set)
    if config.behavioral_blocking_enabled and config.block_threshold is not None:
        if anomaly_score >= config.block_threshold:
            reasons.append("BEHAVIOR_HIGH_RISK")
            reasons.extend(provenance_reasons)
            return {
                "decision": "DENY",
                "reason_codes": reasons,
                "anomaly_score": anomaly_score,
                "model_version": model_version,
                "policy_result": policy_allowed,
                "timestamp": now,
            }

    # 4. Behavioral REVIEW (DENYING disabled, but above DENY threshold -> REVIEW)
    if not config.behavioral_blocking_enabled and config.block_threshold is not None:
        if anomaly_score >= config.block_threshold:
            reasons.append("BEHAVIOR_HIGH_RISK")
            reasons.extend(provenance_reasons)
            return {
                "decision": "REVIEW",
                "reason_codes": reasons,
                "anomaly_score": anomaly_score,
                "model_version": model_version,
                "policy_result": policy_allowed,
                "timestamp": now,
            }

    # 5. Provenance risk -> DENY (authoritative over behavioral REVIEW)
    if provenance_reasons:
        if anomaly_score >= config.flag_threshold:
            reasons.append("BEHAVIOR_REVIEW_REQUIRED")
        else:
            reasons.append("BEHAVIOR_LOW_RISK")
        reasons.extend(provenance_reasons)
        return {
            "decision": "DENY",
            "reason_codes": reasons,
            "anomaly_score": anomaly_score,
            "model_version": model_version,
            "policy_result": policy_allowed,
            "timestamp": now,
        }

    # 6. Behavioral REVIEW (above REVIEW threshold)
    if anomaly_score >= config.flag_threshold:
        reasons.append("BEHAVIOR_REVIEW_REQUIRED")
        return {
            "decision": "REVIEW",
            "reason_codes": reasons,
            "anomaly_score": anomaly_score,
            "model_version": model_version,
            "policy_result": policy_allowed,
            "timestamp": now,
        }

    # 7. All clear -> ALLOW
    reasons.append("BEHAVIOR_LOW_RISK")
    return {
        "decision": "ALLOW",
        "reason_codes": reasons,
        "anomaly_score": anomaly_score,
        "model_version": model_version,
        "policy_result": policy_allowed,
        "timestamp": now,
    }
