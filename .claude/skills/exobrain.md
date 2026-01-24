---
name: exobrain
description: Interface with the ExoBrain local memory engine for document storage, annotation, and retrieval
---

# ExoBrain Skill

Interface with the ExoBrain GraphRAG memory engine for intelligent document storage and retrieval.

## When to Use

Use ExoBrain when you need to:
- Store raw thoughts, transcripts, or notes for long-term memory
- Add annotations (titles, summaries, tags, entities, links) to documents
- Query across all stored content for themes or specific topics
- Find related documents and connections

## CLI Commands

Run these via Docker Compose:

```bash
# Inside the container
docker compose exec exobrain exobrain <command>

# Or from host with alias
alias exo="docker compose exec exobrain exobrain"
```

### Capture a Document

```bash
# From stdin
echo "My thoughts..." | exobrain capture

# With title
echo "My thoughts..." | exobrain capture --title "Morning reflections"
```

Returns the document ID (UUIDv7).

### Stage Documents

Staging merges raw content with overlay annotations:

```bash
exobrain stage --all         # Stage all documents
exobrain stage --doc <id>    # Stage specific document
```

### Index for Retrieval

```bash
exobrain index               # Incremental update
exobrain rebuild             # Full rebuild
```

### Query

```bash
# Global: themes and patterns across corpus
exobrain query "What themes emerge around consciousness?"

# Local: specific entity neighborhoods
exobrain query --mode local "What do I know about Claude Code?"
```

### Status and Health

```bash
exobrain status              # Show document counts, index status
exobrain doctor              # Validate config and connectivity
```

## HTTP API

Base URL: `http://localhost:8420`

### Health & Status

```bash
curl http://localhost:8420/health
curl http://localhost:8420/status
```

### Query

```bash
# Global query
curl -X POST http://localhost:8420/query/global \
  -H "Content-Type: application/json" \
  -d '{"query": "What themes emerge?"}'

# Local query
curl -X POST http://localhost:8420/query/local \
  -H "Content-Type: application/json" \
  -d '{"query": "What about project X?"}'
```

### Documents

```bash
# List all documents
curl http://localhost:8420/doc/

# Get document with raw, overlay, and staged content
curl http://localhost:8420/doc/<id>

# Get just overlay annotations
curl http://localhost:8420/doc/<id>/overlay

# Get linked documents
curl http://localhost:8420/doc/<id>/links
```

### Admin Operations

```bash
# Trigger staging
curl -X POST http://localhost:8420/admin/stage \
  -H "Content-Type: application/json" \
  -d '{}'

# Trigger incremental index
curl -X POST http://localhost:8420/admin/index/incremental

# Trigger full rebuild
curl -X POST http://localhost:8420/admin/index/rebuild
```

## Overlay Annotations

Add structure to documents by appending JSONL records:

```bash
echo '{"v":1,"id":"<new-uuid>","ts":"2026-01-24T10:00:00Z","doc_id":"<doc-uuid>","source":"human","title":"My Title","tags":[{"tag":"idea"}]}' \
  >> $EXOBRAIN_DATA_DIR/overlay/annotations/2026-01-24.jsonl
```

Fields:
- `title`: Human-readable title
- `summary`: Brief summary
- `tags`: Array of `{tag, confidence?, note?}`
- `entities`: Array of `{name, confidence?, note?}`
- `links`: Array of `{doc_id, confidence?, note?}`

## Data Location

All data lives outside the repo at `$EXOBRAIN_DATA_DIR`:

```
$EXOBRAIN_DATA_DIR/
├── raw/           # UUIDv7.md files (your content)
├── overlay/
│   └── annotations/  # YYYY-MM-DD.jsonl files
├── staged/        # Generated merged docs
└── graphrag/
    └── output/    # Index artifacts
```

## Integration Notes

ExoBrain is the memory layer. Claude commands like `/ideate` and `/generate-transcript` currently write to `ideas/`. After migration (Phase 9), new content will flow through ExoBrain.

For now, use ExoBrain for:
- Ad-hoc thought capture
- Querying across all memory
- Finding connections between ideas

Use `ideas/` workflow for:
- Structured ideation sessions
- View generation (blog posts, etc.)
