# ADR-008: Agentic Testing Strategy

- **Status:** Accepted
- **Date:** 2026-02-06
- **Impact:** Medium
- **Related ADRs:** ADR-003 (CLI Architecture), ADR-004 (Claude Code First UI), ADR-007 (Projection Layer)

## Context and Problem Statement

ExoBrain is a personal knowledge system that will hold irreplaceable data. Before committing real ideas and transcripts, the user needs confidence that: (1) data persists correctly across operations, (2) the CLI doesn't crash on standard workflows, (3) migrations upgrade existing databases safely, and (4) the full capture-to-projection-to-sync cycle works end to end.

Traditional unit tests verify code correctness but don't exercise the system the way a person uses it. Shell scripts can automate CLI calls but are brittle and don't test the Claude Code interface that is the actual UI (per ADR-004). The question is: what testing strategy gives confidence that ExoBrain is trustworthy for personal knowledge?

## Decision Drivers

- Personal knowledge must survive years of development; trust requires visible proof
- The primary UI is Claude Code invoking CLI commands; tests should exercise this exact path
- The user wants to *watch* tests run and feel like a person is doing it
- Tests must be repeatable without leaving artifacts in the database
- Unit tests are necessary but insufficient; they don't catch integration failures (e.g., missing migrations on existing databases)
- The system has multiple layers (SQLite, CLI, projection, file sync) that must work together

## Decision

Adopt a three-tier testing strategy:

### Tier 1: Unit Tests (pytest, in-container)
- **241+ tests** in `engine/tests/`
- Cover: repository CRUD, schema validation, migration execution, bootstrap idempotency, projection cycle, FTS5 integrity
- Run via: `docker compose exec exobrain python -m pytest tests/ -v`
- Use in-memory SQLite with fresh schema per test (via `conftest.py` fixtures)
- Run on every code change; must all pass before commit

### Tier 2: Agentic Integration Test (`/test-system`)
- A Claude Code command that simulates a real user session across 8 phases
- Exercises: health check, capture (5 types), search, links, projection, bidirectional sync, update lifecycle, integrity verification
- Tags all test objects with `_system-test` for isolation and cleanup
- Reports results visually as it runs; the user watches it happen
- Asks before cleanup so artifacts can be inspected
- Run after significant changes or before committing personal data

### Tier 3: Test Fixtures (`engine/tests/fixtures/`)
- Sample transcript and blog post content for realistic testing
- Used by both `/test-system` (agentic) and potentially future pytest integration tests
- Content is domain-relevant (about knowledge systems) so projected files look realistic

### Test Isolation Pattern

The `/test-system` command uses **structural isolation**: a dedicated `exobrain-test` Docker Compose service (under the `test` profile) that mounts a separate, disposable data directory (`./test-data/`) instead of the production Dropbox-synced directory. The service name itself is the safety mechanism; there is no mode flag that could be accidentally misconfigured. The test container runs on port 8421 alongside the production container on 8420.

Within the test container, all agentic test objects are also tagged with `_system-test`. This allows:
- Filtering: `exobrain list --tag _system-test` shows only test artifacts
- Cleanup: delete all tagged objects after verification
- Coexistence: tests run alongside real data without collision
- Custom test spaces (e.g., `testing/integration`) are also cleaned up

## Alternatives Considered

### Shell Script Integration Tests
- **Pro:** Automatable, no Claude Code dependency, could run in CI
- **Con:** Brittle string parsing, doesn't exercise the actual UI path, can't adapt to failures
- **Verdict:** Good complement for CI but not sufficient alone

### pytest Integration Tests Inside Docker
- **Pro:** Same test framework as unit tests, assertions, fixtures
- **Con:** Doesn't test the Claude Code invocation path, can't demonstrate system to user, harder to make watchable
- **Verdict:** Unit tests already cover the repository/projection layer; integration gap is at the CLI+projection+sync level

### Full Agentic Only (No Unit Tests)
- **Pro:** Simpler test surface
- **Con:** Slow, expensive (requires Claude API call), can't run in CI, too coarse for regression catching
- **Verdict:** Unit tests are essential for fast feedback; agentic tests are for confidence

## Consequences

### Positive
- User can watch the system being exercised and build trust
- Tests exercise the exact same path a real user follows
- Test isolation via tagging means tests and real data coexist safely
- Three tiers catch different classes of bugs: logic errors (unit), integration failures (agentic), and workflow regressions (agentic)

### Negative
- Agentic tests consume Claude API tokens
- Agentic tests take ~2 minutes vs seconds for unit tests
- No automated CI for the agentic tier (requires Claude Code)
- Test fixtures must be maintained as the system evolves

### Neutral
- Shell script CI tests could be added later as a Tier 1.5 without conflicting with this strategy

## Implementation

### Files
- `.claude/commands/test-system.md` ; the agentic integration test command (8 phases)
- `engine/tests/fixtures/sample-transcript.md` ; realistic conversation fixture
- `engine/tests/fixtures/sample-blog-post.md` ; realistic content fixture
- `engine/tests/` ; pytest unit tests (existing)

### Running Tests
```bash
# Tier 1: Unit tests (fast, every change)
docker compose exec exobrain python -m pytest tests/ -v

# Tier 2: Agentic integration (watchable, after significant changes)
# Uses isolated exobrain-test container (docker compose --profile test)
# In Claude Code:
/test-system
```

## Agent Rules

- MUST run unit tests (`pytest`) before committing code changes to the engine
- MUST tag all agentic test objects with `_system-test` for isolation
- MUST offer cleanup after agentic tests complete; never leave test artifacts without asking
- SHOULD run `/test-system` after significant changes to CLI, projection, or sync
- MUST NOT use `_system-test` tag for real user content
- SHOULD add new unit tests when adding new repository methods or CLI commands
- MUST keep test fixtures in `engine/tests/fixtures/` and update them when schema changes affect content format
