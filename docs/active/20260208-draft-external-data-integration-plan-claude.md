---
status: Planning
date: 2026-02-08
branch: TBD
related-adrs:
  - 002-sqlite-core-memory-layer
  - 003-exobrain-cli-architecture
  - 006-information-centric-computing-vision
  - 007-projection-layer-architecture
  - 011-primitive-semantics-and-knowledge-gardening
---

# External Data Integration and Ephemeral Content Layer

## Summary

ExoBrain is currently an island; AI agents working inside it cannot access data from external services (Gmail, Slack, Jira, Twitter, etc.) without live API calls. This plan proposes a connector architecture that pulls external data into local SQLite storage so agents can work with it as naturally as native ExoBrain objects. It also introduces the concept of ephemeral content: temporary objects or files that exist for project work or sharing, then get swept away. The primary connector ecosystem is Meltano/Singer (MIT, 100% Python, target-sqlite), with PyAirbyte filling gaps.

## Agent Quick Start

**Files to load:**
- `engine/src/core/schema.py` ; object schema, source/status fields
- `engine/src/core/repository.py` ; ObjectRepo.create(), TagRepo, LinkRepo
- `engine/src/core/projection.py` ; projection cycle, scoring, sync
- `engine/src/core/models.py` ; ObjectDetail, ObjectSummary
- `engine/src/cli/main.py` ; CLI capture/list/search commands
- `engine/src/graphrag/adapter.py` ; example adapter pattern (SQLite to staging)
- `engine/src/config.py` ; EXOBRAIN_DATA_DIR, settings

**ADRs to read:**
- ADR-002: SQLite core; repository pattern; FTS5
- ADR-003: CLI as sole write interface
- ADR-006: Information-centric computing vision
- ADR-007: Projection layer with hot tier scoring and bidirectional sync
- ADR-011: Primitive semantics; spaces, types, tags, links

**Areas to explore:**
- Meltano Singer SDK: https://sdk.meltano.com/
- MeltanoLabs tap-slack: https://github.com/MeltanoLabs/tap-slack
- MeltanoLabs target-sqlite: https://github.com/MeltanoLabs/target-sqlite
- PyAirbyte: https://airbyte.com/product/pyairbyte

## Problem Statement

**User persona:** Solo developer/knowledge worker using ExoBrain as a personal knowledge and ideation system.

**Pain point:** ExoBrain stores the user's own thoughts, transcripts, and documents, but the user's professional and personal life generates data across many external services: email (Gmail), messaging (Slack, iMessage/SMS), project management (Jira), social feeds (Twitter, Hacker News, Substack), calendars, and more. Today, this data is inaccessible to AI agents working within ExoBrain unless the agent makes live API calls, which are slow, rate-limited, context-expensive, and require the agent to understand each service's API.

**Core thesis:** Pulling data locally so AI agents can parse over it is what truly opens things up. A local ExoBrain with your Slack messages, Gmail threads, and Jira tickets sitting in SQLite alongside your notes is fundamentally more powerful than an agent that has to make API calls to fetch each piece of data on demand.

**Current state:** No external data integration exists. The `source='import'` field on objects exists but is unused. The projection layer writes markdown files from SQLite but has no mechanism for files that don't originate from the database.

**Secondary pain point:** The user also wants to generate temporary outputs (reports, summaries, briefs) from ExoBrain that can be shared with others but shouldn't permanently live in the system. This "ephemeral content" concept applies to both inbound external data (pulled temporarily for a project) and outbound generated artifacts.

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| External data accessible to agents | 0 sources | 1+ (Slack) | `exobrain list --tag source:slack` returns results |
| Time to access external data | N/A (manual copy-paste) | `exobrain pull slack` completes in < 60s | CLI timing |
| Agent can find external data via search | Not possible | `exobrain search "slack message about X"` works | FTS5 search returns imported objects |
| Connector pipeline proven end-to-end | No pipeline exists | Slack data flows: tap -> transform -> exobrain.db -> projected/ | Manual verification |

## Feature Overview

**What it does:** Adds a connector subsystem to ExoBrain that pulls data from external services into local SQLite storage using open-source connector ecosystems (Meltano/Singer, PyAirbyte). Imported data becomes searchable, taggable, linkable, and projectable just like native ExoBrain objects. An ephemeral content concept (design TBD) allows temporary data to exist for project work without permanent storage commitment.

