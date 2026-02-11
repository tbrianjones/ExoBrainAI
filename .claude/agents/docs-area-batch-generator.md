---
name: docs-area-batch-generator
description: Generates README.md and AGENTS.md for a batch of areas at the same depth level. Max 5 areas per batch for predictable context. Spawned by /generate-docs Phase 2 for depth-grouped area batches.
tools: Read, Glob, Grep, Write
# Read: Load plan file, ADRs, code files, existing docs, parent/child AGENTS.md
# Glob: Find code files in areas, locate related documentation
# Grep: Search for patterns, imports, framework usage
# Write: Create README.md, AGENTS.md files for each area in batch
#
# SPAWNING: Orchestrator MUST use mode: "acceptEdits" (writes documentation files)
model: opus
# Opus required: Areas require deep code understanding and synthesis.
# Batch processing means agent builds understanding across related areas.
---

# Area Batch Generator

Generate README.md and AGENTS.md for a batch of areas at the same depth level.

## Design Principle

This agent handles a bounded batch of areas (max 5) at the same depth level. Benefits:
- Predictable context size (~30-50K tokens per batch)
- Same-depth areas don't depend on each other
- Can read shared parent context once
- Failures don't lose entire depth level (multiple batches)

## Input

```json
{
  "areas": ["engine/src/core/", "engine/src/cli/", "engine/src/api/"],
  "depth": 3,
  "plan_path": "docs/active/20260211-generate-docs-plan.md"
}
```

## Output

```json
{
  "batch_id": "depth3-A",
  "completed": [
    {"area": "engine/src/core/", "files": ["README.md", "AGENTS.md"]},
    {"area": "engine/src/cli/", "files": ["README.md", "AGENTS.md"]},
    {"area": "engine/src/api/", "files": ["README.md", "AGENTS.md"]}
  ],
  "failed": [],
  "total_files": 6
}
```

---

## Process

### Step 1: Read Plan File

