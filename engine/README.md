# ExoBrain Engine

Local-first GraphRAG memory engine.

## Quick Start

```bash
# From repository root
cp .env.example .env
# Edit .env to set EXOBRAIN_DATA_DIR

docker compose up -d
docker compose exec exobrain exobrain init
docker compose exec exobrain exobrain status
```

## CLI Commands

```bash
exobrain init       # Initialize directories and pull models
exobrain status     # Show current status
exobrain doctor     # Validate configuration
exobrain stage      # Stage documents (TODO)
exobrain index      # Run indexing (TODO)
exobrain rebuild    # Full rebuild (TODO)
exobrain query      # Query the index (TODO)
exobrain migrate    # Migrate from ideas/ (TODO)
```

## API Endpoints

- `GET /health` - Health check
- `GET /status` - System status
- `POST /query/global` - Global/theme query (TODO)
- `POST /query/local` - Local/neighborhood query (TODO)
- `GET /doc/:id` - Get document (TODO)
- `POST /admin/stage` - Trigger staging (TODO)
- `POST /admin/index/incremental` - Trigger incremental index (TODO)
- `POST /admin/index/rebuild` - Trigger full rebuild (TODO)

## Development

```bash
cd engine
pip install -e ".[dev]"
pytest
```
