import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Any
from gateway.risk.data_generator import TransactionRecord
from gateway.risk.profiles import AgentBehaviorProfile, temporal_split, update_profile
from gateway.risk.features import extract_features
from gateway.risk.anomaly_model import BehavioralAnomalyModel

@dataclass
class EvaluationConfig:
    fp_cost: float = 10.0
    fn_cost: float = 100.0
    threshold_grid: List[float] = field(default_factory=lambda: [x / 100.0 for x in range(0, 101, 2)])
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    unseen_agent_ratio: float = 0.1
    seed: int = 42

@dataclass
class EvaluationMetrics:
    total: int = 0
    tp: int = 0
    tn: int = 0
    fp: int = 0
    fn: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    fpr: float = 0.0
    fnr: float = 0.0
    expected_cost: float = 0.0
    fp_cost: float = 0.0
    fn_cost: float = 0.0
    fn_monetary_exposure: float = 0.0

@dataclass
class EvaluationResult:
    model_version: str
    feature_schema: tuple
    train_size: int
    validation_size: int
    test_size: int
    threshold: float
    threshold_selection_method: str
    validation_metrics: EvaluationMetrics
    test_metrics: EvaluationMetrics
    per_anomaly_metrics: Dict[str, EvaluationMetrics]
    hard_negative_metrics: Dict[str, float]  # Type -> FPR
    known_agent_metrics: EvaluationMetrics
    unseen_agent_metrics: EvaluationMetrics
    cost_configuration: Dict[str, float]
    validation_expected_cost: float
    test_expected_cost: float
    false_negative_exposure: float
    baseline_comparison: Dict[str, EvaluationMetrics]
    sensitivity_analysis: Dict[float, EvaluationMetrics]

def compute_metrics(y_true: List[bool], y_pred: List[bool], amounts: List[float], config: EvaluationConfig) -> EvaluationMetrics:
    tp, tn, fp, fn = 0, 0, 0, 0
    fn_exposure = 0.0
    for true, pred, amt in zip(y_true, y_pred, amounts):
        if true and pred:
            tp += 1
        elif not true and not pred:
            tn += 1
        elif not true and pred:
            fp += 1
        elif true and not pred:
            fn += 1
            fn_exposure += amt

    total = tp + tn + fp + fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

    fp_cost = fp * config.fp_cost
    fn_cost = fn * config.fn_cost
    expected_cost = fp_cost + fn_cost

    return EvaluationMetrics(
        total=total, tp=tp, tn=tn, fp=fp, fn=fn,
        precision=precision, recall=recall, f1=f1, fpr=fpr, fnr=fnr,
        expected_cost=expected_cost, fp_cost=fp_cost, fn_cost=fn_cost,
        fn_monetary_exposure=fn_exposure
    )

