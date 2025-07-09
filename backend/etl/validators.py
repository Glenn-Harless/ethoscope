import logging
from typing import Any, Dict, List

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class GasMetricValidator(BaseModel):
    """Validate gas metrics data"""

    gas_price_gwei: float = Field(..., ge=0, le=10000)
    pending_transactions: int = Field(..., ge=0)

    @validator("gas_price_gwei")
    def validate_gas_price(cls, v):
        if v < 0:
            raise ValueError("Gas price cannot be negative")
        if v > 10000:  # 10,000 Gwei seems unrealistic
            logger.warning(f"Unusually high gas price: {v} Gwei")
        return v


class MetricValidator:
    """Validate metrics data quality"""

    @staticmethod
    def validate_metric(metric: Dict[str, Any], metric_type: str) -> bool:
        """Validate metric data quality"""
        try:
            # Check for required fields
            if "timestamp" not in metric:
                return False

            # Type-specific validation
            if metric_type == "gas":
                if metric.get("gas_price_gwei", 0) < 0:
                    return False
                if metric.get("gas_price_gwei", 0) > 10000:
                    logger.warning(f"Outlier gas price: {metric['gas_price_gwei']}")

            elif metric_type == "block":
                if metric.get("block_number", 0) <= 0:
                    return False
                if metric.get("transaction_count", 0) < 0:
                    return False

            elif metric_type == "mev":
                if metric.get("total_mev_revenue", 0) < 0:
                    return False

            return True

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False

    @staticmethod
    def detect_outliers(values: List[float], threshold: float = 3.0) -> List[int]:
        """Detect outliers using z-score method"""
        import numpy as np
        from scipy import stats

        if len(values) < 3:
            return []

        z_scores = np.abs(stats.zscore(values))
        return list(np.where(z_scores > threshold)[0])
