import pytest
from gateway.risk.data_generator import generate_dataset, generate_simulation_profiles
from gateway.risk.anomaly_model import BehavioralAnomalyModel
from gateway.risk.evaluation import EvaluationConfig, evaluate_model, compute_metrics, EvaluationMetrics

def test_compute_metrics_zero_division():
    config = EvaluationConfig()
    # Test with empty lists
    metrics = compute_metrics([], [], [], config)
    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0
    assert metrics.fpr == 0.0
    assert metrics.fnr == 0.0
    assert metrics.expected_cost == 0.0
    
    # Test with all negatives (no TP, no FN) -> recall zero div
    metrics = compute_metrics([False, False], [False, False], [10.0, 10.0], config)
    assert metrics.recall == 0.0
    
def test_compute_metrics_correctness():
    config = EvaluationConfig(fp_cost=10, fn_cost=100)
    y_true = [True, True, False, False]
    y_pred = [True, False, True, False]
    amounts = [50.0, 100.0, 20.0, 10.0]
    
    # TP = 1 (idx 0)
    # FN = 1 (idx 1) - amount 100.0
    # FP = 1 (idx 2) - amount 20.0
    # TN = 1 (idx 3)
    
    metrics = compute_metrics(y_true, y_pred, amounts, config)
    assert metrics.tp == 1
    assert metrics.fn == 1
    assert metrics.fp == 1
    assert metrics.tn == 1
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5
    assert metrics.fpr == 0.5
    assert metrics.fnr == 0.5
    
    assert metrics.fp_cost == 10
    assert metrics.fn_cost == 100
    assert metrics.expected_cost == 110
    assert metrics.fn_monetary_exposure == 100.0

def test_evaluation_pipeline_end_to_end():
    # Use a small dataset for fast testing
    dataset = generate_dataset(seed=42, num_agents=5, num_transactions=200)

    
    model = BehavioralAnomalyModel()
    config = EvaluationConfig(threshold_grid=[0.0, 0.4, 0.5, 0.6, 1.0])
    
    result = evaluate_model(model, dataset, config)
    
    assert result.model_version == "behavioral_iforest_v1"
    assert result.train_size + result.validation_size + result.test_size == 200
    
    # Threshold should be from the grid
    assert result.threshold in config.threshold_grid
    
    # Check cost structure
    assert result.cost_configuration["FP_COST"] == 10.0
    assert result.cost_configuration["FN_COST"] == 100.0
    
    # Ensure baseline comparisons are generated
    assert "No_Governance" in result.baseline_comparison
    assert "Simple_Rules" in result.baseline_comparison
    
    # Ensure hard negative metrics exist
    assert isinstance(result.hard_negative_metrics, dict)
    
    # Check sensitivity if test set had anomalies
    if result.test_metrics.fn + result.test_metrics.tp > 0:
        assert 0.01 in result.sensitivity_analysis
        assert 0.05 in result.sensitivity_analysis
