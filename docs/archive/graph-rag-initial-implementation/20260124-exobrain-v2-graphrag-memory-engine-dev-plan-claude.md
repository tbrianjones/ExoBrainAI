---
status: Planning
date: 2026-01-24
branch: feature/exobrain-v2
supersedes:
  - docs/active/20260117-exobrain-cli-implementation-plan-claude.md
  - docs/adr/001-exobrain-workspace-structure-and-schema.md
related-adrs: []
---

# ExoBrain v2: GraphRAG Memory Engine

## Summary

Transform the ExoBrain repository into a Docker-based local-first memory engine with GraphRAG-powered retrieval. Raw documents live in an external folder (Dropbox-backed), annotations accumulate in overlay JSONL, and staged documents feed GraphRAG indexing. Claude Code commands/agents become the first "integration" consuming this memory layer.

## Agent Quick Start

**Files to load first:**
- `docs/active/20260123-exobrain-v2-memory-system-design-plan-chatgpt.md` (v2 design spec)
- `/Users/tbj/.claude/plans/glimmering-twirling-kettle.md` (detailed phase plan)
- `.claude/commands/ideate.md` (current ideation flow to update)
- `.claude/agents/transcript-raw-text-summary-generator.md` (current agent pattern)

**Files to remove (Phase 1):**
- `scripts/gemini.py`
- `.claude/skills/gemini.md`
- `scripts/init.sh`
- `requirements.txt`
- `exobrain.egg-info/`

**Explore before implementing:**
- GraphRAG Python package structure and configuration
- Ollama Docker integration patterns
- FastAPI + Typer CLI patterns for unified codebase

**Relevant skills:** None currently; will create `.claude/skills/exobrain.md`

---

## Problem Statement

| Element | Detail |
|---------|--------|
| **User Persona** | TBJ; creator using Claude Code as primary UI for ideation and content generation |
| **Pain Point** | Current system mixes concerns: `ideas/` is an unstructured memory store, Claude commands are the UI layer, no intelligent retrieval, .venv-based setup isn't portable |
| **Current State** | Prose-based storage in `ideas/`, incomplete `exobrain` CLI, Gemini dependency (unused), manual context loading |
| **Desired State** | Zero-friction capture → overlay annotations → staged docs → GraphRAG indexing → intelligent retrieval via CLI/API |
| **Business Impact** | Enables scalable personal knowledge management; foundation for future integrations (Slack, email, calendar) |

---

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Setup friction | Manual .venv + deps | Single `docker compose up` | Time to first query on fresh clone |
| Capture friction | Navigate to ideas/, create file, add structure | Drop markdown in raw/ folder | Steps to capture a thought |
| Query relevance | Manual file search | GraphRAG global/local retrieval | Subjective relevance of query results |
| Data portability | Committed to repo | External folder (Dropbox sync) | Data survives repo deletion |

---

## Feature Overview

**What it does:** A local-first memory engine that ingests unstructured text, builds a GraphRAG-based index, and provides CLI + API for retrieval.

**Core User Flow:**

1. User drops a markdown file into `${EXOBRAIN_DATA_DIR}/raw/`
2. Watcher detects new file and stages it
3. User (or system) adds overlay annotations via JSONL
4. Staging process merges raw + overlays into staged doc
5. GraphRAG indexes staged documents
6. User queries via `exobrain query` CLI or HTTP API
7. Results return grounded in indexed content

---

## Scope

### In Scope

- Docker-based deployment (engine + Ollama)
- Raw document storage (UUIDv7 filenames, no required structure)
- Overlay JSONL system (titles, summaries, tags, entities, links)
- Staging pipeline (raw + overlays → staged docs)
- GraphRAG integration (incremental + full rebuild)
- CLI: `exobrain init`, `stage`, `index`, `rebuild`, `query`, `status`, `doctor`, `migrate`
- HTTP API: health, status, query endpoints, admin endpoints
- File watcher for automatic staging
- Migration from existing `ideas/` folder
- Update Claude commands/agents to use new engine

### Out of Scope (Do Not Build)

- Ingestion integrations (email, Slack, calendar, web crawling)
- Multi-user authentication or sharing
- Desktop UI or VS Code extension
- Autonomous multi-step agent loops
- Data encryption or enterprise security
- Complex ontology/taxonomy enforcement
- Quarto publishing updates (future integration)

