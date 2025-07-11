-- Convert new tables to hypertables
SELECT create_hypertable('mev_metrics', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

SELECT create_hypertable('l2_network_metrics', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

SELECT create_hypertable('l2_transaction_costs', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Create continuous aggregates for L2 comparison
CREATE MATERIALIZED VIEW l2_costs_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    network,
    AVG(eth_transfer_cost_usd) AS avg_eth_transfer_cost,
    AVG(uniswap_swap_cost_usd) AS avg_swap_cost
FROM l2_transaction_costs
GROUP BY bucket, network;

-- Create indexes for performance
CREATE INDEX idx_mev_builder ON mev_metrics(builder_address);
CREATE INDEX idx_l2_network ON l2_network_metrics(network, timestamp DESC);

-- Add compression for new tables
ALTER TABLE mev_metrics SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'timestamp'
);

SELECT add_compression_policy('mev_metrics', INTERVAL '7 days');
