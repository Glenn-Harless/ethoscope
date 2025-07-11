# ETL Collectors

## Overview

Collectors are responsible for gathering raw data from external sources. Each collector specializes in a specific data type or source, implementing the base collector interface for consistency and error handling.

## Base Collector Pattern

All collectors inherit from `BaseCollector` which provides:
- Logging setup
- Error handling
- Collection timing
- Standard interface

```python
from .base import BaseCollector

class YourCollector(BaseCollector):
    def __init__(self):
        super().__init__("your_collector_name")
        # Initialize your specific requirements

    async def collect(self) -> List[Dict[str, Any]]:
        """Main collection method - must be implemented"""
        pass
```

## Available Collectors

### `alchemy_collector.py` - Ethereum Mainnet Data

Collects core Ethereum metrics using Alchemy's API.

**Data Collected:**
- **Gas Prices**: Current gas price with percentiles
- **Block Information**: Block details, gas usage, transaction count
- **Mempool Stats**: Pending transactions, gas price distribution

**Configuration:**
```python
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
```

**Collection Methods:**
- `_collect_gas_price()` - Current gas price
- `_collect_block_metrics()` - Latest block data
- `_collect_mempool_stats()` - Mempool analysis

**Output Format:**
```json
{
    "metric_type": "gas",
    "timestamp": "2024-01-01T00:00:00Z",
    "gas_price_wei": 25000000000,
    "gas_price_gwei": 25.0,
    "pending_transactions": 150
}
```

### `flashbots_collector.py` - MEV Data

Collects Maximum Extractable Value (MEV) data from MEV-Boost relays.

**Data Sources:**
- Flashbots relay
- Ultra Sound relay
- BloXroute (max profit & ethical)
- Blocknative
- Manifold
- Agnostic

**Key Features:**
- Multi-relay aggregation
- Circuit breaker pattern for resilience
- Request caching with TTL
- Connection pooling

**Data Collected:**
- Block-level MEV revenue
- Builder statistics
- Gas utilization
- MEV intensity analysis

**Output Format:**
```json
{
    "metric_type": "mev",
    "block_number": 18000000,
    "total_mev_revenue": 2.5,
    "builder_pubkey": "0x...",
    "gas_utilization": 95.5,
    "relay_source": "flashbots"
}
```

**MEV Analysis:**
```json
{
    "metric_type": "mev_block_analysis",
    "mev_intensity": "high",
    "value_eth": 5.2,
    "likely_mev_type": "likely_contains_liquidations",
    "gas_efficiency": 0.98
}
```

### `l2_collector.py` - Layer 2 Networks

Collects metrics from multiple L2 networks for comparison.

**Supported Networks:**
- **Arbitrum One** - Optimistic rollup
- **Optimism** - Optimistic rollup
- **Polygon PoS** - Sidechain
- **Base** - Optimistic rollup
- **zkSync Era** - ZK rollup
- **Scroll** - ZK rollup

**Data Collected:**
- Gas prices and savings vs L1
- Block times and throughput
- Transaction counts
- Network-specific metrics (sequencer health, etc.)

**Configuration:**
```python
# Uses Alchemy for most networks
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")

# Network-specific RPCs
networks = {
    "arbitrum": {
        "rpc": f"https://arb-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}",
        "chain_id": 42161
    },
    "zksync": {
        "rpc": "https://mainnet.era.zksync.io",
        "chain_id": 324
    }
    # ... more networks
}
```

**Output Format:**
```json
{
    "metric_type": "l2_network",
    "network": "arbitrum",
    "gas_price_gwei": 0.1,
    "gas_savings_percent": 99.7,
    "transaction_count": 1500,
    "block_time": 0.25
}
```

## Collector Patterns

### Error Handling

All collectors implement robust error handling:

```python
async def collect(self) -> List[Dict[str, Any]]:
    metrics = []

    try:
        # Primary collection
        data = await self._fetch_data()
        metrics.extend(self._process_data(data))
    except httpx.TimeoutException:
        self.logger.warning("API timeout - using cached data")
        # Fallback to cache
    except Exception as e:
        self.logger.error(f"Collection failed: {e}")
        # Return empty list, don't crash pipeline

    return metrics
```

### Rate Limiting

Respect API rate limits:

```python
class RateLimitedCollector(BaseCollector):
    def __init__(self):
        super().__init__("rate_limited")
        self.semaphore = asyncio.Semaphore(10)  # Max 10 concurrent
        self.last_request = 0
        self.min_interval = 0.1  # 100ms between requests

    async def _rate_limited_request(self, url):
        async with self.semaphore:
            # Ensure minimum interval
            elapsed = time.time() - self.last_request
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)

            self.last_request = time.time()
            return await self.client.get(url)
```

### Caching

Implement caching for expensive operations:

```python
from cachetools import TTLCache

class CachedCollector(BaseCollector):
    def __init__(self):
        super().__init__("cached")
        self.cache = TTLCache(maxsize=100, ttl=60)  # 60 second cache

    async def _get_cached_data(self, key):
        if key in self.cache:
            return self.cache[key]

        data = await self._fetch_fresh_data(key)
        self.cache[key] = data
        return data
```

