# ExoBrain Projection Layer

- **Status:** Implemented (Phases 1-3 complete; Phase 4 deferred)
- **Date:** 2026-01-28
- **Completed:** 2026-01-28
- **Branch:** feature/exobrain-v2-projection-layer
- **Related ADRs:**
  - ADR-002: SQLite Core Memory Layer
  - ADR-003: CLI as Sole Write Interface
  - ADR-004: Claude Code as First UI
  - ADR-006: Information-Centric Computing Vision

---

## Summary

A tiered projection system that materializes SQLite objects as human/AI-readable markdown files with YAML frontmatter. The projection layer enables Claude Code to browse, grep, and edit knowledge objects directly on disk while SQLite remains the source of truth. Includes bidirectional sync via file watcher, auto-generated CLAUDE.md context files per directory, and configurable projection settings.

---

## Agent Quick Start

**Files to Load:**
- `engine/src/core/repository.py` ; existing CRUD operations
- `engine/src/core/schema.py` ; migration patterns
- `engine/src/watcher/watcher.py` ; existing watcher implementation
- `engine/src/config.py` ; settings patterns
- `engine/src/cli/main.py` ; CLI command patterns

**ADRs to Read:**
- `docs/adr/002-sqlite-core-memory-layer.md` ; schema design, repository pattern
- `docs/adr/003-exobrain-cli-architecture.md` ; CLI conventions
- `docs/adr/006-information-centric-computing-vision.md` ; why projection matters

**Relevant Skills:**
- `.claude/skills/exobrain.md` ; will need updates for new commands

**Areas to Explore:**
- Current watcher implementation for file change detection patterns
- Bootstrap IDs in `engine/src/core/bootstrap.py` for excluding primitives
- Existing file storage in `FileRepo` for path conventions

---

## Problem Statement

**User Persona:** Developer/knowledge worker using Claude Code as primary interface to ExoBrain

**Pain Point:** Current file storage is opaque; files are sharded by hash (`files/ab/cd/uuid.ext`), making it impossible for Claude Code to grep, browse, or read files directly. Every operation requires CLI commands, adding friction and preventing natural file-based workflows.

**Current State:**
- Claude Code must invoke `exobrain search`, `exobrain get`, `exobrain list` for every query
- No way to browse knowledge by space/topic in a file manager
- Cannot edit object content directly; must use `exobrain update`
- AI agents cannot grep across knowledge base

**Business Impact:** The information-centric vision (ADR-006) requires universal access to data. Claude Code is the first UI, but it's hamstrung by requiring CLI for every read. This creates friction that discourages capture and exploration.

