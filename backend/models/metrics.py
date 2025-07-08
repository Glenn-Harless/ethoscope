import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from .database import Base


class BlockMetric(Base):
    """Block-level metrics"""

    __tablename__ = "block_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    block_number = Column(BigInteger, nullable=False, unique=True, index=True)
    block_timestamp = Column(DateTime, nullable=False)
    gas_used = Column(BigInteger, nullable=False)
    gas_limit = Column(BigInteger, nullable=False)
    transaction_count = Column(Integer, nullable=False)
    base_fee_per_gas = Column(BigInteger)
    difficulty = Column(BigInteger)

    __table_args__ = (
        Index("idx_block_metrics_timestamp", "timestamp"),
        Index("idx_block_metrics_block_timestamp", "block_timestamp"),
    )


class GasMetric(Base):
    """Gas price metrics"""

    __tablename__ = "gas_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    gas_price_wei = Column(BigInteger, nullable=False)
    gas_price_gwei = Column(Float, nullable=False)
    pending_transactions = Column(Integer)

    # Gas price percentiles
    gas_price_p25 = Column(Float)
    gas_price_p50 = Column(Float)
    gas_price_p75 = Column(Float)
    gas_price_p95 = Column(Float)


class MempoolMetric(Base):
    """Mempool statistics"""

    __tablename__ = "mempool_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    pending_count = Column(Integer, nullable=False)
    avg_gas_price_gwei = Column(Float)
    min_gas_price_gwei = Column(Float)
    max_gas_price_gwei = Column(Float)


class NetworkHealthScore(Base):
    """Computed network health scores"""

    __tablename__ = "network_health_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    overall_score = Column(Float, nullable=False)  # 0-100
    gas_score = Column(Float, nullable=False)
    congestion_score = Column(Float, nullable=False)
    block_time_score = Column(Float, nullable=False)

    # Additional metadata
    calculation_version = Column(String(50), default="1.0")
