import math
from typing import Dict, List, Tuple
from collections import defaultdict, deque
from datetime import timedelta
from gateway.risk.data_generator import TransactionRecord
import random

class AgentBehaviorProfile:
    """
    Running historical profile of an agent.
    Built incrementally to avoid temporal leakage.
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        
        self.transaction_count = 0
        self.amount_sum = 0.0
        self.amount_sq_sum = 0.0
        
        self.payee_frequency: Dict[str, int] = defaultdict(int)
        self.category_distribution: Dict[str, int] = defaultdict(int)
        
        self.active_hour_distribution = [0] * 24
        self.weekday_distribution = [0] * 7
        
        # Exponential moving averages for spend
        self.daily_spend_ema = 0.0
        self.weekly_spend_ema = 0.0
        
        # State tracking for EMA
        self.last_txn_date = None
        self.current_day_spend = 0.0
        self.current_week_spend = 0.0
        
        # Memory for velocity calculation
        self.recent_timestamps: deque = deque()

    @property
    def typical_amount_mean(self) -> float:
        if self.transaction_count == 0:
            return 0.0
        return self.amount_sum / self.transaction_count
        
    @property
    def typical_amount_std(self) -> float:
        if self.transaction_count < 2:
            return 0.0
        mean = self.typical_amount_mean
        variance = (self.amount_sq_sum / self.transaction_count) - (mean ** 2)
        return math.sqrt(max(0, variance))

def update_profile(profile: AgentBehaviorProfile, txn: TransactionRecord):
    """
    Updates the running profile with a new transaction.
    """
    profile.transaction_count += 1
    amount = float(txn["amount_paise"])
    profile.amount_sum += amount
    profile.amount_sq_sum += (amount ** 2)
    
    profile.payee_frequency[txn["payee_id"]] += 1
    profile.category_distribution[txn["category"]] += 1
    
    hour = txn["timestamp"].hour
    weekday = txn["timestamp"].weekday()
    
    profile.active_hour_distribution[hour] += 1
    profile.weekday_distribution[weekday] += 1
    
    # Update spend EMAs
    txn_date = txn["timestamp"].date()
    if profile.last_txn_date is None:
        profile.last_txn_date = txn_date
        profile.current_day_spend = amount
        profile.current_week_spend = amount
    else:
        days_diff = (txn_date - profile.last_txn_date).days
        if days_diff > 0:
            alpha_day = 0.2
            profile.daily_spend_ema = (alpha_day * profile.current_day_spend) + ((1 - alpha_day) * profile.daily_spend_ema)
            
            if txn_date.isocalendar()[1] != profile.last_txn_date.isocalendar()[1]:
                alpha_week = 0.2
                profile.weekly_spend_ema = (alpha_week * profile.current_week_spend) + ((1 - alpha_week) * profile.weekly_spend_ema)
                profile.current_week_spend = 0.0
                
            profile.current_day_spend = 0.0
            
            # Decay for missing days
            if days_diff > 1:
                for _ in range(min(days_diff - 1, 30)):
                    profile.daily_spend_ema *= (1 - alpha_day)
                    
        profile.current_day_spend += amount
        profile.current_week_spend += amount
        profile.last_txn_date = txn_date
        
    # Maintain rolling 24-hour window for velocity
    profile.recent_timestamps.append(txn["timestamp"])
    cutoff = txn["timestamp"] - timedelta(hours=24)
    while profile.recent_timestamps and profile.recent_timestamps[0] < cutoff:
        profile.recent_timestamps.popleft()

def temporal_split(
    transactions: List[TransactionRecord], 
    train_ratio: float = 0.7, 
    val_ratio: float = 0.15, 
    unseen_agent_ratio: float = 0.1,
    seed: int = 42
) -> Tuple[List[TransactionRecord], List[TransactionRecord], List[TransactionRecord]]:
    """
    Splits dataset into Train, Val, and Test chronologically.
    Supports a cold-start unseen-agent evaluation by holding out a percentage of agents
    entirely from Train and Val, putting all their transactions into Test.
    """
    if not transactions:
        return [], [], []
        
    unique_agents = list(set(txn["agent_id"] for txn in transactions))
    unique_agents.sort() # Ensure deterministic split
    
    rng = random.Random(seed)
    rng.shuffle(unique_agents)
    
    num_unseen = int(len(unique_agents) * unseen_agent_ratio)
    unseen_agents = set(unique_agents[:num_unseen])
    known_agents = set(unique_agents[num_unseen:])
    
    known_txns = [t for t in transactions if t["agent_id"] in known_agents]
    unseen_txns = [t for t in transactions if t["agent_id"] in unseen_agents]
    
    train_end = int(len(known_txns) * train_ratio)
    val_end = train_end + int(len(known_txns) * val_ratio)
    
    train_set = known_txns[:train_end]
    val_set = known_txns[train_end:val_end]
    
    test_set = known_txns[val_end:] + unseen_txns
    test_set.sort(key=lambda x: x["timestamp"])
    
    return train_set, val_set, test_set
