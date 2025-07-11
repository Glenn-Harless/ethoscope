# Utilities

## Overview

Common utility functions and patterns used throughout the Ethoscope backend. These utilities provide reusable functionality for error handling, resilience patterns, and other cross-cutting concerns.

## Available Utilities

### `circuit_breaker.py` - Fault Tolerance Pattern

Implements the circuit breaker pattern to prevent cascading failures when external services are unavailable.

**How It Works:**

The circuit breaker has three states:
1. **CLOSED** - Normal operation, requests pass through
2. **OPEN** - Service is failing, requests are blocked
3. **HALF-OPEN** - Testing if service has recovered

**State Transitions:**
```
CLOSED --(failures >= threshold)--> OPEN
OPEN --(timeout elapsed)--> HALF-OPEN
HALF-OPEN --(success)--> CLOSED
HALF-OPEN --(failure)--> OPEN
```

**Usage:**

```python
from backend.utils.circuit_breaker import circuit_breaker

# As a decorator
@circuit_breaker(failure_threshold=5, recovery_timeout=60)
async def call_external_api():
    response = await httpx.get("https://api.example.com/data")
    return response.json()

# Manual usage
breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30,
    expected_exceptions=(httpx.HTTPError,)
)

try:
    result = await breaker.call(risky_operation)
except Exception as e:
    # Circuit is open or operation failed
    handle_error(e)
```

**Parameters:**
- `failure_threshold` - Number of failures before opening circuit (default: 5)
- `recovery_timeout` - Seconds to wait before testing recovery (default: 60)
- `expected_exceptions` - Exception types to catch (default: Exception)

**Example with Collector:**

```python
class ResilientCollector(BaseCollector):
    @circuit_breaker(failure_threshold=3, recovery_timeout=120)
    async def _fetch_data(self):
        """Fetch with circuit breaker protection"""
        response = await self.client.get(self.api_url)
        response.raise_for_status()
        return response.json()

    async def collect(self):
        try:
            data = await self._fetch_data()
            return self._process(data)
        except Exception as e:
            if "Circuit breaker is OPEN" in str(e):
                self.logger.warning("API circuit breaker is open, skipping")
                return []
            raise
```

## Common Patterns

### Retry with Backoff

Using `backoff` library for automatic retries:

```python
import backoff
import httpx

@backoff.on_exception(
    backoff.expo,
    httpx.HTTPError,
    max_tries=3,
    max_time=30
)
async def fetch_with_retry(url: str):
    """Fetch with exponential backoff retry"""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
```

### Rate Limiting

Simple rate limiter using asyncio:

```python
import asyncio
import time

class RateLimiter:
    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self.semaphore = asyncio.Semaphore(calls)
        self.call_times = []

    async def __aenter__(self):
        async with self.semaphore:
            now = time.time()
            # Remove old calls outside window
            self.call_times = [t for t in self.call_times if now - t < self.period]

            if len(self.call_times) >= self.calls:
                sleep_time = self.period - (now - self.call_times[0])
                await asyncio.sleep(sleep_time)

            self.call_times.append(time.time())

    async def __aexit__(self, *args):
        pass

# Usage
rate_limiter = RateLimiter(calls=10, period=1.0)  # 10 calls per second

async def make_limited_request():
    async with rate_limiter:
        return await fetch_data()
```

### Timeout Handling

Proper timeout management:

```python
import asyncio
from typing import TypeVar, Coroutine, Optional

T = TypeVar('T')

async def with_timeout(
    coro: Coroutine[None, None, T],
    timeout: float,
    default: Optional[T] = None
) -> Optional[T]:
    """Execute coroutine with timeout"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Operation timed out after {timeout}s")
        return default

# Usage
result = await with_timeout(
    fetch_data(),
    timeout=5.0,
    default=[]
)
```

### Connection Pooling

Reusable HTTP client with connection pooling:

```python
import httpx
from typing import Optional

class HTTPClient:
    _instance: Optional['HTTPClient'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'client'):
            self.client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=100,
                    keepalive_expiry=30
                ),
                timeout=httpx.Timeout(30.0),
                http2=True
            )

    async def get(self, url: str, **kwargs):
        return await self.client.get(url, **kwargs)

    async def close(self):
        await self.client.aclose()

# Usage
client = HTTPClient()
response = await client.get("https://api.example.com/data")
```

### Batch Processing

Process items in batches:

```python
from typing import List, TypeVar, Callable, AsyncIterator

T = TypeVar('T')

async def process_in_batches(
    items: List[T],
    batch_size: int,
    processor: Callable[[List[T]], AsyncIterator[Any]]
) -> AsyncIterator[Any]:
    """Process items in batches"""
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        async for result in processor(batch):
            yield result

# Usage
async def process_batch(batch: List[Dict]) -> AsyncIterator[Dict]:
    # Process batch and yield results
    for item in batch:
        yield transform(item)

async for result in process_in_batches(all_items, 100, process_batch):
    await save(result)
```

