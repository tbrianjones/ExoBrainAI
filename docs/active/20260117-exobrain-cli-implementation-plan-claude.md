---
status: Planning
date: 2026-01-17
branch: feature/exobrain-cli
related-adrs: [001]
---

# ExoBrain CLI Implementation Plan

## Summary

Build the Python CLI (`exobrain`) that enforces workspace structure, manages document/space creation with proper UUIDs, validates schemas, and handles migrations. This is the foundational software layer that all Claude agents will call instead of writing files directly, making the system trustworthy and shareable.

## Agent Quick Start

> Read this section first if you're an AI agent picking up this plan.

**Load these files:**
- `docs/adr/001-exobrain-workspace-structure-and-schema.md` (the authoritative spec)
- `scripts/gemini.py` (example of existing Python CLI pattern)
- `.claude/commands/instantiate-idea.md` (will be updated to call exobrain CLI)

**Read these ADRs:**
- ADR-001: ExoBrain Workspace Structure and Schema (full specification)

**Relevant skills:**
- None directly; this is core infrastructure

**Explore these areas:**
- `ideas/` - current structure to understand migration source
- `.claude/commands/` - commands that will integrate with CLI
- `scripts/` - where CLI will live initially

**Key constraints:**
- Follow ADR-001 Agent Rules exactly
- All document creation MUST generate valid frontmatter
- UUIDs must be UUIDv7 (time-sortable)
- 8-char prefix for space folders, full UUID in frontmatter
- Terminal types require `derived_from`; non-terminal types don't

## Problem Statement

- **User Persona:** Developer using Claude Code to manage ideas and generate content
- **Pain Point:** Current ideas folder is fragile; agents can create arbitrary structures with no enforcement; no machine-readable metadata; can't share publicly because personal content is mixed with app code
- **Current State:** Manual folder creation, prose-only README files, sequential NNNN IDs that collide across collaborators, no validation
- **Business Impact:** Can't trust the system enough to use it heavily; can't share with others; can't build reliable tooling on top

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Validation pass rate | N/A (no validation) | 100% of new docs | `exobrain validate` returns clean |
| Schema consistency | 0% (no schema) | 100% required fields present | Automated validation |
| ID collisions | Possible | Impossible (UUIDv7) | No duplicate IDs across workspaces |
| Test coverage | 0% | >80% for core CLI | pytest coverage report |

## Feature Overview

The `exobrain` CLI is a Python command-line tool that:
1. Initializes workspaces (cloning or creating git repos)
2. Creates spaces and documents with proper UUIDs and frontmatter
3. Validates all documents against the schema
4. Manages schema migrations
5. Handles git sync operations

All Claude agents will call this CLI via Bash instead of writing files directly.

### Core User Flow

1. User clones the exobrain app repo
2. User runs `exobrain init` which:
   - Checks prerequisites (git, gh CLI, Claude Code)
   - Captures user identity (name, email)
   - Asks for existing workspace repo URL or creates new
   - Clones/creates workspace at standard location
   - Saves config to app `.env`
3. User opens Claude Code in the app repo
4. Claude agents call `exobrain doc create`, `exobrain space create`, etc.
5. All documents have valid frontmatter, proper UUIDs, pass validation

## Scope

### In Scope

- Python CLI package in `scripts/exobrain/`
- `exobrain init` - workspace setup wizard
- `exobrain space create` - create new idea space
- `exobrain doc create` - create document with frontmatter
- `exobrain doc update` - update document metadata
- `exobrain validate` - validate workspace against schema
- `exobrain migrate` - run schema migrations
- `exobrain sync` - commit and push to remote
- `exobrain status` - show workspace state
- Pydantic models for schema validation
- pytest test suite with >80% coverage
- Migration of existing `ideas/` folder to new structure

### Out of Scope (Do Not Build)

- MCP server integration (future)
- Web UI or desktop app (future)
- Templates system (future)
- Integrations (Twitter, site publishing automation) (future)
- Space types (constraining doc types per space) (future)
- Full graph/link model beyond `derived_from` (future)
- `exobrain doc delete` (can use git revert; avoid destructive ops in v1)

### Dependencies

- Python 3.10+
- Pydantic for schema validation
- Click or Typer for CLI framework
- GitPython or subprocess for git operations
- pytest for testing
- GitHub CLI (`gh`) installed on user machine
- Git installed and configured

