import os
from datetime import datetime, timedelta
from typing import List, Optional

import redis
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from backend.api.middleware.cache import MetricsCache
from backend.api.schemas import BlockMetricResponse, GasMetricResponse
from backend.models.database import get_db
from backend.models.metrics import BlockMetric, GasMetric, MempoolMetric

router = APIRouter()

# Initialize cache
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
cache = MetricsCache(redis_client)


@router.get("/gas", response_model=List[GasMetricResponse])
async def get_gas_metrics(
    request: Request,
    db: Session = Depends(get_db),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
):
    """Get gas price metrics with optional time range"""
    query = db.query(GasMetric)

    if start_time:
        query = query.filter(GasMetric.timestamp >= start_time)
    if end_time:
        query = query.filter(GasMetric.timestamp <= end_time)
    else:
        # Default to last 24 hours if no time range specified
        query = query.filter(
            GasMetric.timestamp >= datetime.utcnow() - timedelta(hours=24)
        )

    metrics = query.order_by(GasMetric.timestamp.desc()).limit(limit).all()
    return metrics


@router.get("/gas/latest")
async def get_latest_gas_price(db: Session = Depends(get_db)):
    """Get latest gas price"""
    latest = db.query(GasMetric).order_by(GasMetric.timestamp.desc()).first()
    if not latest:
        raise HTTPException(status_code=404, detail="No gas metrics found")

    return {
        "timestamp": latest.timestamp,
        "gas_price_gwei": latest.gas_price_gwei,
        "gas_price_p50": latest.gas_price_p50,
        "gas_price_p95": latest.gas_price_p95,
        "pending_transactions": latest.pending_transactions,
    }


@router.get("/gas/percentiles")
async def get_gas_percentiles(
    db: Session = Depends(get_db), hours: int = Query(1, ge=1, le=24)
):
    """Get gas price percentiles over specified hours"""
    start_time = datetime.utcnow() - timedelta(hours=hours)

    metrics = db.query(GasMetric).filter(GasMetric.timestamp >= start_time).all()

    if not metrics:
        return {"message": "No data available for the specified period"}

    # Get the most recent metric with percentiles
    latest_with_percentiles = None
    for metric in metrics:
        if metric.gas_price_p50 is not None:
            latest_with_percentiles = metric
            break

    if latest_with_percentiles:
        return {
            "period_hours": hours,
            "timestamp": latest_with_percentiles.timestamp,
            "percentiles": {
                "p25": latest_with_percentiles.gas_price_p25,
                "p50": latest_with_percentiles.gas_price_p50,
                "p75": latest_with_percentiles.gas_price_p75,
                "p95": latest_with_percentiles.gas_price_p95,
            },
        }

    return {"message": "Percentile data not yet available"}


@router.get("/blocks", response_model=List[BlockMetricResponse])
async def get_block_metrics(
    db: Session = Depends(get_db),
    start_block: Optional[int] = Query(None),
    end_block: Optional[int] = Query(None),
    limit: int = Query(100, le=1000),
):
    """Get block metrics with optional block range"""
    query = db.query(BlockMetric)

    if start_block:
        query = query.filter(BlockMetric.block_number >= start_block)
    if end_block:
        query = query.filter(BlockMetric.block_number <= end_block)

    metrics = query.order_by(BlockMetric.block_number.desc()).limit(limit).all()
    return metrics


@router.get("/mempool/current")
async def get_current_mempool_stats(db: Session = Depends(get_db)):
    """Get current mempool statistics"""
    latest = db.query(MempoolMetric).order_by(MempoolMetric.timestamp.desc()).first()

    if not latest:
        raise HTTPException(status_code=404, detail="No mempool metrics found")

    return {
        "timestamp": latest.timestamp,
        "pending_count": latest.pending_count,
        "avg_gas_price_gwei": latest.avg_gas_price_gwei,
        "min_gas_price_gwei": latest.min_gas_price_gwei,
        "max_gas_price_gwei": latest.max_gas_price_gwei,
        "congestion_level": _calculate_congestion_level(latest.pending_count),
    }


def _calculate_congestion_level(pending_count: int) -> str:
    """Calculate congestion level based on pending transactions"""
    if pending_count < 50000:
        return "low"
    elif pending_count < 100000:
        return "moderate"
    elif pending_count < 150000:
        return "high"
    else:
        return "severe"
