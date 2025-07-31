import logging
from datetime import datetime, timedelta

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.ml.predictors import AnomalyDetector, CongestionPredictor, GasPricePredictor
from backend.models.database import get_db
from backend.models.metrics import BlockMetric, GasMetric
from backend.models.ml_alerts import MLAlert

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize predictors (in production, use dependency injection)
anomaly_detector = AnomalyDetector()
gas_predictor = GasPricePredictor()
congestion_predictor = CongestionPredictor()

# Track predictions for accuracy monitoring
prediction_history = []


@router.get("/anomalies")
async def get_anomalies(hours: int = 1, db: Session = Depends(get_db)):
    """Get recent anomalies"""
    anomalies = await anomaly_detector.detect_anomalies(db, lookback_hours=hours)
    return {"anomalies": anomalies, "count": len(anomalies), "time_range_hours": hours}


@router.get("/predict/gas-price")
async def predict_gas_price(db: Session = Depends(get_db)):
    """Predict gas price 15 minutes ahead with confidence intervals"""
    try:
        # Get recent data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=2)

        gas_metrics = (
            db.query(GasMetric)
            .filter(GasMetric.timestamp.between(start_time, end_time))
            .order_by(GasMetric.timestamp)
            .all()
        )

        if len(gas_metrics) < 60:
            raise HTTPException(status_code=400, detail="Insufficient data for prediction")

        # Prepare data
        data = pd.DataFrame(
            [{"timestamp": m.timestamp, "gas_price_gwei": m.gas_price_gwei} for m in gas_metrics]
        ).set_index("timestamp")

        # Check if model is trained
        if not gas_predictor.is_trained:
            try:
                gas_predictor.load()
            except FileNotFoundError:
                raise HTTPException(status_code=503, detail="Model not trained yet")

        # Make prediction
        current_price = float(data["gas_price_gwei"].iloc[-1])
        prediction_result = gas_predictor.predict(data)
        predicted_price = prediction_result["predicted_price"]

        # Store prediction for accuracy tracking
        prediction_history.append(
            {
                "timestamp": datetime.utcnow(),
                "predicted_at": datetime.utcnow() + timedelta(minutes=15),
                "current_price": current_price,
                "predicted_price": predicted_price,
            }
        )

        # Create alert if significant increase predicted
        if predicted_price > current_price * 1.2:  # 20% increase
            alert = MLAlert(
                alert_type="prediction",
                severity="high" if predicted_price > current_price * 1.5 else "medium",
                metric_name="gas_price",
                metric_value=current_price,
                predicted_value=predicted_price,
                message=(
                    f"Gas price expected to rise from {current_price:.1f} to "
                    f"{predicted_price:.1f} Gwei"
                ),
            )
            db.add(alert)
            db.commit()

            # TODO: Send WebSocket notification
            # await ws_manager.broadcast_ml_alert(alert)

        return {
            "current_price": current_price,
            "predicted_price": predicted_price,
            "confidence_interval": prediction_result["confidence_interval"],
            "prediction_time": datetime.utcnow() + timedelta(minutes=15),
            "change_percent": (predicted_price / current_price - 1) * 100,
            "model_version": gas_predictor.version,
        }

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Prediction temporarily unavailable",
            headers={"Retry-After": "60"},
        )


@router.get("/predict/congestion")
async def predict_congestion(db: Session = Depends(get_db)):
    """Predict network congestion with feature importance"""
    try:
        # Get recent block metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)

        block_metrics = (
            db.query(BlockMetric)
            .filter(BlockMetric.timestamp.between(start_time, end_time))
            .order_by(BlockMetric.timestamp)
            .all()
        )

        if not block_metrics:
            raise HTTPException(status_code=404, detail="No recent data available")

        # Prepare data
        data = pd.DataFrame(
            [
                {
                    "timestamp": m.timestamp,
                    "gas_used": m.gas_used,
                    "gas_limit": m.gas_limit,
                    "transaction_count": m.transaction_count,
                }
                for m in block_metrics
            ]
        ).set_index("timestamp")

        # Get gas prices for features
        gas_metrics = (
            db.query(GasMetric)
            .filter(GasMetric.timestamp.between(start_time, end_time))
            .order_by(GasMetric.timestamp)
            .all()
        )

        if gas_metrics:
            gas_df = pd.DataFrame(
                [
                    {"timestamp": m.timestamp, "gas_price_gwei": m.gas_price_gwei}
                    for m in gas_metrics
                ]
            ).set_index("timestamp")
            data = data.join(gas_df, how="left")
            data["gas_price_gwei"].fillna(method="ffill", inplace=True)

        # Check if model is trained
        if not congestion_predictor.is_trained:
            try:
                congestion_predictor.load()
            except FileNotFoundError:
                raise HTTPException(status_code=503, detail="Model not trained yet")

        # Make prediction
        prediction = congestion_predictor.predict(data)

        # Create alert if high congestion predicted
        if prediction["congestion_level"] in ["high", "critical"]:
            alert = MLAlert(
                alert_type="prediction",
                severity=prediction["congestion_level"],
                metric_name="network_congestion",
                predicted_value=prediction["predicted_utilization"],
                message=prediction["description"],
            )
            db.add(alert)
            db.commit()

        return {
            **prediction,
            "current_utilization": float(data["gas_used"].iloc[-1] / data["gas_limit"].iloc[-1]),
            "prediction_time": datetime.utcnow() + timedelta(minutes=15),
            "model_version": congestion_predictor.version,
        }

    except Exception as e:
        logger.error(f"Congestion prediction failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Prediction temporarily unavailable",
            headers={"Retry-After": "60"},
        )


