# ExoBrain Engine

Local-first personal knowledge system backed by SQLite. Everything is an object; objects have types, live in spaces, carry tags, link to each other, and can hold file attachments.

## Quick Start

```bash
# From repository root
cp .env.example .env
# Edit .env to set EXOBRAIN_DATA_DIR

docker compose up -d
docker compose exec exobrain exobrain init
docker compose exec exobrain exobrain status
```

## CLI Commands

Run via: `docker compose exec exobrain exobrain <command>`

### System

| Command | Description |
|---------|-------------|
| `init` | Create database, run migrations, bootstrap types/spaces |
| `status` | Show object counts, DB size, integrity |
| `doctor` | Validate integrity, check for orphaned files |
| `version` | Show version |

### Objects

| Command | Description |
|---------|-------------|
| `capture [content]` | Capture a new object (content via argument or stdin) |
| `get <id>` | Show full object detail (tags, links, file) |
| `list` | List objects with optional filters |
| `update <id>` | Update title, summary, content, or space |
| `delete <id>` | Delete object and all related data |
| `search <query>` | Full-text search across title, summary, content |

### Tags, Links, Files

| Command | Description |
|---------|-------------|
| `tag add <id> <tag>` | Add a tag to an object |
| `tag remove <id> <tag>` | Remove a tag |
| `tag list` | List all tags with usage counts |
| `link create <from> <to> <rel>` | Create a directed link |
| `link list <id>` | List all links for an object |
| `link remove <link-id>` | Remove a link |
| `file attach <id> <path>` | Attach a file to an object |
| `file detach <id>` | Remove file attachment |
| `file path <id>` | Print full path to attached file |

### Types and Spaces

| Command | Description |
|---------|-------------|
| `type list` | List all object types |
| `type create <name>` | Create a new type |
| `space list` | List all spaces |
| `space create <name>` | Create a new space (auto-creates parents for `a/b/c`) |

### GraphRAG (optional)

| Command | Description |
|---------|-------------|
| `graphrag stage` | Stage SQLite objects as text files for GraphRAG |
| `graphrag index` | Run GraphRAG indexing |
| `graphrag query <text>` | Query the GraphRAG index |

All commands support `--json` for machine-readable output. Object IDs can be shortened to a unique prefix (minimum 8 characters).

## API Endpoints

Base: `http://localhost:8420`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | System status (objects, types, integrity) |
| `/query/global` | POST | Global/theme query (GraphRAG) |
| `/query/local` | POST | Local/entity query (GraphRAG) |
| `/doc/` | GET | List documents |
| `/doc/{id}` | GET | Get document |
| `/admin/stage` | POST | Trigger staging |
| `/admin/index/incremental` | POST | Incremental index |
| `/admin/index/rebuild` | POST | Full rebuild |

## Data Model

- **Objects**: Core entity. Has type, space, title, summary, content, timestamps.
- **Types**: Bootstrap types: Type, Space, Tag, Document, Transcript, Note, URL. User-extensible.
- **Spaces**: Hierarchical organization (`work/exobrain`). Default capture space: Inbox.
- **Tags**: Free-text labels on objects.
- **Links**: Directed, labeled relationships between objects.
- **Files**: At most one file attachment per object, stored in sharded directories.

## Development

Tests run inside Docker:

```bash
# Build and start the container
docker compose up -d --build

# Run the test suite
docker compose exec exobrain python -m pytest tests/ -v

# Run a specific test file
docker compose exec exobrain python -m pytest tests/test_repository.py -v
```
