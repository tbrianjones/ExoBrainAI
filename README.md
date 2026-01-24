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

### Annotate Documents

Structure is optional and can be added anytime. Use the `annotate` command to add metadata to any document:

```bash
# Add a title
docker compose exec exobrain exobrain annotate <doc-id> --title "My Document Title"

# Add tags (repeatable flag)
docker compose exec exobrain exobrain annotate <doc-id> --tag project-x --tag important

# Add entities (people, places, concepts)
docker compose exec exobrain exobrain annotate <doc-id> --entity "John Smith" --entity "Acme Corp"

# Add a summary
docker compose exec exobrain exobrain annotate <doc-id> --summary "Discussion about Q1 roadmap priorities"

# Link to another document with a note explaining the relationship
docker compose exec exobrain exobrain annotate <doc-id> --link <other-doc-id> --link-note "Related discussion"

# Combine multiple annotations in one call
docker compose exec exobrain exobrain annotate <doc-id> \
  --title "Q1 Planning Meeting" \
  --tag meeting \
  --tag q1-planning \
  --entity "Marketing Team" \
  --summary "Discussed launch timeline and budget allocation"
```

**How it works:** Each `annotate` call appends a new overlay record to today's JSONL file. You can annotate the same document multiple times; staging aggregates all annotations additively. This append-only design means you never lose annotation history.

**Options:**

| Flag | Short | Description |
|------|-------|-------------|
| `--title` | `-t` | Set document title |
| `--summary` | `-s` | Set document summary |
| `--tag` | | Add a tag (use multiple times for multiple tags) |
| `--entity` | `-e` | Add an entity mention (use multiple times) |
| `--link` | `-l` | Link to another document ID (use multiple times) |
| `--link-note` | | Note describing the link relationship (use with single `--link`) |
| `--source` | | Annotation source: human, ai, system (default: human) |

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
| `exobrain annotate <id> [opts]` | Add annotations (title, tags, entities, links) |
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
Capture                    Annotate                   Stage                      Query
   │                          │                         │                          │
   ▼                          ▼                         ▼                          ▼
┌──────┐                 ┌─────────┐               ┌─────────┐    ┌──────────────────┐
│ Raw  │                 │ Overlay │──aggregate───▶│ Staged  │───▶│ GraphRAG Index   │
│ Docs │                 │ (JSONL) │               │  Docs   │    │ (entities, rels, │
└──────┘                 └─────────┘               └─────────┘    │  communities)    │
                                                                   └──────────────────┘
```

1. **Raw Documents** ; Plain markdown, no required structure. UUIDv7 filenames.
2. **Overlay Annotations** ; Append-only JSONL with titles, summaries, tags, entities, links.
3. **Staged Documents** ; Merged view of raw + aggregated overlays, formatted for indexing.
4. **GraphRAG Index** ; Knowledge graph with entities, relationships, and community summaries.

### Directory Structure

```
$EXOBRAIN_DATA_DIR (syncs via Dropbox)
├── raw/                              # Your documents (canonical)
│   ├── 069747b6-d8a2-7e08-8000-ced8a1c38840.md
│   └── 069747c6-d32e-7a1f-8000-30de033be53a.md
└── overlay/
    └── annotations/                  # Your annotations (canonical)
        ├── 2026-01-23.jsonl
        └── 2026-01-24.jsonl

$EXOBRAIN_CACHE_DIR (container volume, regenerable)
├── staged/                           # Merged docs for indexing
│   ├── 069747b6-d8a2-7e08-8000-ced8a1c38840.md
│   └── 069747c6-d32e-7a1f-8000-30de033be53a.md
├── graphrag/                         # Index artifacts
│   ├── output/
│   └── cache/
└── logs/
```

**Key insight**: Only `raw/` and `overlay/` are canonical. Everything in `$EXOBRAIN_CACHE_DIR` is derived and can be regenerated. This keeps your Dropbox sync fast and your data portable.

### Raw Document Format

Raw documents are plain markdown files with UUIDv7 filenames. No required structure; write whatever you want:

```markdown
# My Document

