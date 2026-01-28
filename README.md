# ExoBrain

A local-first personal knowledge system with SQLite-backed storage where everything is an object. Includes AI-assisted ideation and content generation through Claude Code.

Your data stays on your machine, syncs via Dropbox, and never touches external servers except for explicit local LLM calls via Ollama (optional, for GraphRAG).

## Quick Start

### Prerequisites

- macOS with Apple Silicon (M1/M2/M3/M4)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (4GB+ RAM allocated)

### 1. Configure

```bash
cp .env.example .env
```

Edit `.env`:
```bash
EXOBRAIN_DATA_DIR=/Users/you/Dropbox/ExoBrain  # Your canonical data location
```

### 2. Start ExoBrain

```bash
docker compose up -d
docker compose exec exobrain exobrain init
docker compose exec exobrain exobrain status
```

### 3. Capture Your First Object

```bash
# Capture from stdin (note: use -T for piped input)
echo "My idea about distributed systems" | docker compose exec -T exobrain exobrain capture

# Capture with title and tags
docker compose exec exobrain exobrain capture "Meeting notes from Q1 planning" \
  --title "Q1 Planning" --tag meeting --tag planning

# Capture with a file attachment
docker compose exec exobrain exobrain capture "Design document" \
  --title "Architecture v2" --file /path/to/diagram.png
```

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         YOUR MACHINE                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ CANONICAL DATA ($EXOBRAIN_DATA_DIR ; syncs via Dropbox)   │    │
│  │                                                            │    │
│  │  exobrain.db              files/              projected/   │    │
│  │  (SQLite; all objects,    ├── ab/cd/...       ├── CLAUDE.md│    │
│  │   tags, links, FTS5)      └── ef/01/...       └── space/   │    │
│  │                                                  └── *.md  │    │
│  └──────────────────────────────────────────────────────────┘    │
│                              │                                     │
│                              ▼ query / mutate                      │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ SERVICES (Docker Compose)                                  │    │
│  │                                                            │    │
│  │  exobrain      ; CLI + API server   http://localhost:8420 │    │
│  │  dozzle        ; Log viewer         http://localhost:9998 │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ OPTIONAL (--profile graphrag)                              │    │
│  │                                                            │    │
│  │  ollama (native) ; LLM inference with GPU acceleration    │    │
│  │  gephi-lite      ; Graph visualization  :8081             │    │
│  │  watcher         ; File change monitor                    │    │
│  └──────────────────────────────────────────────────────────┘    │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

### Data Model

Everything is an object. Objects have:
- **Type** (Document, Note, Transcript, URL, or custom)
- **Space** (hierarchical organization: `work/exobrain`, `personal/journal`)
- **Tags** (free-text labels)
- **Links** (directed relationships to other objects)
- **File** (optional attachment, sharded on disk)
- **Content** (full text, indexed by FTS5)

Bootstrap types and spaces are created automatically on `init`.

### Key Principle

**Canonical data is permanent; derived data is regenerable.** The SQLite database and attached files sync via Dropbox. GraphRAG indexes are derived and can be rebuilt.

## Using ExoBrain

### Objects

```bash
# Capture
docker compose exec exobrain exobrain capture "Your thought here" --type note --space inbox
echo "Content from stdin" | docker compose exec -T exobrain exobrain capture --title "Stdin capture"

# Read
docker compose exec exobrain exobrain get <id-or-prefix>
docker compose exec exobrain exobrain list --type document --space inbox --tag important
docker compose exec exobrain exobrain search "distributed systems"

# Update
docker compose exec exobrain exobrain update <id> --title "New title" --space work/projects

# Delete
docker compose exec exobrain exobrain delete <id>
```

### Tags and Links

```bash
# Tags
docker compose exec exobrain exobrain tag add <id> "important"
docker compose exec exobrain exobrain tag remove <id> "important"
docker compose exec exobrain exobrain tag list

# Links
docker compose exec exobrain exobrain link create <from-id> <to-id> "relates-to"
docker compose exec exobrain exobrain link list <id>
docker compose exec exobrain exobrain link remove <link-id>
```

### Files

```bash
docker compose exec exobrain exobrain file attach <id> /path/to/file.pdf
docker compose exec exobrain exobrain file path <id>
docker compose exec exobrain exobrain file detach <id>
```

### Types and Spaces

