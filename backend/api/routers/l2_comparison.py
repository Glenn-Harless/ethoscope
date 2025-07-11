from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.models.database import get_db
from backend.models.l2_metrics import L2NetworkMetric, L2TransactionCost, L2TVLMetric

router = APIRouter()


@router.get("/comparison")
async def get_l2_comparison(db: Session = Depends(get_db)):
    """Get current L2 network comparison"""
    networks = ["arbitrum", "optimism", "polygon", "base"]
    comparison = {}

    for network in networks:
        # Get latest metrics
        latest_metric = (
            db.query(L2NetworkMetric)
            .filter(L2NetworkMetric.network == network)
            .order_by(L2NetworkMetric.timestamp.desc())
            .first()
        )

        latest_cost = (
            db.query(L2TransactionCost)
            .filter(L2TransactionCost.network == network)
            .order_by(L2TransactionCost.timestamp.desc())
            .first()
        )

        latest_tvl = (
            db.query(L2TVLMetric)
            .filter(L2TVLMetric.network == network)
            .order_by(L2TVLMetric.timestamp.desc())
            .first()
        )

        if latest_metric:
            comparison[network] = {
                "gas_price_gwei": latest_metric.gas_price_gwei,
                "gas_savings_percent": latest_metric.gas_savings_percent,
                "transaction_count": latest_metric.transaction_count,
                "eth_transfer_cost_usd": (
                    latest_cost.eth_transfer_cost_usd if latest_cost else None
                ),
                "tvl_usd": latest_tvl.tvl_usd if latest_tvl else None,
                "daily_tps": latest_tvl.daily_tps if latest_tvl else None,
            }

    return comparison


@router.get("/costs/{operation}")
async def get_operation_costs(operation: str, db: Session = Depends(get_db)):
    """Get operation costs across all L2s"""
    valid_operations = ["eth_transfer", "erc20_transfer", "uniswap_swap", "nft_mint"]

    if operation not in valid_operations:
        return {"error": f"Invalid operation. Choose from: {valid_operations}"}

    # Get latest costs for each network
    networks = ["arbitrum", "optimism", "polygon", "base", "ethereum"]
    costs = {}

    for network in networks:
        latest = (
            db.query(L2TransactionCost)
            .filter(L2TransactionCost.network == network)
            .order_by(L2TransactionCost.timestamp.desc())
            .first()
        )

        if latest:
            cost_field = f"{operation}_cost_usd"
            costs[network] = getattr(latest, cost_field, None)

    return {
        "operation": operation,
        "costs": costs,
        "cheapest": min(costs, key=costs.get) if costs else None,
    }


@router.get("/tvl")
async def get_l2_tvl_stats(db: Session = Depends(get_db)):
    """Get L2 TVL statistics"""
    networks = ["arbitrum", "optimism", "polygon", "base"]
    tvl_stats = {}
    total_tvl = 0

    for network in networks:
        latest = (
            db.query(L2TVLMetric)
            .filter(L2TVLMetric.network == network)
            .order_by(L2TVLMetric.timestamp.desc())
            .first()
        )

        if latest:
            tvl_stats[network] = {
                "tvl_usd": latest.tvl_usd,
                "tvl_eth": latest.tvl_eth,
                "market_share_percent": latest.market_share_percent,
                "daily_tps": latest.daily_tps,
            }
            total_tvl += latest.tvl_usd

    return {"total_tvl_usd": total_tvl, "networks": tvl_stats}