@router.get("/alerts")
async def get_alerts(limit: int = 50, db: Session = Depends(get_db)):
    """Get recent ML alerts"""
    alerts = db.query(MLAlert).order_by(MLAlert.timestamp.desc()).limit(limit).all()

    return [
        {
            "id": str(alert.id),
            "timestamp": alert.timestamp,
            "type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "metric_name": alert.metric_name,
            "metric_value": alert.metric_value,
            "predicted_value": alert.predicted_value,
        }
        for alert in alerts
    ]


@router.get("/models/status")
async def get_model_status():
    """Get status of ML models with versions"""
    return {
        "anomaly_detector": {
            "trained": anomaly_detector.is_trained,
            "type": "statistical",
            "version": "live",  # Always up-to-date
        },
        "gas_predictor": {
            "trained": gas_predictor.is_trained,
            "type": "prophet",
            "version": gas_predictor.version,
            "training_metrics": gas_predictor.training_metrics,
        },
        "congestion_predictor": {
            "trained": congestion_predictor.is_trained,
            "type": "linear_regression",
            "version": congestion_predictor.version,
            "training_metrics": congestion_predictor.training_metrics,
        },
    }


@router.get("/models/performance")
async def get_model_performance(db: Session = Depends(get_db)):
    """Get recent prediction accuracy metrics"""
    # Calculate gas price prediction accuracy from history
    recent_predictions = [
        p
        for p in prediction_history
        if p["predicted_at"] < datetime.utcnow()  # Only completed predictions
    ][-20:]  # Last 20 predictions

    if not recent_predictions:
        return {"message": "No completed predictions yet"}

    # Get actual prices at prediction times
    accuracies = []
    for pred in recent_predictions:
        actual = (
            db.query(GasMetric)
            .filter(
                GasMetric.timestamp >= pred["predicted_at"] - timedelta(seconds=30),
                GasMetric.timestamp <= pred["predicted_at"] + timedelta(seconds=30),
            )
            .first()
        )

        if actual:
            error = abs(pred["predicted_price"] - actual.gas_price_gwei) / actual.gas_price_gwei
            accuracies.append(
                {
                    "predicted": pred["predicted_price"],
                    "actual": actual.gas_price_gwei,
                    "error_percent": error * 100,
                }
            )

    if accuracies:
        avg_error = sum(a["error_percent"] for a in accuracies) / len(accuracies)
        return {
            "gas_price_predictor": {
                "avg_error_percent": avg_error,
                "samples_evaluated": len(accuracies),
                "recent_predictions": accuracies[-5:],  # Show last 5
            }
        }

    return {"message": "Insufficient data for performance metrics"}


@router.get("/metrics/summary")
async def get_ml_metrics_summary(db: Session = Depends(get_db)):
    """Get ML system health metrics"""
    # Count recent predictions and alerts
    day_ago = datetime.utcnow() - timedelta(days=1)

    alerts_24h = db.query(MLAlert).filter(MLAlert.timestamp > day_ago).count()

    # Get anomalies count
    anomalies_24h = len(await anomaly_detector.detect_anomalies(db, 24))

    # Get last training time from model metadata
    training_times = {}
    for name, predictor in [
        ("gas_predictor", gas_predictor),
        ("congestion_predictor", congestion_predictor),
    ]:
        try:
            metadata_path = predictor.model_path / "metadata.pkl"
            if metadata_path.exists():
                import joblib

                metadata = joblib.load(metadata_path)
                training_times[name] = metadata.get("trained_at", "unknown")
        except Exception:
            training_times[name] = "unknown"

    return {
        "alerts_24h": alerts_24h,
        "anomalies_detected_24h": anomalies_24h,
        "models_last_trained": training_times,
        "prediction_requests_24h": len([p for p in prediction_history if p["timestamp"] > day_ago]),
        "system_status": "healthy",
    }
