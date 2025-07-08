import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class MetricProcessor:
    """Process raw metrics into structured format"""

    async def process(
        self, raw_metrics: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Process raw metrics by type"""
        processed = {
            "block_metrics": [],
            "gas_metrics": [],
            "mempool_metrics": [],
        }

        for metric in raw_metrics:
            metric_type = metric.get("metric_type")

            if metric_type == "block":
                processed["block_metrics"].append(self._process_block_metric(metric))
            elif metric_type == "gas":
                processed["gas_metrics"].append(self._process_gas_metric(metric))
            elif metric_type == "mempool":
                processed["mempool_metrics"].append(
                    self._process_mempool_metric(metric)
                )

        return processed

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

    def _process_gas_metric(self, metric: Dict[str, Any]) -> Dict[str, Any]:
        """Process gas metric"""
        return {
            "timestamp": metric["timestamp"],
            "gas_price_wei": metric["gas_price_wei"],
            "gas_price_gwei": metric["gas_price_gwei"],
            "pending_transactions": metric.get("pending_transactions"),
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
