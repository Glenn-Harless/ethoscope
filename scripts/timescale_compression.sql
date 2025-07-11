-- Enable compression on older data
ALTER TABLE gas_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'timestamp',
    timescaledb.compress_orderby = 'timestamp DESC'
);

ALTER TABLE mev_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'timestamp'
);

ALTER TABLE l2_network_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'network,timestamp'
);

-- Add compression policies (compress data older than 7 days)
SELECT add_compression_policy('gas_metrics', INTERVAL '7 days');
SELECT add_compression_policy('mev_metrics', INTERVAL '7 days');
SELECT add_compression_policy('l2_network_metrics', INTERVAL '7 days');
SELECT add_compression_policy('block_metrics', INTERVAL '7 days');

-- Add retention policies (optional - delete data older than 90 days)
SELECT add_retention_policy('gas_metrics', INTERVAL '90 days');
SELECT add_retention_policy('mev_metrics', INTERVAL '90 days');

-- Create continuous aggregates for common queries
CREATE MATERIALIZED VIEW gas_metrics_5min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', timestamp) AS bucket,
    AVG(gas_price_gwei) AS avg_gas_price,
    MAX(gas_price_gwei) AS max_gas_price,
    MIN(gas_price_gwei) AS min_gas_price,
    AVG(gas_price_p50) AS avg_p50,
    AVG(gas_price_p95) AS avg_p95
FROM gas_metrics
GROUP BY bucket;

-- Add refresh policy
SELECT add_continuous_aggregate_policy('gas_metrics_5min',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '5 minutes');