---

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Object discovery | CLI only | File grep works | `rg "keyword" projected/` returns matches |
| Read access | CLI `get` command | Direct file read | Claude Code reads projected/*.md |
| Write access | CLI `update` command | Edit file, auto-sync | Edit projected file, see DB updated |
| New object creation | CLI `capture` only | CLI `capture` (unchanged) | Projection creates file automatically |
| Navigation | Flat ID listing | Space-based directories | `ls projected/work/exobrain/` shows objects |

---

## Feature Overview

The projection layer creates a human/AI-readable view of ExoBrain objects as markdown files on disk.

**What It Does:**
- Projects SQLite objects as markdown files with YAML frontmatter
- Organizes files by space (directories mirror space hierarchy)
- Generates CLAUDE.md index files per directory for context
- Watches projected files for edits and syncs changes back to SQLite
- Supports override flags to always/never project specific objects
- Configurable hot tier size limits projection to most relevant objects

**Core User Flow:**

1. User runs `exobrain project` to generate/refresh projected files
2. Projected files appear in `$EXOBRAIN_DATA_DIR/projected/` organized by space
3. Claude Code (or human) browses directories, greps for content, reads files
4. Claude Code (or human) edits a projected file directly
5. Watcher detects file change, validates edit, syncs to SQLite
6. If validation fails, watcher logs error; file keeps changes but DB unchanged
7. User runs `exobrain project --cleanup` periodically to recalculate scores and deproject stale objects

---

## Scope

### In Scope

- Schema migration: `access_log` table, `projection_override` column on objects
- Projection engine: `engine/src/core/projection.py`
- Projected file format: markdown with full YAML frontmatter
- File naming: `{title-slug}-{id[:12]}.md`
- Directory structure mirroring spaces
- Auto-generated CLAUDE.md per directory with object index
- Configuration via `local.env` (hot tier size, weights, half-life)
- Watcher enhancement to watch `projected/` for file edits
- File-to-DB sync with validation (immutable ID, required fields)
- Error logging to stdout/stderr for invalid edits
- CLI commands: `exobrain project`, `exobrain project --cleanup`, `exobrain tier status`
- Override flags: `--always-project`, `--never-project`, `--auto-project` on `exobrain update`
- Simple optimization: skip regenerating unchanged spaces if easy

### Out of Scope (Do Not Build)

- **Stub projection**: Deferred; add as configurable setting later
- **Versioning**: No history tracking; last write wins
- **Automated cleanup scheduling**: No cron/watcher-triggered cleanup; manual CLI only
- **Index/don't-index metadata**: Mentioned but explicitly deferred
- **Access tracking integration**: Phase 4; initially use created_at/updated_at as proxy
- **File reversion**: Invalid edits keep file changes; only log error

### Dependencies

- Existing SQLite schema and repository layer (ADR-002)
- Existing watcher infrastructure (`engine/src/watcher/`)
- Existing CLI framework (`engine/src/cli/`)

---

## User Stories + Acceptance Criteria

### US1: Project Objects to Files

**As a** Claude Code user
**I want** ExoBrain objects projected as markdown files
**So that** I can browse and grep my knowledge base directly

**Acceptance Criteria:**

```gherkin
Given objects exist in SQLite with type, space, title, content
When I run `exobrain project`
Then markdown files appear in `projected/{space-path}/`
And each file has YAML frontmatter with id, type, space, title, summary, tags, timestamps
And content appears in the file body
And file is named `{title-slug}-{id[:12]}.md`
```

### US2: Browse by Space

**As a** Claude Code user
**I want** projected files organized by space directories
**So that** I can navigate my knowledge hierarchically

**Acceptance Criteria:**

```gherkin
Given objects in spaces "inbox", "work/exobrain", "work/writing"
When I run `exobrain project`
Then directories exist: projected/inbox/, projected/work/exobrain/, projected/work/writing/
And each directory contains its space's objects
And nested spaces create nested directories
```

### US3: CLAUDE.md Context Files

**As a** Claude Code user
**I want** each directory to have a CLAUDE.md index
**So that** Claude Code understands the context of each space

**Acceptance Criteria:**

```gherkin
Given a space "work/exobrain" with 5 objects
When I run `exobrain project`
Then projected/work/exobrain/CLAUDE.md exists
And it contains a table listing all objects (ID, Type, Title, Tags)
And it includes instructions for working in that space
And root projected/CLAUDE.md summarizes all spaces
```

### US4: Edit Projected Files

**As a** Claude Code user
**I want** to edit projected files directly
**So that** I can modify content without using CLI commands

**Acceptance Criteria:**

```gherkin
Given a projected file exists for object abc123
When I edit the content body and save
Then the watcher detects the change
And SQLite object abc123 content is updated
And updated_at timestamp changes
```

### US5: Validation on Sync

**As a** system administrator
**I want** invalid edits to be rejected gracefully
**So that** data integrity is preserved

**Acceptance Criteria:**

```gherkin
Given a projected file for object abc123
When I edit the file to change the id field
Then the watcher logs an error "ID is immutable"
And SQLite object abc123 is NOT updated
And the file keeps the invalid changes (no revert)
```

### US6: Override Projection

**As a** ExoBrain user
**I want** to force certain objects to always/never be projected
**So that** important objects are always accessible and sensitive ones are hidden

**Acceptance Criteria:**

```gherkin
Given object abc123 with low access score
When I run `exobrain update abc123 --always-project`
Then object abc123 has projection_override = 'always'
And subsequent `exobrain project` includes abc123 regardless of score

Given object def456 with high access score
When I run `exobrain update def456 --never-project`
Then object def456 has projection_override = 'never'
And subsequent `exobrain project` excludes def456 regardless of score
```

### US7: Tier Status

**As a** ExoBrain user
**I want** to see projection tier statistics
**So that** I understand what's projected and why

**Acceptance Criteria:**

```gherkin
When I run `exobrain tier status`
Then I see: total objects, projected count, hot tier limit
And I see: top 5 objects by score with their scores
And I see: objects with always_project override
And I see: objects with never_project override
```

---

## Key Decisions

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Source of truth | SQLite | Files-first | Atomic operations, relationships, integrity |
| File format | Markdown + YAML frontmatter | JSON, pure markdown | Battle-tested, grep-friendly, human-editable |
| Content location | Body (not frontmatter) | YAML multiline | Avoids YAML escaping issues with special chars |
| File naming | `{slug}-{id[:12]}.md` | Full UUID, slug only | 12 chars = full timestamp portion of UUID7 |
| Space in files | Immutable | Editable via move | Prevents sync complexity; use CLI to change |
| Invalid edit handling | Log error, keep file | Revert file, conflict file | Simple; user sees their changes, gets feedback |
| Cleanup trigger | Manual CLI only | Automated cron/watcher | Start simple; add automation later |
| Hot tier size | 200 (configurable) | Fixed, unlimited | Reasonable default; tune via local.env |

### Detail: File Format

The projected file format uses standard markdown with YAML frontmatter:

```markdown
---
id: 01942a3b4c5d-7890-abcd-ef01-234567890abc
type: note
space: work/exobrain
title: "My Document Title"
summary: "Short description of the content"
tags:
  - architecture
  - design
created: 2026-01-15T10:30:00Z
updated: 2026-01-28T14:22:00Z
projection_override: null
---

The actual content body here. This is fully editable.
Can contain any markdown, special characters, etc.
```

**Sync Rules:**
- `id`: Immutable; reject edit if changed
- `type`: Mutable; sync to DB
- `space`: Immutable; reject edit if changed (use CLI to move)
- `title`, `summary`, `tags`: Mutable; sync to DB
- `created`: Immutable; ignored on sync
- `updated`: Set by DB trigger; ignored on sync
- `projection_override`: Mutable; sync to DB
- Body content: Mutable; sync to `content` column

### Detail: Scoring Algorithm

```python
score = recency_weight * exp(-days_since_update / half_life) + frequency_weight * access_count_normalized
```

Default configuration:
- `EXOBRAIN_PROJECTION_HOT_LIMIT=200`
- `EXOBRAIN_PROJECTION_RECENCY_WEIGHT=0.7`
- `EXOBRAIN_PROJECTION_FREQUENCY_WEIGHT=0.3`
- `EXOBRAIN_PROJECTION_HALFLIFE_DAYS=14`

**Phase 1**: Use `updated_at` as proxy for access (no access_log yet)
**Phase 4**: Wire up real access tracking

---

## Technical Approach

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Projection System                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CLI Commands                                                   │
│  ├── exobrain project [--cleanup] [--dry-run]                  │
│  ├── exobrain update <id> --always-project|--never-project     │
│  └── exobrain tier status                                       │
│              │                                                  │
│              ▼                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Projection Engine                           │   │
│  │  engine/src/core/projection.py                          │   │
│  │  ├── calculate_scores() -> dict[id, float]              │   │
│  │  ├── get_projection_candidates(limit) -> list[id]       │   │
│  │  ├── project_object(id) -> Path                         │   │
│  │  ├── deproject_object(id) -> bool                       │   │
│  │  ├── generate_claude_md(space_path) -> str              │   │
│  │  ├── sync_from_file(path) -> Result[Object, Error]      │   │
│  │  └── run_projection_cycle(cleanup=False)                │   │
│  └─────────────────────────────────────────────────────────┘   │
│              │                           ▲                      │
│              ▼                           │                      │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │ projected/       │ ◀─────▶ │ Watcher          │             │
│  │ ├── CLAUDE.md    │  watch  │ (file changes)   │             │
│  │ ├── inbox/       │         │ → sync_from_file │             │
│  │ └── work/...     │         └──────────────────┘             │
│  └──────────────────┘                                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### New Files

| File | Purpose |
|------|---------|
| `engine/src/core/projection.py` | Projection engine (scoring, project, deproject, sync) |
| `engine/src/cli/commands/project.py` | CLI commands for projection |

### Modified Files

| File | Changes |
|------|---------|
| `engine/src/core/schema.py` | Migration v3: access_log table, projection_override column |
| `engine/src/config.py` | Projection settings from env vars |
| `engine/src/cli/main.py` | Register project commands, add override flags to update |
| `engine/src/watcher/watcher.py` | Watch projected/ directory, call sync_from_file |
| `.claude/skills/exobrain.md` | Document new commands |

### Schema Migration (v3)

```sql
-- Track access for scoring (Phase 4; create table now, populate later)
CREATE TABLE IF NOT EXISTS access_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    object_id TEXT NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    action TEXT NOT NULL,  -- 'read', 'write', 'search_hit'
    timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_access_log_object_id ON access_log(object_id);
CREATE INDEX IF NOT EXISTS idx_access_log_timestamp ON access_log(timestamp);

-- Projection override flag
ALTER TABLE objects ADD COLUMN projection_override TEXT;
-- Values: NULL (use score), 'always', 'never'
```

### Configuration (local.env)

```bash
# Projection settings
EXOBRAIN_PROJECTION_HOT_LIMIT=200
EXOBRAIN_PROJECTION_RECENCY_WEIGHT=0.7
EXOBRAIN_PROJECTION_FREQUENCY_WEIGHT=0.3
EXOBRAIN_PROJECTION_HALFLIFE_DAYS=14
```

---

## Implementation Phases

### Phase 1: Core Projection Engine

**Goal:** Project objects to files; no sync back yet

**Tasks:**
1. Add schema migration v3 (access_log table, projection_override column)
2. Add projection settings to `config.py`
3. Create `engine/src/core/projection.py`:
   - `calculate_scores()` using updated_at as proxy
   - `get_projection_candidates()` respecting overrides and limit
   - `project_object()` writes markdown with frontmatter
   - `generate_claude_md()` creates directory index
   - `run_projection_cycle()` orchestrates full projection
4. Create `engine/src/cli/commands/project.py`:
   - `exobrain project` command
   - `exobrain project --dry-run` to preview
5. Add `--always-project`, `--never-project`, `--auto-project` to `exobrain update`
6. Test: run project, verify files appear with correct format

**Deliverable:** `exobrain project` creates readable markdown files

### Phase 2: Bidirectional Sync

**Goal:** Edits to projected files sync back to SQLite

**Tasks:**
1. Add `sync_from_file()` to projection.py:
   - Parse YAML frontmatter
   - Validate: ID matches filename, required fields present
   - Update SQLite object
   - Return Result with success or error details
2. Enhance watcher to watch `projected/` directory
3. On file change: call `sync_from_file()`, log errors to stderr
4. Test: edit file, verify DB updates; edit ID, verify error logged

**Deliverable:** File edits flow back to SQLite with validation

### Phase 3: CLI Polish and Status

**Goal:** Full CLI interface for projection management

**Tasks:**
1. Add `exobrain project --cleanup` (recalculates scores, deprojects stale)
2. Add `exobrain tier status` command
3. Update `.claude/skills/exobrain.md` with new commands
4. Add simple optimization: track which spaces changed, skip unchanged on regenerate

**Deliverable:** Complete CLI for projection management

### Phase 4: Access Tracking (Future)

**Goal:** Real access-based scoring

**Tasks:**
1. Log access to access_log on: `exobrain get`, `exobrain search` hits
2. Update `calculate_scores()` to use real access data
3. Consider logging projected file reads (may need inotify access events)

**Deliverable:** Scoring reflects actual usage patterns

---

## Open Questions

| Question | Impact | Notes |
|----------|--------|-------|
| Should file reads be logged for scoring? | Medium | inotify can detect reads but adds complexity |
| How to handle objects with no space? | Low | Default to inbox; shouldn't happen with current CLI |
| Should CLAUDE.md include content snippets? | Low | Could add first 100 chars of each object |
| Max filename length handling? | Low | Truncate slug, keep full ID suffix |

---

## Future Considerations

Items discussed but explicitly deferred:

1. **Stub projection**: Project metadata-only stubs for cold objects; add as configurable setting when hot tier overflows
2. **Versioning**: Track content history; could use git-style content-addressed storage or simple version table
3. **Automated cleanup**: Cron or watcher-triggered dehydration; currently manual CLI only
4. **Index/don't-index flag**: Control whether object content is indexed by GraphRAG
5. **Space change via file move**: Detect directory moves and update object space
6. **Conflict files**: Instead of just logging errors, create `.conflict` files for review

---

## Verification

### Test Commands

```bash
# After Phase 1
docker compose exec exobrain exobrain project --dry-run
docker compose exec exobrain exobrain project
ls -la $EXOBRAIN_DATA_DIR/projected/
cat $EXOBRAIN_DATA_DIR/projected/CLAUDE.md
cat $EXOBRAIN_DATA_DIR/projected/inbox/*.md

# After Phase 2
# Edit a projected file externally, then check:
docker compose exec exobrain exobrain get <id>
# Verify content updated

# After Phase 3
docker compose exec exobrain exobrain tier status
docker compose exec exobrain exobrain project --cleanup
```

### Manual Checks

- [ ] Projected files have valid YAML frontmatter (parseable)
- [ ] File IDs match the trailing 12 chars in filename
- [ ] Directories mirror space hierarchy
- [ ] CLAUDE.md files list all objects in directory
- [ ] Editing content body updates DB
- [ ] Editing ID field logs error, keeps file, doesn't update DB
- [ ] `--always-project` objects appear even with low score
- [ ] `--never-project` objects don't appear even with high score
- [ ] `tier status` shows accurate counts

### Success Criteria

- [ ] `rg "keyword" projected/` returns relevant objects
- [ ] Claude Code can read projected files without CLI
- [ ] Claude Code can edit projected files and see changes in `exobrain get`
- [ ] New captures via CLI automatically appear in projection on next `exobrain project`

---

## References

- **ADR-002:** `docs/adr/002-sqlite-core-memory-layer.md`
- **ADR-003:** `docs/adr/003-exobrain-cli-architecture.md`
- **ADR-006:** `docs/adr/006-information-centric-computing-vision.md`
- **Research:** Lessons from FinTool article on file-centric AI agent patterns
- **Research:** Tiered storage patterns, hot/cold data management
- **Suggest ADR:** Consider ADR-007 for projection layer architecture decisions