Any markdown content goes here. No required frontmatter,
no required structure. Just your thoughts.
```

Filename: `069747b6-d8a2-7e08-8000-ced8a1c38840.md`

The UUIDv7 is time-sortable, so `ls` will show documents in creation order.

### Overlay Annotation Format

Overlays are stored as **append-only JSONL** files, partitioned by date. Each line is an independent annotation record:

```json
{
  "v": 1,
  "id": "069747d8-50bc-74e8-8000-c6671ad97cfe",
  "ts": "2026-01-24T08:06:29.045988",
  "doc_id": "069747b6-d8a2-7e08-8000-ced8a1c38840",
  "source": "human",
  "title": "Full Transcript: ExoBrain Core Vision",
  "summary": "Raw conversation exploring ExoBrain vision...",
  "tags": [
    {"tag": "transcript", "confidence": null, "note": null},
    {"tag": "exobrain", "confidence": null, "note": null}
  ],
  "entities": [
    {"name": "Brian", "confidence": null, "note": null}
  ],
  "links": null,
  "extra": null
}
```

**Schema fields:**

| Field | Type | Description |
|-------|------|-------------|
| `v` | int | Schema version (always 1) |
| `id` | string | Unique record ID (UUIDv7) |
| `ts` | datetime | When this annotation was created |
| `doc_id` | string | The raw document this annotates |
| `source` | enum | Who created it: `human`, `ai`, `system`, `import` |
| `title` | string? | Document title |
| `summary` | string? | Document summary |
| `tags` | array? | List of `{tag, confidence?, note?}` |
| `entities` | array? | List of `{name, confidence?, note?}` |
| `links` | array? | List of `{doc_id, confidence?, note?}` |
| `extra` | object? | Arbitrary additional data |

**Append-only design:** Multiple records can reference the same `doc_id`. Each `annotate` command appends a new record. Migration creates records. AI analysis creates records. They all accumulate.

### How Staging Aggregates Overlays

When you run `stage`, the system collects all overlay records for a document and merges them:

```
Overlay Record 1 (from migration):
  title: "Transcript: Exobrain Core Vision"
  tags: [transcript, idea:exobrain]

Overlay Record 2 (from annotate):
  title: "Full Transcript: ExoBrain Core Vision"
  summary: "Raw conversation exploring..."
  tags: [ai-architecture, knowledge-management]
  entities: [Brian, Claude]

Overlay Record 3 (from annotate):
  links: [{doc_id: "...", note: "Related discussion"}]

         ↓ aggregate_overlays() ↓

Aggregated Overlay:
  titles: ["Transcript: Exobrain Core Vision", "Full Transcript: ExoBrain Core Vision"]
  summaries: ["Raw conversation exploring..."]
  tags: [transcript, idea:exobrain, ai-architecture, knowledge-management]
  entities: [Brian, Claude]
  links: [{doc_id: "...", note: "Related discussion"}]
```

All values are collected additively. Nothing is overwritten or lost.

### Staged Document Format

The staged document combines raw content with aggregated overlays:

```markdown
[DOC_ID: 069747b6-d8a2-7e08-8000-ced8a1c38840]

[OVERLAY]
TITLES:
- Transcript: Exobrain Core Vision (2026-01-15)
- Full Transcript: ExoBrain Core Vision

SUMMARIES:
- Raw conversation exploring the core vision for ExoBrain...

TAGS:
- transcript (confidence=1.0)
- idea:exobrain (confidence=1.0)
- ai-architecture
- knowledge-management

ENTITIES:
- Brian
- Claude

LINKS:
- 069747c6-d32e-7a1f-8000-30de033be53a ; Synthesized summary of this transcript

[RAW]
# Full Transcript: ExoBrain Core Vision
...original document content...
```

This format is what GraphRAG indexes. The overlay metadata helps the LLM understand document structure and relationships.

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
