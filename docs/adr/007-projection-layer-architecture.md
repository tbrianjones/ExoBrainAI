# ADR 007: Projection Layer Architecture

- **Status:** Accepted
- **Date:** 2026-01-28
- **Tags:** projection, markdown, ai-native, bidirectional-sync
- **Impact:** High

## Context

ExoBrain stores knowledge in SQLite with a CLI as the sole write interface (ADR-003). While this provides data integrity and atomic operations, it creates friction for AI agents and humans who want to explore content. Every read requires a CLI invocation:

```bash
exobrain search "quantum computing"
exobrain get 0697a8c2
exobrain list --type note --space work
```

This is fine for targeted queries but painful for exploratory workflows. Claude Code cannot grep across the knowledge base, browse by topic, or read multiple objects without repeated CLI calls. The information-centric vision (ADR-006) promises "universal access" through multiple interfaces, but CLI-only access falls short.

The projection layer bridges this gap by materializing SQLite objects as markdown files that AI agents can browse, grep, and edit directly.

## Decision Drivers

### AI-Native File Access

Claude Code and other AI agents work naturally with files. They can:
- Grep for patterns across directories
- Read multiple files in parallel
- Edit content in place
- Navigate hierarchical structures

Markdown with YAML frontmatter is the lingua franca for AI-readable structured documents.

### Hot Tier Performance

Not all objects need to be projected. A knowledge base with 10,000 objects would create 10,000 files, most rarely accessed. A tiered approach projects only the most relevant objects based on recency and access patterns.

### Bidirectional Sync

Read-only projections would still require CLI for edits. Bidirectional sync allows users and agents to edit projected files directly, with changes flowing back to SQLite via the file watcher.

### Source of Truth Preservation

SQLite remains the canonical source. Projections are derived views that can be regenerated. This maintains the integrity guarantees from ADR-002 while adding file-based access.

## Considered Options

### Option 1: API-Only Access (Rejected)

Add a REST API for reads. Claude Code would use `curl` or a dedicated tool.

**Pros:** Clean interface, no file management
**Cons:** Still requires explicit calls for each read; cannot grep; no browsing

### Option 2: Full Projection (Rejected)

Project all objects to files, always.

**Pros:** Complete file-based access
**Cons:** Doesn't scale; thousands of files create noise; sync complexity

### Option 3: Hot Tier Projection (Selected)

Project top N objects by score, with override controls.

**Pros:** Bounded file count; configurable; respects user preferences
**Cons:** Some objects not immediately accessible as files (use CLI)

## Decision Outcome

**Implement a tiered projection system with bidirectional sync.**

### File Format

Markdown with YAML frontmatter:

```markdown
---
id: 0697a8c2-e669-7208-8000-bbc1be58e794
type: note
space: work/exobrain
title: "Quantum Computing Notes"
summary: "Key concepts from reading"
tags:
  - quantum
  - computing
created: 2026-01-15T10:30:00Z
updated: 2026-01-28T14:22:00Z
projection_override: null
---

The actual content body here. Fully editable.
Supports any markdown, code blocks, etc.
```

### File Naming and Organization

```
$EXOBRAIN_DATA_DIR/projected/
├── CLAUDE.md              # Root index
├── inbox/
│   ├── CLAUDE.md          # Space index
│   └── my-thought-0697a8c2.md
└── work/
    └── exobrain/
        ├── CLAUDE.md
        └── architecture-notes-0697a8d3.md
```

- Directory structure mirrors space hierarchy
- Filenames: `{title-slug}-{id[:12]}.md`
- CLAUDE.md index files auto-generated per directory

### Scoring Algorithm

```python
score = recency_weight * exp(-days_since_update / half_life)
```

Default configuration:
- `EXOBRAIN_PROJECTION_HOT_LIMIT=200`
- `EXOBRAIN_PROJECTION_RECENCY_WEIGHT=0.7`
- `EXOBRAIN_PROJECTION_HALFLIFE_DAYS=14`

Phase 1 uses `updated_at` as proxy for access. Phase 4 (deferred) will add real access tracking.

### Override Controls

Users can force objects in or out of projection:

```bash
exobrain update <id> --always-project  # Include regardless of score
exobrain update <id> --never-project   # Exclude regardless of score
exobrain update <id> --auto-project    # Use score-based (default)
```

