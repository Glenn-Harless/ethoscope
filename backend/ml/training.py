#!/usr/bin/env python3
"""Simple training script for ML models"""

import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from backend.ml.predictors import CongestionPredictor, GasPricePredictor
from backend.models.database import SessionLocal
from backend.models.metrics import BlockMetric, GasMetric

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def train_models():
    """Train all ML models with recent data"""
    db = SessionLocal()

    try:
        # Get training data (last 7 days)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)

        logger.info(f"Loading data from {start_time} to {end_time}")

        # Load gas metrics
        gas_metrics = (
            db.query(GasMetric)
            .filter(GasMetric.timestamp.between(start_time, end_time))
            .order_by(GasMetric.timestamp)
            .all()
        )

        logger.info(f"Loaded {len(gas_metrics)} gas metrics")

        if len(gas_metrics) < 1000:
            logger.warning("Insufficient gas data for training")
            return

        # Prepare gas data
        gas_data = pd.DataFrame(
            [{"timestamp": m.timestamp, "gas_price_gwei": m.gas_price_gwei} for m in gas_metrics]
        ).set_index("timestamp")

        # Train gas predictor
        logger.info("Training gas price predictor...")
        gas_predictor = GasPricePredictor()
        gas_metrics_result = gas_predictor.train(gas_data)
        gas_predictor.save()
        logger.info(f"Gas predictor trained: {gas_metrics_result}")

        # Load block metrics for congestion
        block_metrics = (
            db.query(BlockMetric)
            .filter(BlockMetric.timestamp.between(start_time, end_time))
            .order_by(BlockMetric.timestamp)
            .all()
        )

        logger.info(f"Loaded {len(block_metrics)} block metrics")

        if len(block_metrics) < 1000:
            logger.warning("Insufficient block data for training")
            return

        # Prepare congestion data
        block_data = pd.DataFrame(
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

        # Merge with gas data
        congestion_data = block_data.join(gas_data, how="left")
        congestion_data["gas_price_gwei"].fillna(method="ffill", inplace=True)

        # Train congestion predictor
        logger.info("Training congestion predictor...")
        congestion_predictor = CongestionPredictor()
        congestion_metrics = congestion_predictor.train(congestion_data)
        congestion_predictor.save()
        logger.info(f"Congestion predictor trained: {congestion_metrics}")

        logger.info("Training completed successfully!")

        # Log summary
        logger.info("\n=== Training Summary ===")
        logger.info(f"Gas Predictor MAE: {gas_metrics_result['mae']:.2f} Gwei")
        logger.info(f"Congestion R² Score: {congestion_metrics['r2_score']:.3f}")
        logger.info(f"Models saved to: {Path('models').absolute()}")

    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(train_models())