### Circuit Breaker

Prevent cascading failures:

```python
from backend.utils.circuit_breaker import circuit_breaker

@circuit_breaker(failure_threshold=5, recovery_timeout=60)
async def _external_api_call(self):
    # If this fails 5 times, circuit opens for 60 seconds
    return await self.client.get(self.api_url)
```

## Adding a New Collector

### 1. Create Collector File

```python
# backend/etl/collectors/new_source_collector.py
from typing import List, Dict, Any
import httpx
from .base import BaseCollector

class NewSourceCollector(BaseCollector):
    def __init__(self):
        super().__init__("new_source")
        self.api_url = "https://api.newsource.com"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def collect(self) -> List[Dict[str, Any]]:
        """Collect data from new source"""
        try:
            response = await self.client.get(f"{self.api_url}/data")
            response.raise_for_status()

            raw_data = response.json()
            return self._transform_data(raw_data)

        except Exception as e:
            self.logger.error(f"Failed to collect from new source: {e}")
            return []

    def _transform_data(self, raw_data: dict) -> List[Dict[str, Any]]:
        """Transform to standard metric format"""
        metrics = []

        for item in raw_data.get("items", []):
            metrics.append({
                "metric_type": "new_metric",
                "timestamp": datetime.utcnow(),
                "value": item["value"],
                "metadata": {
                    "source": "new_source",
                    "original_id": item["id"]
                }
            })

        return metrics

    async def close(self):
        """Cleanup resources"""
        await self.client.aclose()
```

### 2. Register in Pipeline

```python
# backend/etl/pipeline.py
from backend.etl.collectors.new_source_collector import NewSourceCollector

# In ETLPipeline.__init__
self.collectors = [
    AlchemyCollector(),
    FlashbotsCollector(),
    L2Collector(),
    NewSourceCollector()  # Add your collector
]
```

### 3. Add Tests

```python
# backend/tests/etl/collectors/test_new_source_collector.py
import pytest
from backend.etl.collectors.new_source_collector import NewSourceCollector

@pytest.mark.asyncio
async def test_new_source_collection():
    collector = NewSourceCollector()

    # Mock the API response
    with mock.patch.object(collector.client, 'get') as mock_get:
        mock_get.return_value.json.return_value = {
            "items": [{"id": 1, "value": 100}]
        }

        metrics = await collector.collect()

        assert len(metrics) == 1
        assert metrics[0]["metric_type"] == "new_metric"
        assert metrics[0]["value"] == 100
```

## Best Practices

### 1. Data Validation
Always validate external data:
```python
def _validate_block_data(self, block: dict) -> bool:
    required_fields = ['number', 'timestamp', 'gasUsed', 'gasLimit']
    return all(field in block for field in required_fields)
```

### 2. Graceful Degradation
Handle partial failures:
```python
async def collect(self) -> List[Dict[str, Any]]:
    metrics = []

    # Try primary source
    try:
        metrics.extend(await self._collect_primary())
    except Exception as e:
        self.logger.warning(f"Primary collection failed: {e}")

    # Try secondary source regardless
    try:
        metrics.extend(await self._collect_secondary())
    except Exception as e:
        self.logger.warning(f"Secondary collection failed: {e}")

    return metrics  # Return what we could collect
```

### 3. Resource Management
Always clean up:
```python
async def close(self):
    """Clean up resources"""
    if hasattr(self, 'client'):
        await self.client.aclose()
    if hasattr(self, 'ws_connection'):
        await self.ws_connection.close()
```

### 4. Monitoring
Add metrics for observability:
```python
async def collect(self) -> List[Dict[str, Any]]:
    start_time = time.time()

    try:
        metrics = await self._do_collection()
        collection_duration = time.time() - start_time

        self.logger.info(
            f"Collected {len(metrics)} metrics in {collection_duration:.2f}s"
        )

        return metrics
    except Exception as e:
        self.logger.error(
            f"Collection failed after {time.time() - start_time:.2f}s: {e}"
        )
        raise
```

## Troubleshooting

### Common Issues

1. **API Key Errors**
   - Check environment variables
   - Verify key permissions
   - Check rate limits

2. **Network Timeouts**
   - Increase timeout values
   - Check network connectivity
   - Verify API endpoint status

3. **Data Format Changes**
   - Log raw responses for debugging
   - Add flexible parsing
   - Version your transformations

### Debug Mode

Enable detailed logging:
```python
# Set in environment
LOG_LEVEL=DEBUG

# In collector
self.logger.debug(f"Raw API response: {response.json()}")
```

### Performance Issues

1. **Slow Collection**
   - Use concurrent requests
   - Implement caching
   - Optimize transformations

2. **Memory Usage**
   - Process data in chunks
   - Clear large objects
   - Use generators for large datasets

## Future Enhancements

- [ ] WebSocket collectors for real-time data
- [ ] GraphQL support for efficient queries
- [ ] Collector health metrics
- [ ] Automatic retry with exponential backoff
- [ ] Data source failover
- [ ] Collector plugin system
