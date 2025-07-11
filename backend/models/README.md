# Database Models

## Overview

This directory contains SQLAlchemy ORM models that define the database schema for Ethoscope. The models are designed for time-series data storage using PostgreSQL with the TimescaleDB extension, optimized for high-volume blockchain metrics.

## Files

### `database.py` - Database Configuration

Core database setup:
- SQLAlchemy engine configuration
- Session management
- Base model class
- Connection pooling settings

Key components:
```python
# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### `metrics.py` - Core Metrics Models

Time-series metrics for Ethereum mainnet:

1. **BlockMetric**
   - Block-level statistics
   - Gas usage and limits
   - Transaction counts
   - Timestamps and difficulty
   - TimescaleDB hypertable

2. **GasMetric**
   - Gas price snapshots
   - Price percentiles (25th, 50th, 75th, 95th)
   - Pending transaction count
   - Collected every ~12 seconds

3. **MempoolMetric**
   - Mempool size and composition
   - Average/min/max gas prices
   - Transaction backlog

4. **NetworkHealthScore**
   - Calculated health metrics
   - Component scores
   - Overall network health (0-100)
   - Historical tracking

### `mev_metrics.py` - MEV Analytics Models

Maximum Extractable Value (MEV) tracking:

1. **MEVMetric**
   - Per-block MEV data
   - Builder and proposer information
   - Gas utilization
   - Revenue tracking
   - Relay source attribution

2. **MEVBoostStats**
   - Aggregate MEV statistics
   - Average block values
   - Top builder tracking
   - Time-windowed summaries

3. **MEVBlockAnalysis**
   - Block-level MEV characteristics
   - MEV intensity classification
   - Estimated MEV types
   - Gas efficiency metrics

### `l2_metrics.py` - Layer 2 Network Models

Cross-chain comparison metrics:

1. **L2NetworkMetric**
   - Multi-chain support (Arbitrum, Optimism, Base, etc.)
   - Gas price comparisons
   - Transaction throughput
   - Block times and limits

2. **L2ComparisonMetric**
   - Cross-chain gas savings
   - Transaction cost analysis
   - Network performance comparison
   - L1 vs L2 metrics

## Database Schema

### Relationships

```
NetworkHealthScore
    ↓ (calculated from)
BlockMetric, GasMetric, MEVMetric, MempoolMetric
    ↓ (time-series data)
TimescaleDB Hypertables
```

### Indexes

Optimized for common queries:
- Timestamp-based queries (all tables)
- Block number lookups
- Network-specific queries (L2)
- Builder/MEV analysis

### TimescaleDB Features

Hypertables created for:
- `block_metrics`
- `gas_metrics`
- `mev_metrics`
- `mempool_metrics`
- `l2_network_metrics`

Benefits:
- Automatic partitioning by time
- Efficient time-range queries
- Data compression
- Continuous aggregates

## Usage Examples

### Creating a New Metric

```python
from backend.models.metrics import GasMetric
from backend.models.database import SessionLocal

# Create a session
db = SessionLocal()

# Create new metric
gas_metric = GasMetric(
    gas_price_wei=30000000000,  # 30 Gwei
    gas_price_gwei=30.0,
    pending_transactions=150,
    gas_price_p25=25.0,
    gas_price_p50=30.0,
    gas_price_p75=35.0,
    gas_price_p95=50.0
)

# Save to database
db.add(gas_metric)
db.commit()
```

### Querying Time-Series Data

```python
from datetime import datetime, timedelta
from sqlalchemy import func

# Get average gas price last hour
one_hour_ago = datetime.utcnow() - timedelta(hours=1)

avg_gas = db.query(func.avg(GasMetric.gas_price_gwei))\
    .filter(GasMetric.timestamp >= one_hour_ago)\
    .scalar()

# Get MEV revenue by builder
builder_revenue = db.query(
    MEVMetric.builder_pubkey,
    func.sum(MEVMetric.total_mev_revenue).label('total_revenue')
).group_by(MEVMetric.builder_pubkey)\
 .order_by(func.sum(MEVMetric.total_mev_revenue).desc())\
 .limit(10)\
 .all()
