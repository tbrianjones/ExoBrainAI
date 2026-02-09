# ExoBrain

Personal knowledge system with SQLite-backed storage (everything is an object) and Claude Code commands for ideation and content generation.

## ExoBrain Quick Reference

```bash
# Start the engine
docker compose up -d

# Initialize (first time)
docker compose exec exobrain exobrain init

# Capture a thought
docker compose exec exobrain exobrain capture "My idea..." --title "Insight" --type note --tag brainstorm

# Search your memory
docker compose exec exobrain exobrain search "idea"

# List objects
docker compose exec exobrain exobrain list --type note --tag brainstorm

# Check status
docker compose exec exobrain exobrain status
```

**All CLI commands support `--json` for structured output.**

**Endpoints:**
- API: http://localhost:8420
- Web UI: http://localhost:8420/ui/
- Logs: http://localhost:9998 (Dozzle)

**Data locations:**
- `$EXOBRAIN_DATA_DIR` ; Canonical data (exobrain.db, files/) ; syncs via Dropbox
- Container volume ; Derived data (staged/, graphrag/) ; regenerable

## Commands vs Agents vs Skills

| Type | Behavior |
|------|----------|
| **Commands** | Interview the user, have dialogue, require input |
| **Agents** | Run autonomously in their own context, no further input needed |
| **Skills** | Utilities invoked by commands or agents (not directly by users) |

## Commands

| Command | When to Use |
|---------|-------------|
| `/ideate` | User wants to explore an idea (new or existing) |
| `/instantiate-idea` | Create a new idea space in ExoBrain; usually called by /ideate |
| `/generate-transcript` | User wants to capture current conversation |
| `/generate-view` | User wants production content from an idea |
| `/generate-poem-view` | User wants poetry; uses Poetic Inquiry methodology |
| `/generate-academic-infographic-view` | User wants data-focused, academically rigorous infographic specs |
| `/generate-episode-outline` | Generate Zengineering podcast pre-production outlines from brainstorm transcripts |
| `/generate-new-view-command` | User wants to create a new specialized view generator |
| `/publish-quarto` | Publish a view to ideas.tbrianjones.com |
| `/test-system` | Run end-to-end integration test simulating a real user session |

## Agents

| Agent | Invocation |
|-------|------------|
| `transcript-summary-generator` | Called by `/generate-transcript`; produces synthesized Ideas & Themes |
| `transcript-raw-generator` | Called by `/generate-transcript`; produces verbatim Full Transcript |

## Skills

| Skill | Purpose |
|-------|---------|
| `exobrain` | Interface with ExoBrain knowledge system (SQLite + CLI) |
| `title-generation` | Generate effective titles and headlines |
| `summary-generation` | Generate summaries, abstracts, briefs |
| `tag-generation` | Generate tags, hashtags, and classifications |

## Repository Structure

```
├── engine/                 # ExoBrain knowledge engine
│   ├── src/
│   │   ├── core/           # DB, schema, models, bootstrap, repository, projection
│   │   ├── graphrag/       # GraphRAG config, indexer, querier, adapter
│   │   ├── cli/            # Typer CLI commands
│   │   ├── api/            # FastAPI routes
│   │   └── watcher/        # File watcher
│   └── tests/              # pytest unit tests + fixtures/
├── .claude/
│   ├── commands/           # User-invoked commands
│   ├── agents/             # Autonomous subagents
│   └── skills/             # exobrain, title-generation, etc.
├── templates/
│   ├── voices/             # Writing voice/style references
│   ├── poetry/             # Poetry generation frameworks
│   ├── infographics/       # Infographic generation frameworks
│   └── ...
├── docs/
│   └── adr/                # Architecture Decision Records (001-010)
├── site/                   # Quarto site for publishing
├── docker-compose.yml
└── .env.example
```

## ExoBrain CLI Commands

Run via: `docker compose exec exobrain exobrain <command>`

### System

| Command | Description |
|---------|-------------|
| `init` | Create DB, run migrations, bootstrap types/spaces |
| `status` | Object counts, DB size, integrity |
| `doctor` | Validate DB integrity, check orphaned files |
| `version` | Show version |

### Objects

| Command | Description |
|---------|-------------|
| `capture [CONTENT]` | Create object; `--title`, `--type`, `--space`, `--tag`, `--file`, `--created-at`, `--always-project` |
| `get ID` | Full object detail with tags, links, file info |
| `list` | Filter: `--type`, `--space`, `--tag`, `--limit`, `--offset` |
| `update ID` | `--title`, `--summary`, `--content`, `--space`, `--always-project`, `--never-project`, `--auto-project` |
| `delete ID` | Delete with confirmation (`--yes` to skip) |
| `search QUERY` | FTS5 search across title, summary, content |

### Tags, Links, Types, Spaces, Files

