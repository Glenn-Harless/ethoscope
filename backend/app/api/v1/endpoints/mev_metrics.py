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


@router.get("/summary", response_model=dict[str, Any])
async def get_mev_summary(db=Depends(get_db)):
    """Get MEV metrics summary."""
    try:
        query = text(
            """
            SELECT
                AVG(total_mev_revenue) as avg_mev_revenue,
                MAX(total_mev_revenue) as max_mev_revenue,
                MIN(total_mev_revenue) as min_mev_revenue,
                AVG(gas_utilization) as avg_gas_utilization,
                AVG(mev_gas_price_gwei) as avg_mev_gas_price,
                COUNT(DISTINCT builder_pubkey) as unique_builders,
                COUNT(DISTINCT relay_source) as unique_relays,
                COUNT(*) as blocks_count
            FROM mev_metrics
            WHERE timestamp > NOW() - INTERVAL '1 hour'
        """
        )

        result = db.execute(query).fetchone()

        return {
            "avg_mev_revenue": float(result.avg_mev_revenue) if result.avg_mev_revenue else 0,
            "max_mev_revenue": float(result.max_mev_revenue) if result.max_mev_revenue else 0,
            "min_mev_revenue": float(result.min_mev_revenue) if result.min_mev_revenue else 0,
            "avg_gas_utilization": float(result.avg_gas_utilization)
            if result.avg_gas_utilization
            else 0,
            "avg_mev_gas_price": float(result.avg_mev_gas_price) if result.avg_mev_gas_price else 0,
            "unique_builders": int(result.unique_builders) if result.unique_builders else 0,
            "unique_relays": int(result.unique_relays) if result.unique_relays else 0,
            "blocks_analyzed": int(result.blocks_count) if result.blocks_count else 0,
        }
    except Exception as e:
        logger.error(f"Error fetching MEV summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/builders", response_model=list[dict[str, Any]])
async def get_builder_stats(db=Depends(get_db)):
    """Get builder statistics."""
    try:
        query = text(
            """
            SELECT
                builder_pubkey,
                COUNT(*) as blocks_built,
                AVG(total_mev_revenue) as avg_revenue,
                MAX(total_mev_revenue) as max_revenue,
                AVG(gas_utilization) as avg_gas_utilization
            FROM mev_metrics
            WHERE timestamp > NOW() - INTERVAL '24 hours'
                AND builder_pubkey IS NOT NULL
            GROUP BY builder_pubkey
            ORDER BY blocks_built DESC
            LIMIT 20
        """
        )

        result = db.execute(query)
        builders = []
        for row in result:
            builders.append(
                {
                    "builder": row.builder_pubkey[:10] + "..." if row.builder_pubkey else "Unknown",
                    "blocks_built": int(row.blocks_built),
                    "avg_revenue": float(row.avg_revenue) if row.avg_revenue else 0,
                    "max_revenue": float(row.max_revenue) if row.max_revenue else 0,
                    "avg_gas_utilization": float(row.avg_gas_utilization)
                    if row.avg_gas_utilization
                    else 0,
                }
            )

        return builders
    except Exception as e:
        logger.error(f"Error fetching builder stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hourly", response_model=list[dict[str, Any]])
async def get_hourly_mev_stats(db=Depends(get_db)):
    """Get hourly MEV statistics."""
    try:
        query = text(
            """
            SELECT
                DATE_TRUNC('hour', timestamp) as hour,
                AVG(total_mev_revenue) as avg_revenue,
                MAX(total_mev_revenue) as max_revenue,
                AVG(gas_utilization) as avg_utilization,
                COUNT(*) as blocks
            FROM mev_metrics
            WHERE timestamp > NOW() - INTERVAL '24 hours'
            GROUP BY hour
            ORDER BY hour DESC
        """
        )

        result = db.execute(query)
        hourly_stats = []
        for row in result:
            hourly_stats.append(
                {
                    "hour": row.hour.isoformat(),
                    "avg_revenue": float(row.avg_revenue) if row.avg_revenue else 0,
                    "max_revenue": float(row.max_revenue) if row.max_revenue else 0,
                    "avg_utilization": float(row.avg_utilization) if row.avg_utilization else 0,
                    "blocks": int(row.blocks),
                }
            )

        return hourly_stats
    except Exception as e:
        logger.error(f"Error fetching hourly MEV stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
