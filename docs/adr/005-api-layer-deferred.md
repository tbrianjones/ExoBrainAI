# ADR 005: API Layer Deferred

- **Status:** Accepted
- **Date:** 2026-01-27
- **Tags:** architecture, api, deferred
- **Impact:** Low

## Context

ExoBrain v1 includes a partially built FastAPI layer in `engine/src/api/`. This API was started speculatively; it exposes routes for health checks, document CRUD, query endpoints, and admin operations (staging, indexing). However, the v2 redesign focuses on CLI + SQLite as the core interface, and Claude Code (via the exobrain skill) is the first UI.

The API layer has no current consumer. The CLI serves all v0 needs. Building, testing, and maintaining API routes adds complexity without delivering value at this stage. The user explicitly stated the API is not needed for v0.

## Decision Drivers

1. **No current consumer**: No web UI, mobile app, or external service needs HTTP access to ExoBrain
2. **CLI covers all workflows**: Every operation (capture, query, annotate, stage, index) is available via CLI
3. **Reduced scope**: v0 focuses on the core memory engine; fewer moving parts means faster delivery
4. **Maintenance burden**: API routes require testing, documentation, error handling, and versioning; all effort better spent on the core engine
5. **Reversible decision**: The API code exists and can be activated when needed

## Considered Options

### 1. Build and maintain the API for v0

- Rejected: No consumer exists. Building API routes, writing tests, and maintaining documentation for unused endpoints is wasted effort.

### 2. Delete the API code entirely

- Rejected: The code exists and may be useful later. Deleting it creates rework when a consumer eventually appears.

### 3. Preserve but defer the API (chosen)

- The FastAPI code remains in the repository
- It is not scoped, tested, or maintained for v0
- It is not included in the v0 definition of done
- It will be revisited when a web UI or external consumer is needed

## Decision Outcome

Chosen option: **Preserve existing API code but defer all API work until a consumer exists**

The FastAPI layer in `engine/src/api/` remains in the codebase as reference code. It is not part of the v0 scope. No new API routes will be added, no existing routes will be updated, and no API tests will be written until there is a concrete consumer (web UI, mobile app, or external integration) that requires HTTP access.

The CLI is the sole supported interface for v0. Claude Code invokes the CLI through the exobrain skill (see ADR 004). This provides full functionality without the overhead of maintaining an API layer.

## Consequences

### Positive

- **Reduced v0 scope**: Fewer components to build, test, and maintain
- **Faster delivery**: Engineering effort focuses entirely on the core memory engine
- **Simpler architecture**: One interface (CLI) means one set of error handling, validation, and output formatting
- **No premature abstraction**: API design decisions can be made later with real consumer requirements

### Negative

- **Stale API code**: The existing API code will drift from the CLI as the core engine evolves; when the API is eventually activated, it will need updating
- **No remote access**: ExoBrain cannot be accessed from other machines or services without the API (acceptable for a single-user, local-first system)
- **Potential rework**: If a consumer appears soon, some work will need to be redone that could have been done incrementally

### Neutral

- **API code as documentation**: The existing routes serve as a rough specification of what the API could look like, even if the implementation is outdated

## Agent Rules

1. **MUST NOT** rely on API routes for any v0 functionality. All operations go through the CLI.

2. **SHOULD** preserve existing API code in `engine/src/api/` but do not extend, refactor, or add tests for it.

3. **MUST** document this deferral clearly so future agents do not accidentally build features on top of the API layer. The API is not a supported interface for v0.

4. **MUST NOT** add new API routes or update existing ones unless a concrete consumer has been identified and an ADR is written to activate the API.

5. **SHOULD** ensure CLI commands have complete feature parity with any future API; the CLI is the primary interface and must not become a second-class citizen.

## References

- Existing API Code: `engine/src/api/`
- ADR 001: `docs/adr/001-exobrain-v2-graphrag-memory-engine.md`
- ADR 004: `docs/adr/004-claude-code-first-ui.md`
- ExoBrain v2 Plan: `docs/archive/sqlite-base-memory-layer/20260127-exobrain-v2-sqlite-base-memory-layer-dev-plan-claude.md`
