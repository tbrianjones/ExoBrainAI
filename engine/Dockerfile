FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (includes WeasyPrint's Cairo/Pango libs for PDF rendering)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
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
