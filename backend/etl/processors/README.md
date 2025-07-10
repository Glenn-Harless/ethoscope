# ETL Processors

## Overview

Processors transform raw collected data into validated, enriched metrics ready for storage and analysis. They handle data validation, aggregation, anomaly detection, and health score calculations.

## Processor Components

### `metric_processor.py` - Data Transformation

Core processor that validates and transforms raw metrics.

**Key Functions:**

1. **Data Validation**
   - Type checking
   - Range validation
   - Required field verification
   - Data consistency checks

2. **Data Transformation**
   - Standardize formats
   - Calculate derived metrics
   - Aggregate related data
   - Add metadata

3. **Metric Categorization**
   - Route metrics by type
   - Group related metrics
   - Tag with metadata

**Processing Flow:**
```python
async def process(self, raw_metrics: List[Dict]) -> Dict[str, List[Dict]]:
    """Process raw metrics into categorized, validated data"""

    processed = {
        'gas_metrics': [],
        'block_metrics': [],
        'mev_metrics': [],
        'l2_metrics': [],
        'mempool_metrics': []
    }

    for metric in raw_metrics:
        # Validate
        if not self._validate_metric(metric):
            continue

        # Transform
        transformed = self._transform_metric(metric)

        # Categorize
        metric_type = metric.get('metric_type')
        if metric_type in processed:
            processed[metric_type].append(transformed)

    return processed
```

**Validation Rules:**
```python
def _validate_metric(self, metric: Dict) -> bool:
    """Validate metric data"""
    # Check required fields
    required = ['metric_type', 'timestamp']
    if not all(field in metric for field in required):
        return False

    # Type-specific validation
    validators = {
        'gas': self._validate_gas_metric,
        'block': self._validate_block_metric,
        'mev': self._validate_mev_metric
    }

    metric_type = metric['metric_type']
    if metric_type in validators:
        return validators[metric_type](metric)

    return True
```

### `health_score_calculator.py` - Network Health Analysis

Advanced health scoring with statistical analysis.

**Health Components:**

1. **Gas Efficiency (25%)**
   - Gas price stability
   - Transaction success rate
   - Gas utilization

2. **Network Stability (20%)**
   - Block time consistency
   - Reorganization frequency
   - Finality metrics

3. **MEV Fairness (15%)**
   - MEV distribution
   - Builder diversity
   - Censorship resistance

4. **Block Production (15%)**
   - Block fullness
   - Empty block ratio
   - Production rate

5. **Mempool Health (15%)**
   - Transaction backlog
   - Confirmation times
   - Priority fee trends

6. **Validator Performance (10%)**
   - Participation rate
   - Missed slots
   - Sync committee performance

**Calculation Method:**
```python
async def calculate_health_score(self, db: Session) -> Dict[str, Any]:
    """Calculate comprehensive network health"""

    # Get component scores
    gas_score = await self._calculate_gas_efficiency_score(db)
    stability_score = await self._calculate_network_stability_score(db)
    mev_score = await self._calculate_mev_fairness_score(db)
    block_score = await self._calculate_block_production_score(db)
    mempool_score = await self._calculate_mempool_health_score(db)
    validator_score = await self._calculate_validator_performance_score(db)

    # Weighted average
    overall_score = (
        gas_score * self.weights['gas_efficiency'] +
        stability_score * self.weights['network_stability'] +
        mev_score * self.weights['mev_fairness'] +
        block_score * self.weights['block_production'] +
        mempool_score * self.weights['mempool_health'] +
        validator_score * self.weights['validator_performance']
    )

    return {
        'overall_score': overall_score,
        'components': {
            'gas_efficiency': gas_score,
            'network_stability': stability_score,
            'mev_fairness': mev_score,
            'block_production': block_score,
            'mempool_health': mempool_score,
            'validator_performance': validator_score
        },
        'timestamp': datetime.utcnow(),
        'anomalies': self._detect_anomalies(scores)
    }
```

**Dynamic Baselines:**

The calculator uses multiple time windows for context:
- **Short-term**: 1 hour (immediate trends)
- **Medium-term**: 24 hours (daily patterns)
- **Long-term**: 7 days (weekly trends)

