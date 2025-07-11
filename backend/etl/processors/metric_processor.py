import logging
from datetime import datetime, timedelta
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from backend.models.database import SessionLocal
from backend.models.metrics import GasMetric

logger = logging.getLogger(__name__)


class MetricProcessor:
    """Process raw metrics into structured format with enhanced calculations"""

    def __init__(self):
        self.percentile_window_minutes = 60  # 1 hour window for percentile calculations

    async def process(self, raw_metrics: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
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
                    processed["block_metrics"].append(self._process_block_metric(metric))
                elif metric_type == "gas":
                    gas_metric = await self._process_gas_metric_with_percentiles(metric, db)
                    processed["gas_metrics"].append(gas_metric)
                elif metric_type == "mempool":
                    processed["mempool_metrics"].append(self._process_mempool_metric(metric))
                elif metric_type == "mev":
                    processed["mev_metrics"].append(self._process_mev_metric(metric))
                elif metric_type == "l2_network":
                    processed["l2_network_metrics"].append(self._process_l2_network_metric(metric))
                elif metric_type == "l2_transaction_costs":
                    processed["l2_transaction_costs"].append(
                        self._process_l2_transaction_cost(metric)
                    )
                elif metric_type == "l2_tvl":
                    processed["l2_tvl_metrics"].append(self._process_l2_tvl_metric(metric))
                elif metric_type == "mev_boost_stats":
                    # Store in a separate stats table
                    processed["mev_boost_stats"] = [self._process_mev_boost_stats(metric)]
                elif metric_type == "network_health":
                    processed["network_health_scores"].append(self._process_health_score(metric))

        finally:
            db.close()

        return processed

    async def _process_gas_metric_with_percentiles(
        self, metric: dict[str, Any], db: Session
    ) -> dict[str, Any]:
        """Process gas metric with percentile calculations"""
        # Get recent gas prices for percentile calculation
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=self.percentile_window_minutes)

        recent_gas_metrics = (
            db.query(GasMetric).filter(GasMetric.timestamp.between(start_time, end_time)).all()
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

    def _process_block_metric(self, metric: dict[str, Any]) -> dict[str, Any]:
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

    def _process_mempool_metric(self, metric: dict[str, Any]) -> dict[str, Any]:
        """Process mempool metric"""
        return {
            "timestamp": metric["timestamp"],
            "pending_count": metric["pending_count"],
            "avg_gas_price_gwei": metric.get("avg_gas_price_gwei"),
            "min_gas_price_gwei": metric.get("min_gas_price_gwei"),
            "max_gas_price_gwei": metric.get("max_gas_price_gwei"),
        }

    def _process_mev_metric(self, metric: dict[str, Any]) -> dict[str, Any]:
        """Process MEV metric"""
        # Calculate MEV gas price from gas used and total revenue if not provided
        gas_used = metric.get("gas_used", 0)
        total_mev_revenue = metric.get("total_mev_revenue", 0)

        # Estimate MEV gas price (very rough approximation)
        mev_gas_price_gwei = 0
        if gas_used > 0 and total_mev_revenue > 0:
            # Convert ETH to Wei, then to Gwei
            mev_gas_price_gwei = (total_mev_revenue * 1e18) / gas_used / 1e9

        return {
            "timestamp": metric["timestamp"],
            "block_number": metric["block_number"],
            "slot": metric.get("slot", 0),
            "total_mev_revenue": total_mev_revenue,
            "builder_pubkey": metric.get("builder_pubkey", ""),
            "proposer_fee_recipient": metric.get("proposer_fee_recipient", ""),
            "gas_used": gas_used,
            "gas_limit": metric.get("gas_limit", 0),
            "gas_utilization": metric.get("gas_utilization", 0),
            "mev_gas_price_gwei": mev_gas_price_gwei,
            "relay_source": metric.get("relay_source", ""),
            "block_hash": metric.get("block_hash", ""),
            "parent_hash": metric.get("parent_hash", ""),
        }

    def _process_l2_network_metric(self, metric: dict[str, Any]) -> dict[str, Any]:
        """Process L2 network metric, removing metric_type"""
        result = metric.copy()
        result.pop("metric_type", None)
        return result

    def _process_l2_transaction_cost(self, metric: dict[str, Any]) -> dict[str, Any]:
        """Process L2 transaction cost, removing metric_type"""
        result = metric.copy()
        result.pop("metric_type", None)
        return result

    def _process_mev_boost_stats(self, metric: dict[str, Any]) -> dict[str, Any]:
        """Process MEV boost stats, removing metric_type"""
        result = metric.copy()
        result.pop("metric_type", None)
        return result

    def _process_health_score(self, metric: dict[str, Any]) -> dict[str, Any]:
        """Process health score to match database schema"""
        # Check if this is a default health score (has gas_score directly)
        if "gas_score" in metric:
            # It's already in the correct format (from _default_health_score)
            return {
                "timestamp": metric["timestamp"],
                "overall_score": metric.get("overall_score", 50.0),
                "gas_score": metric.get("gas_score", 50.0),
                "congestion_score": metric.get("congestion_score", 50.0),
                "block_time_score": metric.get("block_time_score", 50.0),
                "mev_impact_score": metric.get("mev_impact_score", 50.0),
                "stability_score": metric.get("stability_score", 50.0),
                "health_status": metric.get("health_status", "Unknown"),
                "confidence_level": metric.get("confidence_level", 0.0),
            }
        else:
            # It's a detailed score with component_scores
            component_scores = metric.get("component_scores", {})

            return {
                "timestamp": metric["timestamp"],
                "overall_score": metric.get("overall_score", 50.0),
                "gas_score": component_scores.get("gas_efficiency", 50.0),
                "congestion_score": component_scores.get("network_stability", 50.0),
                "block_time_score": component_scores.get("block_production", 50.0),
                "mev_impact_score": component_scores.get("mev_fairness", 50.0),
                "stability_score": component_scores.get("validator_performance", 50.0),
                "health_status": metric.get("health_status", "Unknown"),
                "confidence_level": metric.get("confidence_level", 0.0),
            }

    def _process_l2_tvl_metric(self, metric: dict[str, Any]) -> dict[str, Any]:
        """Process L2 TVL metric, removing metric_type"""
        result = metric.copy()
        result.pop("metric_type", None)
        return result
