# API Middleware

## Overview

Middleware components that process every request/response in the FastAPI application. These components handle cross-cutting concerns like authentication, rate limiting, caching, and monitoring.

## Middleware Components

### `auth.py` - Authentication & Authorization

API key-based authentication with tier support.

**Features:**
- Bearer token authentication
- Multiple permission tiers (default, premium, admin)
- JWT token generation for WebSocket auth
- Permission-based access control

**Usage:**
```python
from backend.api.middleware.auth import APIKeyAuth

auth = APIKeyAuth()

# In your route
@router.get("/protected")
async def protected_route(user_info = Depends(auth.verify_api_key)):
    return {"user": user_info["name"]}
```

**API Key Structure:**
```python
{
    'tier': 'premium',           # User tier
    'name': 'User Name',         # Display name
    'permissions': ['read', 'write', 'stream'],  # Permissions
    'created': datetime.utcnow() # Creation date
}
```

### `rate_limit.py` - Request Rate Limiting

Token bucket rate limiter with Redis backend.

**Features:**
- Different limits per tier
- Redis-backed for distributed systems
- Graceful degradation if Redis is down
- Rate limit headers in responses

**Rate Limits:**
- Default: 100 requests/hour
- Metrics endpoints: 1,000 requests/hour
- WebSocket: 10 connections/minute
- Premium: 10,000 requests/hour

**Usage:**
```python
from backend.api.middleware.rate_limit import RateLimiter

rate_limiter = RateLimiter(redis_url)

# Check rate limit
rate_info = await rate_limiter.check_rate_limit(
    request,
    tier='premium',
    identifier='user123'
)
```

**Response Headers:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1704067200
```

### `cache.py` - Response Caching

Redis-based caching for expensive operations.

**Features:**
- Automatic cache key generation
- Configurable TTL
- Cache or compute pattern
- MD5-based key hashing

**Usage:**
```python
from backend.api.middleware.cache import MetricsCache

cache = MetricsCache(redis_client)

# Cache or compute
result = await cache.get_or_compute(
    key="gas_metrics_latest",
    compute_func=expensive_calculation,
    ttl=60  # Cache for 60 seconds
)

# Generate cache key
cache_key = cache.cache_key("metrics", timeframe="1h", network="mainnet")
```

### `monitoring.py` - Prometheus Metrics

Application monitoring and metrics collection.

**Metrics Collected:**
- `http_requests_total` - Request count by method, endpoint, status
- `http_request_duration_seconds` - Request latency
- `http_requests_in_progress` - Currently processing requests
- `network_health_score` - Current network health (0-100)
- `active_websocket_connections` - WebSocket connection count
- `mev_revenue_total_eth` - Cumulative MEV revenue

**Usage:**
```python
from backend.api.middleware.monitoring import MetricsMiddleware

# Add to FastAPI app
app.add_middleware(MetricsMiddleware)

# Access metrics endpoint
GET /metrics  # Returns Prometheus format
```

**Custom Metrics:**
```python
from backend.api.middleware.monitoring import health_score_gauge

# Update metric
health_score_gauge.set(85.5)
```

## Middleware Stack Order

The order matters! In `main.py`:

```python
# 1. Monitoring (outermost - tracks everything)
app.add_middleware(MetricsMiddleware)

# 2. GZIP compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 3. CORS
app.add_middleware(CORSMiddleware, ...)

# 4. Custom middleware for rate limit headers
@app.middleware("http")
async def add_rate_limit_headers(request, call_next):
    # Adds rate limit info to response headers
```

## Integration with Routes

### Using Dependencies

```python
from backend.api.dependencies import verify_request

# verify_request combines auth + rate limiting
@router.get("/data")
async def get_data(user_info = Depends(verify_request)):
    # User is authenticated and rate limited
    return {"data": "..."}
```

### Manual Usage

```python
# Direct auth check
user = await auth.verify_api_key(credentials)

# Direct rate limit check
await rate_limiter.check_rate_limit(request, tier=user['tier'])

# Direct cache usage
cached = await cache.get_or_compute(key, fetch_func)
```

## Configuration

### Environment Variables

```env
# Redis for rate limiting and caching
REDIS_URL=redis://localhost:6379

# JWT signing key
API_SECRET_KEY=your-secret-key-here

# Cache TTL (seconds)
DEFAULT_CACHE_TTL=30
```

### Customizing Limits

Edit `rate_limit.py`:
```python
self.limits = {
    'default': {'requests': 100, 'window': 3600},
    'metrics': {'requests': 1000, 'window': 3600},
    'premium': {'requests': 10000, 'window': 3600},
    'custom_tier': {'requests': 5000, 'window': 3600}  # Add new tier
}
```

## Error Handling

### Authentication Errors
```json
{
    "detail": "Invalid API key",
    "status_code": 401
}
```

### Rate Limit Errors
```json
{
    "detail": {
        "error": "Rate limit exceeded",
        "retry_after": 1234,
        "limit": 100,
        "window": 3600
    },
    "status_code": 429
}
```

## Performance Considerations

### Caching Strategy
- Cache keys include all relevant parameters
- Short TTL for real-time data (30s)
- Longer TTL for historical data (5m)
- Cache invalidation on updates

### Rate Limiting
- Uses Redis INCR for atomic operations
- Automatic expiry for windows
- Fallback to allow requests if Redis fails

### Monitoring Overhead
- Minimal overhead (~1-2ms per request)
- Async metric updates
- Batch metric exports

## Security

### API Key Storage
Currently hardcoded for demo. In production:
1. Store in database with hashed keys
2. Implement key rotation
3. Add key expiration
4. Log key usage

### JWT Tokens
- Used for WebSocket authentication
- Short expiration (24 hours)
- Include user permissions
- Signed with secret key

## Testing Middleware

### Unit Tests
```python
# Test auth
async def test_auth_valid_key():
    auth = APIKeyAuth()
    # Mock request with valid key
    result = await auth.verify_api_key(mock_credentials)
    assert result['tier'] == 'default'

# Test rate limiting
async def test_rate_limit_exceeded():
    limiter = RateLimiter("redis://localhost")
    # Exceed limit
    with pytest.raises(HTTPException) as exc:
        for _ in range(101):
            await limiter.check_rate_limit(request)
    assert exc.value.status_code == 429
```

### Integration Tests
```python
# Test full middleware stack
async def test_middleware_integration():
    response = await client.get(
        "/api/v1/metrics/gas",
        headers={"Authorization": "Bearer test-key"}
    )
    assert "X-RateLimit-Remaining" in response.headers
    assert response.status_code == 200
```

## Common Issues

### Redis Connection Failed
- Check Redis is running
- Verify REDIS_URL
- Rate limiter falls back gracefully
- Cache returns None

### API Key Not Working
- Check Authorization header format: `Bearer <key>`
- Verify key exists in auth.py
- Check key permissions

### High Latency
- Review cache hit rates
- Check Redis performance
- Monitor middleware execution time

## Future Improvements

- [ ] Database-backed API key storage
- [ ] Dynamic rate limit adjustment
- [ ] Distributed caching with Redis Cluster
- [ ] Request/response logging middleware
- [ ] API key analytics and usage tracking
- [ ] OAuth2/JWT full implementation
