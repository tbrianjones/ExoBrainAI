# ADR 003: ExoBrain CLI as Sole Write Interface

- **Status:** Accepted
- **Date:** 2026-01-27
- **Tags:** architecture, cli, interface
- **Impact:** High

## Context

ExoBrain v2 needs a primary interface for all write operations. The existing v1 CLI is Typer-based and wraps file operations (creating raw markdown, appending overlay JSONL). The v2 system introduces SQLite as the base memory layer, requiring structured CRUD over typed objects, tags, links, spaces, and file attachments.

The central question: should writes go through the CLI, the API, or direct DB access?

Claude Code is the primary consumer of ExoBrain. It invokes commands via the exobrain skill, which shells out to Docker-wrapped CLI calls. The interface must support programmatic output (JSON), prefix-based ID resolution, and stdin piping for content capture.

## Decision Drivers

1. **Inspectability**: Every write operation is a visible command that can be logged, replayed, and audited. No silent mutations.
2. **Composability**: Pipe-friendly, scriptable interface. Capture from stdin, chain with jq, integrate into shell workflows.
3. **Claude Code integration**: The exobrain skill invokes CLI commands with `--json` output. This is the natural integration point; no HTTP client needed.
4. **Single write path**: All mutations flow through one code path. This prevents data inconsistency that arises when multiple interfaces can write to the same store.
5. **Docker-wrapped execution**: All commands run inside the container via `docker compose exec exobrain exobrain <command>`. The container owns the database file; no host process writes directly.

## Considered Options

### 1. API-first (FastAPI routes as primary write interface)

The existing v1 codebase includes partial FastAPI routes. This option would make HTTP the canonical write path, with the CLI as a thin client.

Rejected: The API is half-built and adds HTTP overhead for what is fundamentally a local, single-user system. Serialization round-trips through JSON over HTTP are unnecessary when the CLI can call repository functions directly. A web UI may eventually need an API, but that is a future concern.

### 2. Direct DB access from Claude Code

Claude Code could write to SQLite directly via the skill, bypassing both CLI and API.

Rejected: This breaks encapsulation entirely. Business logic (validation, ID generation, timestamp management, cascade deletes) would need to be reimplemented in the skill. Every write would be invisible to logging. Schema changes would break the skill silently. Auditing becomes impossible.

### 3. CLI as sole write interface (chosen)

All writes go through the Typer CLI. The API becomes read-only (queries, status, health checks). Claude Code invokes CLI commands via Docker exec with `--json` for structured output.

## Decision Outcome

Chosen option: **Typer-based CLI as the sole write interface for ExoBrain v2**

All mutation operations are CLI commands. Every command supports `--json` output for programmatic consumption. ID arguments support prefix matching (minimum 8 characters of a UUID). All production invocations are Docker-wrapped: `docker compose exec exobrain exobrain <command>`.

### Command Groups

| Group | Commands | Purpose |
|-------|----------|---------|
| **System** | `init`, `status`, `doctor`, `version` | Setup and diagnostics |
| **Objects** | `capture`, `get`, `list`, `update`, `delete`, `search` | Core CRUD over documents |
| **Tags** | `tag add`, `tag remove`, `tag list` | Tag management |
| **Links** | `link create`, `link list`, `link remove` | Typed relationships between objects |
| **Types** | `type list`, `type create` | Object type definitions |
| **Spaces** | `space list`, `space create` | Namespace management |
| **Files** | `file attach`, `file detach`, `file path` | File attachment operations |
| **Projection** | `project`, `project --cleanup`, `project --dry-run`, `sync`, `tier status` | Project objects to markdown files, sync edits back (ADR-007) |

### Output Modes

All commands support two output modes:

- **Human mode** (default): Formatted text for terminal use
- **JSON mode** (`--json`): Structured JSON for programmatic consumption by Claude Code and scripts

### ID Resolution

Commands that accept an ID argument support prefix matching. The first 8 characters of a UUID are sufficient to uniquely identify an object in practice. If a prefix matches multiple objects, the command returns an error listing the ambiguous matches.

### Content Input

Commands that accept content (e.g., `capture`) read from the positional argument first, then fall back to stdin if no argument is provided. This enables both interactive use and piping:

```bash
# Direct argument
docker compose exec exobrain exobrain capture "My thought"

# Piped from stdin
echo "My thought" | docker compose exec -T exobrain exobrain capture
```

### Validated Design Patterns

**Repository layer separation:** The four repo classes (`ObjectRepo`, `TagRepo`, `LinkRepo`, `FileRepo`) each own their SQL and expose clean Python methods. The CLI layer delegates to these repos without embedding SQL. This separation means schema changes only affect repository internals.

**`--json` flag on every command:** Consistent JSON output enables scripting and composition. The `_output()` helper provides a uniform formatting contract. This is well-suited for a CLI that is called by other tools (Claude Code commands, agents).

**Connection lifecycle via context manager:** All CLI commands use a `_db_session()` context manager that guarantees the SQLite connection is closed even if the command raises an exception. This prevents leaked connections holding WAL locks.

