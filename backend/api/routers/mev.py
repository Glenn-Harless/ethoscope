from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.mev_metrics import MEVMetric

router = APIRouter()


@router.get("/impact")
async def get_mev_impact(db: Session = Depends(get_db), hours: int = Query(24, ge=1, le=168)):
    """Get MEV impact statistics"""
    start_time = datetime.utcnow() - timedelta(hours=hours)

    # Aggregate MEV metrics
    mev_stats = (
        db.query(
            func.sum(MEVMetric.total_mev_revenue).label("total_revenue"),
            func.count(MEVMetric.id).label("total_blocks"),
            func.avg(MEVMetric.mev_gas_price_gwei).label("avg_mev_gas"),
        )
        .filter(MEVMetric.timestamp >= start_time)
        .first()
    )

    # Get regular user gas price for comparison
    from backend.models.metrics import GasMetric

    avg_regular_gas = (
        db.query(func.avg(GasMetric.gas_price_gwei))
        .filter(GasMetric.timestamp >= start_time)
        .scalar()
    )

    return {
        "period_hours": hours,
        "total_mev_revenue_eth": float(mev_stats.total_revenue or 0),
        "total_blocks_with_mev": int(mev_stats.total_blocks or 0),
        "avg_mev_gas_price_gwei": float(mev_stats.avg_mev_gas or 0),
        "avg_regular_gas_price_gwei": float(avg_regular_gas or 0),
        "mev_gas_premium_percent": _calculate_premium(mev_stats.avg_mev_gas, avg_regular_gas),
    }


@router.get("/sandwich-attacks")
async def get_recent_sandwich_attacks(
    db: Session = Depends(get_db), limit: int = Query(20, le=100)
):
    """Get recent sandwich attacks - placeholder endpoint"""
    # TODO: Implement sandwich attack detection
    return {"attacks": [], "message": "Sandwich attack detection not yet implemented"}


@router.get("/builders")
async def get_top_builders(db: Session = Depends(get_db), hours: int = Query(24, ge=1, le=168)):
    """Get top MEV builders by revenue"""
    start_time = datetime.utcnow() - timedelta(hours=hours)

    builder_stats = (
        db.query(
            MEVMetric.builder_pubkey,
            func.count(MEVMetric.id).label("block_count"),
            func.sum(MEVMetric.total_mev_revenue).label("total_revenue"),
        )
        .filter(MEVMetric.timestamp >= start_time)
        .group_by(MEVMetric.builder_pubkey)
        .order_by(func.sum(MEVMetric.total_mev_revenue).desc())
        .limit(10)
        .all()
    )

    return {
        "period_hours": hours,
        "builders": [
            {
                "address": stat.builder_pubkey,
                "block_count": stat.block_count,
                "total_revenue_eth": float(stat.total_revenue),
            }
            for stat in builder_stats
        ],
    }


def _calculate_premium(mev_gas: float, regular_gas: float) -> float:
    """Calculate MEV gas premium percentage"""
    if not regular_gas or not mev_gas:
        return 0.0
    return ((mev_gas - regular_gas) / regular_gas) * 100