## User Stories + Acceptance Criteria

### Story 1: Initialize Workspace

**As a** new user, **I want** to run `exobrain init` **so that** I have a properly configured workspace ready to use.

**Acceptance Criteria:**
- [ ] Given git is not installed, when I run `exobrain init`, then I see an error with install instructions
- [ ] Given gh CLI is not installed, when I run `exobrain init`, then I see an error with install instructions
- [ ] Given prerequisites pass, when I run `exobrain init`, then I'm prompted for my name and email
- [ ] Given I provide an existing GitHub repo URL, when init completes, then the repo is cloned to the workspace location
- [ ] Given I choose to create new workspace, when init completes, then a new repo is created and pushed to GitHub
- [ ] Given init completes, when I check `.env`, then my user identity is saved
- [ ] Given init completes, when I check the workspace, then `workspace.yml` and `types.yml` exist

### Story 2: Create Space

**As a** user, **I want** to run `exobrain space create --slug "my-idea"` **so that** I have a new idea space with proper structure.

**Acceptance Criteria:**
- [ ] Given I run `exobrain space create --slug "my-idea"`, when it completes, then a folder `{8-char-uuid}-my-idea/` exists
- [ ] Given the space is created, when I check `README.md`, then it has valid frontmatter with full UUID, type "space", schema_version
- [ ] Given I try to create a space with an existing slug, when I run the command, then I get a warning (not an error; UUIDs differ)

### Story 3: Create Document

**As a** Claude agent, **I want** to call `exobrain doc create --space {uuid} --type brief --title "My Brief"` **so that** documents have proper frontmatter.

**Acceptance Criteria:**
- [ ] Given valid parameters, when doc is created, then it has all required frontmatter fields
- [ ] Given type is "brief" (terminal), when `--derived-from` is missing, then creation fails with error
- [ ] Given type is "transcript" (non-terminal), when `--derived-from` is missing, then creation succeeds
- [ ] Given `--derived-from` is provided, when doc is created, then the field contains the provided UUIDs
- [ ] Given the command succeeds, when I check the file, then `id` is a valid UUIDv7
- [ ] Given `--content` flag or stdin, when doc is created, then body content is included after frontmatter
- [ ] Given `--json` flag, when command completes, then output is JSON with doc metadata

### Story 4: Validate Workspace

**As a** user, **I want** to run `exobrain validate` **so that** I can verify all documents conform to schema.

**Acceptance Criteria:**
- [ ] Given all documents are valid, when I run `exobrain validate`, then exit code is 0 and output says "All documents valid"
- [ ] Given a document is missing required field, when I run validate, then I see the file path and missing field
- [ ] Given a document has unknown type, when I run validate, then I see an error about invalid type
- [ ] Given a terminal type doc is missing `derived_from`, when I run validate, then I see an error
- [ ] Given `--fix` flag, when fixable issues exist (e.g., missing schema_version), then they are auto-fixed

### Story 5: Migrate Schema

**As a** user, **I want** to run `exobrain migrate` **so that** my workspace is updated to the latest schema version.

**Acceptance Criteria:**
- [ ] Given workspace schema_version < app schema_version, when I run any command, then I see "Migration required" and command is blocked
- [ ] Given I run `exobrain migrate`, when uncommitted changes exist, then I'm prompted to commit first
- [ ] Given I run `exobrain migrate`, when unpushed commits exist, then I'm prompted to push first
- [ ] Given I proceed with migrate, when migration starts, then a backup branch is created
- [ ] Given migration completes, when I'm prompted to confirm, then I can review changes before committing
- [ ] Given I confirm, when migration finalizes, then workspace.yml schema_version is updated

### Story 6: Sync Workspace

**As a** user, **I want** to run `exobrain sync` **so that** my changes are committed and pushed to GitHub.

**Acceptance Criteria:**
- [ ] Given uncommitted changes exist, when I run `exobrain sync`, then I'm prompted for a commit message
- [ ] Given I provide a message, when sync completes, then changes are committed and pushed
- [ ] Given no changes exist, when I run `exobrain sync`, then I see "Nothing to sync"

### Story 7: Check Status

**As a** user, **I want** to run `exobrain status` **so that** I can see workspace state at a glance.

