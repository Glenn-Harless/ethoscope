import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np
from scipy import stats

from backend.models.database import SessionLocal as Session
from backend.models.metrics import BlockMetric, GasMetric
from backend.models.mev_metrics import MEVMetric

logger = logging.getLogger(__name__)


class DynamicNetworkHealthCalculator:
    """Advanced network health calculator with dynamic baselines and ML-ready
    features"""

    def __init__(self):
        self.weights = {
            "gas_efficiency": 0.25,
            "network_stability": 0.20,
            "mev_fairness": 0.15,
            "block_production": 0.15,
            "mempool_health": 0.15,
            "validator_performance": 0.10,
        }

        # Dynamic baseline windows
        self.baseline_windows = {
            "short": timedelta(hours=1),
            "medium": timedelta(hours=24),
            "long": timedelta(days=7),
        }

        # Anomaly detection thresholds
        self.z_score_threshold = 3.0
        self.iqr_multiplier = 1.5

    async def calculate_health_score(self, db: Session) -> dict[str, Any]:
        """Calculate comprehensive network health with dynamic baselines"""
        try:
            end_time = datetime.utcnow()

            # Calculate individual component scores
            gas_efficiency = await self._calculate_gas_efficiency_score(db, end_time)
            network_stability = await self._calculate_network_stability_score(db, end_time)
            mev_fairness = await self._calculate_mev_fairness_score(db, end_time)
            block_production = await self._calculate_block_production_score(db, end_time)
            mempool_health = await self._calculate_mempool_health_score(db, end_time)
            validator_performance = await self._calculate_validator_performance_score(db, end_time)

            # Calculate weighted overall score
            scores = {
                "gas_efficiency": gas_efficiency,
                "network_stability": network_stability,
                "mev_fairness": mev_fairness,
                "block_production": block_production,
                "mempool_health": mempool_health,
                "validator_performance": validator_performance,
            }

            overall_score = sum(self.weights[key] * value["score"] for key, value in scores.items())

            # Detect anomalies across all metrics
            anomalies = await self._detect_anomalies(db, end_time)

            # Generate contextual recommendations
            recommendations = self._generate_recommendations(scores, anomalies)

            # Calculate confidence level based on data availability
            confidence = self._calculate_confidence_level(scores)

            return {
                "metric_type": "network_health",
                "timestamp": end_time,
                "overall_score": round(overall_score, 2),
                "confidence_level": confidence,
                "component_scores": {k: v["score"] for k, v in scores.items()},
                "component_details": scores,
                "health_status": self._get_dynamic_health_status(overall_score, anomalies),
                "anomalies_detected": anomalies,
                "recommendations": recommendations,
                "ml_features": self._extract_ml_features(scores, anomalies),
            }

        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return self._default_health_score()

    async def _calculate_gas_efficiency_score(
        self, db: Session, end_time: datetime
    ) -> dict[str, Any]:
        """Calculate gas efficiency with dynamic baselines"""
        scores_by_window = {}

        for window_name, window_delta in self.baseline_windows.items():
            start_time = end_time - window_delta

            gas_metrics = (
                db.query(GasMetric).filter(GasMetric.timestamp.between(start_time, end_time)).all()
            )

            if not gas_metrics:
                continue

            gas_prices = np.array([m.gas_price_gwei for m in gas_metrics])

            # Calculate dynamic baseline using rolling percentiles
            baseline_p50 = np.percentile(gas_prices, 50)
            baseline_p95 = np.percentile(gas_prices, 95)
            current_gas = gas_prices[-1] if len(gas_prices) > 0 else baseline_p50

            # Score based on position within distribution
            if current_gas <= baseline_p50:
                score = 100
            elif current_gas <= baseline_p95:
                score = 100 - ((current_gas - baseline_p50) / (baseline_p95 - baseline_p50)) * 50
            else:
                score = max(0, 50 - ((current_gas - baseline_p95) / baseline_p95) * 50)

            # Calculate volatility penalty
            volatility = np.std(gas_prices) / np.mean(gas_prices) if np.mean(gas_prices) > 0 else 0
            volatility_penalty = min(20, volatility * 100)

            scores_by_window[window_name] = {
                "score": max(0, score - volatility_penalty),
                "baseline_p50": baseline_p50,
                "baseline_p95": baseline_p95,
                "current_value": current_gas,
                "volatility": volatility,
            }

        # Weight recent data more heavily
        if scores_by_window:
            weighted_score = (
                scores_by_window.get("short", {"score": 50})["score"] * 0.5
                + scores_by_window.get("medium", {"score": 50})["score"] * 0.3
                + scores_by_window.get("long", {"score": 50})["score"] * 0.2
            )
        else:
            weighted_score = 50

        return {
            "score": weighted_score,
            "windows": scores_by_window,
            "trend": (self._calculate_trend(gas_prices) if len(gas_prices) > 10 else "stable"),
        }

    async def _calculate_mev_fairness_score(
        self, db: Session, end_time: datetime
    ) -> dict[str, Any]:
        """Calculate MEV fairness score based on user impact"""
        window = timedelta(hours=6)
        start_time = end_time - window

        mev_metrics = (
            db.query(MEVMetric).filter(MEVMetric.timestamp.between(start_time, end_time)).all()
        )

        if not mev_metrics:
            return {"score": 75, "details": "No MEV data available"}

        # Calculate MEV extraction rate relative to total block value
        total_blocks = len(mev_metrics)
        total_mev_revenue = sum(m.total_mev_revenue for m in mev_metrics)
        avg_mev_per_block = total_mev_revenue / total_blocks if total_blocks > 0 else 0

        # Count harmful MEV (sandwich attacks)
        # For now, assume no sandwich attacks as we don't have this data yet
        total_sandwiches = 0  # TODO: implement sandwich attack detection
        sandwich_rate = total_sandwiches / total_blocks if total_blocks > 0 else 0

        # Score calculation
        base_score = 100

        # Penalize for high MEV extraction
        if avg_mev_per_block > 0.1:  # > 0.1 ETH per block
            base_score -= min(30, avg_mev_per_block * 100)

        # Penalize heavily for sandwich attacks
        base_score -= min(40, sandwich_rate * 1000)

        # Check builder diversity
        builder_diversity = len(set(m.builder_pubkey for m in mev_metrics)) / total_blocks
        diversity_bonus = min(10, builder_diversity * 20)

        final_score = max(0, min(100, base_score + diversity_bonus))

        return {
            "score": final_score,
            "avg_mev_per_block": avg_mev_per_block,
            "sandwich_rate": sandwich_rate,
            "builder_diversity": builder_diversity,
            "harmful_mev_percentage": (sandwich_rate * 100),
        }

    async def _calculate_block_time_score(
        self, db: Session, start_time: datetime, end_time: datetime
    ) -> float:
        """Calculate block time consistency score"""
        block_metrics = (
            db.query(BlockMetric)
            .filter(BlockMetric.timestamp.between(start_time, end_time))
            .order_by(BlockMetric.block_number)
            .all()
        )

        if len(block_metrics) < 2:
            return 50.0

        # Calculate block times
        block_times = []
        for i in range(1, len(block_metrics)):
            time_diff = (
                block_metrics[i].block_timestamp - block_metrics[i - 1].block_timestamp
            ).total_seconds()
            block_times.append(time_diff)

        if not block_times:
            return 50.0

        avg_block_time = np.mean(block_times)
        std_block_time = np.std(block_times)

        # Target is 12 seconds with low variance
        target_time = 12.0
        time_deviation = abs(avg_block_time - target_time)

        # Score based on deviation from target
        if time_deviation < 1 and std_block_time < 2:
            return 100.0
        elif time_deviation < 2 and std_block_time < 3:
            return 80.0
        elif time_deviation < 3 and std_block_time < 4:
            return 60.0
        else:
            return 40.0

    async def _detect_anomalies(self, db: Session, end_time: datetime) -> list[dict[str, Any]]:
        """Detect anomalies using statistical methods"""
        anomalies = []
        window = timedelta(hours=24)
        start_time = end_time - window

        # Gas price anomalies
        gas_metrics = (
            db.query(GasMetric)
            .filter(GasMetric.timestamp.between(start_time, end_time))
            .order_by(GasMetric.timestamp)
            .all()
        )

        if len(gas_metrics) > 20:
            gas_prices = [m.gas_price_gwei for m in gas_metrics]
            gas_anomalies = self._detect_statistical_anomalies(
                gas_prices,
                timestamps=[m.timestamp for m in gas_metrics],
                metric_name="gas_price",
            )
            anomalies.extend(gas_anomalies)

        # Block time anomalies
        block_metrics = (
            db.query(BlockMetric)
            .filter(BlockMetric.timestamp.between(start_time, end_time))
            .order_by(BlockMetric.block_number)
            .all()
        )

        if len(block_metrics) > 20:
            block_times = []
            for i in range(1, len(block_metrics)):
                time_diff = (
                    block_metrics[i].block_timestamp - block_metrics[i - 1].block_timestamp
                ).total_seconds()
                block_times.append(time_diff)

            block_anomalies = self._detect_statistical_anomalies(
                block_times,
                timestamps=[m.timestamp for m in block_metrics[1:]],
                metric_name="block_time",
                expected_value=12.0,
            )
            anomalies.extend(block_anomalies)

        # MEV spike detection
        mev_metrics = (
            db.query(MEVMetric).filter(MEVMetric.timestamp.between(start_time, end_time)).all()
        )

        if len(mev_metrics) > 10:
            mev_revenues = [m.total_mev_revenue for m in mev_metrics]
            mev_anomalies = self._detect_statistical_anomalies(
                mev_revenues,
                timestamps=[m.timestamp for m in mev_metrics],
                metric_name="mev_revenue",
            )
            anomalies.extend(mev_anomalies)

        return anomalies

    def _detect_statistical_anomalies(
        self,
        values: list[float],
        timestamps: list[datetime],
        metric_name: str,
        expected_value: Optional[float] = None,
    ) -> list[dict[str, Any]]:
        """Detect anomalies using Z-score and IQR methods"""
        anomalies = []
        values_array = np.array(values)

        # Z-score method
        z_scores = np.abs(stats.zscore(values_array))
        z_anomalies = np.where(z_scores > self.z_score_threshold)[0]

        # IQR method
        Q1 = np.percentile(values_array, 25)
        Q3 = np.percentile(values_array, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - self.iqr_multiplier * IQR
        upper_bound = Q3 + self.iqr_multiplier * IQR
        iqr_anomalies = np.where((values_array < lower_bound) | (values_array > upper_bound))[0]

        # Combine both methods
        all_anomaly_indices = set(z_anomalies) | set(iqr_anomalies)

        for idx in all_anomaly_indices:
            severity = self._calculate_anomaly_severity(
                values_array[idx], values_array, expected_value
            )

            anomalies.append(
                {
                    "timestamp": timestamps[idx],
                    "metric": metric_name,
                    "value": values[idx],
                    "z_score": z_scores[idx],
                    "severity": severity,
                    "type": ("spike" if values[idx] > np.median(values_array) else "drop"),
                    "context": {
                        "median": float(np.median(values_array)),
                        "std": float(np.std(values_array)),
                        "iqr_bounds": [float(lower_bound), float(upper_bound)],
                    },
                }
            )

        return anomalies

    def _calculate_anomaly_severity(
        self,
        value: float,
        all_values: np.ndarray,
        expected_value: Optional[float] = None,
    ) -> str:
        """Calculate anomaly severity"""
        median = np.median(all_values)
        std = np.std(all_values)

        if expected_value:
            deviation = abs(value - expected_value) / expected_value
        else:
            deviation = abs(value - median) / median if median != 0 else 0

        if deviation > 1.0 or abs(value - median) > 5 * std:
            return "critical"
        elif deviation > 0.5 or abs(value - median) > 3 * std:
            return "high"
        elif deviation > 0.25 or abs(value - median) > 2 * std:
            return "medium"
        else:
            return "low"

    def _extract_ml_features(self, scores: dict, anomalies: list[dict]) -> dict[str, Any]:
        """Extract features for ML models (Phase 3 preparation)"""
        return {
            "score_vector": [v["score"] for v in scores.values()],
            "score_variance": np.var([v["score"] for v in scores.values()]),
            "anomaly_count": len(anomalies),
            "anomaly_severity_distribution": {
                "critical": len([a for a in anomalies if a["severity"] == "critical"]),
                "high": len([a for a in anomalies if a["severity"] == "high"]),
                "medium": len([a for a in anomalies if a["severity"] == "medium"]),
                "low": len([a for a in anomalies if a["severity"] == "low"]),
            },
            "component_correlations": self._calculate_component_correlations(scores),
        }

    def _calculate_component_correlations(self, scores: dict) -> dict[str, float]:
        """Calculate correlations between component scores for pattern detection"""
        score_values = {k: v["score"] for k, v in scores.items()}
        correlations = {}

        # Simple correlation pairs that matter
        correlations["gas_mev"] = self._simple_correlation(
            score_values.get("gas_efficiency", 50), score_values.get("mev_fairness", 50)
        )
        correlations["stability_block"] = self._simple_correlation(
            score_values.get("network_stability", 50),
            score_values.get("block_production", 50),
        )

        return correlations

    def _simple_correlation(self, x: float, y: float) -> float:
        """Simple correlation estimate for two values"""
        # Normalize to -1 to 1 range
        return (x - 50) * (y - 50) / 2500

    def _default_health_score(self) -> dict[str, Any]:
        """Return default health score when calculation fails"""
        return {
            "metric_type": "network_health",
            "timestamp": datetime.utcnow(),
            "overall_score": 50.0,
            "gas_score": 50.0,
            "congestion_score": 50.0,
            "block_time_score": 50.0,
            "mev_impact_score": 50.0,
            "stability_score": 50.0,
            "health_status": "Unknown",
            "recommendations": ["Unable to calculate network health - please try again later"],
        }

    async def _calculate_network_stability_score(
        self, db: Session, end_time: datetime
    ) -> dict[str, Any]:
        """Calculate network stability based on block time consistency and reorgs"""
        window = timedelta(hours=24)
        start_time = end_time - window

        block_metrics = (
            db.query(BlockMetric)
            .filter(BlockMetric.timestamp.between(start_time, end_time))
            .order_by(BlockMetric.block_number)
            .all()
        )

        if len(block_metrics) < 10:
            return {"score": 75, "details": "Insufficient data for stability analysis"}

        # Calculate block time variance
        block_times = []
        for i in range(1, len(block_metrics)):
            time_diff = (
                block_metrics[i].block_timestamp - block_metrics[i - 1].block_timestamp
            ).total_seconds()
            block_times.append(time_diff)

        if block_times:
            variance = np.var(block_times)
            mean_time = np.mean(block_times)
            cv = np.sqrt(variance) / mean_time if mean_time > 0 else 0

            # Score based on coefficient of variation
            if cv < 0.1:
                score = 100
            elif cv < 0.2:
                score = 85
            elif cv < 0.3:
                score = 70
            else:
                score = max(50, 100 - cv * 100)
        else:
            score = 75

        return {
            "score": score,
            "block_time_cv": cv if block_times else 0,
            "mean_block_time": np.mean(block_times) if block_times else 12,
        }

    async def _calculate_block_production_score(
        self, db: Session, end_time: datetime
    ) -> dict[str, Any]:
        """Calculate block production health"""
        window = timedelta(hours=1)
        start_time = end_time - window

        block_count = (
            db.query(BlockMetric)
            .filter(BlockMetric.timestamp.between(start_time, end_time))
            .count()
        )

        # Expected blocks in an hour (12 second blocks)
        expected_blocks = 300
        actual_ratio = block_count / expected_blocks

        if actual_ratio >= 0.95:
            score = 100
        elif actual_ratio >= 0.90:
            score = 90
        elif actual_ratio >= 0.85:
            score = 75
        else:
            score = max(50, actual_ratio * 100)

        return {
            "score": score,
            "blocks_produced": block_count,
            "expected_blocks": expected_blocks,
            "production_ratio": actual_ratio,
        }

    async def _calculate_mempool_health_score(
        self, db: Session, end_time: datetime
    ) -> dict[str, Any]:
        """Calculate mempool health based on pending transactions"""
        # For now, return a default score since mempool metrics aren't fully implemented
        return {
            "score": 75,
            "details": "Mempool metrics not fully implemented",
            "pending_tx_count": 0,
        }

    async def _calculate_validator_performance_score(
        self, db: Session, end_time: datetime
    ) -> dict[str, Any]:
        """Calculate validator performance based on MEV data"""
        window = timedelta(hours=6)
        start_time = end_time - window

        mev_metrics = (
            db.query(MEVMetric).filter(MEVMetric.timestamp.between(start_time, end_time)).all()
        )

        if not mev_metrics:
            return {"score": 75, "details": "No validator performance data available"}

        # Calculate builder diversity as proxy for validator decentralization
        builders = [m.builder_pubkey for m in mev_metrics if m.builder_pubkey]
        unique_builders = len(set(builders))
        total_blocks = len(builders)

        if total_blocks > 0:
            diversity_ratio = unique_builders / min(total_blocks, 10)
            score = min(100, diversity_ratio * 100)
        else:
            score = 75

        return {
            "score": score,
            "unique_builders": unique_builders,
            "total_blocks": total_blocks,
            "diversity_ratio": diversity_ratio if total_blocks > 0 else 0,
        }

    def _generate_recommendations(
        self, scores: dict[str, dict[str, Any]], anomalies: list[dict[str, Any]]
    ) -> list[str]:
        """Generate contextual recommendations based on scores and anomalies"""
        recommendations = []

        # Check individual component scores
        for component, data in scores.items():
            score = data.get("score", 100)
            if score < 60:
                if component == "gas_efficiency":
                    recommendations.append(
                        "High gas prices detected. Consider delaying non-urgent transactions."
                    )
                elif component == "network_stability":
                    recommendations.append(
                        "Network instability detected. Monitor block times closely."
                    )
                elif component == "mev_fairness":
                    recommendations.append(
                        "High MEV activity impacting users. Use private mempools when possible."
                    )
                elif component == "block_production":
                    recommendations.append(
                        "Block production below expected rate. Network may be congested."
                    )

        # Check for severe anomalies
        severe_anomalies = [a for a in anomalies if a.get("severity") == "high"]
        if severe_anomalies:
            recommendations.append(
                f"Detected {len(severe_anomalies)} severe anomalies. Check network status."
            )

        # If everything is good
        if not recommendations:
            overall_score = sum(self.weights[k] * v["score"] for k, v in scores.items())
            if overall_score > 85:
                recommendations.append("Network health is excellent. All systems normal.")
            else:
                recommendations.append("Network health is stable.")

        return recommendations[:5]  # Limit to 5 recommendations

    def _calculate_confidence_level(self, scores: dict[str, dict[str, Any]]) -> float:
        """Calculate confidence level based on data availability"""
        # Check how many components have valid scores
        valid_scores = sum(
            1
            for data in scores.values()
            if isinstance(data.get("score"), (int, float)) and data["score"] > 0
        )

        total_components = len(scores)

        # Base confidence on data completeness
        if total_components == 0:
            return 0.0

        data_completeness = valid_scores / total_components

        # Additional factors affecting confidence
        confidence_factors = []

        # Check if we have sufficient data points in each component
        for component, data in scores.items():
            if "windows" in data:  # Has time-based analysis
                confidence_factors.append(0.9)
            elif "details" in data and "insufficient" in str(data.get("details", "")).lower():
                confidence_factors.append(0.5)
            else:
                confidence_factors.append(0.8)

        # Calculate overall confidence
        avg_factor = (
            sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.7
        )
        confidence = data_completeness * avg_factor * 100

        return round(min(100, max(0, confidence)), 1)

    def _get_dynamic_health_status(
        self, overall_score: float, anomalies: list[dict[str, Any]]
    ) -> str:
        """Get dynamic health status based on score and anomalies"""
        # Check for critical anomalies
        critical_anomalies = [a for a in anomalies if a.get("severity") == "critical"]
        high_anomalies = [a for a in anomalies if a.get("severity") == "high"]

        # Adjust status based on anomalies
        if critical_anomalies:
            return "Critical - Immediate Attention Required"
        elif high_anomalies and overall_score < 70:
            return "Warning - Multiple Issues Detected"
        elif overall_score >= 90:
            return "Excellent"
        elif overall_score >= 80:
            return "Good"
        elif overall_score >= 70:
            return "Fair"
        elif overall_score >= 60:
            return "Degraded"
        elif overall_score >= 50:
            return "Poor"
        else:
            return "Critical"

    def _calculate_trend(self, values: list[float]) -> str:
        """Calculate trend direction from a series of values"""
        if len(values) < 3:
            return "stable"

        # Use simple linear regression slope
        x = np.arange(len(values))
        slope, _ = np.polyfit(x, values, 1)

        # Normalize slope by mean value
        mean_val = np.mean(values)
        if mean_val == 0:
            return "stable"

        normalized_slope = slope / mean_val

        # Determine trend based on normalized slope
        if normalized_slope > 0.01:
            return "increasing"
        elif normalized_slope < -0.01:
            return "decreasing"
        else:
            return "stable"