### Dependencies

- Docker and Docker Compose
- Ollama (included in compose or external)
- GraphRAG Python package
- FastAPI, Typer, Pydantic
- watchdog (file watcher)

---

## User Stories + Acceptance Criteria

### US1: Zero-Friction Capture

**As a** user
**I want to** dump a thought into a new doc with one action
**So that** I can capture ideas without cognitive overhead

**Acceptance Criteria:**
- **Given** EXOBRAIN_DATA_DIR is configured
- **When** I create a file `{uuidv7}.md` in `${EXOBRAIN_DATA_DIR}/raw/`
- **Then** the file is accepted with any content (no required structure)

### US2: Add Structure Later

**As a** user
**I want to** attach titles, summaries, tags, and links after capture
**So that** I can organize content when I have time

**Acceptance Criteria:**
- **Given** a raw document exists
- **When** I append a JSONL record to `overlay/annotations/{date}.jsonl`
- **Then** the overlay references the doc_id and includes optional metadata

### US3: Query Themes

**As a** user
**I want to** query for broad themes across my content
**So that** I can find related ideas I may have forgotten

**Acceptance Criteria:**
- **Given** documents have been indexed
- **When** I run `exobrain query --mode global --q "consciousness"`
- **Then** I receive theme-level summaries grounded in my content

### US4: Query Neighborhoods

**As a** user
**I want to** focus on a specific entity or topic
**So that** I can explore connected ideas in depth

**Acceptance Criteria:**
- **Given** documents have been indexed
- **When** I run `exobrain query --mode local --q "Claude Code"`
- **Then** I receive entity-neighborhood context from related documents

### US5: Automatic Staging

**As a** user
**I want** the system to keep staged docs current
**So that** I don't have to manually trigger staging

**Acceptance Criteria:**
- **Given** the watcher service is running
- **When** a new file appears in `raw/` or `overlay/annotations/`
- **Then** affected documents are automatically re-staged

### US6: Migration from Legacy

**As a** user
**I want to** migrate my existing `ideas/` content
**So that** I don't lose previous work

**Acceptance Criteria:**
- **Given** content exists in `ideas/` folder
- **When** I run `exobrain migrate --source ./ideas`
- **Then** transcripts become raw docs with UUIDv7 filenames
- **And** metadata becomes overlay annotations
- **And** original `ideas/` is renamed to `ideas-archived/`

---

## Key Decisions

| Decision | Choice | Alternatives Considered | Rationale |
|----------|--------|------------------------|-----------|
| Naming | ExoBrain / `exobrain` | XO Brain / `xo` | Consistency with existing codebase |
| Runtime | Docker Compose | .venv, Poetry, Nix | Portability; self-contained with Ollama |
| Ollama | Included in compose | External only | Reduces setup friction |
| Data location | External `EXOBRAIN_DATA_DIR` | In-repo `data/` | Dropbox sync; never commit personal data |
| Default models | Llama 3.1 8B + nomic-embed | Mistral 7B, smaller models | Good balance for M2 Pro 16GB |
| API port | 8420 | 8000, 3000 | Less likely to conflict |
| Migration | Include with archive | Defer, manual only | User wants content preserved |

### Decision Detail: Docker over .venv

The existing setup uses Python .venv with manual `init.sh` script. This requires:
- Python version management
- Manual dependency installation
- Platform-specific issues

Docker provides:
- Single `docker compose up` command
- Bundled Ollama service
- Consistent environment across machines
- Easy reset (remove containers/volumes)

### Decision Detail: External Data Directory

Raw documents and GraphRAG artifacts must never be committed to the repo. By requiring `EXOBRAIN_DATA_DIR` in `.env`:
- User chooses their sync solution (Dropbox, iCloud, local)
- Repo remains clone-able without personal data
- Backup strategy is user-controlled

---