```bash
# List what exists
docker compose exec exobrain exobrain type list
docker compose exec exobrain exobrain space list

# Create custom types/spaces
docker compose exec exobrain exobrain type create "Meeting" --summary "Meeting notes"
docker compose exec exobrain exobrain space create "work/exobrain"
```

### System

```bash
docker compose exec exobrain exobrain status   # Object counts, DB info
docker compose exec exobrain exobrain doctor   # Integrity check, orphan scan
docker compose exec exobrain exobrain version
```

### Projection

Project objects to markdown files for direct file access and AI-readable browsing:

```bash
# Project objects to $EXOBRAIN_DATA_DIR/projected/
docker compose exec exobrain exobrain project

# Preview without writing
docker compose exec exobrain exobrain project --dry-run

# Remove stale projections
docker compose exec exobrain exobrain project --cleanup

# View projection statistics
docker compose exec exobrain exobrain tier status
```

Projected files are organized by space, have YAML frontmatter, and support bidirectional sync (edits sync back to SQLite). Control which objects are projected:

```bash
docker compose exec exobrain exobrain update <id> --always-project  # Force inclusion
docker compose exec exobrain exobrain update <id> --never-project   # Force exclusion
docker compose exec exobrain exobrain update <id> --auto-project    # Use scoring (default)
```

### GraphRAG (optional)

```bash
# Stage objects for GraphRAG, then index
docker compose exec exobrain exobrain graphrag stage
docker compose exec exobrain exobrain graphrag index
docker compose exec exobrain exobrain graphrag query "What themes emerge?"
```

All commands support `--json` for machine-readable output. Object IDs can be shortened to unique prefixes (minimum 8 characters).

## HTTP API

Base: `http://localhost:8420`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | System status (objects, DB, integrity) |
| `/query/global` | POST | Theme query `{"query": "..."}` (GraphRAG) |
| `/query/local` | POST | Entity query `{"query": "..."}` (GraphRAG) |
| `/doc/` | GET | List documents |
| `/doc/{id}` | GET | Get document |
| `/admin/stage` | POST | Trigger staging |
| `/admin/index/incremental` | POST | Incremental index |
| `/admin/index/rebuild` | POST | Full rebuild |

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `EXOBRAIN_DATA_DIR` | `/data` | Canonical data directory (Dropbox-synced) |
| `EXOBRAIN_CACHE_DIR` | `/cache` | Derived data directory (container-local) |
| `OLLAMA_MODE` | `native` | `native` (GPU) or `docker` (CPU only) |
| `EXOBRAIN_LLM_MODEL` | `llama3.1:8b` | Chat model for extraction/summarization |
| `EXOBRAIN_EMBED_MODEL` | `nomic-embed-text` | Embedding model for vector search |
| `EXOBRAIN_API_PORT` | `8420` | API server port |

## Commands

Open this project in Claude Code to use:

| Command | Description |
|---------|-------------|
| `/ideate` | Explore an idea through guided conversation |
| `/generate-transcript` | Save current conversation as transcript |
| `/generate-view` | Create production content from an idea |
| `/generate-poem-view` | Generate poetry using Poetic Inquiry |
| `/generate-academic-infographic-view` | Create academically rigorous infographic specs |
| `/publish-quarto` | Publish view to ideas.tbrianjones.com |

## Services

| Service | Port | Purpose |
|---------|------|---------|
| ExoBrain API | 8420 | REST API + CLI |
| Dozzle | 9998 | Container log viewer |
| Gephi Lite | 8081 | Graph visualization (optional; graphrag profile) |
| Ollama | 11434 | LLM inference (native, not in Docker by default) |

## Troubleshooting

### Reset Everything

```bash
docker compose down -v              # Remove containers and volumes
docker compose up -d                # Start fresh
docker compose exec exobrain exobrain init
```

### View Logs

- **Container logs**: http://localhost:9998 (Dozzle)
- **CLI output**: All commands support `--json` for debugging

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| "Database not found" | Not initialized | Run `exobrain init` |
| "Object not found" | Wrong ID/prefix | Use `list` to find objects; prefix needs 8+ chars |
| "Ambiguous prefix" | Multiple matches | Use more characters of the ID |
| "Cannot delete bootstrap object" | Trying to delete Type/Space | Bootstrap objects are protected |

## Known Limitations

- **No authentication**: API is local-only; don't expose to network
- **Single-file attachment**: Each object supports at most one attached file
- **GraphRAG optional**: Full-text search works without GraphRAG; theme/entity queries require it
