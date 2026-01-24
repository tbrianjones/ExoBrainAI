# PRD - XO Brain (v1) - Local GraphRAG Memory Engine

Owner: TBJ  
Status: Draft v1  
Target: A single GitHub repo others can clone and run locally (Docker), with user data stored outside the repo.

---

## 1. Problem

I want a local-first “memory engine” that ingests unstructured text (primarily conversation transcripts and thought dumps), builds a GraphRAG-based derived index (entities + relationships + theme/community summaries), and provides a simple CLI + local API so other tools (initially Claude Code) can:

- write new raw entries with zero required structure
- attach optional annotations and relationships after the fact
- run retrieval queries (global/theme and local/entity neighborhood)
- rebuild or incrementally update the index reliably

User data must never be committed to the repo and should live in a user-chosen folder (eg Dropbox) configured via local environment settings.

---

## 2. Goals

### Must-have (v1)
1) **Local-first**: runs entirely on a laptop in Docker.
2) **Single repo**: includes GraphRAG + wrappers + docker-compose.
3) **User data outside repo**: raw docs + overlays + outputs live in a folder path configured via env.
4) **Zero-friction capture**:
   - raw markdown files can contain anything; no YAML, no tags, no required naming conventions.
   - filenames are UUIDv7 (preferred) or a generated unique ID.
5) **Overlay annotations**:
   - append-only JSONL, partitioned daily
   - can include titles, summaries, tags, entities, and links
   - supports human + AI suggestions with confidence
   - overlays can be created by any UI layer (Claude Code, scripts, future integrations)
6) **Staging is required**:
   - before indexing, build “staged docs” that merge raw + relevant overlay annotations
   - GraphRAG indexes staged docs only (deterministic debugging)
7) **Index lifecycle**:
   - watcher: detect new raw docs and stage them quickly
   - incremental indexing: best-effort using GraphRAG update methods
   - scheduled full rebuild: configurable (eg nightly)
   - manual CLI commands for dev/testing
8) **CLI + local HTTP API**:
   - CLI commands to run stage/index/rebuild/query
   - API endpoints for query + metadata lookup (used by Claude Code or other clients)
9) **Model pluggability**:
   - default: local Ollama for chat + embeddings
   - optional: cloud models via config (OpenAI-compatible endpoints, etc)

### Should-have (v1)
- optional helper CLI to generate summaries as additional raw docs (not required)
- simple logs/metrics for pipeline runs (timestamps, counts, errors)

---

## 3. Non-goals (explicitly out of scope for v1)

- Ingestion integrations: email, calendar, Slack, Twitter/X, Bluesky, web crawling/snapshotting
- Auth/multi-user accounts
- Sharing/permissions UI
- Desktop UI / VS Code fork
- Fully autonomous multi-step “agent” loops (beyond client-driven iterative querying)
- Complex ontology/taxonomy enforcement
- Data encryption, key management, enterprise security features (address later)

Note: The architecture must keep a clear separation so future “integrations” can be added as optional modules without changing the core memory engine.

---

## 4. Key Principles

1) **Raw is canonical**: Raw docs are the durable ground truth; everything else is derived.
2) **Overlays hold intent**: Human and system intent lives in overlay JSONL (append-only).
3) **Staged is what is indexed**: A deterministic build step merges raw + overlays for GraphRAG input.
4) **No user cognition tax**: The system should not require tags/structure at capture time.
5) **Pluggable interfaces**: Claude Code is the initial UI, but the engine is UI-agnostic.

---

## 5. User Stories

### Capture (zero friction)
- As a user, I can dump a thought/transcript into a new doc with one command, without tags or structure.

### Add structure later
- As a user, I can later attach titles, summaries, tags, entity hints, and links via overlay records.
- As a user, I can add rich free-text relationship descriptions between docs (paragraphs).

### Query and iterate
- As a user, I can query for themes (global) or focus on a topic/entity neighborhood (local).
- As a user, my client (Claude Code) can run multiple queries iteratively, fetching more context as needed.

### Maintain and rebuild
- As a user, the system keeps the index current when new docs arrive.
- As a user, I can trigger a full rebuild when models improve.

---

## 6. Architecture Overview

### Components (all in one repo)
1) **Core Engine Container**
   - includes GraphRAG
   - includes wrapper services (stager, watcher, scheduler, API)
2) **Data Folder (external to repo)**
   - raw documents (flat)
   - overlay JSONL (daily partitioned)
   - staged documents (generated)
   - GraphRAG output artifacts (generated)
   - logs/cache (optional)

### High-level data flow
Raw Docs + Overlay JSONL
  -> Stager builds Staged Docs
  -> GraphRAG indexes Staged Docs
  -> Output Artifacts
  -> Query API reads artifacts and serves retrieval results

Watcher/Scheduler:
  - watches raw docs and overlay logs
  - triggers staging
  - triggers incremental index updates
  - triggers scheduled full rebuild

---

## 7. Data Storage Layout (External Folder)

All paths are under a user-defined root `${XO_BRAIN_DATA_DIR}` (configured via local env).

