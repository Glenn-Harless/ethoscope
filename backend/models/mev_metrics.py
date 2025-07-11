import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from .database import Base


class MEVMetric(Base):
    """MEV extraction metrics from relay data"""

    __tablename__ = "mev_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    block_number = Column(BigInteger, nullable=False, index=True)
    slot = Column(BigInteger, nullable=False, index=True)
    total_mev_revenue = Column(Float)  # ETH
    builder_pubkey = Column(String(100))
    proposer_fee_recipient = Column(String(42))
    gas_used = Column(BigInteger)
    gas_limit = Column(BigInteger)
    gas_utilization = Column(Float)  # Percentage
    mev_gas_price_gwei = Column(Float)  # MEV gas price in Gwei
    relay_source = Column(String(50))
    block_hash = Column(String(66))
    parent_hash = Column(String(66))

    __table_args__ = (
        Index("idx_mev_metrics_timestamp_block", "timestamp", "block_number"),
        Index("idx_mev_metrics_slot", "slot"),
        Index("idx_mev_metrics_builder", "builder_pubkey"),
    )


class MEVBoostStats(Base):
    """Aggregate MEV-Boost statistics"""

    __tablename__ = "mev_boost_stats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    total_mev_revenue_eth = Column(Float)
    average_block_value_eth = Column(Float)
    block_count = Column(Integer)
    top_builder = Column(String(100))


class MEVBlockAnalysis(Base):
    """Block-level MEV characteristics analysis"""

    __tablename__ = "mev_block_analysis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    block_number = Column(BigInteger, nullable=False, index=True)
    slot = Column(BigInteger, nullable=False)
    mev_intensity = Column(String(20))  # high/medium/low
    value_eth = Column(Float)
    gas_efficiency = Column(Float)  # 0-1 ratio
    builder_pubkey = Column(String(100))
    likely_mev_type = Column(String(50))  # likely_contains_liquidations, etc.
    relay_source = Column(String(50))

    __table_args__ = (
        Index("idx_mev_block_analysis_timestamp_block", "timestamp", "block_number"),
        Index("idx_mev_block_analysis_intensity", "mev_intensity"),
        Index("idx_mev_block_analysis_type", "likely_mev_type"),
    )
