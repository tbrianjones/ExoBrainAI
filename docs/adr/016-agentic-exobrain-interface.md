# ADR-016: Agentic ExoBrain Interface

- **Status:** Accepted
- **Date:** 2026-02-11
- **Impact:** High
- **Tags:** agentic, interface, cli, integration
- **Related ADRs:** ADR-002 (SQLite Core Memory Layer), ADR-003 (CLI as Sole Write Interface), ADR-004 (Claude Code as First UI), ADR-007 (Projection Layer Architecture), ADR-011 (Primitive Semantics)

## Context and Problem Statement

ExoBrain's CLI (ADR-003) is the sole write interface, and Claude Code is the primary UI (ADR-004). The current `.claude/skills/exobrain.md` skill (358 lines) contains a detailed CLI reference, JSON schemas, and integration patterns. This content overlaps heavily with the root CLAUDE.md. As both files evolved independently, they drifted: the skill documents schemas and patterns that CLAUDE.md omits, while CLAUDE.md captures architectural context the skill lacks. Neither is authoritative on its own.

This ADR captures the canonical specification for how AI agents interact with ExoBrain, serving as the single source of truth. The exobrain.md skill will be replaced by a generated skill derived from this ADR.

The central question: what is the definitive interface contract between AI agents and ExoBrain?

## Decision Drivers

- AI agents need a reliable, well-documented interface to ExoBrain
- The current exobrain.md skill duplicates content from CLAUDE.md, with drift between the two
- JSON output schemas must be documented in one place
- Integration patterns (hybrid read/write, ID prefix matching) need a canonical home
- A generated skill derived from a single ADR eliminates duplication and keeps documentation in sync

## Decision

### Invocation Pattern

All CLI commands run via Docker:

```bash
docker compose exec exobrain exobrain <command>
```

Use the `-T` flag when piping stdin content to avoid TTY allocation issues:

```bash
echo "content" | docker compose exec -T exobrain exobrain capture --title "Title" --type note --json
```

All commands support `--json` for structured output. Agents MUST use `--json` when parsing output programmatically.

### JSON Output Schemas

#### Capture / Get Response

