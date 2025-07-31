from datetime import datetime

import numpy as np
import pandas as pd

from backend.ml.predictors import CongestionPredictor, GasPricePredictor


def test_gas_price_predictor():
    """Test gas price prediction with confidence intervals"""
    # Create sample data
    dates = pd.date_range(end=datetime.utcnow(), periods=1000, freq="1min")
    data = pd.DataFrame(
        {"gas_price_gwei": np.random.normal(50, 10, 1000) + np.sin(np.arange(1000) * 0.01) * 20},
        index=dates,
    )

    # Train predictor
    predictor = GasPricePredictor()
    metrics = predictor.train(data)

    assert predictor.is_trained
    assert "mae" in metrics
    assert metrics["mae"] < 20  # Reasonable MAE

    # Make prediction
    prediction = predictor.predict(data)
    assert "predicted_price" in prediction
    assert "confidence_interval" in prediction
    assert prediction["confidence_interval"]["lower"] < prediction["predicted_price"]
    assert prediction["confidence_interval"]["upper"] > prediction["predicted_price"]


def test_congestion_predictor():
    """Test congestion prediction with feature importance"""
    # Create sample data
    dates = pd.date_range(end=datetime.utcnow(), periods=500, freq="1min")
    data = pd.DataFrame(
        {
            "gas_used": np.random.uniform(10_000_000, 15_000_000, 500),
            "gas_limit": np.full(500, 30_000_000),
            "transaction_count": np.random.poisson(150, 500),
            "gas_price_gwei": np.random.normal(50, 10, 500),
        },
        index=dates,
    )

    # Train predictor
    predictor = CongestionPredictor()
    metrics = predictor.train(data)

    assert predictor.is_trained
    assert "r2_score" in metrics
    assert metrics["r2_score"] > 0  # Model learned something

    # Make prediction
    prediction = predictor.predict(data)
    assert "congestion_level" in prediction
    assert prediction["congestion_level"] in ["low", "medium", "high", "critical"]
    assert "feature_importance" in prediction
    assert len(prediction["feature_importance"]) > 0


def test_model_versioning():
    """Test model versioning works correctly"""
    predictor = GasPricePredictor()
    assert predictor.version  # Version should be set
    assert len(predictor.version) == 15  # Format: YYYYMMDD_HHMMSS
