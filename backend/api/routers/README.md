# API Routers

## Overview

FastAPI routers that define the REST API endpoints. Each router handles a specific domain of functionality, with clear separation of concerns and consistent patterns.

## Router Files

### `metrics.py` - Core Blockchain Metrics

Endpoints for gas prices, blocks, and mempool data.

**Endpoints:**
- `GET /api/v1/metrics/gas` - Gas price history
- `GET /api/v1/metrics/blocks` - Block information
- `GET /api/v1/metrics/mempool` - Mempool statistics
- `GET /api/v1/metrics/summary` - Combined metrics overview

**Query Parameters:**
- `timeframe`: Time window (5m, 1h, 24h, 7d)
- `limit`: Number of records (default: 100)
- `offset`: Pagination offset

**Example Response:**
```json
{
    "data": [
        {
            "timestamp": "2024-01-01T00:00:00Z",
            "gas_price_gwei": 25.5,
            "gas_price_p25": 20.0,
            "gas_price_p50": 25.0,
            "gas_price_p75": 30.0,
            "gas_price_p95": 45.0,
            "pending_transactions": 150
        }
    ],
    "meta": {
        "count": 100,
        "timeframe": "1h"
    }
}
```

### `health.py` - Network Health Monitoring

Network health scores and component analysis.

**Endpoints:**
- `GET /api/v1/health/score` - Current health score
- `GET /api/v1/health/history` - Historical health data
- `GET /api/v1/health/components` - Individual component scores

**Response Structure:**
```json
{
    "overall_score": 85.5,
    "components": {
        "gas_efficiency": 90.0,
        "network_stability": 85.0,
        "mev_fairness": 75.0,
        "block_production": 88.0,
        "mempool_health": 82.0,
        "validator_performance": 93.0
    },
    "timestamp": "2024-01-01T00:00:00Z",
    "status": "healthy"  // healthy, degraded, critical
}
```

**Health Status Thresholds:**
- `healthy`: score >= 80
- `degraded`: 60 <= score < 80
- `critical`: score < 60

### `mev.py` - MEV Analytics

Maximum Extractable Value tracking and analysis.

**Endpoints:**
- `GET /api/v1/mev/recent` - Recent MEV activity
- `GET /api/v1/mev/stats` - Aggregate statistics
- `GET /api/v1/mev/builders` - Builder dominance metrics
- `GET /api/v1/mev/analysis` - Block-level MEV analysis

**Query Parameters:**
- `builder`: Filter by builder pubkey
- `min_value`: Minimum MEV value in ETH
- `relay`: Filter by relay source

**MEV Analysis Response:**
```json
{
    "blocks": [
        {
            "block_number": 18000000,
            "mev_revenue_eth": 2.5,
            "mev_intensity": "high",
            "likely_mev_type": "likely_contains_liquidations",
            "builder": "0x1234...",
            "gas_efficiency": 0.95,
            "relay_source": "flashbots"
        }
    ],
    "statistics": {
        "total_mev_24h": 1250.5,
        "average_block_value": 0.15,
        "top_builders": [...]
    }
}
```

### `l2_comparison.py` - Layer 2 Networks

Cross-chain metrics and comparisons.

**Endpoints:**
- `GET /api/v1/l2/comparison` - Multi-chain comparison
- `GET /api/v1/l2/gas-savings` - L1 vs L2 gas analysis
- `GET /api/v1/l2/network/{network}` - Specific L2 metrics

**Supported Networks:**
- `arbitrum` - Arbitrum One
- `optimism` - Optimism
- `polygon` - Polygon PoS
- `base` - Base
- `zksync` - zkSync Era
- `scroll` - Scroll

