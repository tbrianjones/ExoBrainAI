---
name: exobrain
description: Interface with the ExoBrain local knowledge system for object storage, tagging, linking, search, and retrieval
---

# ExoBrain Skill

Interface with the ExoBrain SQLite-backed personal knowledge system. Everything is an object; objects have types, spaces, tags, links, and optional file attachments.

## When to Use

Use ExoBrain when you need to:
- Store thoughts, transcripts, documents, notes, or URLs
- Search across all stored content via full-text search
- Tag, link, and organize knowledge objects
- List and filter objects by type, space, or tag
- Attach files to objects for evidence preservation
- Browse and grep projected markdown files directly
- Edit knowledge objects via projected files (auto-synced)
- Query the GraphRAG index for theme or entity analysis (optional)

## CLI Commands

Run via Docker Compose:

```bash
docker compose exec exobrain exobrain <command>
```

All commands support `--json` for structured output. Use `--json` when parsing results programmatically.

### System Commands

```bash
# Initialize database and bootstrap types/spaces
exobrain init --json

# Show status: object counts, DB size, integrity
exobrain status --json

# Validate database integrity and check for orphaned files
exobrain doctor --json

# Show version
exobrain version
```

### Capture and Retrieve Objects

```bash
# Capture a new object (content as argument)
exobrain capture "My thought about X" --title "Insight on X" --type note --tag important --json

# Capture from stdin
echo "Long content..." | exobrain capture --title "Title" --type document --json

# Capture with file attachment
exobrain capture "Description" --title "Report" --type document --file /path/to/report.pdf --json

# Get full object detail
exobrain get <id-or-prefix> --json

# Search across title, summary, content (FTS5)
exobrain search "keyword" --json

# List with filters
exobrain list --type note --tag important --json
exobrain list --space work --limit 10 --json

# Update object
exobrain update <id> --title "New Title" --summary "Updated summary" --json

# Delete object
exobrain delete <id> --yes --json
```

### Tags

```bash
# Add tag
exobrain tag add <id> "project-x" --json

# Remove tag
exobrain tag remove <id> "project-x" --json

# List all tags with counts
exobrain tag list --json
```

### Links

```bash
# Link two objects
exobrain link create <from-id> <to-id> "summarizes" --json

# List links for an object
exobrain link list <id> --json

# Remove a link
exobrain link remove <link-id> --json
```

### Types and Spaces

```bash
# List all types
exobrain type list --json

# Create a custom type (rarely needed)
exobrain type create "recipe" --summary "Food recipes" --json

# List all spaces
exobrain space list --json

# Create a space (auto-creates parents)
exobrain space create "work/exobrain" --json
```

### Files

```bash
# Attach file to object
exobrain file attach <id> /path/to/file.pdf --json

# Get file path
exobrain file path <id> --json

# Detach file
exobrain file detach <id> --json
```

### Projection

Project objects to markdown files for direct AI/human access:

```bash
# Project objects to markdown files
exobrain project --json

# Preview what would be projected
exobrain project --dry-run --json

# Project and remove stale files
exobrain project --cleanup --json

# View projection tier statistics
exobrain tier status --json
```

**Projected file location:** `$EXOBRAIN_DATA_DIR/projected/`

**File format:**
```markdown
---
id: 019477a3-b1c2-7def-8901-234567890abc
type: note
space: work/exobrain
title: "My Document Title"
summary: "Short description"
tags:
  - architecture
  - design
created: 2026-01-15T10:30:00Z
updated: 2026-01-28T14:22:00Z
---

The actual content body here. Fully editable.
```

**Sync behavior:**
- Edits to projected files automatically sync back to SQLite via watcher
- `id` and `space` are immutable; use CLI to change
- `title`, `summary`, `tags`, `content` are mutable

**Projection override flags:**
```bash
# Always include in projection (even with low score)
exobrain update <id> --always-project --json

# Never include in projection (even with high score)
exobrain update <id> --never-project --json

# Use score-based projection (default)
exobrain update <id> --auto-project --json
```

### GraphRAG (Optional)

```bash
# Stage SQLite objects for GraphRAG
exobrain graphrag stage --json

# Run indexing
exobrain graphrag index --json

# Query themes
exobrain graphrag query "What themes emerge?" --json

# Query entities
exobrain graphrag query "What about project X?" --mode local --json
```

## JSON Output Schemas

### Capture / Get Response
```json
{
  "id": "019477a3-b1c2-7def-8901-234567890abc",
  "type_id": "00000000-0000-7000-8000-000000000004",
  "space_id": "00000000-0000-7000-8000-000000000101",
  "title": "My thought",
  "summary": null,
  "content": "The actual content...",
  "type_name": "Document",
  "space_name": "Primitives",
  "created_at": "2026-01-27T10:00:00.000Z",
  "updated_at": "2026-01-27T10:00:00.000Z"
}
```

### Search / List Response
```json
[
  {
    "id": "...",
    "type_name": "Note",
    "space_name": "Work",
    "title": "My note",
    "summary": null,
    "created_at": "..."
  }
]
```

### Status Response
```json
{
  "version": "2.1.0",
  "data_dir": "/data",
  "db_path": "/data/exobrain.db",
  "db_size_bytes": 49152,
  "object_count": 15,
  "type_counts": {"Document": 5, "Note": 3, "Type": 7},
  "tag_count": 8,
  "link_count": 2,
  "file_count": 1,
  "integrity": "ok"
}
```

## Object Types

Bootstrap types (always available):
- `type` ; object type definitions
- `space` ; hierarchical organizational units
- `tag` ; semantic label objects
- `document` ; general purpose documents
- `transcript` ; conversation or interview transcripts
- `note` ; short thoughts or observations
- `url` ; web resource references

## Spaces

Bootstrap spaces:
- `primitives` ; system primitive objects
- `primitives/type` ; type definitions
- `primitives/space` ; space definitions
- `primitives/tag` ; tag definitions

Create user spaces with: `exobrain space create "work/project-name"`

## ID Prefix Matching

All ID arguments accept either full UUIDs or prefixes (minimum 8 characters):
```bash
exobrain get 019477a3    # matches 019477a3-b1c2-7def-8901-234567890abc
```

## Data Location

All data lives at `$EXOBRAIN_DATA_DIR`:
```
$EXOBRAIN_DATA_DIR/
├── exobrain.db        # SQLite database (source of truth)
├── files/             # Sharded file attachments
│   └── 01/94/         # Two-level shard directories
├── projected/         # AI-readable markdown projections
│   ├── CLAUDE.md      # Root index
│   ├── inbox/         # Default space
│   └── work/          # User spaces
│       └── exobrain/
└── raw/               # Legacy v1 raw documents
```

## Integration Workflow

When using ExoBrain during ideation or content generation:

1. **Capture** the raw content: `exobrain capture "..." --type note --tag ideation`
2. **Search** for related content: `exobrain search "related topic" --json`
3. **Link** related objects: `exobrain link create <new-id> <related-id> "builds on"`
4. **Tag** for organization: `exobrain tag add <id> "project-x"`
5. **Propose** titles and summaries using Claude's judgment, then update: `exobrain update <id> --title "Better Title" --summary "..."`
