---
id: 001
title: ExoBrain Workspace Structure and Schema
status: Accepted
date: 2026-01-17
tags: [architecture, data-model, exobrain, workspace, schema]
impact: high
supersedes: []
---

# Context

The current claude_writer system stores ideas in a filesystem structure (`ideas/NNNN-name/`) with prose README.md files and no machine-readable metadata. This documents a planned decision not yet fully implemented.

The current approach fails in several ways:

- No unique identifiers for documents or spaces (sequential numbers can collide across collaborators)
- No schema validation (agents can create arbitrary structures)
- No separation of application code from user content (both live in same repo)
- No safe evolution path (no versioning or migrations)
- Metadata is prose only, not machine-processable

# Decision Drivers

- **Trustworthiness**: Structure must be reliable enough to build tooling on
- **Collaboration**: Multiple users must be able to work without conflicts
- **Human readability**: Pre-UI, humans navigate via filesystem
- **Machine processability**: Agents and tools need consistent metadata
- **Evolvability**: Schema must be able to change over time safely
- **Simplicity**: Avoid over-engineering; git as primary infrastructure

# Decision

Implement a two-repository architecture with enforced schema validation, UUIDv7 identities, and a CLI that gates all document operations.

## Architecture

Two separate repositories:

- **App repo** (public): Python CLI, agents, commands, master type definitions, schema definitions, validation and migration tools
- **Workspace repo** (private, pure data): `workspace.yml`, `types.yml`, space folders with content, no application code

## Identity System

**Space folders** use 8-character UUIDv7 prefix plus slug: `{8-char-uuid}-{slug}/`

- Example: `01957a3b-economics-of-claude-code/`
- Full UUID stored in space's README.md frontmatter
- Slug is human context; can change without breaking identity

**Documents** use human-readable filenames with full UUIDv7 in frontmatter:

- Filenames like `2026-01-17-exploration.md` or `brief-token-economics.md`
- UUID is permanent identity; filename can change

## Frontmatter Schema

**Required fields:**

```yaml
---
id: 01958c3d4e5f6a7b9c0d1e2f3a4b5c6d    # Full UUIDv7
type: brief                               # Enumerated, validated
space: 01957a3b                           # Space UUID (8-char)
created: 2026-01-17T14:30:00Z            # ISO 8601
created_by: "Human Name"                  # From app config
agent: claude-opus-4-5-20251101           # Model that created this
schema_version: 1                         # For migrations
---
```

**Optional fields:**

- `title`: Display name
- `subtitle`: Secondary title
- `brief`: Short description
- `status`: draft | published | in_review | archived
- `updated`: ISO 8601 datetime of last modification
- `updated_by`: Human who last modified
- `updated_agent`: Agent that last modified
- `derived_from`: List of source document UUIDs
- `tags`: General classification
- `hashtags`: Platform-specific tags

## Type System

**Terminal types** (final outputs, `derived_from` required):

- brief, blog-post, poem, tweet, etc.
- Should not be used as source material (information already exists elsewhere)

**Non-terminal types** (source material, `derived_from` optional):

- transcript, character, setting, summary, etc.
- Can be used to derive other documents

**Configuration:**

- App has master types with associated tooling
- Workspace `types.yml` defines allowed types (subset of master + custom)
- Custom types work but lack app tooling

## Folder Structure

**System ignores folder structure within spaces.** Validates by document `type` in frontmatter, not folder location. Humans can organize subfolders however they want.

Only `README.md` at space root is required.

Example:

```
01957a3b-my-book/
├── README.md                    # Required, space metadata
├── chapters/                    # Human organization
│   ├── chapter-1.md            # type: chapter in frontmatter
│   └── chapter-2.md
├── characters/
│   └── protagonist.md          # type: character
└── outputs/
    └── synopsis.md             # type: brief (terminal)
```

## Software Layer

**Python CLI** (`exobrain`) gates all document operations:

- `exobrain doc create/update/delete`
- `exobrain space create`
- `exobrain validate`
- `exobrain migrate`
- `exobrain sync` (commit + push)
- `exobrain status`

Agents call via Bash. Future: MCP server wrapper for native Claude integration.

## Links and Provenance

Simple `derived_from` field in frontmatter:

```yaml
derived_from:
  - 01958a2b3c4d5e6f7a8b9c0d1e2f3a4b  # transcript
  - 01958b3c4d5e6f7a8b9c0d1e2f3a4b5c  # another source
```

- Required for terminal types
- Optional for non-terminal types
- More sophisticated graph model deferred to future