**Core user flow (permanent capture):**
1. User configures a connector: `exobrain connector add slack --token xoxb-...`
2. User pulls data: `exobrain pull slack --since 7d`
3. Singer tap-slack extracts messages from Slack API
4. ExoBrain adapter transforms raw Singer records into ExoBrain objects
5. Objects are created with `source='import'`, `type='Document'` (or custom type), `space='imports/slack'`, and tags like `source:slack`, `channel:#general`
6. `exobrain project` makes them available as markdown in `projected/imports/slack/`
7. AI agent can now read, search, and reason over Slack data alongside native objects

**Core user flow (ephemeral; design TBD):**
1. User pulls data temporarily: `exobrain pull slack --mode=stage --since 7d`
2. Data appears in projection space (or DB with TTL) for project work
3. AI agent works with it alongside permanent objects
4. Data auto-expires or is manually cleaned up

## Scope

### In scope

- Connector registry: configuration, credential storage, last-sync tracking
- Adapter layer: transform Singer/PyAirbyte output to ExoBrain objects
- CLI commands: `exobrain connector add/list/remove`, `exobrain pull <source>`
- Slack as first connector (tap-slack, API token auth)
- Tagging and space organization for imported data
- Provenance tracking via `source='import'` and tags
- Research and design document for ephemeral content concept

### Out of scope (do not build)

- OAuth flow UI or web-based connection setup
- Real-time streaming or webhooks (batch pull only for Phase 1)
- MCP server integration (future phase)
- Write-back to external services (push data to Slack, send emails)
- Building custom Singer taps (use existing community taps)
- Full Meltano platform deployment (use taps as Python libraries or CLI)
- Composio, OpenClaw, n8n, or Activepieces integration
- Multi-user or multi-tenant connector management

### Dependencies

- Meltano Singer SDK (pip-installable)
- tap-slack (pip-installable from MeltanoLabs)
- target-sqlite or direct Python integration
- Docker compose setup may need updates for new dependencies

## User Stories and Acceptance Criteria

### US-1: Pull Slack data into ExoBrain

**As a** knowledge worker, **I want to** pull my recent Slack messages into ExoBrain **so that** AI agents can search and reason over them alongside my notes.

**Acceptance Criteria:**

- **Given** a configured Slack connector with valid API token, **when** I run `exobrain pull slack --since 7d`, **then** messages from the last 7 days are created as ExoBrain objects with `source='import'` and tagged `source:slack`.
- **Given** imported Slack messages, **when** I run `exobrain search "project deadline"`, **then** matching Slack messages appear in search results alongside native objects.
- **Given** imported Slack messages, **when** I run `exobrain project`, **then** hot-tier imported messages appear as markdown files in `projected/imports/slack/`.

### US-2: Manage connectors

**As a** user, **I want to** add, list, and remove connector configurations **so that** I can control which external services ExoBrain pulls from.

**Acceptance Criteria:**

- **Given** no configured connectors, **when** I run `exobrain connector add slack --token xoxb-...`, **then** the connector is registered and credentials are stored securely.
- **Given** configured connectors, **when** I run `exobrain connector list`, **then** I see all configured connectors with last-sync timestamps and status.
- **Given** a configured connector, **when** I run `exobrain connector remove slack`, **then** the connector and its stored credentials are removed (imported objects remain).

### US-3: Incremental sync

**As a** user, **I want** subsequent pulls to only fetch new data **so that** I don't duplicate objects or waste API calls.

**Acceptance Criteria:**

- **Given** a previous pull completed at timestamp T, **when** I run `exobrain pull slack` again, **then** only data newer than T is fetched and imported.
- **Given** incremental sync, **when** the same message is encountered, **then** it is deduplicated (not created as a second object).

### US-4: Ephemeral content (design story)

**As a** user, **I want** to generate or import temporary content that exists for project work but doesn't permanently live in ExoBrain **so that** I can share reports with others or stage external data without cluttering my knowledge base.

**Acceptance Criteria:** TBD pending design decision (see Open Questions).

## Key Decisions

