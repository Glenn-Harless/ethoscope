import logging
from typing import Any, Dict, List

from sqlalchemy.dialects.postgresql import insert

from backend.models.database import SessionLocal
from backend.models.metrics import BlockMetric, GasMetric, MempoolMetric

logger = logging.getLogger(__name__)


class DatabaseLoader:
    """Load processed metrics into database"""

    async def load(self, processed_data: Dict[str, List[Dict[str, Any]]]):
        """Load all metric types"""
        db = SessionLocal()
        try:
            # Load block metrics
            if processed_data.get("block_metrics"):
                await self._load_block_metrics(db, processed_data["block_metrics"])

            # Load gas metrics
            if processed_data.get("gas_metrics"):
                await self._load_gas_metrics(db, processed_data["gas_metrics"])

            # Load mempool metrics
            if processed_data.get("mempool_metrics"):
                await self._load_mempool_metrics(db, processed_data["mempool_metrics"])

            db.commit()
            logger.info("All metrics loaded successfully")

        except Exception as e:
            db.rollback()
            logger.error(f"Error loading data: {e}")
            raise
        finally:
            db.close()

    async def _load_block_metrics(self, db, metrics: List[Dict[str, Any]]):
        """Load block metrics with upsert"""
        for metric in metrics:
            stmt = insert(BlockMetric).values(**metric)
            stmt = stmt.on_conflict_do_update(
                index_elements=["block_number"], set_=metric
            )
            db.execute(stmt)

    async def _load_gas_metrics(self, db, metrics: List[Dict[str, Any]]):
        """Load gas metrics"""
        for metric in metrics:
            db.add(GasMetric(**metric))

    async def _load_mempool_metrics(self, db, metrics: List[Dict[str, Any]]):
        """Load mempool metrics"""
        for metric in metrics:
            db.add(MempoolMetric(**metric))