## Migrations

**Forward-only** (git is rollback mechanism):

1. User runs `exobrain migrate`
2. System checks for uncommitted/unpushed changes; prompts to commit+push
3. Creates backup branch (`pre-migration-v1-backup`)
4. Runs migration scripts sequentially
5. Validates all documents
6. Prompts user to confirm
7. Optionally commits changes

**Schema versioning:**

- `workspace.yml` has `schema_version`
- App checks on startup; blocks operations on mismatch
- Migration scripts in `migrations/` directory

## Sync and Safety

- Prompt for commits after significant operations
- Block operations when workspace schema doesn't match app
- Pre-migration checklist: uncommitted changes, unpushed commits
- Create backup branch before destructive operations
- Never lose uncommitted/unpushed work

## Configuration Split

**App repo contains:**

- User identity in `.env` (gitignored)
- Master type definitions with tooling
- Schema definitions (JSON Schema or Pydantic)
- Validation and migration tools

**Workspace repo contains:**

- `workspace.yml`: owner info, `schema_version`, workspace settings
- `types.yml`: allowed types for this workspace, custom types
- Space folders with content

# Alternatives Considered

## UUID in Filenames

- **Considered:** `01958c3d-brief-economics.md`
- **Decided:** Human-readable filenames, UUID in frontmatter only
- **Rationale:** Better readability pre-UI; validation ensures IDs exist

## Folder-Based Type Validation

- **Considered:** `transcripts/` folder means transcript type
- **Decided:** Type in frontmatter, folders ignored
- **Rationale:** More flexible; humans organize freely; type is explicit

## Full UUID in Folder Names

- **Considered:** Full 32-char UUID in folder names
- **Decided:** 8-char prefix + slug
- **Rationale:** Collision risk negligible at expected scale (<1000 spaces); much more readable

## Single Repository

- **Considered:** Single repo with `.gitignore` for content
- **Decided:** Separate app and workspace repos
- **Rationale:** Clean separation; workspace is pure data; can share app publicly

## Separate Link Store

- **Considered:** `links.jsonl` as separate entity store
- **Decided:** `derived_from` in document frontmatter
- **Rationale:** Simpler; captures primary use case; graph model can come later

# Consequences

## Positive

- Structure becomes trustworthy enough to build tooling on
- Multiple collaborators can work without ID collisions
- Schema can evolve safely through versioned migrations
- Clear separation of app code (shareable) and content (private)
- Human-navigable filesystem pre-UI

## Negative

- Validation is mandatory (computational overhead on every operation)
- All document operations must go through CLI (no direct file editing for creation)
- Agents cannot write files directly anymore
- Migration scripts required for schema changes
- 8-character prefix has theoretical collision risk (~1 in 4 billion)

## Neutral

- Git becomes critical infrastructure (already was)
- More ceremony for simple operations (but more safety)

# Future Considerations

Not in scope for this ADR, but noted for future:

- **Templates system**: Frameworks for generating content types
- **Integrations model**: Site publishing, Twitter, etc. as workspace readers/writers
- **Space types**: Constrain valid document types per space (book vs concept)
- **Full graph model**: Link entities with type, direction, status
- **MCP server**: Native Claude tool integration

# Pending Items

| Item | Status | Notes |
|------|--------|-------|
| Python CLI implementation | Pending | Core doc/space/validate commands |
| Frontmatter schema definition | Pending | JSON Schema or Pydantic models |
| Migration framework | Pending | Forward-only with backup branches |
| Workspace spec document | Pending | Folder layout and rules |
| Types registry | Pending | Master types with tooling hooks |
| Workspace separation | Pending | Split current repo into app + workspace |

# Agent Rules

- RULE: All document creation MUST go through `exobrain doc create`; never write markdown files directly
- RULE: Space folders MUST use format `{8-char-uuid}-{slug}/`; example: `01957a3b-my-idea/`
- RULE: Terminal types (brief, blog-post, poem, tweet) MUST have `derived_from` field listing source document UUIDs
- RULE: Frontmatter MUST include required fields: `id`, `type`, `space`, `created`, `created_by`, `agent`, `schema_version`
- RULE: Document `type` field MUST be validated against workspace `types.yml`; reject unknown types
- RULE: Never store application code in workspace repo; workspace contains only data
- RULE: User identity (`created_by`) MUST come from app `.env`, never hardcoded in agents
- RULE: Before migrations, verify no uncommitted/unpushed changes exist; create backup branch before running