**Acceptance Criteria:**
- [ ] Given I run `exobrain status`, then I see: workspace name, schema version, space count, document count
- [ ] Given uncommitted changes exist, then I see a warning with count
- [ ] Given unpushed commits exist, then I see a warning with count
- [ ] Given schema mismatch, then I see a warning to run migrate

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CLI framework | Click or Typer | Typer is modern and uses type hints; Click is more mature |
| Schema validation | Pydantic | Type-safe, good error messages, widespread adoption |
| Git operations | subprocess calling git | Simpler than GitPython; we're just running commands |
| Workspace location | `~/Library/Application Support/exobrain/workspaces/` | Standard macOS app data location |
| Config location | App repo `.env` (gitignored) | User identity stays with app install |
| UUID generation | Python uuid module or uuid7 package | UUIDv7 for time-sortability |

### Decision 1: CLI Framework

**Choice:** Typer (preferred) or Click
**Alternatives:** argparse, fire
**Rationale:** Typer uses type hints for automatic CLI generation, has good documentation, and produces clean help text. Click is the underlying library and also acceptable.

### Decision 2: Workspace Default Location

**Choice:** `~/Library/Application Support/exobrain/workspaces/{workspace-name}/`
**Alternatives:** `~/.exobrain/`, within app repo
**Rationale:** Standard macOS location for app data. The workspace folder IS the git repo (cloned or created there). User can override during init.

### Decision 3: Testing Framework

**Choice:** pytest with pytest-cov
**Alternatives:** unittest
**Rationale:** pytest is the standard; fixtures make testing CLI commands clean; coverage reporting built-in.

## Technical Approach

### Directory Structure

```
scripts/exobrain/
├── __init__.py
├── __main__.py           # Entry point: python -m exobrain
├── cli.py                # Typer app, command definitions
├── config.py             # Config loading (.env, workspace.yml)
├── models/
│   ├── __init__.py
│   ├── document.py       # Pydantic model for document frontmatter
│   ├── space.py          # Pydantic model for space (README frontmatter)
│   └── workspace.py      # Pydantic model for workspace.yml
├── services/
│   ├── __init__.py
│   ├── uuid.py           # UUIDv7 generation, 8-char prefix extraction
│   ├── frontmatter.py    # Parse/write YAML frontmatter
│   ├── validation.py     # Validate documents against schema
│   ├── migration.py      # Run migrations
│   └── git.py            # Git operations (commit, push, branch)
├── migrations/
│   ├── __init__.py
│   └── 001_initial.py    # Initial migration (for existing ideas)
└── types/
    └── master_types.yml  # Master type definitions
```

### Test Structure

```
tests/
├── conftest.py           # Fixtures: temp workspace, mock git
├── test_cli.py           # CLI command tests
├── test_models.py        # Pydantic model tests
├── test_validation.py    # Validation logic tests
├── test_migration.py     # Migration tests
├── test_frontmatter.py   # Frontmatter parsing tests
└── test_uuid.py          # UUID generation tests
```

### Pydantic Models

```python
# models/document.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class DocumentType(str, Enum):
    # Non-terminal (source)
    TRANSCRIPT = "transcript"
    CHARACTER = "character"
    SETTING = "setting"
    SUMMARY = "summary"
    # Terminal (output)
    BRIEF = "brief"
    BLOG_POST = "blog-post"
    POEM = "poem"
    TWEET = "tweet"

TERMINAL_TYPES = {DocumentType.BRIEF, DocumentType.BLOG_POST, DocumentType.POEM, DocumentType.TWEET}

class DocumentFrontmatter(BaseModel):
    id: str = Field(..., description="Full UUIDv7")
    type: DocumentType
    space: str = Field(..., description="8-char space UUID")
    created: datetime
    created_by: str
    agent: str
    schema_version: int = 1

    # Optional
    title: Optional[str] = None
    subtitle: Optional[str] = None
    brief: Optional[str] = None
    status: Optional[str] = None  # draft, published, in_review, archived
    updated: Optional[datetime] = None
    updated_by: Optional[str] = None
    updated_agent: Optional[str] = None
    derived_from: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    hashtags: Optional[List[str]] = None

    def validate_derived_from(self) -> List[str]:
        """Returns errors if derived_from rules are violated."""
        errors = []
        if self.type in TERMINAL_TYPES and not self.derived_from:
            errors.append(f"Terminal type '{self.type}' requires 'derived_from' field")
        return errors
```

