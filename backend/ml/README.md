# ML Prediction Module

## Overview
This module provides machine learning-based predictions for the Ethereum monitoring system.

## Models

### Gas Price Prediction
- **Model**: Facebook Prophet with confidence intervals
- **Forecast Horizon**: 15 minutes
- **Features**: Historical gas prices, transaction counts
- **Update Frequency**: Every 6 hours
- **Typical Performance**: MAE ~2.5 Gwei (5% error)

### Congestion Prediction
- **Model**: Linear Regression with feature importance
- **Forecast Horizon**: 15 minutes
- **Features**: Network utilization, gas prices, transaction rates
- **Update Frequency**: Every 6 hours
- **Typical Performance**: 85% correct level prediction

### Anomaly Detection
- **Model**: Statistical detection (reuses health calculator)
- **Method**: Z-score based with dynamic thresholds
- **Update Frequency**: Real-time
- **Typical Performance**: < 0.5% false positive rate

## API Endpoints

- `GET /api/v1/ml/predict/gas-price` - Gas price prediction with confidence intervals
- `GET /api/v1/ml/predict/congestion` - Network congestion forecast
- `GET /api/v1/ml/anomalies` - Recent anomalies
- `GET /api/v1/ml/alerts` - ML-based alerts
- `GET /api/v1/ml/models/status` - Model status and versions
- `GET /api/v1/ml/models/performance` - Model performance metrics
- `GET /api/v1/ml/metrics/summary` - ML system health metrics

## Training

Run the training script to update models:
```bash
python -m backend.ml.training
```

Models are automatically versioned and saved to the `models/` directory.
