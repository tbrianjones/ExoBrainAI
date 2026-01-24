# Claude Writer + ExoBrain

Two-layer personal knowledge system:

1. **ExoBrain** ; GraphRAG memory engine (Docker-based, local LLM)
2. **Claude Writer** ; Ideation and content generation (Claude Code commands)

## ExoBrain Quick Reference

```bash
# Start the engine
docker compose up -d

# Capture a thought
echo "My idea..." | docker compose exec -T exobrain exobrain capture

# Query your memory
docker compose exec exobrain exobrain query "What themes emerge?"

# Check status
docker compose exec exobrain exobrain status
```

**Endpoints:**
- API: http://localhost:8420
- Logs: http://localhost:9998 (Dozzle)

**Data locations:**
- `$EXOBRAIN_DATA_DIR` ; Canonical data (raw/, overlay/) ; syncs via Dropbox
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
| `/instantiate-idea` | Create folder structure; usually called by /ideate |
| `/generate-transcript` | User wants to capture current conversation |
| `/generate-view` | User wants production content from an idea |
| `/generate-poem-view` | User wants poetry; uses Poetic Inquiry methodology |
| `/generate-academic-infographic-view` | User wants data-focused, academically rigorous infographic specs |
| `/generate-new-view-command` | User wants to create a new specialized view generator |
| `/publish-quarto` | Publish a view to ideas.tbrianjones.com |

## Agents

| Agent | Invocation |
|-------|------------|
| `transcript-summary-generator` | Called by `/generate-transcript`; produces synthesized Ideas & Themes |
| `transcript-raw-generator` | Called by `/generate-transcript`; produces verbatim Full Transcript |

## Skills

| Skill | Purpose |
|-------|---------|
| `exobrain` | Interface with ExoBrain memory engine (CLI and API) |
| `title-generation` | Generate effective titles and headlines |
| `summary-generation` | Generate summaries, abstracts, briefs |
| `tag-generation` | Generate tags, hashtags, and classifications |

## Repository Structure

```
├── engine/                 # ExoBrain memory engine
│   └── src/
│       ├── core/           # Models, raw ops, overlay ops, stager
│       ├── graphrag/       # GraphRAG config, indexer, querier
│       ├── cli/            # Typer CLI commands
│       ├── api/            # FastAPI routes
│       └── watcher/        # File watcher, scheduler
├── .claude/
│   ├── commands/           # User-invoked commands
│   ├── agents/             # Autonomous subagents
│   └── skills/             # exobrain, title-generation, etc.
├── ideas/NNNN-name/        # Legacy idea spaces (migrating to ExoBrain)
│   ├── README.md
│   ├── assets/
│   ├── transcripts/
│   └── views/
├── templates/
│   ├── voices/             # Writing voice/style references
│   ├── poetry/             # Poetry generation frameworks
│   ├── infographics/       # Infographic generation frameworks
│   └── ...
├── site/                   # Quarto site for publishing
├── docker-compose.yml
└── .env.example
```

## ExoBrain CLI Commands

Run via: `docker compose exec exobrain exobrain <command>`

| Command | Description |
|---------|-------------|
| `init` | Create directories, pull Ollama models |
| `status` | Show document counts, index status |
| `doctor` | Validate config, check Ollama connectivity |
| `capture [content]` | Capture new document (stdin or argument) |
| `stage --all` | Stage all documents |
| `stage --doc <id>` | Stage specific document |
| `index` | Run incremental GraphRAG update |
| `rebuild` | Full index rebuild |
| `query "<text>"` | Global (theme) query |
| `query --mode local "<text>"` | Local (entity) query |
| `migrate <path>` | Migrate from ideas/ (dry-run by default) |

## ExoBrain HTTP API

Base: `http://localhost:8420`

```
GET  /health                 # Health check
GET  /status                 # Full status
POST /query/global           # Theme query
POST /query/local            # Entity query
GET  /doc/                   # List documents
GET  /doc/{id}               # Get document
GET  /doc/{id}/overlay       # Get overlay data
POST /admin/stage            # Trigger staging
POST /admin/index/incremental
POST /admin/index/rebuild
```

## Working in Idea Spaces

Before generating content in `ideas/NNNN-name/`:

1. Read `README.md`
2. Read all files in `transcripts/`
3. Read all files in `assets/`
4. Scan `views/` for existing voice/style patterns

Commands `/generate-view`, `/generate-poem-view`, and `/generate-academic-infographic-view` do this automatically.

## Style Rules

- **No dashes or double dashes.** Use semicolons or restructure.
- **Semicolons** join related independent clauses.
- **Ellipses** for trailing off (use sparingly).
- Preserve human's phrasing when it captures the idea.
- Avoid flowery language.

## Behavior

- Always do work in feature branches. Propose this as soon as you launch.
- **Infrastructure as code.** Never configure infrastructure manually. All configuration in repository files, version controlled, deployed via push.
