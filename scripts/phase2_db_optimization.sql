-- Optimize MEV queries
CREATE INDEX idx_mev_sandwich_attacks ON mev_metrics(sandwich_attack_count)
WHERE sandwich_attack_count > 0;

CREATE INDEX idx_mev_builder_revenue ON mev_metrics(builder_address, total_mev_revenue);

-- Materialized view for L2 comparison
CREATE MATERIALIZED VIEW l2_comparison_latest AS
SELECT DISTINCT ON (network)
    network,
    gas_price_gwei,
    gas_savings_percent,
    timestamp,
    transaction_count,
    sequencer_latency_ms
FROM l2_network_metrics
ORDER BY network, timestamp DESC;

-- Refresh every minute
CREATE OR REPLACE FUNCTION refresh_l2_comparison()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY l2_comparison_latest;
END;
$$ LANGUAGE plpgsql;

-- Create scheduled job for refresh (using pg_cron)
SELECT cron.schedule('refresh-l2-comparison', '*/1 * * * *', 'SELECT refresh_l2_comparison();');

-- Materialized view for health score trends
CREATE MATERIALIZED VIEW health_score_hourly AS
SELECT
    time_bucket('1 hour', timestamp) AS hour,
    AVG(overall_score) as avg_score,
    MIN(overall_score) as min_score,
    MAX(overall_score) as max_score,
    COUNT(*) as sample_count
FROM network_health_scores
GROUP BY hour
ORDER BY hour DESC;

-- Index for anomaly detection queries
CREATE INDEX idx_gas_metrics_percentiles ON gas_metrics(timestamp)
WHERE gas_price_p95 IS NOT NULL;

-- Composite indexes for common query patterns
CREATE INDEX idx_mev_metrics_composite ON mev_metrics(timestamp, block_number, total_mev_revenue);
CREATE INDEX idx_block_metrics_time_range ON block_metrics(block_timestamp, block_number);

-- Partial indexes for performance
CREATE INDEX idx_high_gas_prices ON gas_metrics(timestamp, gas_price_gwei)
WHERE gas_price_gwei > 100;

CREATE INDEX idx_sandwich_attacks_only ON mev_metrics(timestamp, sandwich_attack_count, sandwich_attack_profit_eth)
WHERE sandwich_attack_count > 0;