## Adding New Utilities

### Utility Template

```python
# backend/utils/your_utility.py
"""
Module description explaining purpose and usage.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

class YourUtility:
    """
    Utility class description.

    Example:
        >>> util = YourUtility()
        >>> result = util.process(data)
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._setup()

    def _setup(self):
        """Initialize utility resources"""
        pass

    def process(self, data: Any) -> Any:
        """
        Process data with utility logic.

        Args:
            data: Input data to process

        Returns:
            Processed result

        Raises:
            ValueError: If data is invalid
        """
        if not self._validate(data):
            raise ValueError("Invalid data")

        return self._transform(data)

    def _validate(self, data: Any) -> bool:
        """Validate input data"""
        return data is not None

    def _transform(self, data: Any) -> Any:
        """Transform data"""
        return data

# Convenience function
def your_utility_function(data: Any, **kwargs) -> Any:
    """Convenience function for common use case"""
    util = YourUtility(kwargs)
    return util.process(data)
```

### Testing Utilities

```python
# backend/tests/utils/test_your_utility.py
import pytest
from backend.utils.your_utility import YourUtility, your_utility_function

class TestYourUtility:
    def test_initialization(self):
        util = YourUtility({'key': 'value'})
        assert util.config['key'] == 'value'

    def test_process_valid_data(self):
        util = YourUtility()
        result = util.process("test")
        assert result == "test"

    def test_process_invalid_data(self):
        util = YourUtility()
        with pytest.raises(ValueError):
            util.process(None)

    def test_convenience_function(self):
        result = your_utility_function("test", key="value")
        assert result == "test"
```

## Best Practices

### 1. Error Handling
Always provide meaningful error messages:

```python
def validate_input(data: Dict[str, Any]) -> None:
    """Validate input data with clear error messages"""
    if not isinstance(data, dict):
        raise TypeError(f"Expected dict, got {type(data).__name__}")

    required_fields = ['id', 'value', 'timestamp']
    missing = [f for f in required_fields if f not in data]

    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")
```

### 2. Type Hints
Use type hints for clarity:

```python
from typing import Union, List, Dict, Optional, TypeVar, Generic

T = TypeVar('T')

class Cache(Generic[T]):
    def __init__(self, max_size: int = 100):
        self._cache: Dict[str, T] = {}
        self._max_size = max_size

    def get(self, key: str) -> Optional[T]:
        return self._cache.get(key)

    def set(self, key: str, value: T) -> None:
        if len(self._cache) >= self._max_size:
            # Remove oldest
            oldest = next(iter(self._cache))
            del self._cache[oldest]
        self._cache[key] = value
```

### 3. Logging
Add appropriate logging:

```python
import logging

logger = logging.getLogger(__name__)

def complex_operation(data: Any) -> Any:
    logger.debug(f"Starting operation with {len(data)} items")

    try:
        result = process(data)
        logger.info(f"Operation completed successfully")
        return result
    except Exception as e:
        logger.error(f"Operation failed: {e}", exc_info=True)
        raise
```

### 4. Documentation
Document utilities thoroughly:

```python
def calculate_percentile(values: List[float], percentile: float) -> float:
    """
    Calculate the specified percentile of a list of values.

    Args:
        values: List of numeric values
        percentile: Percentile to calculate (0-100)

    Returns:
        The calculated percentile value

    Raises:
        ValueError: If percentile is not between 0 and 100
        ValueError: If values list is empty

    Example:
        >>> values = [1, 2, 3, 4, 5]
        >>> calculate_percentile(values, 50)
        3.0
    """
    if not 0 <= percentile <= 100:
        raise ValueError("Percentile must be between 0 and 100")

    if not values:
        raise ValueError("Cannot calculate percentile of empty list")

    return np.percentile(values, percentile)
```

## Performance Considerations

### Caching
Use caching for expensive operations:

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=128)
def expensive_calculation(data: str) -> float:
    """Cached expensive calculation"""
    # Expensive operation
    return sum(ord(c) for c in data) / len(data)

# For unhashable types
def cache_key(*args, **kwargs) -> str:
    """Generate cache key for complex arguments"""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()
```

### Resource Management
Always clean up resources:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def managed_resource():
    """Context manager for resource cleanup"""
    resource = await acquire_resource()
    try:
        yield resource
    finally:
        await release_resource(resource)

# Usage
async with managed_resource() as resource:
    await use_resource(resource)
```

## Future Utilities

Planned utilities for future implementation:

- [ ] **Distributed Locking** - For multi-instance coordination
- [ ] **Event Bus** - For decoupled communication
- [ ] **Feature Flags** - For gradual rollouts
- [ ] **Metrics Aggregator** - For custom metrics
- [ ] **Data Sanitizer** - For PII removal
- [ ] **Async Queue** - For task processing
- [ ] **Health Checker** - For dependency monitoring
