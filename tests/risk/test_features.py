import pytest
from datetime import datetime, timezone, timedelta
from copy import deepcopy
from gateway.risk.profiles import AgentBehaviorProfile, update_profile
from gateway.risk.features import extract_features
import uuid

def _txn(amount: int, dt: datetime, payee: str = "fa_123", category: str = "software") -> dict:
    return {
        "transaction_id": f"txn_{uuid.uuid4().hex[:8]}",
        "agent_id": "ag_test",
        "amount_paise": amount,
        "currency": "INR",
        "timestamp": dt,
        "payee_id": payee,
        "category": category,
        "status": "SUCCEEDED",
        "is_anomaly": False,
        "anomaly_type": "NORMAL"
    }

def test_feature_immutability():
    """extract_features() must not mutate the profile."""
    profile = AgentBehaviorProfile("ag_test")
    dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    txn = _txn(1000, dt)
    
    update_profile(profile, txn)
    
    profile_before = deepcopy(profile)
    
    new_txn = _txn(2000, dt + timedelta(hours=1))
    features = extract_features(profile, new_txn)
    
    assert profile.transaction_count == profile_before.transaction_count
    assert profile.amount_sum == profile_before.amount_sum
    assert profile.recent_timestamps == profile_before.recent_timestamps
    assert profile.current_day_spend == profile_before.current_day_spend

def test_deterministic_repeated_extraction():
    """extract_features() must return exactly the same dict if called multiple times."""
    profile = AgentBehaviorProfile("ag_test")
    dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    update_profile(profile, _txn(1000, dt))
    
    new_txn = _txn(2000, dt + timedelta(hours=1))
    f1 = extract_features(profile, new_txn)
    f2 = extract_features(profile, new_txn)
    
    assert f1 == f2

def test_cold_start_zero_history():
    """Agent with 0 history: no div by zero, deterministic output."""
    profile = AgentBehaviorProfile("ag_test")
    txn = _txn(5000, datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc))
    
    features = extract_features(profile, txn)
    
    assert features["amount_deviation"] == 0.0
    assert features["payee_novelty"] == 1.0 # New payee
    assert features["velocity_5m"] == 0
    assert features["time_of_day_deviation"] == 0.0
    assert features["weekday_deviation"] == 0.0
    assert features["category_deviation"] == 0.0
    assert features["payee_concentration"] == 0.0
    
def test_zero_variance_one_txn():
    """Agent with exactly 1 historical transaction (zero variance/std dev)."""
    profile = AgentBehaviorProfile("ag_test")
    dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    update_profile(profile, _txn(1000, dt))
    
    assert profile.typical_amount_std == 0.0
    
    # New transaction with different amount
    new_txn = _txn(5000, dt + timedelta(hours=1))
    features = extract_features(profile, new_txn)
    
    # STD is floored at MIN_STD = 100.0, so 4000 diff / 100 = 40.0 deviation
    assert features["amount_deviation"] == 40.0

def test_amount_deviation_large():
    """Test large amount deviation."""
    profile = AgentBehaviorProfile("ag_test")
    dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    update_profile(profile, _txn(1000, dt))
    update_profile(profile, _txn(1200, dt + timedelta(days=1)))
    update_profile(profile, _txn(900, dt + timedelta(days=2)))
    
    new_txn = _txn(20000, dt + timedelta(days=3))
    features = extract_features(profile, new_txn)
    
    assert features["amount_deviation"] > 10.0

def test_payee_novelty():
    """Test new, rare, and frequent payee mappings."""
    profile = AgentBehaviorProfile("ag_test")
    dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    
    for i in range(6):
        update_profile(profile, _txn(1000, dt + timedelta(days=i), payee="fa_freq"))
    for i in range(2):
        update_profile(profile, _txn(1000, dt + timedelta(days=i), payee="fa_rare"))
        
    f_freq = extract_features(profile, _txn(1000, dt + timedelta(days=10), payee="fa_freq"))
    f_rare = extract_features(profile, _txn(1000, dt + timedelta(days=10), payee="fa_rare"))
    f_new = extract_features(profile, _txn(1000, dt + timedelta(days=10), payee="fa_new"))
    
    assert f_freq["payee_novelty"] == 0.0
    assert f_rare["payee_novelty"] == 0.5
    assert f_new["payee_novelty"] == 1.0