Get context from plan file:
- Tech stack per area
- Relevant ADRs per area
- Generation order (verify we're at correct depth)

### Step 2: Read Shared Context Once

For the batch, read shared resources:
- Parent AGENTS.md (if areas share parent, e.g., all under `engine/src/`)
- Relevant ADRs for this batch (union of all areas' ADRs)
- Child AGENTS.md files (if children already generated at deeper depth)

**Efficiency note**: If all areas are under `engine/src/`, read parent context once, not per-area.

### Step 3: Process Each Area Sequentially

For each area in the batch:

1. **Read area code files**
   - Use Glob to find `.py` files
   - Read key files (not all; use judgment)
   - Understand what this area does

2. **Generate AGENTS.md**
   ```markdown
   # {Area Name} - Agent Instructions

   ## Scope

   Agent rules for working in {path}/.
   Parent: @/{parent}/AGENTS.md

   ## Key Files

   | File | Purpose |
   |------|---------|
   | `file.py` | {Specific purpose} |

   ## Rules

   ### From ADR-{id}: {title}
   - {Rule in actionable form}

   ### From Code Patterns
   - {Pattern discovered in code}

   ## Boundaries

   Always:
   - {Safe actions}

   Ask First:
   - {Actions requiring approval}

   Never:
   - {Prohibited actions}
   ```

3. **Generate README.md**

   **IMPORTANT**: Use the appropriate diagram type for the area.

   ```markdown
   # {Area Name}

   {1-2 sentence purpose}

   ## Architecture

   {Use appropriate diagram template below based on area type}

   ## Key Files

   | File | Purpose |
   |------|---------|

   ## Quick Start

   ```bash
   # Working commands
   ```

   ## Key Patterns

   ### {Pattern Name}
   {Explanation with code example}

   ## Related

   - Agent rules: [AGENTS.md](AGENTS.md)
   - Parent: [../README.md](../README.md)
   ```

   **Diagram Templates by Area Type:**

   *Core/Storage areas* (`engine/src/core/`):
   ```mermaid
   graph TD
       subgraph "Data Layer"
           DB[(SQLite + FTS5)]
           Schema[schema.py]
           Migrations[MIGRATIONS list]
       end

       subgraph "Repository Layer"
           ObjRepo[ObjectRepo]
           TagRepo[TagRepo]
           LinkRepo[LinkRepo]
           FileRepo[FileRepo]
       end

       subgraph "Projection"
           Scorer[Hot Tier Scorer]
           Projector[Markdown Projector]
           Syncer[Bidirectional Sync]
       end

       ObjRepo -->|"SQL via _db_session()"| DB
       TagRepo --> DB
       LinkRepo --> DB
       FileRepo --> DB
       Scorer -->|"score objects"| ObjRepo
       Projector -->|"write .md files"| FS[($EXOBRAIN_DATA_DIR/projected/)]
       Syncer -->|"read .md, update DB"| DB
   ```

   *CLI areas* (`engine/src/cli/`):
   ```mermaid
   graph LR
       subgraph "User Interface"
           Claude[Claude Code] -->|"docker compose exec"| CLI[Typer CLI]
           Terminal[Terminal] --> CLI
       end

       subgraph "Command Groups"
           CLI --> Objects[capture/get/list/update/delete/search]
           CLI --> Tags[tag add/remove/list]
           CLI --> Links[link create/list/remove]
           CLI --> System[init/status/doctor/backup]
           CLI --> Projection[project/sync/tier status]
       end

       subgraph "Data Access"
           Objects -->|"repository layer"| Repo[ObjectRepo/TagRepo/LinkRepo]
           Repo -->|"_db_session()"| DB[(SQLite)]
       end
   ```

   *Web UI/API areas* (`engine/src/api/`):
   ```mermaid
   graph TD
       subgraph "FastAPI Application"
           Routes[/ui/ Routes]
           Fragments[/ui-api/ HTMX Fragments]
           WriteOps[/ui-api/ POST Endpoints]
       end

       subgraph "Rendering"
           Routes -->|"Jinja2"| Templates[HTML Templates]
           Templates -->|"Tailwind CSS CDN"| Browser[Browser]
           Fragments -->|"HTMX swap"| Browser
       end

       subgraph "Data Access"
           Routes -->|"read-only"| Repo[Repository Layer]
           Repo --> DB[(SQLite)]
       end

       subgraph "Write Path"
           WriteOps -->|"HX-Request check"| SubProc[asyncio.subprocess]
           SubProc -->|"exobrain CLI"| DB
       end
   ```

   *GraphRAG areas* (`engine/src/graphrag/`):
   ```mermaid
   graph LR
       subgraph "Staging"
           Adapter[adapter.py] -->|"read objects"| DB[(SQLite)]
           Adapter -->|"write docs"| Staged[/cache/staged/]
       end

       subgraph "Indexing"
           Staged --> Indexer[GraphRAG Indexer]
           Indexer --> Index[/cache/graphrag/]
       end

       subgraph "Querying"
           Query[graphrag query] --> Index
           Query -->|"global/local mode"| Results[Theme/Entity Results]
       end
   ```

   *Watcher areas* (`engine/src/watcher/`):
   ```mermaid
   graph LR
       subgraph "File System"
           Projected[$EXOBRAIN_DATA_DIR/projected/]
       end

       subgraph "Watcher"
           Observer[watchdog Observer] -->|"detect changes"| Debounce[2s Debounce]
           Debounce -->|"trigger"| SyncCmd[exobrain sync]
       end

       Projected -->|"inotify/FSEvents"| Observer
       SyncCmd -->|"update"| DB[(SQLite)]
   ```

   **Diagram Quality Requirements:**
   - Use actual service/component names (not generic A, B, C)
   - Include logical boundaries via subgraphs
   - Label edges with data types or protocols (`-->|"SQL"|`, `-->|"JSON"|`)
   - Match diagram to current code state, not aspirational architecture

4. **Write files immediately**
   - Write AGENTS.md
   - Write README.md
   - Report completion before moving to next area

### Step 4: Report Results

Return structured output with:
- Each area's completion status
- Files written per area
- Any failures with error messages

---

## AGENTS.md Rules

**Important**: Since skills no longer contain reference content, AGENTS.md must provide sufficient context for agents working in an area. Include code examples and patterns.

- **Under 150 lines** (warn if over, consider sub-area AGENTS.md if needed)
- **Must have Boundaries section** (Always/Ask First/Never)
- **Must reference parent AGENTS.md** (except root)
- **Don't duplicate parent rules** - if parent says "use Docker", don't repeat
- **Attribute rules to sources** - "From ADR-003" or "From code patterns"
- **Include code examples** - Show common patterns agents will need:
  - How to use _db_session() (core areas)
  - How to add CLI commands with --json (CLI areas)
  - How to create Jinja2 templates with HTMX (API areas)

**Code Examples to Include** (by area type):
- **Core areas**: Repository pattern usage, _db_session() context manager, FTS5 queries
- **CLI areas**: Typer command patterns, _output() helper, --json flag handling
- **API areas**: Jinja2 template patterns, HTMX fragment endpoints, HX-Request verification
- **GraphRAG areas**: Staging adapter pattern, indexer configuration
- **Watcher areas**: File change detection, debounce configuration

**Example pattern block:**
```markdown
## Common Patterns

### Repository Method
```python
from engine.src.core.repository import ObjectRepo

def get_object(conn, object_id):
    repo = ObjectRepo(conn)
    return repo.get(object_id)
```
```

## README.md Rules

- **Must have quality Mermaid diagram** - use appropriate type for area (see templates above)
- **Diagram must include**: actual service names, logical boundaries via subgraphs, labeled edges
- **Anti-patterns to avoid**: generic labels (A→B→C), missing boundaries, unlabeled arrows
- **Must have Key Files table** - specific purposes, not generic
- **Must have working code examples** - copy from actual code
- **Focus on humans** - explain "why" not just "what"

---

## Hierarchy Awareness

### Reading Children (Already Generated)

If deeper areas already have AGENTS.md (generated in earlier depth pass):
- Read them to understand what's delegated
- Don't duplicate rules that exist in children
- Reference children appropriately

### Reading Parent (If Exists)

If parent AGENTS.md exists (for depth 2+, parent is depth 1):
- Read to understand inherited rules
- Don't duplicate rules from parent
- Reference parent in Scope section

### Sibling Coordination

Areas in the same batch are siblings (same depth). They:
- Don't depend on each other
- Can be processed in any order
- May share patterns (note for harmonizer later)

---

## Source of Truth Hierarchy

When sources conflict:

| Priority | Source | What It Provides |
|----------|--------|------------------|
| 1 | **ADRs** | Rules, constraints, decisions |
| 2 | **Code** | Actual patterns, implementation |
| 3 | **Existing docs** | "Why" explanations, context |

**When ADR and Code Disagree:**
- Code clearly ahead (new feature) → Document code, note ADR may need update
- Code violates ADR → Document ADR rule, flag code for fix
- Unclear → Favor ADR (deliberate decision), flag for review

---

## Quality Checklist

Before moving to next area, verify:

**AGENTS.md:**
- [ ] Has Scope section with parent reference
- [ ] Has Boundaries section (Always/Ask First/Never)
- [ ] Under 150 lines
- [ ] No rules duplicated from parent
- [ ] Rules attributed to sources (ADR-xxx or code pattern)

**README.md:**
- [ ] Has Mermaid diagram appropriate to area type
- [ ] Diagram uses actual service/component names (not generic labels)
- [ ] Diagram has subgraphs for logical grouping
- [ ] Diagram edges are labeled with data types or protocols
- [ ] Has Key Files table with specific purposes
- [ ] Has working code examples
- [ ] Links to AGENTS.md

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Area has no code files | Skip with warning, report in failed |
| Cannot read parent AGENTS.md | Continue without parent context, warn |
| Write fails | Report failure, continue with other areas |
| Area path doesn't exist | Skip with error, report in failed |

**Key principle**: One area's failure doesn't stop the batch. Complete what we can.

---

## Important

- **Bounded batch only** - This agent handles max 5 areas, no more
- **Sequential within batch** - Process one area at a time, report each
- **Same depth only** - All areas in batch must be at same depth level
- **Don't write CLAUDE.md** - Orchestrator handles that in finalize step
- **Quality matters** - These docs guide all future agent work
