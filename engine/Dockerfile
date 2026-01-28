FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for layer caching
COPY pyproject.toml .
COPY README.md .

# Install dependencies only (from pyproject.toml)
# Note: graphrag excluded due to azure-identity version conflict; reconnect later
RUN pip install --no-cache-dir ".[api,watcher,dev]"

# Copy application code
COPY . .

# Re-install to pick up source code
RUN pip install --no-cache-dir ".[api,watcher,dev]"

# Default command (CLI; override in docker-compose)
CMD ["python", "-m", "src.cli.main"]