def test_transaction_velocity_double_count():
    """Verify incoming transaction is not double-counted in velocity."""
    profile = AgentBehaviorProfile("ag_test")
    dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    
    # 2 transactions inside 5 mins
    update_profile(profile, _txn(1000, dt))
    update_profile(profile, _txn(1000, dt + timedelta(minutes=2)))
    
    new_txn = _txn(1000, dt + timedelta(minutes=4))
    features = extract_features(profile, new_txn)
    
    # Velocity should be exactly 2 (the history), not 3 (history + current)
    assert features["velocity_5m"] == 2
    assert features["velocity_1h"] == 2
    assert features["velocity_24h"] == 2

def test_high_velocity_pruning():
    """High-velocity agent test, > 24 hours shouldn't count."""
    profile = AgentBehaviorProfile("ag_test")
    dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    
    update_profile(profile, _txn(1000, dt)) # 48 hours ago
    update_profile(profile, _txn(1000, dt + timedelta(hours=24))) # 24 hours ago
    update_profile(profile, _txn(1000, dt + timedelta(hours=47, minutes=30))) # 30 mins ago
    
    new_txn = _txn(1000, dt + timedelta(hours=48))
    features = extract_features(profile, new_txn)
    
    assert features["velocity_5m"] == 0
    assert features["velocity_1h"] == 1
    assert features["velocity_24h"] == 2  # The one at 24h and the one at 47h30m

def test_current_day_rollover():
    """Test daily spend deviation across a day boundary."""
    profile = AgentBehaviorProfile("ag_test")
    dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    
    update_profile(profile, _txn(1000, dt))
    assert profile.daily_spend_ema == 0.0 # Initial hasn't flushed
    
    # Next day transaction
    new_txn = _txn(5000, dt + timedelta(days=1))
    features = extract_features(profile, new_txn)
    
    # Profile should still not be flushed
    assert profile.daily_spend_ema == 0.0
    
    # But feature extractor simulates the flush: ema should be 0.2*1000 = 200
    # proposed spend is 5000. Ratio = 5000/200 = 25.0
    assert features["daily_spend_deviation"] == 25.0

def test_current_week_rollover():
    """Test weekly spend deviation across an iso-week boundary."""
    profile = AgentBehaviorProfile("ag_test")
    dt = datetime(2024, 1, 7, 10, 0, 0, tzinfo=timezone.utc) # Sunday
    
    update_profile(profile, _txn(1000, dt))
    
    # Next day is Monday, new iso week
    new_txn = _txn(5000, dt + timedelta(days=1))
    features = extract_features(profile, new_txn)
    
    # Feature extractor simulates week flush: ema = 0.2*1000 = 200
    # proposed weekly spend is 5000. Ratio = 5000/200 = 25.0
    assert features["weekly_spend_deviation"] == 25.0

def test_time_and_category_deviations():
    """Unusual hour and missing-category history test."""
    profile = AgentBehaviorProfile("ag_test")
    dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    
    for _ in range(10):
        update_profile(profile, _txn(1000, dt, category="software"))
        
    # All txns at 10 AM.
    new_txn = _txn(1000, dt.replace(hour=23), category="hardware")
    features = extract_features(profile, new_txn)
    
    assert features["time_of_day_deviation"] == 1.0 # 0 probability of 23
    assert features["category_deviation"] == 1.0 # 0 probability of hardware
    
def test_bounds_test_composite():
    """Bounds test for normalized features."""
    profile = AgentBehaviorProfile("ag_test")
    dt = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    update_profile(profile, _txn(1000, dt))
    
    new_txn = _txn(1000000000, dt + timedelta(days=1)) # Extreme anomaly
    features = extract_features(profile, new_txn)
    
    assert 0.0 <= features["behavioral_distance"] <= 1.0

def test_strict_no_future_leakage():
    """Verify point-in-time ordering strictly relies on past data."""
    profile = AgentBehaviorProfile("ag_test")
    dt1 = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    dt2 = datetime(2024, 1, 2, 10, 0, 0, tzinfo=timezone.utc)
    
    txn1 = _txn(1000, dt1)
    txn2 = _txn(50000, dt2) # Future anomaly
    
    update_profile(profile, txn1)
    # Extract features BEFORE updating profile with txn2
    f_before = extract_features(profile, txn2)
    
    assert f_before["amount_deviation"] > 0
    
    # Update profile
    update_profile(profile, txn2)
    
    # Extract features AFTER updating profile with txn2
    f_after = extract_features(profile, txn2)
    
    # f_after would be meaningless in practice, but tests that feature extractor 
    # output changes significantly if future data was leaked into the profile
    assert f_before != f_after
