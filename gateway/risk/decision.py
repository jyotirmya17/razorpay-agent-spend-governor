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
    config: RiskConfig = RiskConfig()
) -> Dict[str, Any]:
    """
    Combined Risk Decision Engine.
    Integrates deterministic policy with behavioral risk scores.
    """
    now = datetime.now(timezone.utc).isoformat()
    
    reasons: List[str] = [policy_reason]
    
    # 1. Deterministic Policy Violation -> BLOCK
    if not policy_allowed:
        return {
            "decision": "BLOCK",
            "reason_codes": reasons,
            "anomaly_score": anomaly_score,
            "model_version": model_version,
            "policy_result": policy_allowed,
            "timestamp": now
        }
        
    # Policy is ALLOW. Evaluate behavioral risk.
    
    # 2. Invalid or missing behavioral score -> FLAG (Fail-safe)
    if anomaly_score is None or not math.isfinite(anomaly_score) or anomaly_score < 0.0 or anomaly_score > 1.0:
        reasons.append("BEHAVIOR_EVALUATION_FAILED")
        return {
            "decision": "FLAG",
            "reason_codes": reasons,
            "anomaly_score": anomaly_score,
            "model_version": model_version,
            "policy_result": policy_allowed,
            "timestamp": now
        }
        
    # 3. Behavioral Block (if enabled and threshold set)
    if config.behavioral_blocking_enabled and config.block_threshold is not None:
        if anomaly_score >= config.block_threshold:
            reasons.append("BEHAVIOR_HIGH_RISK")
            return {
                "decision": "BLOCK",
                "reason_codes": reasons,
                "anomaly_score": anomaly_score,
                "model_version": model_version,
                "policy_result": policy_allowed,
                "timestamp": now
            }
            
    # 4. Behavioral Flag (Disabled blocking, but above block threshold)
    if not config.behavioral_blocking_enabled and config.block_threshold is not None:
        if anomaly_score >= config.block_threshold:
            reasons.append("BEHAVIOR_HIGH_RISK")
            return {
                "decision": "FLAG",
                "reason_codes": reasons,
                "anomaly_score": anomaly_score,
                "model_version": model_version,
                "policy_result": policy_allowed,
                "timestamp": now
            }
            
    # 5. Behavioral Flag (Above flag threshold)
    if anomaly_score >= config.flag_threshold:
        reasons.append("BEHAVIOR_REVIEW_REQUIRED")
        return {
            "decision": "FLAG",
            "reason_codes": reasons,
            "anomaly_score": anomaly_score,
            "model_version": model_version,
            "policy_result": policy_allowed,
            "timestamp": now
        }
        
    # 6. Low Behavioral Risk -> ALLOW
    reasons.append("BEHAVIOR_LOW_RISK")
    return {
        "decision": "ALLOW",
        "reason_codes": reasons,
        "anomaly_score": anomaly_score,
        "model_version": model_version,
        "policy_result": policy_allowed,
        "timestamp": now
    }