| # | Decision | Alternatives Considered | Rationale |
|---|----------|------------------------|-----------|
| 1 | Meltano/Singer as primary connector ecosystem | Composio, OpenClaw, n8n, Activepieces, Nango, PyAirbyte | MIT licensed, 100% Python, target-sqlite exists, 600+ taps, CLI-first matches ExoBrain philosophy |
| 2 | PyAirbyte as complement for gaps | Meltano-only, custom connectors | Covers services where Singer taps don't exist (e.g., Google Calendar); pip-installable; runs in-process |
| 3 | Local data storage over API proxying | Composio (cloud-mediated proxy), MCP (real-time tool calls) | Core thesis: local data is more powerful for AI agents than API access. No rate limits, no latency, no context window waste |
| 4 | Slack as first connector | Gmail (complex OAuth), RSS/HN (no auth), SMS/iMessage (no existing tap) | Existing MeltanoLabs tap, simple API token auth, high-value messaging data, proves pipeline without OAuth complexity |
| 5 | Ephemeral content as open question | In-DB with TTL, projection-only files, new status field | Both approaches have merit; needs more design exploration before committing |

### Decision 1: Meltano/Singer

**Research findings:** Four research agents investigated Composio, OpenClaw, and alternatives (Nango, Airbyte, Meltano, n8n, Activepieces).

- **Composio** is a cloud-mediated API proxy. Every call routes through `backend.composio.dev`. No self-hosting. No raw token access. "Open source" is SDK-only; the backend is proprietary SaaS. Architecturally misaligned with local-first philosophy.
- **OpenClaw** (176K GitHub stars, MIT) is an AI chat gateway, not a data integration tool. Its credential management patterns (auth-profiles with rotation/cooldown) are worth studying, but it's too heavy as a dependency. TypeScript; not Python.
- **Nango** has excellent OAuth management but is Elastic License 2.0, TypeScript-only, requires Postgres/Redis/S3/5 Node services. Way too heavy.
- **n8n** and **Activepieces** are workflow automation tools, not data ingestion libraries. Their connectors can't be used standalone.
- **Meltano/Singer** is MIT, 100% Python, has target-sqlite, has taps for Gmail/GitHub/Slack/Jira/RSS. CLI-first. The Singer SDK makes building custom taps straightforward.
- **PyAirbyte** (`pip install airbyte`) runs 600+ Airbyte connectors in-process with local DuckDB cache. Fills gaps where Singer taps don't exist.

### Decision 3: Local data over API proxying

The user's articulation: "I don't believe hitting APIs gives AI agents power. I think pulling data locally so they can just parse over it is what truly opens things up."

This aligns with ADR-006 (information-centric computing vision) and the projection layer design (ADR-007). An AI agent reading markdown files in `projected/` is fundamentally simpler and more capable than one making API calls mid-conversation.

## Technical Approach

### Architecture

```
                     ┌─────────────────────────────┐
                     │     Credential Store         │
                     │  (.env / Docker secrets /    │
                     │   future: encrypted SQLite)  │
                     └──────────┬──────────────────┘
                                │
              ┌─────────────────┼─────────────────────┐
              │                 │                      │
     ┌────────▼───────┐ ┌──────▼────────┐  ┌─────────▼────────┐
     │ Singer/Meltano │ │   PyAirbyte   │  │  Custom Python   │
     │   tap-slack    │ │ (gap-filler)  │  │  (future: HN,    │
     │   tap-gmail    │ │               │  │   iMessage, etc) │
     │   tap-jira     │ │               │  │                  │
     └────────┬───────┘ └──────┬────────┘  └─────────┬────────┘
              │                │                      │
              └────────────────┼──────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  ExoBrain Connector  │
                    │    Adapter Layer     │
                    │                     │
                    │  Transform raw      │
                    │  records → ExoObjects│
                    │                     │
                    │  Two modes:         │
                    │  1. capture → DB    │
                    │  2. stage → TBD     │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                                 │
    ┌─────────▼──────────┐          ┌──────────▼──────────┐
    │   exobrain.db      │          │  Ephemeral layer    │
    │                    │          │  (design TBD)       │
    │  source='import'   │          │                     │
    │  tags: source:slack│          │  Options:           │
    │  space: imports/   │          │  - projected/ files │
    │  type: Document    │          │  - DB with TTL      │
    └────────────────────┘          └─────────────────────┘
```

### Code organization