### CLI Commands

```python
# cli.py
import typer
from pathlib import Path

app = typer.Typer(name="exobrain", help="ExoBrain workspace management CLI")

@app.command()
def init(
    workspace_url: str = typer.Option(None, help="Existing GitHub repo URL"),
    location: Path = typer.Option(None, help="Override default workspace location"),
):
    """Initialize exobrain: check prerequisites, setup workspace."""
    ...

@app.command()
def space_create(
    slug: str = typer.Argument(..., help="Human-readable slug for the space"),
):
    """Create a new idea space with proper UUID and structure."""
    ...

@app.command()
def doc_create(
    space: str = typer.Argument(..., help="Space UUID (8-char prefix)"),
    type: str = typer.Argument(..., help="Document type"),
    title: str = typer.Option(None, help="Document title"),
    derived_from: List[str] = typer.Option(None, help="Source document UUIDs"),
    content: str = typer.Option(None, help="Document body content"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Create a new document with proper frontmatter."""
    ...

@app.command()
def validate(
    fix: bool = typer.Option(False, help="Auto-fix fixable issues"),
):
    """Validate all documents in workspace against schema."""
    ...

@app.command()
def migrate():
    """Migrate workspace to latest schema version."""
    ...

@app.command()
def sync(
    message: str = typer.Option(None, "-m", help="Commit message"),
):
    """Commit and push workspace changes."""
    ...

@app.command()
def status():
    """Show workspace status."""
    ...
```

### Init Flow Detail

```
exobrain init
│
├─> Check prerequisites
│   ├─ git --version (fail with install instructions if missing)
│   ├─ gh --version (fail with install instructions if missing)
│   └─ gh auth status (fail if not authenticated)
│
├─> Capture user identity
│   ├─ Prompt: "Your name:" (default from git config user.name)
│   └─ Prompt: "Your email:" (default from git config user.email)
│
├─> Workspace setup
│   ├─ Prompt: "Existing workspace repo URL? (leave blank to create new)"
│   │   ├─ If URL provided:
│   │   │   └─ git clone {url} {location}
│   │   └─ If blank:
│   │       ├─ Prompt: "Workspace name:"
│   │       ├─ Create local folder structure
│   │       ├─ git init
│   │       ├─ Create workspace.yml, types.yml
│   │       ├─ Initial commit
│   │       └─ gh repo create --private --source=. --push
│   │
│   └─ Prompt: "Workspace location:" (default: ~/Library/Application Support/exobrain/workspaces/{name}/)
│
├─> Save config
│   └─ Write to app .env: EXOBRAIN_USER, EXOBRAIN_EMAIL, EXOBRAIN_WORKSPACE
│
└─> Success message
    └─ "Workspace ready! Open Claude Code in {app-repo} and start creating."
```

### Migration of Existing Ideas

The final step of Phase 1 is migrating `ideas/` to the new structure:

1. Create migration script `migrations/001_initial.py`
2. For each folder in `ideas/NNNN-name/`:
   - Generate UUIDv7 for the space
   - Rename folder to `{8-char}-{slug}/`
   - Update README.md with proper frontmatter
   - For each file in transcripts/ and views/:
     - Generate UUIDv7 for the document
     - Add/update frontmatter with required fields
     - Infer `derived_from` where possible (views derive from transcripts in same space)
3. Create `workspace.yml` with schema_version: 1
4. Create `types.yml` with allowed types
5. Run validation to confirm success
6. Commit with message "Migration: ideas/ to exobrain workspace structure"

## Implementation Phases

### Phase 1: Core CLI (This Plan)

1. **Setup** (Day 1)
   - Create `scripts/exobrain/` package structure
   - Add dependencies: typer, pydantic, pytest, pytest-cov
   - Create pyproject.toml or setup.py
   - Setup pytest configuration

2. **Models** (Day 1-2)
   - Implement Pydantic models for Document, Space, Workspace
   - Implement frontmatter parsing/writing service
   - Write tests for models and frontmatter

3. **UUID Service** (Day 2)
   - Implement UUIDv7 generation
   - Implement 8-char prefix extraction
   - Write tests

4. **Validation Service** (Day 2-3)
   - Implement document validation against schema
   - Implement type checking (terminal vs non-terminal rules)
   - Implement workspace-wide validation
   - Write tests

