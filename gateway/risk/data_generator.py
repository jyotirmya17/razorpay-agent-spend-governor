import random
import uuid
from typing import Dict, List, TypedDict, Any
from datetime import datetime, timedelta, timezone

class TransactionRecord(TypedDict):
    transaction_id: str
    agent_id: str
    timestamp: datetime
    amount_paise: int
    currency: str
    payee_id: str
    category: str
    status: str
    is_anomaly: bool
    anomaly_type: str

class AgentSimulationProfile:
    """
    Ground-truth simulation profile for generating synthetic data.
    Strictly separate from the detector's running profile.
    """
    def __init__(
        self,
        agent_id: str,
        agent_type: str,
        min_amount: int,
        max_amount: int,
        active_hours: List[int],
        active_weekdays: List[int],
        preferred_categories: List[str],
        preferred_payees: List[str],
        txns_per_week: float
    ):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.active_hours = active_hours
        self.active_weekdays = active_weekdays
        self.preferred_categories = preferred_categories
        self.preferred_payees = preferred_payees
        self.txns_per_week = txns_per_week

def generate_simulation_profiles(num_agents: int, rng: random.Random = None) -> List[AgentSimulationProfile]:
    if rng is None:
        rng = random.Random(42)
    profiles = []
    agent_types = ["procurement", "saas_billing", "contractor", "travel", "operations", "finance"]
    
    for _ in range(num_agents):
        agent_id = f"ag_{rng.getrandbits(48):012x}"
        agent_type = rng.choice(agent_types)
        
        if agent_type == "saas_billing":
            min_a, max_a = 100000, 1000000 # 1000 to 10000 INR
            hours = list(range(9, 18))
            days = [0, 1, 2, 3, 4]
            cats = ["cloud", "software", "subscription"]
            txns_per_week = rng.uniform(1.0, 5.0)
        elif agent_type == "contractor":
            min_a, max_a = 2000000, 8000000 # 20k to 80k INR
            hours = list(range(12, 18))
            days = [0, 1, 2, 3, 4]
            cats = ["contractor", "freelance", "services"]
            txns_per_week = rng.uniform(0.5, 2.0)
        elif agent_type == "travel":
            min_a, max_a = 500000, 3000000
            hours = list(range(6, 23))
            days = [0, 1, 2, 3, 4, 5, 6]
            cats = ["flight", "hotel", "cab", "meal"]
            txns_per_week = rng.uniform(2.0, 10.0)
        elif agent_type == "operations":
            min_a, max_a = 50000, 500000
            hours = list(range(8, 20))
            days = [0, 1, 2, 3, 4, 5]
            cats = ["supplies", "logistics", "maintenance"]
            txns_per_week = rng.uniform(5.0, 20.0)
        elif agent_type == "finance":
            min_a, max_a = 5000000, 50000000
            hours = list(range(10, 16))
            days = [0, 1, 2, 3, 4]
            cats = ["tax", "legal", "compliance", "payroll"]
            txns_per_week = rng.uniform(0.1, 1.0)
        else: # procurement
            min_a, max_a = 1000000, 20000000
            hours = list(range(9, 17))
            days = [0, 1, 2, 3, 4]
            cats = ["equipment", "inventory", "hardware"]
            txns_per_week = rng.uniform(3.0, 15.0)
            
        num_payees = rng.randint(3, 15)
        payees = [f"fa_{rng.getrandbits(48):012x}" for _ in range(num_payees)]
        
        profiles.append(AgentSimulationProfile(
            agent_id, agent_type, min_a, max_a, hours, days, cats, payees, txns_per_week
        ))
        
    return profiles

