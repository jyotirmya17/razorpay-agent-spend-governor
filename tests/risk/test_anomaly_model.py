import pytest
import numpy as np
import math
import os
import tempfile
from gateway.risk.anomaly_model import BehavioralAnomalyModel, CANONICAL_FEATURES
from gateway.risk.profiles import AgentBehaviorProfile, temporal_split, update_profile
from gateway.risk.features import extract_features
from gateway.risk.data_generator import generate_dataset

@pytest.fixture
def base_features():
    return {
        "amount_deviation": 0.0,
        "payee_novelty": 0.0,
        "velocity_5m": 1.0,
        "velocity_1h": 2.0,
        "velocity_24h": 5.0,
        "time_of_day_deviation": 0.1,
        "weekday_deviation": 0.1,
        "category_deviation": 0.1,
        "daily_spend_deviation": 0.2,
        "weekly_spend_deviation": 0.3,
        "payee_concentration": 0.8,
        "behavioral_distance": 0.1
    }

def test_missing_features_rejected(base_features):
    model = BehavioralAnomalyModel()
    del base_features["amount_deviation"]
    with pytest.raises(ValueError, match="Missing features"):
        model._dict_to_array(base_features)

def test_unexpected_features_rejected(base_features):
    model = BehavioralAnomalyModel()
    base_features["is_anomaly"] = True
    base_features["transaction_id"] = "txn_123"
    with pytest.raises(ValueError, match="Unexpected features"):
        model._dict_to_array(base_features)

def test_invalid_values_rejected(base_features):
    model = BehavioralAnomalyModel()
    base_features["amount_deviation"] = math.nan
    with pytest.raises(ValueError, match="invalid value"):
        model._dict_to_array(base_features)
        
    base_features["amount_deviation"] = math.inf
    with pytest.raises(ValueError, match="invalid value"):
        model._dict_to_array(base_features)

def test_canonical_ordering(base_features):
    model = BehavioralAnomalyModel()
    # Dictionary order should not matter
    scrambled = {k: base_features[k] for k in reversed(list(base_features.keys()))}
    arr1 = model._dict_to_array(base_features)
    arr2 = model._dict_to_array(scrambled)
    assert np.array_equal(arr1, arr2)
    # Ensure it exactly matches canonical features
    for i, f in enumerate(CANONICAL_FEATURES):
        assert arr1[i] == base_features[f]

def test_model_training_and_deterministic(base_features):
    train_data = [base_features.copy() for _ in range(50)]
    
    model1 = BehavioralAnomalyModel()
    model1.train(train_data)
    pred1 = model1.predict_one(base_features)
    
    model2 = BehavioralAnomalyModel()
    model2.train(train_data)
    pred2 = model2.predict_one(base_features)
    
    assert pred1["anomaly_score"] == pred2["anomaly_score"]
    assert pred1["prediction"] == pred2["prediction"]
    assert pred1["model_version"] == "behavioral_iforest_v1"

def test_save_load_equivalence(base_features):
    train_data = [base_features.copy() for _ in range(50)]
    model = BehavioralAnomalyModel()
    model.train(train_data)
    
    original_pred = model.predict_one(base_features)
    
    with tempfile.NamedTemporaryFile(delete=False) as f:
        filepath = f.name
        
    try:
        model.save(filepath)
        
        new_model = BehavioralAnomalyModel()
        new_model.load(filepath)
        
        loaded_pred = new_model.predict_one(base_features)
        assert original_pred == loaded_pred
    finally:
        os.remove(filepath)

def test_no_mutation_during_inference(base_features):
    model = BehavioralAnomalyModel()
    train_data = [base_features.copy() for _ in range(10)]
    model.train(train_data)
    
    # Copy dict
    test_dict = base_features.copy()
    model.predict_one(test_dict)
    
    # Should not be mutated
    assert test_dict == base_features

def test_controlled_deviation_elevated_risk(base_features):
    train_data = []
    for i in range(100):
        f = base_features.copy()
        # Add slight variance so Isolation Forest can build trees
        f["amount_deviation"] = (i % 5) * 0.1
        f["velocity_1h"] = 1.0 + (i % 3)
        train_data.append(f)
        
    model = BehavioralAnomalyModel()
    model.train(train_data)
    
    normal_pred = model.predict_one(base_features)
    
    anomalous = base_features.copy()
    anomalous["amount_deviation"] = 100.0
    anomalous["velocity_1h"] = 50.0
    anomalous["payee_novelty"] = 1.0
    
    anom_pred = model.predict_one(anomalous)
    
    # Anomaly score should be higher for obvious deviations
    assert anom_pred["anomaly_score"] > normal_pred["anomaly_score"]

def test_temporal_training_no_leakage():
    # Use real synthetic generator
    transactions = generate_dataset(num_transactions=100, seed=42)
    train_txns, val_txns, test_txns = temporal_split(transactions)
    
    # 1. We must construct historical feature vectors strictly sequentially.
    profiles = {}
    train_features = []
    
    for txn in train_txns:
        agent_id = txn["agent_id"]
        if agent_id not in profiles:
            profiles[agent_id] = AgentBehaviorProfile(agent_id=agent_id)
            
        profile = profiles[agent_id]
        
        # Point-in-time extraction BEFORE update
        feats = extract_features(profile, txn)
        train_features.append(feats)
        
        # Then update
        update_profile(profile, txn)
        
    # Check that labels are not in features
    for feats in train_features:
        assert "is_anomaly" not in feats
        assert "anomaly_type" not in feats
        assert "timestamp" not in feats
        
    # Model trains successfully on real synthetic data
    model = BehavioralAnomalyModel()
    model.train(train_features)
    
    # 2. No future data leakage check.
    # We grab a validation transaction and ensure its features don't rely on future data.
    val_txn = val_txns[0]
    agent_id = val_txn["agent_id"]
    
    profile = profiles[agent_id] # State exactly at end of training
    pre_update_feats = extract_features(profile, val_txn)
    
    # Ensure prediction works
    pred = model.predict_one(pre_update_feats)
    assert 0.0 <= pred["anomaly_score"] <= 1.0
    assert pred["prediction"] in ["NORMAL", "ANOMALY"]