```

### Working with Network Health

```python
# Get latest health score
latest_health = db.query(NetworkHealthScore)\
    .order_by(NetworkHealthScore.timestamp.desc())\
    .first()

print(f"Network Health: {latest_health.overall_score}/100")
print(f"Gas Score: {latest_health.gas_score}")
print(f"Congestion Score: {latest_health.congestion_score}")
```

## Migrations

### Creating Tables

Initial setup:
```bash
# Create migration
poetry run alembic revision --autogenerate -m "Create metrics tables"

# Apply migration
poetry run alembic upgrade head
```

### Adding TimescaleDB Hypertables

Run after tables are created:
```sql
-- Convert to hypertables
SELECT create_hypertable('block_metrics', 'timestamp');
SELECT create_hypertable('gas_metrics', 'timestamp');
SELECT create_hypertable('mev_metrics', 'timestamp');

-- Set chunk time interval (1 day)
SELECT set_chunk_time_interval('block_metrics', INTERVAL '1 day');
```

### Adding New Models

1. Create model class in appropriate file
2. Import in `alembic/env.py`
3. Generate migration
4. Review and apply

## Best Practices

### Model Design

1. **UUID Primary Keys**: Use for distributed systems
2. **Timestamps**: Always include, index for queries
3. **Enums**: Use for fixed value sets
4. **Indexes**: Add for common query patterns
5. **Constraints**: Enforce data integrity

### Performance

1. **Batch Inserts**: Use `bulk_insert_mappings()`
2. **Query Optimization**: Use `.options()` for eager loading
3. **Connection Pooling**: Configure in `database.py`
4. **Partitioning**: Leverage TimescaleDB features

### Data Types

- **Monetary Values**: Use `Float` for ETH amounts
- **Large Integers**: Use `BigInteger` for wei values
- **Percentages**: Store as `Float` (0-100)
- **Addresses**: Use `String(42)` for Ethereum addresses
- **Hashes**: Use `String(66)` for transaction hashes

## Common Patterns

### Time-Window Queries

```python
def get_metrics_window(db, model, hours=24):
    """Get metrics for time window"""
    start_time = datetime.utcnow() - timedelta(hours=hours)
    return db.query(model)\
        .filter(model.timestamp >= start_time)\
        .order_by(model.timestamp.desc())\
        .all()
```

### Aggregation Queries

```python
def get_hourly_averages(db, model, metric_field):
    """Get hourly averages for a metric"""
    return db.query(
        func.date_trunc('hour', model.timestamp).label('hour'),
        func.avg(getattr(model, metric_field)).label('avg_value')
    ).group_by('hour')\
     .order_by('hour')\
     .all()
```

### Bulk Operations

```python
def bulk_insert_metrics(db, metrics_data):
    """Efficiently insert multiple metrics"""
    db.bulk_insert_mappings(GasMetric, metrics_data)
    db.commit()
```

## Maintenance

### Data Retention

Configure in TimescaleDB:
```sql
-- Keep detailed data for 30 days
SELECT add_retention_policy('gas_metrics', INTERVAL '30 days');

-- Keep aggregated data longer
CREATE MATERIALIZED VIEW gas_metrics_hourly
AS SELECT
    time_bucket('1 hour', timestamp) AS hour,
    avg(gas_price_gwei) as avg_gas_price,
    max(gas_price_gwei) as max_gas_price,
    min(gas_price_gwei) as min_gas_price
FROM gas_metrics
GROUP BY hour;
```

### Compression

Enable after 7 days:
```sql
ALTER TABLE gas_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'timestamp'
);

SELECT add_compression_policy('gas_metrics', INTERVAL '7 days');
```

## Troubleshooting

### Common Issues

1. **Migration Conflicts**
   - Check for uncommitted migrations
   - Verify model imports in `env.py`
   - Review migration history

2. **Performance Issues**
   - Check missing indexes
   - Verify TimescaleDB chunks
   - Monitor connection pool

3. **Data Integrity**
   - Use transactions for related updates
   - Add check constraints
   - Validate before insert
