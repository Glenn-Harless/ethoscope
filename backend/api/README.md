# API Layer

## Overview

The API layer provides RESTful endpoints and WebSocket connections for accessing Ethereum network health data. Built with FastAPI, it offers high-performance async operations, automatic API documentation, and real-time data streaming.

## Directory Structure

```
api/
├── middleware/       # Request/response middleware components
├── routers/         # API endpoint definitions
├── dependencies.py  # Shared dependencies and auth
├── main.py         # FastAPI application setup
├── schemas.py      # Pydantic models for validation
├── websocket.py    # WebSocket manager for real-time updates
└── monitoring.py   # (Legacy - duplicate of middleware/monitoring.py)
```

## Core Files

### `main.py` - Application Entry Point
The main FastAPI application with:
- Lifespan management for startup/shutdown
- Middleware configuration (CORS, compression, monitoring)
- Router registration
- WebSocket endpoint setup

Key features:
- Global instances for ETL pipeline and WebSocket manager
- Background tasks for health metric updates
- Structured error handling

### `websocket.py` - Real-time Communication
WebSocket manager handling:
- Client connection management
- Channel-based subscriptions
- Redis pub/sub for multi-instance support
- Automatic reconnection handling

Available channels:
- `gas_prices` - Real-time gas price updates
- `block_metrics` - New block information
- `network_health` - Health score changes
- `mev_activity` - MEV extraction events
- `l2_comparison` - L2 network metrics
- `mempool_stats` - Mempool statistics

### `schemas.py` - Data Validation
Pydantic models for:
- Request validation
- Response serialization
- Type safety
- Automatic OpenAPI documentation

### `dependencies.py` - Shared Dependencies
Common dependencies for:
- Authentication verification
- Rate limit checking
- Database session management

## API Endpoints

### Public Endpoints
- `GET /` - Root endpoint with API info
- `GET /api/v1/status` - API operational status

### Authenticated Endpoints

All authenticated endpoints require an API key in the Authorization header:
```
Authorization: Bearer your-api-key
```

#### Metrics Router (`/api/v1/metrics`)
- `GET /gas` - Gas price metrics
- `GET /blocks` - Block metrics
- `GET /mempool` - Mempool statistics
- `GET /summary` - Combined metrics summary

#### Health Router (`/api/v1/health`)
- `GET /score` - Current network health score
- `GET /history` - Historical health scores
- `GET /components` - Individual component scores

#### MEV Router (`/api/v1/mev`)
- `GET /recent` - Recent MEV activity
- `GET /stats` - Aggregate MEV statistics
- `GET /builders` - Builder dominance metrics
- `GET /analysis` - MEV block analysis

#### L2 Comparison Router (`/api/v1/l2`)
- `GET /comparison` - Cross-chain metrics
- `GET /gas-savings` - L1 vs L2 gas comparison
- `GET /network/{network}` - Specific L2 metrics

#### Admin Router (`/api/v1/admin`)
- `GET /stats` - Admin statistics (requires admin permission)
- `POST /clear-cache` - Clear all caches

## WebSocket Usage

### Client Connection Example

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Subscribe to channels
ws.send(JSON.stringify({
    action: 'subscribe',
    channels: ['gas_prices', 'network_health']
}));

// Handle incoming data
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`Update from ${data.channel}:`, data.data);
};
```

### Message Types

#### Client → Server
```json
{
    "action": "subscribe",
    "channels": ["gas_prices", "mev_activity"]
}

{
    "action": "unsubscribe",
    "channels": ["gas_prices"]
}

{
    "action": "ping"
}
```

#### Server → Client
```json
{
    "type": "connection",
    "status": "connected",
    "timestamp": "2024-01-01T00:00:00"
}

{
    "type": "update",
    "channel": "gas_prices",
    "data": {...},
    "timestamp": "2024-01-01T00:00:00"
}

{
    "type": "error",
    "message": "Invalid subscription channel"
}
```

## Authentication

### API Key Tiers

1. **Default Tier**
   - 100 requests/hour
   - Read-only access
   - Basic channels

2. **Premium Tier**
   - 10,000 requests/hour
   - All permissions
   - All channels
   - Priority support

3. **Admin Tier**
   - Unlimited requests
   - Admin endpoints
   - System management

### Adding API Keys

Currently hardcoded in `middleware/auth.py`. In production, store in database:

```python
# Example API key structure
{
    'api_key': 'demo-key-123',
    'tier': 'default',
    'name': 'Demo User',
    'permissions': ['read'],
    'created': datetime.utcnow()
}
```

## Rate Limiting

Rate limits by endpoint tier:
- Default: 100 req/hour
- Metrics endpoints: 1000 req/hour
- WebSocket connections: 10/minute
- Premium: 10,000 req/hour

Rate limit headers in responses:
- `X-RateLimit-Limit` - Request limit
- `X-RateLimit-Remaining` - Remaining requests
- `X-RateLimit-Reset` - Reset timestamp

## Monitoring

### Prometheus Metrics

Available at `/metrics` endpoint:

- `http_requests_total` - Total requests by method, endpoint, status
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Current active requests
- `network_health_score` - Current health score gauge
- `active_websocket_connections` - Active WebSocket count
- `mev_revenue_total_eth` - Cumulative MEV revenue

### Health Checks

- `/api/v1/health/score` - Application health
- Database connectivity check
- Redis connectivity check
- External API availability

## Error Handling

### Standard Error Response
```json
{
    "detail": "Error message",
    "status_code": 400,
    "timestamp": "2024-01-01T00:00:00"
}
```

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error

## Configuration

### Environment Variables
- `REDIS_URL` - Redis connection string
- `API_SECRET_KEY` - JWT signing key
- `LOG_LEVEL` - Logging verbosity

### CORS Settings
Configure in `main.py`:
```python
allow_origins=["http://localhost:3000"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"]
```

## Development

### Running Locally
```bash
# Start with auto-reload
poetry run uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

# With custom settings
poetry run uvicorn backend.api.main:app --env-file .env.local
```

### API Documentation

FastAPI auto-generates documentation:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### Adding New Endpoints

1. Create router in `routers/`
2. Define schemas in `schemas.py`
3. Include in `main.py`:
```python
app.include_router(
    your_router.router,
    prefix="/api/v1/your-endpoint",
    tags=["your-tag"],
    dependencies=[Depends(verify_request)]
)
```

## Performance Optimization

### Caching Strategy
- Redis caching for expensive queries
- 30-second default TTL
- Cache key generation with request parameters

### Connection Pooling
- Database connection pooling via SQLAlchemy
- Redis connection reuse
- HTTP client connection limits

### Async Operations
- All database queries are async
- Non-blocking I/O for external APIs
- Concurrent request handling

## Security

### Best Practices
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy
- Rate limiting to prevent abuse
- API key rotation support
- HTTPS enforcement in production

### Headers
Security headers set by middleware:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`

## Troubleshooting

### Common Issues

1. **WebSocket Connection Drops**
   - Check Redis connectivity
   - Verify WebSocket URL
   - Check for proxy/firewall issues

2. **Rate Limit Exceeded**
   - Check API key tier
   - Implement client-side throttling
   - Use WebSocket for real-time data

3. **CORS Errors**
   - Verify allowed origins
   - Check request headers
   - Ensure credentials are included
