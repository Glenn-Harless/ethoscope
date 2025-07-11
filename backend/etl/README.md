# ETL Pipeline

## Overview

The ETL (Extract, Transform, Load) pipeline is the heart of Ethoscope's data collection system. It continuously gathers blockchain metrics from multiple sources, processes them for consistency and quality, and stores them in TimescaleDB for efficient time-series queries.

## Directory Structure

```
etl/
├── collectors/      # Data collection from external sources
├── processors/      # Data transformation and analysis
├── loaders/        # Database persistence layer
├── config.py       # Configuration settings
├── pipeline.py     # Main orchestration logic
└── validators.py   # Data validation rules
```

## Core Components

### `pipeline.py` - ETL Orchestrator

The main pipeline that:
- Manages collector lifecycle
- Coordinates data flow
- Handles error recovery
- Broadcasts real-time updates via WebSocket

Key features:
- Configurable collection intervals (default: 12 seconds)
- Graceful shutdown handling
- Automatic retry with exponential backoff
- Performance metrics logging

### `config.py` - Configuration Management

Centralized settings using Pydantic:
- Environment variable loading
- Type validation
- Default values
- Nested configuration structures

Configuration categories:
- Database settings
- Redis configuration
- API keys
- Collection intervals
- Logging preferences

### `validators.py` - Data Quality

Validation functions ensuring:
- Data completeness
- Type correctness
- Range validation
- Consistency checks

## Data Flow

```
1. Collection Phase
   ├── AlchemyCollector → Gas prices, blocks, mempool
   ├── FlashbotsCollector → MEV data from relays
   └── L2Collector → Multi-chain metrics

2. Processing Phase
   ├── MetricProcessor → Validation and transformation
   └── HealthScoreCalculator → Network health analysis

3. Loading Phase
   ├── DatabaseLoader → PostgreSQL/TimescaleDB
   └── WebSocketManager → Real-time broadcasts

4. Post-Processing
   └── Cache updates, alerts, cleanup
```

## Collectors

### Available Collectors

1. **AlchemyCollector** (`collectors/alchemy_collector.py`)
   - Gas price metrics
   - Block information
   - Mempool statistics
   - Pending transaction analysis

2. **FlashbotsCollector** (`collectors/flashbots_collector.py`)
   - MEV-Boost relay data
   - Builder statistics
   - Block value analysis
   - MEV type estimation

3. **L2Collector** (`collectors/l2_collector.py`)
   - Multi-chain support (Arbitrum, Optimism, Base, zkSync, Scroll)
   - Gas comparison metrics
   - Transaction throughput
   - Bridge activity

### Collector Interface

All collectors inherit from `BaseCollector`:

```python
class YourCollector(BaseCollector):
    async def collect(self) -> List[Dict[str, Any]]:
        """Collect and return metrics"""
        pass
```

## Processors

### MetricProcessor (`processors/metric_processor.py`)

Handles:
- Data validation
- Type conversion
- Metric aggregation
- Anomaly flagging

### HealthScoreCalculator (`processors/health_score_calculator.py`)

Calculates network health using:
- Gas efficiency (25%)
- Network stability (20%)
- MEV fairness (15%)
- Block production (15%)
- Mempool health (15%)
- Validator performance (10%)

Features:
- Dynamic baseline calculation
- Statistical anomaly detection (Z-score, IQR)
- Multi-window analysis (1h, 24h, 7d)

## Running the Pipeline

### Standalone Mode
```bash
# Run ETL pipeline directly
poetry run python -m backend.etl.pipeline
```

### With API Server
The pipeline starts automatically with the API:
```bash
poetry run uvicorn backend.api.main:app
```

### Configuration

Set environment variables:
```env
# Collection intervals (seconds)
ETL_COLLECT_INTERVAL=12
ETL_HEALTH_CHECK_INTERVAL=60

# Feature flags
ETL_ENABLE_MEV=true
ETL_ENABLE_L2=true

# Performance
ETL_MAX_WORKERS=10
ETL_BATCH_SIZE=1000
```

