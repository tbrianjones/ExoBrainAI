# ExoBrain + Claude Writer

A local-first personal knowledge system with two layers:

1. **ExoBrain** ; GraphRAG-powered memory engine for capturing, annotating, and querying your thoughts
2. **Claude Writer** ; AI-assisted ideation and content generation through Claude Code

Your data stays on your machine, syncs via Dropbox, and never touches external servers except for explicit local LLM calls via Ollama.

## Quick Start

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (4GB+ RAM allocated)
- [Homebrew](https://brew.sh)

### 1. Configure

```bash
cp .env.example .env
```

Edit `.env`:
```bash
EXOBRAIN_DATA_DIR=/Users/you/Dropbox/ExoBrain  # Your canonical data location
OLLAMA_MODE=native                              # Use GPU acceleration
EXOBRAIN_LLM_MODEL=llama3.1:8b                  # 8B model recommended
```

### 2. Setup Native Ollama

Native Ollama uses Metal GPU acceleration (30-50 tok/sec vs 1-2 tok/sec in Docker).

```bash
./scripts/setup-native-ollama.sh
```

This installs Ollama via Homebrew, starts the service, and pulls required models.

### 3. Start ExoBrain

```bash
docker compose up -d
```

### 4. Initialize and Verify

```bash
docker compose exec exobrain exobrain init
docker compose exec exobrain exobrain doctor
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           YOUR MACHINE                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ CANONICAL DATA ($EXOBRAIN_DATA_DIR ; syncs via Dropbox)         │    │
│  │                                                                  │    │
│  │  raw/                     overlay/annotations/                   │    │
│  │  ├── 019abc123.md         ├── 2026-01-25.jsonl                  │    │
│  │  ├── 019abc456.md         └── 2026-01-24.jsonl                  │    │
│  │  └── ...                                                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                           │
│                              ▼ stage                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ DERIVED DATA (Docker volume ; regenerable)                       │    │
│  │                                                                  │    │
│  │  staged/                  graphrag/output/                       │    │
│  │  ├── 019abc123.txt        ├── entities.parquet     (206 nodes)  │    │
│  │  └── ...                  ├── relationships.parquet (219 edges) │    │
│  │                           ├── communities.parquet               │    │
│  │                           ├── community_reports.parquet         │    │
│  │                           └── graph.graphml        (for Gephi)  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                           │
│                              ▼ query                                     │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ SERVICES (Docker Compose)                                        │    │
│  │                                                                  │    │
│  │  exobrain      ; API server           http://localhost:8420     │    │
│  │  watcher       ; File change monitor                            │    │
│  │  gephi-lite    ; Graph visualization  http://localhost:8081     │    │
│  │  dozzle        ; Log viewer           http://localhost:9998     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                              │                                           │
│                              ▼ inference                                 │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ OLLAMA (Native on Mac ; GPU accelerated)                         │    │
│  │                                                                  │    │
│  │  llama3.1:8b        ; Entity extraction, summarization          │    │
│  │  nomic-embed-text   ; Vector embeddings                         │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Capture**: Raw markdown → `raw/{uuidv7}.md`
2. **Annotate**: Overlay records → `overlay/annotations/{date}.jsonl`
3. **Stage**: Merge raw + overlays → `staged/{id}.txt`
4. **Index**: GraphRAG extracts entities, relationships, communities
5. **Query**: Global (themes) or Local (entities) search

### Key Principle

**Canonical data is permanent; derived data is regenerable.** If you delete the Docker volume, run `exobrain rebuild` to recreate the index from raw data.

## Using ExoBrain

### Capture

```bash
# Capture from stdin
echo "My idea about distributed systems..." | docker compose exec -T exobrain exobrain capture

# Capture with title
echo "Meeting notes" | docker compose exec -T exobrain exobrain capture --title "Q1 Planning"
```

### Annotate

```bash
# Add metadata to existing documents
docker compose exec exobrain exobrain annotate <doc-id> --title "My Document"
docker compose exec exobrain exobrain annotate <doc-id> --tag project-x --tag important
docker compose exec exobrain exobrain annotate <doc-id> --entity "John Smith"
docker compose exec exobrain exobrain annotate <doc-id> --link <other-id> --link-note "Related discussion"
```

### Index

```bash
# Stage all documents (merge raw + overlays)
docker compose exec exobrain exobrain stage --all

# Build/update the index
docker compose exec exobrain exobrain index

# Full rebuild (if index is corrupted or config changed)
docker compose exec exobrain exobrain rebuild
```

### Query

```bash
# Global query: themes, patterns, high-level synthesis
docker compose exec exobrain exobrain query "What themes emerge from my documents?"

# Local query: specific entities, relationships
docker compose exec exobrain exobrain query --mode local "What do I know about project X?"
```

### Visualize

1. Open http://localhost:8081 (Gephi Lite)
2. Click "Open" and load `graph.graphml` from the project root
3. Layout: Force Atlas 2 → Run → Stop
4. Color by entity type: Appearance → Partition → "type"

## CLI Reference

Run via: `docker compose exec exobrain exobrain <command>`

| Command | Description |
|---------|-------------|
| `init` | Create directories, pull Ollama models |
| `status` | Show document counts, index status, Ollama mode |
| `doctor` | Validate config, check Ollama connectivity |
| `capture [content]` | Capture new document (stdin or argument) |
| `annotate <id> [opts]` | Add title, tags, entities, links to document |
| `stage --all` | Stage all documents for indexing |
| `index` | Incremental GraphRAG update |
| `index --fast` | NLP-based extraction (faster, less accurate) |
| `rebuild` | Full index rebuild from scratch |
| `query "<text>"` | Global (theme) query |
| `query --mode local` | Local (entity) query |
| `migrate <path>` | Migrate from legacy ideas/ folder |

## HTTP API

Base: `http://localhost:8420`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | System status (docs, index, Ollama) |
| `/query/global` | POST | Theme query `{"query": "..."}` |
| `/query/local` | POST | Entity query `{"query": "..."}` |
| `/doc/` | GET | List all documents |
| `/doc/{id}` | GET | Get document content |
| `/doc/{id}/overlay` | GET | Get document annotations |
| `/admin/stage` | POST | Trigger staging |
| `/admin/index/incremental` | POST | Trigger incremental index |
| `/admin/index/rebuild` | POST | Trigger full rebuild |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `EXOBRAIN_DATA_DIR` | `/data` | Canonical data directory (Dropbox-synced) |
| `OLLAMA_MODE` | `native` | `native` (GPU) or `docker` (CPU only) |
| `EXOBRAIN_LLM_MODEL` | `llama3.1:8b` | Chat model for extraction/summarization |
| `EXOBRAIN_EMBED_MODEL` | `nomic-embed-text` | Embedding model for vector search |
| `EXOBRAIN_API_PORT` | `8420` | API server port |
| `GEPHI_PORT` | `8081` | Gephi Lite port |
| `DOZZLE_PORT` | `9998` | Log viewer port |

## Services

| Service | Port | Purpose |
|---------|------|---------|
| ExoBrain API | 8420 | REST API for queries and admin |
| Gephi Lite | 8081 | Interactive graph visualization |
| Dozzle | 9998 | Container log viewer |
| Ollama | 11434 | LLM inference (native, not in Docker) |

## Claude Writer Commands

Open this project in Claude Code to use:

| Command | Description |
|---------|-------------|
| `/ideate` | Explore an idea through guided conversation |
| `/generate-transcript` | Save current conversation as transcript |
| `/generate-view` | Create production content from an idea |
| `/generate-poem-view` | Generate poetry using Poetic Inquiry |
| `/publish-quarto` | Publish view to ideas.tbrianjones.com |

## Troubleshooting

### Reset Everything

```bash
docker compose down -v              # Remove containers and volumes
./scripts/setup-native-ollama.sh    # Reinstall Ollama models
docker compose up -d                # Start fresh
docker compose exec exobrain exobrain init
docker compose exec exobrain exobrain rebuild
```

### Check Ollama

```bash
ollama list                         # Installed models
brew services list                  # Service status
curl localhost:11434/api/tags       # API check
```

### View Logs

- **Container logs**: http://localhost:9998 (Dozzle)
- **Ollama logs**: `~/.ollama/logs/server.log` or run `ollama serve` in foreground

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Request URL missing protocol" | Empty OLLAMA_HOST | Remove EXOBRAIN_OLLAMA_HOST from .env |
| Indexing stalls at extract_graph | Ollama not running | `brew services start ollama` |
| Very slow indexing (1-2 tok/sec) | Docker Ollama mode | Set `OLLAMA_MODE=native` in .env |
| ArrowStringArray error | pandas 3.0 bug | Already pinned to <3.0 in requirements.txt |

## Known Limitations

- **Watcher overlay handling incomplete**: Changing overlay files doesn't auto-restage (run `stage --all` manually)
- **No authentication**: API is local-only; don't expose to network
- **Long index times**: Full rebuild with llama3.1:8b takes 20-40 minutes for ~50 documents
