# ExoBrain + Claude Writer

A local-first personal knowledge system with two layers:

1. **ExoBrain** ; GraphRAG-powered memory engine for capturing, annotating, and querying your thoughts
2. **Claude Writer** ; AI-assisted ideation and content generation through Claude Code

Your data stays on your machine, syncs via Dropbox (or any folder sync), and never touches external servers except for the LLM calls you explicitly make.

## Quick Start

### 1. Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Claude Code](https://claude.ai/download) (for ideation workflows)

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` to set your data directory:

```bash
# Where your documents and annotations live (syncs via Dropbox)
EXOBRAIN_DATA_DIR=/Users/you/Dropbox/ExoBrain
```

### 3. Start the Engine

```bash
docker compose up -d
```

This starts four services:
- **exobrain** ; API server (port 8420)
- **exobrain-watcher** ; File watcher for automatic staging
- **exobrain-ollama** ; Local LLM (Llama 3.1 8B + nomic-embed)
- **exobrain-dozzle** ; Log viewer (port 9998)

### 4. Initialize

```bash
docker compose exec exobrain exobrain init
```

This creates the directory structure and pulls Ollama models.

### 5. Verify

```bash
curl http://localhost:8420/health
# {"status":"ok","version":"2.0.0"}
```

## Using ExoBrain

### Capture a Thought

Zero friction. Just write:

```bash
# From stdin
echo "My idea about consciousness..." | docker compose exec -T exobrain exobrain capture

# With a title
echo "Notes from meeting..." | docker compose exec -T exobrain exobrain capture --title "Q1 Planning"
```

Returns a document ID (UUIDv7). That's it. No tags, no structure, no decisions.

### Add Structure Later

Structure is optional and can be added anytime via overlay annotations:

```bash
# Add to today's overlay file
echo '{"v":1,"id":"'$(uuidgen)'","ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","doc_id":"YOUR_DOC_ID","source":"human","title":"My Title","tags":[{"tag":"project-x"}]}' \
  >> $EXOBRAIN_DATA_DIR/overlay/annotations/$(date +%Y-%m-%d).jsonl
```

### Stage Documents

Staging merges raw content with overlay annotations into indexed documents:

```bash
# Stage all documents
docker compose exec exobrain exobrain stage --all

# Stage a specific document
docker compose exec exobrain exobrain stage --doc <doc-id>
```

### Build the Index

```bash
# Incremental update (fast, for new docs)
docker compose exec exobrain exobrain index

# Full rebuild (slow, for model changes)
docker compose exec exobrain exobrain rebuild
```

### Query Your Memory

```bash
# Global query: themes and patterns across everything
docker compose exec exobrain exobrain query "What themes emerge around consciousness?"

# Local query: specific entity neighborhoods
docker compose exec exobrain exobrain query --mode local "What do I know about project X?"
```

### Check Status

```bash
docker compose exec exobrain exobrain status
docker compose exec exobrain exobrain doctor
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `exobrain init` | Create directories, pull Ollama models |
| `exobrain status` | Show document counts, index status |
| `exobrain doctor` | Validate config, check Ollama connectivity |
| `exobrain capture [content]` | Capture a new document (stdin or argument) |
| `exobrain stage --all` | Stage all documents |
| `exobrain stage --doc <id>` | Stage specific document |
| `exobrain index` | Run incremental GraphRAG update |
| `exobrain rebuild` | Full index rebuild |
| `exobrain query "<text>"` | Global (theme) query |
| `exobrain query --mode local "<text>"` | Local (entity) query |
| `exobrain migrate <path>` | Migrate from ideas/ folder (dry-run by default) |

## HTTP API

Base URL: `http://localhost:8420`

### Health & Status

```bash
GET /health          # {"status":"ok","version":"2.0.0"}
GET /status          # Full system status
```

### Query

```bash
POST /query/global   # Theme-level query
POST /query/local    # Entity-neighborhood query

# Body: {"query": "your question", "community_level": 2}
```

### Documents

```bash
GET /doc/                    # List all document IDs
GET /doc/{id}                # Get document (raw + overlay + staged)
GET /doc/{id}/raw            # Get raw content only
GET /doc/{id}/overlay        # Get aggregated overlay data
GET /doc/{id}/staged         # Get staged content
GET /doc/{id}/links          # Get linked documents
```

### Admin

```bash
POST /admin/stage            # Trigger staging {"doc_id": "..." or null for all}
POST /admin/index/incremental
POST /admin/index/rebuild
```

## Monitoring

**Dozzle** provides real-time log viewing at http://localhost:9998

Filtered to ExoBrain containers only. Useful for debugging indexing and query issues.

## Claude Writer Commands

For ideation workflows, open this project in Claude Code and use:

| Command | What it does |
|---------|--------------|
| `/ideate` | Explore an idea through guided conversation |
| `/generate-transcript` | Save the current conversation to an idea space |
| `/generate-view` | Create content (blog post, brief, essay) from an idea |
| `/generate-poem-view` | Generate poetry using Poetic Inquiry methodology |
| `/generate-academic-infographic-view` | Create infographic specifications |
| `/publish-quarto` | Publish a view to ideas.tbrianjones.com |

## Architecture

### Data Flow