5. **CLI Commands** (Day 3-4)
   - Implement `exobrain init`
   - Implement `exobrain space create`
   - Implement `exobrain doc create`
   - Implement `exobrain validate`
   - Implement `exobrain status`
   - Write CLI tests

6. **Git Operations** (Day 4)
   - Implement git service (status, commit, push, branch)
   - Implement `exobrain sync`
   - Write tests

7. **Migration Framework** (Day 5)
   - Implement migration runner
   - Implement `exobrain migrate`
   - Write tests

8. **Existing Ideas Migration** (Day 5-6)
   - Write migration script for current `ideas/` folder
   - Test migration on copy of data
   - Run migration
   - Validate and commit

9. **Integration & Polish** (Day 6)
   - End-to-end testing
   - Documentation in README
   - Update `.claude/commands/` to reference new CLI

### Phase 2: Agent Integration (Future)

- Update `instantiate-idea.md` to call `exobrain space create`
- Update `generate-view.md` to call `exobrain doc create`
- Update `generate-transcript.md` to call `exobrain doc create`
- Add MCP server wrapper

### Phase 3: Advanced Features (Future)

- Templates system
- Integrations (site publishing, social media)
- Space types
- Full graph/link model

## Testing Strategy

### Unit Tests

- Test each Pydantic model with valid and invalid data
- Test frontmatter parsing with edge cases (empty, malformed, missing fields)
- Test UUID generation produces valid UUIDv7
- Test validation catches all rule violations

### Integration Tests

- Test CLI commands with temp workspace
- Test init flow with mocked git/gh commands
- Test migration on sample data

### Fixtures

```python
# conftest.py
import pytest
from pathlib import Path
import tempfile

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        # Create minimal structure
        (workspace / "workspace.yml").write_text("schema_version: 1\n")
        (workspace / "types.yml").write_text("types: {}\n")
        yield workspace

@pytest.fixture
def sample_document():
    """Return a valid document frontmatter dict."""
    return {
        "id": "01957a3b4c2d7a8e9f1c3d4e5f6a7b8c",
        "type": "transcript",
        "space": "01957a3b",
        "created": "2026-01-17T14:30:00Z",
        "created_by": "Test User",
        "agent": "claude-opus-4-5-20251101",
        "schema_version": 1,
    }
```

### Coverage Target

- Minimum 80% line coverage
- 100% coverage on validation logic
- All CLI commands have at least one happy-path and one error-path test

## Open Questions

| Question | Impact | Notes |
|----------|--------|-------|
| Typer vs Click? | Low | Both work; Typer is more modern |
| How to handle stdin for doc content? | Medium | Need to support piping content into doc create |
| Should we support `--dry-run` on commands? | Low | Nice to have for testing |

## Future Considerations

Discussed but deferred:

- **MCP Server**: Wrap CLI for native Claude tool integration
- **Templates**: Frameworks for generating specific content types
- **Integrations**: Site publishing, Twitter, etc. as workspace readers/writers
- **Space Types**: Constrain valid doc types per space (book, concept, etc.)
- **Full Graph Model**: Link entities with type, direction, status
- **UI**: IDE plugin or web interface

## Verification

- [ ] `exobrain init` completes successfully on fresh machine
- [ ] `exobrain space create --slug test` creates valid folder
- [ ] `exobrain doc create` with terminal type fails without `--derived-from`
- [ ] `exobrain doc create` with non-terminal type succeeds without `--derived-from`
- [ ] `exobrain validate` passes on migrated workspace
- [ ] `exobrain status` shows correct counts
- [ ] `exobrain sync` commits and pushes
- [ ] pytest runs with >80% coverage
- [ ] Existing `ideas/` folder successfully migrated
- [ ] Claude agents can call CLI via Bash and create valid documents

## References

- ADR-001: ExoBrain Workspace Structure and Schema (`docs/adr/001-exobrain-workspace-structure-and-schema.md`)
- ExoBrain V1 Feature Overview: `docs/active/20260117-exobrain_v1_feature_overview-chatgpt.md`
- ExoBrain KnowledgeFS Plan: `docs/active/20260117-exobrain-knowledgefs-plan-chatgpt.md`
- Existing CLI pattern: `scripts/gemini.py`