| Command | Description |
|---------|-------------|
| `tag add ID TAG` | Add tag to object |
| `tag remove ID TAG` | Remove tag from object |
| `tag list` | All tags with counts |
| `link create FROM TO REL` | Link two objects |
| `link list ID` | Show links for object |
| `link remove LINK_ID` | Remove link |
| `type list` | List all types |
| `type create NAME` | Create new type |
| `space list` | List all spaces |
| `space create NAME` | Create space (auto-creates parents) |
| `file attach ID PATH` | Attach file to object |
| `file detach ID` | Remove file |
| `file path ID` | Print file path |

### Projection

| Command | Description |
|---------|-------------|
| `project` | Project objects to `$EXOBRAIN_DATA_DIR/projected/` as markdown |
| `project --cleanup` | Recalculate scores, remove stale projections |
| `project --dry-run` | Preview what would be projected |
| `sync [FILE]` | Sync edited projected files back to SQLite (all files if no path given) |
| `tier status` | Show projection statistics (counts, top scores, overrides) |

Projected files have YAML frontmatter and support bidirectional sync. Edit projected files, then run `sync` to write changes back to SQLite. Fields `id` and `space` are immutable.

### GraphRAG (Optional)

| Command | Description |
|---------|-------------|
| `graphrag stage` | Stage SQLite objects for GraphRAG |
| `graphrag index` | Run GraphRAG indexing |
| `graphrag query "text"` | Query the GraphRAG index |

## Working with Idea Spaces

Idea spaces live in ExoBrain under the `ideas/` space hierarchy. Commands use a hybrid pattern: projected files for reads, CLI for writes.

**Loading context** (reading from an idea space):
1. Refresh projection: `docker compose exec exobrain exobrain project`
2. Read `.env` to find `EXOBRAIN_DATA_DIR`
3. Read projected files from `$EXOBRAIN_DATA_DIR/projected/ideas/{space-name}/*.md`
4. Each file has YAML frontmatter (id, type, space, title, summary, tags, dates) + content body

**Creating content** (writing to an idea space):
```bash
echo "[content]" | docker compose exec -T exobrain exobrain capture \
  --title "Title" --type document --space "ideas/space-name" \
  --tag view --tag draft --always-project --json
docker compose exec exobrain exobrain project
```

**Linking provenance**: When creating content in an idea space (views, documents, responses), always link the new object back to its sources using `derived-from` for transcripts and concepts it was generated from, and `references` for specific objects it cites. This applies both inside commands and in ad-hoc creation.

**Discovering spaces**: `docker compose exec exobrain exobrain space list --json` (filter for `ideas/`)

Commands `/generate-view`, `/generate-poem-view`, and `/generate-academic-infographic-view` handle this automatically.

## Style Rules

- **No dashes or double dashes.** Use semicolons or restructure.
- **Semicolons** join related independent clauses.
- **Ellipses** for trailing off (use sparingly).
- Preserve human's phrasing when it captures the idea.
- Avoid flowery language.

## Object Types

Bootstrap types (always available): `Document`, `Note`, `Transcript`, `URL`, `Concept`, `Event`, `Person`, `Project`. Create custom types with `type create`.

## Architecture Decision Records

ADRs document key architectural choices. Read these before making significant changes:

| ADR | Decision |
|-----|----------|
| [001](docs/adr/001-exobrain-v2-graphrag-memory-engine.md) | GraphRAG memory engine (superseded; deferred to Phase 6) |
| [002](docs/adr/002-sqlite-core-memory-layer.md) | SQLite as core memory layer; repository pattern; FTS5 |
| [003](docs/adr/003-exobrain-cli-architecture.md) | CLI as sole write interface |
| [004](docs/adr/004-claude-code-first-ui.md) | Claude Code as first UI |
| [005](docs/adr/005-api-layer.md) | API layer (partially superseded by ADR-010) |
| [006](docs/adr/006-information-centric-computing-vision.md) | Information-centric computing vision |
| [007](docs/adr/007-projection-layer-architecture.md) | Projection layer with hot tier scoring and bidirectional sync |
| [008](docs/adr/008-agentic-testing-strategy.md) | Three-tier testing: unit tests + agentic integration + fixtures |
| [009](docs/adr/009-schema-migration-and-data-durability.md) | Forward-only migrations; `init` safe on any DB state |
| [010](docs/adr/010-web-ui-architecture.md) | Read-only web UI with Jinja2 + HTMX + Tailwind; integrated into FastAPI on `/ui/` |
| [011](docs/adr/011-primitive-semantics-and-knowledge-gardening.md) | Primitive semantic roles (spaces, types, tags, links); emergent taxonomy; knowledge gardening vision |

## Behavior

- Always do work in feature branches. Propose this as soon as you launch.
- **Infrastructure as code.** Never configure infrastructure manually. All configuration in repository files, version controlled, deployed via push.
