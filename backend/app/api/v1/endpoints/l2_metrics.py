import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text

from backend.models.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/tvl", response_model=list[dict[str, Any]])
async def get_l2_tvl(db=Depends(get_db)):
    """Get latest L2 TVL metrics."""
    try:
        query = text(
            """
            WITH latest_tvl AS (
                SELECT DISTINCT ON (network)
                    network,
                    tvl_usd,
                    tvl_eth,
                    market_share_percent,
                    daily_tps,
                    timestamp
                FROM l2_tvl_metrics
                WHERE timestamp > NOW() - INTERVAL '24 hours'
                ORDER BY network, timestamp DESC
            )
            SELECT * FROM latest_tvl
            WHERE tvl_usd > 0
            ORDER BY tvl_usd DESC
        """
        )

        result = db.execute(query)
        data = []
        for row in result:
            data.append(
                {
                    "network": row.network,
                    "tvl_usd": float(row.tvl_usd),
                    "tvl_eth": float(row.tvl_eth) if row.tvl_eth else 0,
                    "market_share_percent": float(row.market_share_percent),
                    "daily_tps": float(row.daily_tps) if row.daily_tps else 0,
                    "timestamp": row.timestamp.isoformat(),
                }
            )

        return data
    except Exception as e:
        logger.error(f"Error fetching L2 TVL: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparison", response_model=dict[str, Any])
async def get_l2_comparison(db=Depends(get_db)):
    """Get L2 network comparison metrics."""
    try:
        query = text(
            """
            SELECT
                network,
                AVG(tvl_usd) as avg_tvl,
                AVG(daily_tps) as avg_tps,
                MAX(tvl_usd) as max_tvl,
                MIN(tvl_usd) as min_tvl
            FROM l2_tvl_metrics
            WHERE timestamp > NOW() - INTERVAL '7 days'
            GROUP BY network
            ORDER BY avg_tvl DESC
        """
        )

        result = db.execute(query)
        networks = []
        for row in result:
            networks.append(
                {
                    "network": row.network,
                    "avg_tvl": float(row.avg_tvl) if row.avg_tvl else 0,
                    "avg_tps": float(row.avg_tps) if row.avg_tps else 0,
                    "max_tvl": float(row.max_tvl) if row.max_tvl else 0,
                    "min_tvl": float(row.min_tvl) if row.min_tvl else 0,
                }
            )

        return {"networks": networks}
    except Exception as e:
        logger.error(f"Error fetching L2 comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))