```python
baseline_windows = {
    "short": timedelta(hours=1),
    "medium": timedelta(hours=24),
    "long": timedelta(days=7)
}
```

**Anomaly Detection:**

Two methods for identifying anomalies:

1. **Z-Score Method**
```python
def _calculate_z_score(self, value: float, data: List[float]) -> float:
    """Calculate Z-score for anomaly detection"""
    mean = np.mean(data)
    std = np.std(data)

    if std == 0:
        return 0

    return (value - mean) / std

# Anomaly if |z_score| > 3
is_anomaly = abs(z_score) > self.z_score_threshold
```

2. **IQR Method**
```python
def _calculate_iqr_bounds(self, data: List[float]) -> Tuple[float, float]:
    """Calculate IQR bounds for outlier detection"""
    q1 = np.percentile(data, 25)
    q3 = np.percentile(data, 75)
    iqr = q3 - q1

    lower_bound = q1 - (self.iqr_multiplier * iqr)
    upper_bound = q3 + (self.iqr_multiplier * iqr)

    return lower_bound, upper_bound

# Anomaly if outside bounds
is_outlier = value < lower_bound or value > upper_bound
```

## Processing Patterns

### Batch Processing

Process metrics in batches for efficiency:

```python
async def process_batch(self, metrics: List[Dict], batch_size: int = 1000):
    """Process metrics in batches"""
    for i in range(0, len(metrics), batch_size):
        batch = metrics[i:i + batch_size]
        processed = await self._process_batch(batch)
        yield processed
```

### Parallel Processing

Use async operations for concurrent processing:

```python
async def process_parallel(self, metric_groups: Dict[str, List]):
    """Process different metric types in parallel"""
    tasks = []

    for metric_type, metrics in metric_groups.items():
        processor = self._get_processor(metric_type)
        tasks.append(processor.process(metrics))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return self._merge_results(results)
```

### Stream Processing

Handle continuous data streams:

```python
async def process_stream(self, metric_stream):
    """Process continuous stream of metrics"""
    buffer = []
    buffer_size = 100
    flush_interval = 5.0  # seconds
    last_flush = time.time()

    async for metric in metric_stream:
        buffer.append(metric)

        # Flush on size or time
        if len(buffer) >= buffer_size or \
           time.time() - last_flush > flush_interval:
            await self._flush_buffer(buffer)
            buffer.clear()
            last_flush = time.time()
```

## Adding New Processors

### 1. Create Processor Class

```python
# backend/etl/processors/custom_processor.py
from typing import Dict, List, Any
import numpy as np

class CustomProcessor:
    """Process custom metrics"""

    def __init__(self):
        self.thresholds = {
            'critical': 0.9,
            'warning': 0.7,
            'normal': 0.5
        }

    async def process(self, metrics: List[Dict]) -> List[Dict]:
        """Process custom metrics"""
        processed = []

        for metric in metrics:
            # Validate
            if not self._validate(metric):
                continue

            # Enrich
            enriched = self._enrich(metric)

            # Analyze
            enriched['status'] = self._analyze_status(enriched)

            processed.append(enriched)

        return processed

    def _validate(self, metric: Dict) -> bool:
        """Validate metric data"""
        return 'value' in metric and metric['value'] >= 0

    def _enrich(self, metric: Dict) -> Dict:
        """Add calculated fields"""
        metric['normalized_value'] = metric['value'] / 100
        metric['category'] = self._categorize(metric['value'])
        return metric

    def _analyze_status(self, metric: Dict) -> str:
        """Determine metric status"""
        value = metric['normalized_value']

        if value >= self.thresholds['critical']:
            return 'critical'
        elif value >= self.thresholds['warning']:
            return 'warning'
        else:
            return 'normal'
```

### 2. Integrate with Pipeline

```python
# In metric_processor.py or pipeline.py
from backend.etl.processors.custom_processor import CustomProcessor

# Add to processing chain
self.processors = {
    'custom': CustomProcessor(),
    # ... other processors
}
```

### 3. Add Tests

