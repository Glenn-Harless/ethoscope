import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID

from .database import Base


class L2NetworkMetric(Base):
    """L2 network metrics"""

    __tablename__ = "l2_network_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    network = Column(String(50), nullable=False, index=True)
    chain_id = Column(Integer, nullable=False)
    block_number = Column(BigInteger, nullable=False)
    gas_price_wei = Column(BigInteger)
    gas_price_gwei = Column(Float)
    l1_gas_price_gwei = Column(Float)
    gas_savings_percent = Column(Float)
    transaction_count = Column(Integer)
    block_time = Column(BigInteger)

    __table_args__ = (
        Index("idx_l2_metrics_network_timestamp", "network", "timestamp"),
    )


class L2TransactionCost(Base):
    """L2 transaction cost comparisons"""

    __tablename__ = "l2_transaction_costs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    network = Column(String(50), nullable=False, index=True)
    eth_transfer_cost_usd = Column(Float)
    erc20_transfer_cost_usd = Column(Float)
    uniswap_swap_cost_usd = Column(Float)
    nft_mint_cost_usd = Column(Float)


class L2TVLMetric(Base):
    """L2 Total Value Locked metrics"""

    __tablename__ = "l2_tvl_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    network = Column(String(50), nullable=False, index=True)
    tvl_usd = Column(Float)
    tvl_eth = Column(Float)
    daily_tps = Column(Float)
    market_share_percent = Column(Float)
