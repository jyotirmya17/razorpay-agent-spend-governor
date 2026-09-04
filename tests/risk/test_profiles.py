import pytest
from datetime import datetime
from gateway.risk.data_generator import generate_dataset
from gateway.risk.profiles import AgentBehaviorProfile, update_profile, temporal_split

def test_profile_update():
    """Verify profile tracks state correctly."""
    profile = AgentBehaviorProfile(agent_id="test_agent")
    assert profile.transaction_count == 0
    assert profile.typical_amount_mean == 0.0
    
    # Mock some txns
    from gateway.risk.data_generator import TransactionRecord
    t1 = TransactionRecord(
        transaction_id="txn_1", agent_id="test_agent", timestamp=datetime(2025, 1, 1, 10, 0),
        amount_paise=1000, currency="INR", payee_id="payee1", category="cat1", 
        status="SUCCEEDED", is_anomaly=False, anomaly_type="NORMAL"
    )
    t2 = TransactionRecord(
        transaction_id="txn_2", agent_id="test_agent", timestamp=datetime(2025, 1, 2, 11, 0),
        amount_paise=2000, currency="INR", payee_id="payee2", category="cat1", 
        status="SUCCEEDED", is_anomaly=False, anomaly_type="NORMAL"
    )
    
    update_profile(profile, t1)
    assert profile.transaction_count == 1
    assert profile.typical_amount_mean == 1000.0
    
    update_profile(profile, t2)
    assert profile.transaction_count == 2
    assert profile.typical_amount_mean == 1500.0
    assert profile.payee_frequency["payee1"] == 1
    assert profile.payee_frequency["payee2"] == 1
    assert profile.category_distribution["cat1"] == 2
    
def test_temporal_split():
    """Verify chronological split and cold-start agent isolation."""
    ds = generate_dataset(seed=42, num_agents=20, num_transactions=1000)
    train, val, test = temporal_split(ds, train_ratio=0.7, val_ratio=0.15, unseen_agent_ratio=0.1, seed=42)
    
    # Verify split sizes (approx)
    assert len(train) > 0
    assert len(val) > 0
    assert len(test) > 0
    
    # Check Chronological Order (for known agents, train -> val -> test_known)
    train_max_ts = max(t["timestamp"] for t in train)
    val_min_ts = min(t["timestamp"] for t in val)
    assert train_max_ts <= val_min_ts
    
    # Identify unseen agents
    train_agents = set(t["agent_id"] for t in train)
    val_agents = set(t["agent_id"] for t in val)
    test_agents = set(t["agent_id"] for t in test)
    
    known_agents = train_agents | val_agents
    
    # Verify unseen agents are strictly in test
    unseen_agents_in_test = test_agents - known_agents
    assert len(unseen_agents_in_test) > 0 # Given unseen_agent_ratio=0.1 on 20 agents -> ~2 unseen agents
    
    for t in train:
        assert t["agent_id"] not in unseen_agents_in_test
    for t in val:
        assert t["agent_id"] not in unseen_agents_in_test
