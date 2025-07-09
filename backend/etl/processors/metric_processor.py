import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
from sqlalchemy.orm import Session

from backend.models.database import SessionLocal
from backend.models.metrics import GasMetric

logger = logging.getLogger(__name__)


class MetricProcessor:
    """Process raw metrics into structured format with enhanced calculations"""

    def __init__(self):
        self.percentile_window_minutes = 60  # 1 hour window for percentile calculations

    async def process(
        self, raw_metrics: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Process raw metrics by type with enhanced calculations"""
        processed = {
            "block_metrics": [],
            "gas_metrics": [],
            "mempool_metrics": [],
            "mev_metrics": [],
            "l2_network_metrics": [],
            "l2_transaction_costs": [],
            "l2_tvl_metrics": [],
            "network_health_scores": [],
        }

        db = SessionLocal()
        try:
            for metric in raw_metrics:
                metric_type = metric.get("metric_type")

                if metric_type == "block":
                    processed["block_metrics"].append(
                        self._process_block_metric(metric)
                    )
                elif metric_type == "gas":
                    gas_metric = await self._process_gas_metric_with_percentiles(
                        metric, db
                    )
                    processed["gas_metrics"].append(gas_metric)
                elif metric_type == "mempool":
                    processed["mempool_metrics"].append(
                        self._process_mempool_metric(metric)
                    )
                elif metric_type == "mev":
                    processed["mev_metrics"].append(self._process_mev_metric(metric))
                elif metric_type == "l2_network":
                    processed["l2_network_metrics"].append(metric)
                elif metric_type == "l2_transaction_costs":
                    processed["l2_transaction_costs"].append(metric)
                elif metric_type == "l2_tvl":
                    processed["l2_tvl_metrics"].append(metric)
                elif metric_type == "mev_boost_stats":
                    # Store in a separate stats table
                    processed["mev_boost_stats"] = [metric]
                elif metric_type == "network_health":
                    processed["network_health_scores"].append(metric)

        finally:
            db.close()

        return processed

    async def _process_gas_metric_with_percentiles(
        self, metric: Dict[str, Any], db: Session
    ) -> Dict[str, Any]:
        """Process gas metric with percentile calculations"""
        # Get recent gas prices for percentile calculation
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=self.percentile_window_minutes)

        recent_gas_metrics = (
            db.query(GasMetric)
            .filter(GasMetric.timestamp.between(start_time, end_time))
            .all()
        )

        # Add current metric to the list for calculation
        gas_prices = [m.gas_price_gwei for m in recent_gas_metrics]
        gas_prices.append(metric["gas_price_gwei"])

        # Calculate percentiles
        percentiles = {}
        if len(gas_prices) >= 4:  # Need at least 4 data points
            percentiles = {
                "gas_price_p25": float(np.percentile(gas_prices, 25)),
                "gas_price_p50": float(np.percentile(gas_prices, 50)),
                "gas_price_p75": float(np.percentile(gas_prices, 75)),
                "gas_price_p95": float(np.percentile(gas_prices, 95)),
            }

        return {
            "timestamp": metric["timestamp"],
            "gas_price_wei": metric["gas_price_wei"],
            "gas_price_gwei": metric["gas_price_gwei"],
            "pending_transactions": metric.get("pending_transactions"),
            **percentiles,  # Add percentile fields
        }

    def _process_block_metric(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        """Process block metric"""
        return {
            "timestamp": metric["timestamp"],
            "block_number": metric["block_number"],
            "block_timestamp": metric["block_timestamp"],
            "gas_used": metric["gas_used"],
            "gas_limit": metric["gas_limit"],
            "transaction_count": metric["transaction_count"],
            "base_fee_per_gas": metric.get("base_fee_per_gas"),
            "difficulty": metric.get("difficulty"),
        }

    def _process_mempool_metric(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        """Process mempool metric"""
        return {
            "timestamp": metric["timestamp"],
            "pending_count": metric["pending_count"],
            "avg_gas_price_gwei": metric.get("avg_gas_price_gwei"),
            "min_gas_price_gwei": metric.get("min_gas_price_gwei"),
            "max_gas_price_gwei": metric.get("max_gas_price_gwei"),
        }

    def _process_mev_metric(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        """Process MEV metric"""
        return {
            "timestamp": metric["timestamp"],
            "block_number": metric["block_number"],
            "mev_gas_price_gwei": metric.get("mev_gas_price_gwei", 0),
            "coinbase_transfer": metric.get("coinbase_transfer", 0),
            "total_mev_revenue": metric.get("total_mev_revenue", 0),
            "bundle_count": metric.get("bundle_count", 0),
            "sandwich_attack_count": metric.get("sandwich_attack_count", 0),
            "sandwich_attack_profit_eth": metric.get("sandwich_attack_profit_eth", 0),
            "builder_address": metric.get("builder_address", ""),
        }
