from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class GasMetricResponse(BaseModel):
    id: UUID
    timestamp: datetime
    gas_price_wei: int
    gas_price_gwei: float
    pending_transactions: Optional[int]
    gas_price_p25: Optional[float]
    gas_price_p50: Optional[float]
    gas_price_p75: Optional[float]
    gas_price_p95: Optional[float]

    class Config:
        from_attributes = True


class BlockMetricResponse(BaseModel):
    id: UUID
    timestamp: datetime
    block_number: int
    block_timestamp: datetime
    gas_used: int
    gas_limit: int
    transaction_count: int
    base_fee_per_gas: Optional[int]
    difficulty: Optional[int]

    class Config:
        from_attributes = True


class NetworkHealthResponse(BaseModel):
    timestamp: datetime
    overall_score: float = Field(..., ge=0, le=100)
    gas_score: float = Field(..., ge=0, le=100)
    congestion_score: float = Field(..., ge=0, le=100)
    block_time_score: float = Field(..., ge=0, le=100)
    mev_impact_score: float = Field(..., ge=0, le=100)
    stability_score: float = Field(..., ge=0, le=100)
    health_status: str
    recommendations: list[str]


class MEVImpactResponse(BaseModel):
    period_hours: int
    total_mev_revenue_eth: float
    total_sandwich_attacks: int
    total_sandwich_profit_eth: float
    avg_mev_gas_price_gwei: float
    avg_regular_gas_price_gwei: float
    mev_gas_premium_percent: float


class L2ComparisonResponse(BaseModel):
    network: str
    gas_price_gwei: float
    gas_savings_percent: Optional[float]
    transaction_count: int
    eth_transfer_cost_usd: Optional[float]
    tvl_usd: Optional[float]
    daily_tps: Optional[float]


class TimeSeriesQuery(BaseModel):
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    interval: Optional[str] = "5m"  # 5m, 15m, 1h, 1d
    limit: Optional[int] = Field(100, le=1000)