```python
# backend/tests/etl/processors/test_custom_processor.py
import pytest
from backend.etl.processors.custom_processor import CustomProcessor

@pytest.mark.asyncio
async def test_custom_processing():
    processor = CustomProcessor()

    metrics = [
        {'value': 95, 'timestamp': '2024-01-01'},
        {'value': 75, 'timestamp': '2024-01-01'},
        {'value': 45, 'timestamp': '2024-01-01'}
    ]

    processed = await processor.process(metrics)

    assert len(processed) == 3
    assert processed[0]['status'] == 'critical'
    assert processed[1]['status'] == 'warning'
    assert processed[2]['status'] == 'normal'
```

## Performance Optimization

### Caching Calculations

Cache expensive computations:

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def _calculate_percentile(values: tuple, percentile: float) -> float:
    """Cached percentile calculation"""
    return np.percentile(values, percentile)
```

### Numpy Operations

Use vectorized operations:

```python
# Slow
results = []
for value in values:
    results.append(value * 2 + 10)

# Fast
results = np.array(values) * 2 + 10
```

### Database Queries

Optimize database access:

```python
# Use single query with aggregation
metrics = db.query(
    func.avg(GasMetric.gas_price_gwei).label('avg'),
    func.stddev(GasMetric.gas_price_gwei).label('std'),
    func.count(GasMetric.id).label('count')
).filter(
    GasMetric.timestamp >= start_time
).first()

# Instead of multiple queries
avg = db.query(func.avg(GasMetric.gas_price_gwei))...
std = db.query(func.stddev(GasMetric.gas_price_gwei))...
count = db.query(func.count(GasMetric.id))...
```

## Error Handling

### Graceful Degradation

Continue processing on partial failures:

```python
async def process_with_fallback(self, metrics: List[Dict]) -> List[Dict]:
    """Process with graceful degradation"""
    processed = []
    failed = []

    for metric in metrics:
        try:
            result = await self._process_single(metric)
            processed.append(result)
        except ValidationError as e:
            self.logger.warning(f"Validation failed: {e}")
            failed.append(metric)
        except Exception as e:
            self.logger.error(f"Processing failed: {e}")
            # Continue with next metric

    # Log summary
    self.logger.info(
        f"Processed {len(processed)} metrics, "
        f"{len(failed)} failed validation"
    )

    return processed
```

### Data Recovery

Implement recovery strategies:

```python
async def process_with_recovery(self, metric: Dict) -> Dict:
    """Process with data recovery"""

    # Try to fill missing data
    if 'timestamp' not in metric:
        metric['timestamp'] = datetime.utcnow()

    if 'value' not in metric and 'raw_value' in metric:
        # Try to derive from raw data
        metric['value'] = self._parse_raw_value(metric['raw_value'])

    # Use defaults for non-critical fields
    metric.setdefault('source', 'unknown')
    metric.setdefault('confidence', 0.5)

    return metric
```

## Monitoring & Debugging

### Processing Metrics

Track processing performance:

```python
from backend.api.middleware.monitoring import (
    processing_duration_histogram,
    processed_metrics_counter
)

async def process(self, metrics: List[Dict]) -> List[Dict]:
    """Process with monitoring"""
    start_time = time.time()

    try:
        processed = await self._do_processing(metrics)

        # Record metrics
        duration = time.time() - start_time
        processing_duration_histogram.observe(duration)
        processed_metrics_counter.inc(len(processed))

        return processed
    finally:
        self.logger.info(
            f"Processing completed in {time.time() - start_time:.2f}s"
        )
```

### Debug Mode

Enable detailed logging:

```python
if os.getenv('DEBUG_PROCESSING', 'false').lower() == 'true':
    self.logger.debug(f"Processing metric: {metric}")
    self.logger.debug(f"Validation result: {is_valid}")
    self.logger.debug(f"Transformed data: {transformed}")
```

## Best Practices

1. **Immutability**: Don't modify input data
2. **Idempotency**: Same input = same output
3. **Error Context**: Include metric info in errors
4. **Type Safety**: Use type hints throughout
5. **Testing**: Test edge cases and failures
6. **Documentation**: Document assumptions and limitations

## Future Enhancements

- [ ] Machine learning anomaly detection
- [ ] Real-time streaming processing
- [ ] Custom processor plugins
- [ ] Processing pipeline visualization
- [ ] Automatic data quality scoring
- [ ] Historical trend analysis
