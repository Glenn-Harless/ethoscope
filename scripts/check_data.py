#!/usr/bin/env python3
"""Check what data has been collected in the database"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import func

from backend.models.database import SessionLocal
from backend.models.l2_metrics import L2NetworkMetric, L2TransactionCost, L2TVLMetric
from backend.models.metrics import (
    BlockMetric,
    GasMetric,
    MempoolMetric,
    NetworkHealthScore,
)
from backend.models.mev_metrics import MEVBlockAnalysis, MEVBoostStats, MEVMetric


def check_data_collection():
    """Check what data has been collected"""
    db = SessionLocal()

    try:
        print("=" * 60)
        print("ETHOSCOPE DATA COLLECTION STATUS")
        print("=" * 60)
        print(f"Check Time: {datetime.utcnow()}")
        print()

        # Define time windows
        last_hour = datetime.utcnow() - timedelta(hours=1)
        last_24h = datetime.utcnow() - timedelta(hours=24)

        # Check each metric type
        metrics = [
            ("Block Metrics", BlockMetric),
            ("Gas Metrics", GasMetric),
            ("Mempool Metrics", MempoolMetric),
            ("MEV Metrics", MEVMetric),
            ("MEV Boost Stats", MEVBoostStats),
            ("MEV Block Analysis", MEVBlockAnalysis),
            ("L2 Network Metrics", L2NetworkMetric),
            ("L2 Transaction Costs", L2TransactionCost),
            ("L2 TVL Metrics", L2TVLMetric),
            ("Network Health Scores", NetworkHealthScore),
        ]

        for name, model in metrics:
            total = db.query(model).count()
            recent = db.query(model).filter(model.timestamp >= last_hour).count()
            today = db.query(model).filter(model.timestamp >= last_24h).count()

            if hasattr(model, "timestamp"):
                latest = db.query(model).order_by(model.timestamp.desc()).first()
                latest_time = latest.timestamp if latest else None
            else:
                latest_time = None

            print(f"{name}:")
            print(f"  Total records: {total}")
            print(f"  Last 24h: {today}")
            print(f"  Last hour: {recent}")
            if latest_time:
                time_ago = datetime.utcnow() - latest_time
                print(f"  Latest: {time_ago.total_seconds():.0f} seconds ago")
            print()

        # Show sample data for working collectors
        print("-" * 60)
        print("SAMPLE DATA FROM WORKING COLLECTORS:")
        print("-" * 60)

        # Latest block
        latest_block = db.query(BlockMetric).order_by(BlockMetric.block_number.desc()).first()
        if latest_block:
            print("\nLatest Block:")
            print(f"  Number: {latest_block.block_number}")
            print(f"  Time: {latest_block.block_timestamp}")
            print(f"  Gas Used: {latest_block.gas_used:,}")
            if hasattr(latest_block, "base_fee_gwei"):
                print(f"  Base Fee: {latest_block.base_fee_gwei:.2f} Gwei")
            else:
                print("  Base Fee: Not available")

        # Latest gas metrics
        latest_gas = db.query(GasMetric).order_by(GasMetric.timestamp.desc()).first()
        if latest_gas:
            print("\nLatest Gas Prices:")
            print(f"  Average: {latest_gas.gas_price_gwei:.2f} Gwei")
            if hasattr(latest_gas, "fast_gas_price"):
                print(f"  Fast: {latest_gas.fast_gas_price:.2f} Gwei")
            if hasattr(latest_gas, "gas_price_p50"):
                print(
                    f"  Percentiles: P25={latest_gas.gas_price_p25:.2f}, "
                    f"P50={latest_gas.gas_price_p50:.2f}, P75={latest_gas.gas_price_p75:.2f}"
                )

        # MEV data
        mev_count = db.query(MEVMetric).filter(MEVMetric.timestamp >= last_hour).count()
        if mev_count > 0:
            total_mev = (
                db.query(func.sum(MEVMetric.total_mev_revenue))
                .filter(MEVMetric.timestamp >= last_hour)
                .scalar()
            )
            print("\nMEV Activity (Last Hour):")
            print(f"  Blocks with MEV: {mev_count}")
            print(f"  Total MEV Revenue: {total_mev:.4f} ETH")

            # Top builders
            top_builders = (
                db.query(MEVMetric.builder_pubkey, func.count(MEVMetric.id).label("count"))
                .filter(MEVMetric.timestamp >= last_hour)
                .group_by(MEVMetric.builder_pubkey)
                .order_by(func.count(MEVMetric.id).desc())
                .limit(3)
                .all()
            )

            if top_builders:
                print("  Top Builders:")
                for builder, count in top_builders:
                    print(f"    {builder[:16]}...: {count} blocks")

        # L2 data
        l2_networks = db.query(L2NetworkMetric.network).distinct().all()
        if l2_networks:
            print("\nActive L2 Networks:")
            for (network,) in l2_networks:
                latest = (
                    db.query(L2NetworkMetric)
                    .filter(L2NetworkMetric.network == network)
                    .order_by(L2NetworkMetric.timestamp.desc())
                    .first()
                )
                if latest:
                    print(
                        f"  {network}: Gas {latest.gas_price_gwei:.4f} Gwei, "
                        f"Savings: {latest.gas_savings_percent:.1f}%"
                    )

    except Exception as e:
        print(f"Error checking data: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    check_data_collection()