def evaluate_model(model: BehavioralAnomalyModel, dataset: List[TransactionRecord], config: EvaluationConfig) -> EvaluationResult:
    # 1. Temporal Split
    train_txns, val_txns, test_txns = temporal_split(
        dataset, 
        train_ratio=config.train_ratio, 
        val_ratio=config.val_ratio, 
        unseen_agent_ratio=config.unseen_agent_ratio,
        seed=config.seed
    )
    
    unseen_agents = set(t["agent_id"] for t in test_txns) - set(t["agent_id"] for t in train_txns)
    
    profiles = {}
    
    # 2. Sequential Feature Construction & Profile Updates for Training
    train_features = []
    for txn in train_txns:
        agent_id = txn["agent_id"]
        if agent_id not in profiles:
            profiles[agent_id] = AgentBehaviorProfile(agent_id)
            
        features = extract_features(profiles[agent_id], txn)
        train_features.append(features)
        
        update_profile(profiles[agent_id], txn)
        
    # 3. Fit Model on Training Feature Matrix
    model.train(train_features)
    
    # 4. Score Validation Set
    val_true = []
    val_scores = []
    val_amounts = []
    
    for txn in val_txns:
        agent_id = txn["agent_id"]
        if agent_id not in profiles:
            profiles[agent_id] = AgentBehaviorProfile(agent_id)
            
        features = extract_features(profiles[agent_id], txn)
        score = model.predict_one(features)["anomaly_score"]
        
        val_scores.append(score)
        val_true.append(txn.get("is_anomaly", False))
        val_amounts.append(txn["amount_paise"] / 100.0) # Using INR value for cost analysis
        
        update_profile(profiles[agent_id], txn)
        
    # 5. Threshold Selection using Validation Set (Minimize Cost)
    best_threshold = 0.0
    best_cost = float('inf')
    best_val_metrics = None
    
    for th in config.threshold_grid:
        preds = [s >= th for s in val_scores]
        metrics = compute_metrics(val_true, preds, val_amounts, config)
        if metrics.expected_cost < best_cost:
            best_cost = metrics.expected_cost
            best_threshold = th
            best_val_metrics = metrics
            
    # Fallback to 0.5 if no variation
    if best_val_metrics is None:
        best_threshold = 0.5
        preds = [s >= 0.5 for s in val_scores]
        best_val_metrics = compute_metrics(val_true, preds, val_amounts, config)
        
    # 6. Score Test Set (Exactly Once)
    test_true = []
    test_scores = []
    test_amounts = []
    test_txns_annotated = []
    
    for txn in test_txns:
        agent_id = txn["agent_id"]
        if agent_id not in profiles:
            profiles[agent_id] = AgentBehaviorProfile(agent_id)
            
        features = extract_features(profiles[agent_id], txn)
        score = model.predict_one(features)["anomaly_score"]
        
        test_scores.append(score)
        test_true.append(txn.get("is_anomaly", False))
        test_amounts.append(txn["amount_paise"] / 100.0)
        
        test_txns_annotated.append({"txn": txn, "score": score, "pred": score >= best_threshold, "features": features})
        
        update_profile(profiles[agent_id], txn)
        
    test_preds = [s >= best_threshold for s in test_scores]
    test_metrics = compute_metrics(test_true, test_preds, test_amounts, config)
    
    # 7. Sub-population Metrics
    # a. Per-anomaly metrics
    per_anomaly_metrics = {}
    anomaly_types = set(t["txn"]["anomaly_type"] for t in test_txns_annotated if t["txn"].get("is_anomaly"))
    for a_type in anomaly_types:
        subset = [t for t in test_txns_annotated if t["txn"].get("anomaly_type") == a_type or not t["txn"].get("is_anomaly")]
        sub_true = [t["txn"].get("is_anomaly", False) for t in subset]
        sub_pred = [t["pred"] for t in subset]
        sub_amts = [t["txn"]["amount_paise"] / 100.0 for t in subset]
        # Only interested in True Positives and False Negatives for this specific anomaly class
        tp = sum(1 for tr, pr, t in zip(sub_true, sub_pred, subset) if tr and pr and t["txn"].get("anomaly_type") == a_type)
        fn = sum(1 for tr, pr, t in zip(sub_true, sub_pred, subset) if tr and not pr and t["txn"].get("anomaly_type") == a_type)
        total_a = tp + fn
        recall = tp / total_a if total_a > 0 else 0.0
        
        per_anomaly_metrics[a_type] = EvaluationMetrics(
            total=total_a, tp=tp, tn=0, fp=0, fn=fn, recall=recall
        )
        
    # b. Hard-negative metrics
    hard_negative_metrics = {}
    hn_types = set(t["txn"]["hard_negative_type"] for t in test_txns_annotated if t["txn"].get("hard_negative_type"))
    for hn_type in hn_types:
        subset = [t for t in test_txns_annotated if t["txn"].get("hard_negative_type") == hn_type]
        sub_pred = [t["pred"] for t in subset]
        fp = sum(1 for pr in sub_pred if pr)
        total_hn = len(subset)
        fpr = fp / total_hn if total_hn > 0 else 0.0
        hard_negative_metrics[hn_type] = fpr
        
    # c. Known vs Unseen Agent metrics
    known_subset = [t for t in test_txns_annotated if t["txn"]["agent_id"] not in unseen_agents]
    known_metrics = compute_metrics(
        [t["txn"].get("is_anomaly", False) for t in known_subset],
        [t["pred"] for t in known_subset],
        [t["txn"]["amount_paise"] / 100.0 for t in known_subset],
        config
    )
    
    unseen_subset = [t for t in test_txns_annotated if t["txn"]["agent_id"] in unseen_agents]
    unseen_metrics = compute_metrics(
        [t["txn"].get("is_anomaly", False) for t in unseen_subset],
        [t["pred"] for t in unseen_subset],
        [t["txn"]["amount_paise"] / 100.0 for t in unseen_subset],
        config
    )
    
    # 8. Baseline Comparisons
    # a. Baseline A: No governance (predict all False)
    baseline_a_preds = [False] * len(test_txns)
    baseline_a_metrics = compute_metrics(test_true, baseline_a_preds, test_amounts, config)
    
    # b. Baseline B: Simple Rules
    # Rule: amount_deviation > 3.0 OR payee_novelty == 1.0 OR time_of_day_deviation > 3.0 OR velocity_1h > 10
    baseline_b_preds = []
    for t in test_txns_annotated:
        f = t["features"]
        rule_flag = (
            f.get("amount_deviation", 0) > 3.0 or 
            f.get("payee_novelty", 0) == 1.0 or 
            f.get("time_of_day_deviation", 0) > 3.0 or 
            f.get("velocity_1h", 0) > 10.0
        )
        baseline_b_preds.append(rule_flag)
    
    baseline_b_metrics = compute_metrics(test_true, baseline_b_preds, test_amounts, config)
    
    # 9. Sensitivity Analysis
    # Re-evaluate Test Expected Cost assuming different base anomaly prevalence 
    # (By weighting TPs and FNs differently based on multiplier)
    sensitivity = {}
    current_prevalence = sum(test_true) / len(test_true) if len(test_true) > 0 else 0
    for assumed_prev in [0.01, 0.05, 0.1]:
        if current_prevalence > 0:
            multiplier = assumed_prev / current_prevalence
            # Scale TP and FN by multiplier
            adj_tp = test_metrics.tp * multiplier
            adj_fn = test_metrics.fn * multiplier
            adj_fp = test_metrics.fp * ((1 - assumed_prev) / (1 - current_prevalence))
            adj_tn = test_metrics.tn * ((1 - assumed_prev) / (1 - current_prevalence))
            
            adj_fp_cost = adj_fp * config.fp_cost
            adj_fn_cost = adj_fn * config.fn_cost
            adj_cost = adj_fp_cost + adj_fn_cost
            
            # Approximated evaluation metric for sensitivity
            sensitivity[assumed_prev] = EvaluationMetrics(
                expected_cost=adj_cost, fp_cost=adj_fp_cost, fn_cost=adj_fn_cost
            )
            
    from gateway.risk.anomaly_model import CANONICAL_FEATURES
    return EvaluationResult(
        model_version=model.model_version,
        feature_schema=CANONICAL_FEATURES,
        train_size=len(train_txns),
        validation_size=len(val_txns),
        test_size=len(test_txns),
        threshold=best_threshold,
        threshold_selection_method="Minimize Expected Cost (Validation Set)",
        validation_metrics=best_val_metrics,
        test_metrics=test_metrics,
        per_anomaly_metrics=per_anomaly_metrics,
        hard_negative_metrics=hard_negative_metrics,
        known_agent_metrics=known_metrics,
        unseen_agent_metrics=unseen_metrics,
        cost_configuration={"FP_COST": config.fp_cost, "FN_COST": config.fn_cost},
        validation_expected_cost=best_val_metrics.expected_cost,
        test_expected_cost=test_metrics.expected_cost,
        false_negative_exposure=test_metrics.fn_monetary_exposure,
        baseline_comparison={
            "No_Governance": baseline_a_metrics,
            "Simple_Rules": baseline_b_metrics
        },
        sensitivity_analysis=sensitivity
    )
