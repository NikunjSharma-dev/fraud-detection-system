"""
ML Prediction Module — Real-time fraud risk scoring.

Combines Isolation Forest anomaly score + XGBoost probability
into a unified risk score in [0, 1].
"""
import numpy as np
import joblib
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

MODELS_DIR = Path(__file__).parent / "models"


@dataclass
class FraudPrediction:
    risk_score: float          # 0.0 = safe, 1.0 = highly suspicious
    is_fraudulent: bool        # True if risk_score >= threshold
    iso_anomaly: int           # -1 = anomaly, 1 = normal (from Isolation Forest)
    xgb_probability: float     # XGBoost fraud probability
    threshold: float = 0.55    # Decision threshold


class FraudPredictor:
    """
    Wraps both ML models and exposes a single .predict() method.
    Models are loaded lazily and cached as class-level attributes.
    """
    _iso_forest = None
    _xgb_model  = None
    _scaler     = None
    _features   = None

    @classmethod
    def load(cls):
        """Load model artifacts from disk. Safe to call multiple times."""
        if cls._iso_forest is None:
            try:
                cls._iso_forest = joblib.load(MODELS_DIR / "isolation_forest.pkl")
                cls._xgb_model  = joblib.load(MODELS_DIR / "xgboost_classifier.pkl")
                cls._scaler     = joblib.load(MODELS_DIR / "scaler.pkl")
                cls._features   = joblib.load(MODELS_DIR / "feature_columns.pkl")
                print("✅ ML models loaded successfully.")
            except FileNotFoundError:
                print("⚠️  Model files not found. Run: python app/ml/train.py")
                cls._iso_forest = None

    @classmethod
    def predict(
        cls,
        amount: float,
        geo_velocity: float,
        tx_count_10m: int,
        hour_of_day: int,
        is_weekend: int,
        amount_z_score: float,
    ) -> Optional[FraudPrediction]:
        """
        Score a single transaction.

        Returns None if models aren't loaded (fallback to rule-based only).
        """
        if cls._iso_forest is None:
            return None

        features = np.array([[
            amount,
            geo_velocity,
            tx_count_10m,
            hour_of_day,
            is_weekend,
            amount_z_score,
        ]])

        # Scale features
        features_scaled = cls._scaler.transform(features)

        # Isolation Forest: returns -1 (anomaly) or 1 (normal)
        iso_result = cls._iso_forest.predict(features_scaled)[0]

        # XGBoost: fraud probability
        xgb_proba = cls._xgb_model.predict_proba(features_scaled)[0][1]

        # Combine: weight XGBoost more heavily (it's supervised)
        # Isolation Forest anomaly contributes a 0.2 bump
        iso_contribution = 0.2 if iso_result == -1 else 0.0
        risk_score = min(1.0, (0.8 * xgb_proba) + iso_contribution)

        return FraudPrediction(
            risk_score=round(risk_score, 4),
            is_fraudulent=risk_score >= 0.55,
            iso_anomaly=iso_result,
            xgb_probability=round(float(xgb_proba), 4),
        )