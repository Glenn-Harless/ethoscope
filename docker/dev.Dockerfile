FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install poetry in the container
RUN pip install poetry

# Copy only dependency files first (better caching)
COPY pyproject.toml poetry.lock ./

# Install dependencies including dev dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --with dev

# Copy source code
COPY . .

# Development command with reload
CMD ["poetry", "run", "uvicorn", "backend.api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