def generate_dataset(
    seed: int = 42,
    num_agents: int = 50,
    num_transactions: int = 10000,
    anomaly_rate: float = 0.05,
    hard_negative_rate: float = 0.05
) -> List[TransactionRecord]:
    rng = random.Random(seed)
    
    profiles = generate_simulation_profiles(num_agents, rng=rng)
    total_weight = sum(p.txns_per_week for p in profiles)
    
    end_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    start_date = end_date - timedelta(days=365)
    
    transactions: List[TransactionRecord] = []
    
    anomaly_types = [
        "AMOUNT_DEVIATION", "NEW_PAYEE", "ODD_HOUR", "BURST_ACTIVITY",
        "CATEGORY_DEVIATION", "SPEND_SPIKE", "BEHAVIOR_SHIFT"
    ]
    hard_negative_types = [
        "LEGITIMATE_NEW_VENDOR", "LEGITIMATE_LARGE_INVOICE", "LEGITIMATE_WEEKEND_PAYMENT",
        "LEGITIMATE_CATEGORY_CHANGE", "LEGITIMATE_TEMPORARY_SPIKE"
    ]
    
    for i, profile in enumerate(profiles):
        if i == len(profiles) - 1:
            # Last agent gets the remainder to ensure exact num_transactions
            agent_txns_count = max(1, num_transactions - len(transactions))
        else:
            agent_txns_count = max(1, int(round((profile.txns_per_week / total_weight) * num_transactions)))
            
        agent_txns = []
        burst_txns_remaining = 0
        burst_base_ts = None
        
        for _ in range(agent_txns_count):
            if burst_txns_remaining > 0:
                burst_txns_remaining -= 1
                burst_base_ts += timedelta(minutes=rng.randint(1, 15))
                
                agent_txns.append(TransactionRecord(
                    transaction_id=f"txn_{rng.getrandbits(64):016x}",
                    agent_id=profile.agent_id,
                    timestamp=burst_base_ts,
                    amount_paise=int(rng.randint(profile.min_amount, profile.max_amount)),
                    currency="INR",
                    payee_id=rng.choice(profile.preferred_payees),
                    category=rng.choice(profile.preferred_categories),
                    status="SUCCEEDED",
                    is_anomaly=False,
                    anomaly_type="LEGITIMATE_TEMPORARY_SPIKE"
                ))
                continue
                
            days_offset = rng.randint(0, 364)
            txn_date = start_date + timedelta(days=days_offset)
            
            r = rng.random()
            if r < anomaly_rate:
                is_anomaly = True
                anomaly_type = rng.choice(anomaly_types)
            elif r < anomaly_rate + hard_negative_rate:
                is_anomaly = False
                anomaly_type = rng.choice(hard_negative_types) # Store type even if it's a hard negative
            else:
                is_anomaly = False
                anomaly_type = "NORMAL"
                
            amount = rng.randint(profile.min_amount, profile.max_amount)
            payee = rng.choice(profile.preferred_payees)
            category = rng.choice(profile.preferred_categories)
            hour = rng.choice(profile.active_hours)
            
            # Anomalies overrides
            if is_anomaly:
                if anomaly_type == "AMOUNT_DEVIATION":
                    amount = profile.max_amount * rng.randint(3, 10)
                elif anomaly_type == "NEW_PAYEE":
                    payee = f"fa_anomaly_{rng.getrandbits(32):08x}"
                elif anomaly_type == "ODD_HOUR":
                    available_hours = [h for h in range(24) if h not in profile.active_hours]
                    hour = rng.choice(available_hours) if available_hours else 0
                elif anomaly_type == "CATEGORY_DEVIATION":
                    category = "unauthorized_category"
                elif anomaly_type == "BEHAVIOR_SHIFT":
                    amount = profile.max_amount * rng.uniform(1.5, 3.0)
                    available_hours = [h for h in range(24) if h not in profile.active_hours]
                    hour = rng.choice(available_hours) if available_hours else 0
                    category = "shifted_category"
            
            # Hard negatives overrides
            if not is_anomaly and anomaly_type != "NORMAL":
                if anomaly_type == "LEGITIMATE_NEW_VENDOR":
                    payee = f"fa_legit_new_{rng.getrandbits(32):08x}"
                elif anomaly_type == "LEGITIMATE_LARGE_INVOICE":
                    amount = profile.max_amount * rng.randint(2, 5)
                elif anomaly_type == "LEGITIMATE_WEEKEND_PAYMENT":
                    # Force weekend
                    days_offset += (5 - txn_date.weekday()) % 7
                    txn_date = start_date + timedelta(days=days_offset)
                elif anomaly_type == "LEGITIMATE_CATEGORY_CHANGE":
                    category = "legit_temp_category"
                    
            if anomaly_type not in ["LEGITIMATE_WEEKEND_PAYMENT"]:
                # Ensure day matches if not explicitly forcing weekend
                attempts = 0
                while txn_date.weekday() not in profile.active_weekdays and attempts < 7:
                    txn_date += timedelta(days=1)
                    attempts += 1
                        
            final_timestamp = txn_date.replace(
                hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59)
            )
            
            agent_txns.append(TransactionRecord(
                transaction_id=f"txn_{rng.getrandbits(64):016x}",
                agent_id=profile.agent_id,
                timestamp=final_timestamp,
                amount_paise=int(amount),
                currency="INR",
                payee_id=payee,
                category=category,
                status="SUCCEEDED",
                is_anomaly=is_anomaly,
                anomaly_type=anomaly_type
            ))
            
            if anomaly_type == "LEGITIMATE_TEMPORARY_SPIKE":
                burst_txns_remaining = rng.randint(2, 3)
                burst_base_ts = final_timestamp
            
        transactions.extend(agent_txns)
        
    transactions.sort(key=lambda x: (x["timestamp"], x["transaction_id"]))
    
    if len(transactions) > num_transactions:
        transactions = transactions[:num_transactions]
        
    return transactions
