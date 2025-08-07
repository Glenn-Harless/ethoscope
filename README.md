# Ethoscope - Ethereum Network Health Monitor

> ⚠️ **IMPORTANT SECURITY NOTICE**: This repository contains sample credentials and API keys intended for local development only. **NEVER** use these default credentials in production environments. Always use secure, unique credentials and proper secret management practices.

Ethoscope is a comprehensive monitoring and analytics platform for the Ethereum blockchain, providing real-time insights into network health, gas prices, MEV activity, and L2 migration patterns.

## Features

- **Real-time Network Monitoring**: Track gas prices, block times, and mempool congestion
- **MEV Impact Analysis**: Monitor MEV-Boost adoption and its effects on the network
- **L2 Migration Tracking**: Analyze the movement of activity to Layer 2 solutions
- **Time-Series Analytics**: Powered by TimescaleDB for efficient historical data analysis
- **Caching Layer**: Redis-based caching for improved performance

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- PostgreSQL with TimescaleDB extension
- Alchemy API key (free tier is sufficient)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ethoscope.git
cd ethoscope
```

### 2. Install Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Install Dependencies

```bash
poetry install
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your Alchemy API key
```

### 5. Start Services

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Wait for services to be healthy
docker-compose ps

# Run database migrations
poetry run alembic upgrade head

# Set up TimescaleDB extensions
docker-compose exec postgres psql -U ethoscope -d ethoscope -f /docker-entrypoint-initdb.d/10-setup-timescale.sql
```

### 6. Run the ETL Pipeline

```bash
# Test the connection first
poetry run python scripts/test_integration.py

# Run the ETL pipeline
poetry run python scripts/run_etl.py
```

## Development

### Running with Docker (Development Mode)

```bash
# Start all services including development container
docker-compose --profile dev up

# Or use the Makefile
make dev
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=backend

# Run specific test file
poetry run pytest tests/backend/test_collectors.py
```

### Code Quality

```bash
# Run pre-commit hooks
poetry run pre-commit run --all-files

# Or use the Makefile
make lint
```

### Useful Make Commands

```bash
make help          # Show all available commands
make dev           # Start development environment
make test          # Run tests
make lint          # Run linters
make migrate       # Run database migrations
make logs          # View logs
make clean         # Clean up containers and volumes
```

## Project Structure

```
ethoscope/
├── backend/
│   ├── api/           # FastAPI endpoints
│   ├── etl/           # ETL pipeline components
│   │   ├── collectors/    # Data collection from APIs
│   │   ├── processors/    # Data transformation
│   │   └── loaders/       # Data persistence
│   ├── models/        # Database models
│   ├── services/      # Business logic
│   └── utils/         # Utility functions
├── frontend/          # Frontend application (Phase 3)
├── docker/            # Docker configurations
├── scripts/           # Utility scripts
│   ├── analysis/      # Data analysis scripts
│   └── maintenance/   # Database maintenance
├── tests/             # Test suite
└── docs/              # Documentation
```

## Architecture

- **Data Collection**: Web3.py + Alchemy for blockchain data
- **Storage**: TimescaleDB (PostgreSQL) for time-series data
- **Caching**: Redis for deduplication and performance
- **Processing**: Python-based ETL pipeline
- **API**: FastAPI for REST endpoints
- **Frontend**: React-based dashboard (Phase 3)

## Configuration

### Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `ALCHEMY_API_KEY`: Your Alchemy API key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `COLLECTION_INTERVAL`: How often to collect data (seconds)

### TimescaleDB

The project uses TimescaleDB for efficient time-series data storage:
- Automatic partitioning with hypertables
- Continuous aggregates for real-time analytics
- Data retention policies
- Compression for historical data

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Alchemy for blockchain data access
- TimescaleDB for time-series database
- The Ethereum community for inspiration
