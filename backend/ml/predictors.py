import logging
from datetime import datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error

from backend.etl.processors.health_score_calculator import DynamicNetworkHealthCalculator

from .models import BasePredictor

logger = logging.getLogger(__name__)


class AnomalyDetector(BasePredictor):
    """Wrapper around existing statistical anomaly detection"""

    def __init__(self):
        super().__init__("anomaly_detector")
        self.health_calculator = DynamicNetworkHealthCalculator()

    async def detect_anomalies(self, db, lookback_hours: int = 1) -> list[dict[str, Any]]:
        """Detect anomalies using existing health calculator logic"""
        end_time = datetime.utcnow()

        # Use the existing anomaly detection
        anomalies = await self.health_calculator._detect_anomalies(db, end_time)

        # Filter to requested time window
        start_time = end_time - timedelta(hours=lookback_hours)
        recent_anomalies = [a for a in anomalies if a["timestamp"] >= start_time]

        return recent_anomalies

    def train(self, data: pd.DataFrame) -> dict[str, float]:
        """No training needed - uses statistical methods"""
        self.is_trained = True
        return {"status": "ready", "method": "statistical"}

    def predict(self, data: pd.DataFrame) -> Any:
        """Not used - detection is done via detect_anomalies"""
        pass


class GasPricePredictor(BasePredictor):
    """Simple gas price predictor using Prophet with confidence intervals"""

    def __init__(self):
        super().__init__("gas_price_predictor")
        self.prediction_horizon = 15  # minutes

    def prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for Prophet"""
        prophet_df = pd.DataFrame({"ds": data.index, "y": data["gas_price_gwei"]})

        # Add simple features if available
        if "transaction_count" in data.columns:
            prophet_df["tx_count"] = data["transaction_count"]

        return prophet_df

    def train(self, data: pd.DataFrame) -> dict[str, float]:
        """Train Prophet model"""
        prophet_df = self.prepare_data(data)

        # Initialize Prophet with simple settings
        self.model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,
            interval_width=0.95,  # 95% confidence interval
        )

        # Add regressors if available
        if "tx_count" in prophet_df.columns:
            self.model.add_regressor("tx_count")

        # Fit model
        self.model.fit(prophet_df)
        self.is_trained = True

        # Simple evaluation
        forecast = self.model.predict(prophet_df)
        mae = mean_absolute_error(prophet_df["y"], forecast["yhat"])

        self.training_metrics = {
            "mae": float(mae),
            "samples": len(prophet_df),
            "mean_gas_price": float(prophet_df["y"].mean()),
        }

        logger.info(f"Gas price predictor trained with MAE: {mae:.2f}")

        return self.training_metrics

    def predict(self, data: pd.DataFrame) -> dict[str, float]:
        """Predict gas price 15 minutes ahead with confidence intervals"""
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        # Create future dataframe
        future = self.model.make_future_dataframe(periods=self.prediction_horizon, freq="min")

        # Add regressor values (simplified - use last known values)
        if "tx_count" in self.model.extra_regressors:
            future["tx_count"] = data["transaction_count"].iloc[-1]

        # Make prediction
        forecast = self.model.predict(future)

        # Return prediction with confidence intervals
        last_forecast = forecast.iloc[-1]
        return {
            "predicted_price": float(last_forecast["yhat"]),
            "confidence_interval": {
                "lower": float(last_forecast["yhat_lower"]),
                "upper": float(last_forecast["yhat_upper"]),
            },
            "prediction_horizon_minutes": self.prediction_horizon,
        }


class CongestionPredictor(BasePredictor):
    """Simple congestion predictor using linear regression with feature importance"""

    def __init__(self):
        super().__init__("congestion_predictor")
        self.model = LinearRegression()
        self.feature_names = []

    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare simple features for congestion prediction"""
        features = pd.DataFrame()

        # Basic features
        if "gas_used" in data.columns and "gas_limit" in data.columns:
            features["utilization"] = data["gas_used"] / data["gas_limit"]
            features["utilization_ma"] = features["utilization"].rolling(5, min_periods=1).mean()

        if "gas_price_gwei" in data.columns:
            features["gas_price_normalized"] = (
                data["gas_price_gwei"] / data["gas_price_gwei"].rolling(20, min_periods=1).mean()
            )

        if "transaction_count" in data.columns:
            features["tx_rate_ma"] = data["transaction_count"].rolling(5, min_periods=1).mean()

        # Time features
        features["hour"] = pd.to_datetime(data.index).hour
        features["day_of_week"] = pd.to_datetime(data.index).dayofweek

        # Store feature names
        self.feature_names = features.columns.tolist()

        return features.fillna(0)

    def get_feature_importance(self) -> dict[str, float]:
        """Get feature importance from linear regression"""
        if not self.is_trained or not self.feature_names:
            return {}

        # Get absolute importance
        importance = np.abs(self.model.coef_)
        # Normalize to percentages
        importance = importance / importance.sum() * 100

        return dict(zip(self.feature_names, importance, strict=False))

    def train(self, data: pd.DataFrame) -> dict[str, float]:
        """Train congestion model"""
        features = self.prepare_features(data)

        # Create target (future utilization)
        target = features["utilization"].shift(-15)  # 15 min ahead

        # Remove NaN rows
        valid_idx = ~target.isna()
        X_train = features[valid_idx]
        y_train = target[valid_idx]

        if len(X_train) < 100:
            raise ValueError("Insufficient data for training")

        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True

        # Calculate metrics
        train_score = self.model.score(X_train, y_train)
        feature_importance = self.get_feature_importance()

        self.training_metrics = {
            "r2_score": float(train_score),
            "samples": len(X_train),
            "top_feature": max(feature_importance, key=feature_importance.get)
            if feature_importance
            else "unknown",
        }

        return self.training_metrics

    def predict(self, data: pd.DataFrame) -> dict[str, Any]:
        """Predict congestion level"""
        if not self.is_trained:
            raise ValueError("Model must be trained first")

        features = self.prepare_features(data)
        last_features = features.iloc[-1:].values

        # Predict utilization
        predicted_utilization = float(self.model.predict(last_features)[0])
        predicted_utilization = max(0, min(1, predicted_utilization))  # Clamp to [0, 1]

        # Convert to congestion level
        if predicted_utilization < 0.7:
            level = "low"
            description = "Network operating normally"
        elif predicted_utilization < 0.85:
            level = "medium"
            description = "Moderate congestion expected"
        elif predicted_utilization < 0.95:
            level = "high"
            description = "High congestion expected"
        else:
            level = "critical"
            description = "Critical congestion expected"

        return {
            "predicted_utilization": predicted_utilization,
            "congestion_level": level,
            "description": description,
            "feature_importance": self.get_feature_importance(),
        }
