import math
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

CANONICAL_FEATURES = (
    "amount_deviation",
    "payee_novelty",
    "velocity_5m",
    "velocity_1h",
    "velocity_24h",
    "time_of_day_deviation",
    "weekday_deviation",
    "category_deviation",
    "daily_spend_deviation",
    "weekly_spend_deviation",
    "payee_concentration",
    "behavioral_distance",
)

class BehavioralAnomalyModel:
    """
    Unsupervised behavioral anomaly detector.
    
    Why IsolationForest was selected:
    - unsupervised (doesn't require anomaly labels during training)
    - suitable for anomaly detection on tabular data
    - lightweight (no neural network/tensor dependencies)
    - deterministic with fixed random_state
    
    This model strictly outputs a behavioral anomaly risk score.
    It does NOT make ALLOW/FLAG/BLOCK decisions, and it is NOT a fraud detection system by itself.
    anomaly_score is a behavioral risk score, not a calibrated probability.
    """
    
    def __init__(self):
        self.model_version = "behavioral_iforest_v1"
        self.model = IsolationForest(
            n_estimators=100,
            contamination="auto",
            random_state=42
        )
        self.is_fitted = False

    def _dict_to_array(self, feature_dict: dict) -> np.ndarray:
        """
        Safely converts a feature dictionary into a strictly ordered numpy array.
        Enforces canonical schema and prevents invalid float values.
        """
        missing = [f for f in CANONICAL_FEATURES if f not in feature_dict]
        if missing:
            raise ValueError(f"Missing features: {missing}")
            
        unexpected = [k for k in feature_dict.keys() if k not in CANONICAL_FEATURES]
        if unexpected:
            raise ValueError(f"Unexpected features: {unexpected}")
            
        vector = []
        for f in CANONICAL_FEATURES:
            val = feature_dict[f]
            if val is None or math.isnan(val) or math.isinf(val):
                raise ValueError(f"Feature '{f}' contains invalid value: {val}")
            vector.append(float(val))
            
        return np.array(vector, dtype=np.float32)

    def train(self, historical_feature_dicts: list[dict]) -> None:
        """
        Trains the unsupervised Isolation Forest baseline on point-in-time historical features.
        """
        if not historical_feature_dicts:
            raise ValueError("Training data cannot be empty.")
            
        matrix = []
        for fdict in historical_feature_dicts:
            matrix.append(self._dict_to_array(fdict))
            
        X = np.stack(matrix)
        self.model.fit(X)
        self.is_fitted = True

    def predict_one(self, feature_dict: dict) -> dict:
        """
        Scores a single point-in-time feature dictionary.
        Returns anomaly_score, prediction (NORMAL/ANOMALY), and model_version.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be trained before calling predict.")
            
        x = self._dict_to_array(feature_dict).reshape(1, -1)
        
        # decision_function typically bounded around [-0.5, 0.5]
        # negative -> anomaly, positive -> normal
        raw_score = float(self.model.decision_function(x)[0])
        
        # predict returns -1 for outliers (anomaly), 1 for inliers (normal)
        raw_pred = int(self.model.predict(x)[0])
        
        # Transform into a score where higher = more anomalous risk.
        # anomaly_score is a behavioral risk score, not a calibrated probability.
        # We shift by 0.5 and bound it to [0.0, 1.0] for deterministic normalized semantics.
        anomaly_score = max(0.0, min(1.0, 0.5 - raw_score))
        
        prediction = "ANOMALY" if raw_pred == -1 else "NORMAL"
        
        return {
            "anomaly_score": anomaly_score,
            "prediction": prediction,
            "model_version": self.model_version
        }

    def predict_batch(self, feature_dicts: list[dict]) -> list[dict]:
        """
        Scores a list of feature dictionaries in batch.
        """
        if not self.is_fitted:
            raise RuntimeError("Model must be trained before calling predict.")
            
        if not feature_dicts:
            return []
            
        X = np.stack([self._dict_to_array(f) for f in feature_dicts])
        raw_scores = self.model.decision_function(X)
        raw_preds = self.model.predict(X)
        
        results = []
        for s, p in zip(raw_scores, raw_preds):
            anomaly_score = max(0.0, min(1.0, 0.5 - float(s)))
            prediction = "ANOMALY" if int(p) == -1 else "NORMAL"
            results.append({
                "anomaly_score": anomaly_score,
                "prediction": prediction,
                "model_version": self.model_version
            })
        return results

    def save(self, filepath: str) -> None:
        """
        Serialize the local trusted model using joblib.
        """
        if not self.is_fitted:
            raise RuntimeError("Cannot save an unfitted model.")
        joblib.dump(
            {"model": self.model, "model_version": self.model_version}, 
            filepath
        )

    def load(self, filepath: str) -> None:
        """
        Load a serialized local model.
        WARNING: Serialized model files must only be loaded from trusted sources 
        because joblib/pickle-based deserialization can execute arbitrary Python code.
        """
        data = joblib.load(filepath)
        if data["model_version"] != self.model_version:
            raise ValueError(f"Version mismatch: expected {self.model_version}, got {data['model_version']}")
        self.model = data["model"]
        self.is_fitted = True
