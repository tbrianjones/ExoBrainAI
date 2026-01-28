---
status: Done
date: 2026-01-27
completed: 2026-01-28
branch: feature/exobrain-v2-base-memory-layer-sqlite
related-adrs:
  - docs/adr/001-exobrain-v2-graphrag-memory-engine.md (updated; superseded)
  - docs/adr/002-sqlite-core-memory-layer.md (created)
  - docs/adr/003-exobrain-cli-architecture.md (created)
  - docs/adr/004-claude-code-first-ui.md (created)
  - docs/adr/005-api-layer-deferred.md (created)
---

# ExoBrain v2: SQLite Base Memory Layer

## Status: DONE

All phases 0 through 6 implemented and verified. 140 tests passing.

## Summary

Replace ExoBrain's file-based raw+overlay storage with a SQLite database as the single source of truth. Everything is an object; types, spaces, and tags are objects. The CLI is the sole write interface, Claude Code is the first UI, and the system runs in Docker. GraphRAG is retained and reconnected as a later phase.

## Completion Notes

### Phase 0: ADRs First ; DONE

All five ADRs written by parallel agents:

| ADR | File | Status |
|-----|------|--------|
| ADR-002 | `docs/adr/002-sqlite-core-memory-layer.md` | Created |
| ADR-003 | `docs/adr/003-exobrain-cli-architecture.md` | Created |
| ADR-004 | `docs/adr/004-claude-code-first-ui.md` | Created |
| ADR-005 | `docs/adr/005-api-layer-deferred.md` | Created |
| ADR-001 | `docs/adr/001-exobrain-v2-graphrag-memory-engine.md` | Updated to "Superseded (temporarily deactivated)" |

### Phase 1: Foundation ; DONE

Files created:
- `engine/src/core/db.py` ; connection management, WAL mode, migration runner
- `engine/src/core/schema.py` ; migration v1 SQL (all tables, indexes, FTS5, triggers)
- `engine/src/core/models.py` ; Pydantic models (rewritten with v2 models, legacy preserved)
- `engine/src/core/bootstrap.py` ; bootstrap sequence (idempotent, deterministic UUIDs)
- `engine/src/config.py` ; updated with db_path, files_dir properties

Tests: `test_db.py` (12 tests), `test_schema.py` (8 tests), `test_bootstrap.py` (14 tests)

### Phase 2: Repository Layer ; DONE

Files created:
- `engine/src/core/repository.py` ; ObjectRepo, TagRepo, LinkRepo, FileRepo

Tests: `test_repository.py` (55 tests covering CRUD, FTS, constraints, cascades, file sharding)

### Phase 3: CLI Commands ; DONE

Files rewritten:
- `engine/src/cli/main.py` ; full Typer CLI with subcommand groups (tag, link, type, space, file, graphrag)

All commands support `--json`. ID prefix matching on all ID arguments. Pipe-friendly stdin capture.

Tests: `test_cli.py` (38 tests including JSON output consistency)

**Implementation deviation from plan:** All CLI commands implemented in a single `main.py` rather than separate subcommand modules under `engine/src/cli/commands/`. The single file approach is cleaner for this command count.

### Phase 4: Docker + Integration ; DONE

Files modified:
- `docker-compose.yml` ; simplified healthcheck (SQLite), watcher/Gephi moved to graphrag profile
- `engine/Dockerfile` ; installs with optional extras
- `engine/pyproject.toml` ; core deps minimized, graphrag/api/watcher as optional extras

Verified: `docker compose up -d && docker compose exec exobrain exobrain init && docker compose exec exobrain exobrain status`

### Phase 5: Claude Code Skill + Documentation ; DONE

Files rewritten:
- `.claude/skills/exobrain.md` ; full new CLI command reference with JSON schemas
- `CLAUDE.md` ; updated quick reference, CLI tables, repo structure

### Phase 6: GraphRAG Reconnection ; DONE