```
engine/src/
  connectors/                    # NEW: connector subsystem
    __init__.py
    registry.py                  # Connector config, credentials, sync state
    adapter.py                   # Transform raw records → ExoObjects
    singer.py                    # Singer tap runner (invoke taps, parse output)
    connectors/
      slack.py                   # Slack-specific field mapping and types
      # gmail.py, jira.py, etc. (future)
  cli/
    main.py                      # Add: connector and pull commands
```

### Data mapping (Slack example)

Singer tap-slack emits records with schemas like:
```json
{
  "type": "RECORD",
  "stream": "messages",
  "record": {
    "channel_id": "C01234",
    "ts": "1707350400.000000",
    "user": "U01234",
    "text": "Has anyone reviewed the PR?"
  }
}
```

The adapter transforms this to:
```python
ObjectRepo.create(
    title=f"Slack message in #{channel_name}",
    content=record["text"],
    summary=f"From @{username} in #{channel_name} at {timestamp}",
    type_name="Document",        # or custom "SlackMessage" type
    space_name="imports/slack",
    source="import",
)
TagRepo.add(obj_id, "source:slack")
TagRepo.add(obj_id, f"channel:{channel_name}")
TagRepo.add(obj_id, f"user:{username}")
```

### Credential storage (Phase 1)

Start simple: credentials in `.env` or Docker secrets. The connector registry stores:
- Connector name and type
- Credential reference (env var name, not the secret itself)
- Last sync timestamp
- Sync configuration (--since, streams to include/exclude)

This could be a new table in `exobrain.db` or a simple JSON file in `$EXOBRAIN_DATA_DIR`.

### Deduplication

Each imported object needs a stable external ID for deduplication. For Slack: `slack:{channel_id}:{message_ts}`. Store this as a tag (`external-id:slack:C01234:1707350400.000000`) or in a dedicated field. On subsequent pulls, check for existing objects with the same external ID before creating duplicates.

## Implementation Phases

### Phase 1: Slack connector end-to-end (MVP)

- [ ] Create `engine/src/connectors/` module structure
- [ ] Implement connector registry (add/list/remove, credential references, sync state)
- [ ] Implement Singer tap runner (invoke tap-slack as subprocess, parse JSON output)
- [ ] Implement Slack adapter (transform records → ExoBrain objects)
- [ ] Add CLI commands: `exobrain connector add`, `exobrain connector list`, `exobrain connector remove`, `exobrain pull`
- [ ] Add deduplication via external ID
- [ ] Add `imports/slack` space auto-creation
- [ ] Add incremental sync (track last-sync timestamp, pass to tap)
- [ ] Write unit tests for adapter and registry
- [ ] Write agentic integration test for pull pipeline
- [ ] Update Docker compose if new dependencies needed
- [ ] Create `imports/` space hierarchy in bootstrap

**Deliverable:** `exobrain pull slack --since 7d` populates ExoBrain with Slack messages that are searchable, taggable, and projectable.

### Phase 2: Ephemeral content design

- [ ] Design exploration: in-DB with TTL vs projection-only files vs hybrid
- [ ] Consider implications for both inbound (imported data) and outbound (generated reports)
- [ ] Prototype the chosen approach
- [ ] Possibly create ADR for ephemeral content architecture
- [ ] Implement ephemeral mode for `exobrain pull --mode=stage`
- [ ] Implement ephemeral mode for generated outputs (reports, summaries)

### Phase 3: Additional connectors

- [ ] Gmail connector (requires OAuth flow; more complex auth)
- [ ] RSS/Hacker News (tap-feed; simple, no auth)
- [ ] Twitter (evaluate available taps or custom)
- [ ] SMS/iMessage (likely custom; Apple platform integration)
- [ ] Substack (evaluate available taps or custom scraper)
- [ ] Generalize adapter pattern based on lessons from Slack

### Phase 4: Advanced features

- [ ] Credential management upgrade (encrypted storage, rotation, cooldown pattern inspired by OpenClaw)
- [ ] Scheduled sync (cron-based, configurable per connector)
- [ ] MCP server layer for real-time access when local data is stale
- [ ] PyAirbyte integration for connectors without Singer taps
- [ ] Web UI connector management view
- [ ] Write-back capability (push data to external services)

## Open Questions

