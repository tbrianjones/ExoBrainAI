# ADR 001: ExoBrain v2 GraphRAG Memory Engine

- **Status:** Accepted
- **Date:** 2026-01-24
- **Updated:** 2026-01-25
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
  - `staged/{uuidv7}.txt`: Merged raw + aggregated overlays
  - `graphrag/output/`: Index artifacts (parquet files, GraphML)
  - `graphrag/cache/`: LLM response cache
  - `logs/`: Application logs

Staging aggregates all overlay records for a document into a single view. GraphRAG indexes the staged documents. Everything in the cache is regenerable from canonical data.

## Infrastructure Requirements

### Ollama Deployment Options

**CRITICAL**: Ollama in Docker on Mac runs on CPU only (no GPU access). This is 20-30x slower than native. For production use, install Ollama natively.

| Deployment | Tokens/sec | Recommended For |
|------------|-----------|-----------------|
| Native Ollama (Mac) | 30-50 | Production indexing |
| Docker Ollama (Mac) | 1-2 | Testing only |

#### Option A: Native Ollama (Recommended)

1. Set in `.env`: `OLLAMA_MODE=native`
2. Run setup script: `./scripts/setup-native-ollama.sh`
3. Start containers: `docker compose up -d`

The setup script installs Ollama via Homebrew, starts the service, and pulls required models.

#### Option B: Docker Ollama (Testing Only)

1. Set in `.env`: `OLLAMA_MODE=docker`
2. Start with profile: `docker compose --profile docker up -d`

Only use this for basic testing; indexing will be too slow for real data.

### Docker Desktop Memory

If using Docker Ollama, Docker Desktop must be configured with adequate memory:

| Model | Minimum Docker RAM | Recommended |
|-------|-------------------|-------------|
| llama3.2:3b | 6GB | 8GB |
| llama3.1:8b | 10GB | 12GB |

On a 16GB Mac, allocate 10GB to Docker (Settings → Resources → Memory). This leaves 6GB for macOS.

**Failure mode**: If Docker has insufficient memory, Ollama loads the model successfully but the runner process is killed during inference with "signal: killed". The indexing appears to stall at `extract_graph` or `community_reports` with no error message.

### Ollama Configuration

Critical environment variables in `docker-compose.yml`:

```yaml
environment:
  - OLLAMA_CONTEXT_LENGTH=8192    # Minimum for community_reports
  - OLLAMA_KV_CACHE_TYPE=fp16     # Faster on Apple Silicon
  - OLLAMA_KEEP_ALIVE=30m         # Keep model loaded between calls
```

### GraphRAG v2.x Configuration

Key settings in `engine/src/graphrag/config.py`:

| Setting | Value | Rationale |
|---------|-------|-----------|
| `model_supports_json` | `False` | Local models don't reliably produce valid JSON |
| `request_timeout` | `1200.0` | Community reports take 2-3 min each |
| `max_retries` | `2` | Fewer retries; each wastes timeout budget |
| `chunks.size` | `300` | Smaller chunks improve entity extraction |
| `community_reports.max_input_length` | `4000` | Must fit in 8K context with output |

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
- **No GPU access in Docker on Mac**: Ollama in Docker runs on CPU only (20-30x slower); requires native Ollama for production use
- **Significant RAM requirements**: Docker Desktop needs 10GB+ for llama3.1:8b; on 16GB machines, this constrains other applications during indexing
- **Long indexing times**: Community reports generation takes 2-3 minutes per community; a 50-document index may take 1-2 hours
- **Silent OOM failures**: Insufficient Docker memory causes model runner to be killed without clear error messages
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

9. **MUST** verify Docker Desktop has 10GB+ memory before running indexing with llama3.1:8b. Check with `docker system info | grep "Total Memory"`.

10. **MUST** clear GraphRAG cache after changing `engine/src/graphrag/config.py`. Settings are written to `settings.yaml` on first run; delete `/cache/graphrag/settings.yaml` to regenerate.

11. **SHOULD** test indexing with `--method fast` (NLP-based) before attempting full LLM indexing to verify pipeline works end-to-end.

12. **MUST NOT** set `model_supports_json: True` for Ollama models. Local models produce malformed JSON that causes silent entity extraction failures.

13. **MUST** use native Ollama on Mac for production indexing. Docker Ollama runs on CPU only (1-2 tok/sec vs 30-50 tok/sec native). Set `OLLAMA_MODE=native` in `.env` and run `./scripts/setup-native-ollama.sh`.

14. **SHOULD** run `exobrain stage --all` after modifying overlay files. The watcher currently does not auto-restage on overlay changes (known limitation).

15. **MUST** regenerate `settings.yaml` after changing entity types. Delete `/cache/graphrag/settings.yaml` and run `exobrain init` to apply new entity type configuration.

## References

- PRD: `docs/active/20260123-exobrain-v2-graphrag-memory-engine-prd-chatgpt.md`
- Development Plan: `docs/active/20260124-exobrain-v2-graphrag-memory-engine-dev-plan-claude.md`
- Best Practices: `docs/active/graphrag-ollama-best-practices.md`
- GraphRAG: https://github.com/microsoft/graphrag
- GraphRAG Configuration: https://microsoft.github.io/graphrag/config/yaml/
- UUIDv7: https://www.rfc-editor.org/rfc/rfc9562.html