## Technical Approach

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                           │
│  ┌─────────────────────┐    ┌─────────────────────────┐    │
│  │   exobrain service  │    │    ollama service       │    │
│  │  ┌───────────────┐  │    │  ┌───────────────────┐  │    │
│  │  │   FastAPI     │  │    │  │  Llama 3.1 8B     │  │    │
│  │  │   (port 8420) │  │    │  │  nomic-embed      │  │    │
│  │  ├───────────────┤  │    │  └───────────────────┘  │    │
│  │  │   CLI (Typer) │  │    └─────────────────────────┘    │
│  │  ├───────────────┤  │                                    │
│  │  │   Watcher     │  │                                    │
│  │  ├───────────────┤  │                                    │
│  │  │   GraphRAG    │  │                                    │
│  │  └───────────────┘  │                                    │
│  └──────────┬──────────┘                                    │
└─────────────┼───────────────────────────────────────────────┘
              │ volume mount
              ▼
┌─────────────────────────────────────────────────────────────┐
│              ${EXOBRAIN_DATA_DIR}                           │
│  ├── raw/              # UUIDv7.md files                    │
│  ├── overlay/                                               │
│  │   └── annotations/  # YYYY-MM-DD.jsonl                   │
│  ├── staged/           # Generated merged docs              │
│  ├── graphrag/                                              │
│  │   └── output/       # GraphRAG artifacts                 │
│  └── logs/                                                  │
└─────────────────────────────────────────────────────────────┘
```

### Code Structure

```
engine/
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── src/
    ├── __init__.py
    ├── config.py              # Environment config
    ├── core/
    │   ├── __init__.py
    │   ├── models.py          # Pydantic schemas
    │   ├── raw.py             # Raw document operations
    │   ├── overlay.py         # Overlay JSONL operations
    │   └── stager.py          # Staging logic
    ├── graphrag/
    │   ├── __init__.py
    │   ├── config.py          # GraphRAG settings
    │   ├── indexer.py         # Index operations
    │   └── querier.py         # Query operations
    ├── cli/
    │   ├── __init__.py
    │   ├── main.py            # Typer app entry
    │   └── commands/
    │       ├── init.py
    │       ├── stage.py
    │       ├── index.py
    │       ├── query.py
    │       ├── status.py
    │       ├── doctor.py
    │       └── migrate.py
    ├── api/
    │   ├── __init__.py
    │   ├── main.py            # FastAPI app
    │   └── routes/
    │       ├── health.py
    │       ├── query.py
    │       ├── docs.py
    │       └── admin.py
    └── watcher/
        ├── __init__.py
        ├── watcher.py         # File system watcher
        └── scheduler.py       # Scheduled rebuilds
```

### Overlay Schema (Pydantic)

```python
class OverlayRecord(BaseModel):
    v: int = 1
    id: str  # UUIDv7
    ts: datetime
    doc_id: str  # UUIDv7 of raw doc
    source: Literal["human", "ai", "system", "import"]
    title: str | None = None
    summary: str | None = None
    tags: list[TagItem] | None = None
    entities: list[EntityItem] | None = None
    links: list[LinkItem] | None = None
    extra: dict | None = None
