# ADR 001: ExoBrain v2 GraphRAG Memory Engine

- **Status:** Accepted
- **Date:** 2026-01-24
- **Updated:** 2026-01-24
- **Tags:** architecture, infrastructure, graphrag, local-first
- **Impact:** High

## Context

ExoBrain is a local-first personal knowledge system. V1 attempted to implement everything in a file structure with YAML frontmatter in markdown files, IDs linking documents to each other, and GitHub as the versioning layer. This approach became unmanageable: files on disk with embedded IDs felt messy, linking was fragile, and the structure was difficult to maintain.

V2 redesigns the system around two distinct memory layers:

1. **Hard Memory Layer**: Raw data stored as plain markdown files and append-only JSONL overlay annotations. Simple, human-readable, portable, and sync-friendly (Dropbox/iCloud).

2. **Searchable Memory Layer**: GraphRAG-powered knowledge graph built from the hard memory layer. Regenerable at any time from the canonical raw data.

This separation means raw data survives technology changes. As memory engines evolve (GraphRAG today, something better tomorrow), the raw data can always be reparsed into new systems.

## Decision Drivers

1. **Permanent raw data store**: Need a format that survives decades and can feed into any future system, including human readers
2. **Zero-friction capture**: No decisions required at capture time; structure added later via overlays
3. **Upgrade path flexibility**: Memory engines will evolve; raw data must remain constant
4. **Circular annotation capability**: AI can analyze raw data and generate meta-annotations (summaries, entity links, confidence scores) that feed back into the overlay layer
5. **Local-first privacy**: Data stays on user's machine; only explicit LLM calls touch external services
6. **Sync-friendly**: Must work with Dropbox/iCloud without conflicts
7. **Confidence scoring**: Both full annotation objects and individual items (tags, entities) need granular confidence levels

## Considered Options

### Overlay Format

1. **YAML frontmatter in markdown files** (V1 approach)
   - Rejected: Mixes content with metadata, makes raw docs messy, difficult to link documents, hard to maintain

2. **Single JSONL file for all annotations**
   - Rejected: File grows unbounded, harder to sync, no natural partitioning

3. **Per-document JSON sidecar files**
   - Rejected: Doubles file count, complex to manage, harder to scan for cross-document queries

4. **Date-partitioned append-only JSONL** (chosen)
   - Append-only semantics; never edit, only add
   - Human-readable and debuggable
   - Sync-friendly (new lines append, no conflicts)
   - Natural partitioning by date
   - Same JSON schema repeated; super simple structure
   - Supports both full objects (human-authored) and individual records (AI-generated tags with scores)

### Storage Engine

GraphRAG (Microsoft) was chosen as the initial searchable memory layer. LlamaIndex, LangChain, and similar tools are not alternatives to the overlay format; they are storage engines that the overlay data parses INTO. The architecture explicitly separates raw data (canonical) from indexed data (derived).

### Deployment

Docker Compose with Ollama for local LLM inference. This keeps all processing local while enabling frontier-model-equivalent capabilities for entity extraction, summarization, and community detection.

## Decision Outcome

Chosen option: **Date-partitioned append-only JSONL overlays with Docker-based GraphRAG indexing**

The system separates into:

- **Canonical data** (`$EXOBRAIN_DATA_DIR`, syncs via Dropbox):
  - `raw/{uuidv7}.md`: Plain markdown documents
  - `overlay/annotations/{date}.jsonl`: Append-only annotation records

- **Derived data** (`$EXOBRAIN_CACHE_DIR`, container volume):
  - `staged/{uuidv7}.md`: Merged raw + aggregated overlays
  - `graphrag/`: Index artifacts (parquet files, embeddings)
  - `logs/`: Application logs

Staging aggregates all overlay records for a document into a single view. GraphRAG indexes the staged documents. Everything in the cache is regenerable from canonical data.

## Consequences

### Positive

- **Extreme simplicity**: Entire raw system reduces to markdown files + JSONL with one repeated schema
- **Flexibility**: Full JSON objects or individual records; human-authored or AI-generated
- **Granular scoring**: Confidence levels at object level or individual item level
- **Future-proof**: Raw data survives any technology change; reparse into new engines
- **Circular annotation**: AI can generate meta-annotations that feed back into overlays
- **Portable**: Copy `raw/` and `overlay/` to move entire knowledge base
- **Debuggable**: Human-readable files; inspect with any text editor
- **Local-first**: Data never leaves machine except explicit LLM calls

### Negative

- **Query scanning**: Date-partitioned JSONL requires scanning multiple files to find all annotations for a document (mitigated by overlay window configuration)
- **No schema enforcement at write**: Append-only means malformed data can accumulate (mitigated by Pydantic validation in API/CLI)
- **Docker overhead**: Requires Docker Desktop running; not a single binary
- **Ollama memory**: Local LLM requires significant RAM (8GB+ for Llama 3.1 8B)
- **Eventual consistency**: File watcher has debounce delay; changes not immediately indexed

### Neutral

- **AI circular annotation not yet implemented**: Planned as integration layer; schema supports it via `source: "ai"` field

## Agent Rules

1. **MUST** use UUIDv7 for document IDs. See `engine/src/core/raw.py:generate_doc_id()` which calls `uuid_extensions.uuid7()`.

2. **MUST** append overlay records; NEVER edit existing JSONL lines. See `engine/src/core/overlay.py:append_overlay()` which opens files in append mode.

3. **MUST** use `OverlayRecord` model for all annotations. See `engine/src/core/models.py:39-58` for schema definition.

4. **MUST** set `source` field to one of: `human`, `ai`, `system`, `import`. This enables filtering by annotation origin.

5. **MUST** regenerate staged documents after overlay changes. Staged files are derived; call `stage_doc()` or `stage --all` after annotations.

6. **NEVER** store derived data in `$EXOBRAIN_DATA_DIR`. Only `raw/` and `overlay/` are canonical. See `engine/src/config.py` for directory structure.

7. **SHOULD** include confidence scores for AI-generated annotations. See `TagItem`, `EntityItem`, `LinkItem` models which all support `confidence: float | None`.

8. **SHOULD** use `--link` and `--link-note` together when creating document relationships. See `engine/src/cli/main.py:annotate` command.

## References

- PRD: `docs/active/20260123-exobrain-v2-graphrag-memory-engine-prd-chatgpt.md`
- Development Plan: `docs/active/20260124-exobrain-v2-graphrag-memory-engine-dev-plan-claude.md`
- GraphRAG: https://github.com/microsoft/graphrag
- UUIDv7: https://www.rfc-editor.org/rfc/rfc9562.html
