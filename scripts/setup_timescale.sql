-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Convert tables to hypertables (only if tables exist)
SELECT create_hypertable('block_metrics', 'block_timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);
SELECT create_hypertable('gas_metrics', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);
SELECT create_hypertable('mempool_metrics', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);
SELECT create_hypertable('network_health_scores', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Create continuous aggregates for common queries
CREATE MATERIALIZED VIEW gas_metrics_5min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', timestamp) AS bucket,
    AVG(gas_price_gwei) AS avg_gas_price,
    MIN(gas_price_gwei) AS min_gas_price,
    MAX(gas_price_gwei) AS max_gas_price,
    AVG(pending_transactions) AS avg_pending_tx
FROM gas_metrics
GROUP BY bucket;

-- Add retention policy (keep raw data for 30 days)
SELECT add_retention_policy('gas_metrics', INTERVAL '30 days');
SELECT add_retention_policy('mempool_metrics', INTERVAL '30 days');

-- Add compression policy (compress data older than 7 days)
ALTER TABLE gas_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'timestamp'
);

SELECT add_compression_policy('gas_metrics', INTERVAL '7 days');