```

### Key Files to Modify

| File | Change |
|------|--------|
| `CLAUDE.md` | Remove gemini skill; add exobrain CLI docs; update folder structure |
| `.claude/skills/gemini.md` | Delete |
| `.claude/skills/exobrain.md` | Create; document CLI and API usage |
| `.claude/commands/ideate.md` | Update to write to EXOBRAIN_DATA_DIR |
| `.claude/commands/generate-transcript.md` | Update output location |
| `.claude/agents/transcript-*.md` | Update to use new structure |

---

## Implementation Phases

### Phase 1: Branch and Cleanup

- Create `feature/exobrain-v2` branch off `main`
- Delete: `scripts/gemini.py`, `.claude/skills/gemini.md`, `scripts/init.sh`, `requirements.txt`, `exobrain.egg-info/`
- Update `CLAUDE.md` to remove gemini references
- Update `.gitignore` for new patterns

### Phase 2: Docker Foundation

- Create `docker-compose.yml` (exobrain + ollama services)
- Create `.env.example` with `EXOBRAIN_DATA_DIR`, `OLLAMA_HOST`
- Create `engine/Dockerfile` (Python 3.11 base)
- Create `engine/requirements.txt` and `engine/pyproject.toml`

### Phase 3: Core Memory Engine

- Implement `engine/src/core/models.py` (Pydantic schemas)
- Implement `engine/src/core/raw.py` (read/write raw docs)
- Implement `engine/src/core/overlay.py` (JSONL operations)
- Implement `engine/src/core/stager.py` (merge raw + overlays)

### Phase 4: GraphRAG Integration

- Implement `engine/src/graphrag/config.py` (model settings)
- Implement `engine/src/graphrag/indexer.py` (incremental + full)
- Implement `engine/src/graphrag/querier.py` (global + local)

### Phase 5: CLI Implementation

- Implement `engine/src/cli/main.py` (Typer app)
- Implement all subcommands: init, stage, index, rebuild, query, status, doctor

### Phase 6: HTTP API

- Implement `engine/src/api/main.py` (FastAPI)
- Implement routes: health, status, query, docs, admin

### Phase 7: Watcher and Scheduler

- Implement `engine/src/watcher/watcher.py` (watchdog-based)
- Implement `engine/src/watcher/scheduler.py` (optional scheduled rebuilds)

### Phase 8: Claude Integration Updates

- Create `.claude/skills/exobrain.md`
- Update `/ideate`, `/generate-transcript` commands
- Update transcript agents

### Phase 9: Migration

- Implement `engine/src/cli/commands/migrate.py`
- Run migration with `--dry-run` first
- Archive `ideas/` to `ideas-archived/`
- Verify document counts and content integrity

---

## Open Questions

| Question | Impact | Notes |
|----------|--------|-------|
| GraphRAG incremental update reliability | May need batching | Test with real workload |
| Optimal overlay aggregation window | Affects staged doc size | Start with 30 days, make configurable |
| Watcher debounce strategy | Affects responsiveness | Avoid re-staging on rapid edits |
| Model pull strategy | First-run experience | Pull models on `exobrain init` or lazy? |

---

## Future Considerations

Items discussed but explicitly deferred:

- **Quarto publishing integration**: Convert `/publish-quarto` to read from ExoBrain
- **Ingestion integrations**: Slack, email, calendar, web crawling
- **Policy overlays**: Scoping, sharing, visibility controls
- **Multiple indices**: Per-scope indices for stronger isolation
- **Cloud model fallback**: OpenAI/Anthropic when Ollama unavailable

---

## Verification

### Per-Phase Verification

| Phase | Verification |
|-------|--------------|
| 1-2 | `docker compose up` succeeds; `docker compose exec exobrain exobrain --help` returns docs |
| 3 | Create raw doc; run `exobrain stage --all`; verify staged doc exists |
| 4 | Run `exobrain index --incremental`; verify artifacts in `graphrag/output/` |
| 5 | Run `exobrain query --mode global --q "test"`; get response |
| 6 | `curl http://localhost:8420/health` returns OK |
| 7 | Add file to raw/; observe automatic staging within 5 seconds |
| 8 | Run `/ideate` in Claude Code; verify data lands in ExoBrain |
| 9 | Run migration; compare document counts; spot-check content |

### End-to-End Acceptance Test

1. Clone repo on fresh machine
2. Copy `.env.example` to `.env`; set `EXOBRAIN_DATA_DIR=~/Dropbox/ExoBrain`
3. Run `docker compose up -d`
4. Run `docker compose exec exobrain exobrain init`
5. Create `${EXOBRAIN_DATA_DIR}/raw/019c0000-test.md` with any content
6. Wait for watcher to stage it (check `staged/` folder)
7. Add overlay: `echo '{"v":1,"id":"019c0001","ts":"2026-01-24T00:00:00Z","doc_id":"019c0000","source":"human","title":"Test Document"}' >> ${EXOBRAIN_DATA_DIR}/overlay/annotations/2026-01-24.jsonl`
8. Run `docker compose exec exobrain exobrain stage --all`
9. Run `docker compose exec exobrain exobrain index --incremental`
10. Run `docker compose exec exobrain exobrain query --mode global --q "test"`
11. Verify response is grounded in the test document

---

## References

- **v2 Design Spec**: `docs/active/20260123-exobrain-v2-memory-system-design-plan-chatgpt.md`
- **Detailed Phase Plan**: `/Users/tbj/.claude/plans/glimmering-twirling-kettle.md`
- **Superseded CLI Plan**: `docs/active/20260117-exobrain-cli-implementation-plan-claude.md` (mark deprecated)
- **Superseded ADR**: `docs/adr/001-exobrain-workspace-structure-and-schema.md` (mark deprecated)

**Future ADR to generate**: Consider creating ADR for "ExoBrain v2 Architecture" once implementation stabilizes.