Example:
${XO_BRAIN_DATA_DIR}/
  raw/
    <uuidv7>.md
  overlay/
    annotations/
      2026-01-23.jsonl
      2026-01-24.jsonl
    policy/                 # optional later; not required v1 but reserved
  staged/
    <uuidv7>.md             # generated, safe to delete/recreate
  graphrag/
    output/                 # GraphRAG artifacts
    cache/                  # optional
  logs/

Repo must ship with a `.env.example` showing how to set XO_BRAIN_DATA_DIR.

---

## 8. Raw Document Format (v1)

- Raw docs are plain markdown, no required front matter.
- Filename is the document ID (UUIDv7 preferred).
- Raw doc content is free-form: transcripts, notes, links, summaries, anything.

---

## 9. Overlay Schema (v1)

### Overlay storage
- Append-only JSONL
- Partitioned daily: `${XO_BRAIN_DATA_DIR}/overlay/annotations/YYYY-MM-DD.jsonl`
- Many records can target the same doc.
- v1 staging behavior is **additive aggregation**:
  - Do not deduplicate or “latest wins” yet
  - If multiple titles exist, include them all in staged output
  - Same for summaries, tags, entities, links

### Single standard JSON object shape (v1)
Each JSONL line is an “annotation record” for one `doc_id`.

Required fields:
- `v` (int) - schema version, start with 1
- `id` (string) - uuidv7
- `ts` (string) - ISO timestamp
- `doc_id` (string) - uuidv7 of raw doc (filename)
- `source` (string enum) - `human | ai | system | import`

Optional fields:
- `title` (string)
- `summary` (string)
- `tags` (array of objects)
- `entities` (array of objects)
- `links` (array of objects)
- `extra` (object)

#### tags item
- `tag` (string)
- `confidence` (float 0..1, optional)
- `note` (string, optional)

#### entities item
- `name` (string)
- `confidence` (float 0..1, optional)
- `note` (string, optional)

#### links item
- `doc_id` (string) - linked doc ID
- `confidence` (float 0..1, optional)
- `note` (string, optional, can be a paragraph)

Example:
{
  "v": 1,
  "id": "01992c8f3c9a7...",
  "ts": "2026-01-23T20:12:00-08:00",
  "doc_id": "01992c8b0d9e7...",
  "source": "human",
  "title": "Book chapter ideas - tone",
  "tags": [{"tag":"book","confidence":1.0}],
  "links": [{"doc_id":"01992c8a2c6a7...","confidence":1.0,"note":"Follow-up refining same concept."}]
}

Notes:
- Links have no typed relation in v1. “Link exists” implies related; `note` carries semantics.
- Confidence granularity: per tag/entity/link.

---

## 10. Staging (Required)

### Purpose
GraphRAG must see both:
- raw doc content
- overlay annotations relevant to that doc

Staging builds `${XO_BRAIN_DATA_DIR}/staged/<doc_id>.md` for each raw doc.

### Staged file format (v1)
Staged docs prepend an overlay section before the raw content.

Example staged doc:

[DOC_ID: <doc_id>]

[OVERLAY]
TITLES:
- <title 1>
- <title 2>

SUMMARIES:
- <summary 1>
- <summary 2>

TAGS:
- <tag> (confidence=...)
- ...

ENTITIES:
- <name> (confidence=...) - <note>
- ...

LINKS:
- <linked_doc_id> (confidence=...) - <free text note>
- ...

[RAW]
<raw markdown content>

### Overlay aggregation rule (v1)
- Collect all overlay records for `doc_id` across:
  - last N days (default, configurable) OR all days (config)
- Concatenate lists; do not dedupe.

### Implementation details
- Provide a stager module that can:
  - stage one doc by ID
  - stage all docs
  - stage docs modified since a watermark
- Stager should be deterministic and idempotent.

---

## 11. GraphRAG Integration

### GraphRAG project root
Within `${XO_BRAIN_DATA_DIR}/graphrag/` maintain GraphRAG config and outputs.

GraphRAG input points to `${XO_BRAIN_DATA_DIR}/staged/`.

### Index methods
- Incremental updates:
  - use GraphRAG update methods when new staged docs appear
- Full rebuild:
  - run full standard method and replace artifacts

### Model config
- Default: local Ollama for chat + embeddings
- Optional: cloud model endpoints via env-config

GraphRAG configuration must be driven by env vars so users can switch providers without code changes.

---

## 12. Watcher + Scheduler

### Watcher (v1)
- Watches `${XO_BRAIN_DATA_DIR}/raw/` for new/changed files.
- Watches `${XO_BRAIN_DATA_DIR}/overlay/annotations/` for changes.
- On change:
  - stage affected docs
  - enqueue an incremental index update job (best-effort)

### Scheduler (v1)
- Configurable schedule for full rebuild (default off, or default nightly).
- Provide a safe lock to prevent overlapping index runs.

---

## 13. CLI (v1)

CLI must be well documented and stable, designed to be called by Claude Code.

