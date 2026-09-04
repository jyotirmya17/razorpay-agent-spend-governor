import pytest
from gateway.risk.data_generator import generate_dataset

def test_data_generator_reproducibility():
    """Verify exact same data is produced for the same seed."""
    ds1 = generate_dataset(seed=42, num_agents=50, num_transactions=1000)
    ds2 = generate_dataset(seed=42, num_agents=50, num_transactions=1000)
    
    assert len(ds1) == len(ds2) == 1000
    for t1, t2 in zip(ds1, ds2):
        assert t1 == t2

def test_data_generator_constraints():
    """Verify constraints: 50 agents, 10000 transactions, all fields present."""
    ds = generate_dataset(seed=99, num_agents=50, num_transactions=10000)
    assert len(ds) == 10000
    
    agents = set(t["agent_id"] for t in ds)
    assert len(agents) == 50
    
    first = ds[0]
    expected_keys = {
        "transaction_id", "agent_id", "timestamp", "amount_paise", 
        "currency", "payee_id", "category", "status", "is_anomaly", "anomaly_type"
    }
    assert set(first.keys()) == expected_keys

def test_data_generator_anomalies_and_hard_negatives():
    ds = generate_dataset(seed=123, num_transactions=10000, anomaly_rate=0.05, hard_negative_rate=0.05)
    
    true_anomalies = [t for t in ds if t["is_anomaly"]]
    hard_negatives = [t for t in ds if not t["is_anomaly"] and t["anomaly_type"] != "NORMAL"]
    
    assert len(true_anomalies) > 0
    assert len(hard_negatives) > 0
    
    anomaly_types = set(t["anomaly_type"] for t in true_anomalies)
    assert len(anomaly_types) > 1 # Should have multiple anomaly types generated
    
    hn_types = set(t["anomaly_type"] for t in hard_negatives)
    assert len(hn_types) > 1 # Should have multiple hard negative types generated
    
    # Assert normal exist
    normals = [t for t in ds if not t["is_anomaly"] and t["anomaly_type"] == "NORMAL"]
    assert len(normals) > 5000