**Atomic multi-step operations:** Commands that perform multiple writes (e.g., `capture` with tags and file attachment) wrap the entire sequence in a transaction. On failure, the partially created object is rolled back to prevent orphaned data.

## Consequences

### Positive

- **Every write is auditable**: CLI commands appear in shell history, can be logged by the watcher, and can be replayed for debugging
- **Composable by design**: Standard Unix patterns work naturally; pipe content in, pipe JSON out, chain with jq
- **Claude Code integration is natural**: The exobrain skill invokes CLI commands with `--json` and parses structured output; no HTTP client, no connection management
- **Single source of truth for business logic**: Validation, ID generation, and cascade operations live in one place; the repository layer called by CLI handlers
- **Testable in isolation**: CLI commands can be tested without spinning up an HTTP server
- **Scriptable migrations**: Bulk operations are just shell loops over CLI commands

### Negative

- **No real-time API for future web UI**: A web interface would need an API layer added later. This is deliberately deferred; the current user is Claude Code, not a browser.
- **Docker exec adds latency**: Each command invocation pays the cost of `docker compose exec`, which adds roughly 200-500ms overhead. For interactive use this is acceptable; for bulk operations it accumulates.
- **No streaming output**: CLI commands return complete results. Long-running operations (like search over large datasets) cannot stream partial results to the caller.

## Agent Rules

1. **MUST** use `--json` flag for all programmatic output. Human-formatted output is for terminal use only; the exobrain skill must always pass `--json`.

2. **MUST** support ID prefix matching with a minimum of 8 characters. Commands that accept an ID argument must resolve prefixes and error clearly on ambiguous matches.

3. **MUST** wrap all commands in Docker exec for production use: `docker compose exec exobrain exobrain <command>`. Direct invocation outside the container is for development only.

4. **MUST** use Typer as the CLI framework. All commands are Typer commands with type-annotated parameters and auto-generated help text.

5. **SHOULD** accept stdin for content when the positional argument is omitted. Use `-T` flag on `docker compose exec` when piping stdin.

6. **MUST** return exit code 0 on success and exit code 1 on errors. The `--json` output on error must include an `error` field with a human-readable message.

7. **NEVER** write to the database outside the repository layer. CLI handlers call repository functions; they do not execute raw SQL.

8. **MUST** use the `_db_session()` context manager for all database access in CLI commands. This guarantees connection cleanup even on exceptions, preventing leaked WAL locks.

9. **SHOULD** validate input through Pydantic models where applicable. Not all CLI parameters require Pydantic validation; Typer handles basic type coercion and validation for command arguments. Pydantic models are used for structured data like JSON output schemas.

10. **SHOULD** include `id`, `created_at`, and `updated_at` fields in all `--json` output for created or modified objects.

11. **MUST** support `--help` on every command and subcommand. Typer generates this automatically from docstrings and type annotations.

12. **SHOULD** use consistent naming conventions: singular nouns for subcommand groups (`tag`, `link`, `type`, `space`, `file`), action verbs for operations (`add`, `remove`, `list`, `create`).

13. **MUST** use repository methods for all database lookups in CLI commands, including type/space resolution. Never execute raw SQL in CLI handlers. Use `ObjectRepo.resolve_type_by_name()`, `ObjectRepo.resolve_space_by_name()`, and `ObjectRepo.resolve_prefix_matches()` for name-to-ID resolution.

## Future Work

**JSON error output.** Rule 6 specifies that `--json` error output must include an `error` field. Currently, errors are written to stderr as plain text regardless of the `--json` flag. A future pass should wrap error paths so that `--json` produces `{"error": "message"}` on stderr with exit code 1.

**GraphRAG adapter repository access.** The `stage_for_graphrag` adapter in `engine/src/graphrag/adapter.py` reads objects directly from the connection rather than going through `ObjectRepo`. This predates the v2 repository layer. When GraphRAG integration is next updated, the adapter should use repository methods for consistency.

**Structured error types.** CLI commands currently raise `typer.Exit(1)` with ad-hoc error messages. A future improvement could define an `ExoError` hierarchy so that the exobrain skill can programmatically distinguish "not found" from "ambiguous prefix" from "FK constraint violation."

**Projection and sync commands.** The `project`, `sync`, and `tier status` commands were added as part of the projection layer (ADR-007). The `sync` command exposes bidirectional sync from projected files back to SQLite, either for a single file or all projected files at once. See ADR-007 for details.

**Link vocabulary.** Link relationships are unconstrained free text. Any string can be a relationship label. This provides flexibility but makes it harder to query or aggregate by relationship type. A future decision: should relationships be constrained to a vocabulary (like types are), or should the free-text approach continue? Document the choice when it matters.

## References

- Base Memory Layer Plan: `docs/archive/sqlite-base-memory-layer/20260127-exobrain-v2-sqlite-base-memory-layer-dev-plan-claude.md`
- ExoBrain v2 Architecture: `docs/adr/001-exobrain-v2-graphrag-memory-engine.md`
- Typer: https://typer.tiangolo.com/
- CLI source: `engine/src/cli/`