```
Capture                    Index                      Query
   │                         │                          │
   ▼                         ▼                          ▼
┌──────┐    ┌─────────┐    ┌─────────┐    ┌──────────────────┐
│ Raw  │───▶│ Overlay │───▶│ Staged  │───▶│ GraphRAG Index   │
│ Docs │    │ (JSONL) │    │  Docs   │    │ (entities, rels, │
└──────┘    └─────────┘    └─────────┘    │  communities)    │
                                          └──────────────────┘
```

1. **Raw Documents** ; Plain markdown, no required structure. UUIDv7 filenames.
2. **Overlay Annotations** ; Append-only JSONL with titles, summaries, tags, entities, links.
3. **Staged Documents** ; Merged view of raw + overlays, formatted for indexing.
4. **GraphRAG Index** ; Knowledge graph with entities, relationships, and community summaries.

### Directory Structure

```
$EXOBRAIN_DATA_DIR (Dropbox-synced)
├── raw/                    # Your documents (canonical)
│   └── {uuidv7}.md
└── overlay/
    └── annotations/        # Your annotations (canonical)
        └── YYYY-MM-DD.jsonl

$EXOBRAIN_CACHE_DIR (container volume)
├── staged/                 # Merged docs (regenerable)
├── graphrag/               # Index artifacts (regenerable)
│   ├── output/
│   └── cache/
└── logs/
```

**Key insight**: Only `raw/` and `overlay/` are canonical. Everything else is derived and can be regenerated. This keeps your Dropbox sync fast and your data portable.

### Container Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Docker Compose                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │   exobrain   │  │   watcher    │  │      ollama      │ │
│  │  (FastAPI)   │  │  (watchdog)  │  │  (Llama 3.1 8B)  │ │
│  │  port 8420   │  │              │  │  port 11434      │ │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘ │
│         │                 │                    │           │
│         ▼                 ▼                    ▼           │
│  ┌────────────────────────────────────────────────────────┐│
│  │              Shared Volumes                            ││
│  │  /data  ← $EXOBRAIN_DATA_DIR (Dropbox)                ││
│  │  /cache ← exobrain_cache (Docker volume)              ││
│  └────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────┘
```

### Overlay Schema

Each JSONL line is an annotation record:

```json
{
  "v": 1,
  "id": "01992c8f3c9a7...",
  "ts": "2026-01-23T20:12:00Z",
  "doc_id": "01992c8b0d9e7...",
  "source": "human|ai|system|import",
  "title": "Optional title",
  "summary": "Optional summary",
  "tags": [{"tag": "project-x", "confidence": 0.9}],
  "entities": [{"name": "Claude", "confidence": 1.0}],
  "links": [{"doc_id": "...", "note": "Related discussion"}],
  "extra": {}
}
```

Multiple records can reference the same `doc_id`. Staging aggregates them additively.

### Staged Document Format

```markdown
[DOC_ID: 01992c8b0d9e7...]

[OVERLAY]
TITLES:
- My Document Title

TAGS:
- project-x (confidence=0.9)

ENTITIES:
- Claude (confidence=1.0)

LINKS:
- 01992c8a2c6a7... ; Related discussion

[RAW]
The original document content goes here...
```

## Configuration

All settings via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `EXOBRAIN_DATA_DIR` | `/data` | Canonical data (Dropbox) |
| `EXOBRAIN_CACHE_DIR` | `/cache` | Derived data (container) |
| `EXOBRAIN_API_PORT` | `8420` | API server port |
| `EXOBRAIN_USER` | `Unknown` | Your name (for overlays) |
| `EXOBRAIN_LLM_MODEL` | `llama3.1:8b` | Ollama chat model |
| `EXOBRAIN_EMBED_MODEL` | `nomic-embed-text` | Ollama embedding model |
| `EXOBRAIN_OVERLAY_WINDOW_DAYS` | `30` | Days of overlays to aggregate |
| `EXOBRAIN_WATCHER_DEBOUNCE_SECONDS` | `2` | Watcher debounce delay |

## Migration from ideas/

If you have existing content in `ideas/`:

```bash
# Dry run (see what would be migrated)
docker compose exec exobrain exobrain migrate ideas/0001-my-idea

# Migrate transcripts only
docker compose exec exobrain exobrain migrate ideas/0001-my-idea --transcripts-only

# Actually execute
docker compose exec exobrain exobrain migrate ideas/0001-my-idea --execute
```

## Principles

1. **Raw is canonical** ; Your documents are the ground truth
2. **Overlays hold intent** ; Structure and annotations live separately
3. **Staged is derived** ; Always regenerable from raw + overlays
4. **Zero-friction capture** ; No decisions required at capture time
5. **Local-first** ; Your data, your machine, your control

## Repository Structure

```
claude_writer/
├── engine/                 # ExoBrain Python package
│   ├── src/
│   │   ├── core/           # Models, raw ops, overlay ops, stager
│   │   ├── graphrag/       # GraphRAG config, indexer, querier
│   │   ├── cli/            # Typer CLI commands
│   │   ├── api/            # FastAPI routes
│   │   └── watcher/        # File watcher, scheduler
│   ├── Dockerfile
│   └── requirements.txt
├── .claude/
│   ├── commands/           # Claude Code commands
│   ├── agents/             # Autonomous subagents
│   └── skills/             # Utility skills (exobrain, title-generation, etc.)
├── ideas/                  # Legacy idea spaces (migrating to ExoBrain)
├── templates/              # Voice, poetry, infographic frameworks
├── site/                   # Quarto site for publishing
├── docker-compose.yml
└── .env.example
```
