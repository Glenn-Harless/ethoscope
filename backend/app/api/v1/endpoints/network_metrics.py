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


@router.get("/stats", response_model=dict[str, Any])
async def get_network_stats(db=Depends(get_db)):
    """Get current network statistics."""
    try:
        # Get block metrics
        block_query = text(
            """
            SELECT
                AVG(transaction_count) as avg_tx_count,
                AVG(gas_used) as avg_gas_used,
                AVG(gas_limit) as avg_gas_limit,
                MAX(block_number) as latest_block,
                COUNT(*) as blocks_analyzed
            FROM block_metrics
            WHERE timestamp > NOW() - INTERVAL '1 hour'
        """
        )

        block_result = db.execute(block_query).fetchone()

        # Get mempool metrics
        mempool_query = text(
            """
            SELECT
                AVG(pending_transactions) as avg_pending,
                MAX(pending_transactions) as max_pending,
                AVG(queued_transactions) as avg_queued
            FROM mempool_metrics
            WHERE timestamp > NOW() - INTERVAL '1 hour'
        """
        )

        mempool_result = db.execute(mempool_query).fetchone()

        # Get gas metrics
        gas_query = text(
            """
            SELECT
                gas_price_gwei,
                gas_price_p50,
                gas_price_p95,
                pending_transactions
            FROM gas_metrics
            ORDER BY timestamp DESC
            LIMIT 1
        """
        )

        gas_result = db.execute(gas_query).fetchone()

        return {
            "block_stats": {
                "avg_transaction_count": float(block_result.avg_tx_count)
                if block_result.avg_tx_count
                else 0,
                "avg_gas_used": float(block_result.avg_gas_used)
                if block_result.avg_gas_used
                else 0,
                "avg_gas_limit": float(block_result.avg_gas_limit)
                if block_result.avg_gas_limit
                else 0,
                "latest_block": int(block_result.latest_block) if block_result.latest_block else 0,
                "blocks_analyzed": int(block_result.blocks_analyzed)
                if block_result.blocks_analyzed
                else 0,
            },
            "mempool_stats": {
                "avg_pending_transactions": float(mempool_result.avg_pending)
                if mempool_result and mempool_result.avg_pending
                else 0,
                "max_pending_transactions": float(mempool_result.max_pending)
                if mempool_result and mempool_result.max_pending
                else 0,
                "avg_queued_transactions": float(mempool_result.avg_queued)
                if mempool_result and mempool_result.avg_queued
                else 0,
            },
            "current_gas": {
                "gas_price_gwei": float(gas_result.gas_price_gwei) if gas_result else 0,
                "gas_price_p50": float(gas_result.gas_price_p50) if gas_result else 0,
                "gas_price_p95": float(gas_result.gas_price_p95) if gas_result else 0,
                "pending_transactions": int(gas_result.pending_transactions) if gas_result else 0,
            },
        }
    except Exception as e:
        logger.error(f"Error fetching network stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=dict[str, Any])
async def get_network_health(db=Depends(get_db)):
    """Calculate network health score based on multiple metrics."""
    try:
        # Get recent metrics for health calculation
        query = text(
            """
            WITH recent_metrics AS (
                SELECT
                    AVG(g.gas_price_gwei) as avg_gas,
                    AVG(m.pending_transactions) as avg_pending,
                    AVG(b.gas_used::float / NULLIF(b.gas_limit, 0)) as avg_utilization
                FROM gas_metrics g
                JOIN mempool_metrics m ON ABS(EXTRACT(EPOCH FROM g.timestamp - m.timestamp)) < 60
                JOIN block_metrics b ON ABS(EXTRACT(EPOCH FROM g.timestamp - b.timestamp)) < 60
                WHERE g.timestamp > NOW() - INTERVAL '1 hour'
            )
            SELECT * FROM recent_metrics
        """
        )

        result = db.execute(query).fetchone()

        # Calculate health score (0-100)
        health_score = 100
        reasons = []

        if result and result.avg_gas:
            # Deduct points for high gas
            if result.avg_gas > 10:
                health_score -= 30
                reasons.append("High gas prices")
            elif result.avg_gas > 5:
                health_score -= 20
                reasons.append("Moderate gas prices")
            elif result.avg_gas > 2:
                health_score -= 10
                reasons.append("Slightly elevated gas")

            # Deduct points for high pending transactions
            if result.avg_pending and result.avg_pending > 10000:
                health_score -= 20
                reasons.append("High mempool congestion")
            elif result.avg_pending and result.avg_pending > 5000:
                health_score -= 10
                reasons.append("Moderate mempool activity")

            # Deduct points for high utilization
            if result.avg_utilization and result.avg_utilization > 0.9:
                health_score -= 20
                reasons.append("High block utilization")
            elif result.avg_utilization and result.avg_utilization > 0.7:
                health_score -= 10
                reasons.append("Moderate block utilization")

        # Determine status
        if health_score >= 80:
            status = "Excellent"
        elif health_score >= 60:
            status = "Good"
        elif health_score >= 40:
            status = "Fair"
        else:
            status = "Poor"

        return {
            "health_score": max(0, health_score),
            "status": status,
            "factors": reasons if reasons else ["Network operating normally"],
            "metrics": {
                "avg_gas_price": float(result.avg_gas) if result and result.avg_gas else 0,
                "avg_pending_tx": float(result.avg_pending) if result and result.avg_pending else 0,
                "avg_block_utilization": float(result.avg_utilization * 100)
                if result and result.avg_utilization
                else 0,
            },
        }
    except Exception as e:
        logger.error(f"Error calculating network health: {e}")
        raise HTTPException(status_code=500, detail=str(e))
