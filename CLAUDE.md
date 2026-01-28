# Claude Writer + ExoBrain

Two-layer personal knowledge system:

1. **ExoBrain** ; SQLite-backed knowledge engine (everything is an object)
2. **Claude Writer** ; Ideation and content generation (Claude Code commands)

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
| `exobrain` | Interface with ExoBrain knowledge system (SQLite + CLI) |
| `title-generation` | Generate effective titles and headlines |
| `summary-generation` | Generate summaries, abstracts, briefs |
| `tag-generation` | Generate tags, hashtags, and classifications |

## Repository Structure

```
├── engine/                 # ExoBrain knowledge engine
│   └── src/
│       ├── core/           # DB, schema, models, bootstrap, repository
│       ├── graphrag/       # GraphRAG config, indexer, querier, adapter
│       ├── cli/            # Typer CLI commands
│       ├── api/            # FastAPI routes
│       └── watcher/        # File watcher
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
| `capture [CONTENT]` | Create object; `--title`, `--type`, `--space`, `--tag`, `--file` |
| `get ID` | Full object detail with tags, links, file info |
| `list` | Filter: `--type`, `--space`, `--tag`, `--limit`, `--offset` |
| `update ID` | `--title`, `--summary`, `--content`, `--space` |
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

### GraphRAG (Optional)

| Command | Description |
|---------|-------------|
| `graphrag stage` | Stage SQLite objects for GraphRAG |
| `graphrag index` | Run GraphRAG indexing |
| `graphrag query "text"` | Query the GraphRAG index |

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
