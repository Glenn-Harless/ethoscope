# Backend Architecture

## Overview

The Ethoscope backend is a sophisticated Ethereum network health monitoring system built with Python, FastAPI, and PostgreSQL/TimescaleDB. It collects, processes, and analyzes blockchain metrics in real-time to provide comprehensive network health insights.

## Directory Structure

```
backend/
├── api/              # FastAPI application and API endpoints
├── etl/              # Extract, Transform, Load pipeline
├── models/           # SQLAlchemy database models
├── utils/            # Utility functions and helpers
├── middleware/       # (Legacy - being migrated to api/middleware)
├── ml/               # Machine learning components (future)
└── services/         # Business logic services (future)
```

## Key Components

### 1. API Layer (`/api`)
- **FastAPI Application**: Modern async web framework
- **WebSocket Support**: Real-time data streaming
- **Authentication**: API key-based with tier support
- **Rate Limiting**: Redis-backed request throttling
- **Monitoring**: Prometheus metrics integration

### 2. ETL Pipeline (`/etl`)
- **Collectors**: Gather data from various sources
  - Alchemy API for gas/block metrics
  - MEV-Boost relays for MEV data
  - Multiple L2 networks (Arbitrum, Optimism, Base, etc.)
- **Processors**: Transform and validate raw data
- **Loaders**: Persist data to PostgreSQL/TimescaleDB

### 3. Data Models (`/models`)
- **Time-series Metrics**: Block, gas, and mempool data
- **MEV Analytics**: MEV extraction and builder statistics
- **L2 Comparisons**: Cross-chain metrics
- **Network Health Scores**: Calculated health indicators

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL with TimescaleDB extension
- Redis
- Poetry for dependency management

### Environment Variables
Create a `.env` file with:
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/ethoscope

# Redis
REDIS_URL=redis://localhost:6379

# API Keys
ALCHEMY_API_KEY=your_alchemy_key
API_SECRET_KEY=your_secret_key

# Optional
LOG_LEVEL=INFO
```

### Installation
```bash
# Install dependencies
poetry install

# Run database migrations
poetry run alembic upgrade head

# Start the API server
poetry run uvicorn backend.api.main:app --reload

# Or use the run script
poetry run python scripts/run_api.py
```

## Architecture Patterns

### 1. Collector Pattern
All data collectors inherit from `BaseCollector` and implement:
- Async data collection
- Error handling with retries
- Rate limiting
- Result validation

### 2. Circuit Breaker
Prevents cascading failures when external services are down:
- Automatic failure detection
- Service recovery monitoring
- Fallback mechanisms

### 3. Repository Pattern
Database operations are abstracted through:
- Model-specific repositories
- Transaction management
- Query optimization

## Data Flow

```
External APIs → Collectors → Processors → Database → API → Clients
                    ↓            ↓           ↓
                  Redis      Validation   WebSocket
                 (cache)                  (real-time)
```

## Key Features

### Real-time Updates
- WebSocket connections for live data
- Redis pub/sub for multi-instance support
- Configurable update intervals

### Multi-chain Support
- Ethereum mainnet
- Layer 2 networks (Arbitrum, Optimism, Base, zkSync, Scroll)
- Cross-chain comparisons

### MEV Analytics
- MEV-Boost relay integration
- Builder dominance tracking
- Block-level MEV characteristics

### Health Scoring
- Dynamic baseline calculations
- Anomaly detection (Z-score, IQR)
- Multi-factor scoring:
  - Gas efficiency
  - Network stability
  - MEV fairness
  - Block production
  - Mempool health

## Development

### Adding a New Collector
1. Create a new file in `etl/collectors/`
2. Inherit from `BaseCollector`
3. Implement the `collect()` method
4. Register in the ETL pipeline

### Adding a New API Endpoint
1. Create a router in `api/routers/`
2. Define schemas in `api/schemas.py`
3. Include router in `api/main.py`
4. Add tests

### Database Migrations
```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

## Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=backend

# Test specific component
poetry run pytest backend/tests/test_collectors.py
```

## Production Considerations

### Performance
- Connection pooling for databases
- Async I/O throughout
- Caching with Redis
- Query optimization with indexes

### Monitoring
- Prometheus metrics at `/metrics`
- Health checks at `/api/v1/health`
- Structured logging with context

### Security
- API key authentication
- Rate limiting by tier
- Input validation
- SQL injection prevention

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check PostgreSQL is running
   - Verify TimescaleDB extension
   - Check connection string

2. **Redis Connection Failed**
   - Ensure Redis is running
   - Check Redis URL configuration

3. **API Key Errors**
   - Verify Alchemy API key is set
   - Check rate limits haven't been exceeded

## Contributing

1. Follow the existing patterns
2. Add tests for new features
3. Update relevant documentation
4. Run pre-commit hooks before committing

## License

This project is part of the Ethoscope network monitoring system.