| # | Question | Impact | Notes |
|---|----------|--------|-------|
| 1 | Should ephemeral content live in ExoBrain DB with TTL/auto-sweep, or as projection-only files that never touch SQLite? | Determines data model for temporary content | In-DB gives search/tags/links; projection-only is simpler but loses those features. Could also be a new `status='ephemeral'` value. User wants to think more before committing. |
| 2 | Should imported objects use existing types (Document) or create custom types (SlackMessage, Email, Tweet)? | Affects schema design and query patterns | Custom types are more semantic but add complexity. Could start with Document and add types later if needed. |
| 3 | How should external IDs be stored for deduplication? | Affects dedup reliability and query performance | Options: tag (`external-id:...`), dedicated field on objects table, separate mapping table. Tags are simplest but could get verbose. |
| 4 | Should connectors run inside the Docker container or on the host? | Affects dependency management and networking | Inside container is simpler for isolation; host gives access to Apple APIs (iMessage). |
| 5 | How should credential storage evolve beyond .env files? | Affects security and UX | Options: encrypted SQLite table, system keychain, Docker secrets. Phase 1 uses .env; needs a plan for Phase 3+. |
| 6 | Should the connector adapter be a CLI-level concept or a repository-level concept? | Affects where the transform logic lives | ADR-003 says CLI is sole write interface, but bulk imports might justify repository-level batch operations for performance. |
| 7 | Ephemeral outbound content: how do generated reports/summaries get shared? | Affects the ephemeral layer design | Options: projected markdown files, exported to a temp directory, served via web UI, pushed to external service. |

## Future Considerations

**Discussed but deferred:**
- **MCP as complementary layer:** When an agent needs fresh data that hasn't been synced yet, MCP servers could provide real-time access. The synced SQLite data covers the 95% case; MCP handles edge cases. Deferred until after connector pipeline is proven.
- **OpenClaw credential patterns:** The auth-profile system with rotation and cooldown is worth implementing when credential management becomes complex (Phase 4).
- **Nango for OAuth:** If Gmail and other OAuth-heavy services prove difficult with DIY token management, Nango's auth layer could be adopted (heavy infrastructure cost, but excellent OAuth handling).
- **PyAirbyte Agent Connectors:** Airbyte launched 21 real-time agent connectors (GitHub, Jira, Stripe, etc.) as Python packages. These are proxy-only (not local storage) but could complement the sync pipeline for real-time needs.
- **Bidirectional sync:** The projection layer already supports sync (markdown edits → SQLite). Could extend this to sync edits on imported objects back to external services (e.g., update a Jira ticket from ExoBrain).
- **Custom Singer taps:** The Meltano Singer SDK makes building custom taps straightforward. Missing services (iMessage, Hacker News, custom sites) could get dedicated taps.

## Verification

**Phase 1 verification:**

```bash
# Add Slack connector
docker compose exec exobrain exobrain connector add slack --token "$SLACK_TOKEN"

# Pull recent messages
docker compose exec exobrain exobrain pull slack --since 7d

# Verify objects were created
docker compose exec exobrain exobrain list --tag source:slack --json

# Verify search works
docker compose exec exobrain exobrain search "search term from slack"

# Verify projection
docker compose exec exobrain exobrain project
ls $EXOBRAIN_DATA_DIR/projected/imports/slack/

# Verify incremental sync (second pull should be fast, no dupes)
docker compose exec exobrain exobrain pull slack --since 7d
docker compose exec exobrain exobrain list --tag source:slack --json | python -c "import json,sys; d=json.load(sys.stdin); print(f'{len(d)} objects, no dupes')"

# Verify connector management
docker compose exec exobrain exobrain connector list
docker compose exec exobrain exobrain connector remove slack
```

## References

- **Research session:** 2026-02-08 conversation exploring Composio, OpenClaw, and alternatives
- **Libraries evaluated:** Composio (cloud proxy, rejected), OpenClaw (too heavy, patterns studied), Nango (heavy infrastructure), PyAirbyte (complement), Meltano/Singer (primary), n8n (wrong tool), Activepieces (wrong tool)
- **Related plans:** `20260128-exobrain-projection-layer-plan-claude.md`
- **Future ADR:** Consider creating ADR for connector architecture and/or ephemeral content layer once design solidifies