## Adding New Data Sources

### 1. Create a Collector

```python
# backend/etl/collectors/your_collector.py
from .base import BaseCollector
from typing import List, Dict, Any

class YourCollector(BaseCollector):
    def __init__(self):
        super().__init__("your_collector")
        self.api_client = YourAPIClient()

    async def collect(self) -> List[Dict[str, Any]]:
        try:
            data = await self.api_client.fetch_data()
            return self._transform_data(data)
        except Exception as e:
            self.logger.error(f"Collection failed: {e}")
            return []

    def _transform_data(self, raw_data):
        # Transform to standard format
        return [{
            'metric_type': 'your_metric',
            'timestamp': datetime.utcnow(),
            'value': data['value'],
            # ... other fields
        }]
```

### 2. Register in Pipeline

```python
# backend/etl/pipeline.py
from .collectors.your_collector import YourCollector

# In __init__
self.collectors.append(YourCollector())
```

### 3. Add Validation Rules

```python
# backend/etl/validators.py
def validate_your_metric(data: Dict[str, Any]) -> bool:
    required_fields = ['value', 'timestamp']
    return all(field in data for field in required_fields)
```

## Error Handling

### Collector Failures
- Individual collector failures don't stop the pipeline
- Failed collections are logged and skipped
- Retry logic with exponential backoff

### Processing Errors
- Invalid data is logged and discarded
- Partial batch processing continues
- Error metrics are tracked

### Database Failures
- Transactions ensure data consistency
- Failed batches are retried
- Circuit breaker prevents cascading failures

## Performance Optimization

### Batching
- Collectors return data in batches
- Database inserts are batched (default: 1000 records)
- Reduces database round trips

### Caching
- Redis caching for expensive calculations
- Request deduplication
- TTL-based cache expiration

### Async Operations
- All I/O operations are async
- Concurrent collector execution
- Non-blocking database operations

## Monitoring

### Metrics
- Collection duration per source
- Records processed per cycle
- Error rates by collector
- Pipeline latency

### Logging
Structured logging with levels:
- `INFO`: Normal operations
- `WARNING`: Recoverable issues
- `ERROR`: Failed operations
- `DEBUG`: Detailed troubleshooting

### Health Checks
- Collector status monitoring
- Database connectivity
- External API availability

## Testing

### Unit Tests
```bash
# Test individual collectors
poetry run pytest backend/tests/etl/test_collectors.py

# Test processors
poetry run pytest backend/tests/etl/test_processors.py
```

### Integration Tests
```bash
# Test full pipeline
poetry run pytest backend/tests/etl/test_pipeline_integration.py
```

### Manual Testing
```bash
# Test specific collector
poetry run python scripts/test_collectors.py
```

## Troubleshooting

### Common Issues

1. **Collector Timeout**
   - Check API rate limits
   - Verify network connectivity
   - Increase timeout settings

2. **High Memory Usage**
   - Reduce batch sizes
   - Enable batch processing
   - Check for memory leaks

3. **Data Inconsistency**
   - Verify validator rules
   - Check timezone handling
   - Review transformation logic

### Debug Mode

Enable detailed logging:
```python
# Set in .env
LOG_LEVEL=DEBUG
ETL_DEBUG_MODE=true
```

## Best Practices

1. **Idempotency**: Collectors should be safe to run multiple times
2. **Graceful Degradation**: Handle partial failures without stopping
3. **Resource Management**: Close connections and clean up resources
4. **Data Validation**: Always validate before processing
5. **Error Context**: Include relevant context in error messages

## Future Improvements

- [ ] Dynamic collector loading
- [ ] Distributed processing with Celery
- [ ] Data quality scoring
- [ ] Automated anomaly response
- [ ] Historical data backfill
- [ ] Custom collector plugins