### Sync Rules

**Mutable fields (sync to DB on edit):**
- `title`
- `summary`
- `content` (body)
- `tags`
- `projection_override`

**Immutable fields (reject edit, return error):**
- `id` ; permanent identifier
- `space` ; use CLI to move objects
- `created` ; timestamp of creation

**Ignored on sync:**
- `updated` ; set by DB trigger
- `type` ; changing type is complex; use CLI

### Sync Mechanism

Bidirectional sync is triggered explicitly via the `sync` CLI command (not via a file watcher). The workflow is:

1. Edit a projected markdown file (content body, tags, title, summary)
2. Run `exobrain sync` to write changes back to SQLite
3. Run `exobrain project` to regenerate projected files from updated database state

Single-file sync: `exobrain sync /data/projected/inbox/my-note-069xxx.md`
Batch sync: `exobrain sync` (syncs all projected files)

The `sync_from_file()` function in `projection.py` parses YAML frontmatter, validates immutable fields, updates mutable fields via the repository layer, and reconciles tags (adds new, removes deleted).

### CLI Commands

```bash
exobrain project              # Run projection cycle
exobrain project --dry-run    # Preview without writing
exobrain project --cleanup    # Remove stale projections
exobrain sync                 # Sync all projected files back to DB
exobrain sync <file-path>     # Sync a single projected file
exobrain tier status          # Show projection statistics
```

## Consequences

### Positive

- **Reduced friction.** Claude Code can grep, browse, and read files directly without CLI calls.
- **Familiar interface.** Markdown files work with any editor, grep, git, etc.
- **Bounded complexity.** Hot tier limits file count; cold objects still accessible via CLI.
- **Override control.** Users can pin important objects or hide sensitive ones.
- **AI-native.** YAML frontmatter provides structured metadata; body provides content.

### Negative

- **Sync complexity.** Bidirectional sync requires careful validation to prevent corruption.
- **Partial visibility.** Not all objects are projected; some require CLI access.
- **File system dependency.** Projection assumes local filesystem; doesn't work in cloud-only scenarios.
- **Regeneration cost.** Full re-projection reads all candidate objects from SQLite.

### Neutral

- **Explicit sync model.** Sync is triggered by `exobrain sync`, not by a file watcher. Edits to projected files are not automatically synced; the user or agent must explicitly invoke sync before re-projecting. This is deliberate: explicit sync prevents accidental overwrites and makes the data flow visible.
- **Configuration tuning.** Hot tier size and scoring weights may need adjustment per user.

## Agent Rules

1. **SHOULD** prefer reading from `projected/` for exploratory workflows. Grepping and browsing files is faster than repeated CLI calls.

2. **MUST** use CLI for mutations not supported by projection sync. Moving objects between spaces, deleting objects, and changing types require CLI commands.

3. **MUST NOT** edit `id` or `space` fields in projected files. These are immutable; `exobrain sync` will reject the edit and return an error.

4. **SHOULD** run `exobrain project` after bulk imports or significant changes. This ensures projections reflect current state.

5. **MUST** treat projection as a read cache with sync capability, not a replacement for CLI. Complex queries, filtered lists, and system commands require CLI.

6. **SHOULD** use `--always-project` for frequently referenced objects and `--never-project` for sensitive or low-value content.

7. **MUST** remember that projection is hot-tier only. If an object isn't in `projected/`, it still exists in SQLite; use CLI to access it.

## Schema Changes

Migration v3 adds:

```sql
-- Access tracking for future scoring (Phase 4)
CREATE TABLE access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

-- Projection override per object
ALTER TABLE objects ADD COLUMN projection_override TEXT;
-- Values: NULL (use score), 'always', 'never'
```

## References

- ADR-002: `docs/adr/002-sqlite-core-memory-layer.md` (SQLite as source of truth)
- ADR-003: `docs/adr/003-exobrain-cli-architecture.md` (CLI as mutation gateway)
- ADR-004: `docs/adr/004-claude-code-first-ui.md` (AI agent as primary consumer)
- ADR-006: `docs/adr/006-information-centric-computing-vision.md` (Universal access vision)
- Implementation Plan: `docs/active/20260128-exobrain-projection-layer-plan-claude.md`