```json
{
  "id": "UUID",
  "type_id": "UUID",
  "space_id": "UUID",
  "title": "string",
  "summary": "string|null",
  "content": "string",
  "type_name": "string",
  "space_name": "string",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

#### Search / List Response

Array of objects with `id`, `type_name`, `space_name`, `title`, `summary`, `created_at`.

```json
[
  {
    "id": "UUID",
    "type_name": "string",
    "space_name": "string",
    "title": "string",
    "summary": "string|null",
    "created_at": "ISO8601"
  }
]
```

#### Status Response

```json
{
  "version": "string",
  "data_dir": "string",
  "db_path": "string",
  "db_size_bytes": 0,
  "object_count": 0,
  "type_counts": {"TypeName": 0},
  "tag_count": 0,
  "link_count": 0,
  "file_count": 0,
  "integrity": "ok"
}
```

#### Tag List Response

Uses `tag_text` key (not `tag`):

```json
[
  {"tag_text": "architecture", "count": 5},
  {"tag_text": "design", "count": 3}
]
```

Note: `get --json` returns tags as a plain list of strings (not objects).

### ID Prefix Matching

All ID arguments accept full UUIDs or prefixes (minimum 8 characters):

```bash
exobrain get 019477a3    # matches 019477a3-b1c2-7def-8901-234567890abc
```

Bootstrap IDs are deterministic UUIDs starting with `00000000-0000-7000-8000-*`. User object IDs are UUIDv7 starting with `069...`.

### The Hybrid Pattern

Commands and agents use a hybrid approach for reading and writing ExoBrain data.

**Read path**: Run `exobrain project` to refresh projections, then read projected markdown files from `$EXOBRAIN_DATA_DIR/projected/`. Each file has YAML frontmatter (id, type, space, title, summary, tags, dates) and a content body. This is more efficient than issuing individual `get` commands for bulk reads.

**Write path**: Use CLI commands (`capture`, `update`, `tag add`, `link create`, etc.) for all mutations. The CLI handles validation, ID generation, versioning, and audit logging.

**Edit path**: Edit projected files directly; the file watcher (2-second debounce) auto-syncs changes back to SQLite. Immutable fields (`id`, `space`) are protected; sync rejects changes to these.

### Data Location Structure

```
$EXOBRAIN_DATA_DIR/
├── exobrain.db        # SQLite database (source of truth)
├── files/             # Sharded file attachments (two-level shard dirs)
├── projected/         # AI-readable markdown projections
│   ├── CLAUDE.md      # Root index
│   ├── inbox/         # Default space
│   └── {spaces}/      # User spaces (e.g., ideas/my-project/)
└── raw/               # Legacy v1 raw documents
```

Only `$EXOBRAIN_DATA_DIR` is required for full data recovery. Container volumes hold derived data (staged/, graphrag/) that can be regenerated.

### Integration Workflow

The standard agent workflow for interacting with ExoBrain:

1. **Capture** raw content: `exobrain capture "..." --type note --tag ideation --json`
2. **Search** for related content: `exobrain search "topic" --json`
3. **Link** related objects: `exobrain link create <new-id> <related-id> "references" --json`
4. **Tag** for organization: `exobrain tag add <id> "project-x" --json`
5. **Propose** metadata: `exobrain update <id> --title "Better Title" --summary "..." --json`

When creating content in idea spaces (views, documents, responses), always link provenance using `derived-from` for transcripts and concepts the content was generated from, and `references` for specific objects it cites.

### Bootstrap Types

Always available: Document, Note, Transcript, URL, Concept, Event, Person, Project. Create custom types with `type create`.

### Bootstrap Spaces

System spaces: `primitives`, `primitives/type`, `primitives/space`, `primitives/tag`. User default: `inbox`. Create user spaces with `space create "work/project-name"` (auto-creates parents).

## Alternatives Considered

### Direct Database Access from Agents

- **Pro:** Eliminates Docker exec latency; enables complex queries
- **Con:** Bypasses validation, ID generation, versioning triggers, and business logic. Creates a second write path that could produce inconsistent state.
- **Verdict:** Rejected. The CLI encapsulates all write logic and must remain the single write authority per ADR-003.

### HTTP API as Primary Agent Interface

- **Pro:** Standard REST semantics; language-agnostic; could serve remote agents
- **Con:** Unnecessary overhead for a single-user local system. Adds a network hop and an HTTP server dependency for operations that are fundamentally local subprocess calls.
- **Verdict:** Rejected. CLI via Docker exec is simpler, inspectable, and composable. The API (ADR-005) exists for the web UI, not as an agent interface.

### CLI via Docker Exec (Chosen)

- **Pro:** Single write path; inspectable; composable; `--json` output for structured parsing; consistent with ADR-003
- **Con:** 200-500ms latency per call due to Docker exec overhead
- **Verdict:** Accepted. The latency is acceptable for an interactive knowledge system; correctness and simplicity outweigh raw speed.

## Consequences

### Positive

- Single source of truth for the agent-ExoBrain interface specification
- Replaces duplicated content between CLAUDE.md and `.claude/skills/exobrain.md`
- Generated skill stays in sync with this ADR automatically
- JSON schemas are documented once, reducing inconsistency risk
- Integration patterns (hybrid read/write, ID prefix matching) have a canonical home

### Negative

- Docker exec latency (~200-500ms per call) is inherent to the chosen invocation pattern
- This ADR must be updated when CLI commands change; stale documentation would mislead agents
- The skill generation step adds a maintenance dependency on this ADR

### Neutral

- The existing `.claude/skills/exobrain.md` can be removed once the generated skill is in place
- Future CLI changes should update this ADR as part of the same changeset

## Generated Skills

### `exobrain-interface`

Reference skill for AI agent interaction with ExoBrain. Use when user mentions exobrain, capture thought, search memory, tag object, link objects, attach file, list objects, project, sync, or graphrag. Replaces the hand-maintained `.claude/skills/exobrain.md`.

## Agent Rules

1. MUST invoke all ExoBrain CLI commands via Docker: `docker compose exec exobrain exobrain <command>`
2. MUST use `--json` flag when parsing output programmatically
3. MUST use `-T` flag on `docker compose exec` when piping stdin content
4. MUST support ID prefix matching with minimum 8 characters
5. MUST use the hybrid pattern: projected files for reads, CLI for writes
6. MUST NOT access the SQLite database or `$EXOBRAIN_DATA_DIR` files directly for write operations
7. SHOULD propose titles, summaries, and tags during capture workflows
8. SHOULD use `exobrain project` to refresh projections before reading projected files
9. MUST handle CLI errors gracefully with user-visible remediation suggestions
10. MUST link provenance when creating content in idea spaces (`derived-from`, `references`)
11. MUST ensure `$EXOBRAIN_DATA_DIR` is the only directory required for full data recovery