Proposed commands:
- `xo stage --doc <id>`: stage one doc
- `xo stage --all`: stage all docs
- `xo index --incremental`: run incremental GraphRAG update
- `xo rebuild`: full rebuild
- `xo query --mode global --q "..."`: query global/theme
- `xo query --mode local --q "..."`: query local/neighborhood
- `xo status`: show last index time, counts, watcher status
- `xo doctor`: validate config, model connectivity, folder permissions

Note: v1 does not require a “capture spec”. Capture can be implemented by any client by writing a new file into raw folder.

---

## 14. Local HTTP API (v1)

API is for programmatic access (Claude Code wrapper, future integrations).

Endpoints:
- `GET /health`
- `GET /status`
- `POST /query/global` { query: string, options?: {...} }
- `POST /query/local`  { query: string, options?: {...} }
- `GET /doc/:id` - returns raw + overlay + staged (optional)
- `GET /doc/:id/overlay` - returns aggregated overlay records
- `GET /doc/:id/links` - returns linked doc_ids + notes + confidence
- `POST /admin/stage` - stage one/all (optional admin)
- `POST /admin/index/incremental`
- `POST /admin/index/rebuild`

API should support “scope filters” later (see Section 17).

---

## 15. Docker / Repo Requirements

Repo includes:
- docker-compose.yml to start:
  - api service
  - watcher/scheduler service (can be same container)
  - optional ollama service (or user runs ollama separately)
- `.env.example`:
  - `XO_BRAIN_DATA_DIR=/Users/<you>/Dropbox/XOBrain`
  - model provider settings
- `.gitignore`:
  - ignore any local env files
  - ignore any user data folders if accidentally placed inside repo
  - ignore staged and graphrag outputs if inside repo during dev

Must ensure:
- repo can run without committing any private data
- user can point to any folder (Dropbox/iCloud/local) for persistence and sync

---

## 16. Future Integrations (Not built in v1, but planned)

Concept: “XO Brain Integrations” are separate modules/packages that:
- ingest data into raw + overlays
- query the API
- export outputs

Examples (future):
- Slack bot integration
- Email triage integration
- Calendar assistant integration
- Blog/tweet generator
- Personal personas (work vs home) implemented as policies/scopes

v1 must keep core engine clean and decoupled from integration logic.

---

## 17. Scoping, Sharing, and “Query Only This Area” (Design for now, implement later)

Even though permissions UI and multi-user are out of scope, v1 should be designed so we can later:
- restrict queries to subsets of docs/entities
- share limited slices with others

### Recommended approach: Policy overlay (separate lifecycle)
Create a reserved folder:
`${XO_BRAIN_DATA_DIR}/overlay/policy/`

Policy records can be updated frequently without mutating raw or annotation overlays.

Proposed policy record shape (not required to implement fully in v1):
- doc-level visibility: `private | shared:<group> | public`
- scope tags: `scope:work`, `scope:family`, `scope:book:redbane`
- redaction flags: “do not include raw text”, “summary only”, etc

Example policy JSONL line:
{
  "v": 1,
  "id": "uuidv7",
  "ts": "iso8601",
  "target": {"kind":"doc","id":"<doc_id>"},
  "policy": {
    "scopes": ["work", "project_x"],
    "visibility": "private"
  }
}

### Query-time filtering
Later, the query API should accept:
- `scope_allow: ["work"]`
- `scope_deny: ["family"]`
- `visibility: private|shared|public`
and filter retrieval to eligible docs before building context.

### Index-time considerations
In v1, GraphRAG indexing is global over staged docs. For later sharing, two viable strategies exist:
1) Keep one global index, but enforce filtering at query time by excluding disallowed contexts.
2) Build multiple indices per scope (heavier, but stronger isolation).

PRD decision for v1: implement placeholders only.
- Reserve policy overlay path
- Add API request fields for scope filters (no-op in v1 or limited filtering)
- Document how sharing will be layered later

---

## 18. Acceptance Criteria

1) Clone repo, set `XO_BRAIN_DATA_DIR` to an external folder, run `docker compose up`, system starts.
2) Drop a UUIDv7 markdown file into `${XO_BRAIN_DATA_DIR}/raw/`.
3) Watcher stages it into `${XO_BRAIN_DATA_DIR}/staged/` with overlay section.
4) Add overlay JSONL line referencing that doc in today’s overlay file; watcher updates staged file.
5) Run incremental index update; query returns answers grounded in indexed content.
6) Full rebuild succeeds and produces GraphRAG output artifacts in `${XO_BRAIN_DATA_DIR}/graphrag/output/`.
7) No user data is stored inside the repo; `.gitignore` prevents accidental commits.

---

## 19. Open Questions (for implementation, not blocking PRD)
- Best default local models for M2 Pro 16GB (likely 7B-8B chat + small embedding)
- Exact GraphRAG query modes to expose first (global and local)
- Incremental update robustness vs batching updates
- Whether to include an optional “summary helper” command in v1

---

## 20. Implementation Notes (guidance)
- Keep overlay parsing fast: read only recent overlay files by default, allow “scan all” mode.
- Maintain a watermark for staging so the watcher can stage efficiently.
- Provide clear logs for staging/indexing steps, especially on model failures.
- Ensure stager never mutates raw docs.