**Comparison Response:**
```json
{
    "networks": {
        "ethereum": {
            "gas_price_gwei": 30.0,
            "avg_block_time": 12.1,
            "tps": 15.5
        },
        "arbitrum": {
            "gas_price_gwei": 0.1,
            "avg_block_time": 0.25,
            "tps": 40.2,
            "gas_savings_percent": 99.7
        }
    },
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### `admin.py` - Administrative Functions

Admin-only endpoints for system management.

**Endpoints:**
- `GET /api/v1/admin/stats` - System statistics
- `POST /api/v1/admin/clear-cache` - Clear all caches

**Required Permission:** `admin` in user permissions

**Stats Response:**
```json
{
    "total_users": 1250,
    "total_requests": 1500000,
    "active_connections": 45,
    "cache_hit_rate": 0.85,
    "uptime_hours": 720
}
```

## Common Patterns

### Error Responses

All routers use consistent error formatting:

```json
{
    "detail": "Error message",
    "status_code": 400,
    "error_code": "INVALID_TIMEFRAME",
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### Pagination

Standard pagination for list endpoints:

```python
@router.get("/items")
async def get_items(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    # Implementation
```

### Time-based Queries

Common timeframe handling:

```python
def parse_timeframe(timeframe: str) -> timedelta:
    """Convert timeframe string to timedelta"""
    timeframes = {
        "5m": timedelta(minutes=5),
        "1h": timedelta(hours=1),
        "24h": timedelta(days=1),
        "7d": timedelta(days=7)
    }
    return timeframes.get(timeframe, timedelta(hours=1))
```

### Caching

Using cache middleware:

```python
@router.get("/expensive-query")
async def expensive_endpoint(db: Session = Depends(get_db)):
    cache_key = cache.cache_key("expensive", param=value)

    async def compute():
        # Expensive database query
        return result

    return await cache.get_or_compute(cache_key, compute, ttl=300)
```

## Authentication & Authorization

All routers (except admin) use the same auth pattern:

```python
# In main.py
app.include_router(
    metrics.router,
    prefix="/api/v1/metrics",
    tags=["metrics"],
    dependencies=[Depends(verify_request)]  # Auth + rate limit
)
```

The `verify_request` dependency:
1. Validates API key
2. Checks rate limits
3. Returns user info
4. Sets rate limit headers

## Adding New Endpoints

### 1. Create the Endpoint

```python
@router.get("/new-endpoint", response_model=NewDataResponse)
async def get_new_data(
    timeframe: str = Query("1h", regex="^(5m|1h|24h|7d)$"),
    db: Session = Depends(get_db),
    user_info: dict = Depends(verify_request)
):
    """
    Get new data with timeframe filtering.

    - **timeframe**: Time window for data
    """
    # Validate input
    tf = parse_timeframe(timeframe)

    # Query database
    data = db.query(NewModel)\
        .filter(NewModel.timestamp >= datetime.utcnow() - tf)\
        .all()

    # Return formatted response
    return {
        "data": data,
        "meta": {
            "count": len(data),
            "timeframe": timeframe
        }
    }
```

### 2. Define Response Schema

In `schemas.py`:

```python
class NewDataResponse(BaseModel):
    data: List[NewDataItem]
    meta: MetaInfo

class NewDataItem(BaseModel):
    id: UUID
    value: float
    timestamp: datetime

    class Config:
        from_attributes = True
```

### 3. Add Router to Main

In `main.py`:

```python
from backend.api.routers import new_router

app.include_router(
    new_router.router,
    prefix="/api/v1/new",
    tags=["new"],
    dependencies=[Depends(verify_request)]
)
```

## Testing Routers

### Unit Tests

```python
from fastapi.testclient import TestClient

def test_get_metrics(client: TestClient, mock_db):
    response = client.get(
        "/api/v1/metrics/gas",
        headers={"Authorization": "Bearer test-key"}
    )
    assert response.status_code == 200
    assert "data" in response.json()
```

### Integration Tests

```python
@pytest.mark.integration
async def test_mev_analysis_flow(client: TestClient):
    # Get recent MEV blocks
    response = await client.get("/api/v1/mev/recent")
    blocks = response.json()["blocks"]

    # Analyze specific block
    block_number = blocks[0]["block_number"]
    analysis = await client.get(f"/api/v1/mev/analysis?block={block_number}")

    assert analysis.json()["mev_intensity"] in ["high", "medium", "low"]
```

## Performance Tips

### Database Queries
- Use indexes for timestamp queries
- Limit default query sizes
- Use query optimization with `.options()`

### Response Size
- Paginate large datasets
- Use field filtering when possible
- Compress responses with gzip

### Caching
- Cache expensive aggregations
- Use appropriate TTLs
- Invalidate on updates

## API Documentation

FastAPI auto-generates documentation:

- **Swagger UI**: `/api/docs`
- **ReDoc**: `/api/redoc`

Each endpoint includes:
- Parameter descriptions
- Response schemas
- Example values
- Authentication requirements

## Common Issues

### Slow Queries
- Add database indexes
- Use query explains
- Implement caching

### Large Responses
- Add pagination
- Filter unnecessary fields
- Use streaming responses

### Rate Limiting
- Check tier limits
- Implement client-side retry
- Use WebSocket for real-time data