Files created:
- `engine/src/graphrag/adapter.py` ; `stage_for_graphrag()` reads SQLite objects, produces text files
- `engine/src/graphrag/__init__.py` ; updated with guarded adapter import

CLI commands: `exobrain graphrag stage`, `exobrain graphrag index`, `exobrain graphrag query` (all gated behind optional import)

### Phase 7: v1 Data Migration ; NOT STARTED

Deferred. Old data is not critical.

## Test Suite

140 tests, all passing in 4.28s inside Docker:

| File | Tests | Coverage |
|------|-------|----------|
| `test_bootstrap.py` | 14 | Bootstrap creation, idempotency, integrity, determinism |
| `test_cli.py` | 38 | Init, status, capture, search, list, tags, links, JSON consistency |
| `test_db.py` | 12 | WAL mode, FK, migrations, init, integrity |
| `test_repository.py` | 55 | All repos: CRUD, FTS, constraints, cascades, files |
| `test_schema.py` | 8 | Tables, columns, FTS5, indexes |

**Implementation deviation from plan:** Tests organized as flat files (`test_repository.py`, `test_cli.py`) rather than subdirectories (`test_repository/`, `test_cli/`). Simpler for this test count.

## Bugs Found During Testing

1. **`status` command conn.close() ordering** ; The status command called `conn.close()` before accessing repo methods. Fixed by computing all values before closing.
2. **`from __future__ import annotations` missing** ; `repository.py` in the Docker image was missing this import, causing `list[dict]` type annotations to fail at class scope because `ObjectRepo.list` method shadowed the builtin.

## Open Questions Resolved

| # | Question | Resolution |
|---|----------|------------|
| 1 | Tag promotion to objects | Deferred; tags are strings with optional object_id FK |
| 2 | `primitives/tag` naming | Used `primitives/tag` (singular) |
| 3 | Default space for capture | `primitives` space is the default when `--space` omitted |
| 4 | Stdin support in capture | Yes; reads stdin when no CONTENT argument provided |

## Agent Quick Start

**Read these first:**
- `docs/archive/sqlite-base-memory-layer/20260127-exobrain-v2-sqlite-base-memory-layer-prd-chatgpt.md` ; PRD / conceptual data model
- `docs/adr/002-sqlite-core-memory-layer.md` ; SQLite architecture decision
- This plan document

**Key files to understand current state:**
- `engine/src/core/db.py` ; connection management, WAL mode, migrations
- `engine/src/core/schema.py` ; SQL schema definitions
- `engine/src/core/bootstrap.py` ; type system bootstrap with deterministic UUIDs
- `engine/src/core/repository.py` ; ObjectRepo, TagRepo, LinkRepo, FileRepo
- `engine/src/cli/main.py` ; full Typer CLI
- `engine/src/graphrag/adapter.py` ; SQLite-to-GraphRAG bridge
- `docker-compose.yml` ; container orchestration
- `.claude/skills/exobrain.md` ; Claude Code skill

**Relevant skills:**
- `.claude/skills/exobrain.md` ; rewritten for v2 SQLite CLI

## References

- **PRD:** `docs/archive/sqlite-base-memory-layer/20260127-exobrain-v2-sqlite-base-memory-layer-prd-chatgpt.md`
- **ADR-001 (GraphRAG, superseded):** `docs/adr/001-exobrain-v2-graphrag-memory-engine.md`
- **ADR-002 (SQLite):** `docs/adr/002-sqlite-core-memory-layer.md`
- **ADR-003 (CLI):** `docs/adr/003-exobrain-cli-architecture.md`
- **ADR-004 (Claude Code UI):** `docs/adr/004-claude-code-first-ui.md`
- **ADR-005 (API deferred):** `docs/adr/005-api-layer-deferred.md`
- **Lessons Learned (Fintool):** `docs/resources/exobrain-memory-architecture/lessons-learned-building-an-exobrain-for-fintool.md`
