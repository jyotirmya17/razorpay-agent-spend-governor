import pytest
from gateway.risk.decision import make_risk_decision, RiskConfig

def test_valid_mandate_low_risk_allow():
    config = RiskConfig(flag_threshold=0.5, behavioral_blocking_enabled=False)
    result = make_risk_decision(True, "AUTHORIZED", 0.1, "v1", config)
    assert result["decision"] == "ALLOW"
    assert "BEHAVIOR_LOW_RISK" in result["reason_codes"]
    assert result["policy_result"] is True

def test_valid_mandate_behavioral_anomaly_flag():
    config = RiskConfig(flag_threshold=0.5, behavioral_blocking_enabled=False)
    result = make_risk_decision(True, "AUTHORIZED", 0.6, "v1", config)
    assert result["decision"] == "FLAG"
    assert "BEHAVIOR_REVIEW_REQUIRED" in result["reason_codes"]

def test_policy_violation_low_anomaly_block():
    config = RiskConfig(flag_threshold=0.5)
    result = make_risk_decision(False, "DAILY_CAP_EXCEEDED", 0.1, "v1", config)
    assert result["decision"] == "BLOCK"
    assert "DAILY_CAP_EXCEEDED" in result["reason_codes"]
    assert "BEHAVIOR_LOW_RISK" not in result["reason_codes"] # Policy blocks immediately

def test_policy_violation_high_anomaly_block():
    config = RiskConfig(flag_threshold=0.5)
    result = make_risk_decision(False, "AMOUNT_EXCEEDS_TXN_CAP", 0.9, "v1", config)
    assert result["decision"] == "BLOCK"
    assert "AMOUNT_EXCEEDS_TXN_CAP" in result["reason_codes"]

def test_expired_mandate_block():
    config = RiskConfig(flag_threshold=0.5)
    result = make_risk_decision(False, "MANDATE_EXPIRED", 0.1, "v1", config)
    assert result["decision"] == "BLOCK"
    assert "MANDATE_EXPIRED" in result["reason_codes"]

def test_revoked_mandate_block():
    config = RiskConfig(flag_threshold=0.5)
    result = make_risk_decision(False, "AGENT_REVOKED", 0.1, "v1", config)
    assert result["decision"] == "BLOCK"
    assert "AGENT_REVOKED" in result["reason_codes"]

def test_transaction_limit_violation_block():
    config = RiskConfig(flag_threshold=0.5)
    result = make_risk_decision(False, "AMOUNT_EXCEEDS_TXN_CAP", 0.1, "v1", config)
    assert result["decision"] == "BLOCK"
    assert "AMOUNT_EXCEEDS_TXN_CAP" in result["reason_codes"]

def test_high_risk_blocking_disabled_flag():
    config = RiskConfig(flag_threshold=0.5, block_threshold=0.9, behavioral_blocking_enabled=False)
    result = make_risk_decision(True, "AUTHORIZED", 0.95, "v1", config)
    assert result["decision"] == "FLAG"
    assert "BEHAVIOR_HIGH_RISK" in result["reason_codes"]

def test_high_risk_blocking_enabled_block():
    config = RiskConfig(flag_threshold=0.5, block_threshold=0.9, behavioral_blocking_enabled=True)
    result = make_risk_decision(True, "AUTHORIZED", 0.95, "v1", config)
    assert result["decision"] == "BLOCK"
    assert "BEHAVIOR_HIGH_RISK" in result["reason_codes"]

def test_missing_model_output_fails_safe_flag():
    config = RiskConfig(flag_threshold=0.5)
    result = make_risk_decision(True, "AUTHORIZED", None, None, config)
    assert result["decision"] == "FLAG"
    assert "BEHAVIOR_EVALUATION_FAILED" in result["reason_codes"]

def test_invalid_model_output_fails_safe_flag():
    config = RiskConfig(flag_threshold=0.5)
    
    # Negative value
    result = make_risk_decision(True, "AUTHORIZED", -0.1, "v1", config)
    assert result["decision"] == "FLAG"
    assert "BEHAVIOR_EVALUATION_FAILED" in result["reason_codes"]
    
    # > 1 value
    result2 = make_risk_decision(True, "AUTHORIZED", 1.5, "v1", config)
    assert result2["decision"] == "FLAG"
    assert "BEHAVIOR_EVALUATION_FAILED" in result2["reason_codes"]
    
    # NaN
    result_nan = make_risk_decision(True, "AUTHORIZED", float('nan'), "v1", config)
    assert result_nan["decision"] == "FLAG"
    assert "BEHAVIOR_EVALUATION_FAILED" in result_nan["reason_codes"]
    
    # Infinity
    result_inf = make_risk_decision(True, "AUTHORIZED", float('inf'), "v1", config)
    assert result_inf["decision"] == "FLAG"
    assert "BEHAVIOR_EVALUATION_FAILED" in result_inf["reason_codes"]
    
    # -Infinity
    result_ninf = make_risk_decision(True, "AUTHORIZED", float('-inf'), "v1", config)
    assert result_ninf["decision"] == "FLAG"
    assert "BEHAVIOR_EVALUATION_FAILED" in result_ninf["reason_codes"]

def test_policy_violation_precedence_with_nan_score():
    config = RiskConfig(flag_threshold=0.5)
    result = make_risk_decision(False, "DAILY_CAP_EXCEEDED", float('nan'), "v1", config)
    assert result["decision"] == "BLOCK"
    assert "DAILY_CAP_EXCEEDED" in result["reason_codes"]
    assert "BEHAVIOR_EVALUATION_FAILED" not in result["reason_codes"]

def test_boundary_values():
    config = RiskConfig(flag_threshold=0.5, block_threshold=0.9, behavioral_blocking_enabled=True)
    
    # Exactly flag threshold -> FLAG
    result = make_risk_decision(True, "AUTHORIZED", 0.5, "v1", config)
    assert result["decision"] == "FLAG"
    assert "BEHAVIOR_REVIEW_REQUIRED" in result["reason_codes"]
    
    # Just below flag threshold -> ALLOW
    result2 = make_risk_decision(True, "AUTHORIZED", 0.499, "v1", config)
    assert result2["decision"] == "ALLOW"
    
    # Exactly block threshold -> BLOCK
    result3 = make_risk_decision(True, "AUTHORIZED", 0.9, "v1", config)
    assert result3["decision"] == "BLOCK"
    assert "BEHAVIOR_HIGH_RISK" in result3["reason_codes"]

def test_reason_codes_deterministic_and_preserved_model_version():
    config = RiskConfig(flag_threshold=0.5)
    result = make_risk_decision(True, "AUTHORIZED", 0.1, "my_model_v2", config)
    assert result["model_version"] == "my_model_v2"
    assert result["anomaly_score"] == 0.1
    assert "timestamp" in result
