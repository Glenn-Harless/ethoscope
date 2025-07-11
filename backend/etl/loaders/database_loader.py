import logging
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError

from backend.models.database import SessionLocal
from backend.models.l2_metrics import L2NetworkMetric, L2TransactionCost, L2TVLMetric
from backend.models.metrics import (
    BlockMetric,
    GasMetric,
    MempoolMetric,
    NetworkHealthScore,
)
from backend.models.mev_metrics import MEVBoostStats, MEVMetric

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Enhanced database loader for all metric types"""

    async def load(self, processed_data: dict[str, list[dict[str, Any]]]):
        """Load all metric types with error handling"""
        db = SessionLocal()
        try:
            # Track loading statistics
            load_stats = {}

            # Load each metric type
            loaders = {
                "block_metrics": self._load_block_metrics,
                "gas_metrics": self._load_gas_metrics,
                "mempool_metrics": self._load_mempool_metrics,
                "mev_metrics": self._load_mev_metrics,
                "mev_boost_stats": self._load_mev_boost_stats,
                "l2_network_metrics": self._load_l2_network_metrics,
                "l2_transaction_costs": self._load_l2_transaction_costs,
                "l2_tvl_metrics": self._load_l2_tvl_metrics,
                "network_health_scores": self._load_network_health_scores,
            }

            for metric_type, loader_func in loaders.items():
                if processed_data.get(metric_type):
                    try:
                        count = await loader_func(db, processed_data[metric_type])
                        load_stats[metric_type] = count
                    except Exception as e:
                        logger.error(f"Error loading {metric_type}: {e}")
                        load_stats[metric_type] = 0

            db.commit()
            logger.info(f"Load statistics: {load_stats}")

        except Exception as e:
            db.rollback()
            logger.error(f"Error loading data: {e}")
            raise
        finally:
            db.close()

    async def _load_block_metrics(self, db, metrics: list[dict[str, Any]]) -> int:
        """Load block metrics with upsert"""
        loaded = 0
        for metric in metrics:
            try:
                stmt = insert(BlockMetric).values(**metric)
                stmt = stmt.on_conflict_do_update(index_elements=["block_number"], set_=metric)
                db.execute(stmt)
                loaded += 1
            except IntegrityError as e:
                logger.warning(f"Duplicate block metric: {e}")
        return loaded

    async def _load_gas_metrics(self, db, metrics: list[dict[str, Any]]) -> int:
        """Load gas metrics"""
        loaded = 0
        for metric in metrics:
            try:
                db.add(GasMetric(**metric))
                loaded += 1
            except Exception as e:
                logger.error(f"Error loading gas metric: {e}")
        return loaded

    async def _load_mempool_metrics(self, db, metrics: list[dict[str, Any]]) -> int:
        """Load mempool metrics"""
        loaded = 0
        for metric in metrics:
            try:
                db.add(MempoolMetric(**metric))
                loaded += 1
            except Exception as e:
                logger.error(f"Error loading mempool metric: {e}")
        return loaded

    async def _load_mev_metrics(self, db, metrics: list[dict[str, Any]]) -> int:
        """Load MEV metrics"""
        loaded = 0
        for metric in metrics:
            try:
                db.add(MEVMetric(**metric))
                loaded += 1
            except Exception as e:
                logger.error(f"Error loading MEV metric: {e}")
        return loaded

    async def _load_mev_boost_stats(self, db, metrics: list[dict[str, Any]]) -> int:
        """Load MEV boost statistics"""
        loaded = 0
        for metric in metrics:
            try:
                db.add(MEVBoostStats(**metric))
                loaded += 1
            except Exception as e:
                logger.error(f"Error loading MEV boost stats: {e}")
        return loaded

    async def _load_l2_network_metrics(self, db, metrics: list[dict[str, Any]]) -> int:
        """Load L2 network metrics"""
        loaded = 0
        for metric in metrics:
            try:
                db.add(L2NetworkMetric(**metric))
                loaded += 1
            except Exception as e:
                logger.error(f"Error loading L2 network metric: {e}")
        return loaded

    async def _load_l2_transaction_costs(self, db, metrics: list[dict[str, Any]]) -> int:
        """Load L2 transaction costs"""
        loaded = 0
        for metric in metrics:
            try:
                db.add(L2TransactionCost(**metric))
                loaded += 1
            except Exception as e:
                logger.error(f"Error loading L2 transaction cost: {e}")
        return loaded

    async def _load_l2_tvl_metrics(self, db, metrics: list[dict[str, Any]]) -> int:
        """Load L2 TVL metrics"""
        loaded = 0
        for metric in metrics:
            try:
                db.add(L2TVLMetric(**metric))
                loaded += 1
            except Exception as e:
                logger.error(f"Error loading L2 TVL metric: {e}")
        return loaded

    async def _load_network_health_scores(self, db, metrics: list[dict[str, Any]]) -> int:
        """Load network health scores"""
        loaded = 0
        for metric in metrics:
            try:
                score = NetworkHealthScore(
                    overall_score=metric["overall_score"],
                    gas_score=metric["gas_score"],
                    congestion_score=metric["congestion_score"],
                    block_time_score=metric["block_time_score"],
                )
                db.add(score)
                loaded += 1
            except Exception as e:
                logger.error(f"Error loading health score: {e}")
        return loaded
