import math
from datetime import timedelta
from gateway.risk.profiles import AgentBehaviorProfile
from gateway.risk.data_generator import TransactionRecord

def sigmoid(x: float) -> float:
    """Standard sigmoid function to map values to (0, 1) bounds."""
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0

def extract_features(profile: AgentBehaviorProfile, txn: TransactionRecord) -> dict:
    """
    Extracts point-in-time behavioral features for a transaction based on historical profile.
    This function is strictly immutable regarding the profile.
    """
    amount = float(txn["amount_paise"])
    timestamp = txn["timestamp"]
    txn_date = timestamp.date()
    
    # 1. AMOUNT DEVIATION
    MIN_STD = 100.0  # Safe floor to prevent extreme z-scores for highly rigid spenders
    if profile.transaction_count > 0:
        std = max(profile.typical_amount_std, MIN_STD)
        amount_deviation = abs(amount - profile.typical_amount_mean) / std
    else:
        amount_deviation = 0.0

    # 2. PAYEE NOVELTY
    payee_id = txn["payee_id"]
    payee_freq = profile.payee_frequency.get(payee_id, 0)
    if payee_freq == 0:
        payee_novelty = 1.0  # New
    elif payee_freq < 5:
        payee_novelty = 0.5  # Rare
    else:
        payee_novelty = 0.0  # Frequent

    # 3. TRANSACTION VELOCITY
    v_5m, v_1h, v_24h = 0, 0, 0
    t_5m = timestamp - timedelta(minutes=5)
    t_1h = timestamp - timedelta(hours=1)
    t_24h = timestamp - timedelta(hours=24)
    
    # Iterate backwards over the deque (which is sorted ascending by time)
    for i in range(len(profile.recent_timestamps) - 1, -1, -1):
        prev_time = profile.recent_timestamps[i]
        if prev_time >= t_5m:
            v_5m += 1
        if prev_time >= t_1h:
            v_1h += 1
        if prev_time >= t_24h:
            v_24h += 1
        else:
            break
            
    # 4. TIME OF DAY DEVIATION
    hour = timestamp.hour
    if profile.transaction_count > 0:
        p_hour = profile.active_hour_distribution[hour] / profile.transaction_count
        time_of_day_deviation = 1.0 - p_hour
    else:
        time_of_day_deviation = 0.0

    # 5. WEEKDAY DEVIATION
    weekday = timestamp.weekday()
    if profile.transaction_count > 0:
        p_weekday = profile.weekday_distribution[weekday] / profile.transaction_count
        weekday_deviation = 1.0 - p_weekday
    else:
        weekday_deviation = 0.0

    # 6. CATEGORY DEVIATION
    category = txn["category"]
    if profile.transaction_count > 0:
        p_category = profile.category_distribution.get(category, 0) / profile.transaction_count
        category_deviation = 1.0 - p_category
    else:
        category_deviation = 0.0

    # 7. & 8. DAILY/WEEKLY SPEND DEVIATION
    MIN_SPEND = 100.0  # Safe floor to prevent divide-by-zero or explosion
    
    if profile.last_txn_date is None:
        effective_daily_ema = 0.0
        effective_weekly_ema = 0.0
        proposed_daily_spend = amount
        proposed_weekly_spend = amount
    else:
        days_diff = (txn_date - profile.last_txn_date).days
        if days_diff <= 0:
            effective_daily_ema = profile.daily_spend_ema
            effective_weekly_ema = profile.weekly_spend_ema
            proposed_daily_spend = profile.current_day_spend + amount
            proposed_weekly_spend = profile.current_week_spend + amount
        else:
            # Simulate the EMA flush that would happen
            alpha = 0.2
            effective_daily_ema = (alpha * profile.current_day_spend) + ((1 - alpha) * profile.daily_spend_ema)
            
            # Simulate missing days decay
            if days_diff > 1:
                effective_daily_ema *= ((1 - alpha) ** min(days_diff - 1, 30))
                
            # Simulate weekly flush if iso-week changed
            if txn_date.isocalendar()[1] != profile.last_txn_date.isocalendar()[1]:
                effective_weekly_ema = (alpha * profile.current_week_spend) + ((1 - alpha) * profile.weekly_spend_ema)
                proposed_weekly_spend = amount
            else:
                effective_weekly_ema = profile.weekly_spend_ema
                proposed_weekly_spend = profile.current_week_spend + amount
                
            proposed_daily_spend = amount

    daily_spend_deviation = proposed_daily_spend / max(effective_daily_ema, MIN_SPEND)
    weekly_spend_deviation = proposed_weekly_spend / max(effective_weekly_ema, MIN_SPEND)

    # 9. PAYEE CONCENTRATION
    if profile.transaction_count > 0 and profile.payee_frequency:
        max_payee_freq = max(profile.payee_frequency.values())
        payee_concentration = max_payee_freq / profile.transaction_count
    else:
        payee_concentration = 0.0

    # 10. BEHAVIORAL DISTANCE
    # Bounded [0,1] composite of normalized behavioral signals.
    # We use sigmoid to cap unbounded metrics like amount_deviation and spend deviations.
    
    # Base weight components
    comp_amount = sigmoid(amount_deviation - 3.0)  # Centers around 3 sigma
    comp_daily = sigmoid((daily_spend_deviation - 2.0) * 2) # Centers around 2x normal spend
    comp_weekly = sigmoid((weekly_spend_deviation - 1.5) * 2)
    
    # Categorical/Probability deviations are already in [0, 1] range
    comp_time = time_of_day_deviation
    comp_category = category_deviation
    
    # Payee novelty already [0, 0.5, 1.0]
    comp_novelty = payee_novelty
    
    # Simple weighted average of the strongest indicators
    weights = [2.0, 1.0, 1.0, 1.0, 1.5, 1.5]
    values = [comp_amount, comp_daily, comp_weekly, comp_time, comp_category, comp_novelty]
    
    behavioral_distance = sum(w * v for w, v in zip(weights, values)) / sum(weights)

    return {
        "amount_deviation": amount_deviation,
        "payee_novelty": payee_novelty,
        "velocity_5m": v_5m,
        "velocity_1h": v_1h,
        "velocity_24h": v_24h,
        "time_of_day_deviation": time_of_day_deviation,
        "weekday_deviation": weekday_deviation,
        "category_deviation": category_deviation,
        "daily_spend_deviation": daily_spend_deviation,
        "weekly_spend_deviation": weekly_spend_deviation,
        "payee_concentration": payee_concentration,
        "behavioral_distance": behavioral_distance
    }
