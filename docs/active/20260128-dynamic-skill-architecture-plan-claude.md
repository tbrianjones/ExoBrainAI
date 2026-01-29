---
status: Research
date: 2026-01-28
branch: n/a
related-adrs:
  - docs/adr/004-claude-code-first-ui.md
  - docs/adr/006-information-centric-computing-vision.md
---

# Dynamic Skill Architecture

Research document capturing patterns for organizing `.claude/` folder structure, managing skills at scale, and implementing MCP-based dynamic skill discovery from ExoBrain.

## Summary

As the skill library grows to hundreds or thousands of skills, the current flat structure becomes unmanageable. This document captures emerging patterns for: (1) organizing skills into categorical subdirectories, (2) co-locating supporting materials (frameworks, templates, voices) with skills, and (3) using MCP servers to dynamically discover and expose skills based on task context. The vision is that skills become ExoBrain objects themselves, queryable and composable like any other knowledge.

## Agent Quick Start

**Files to load:**
- `.claude/CLAUDE.md` ; folder structure documentation
- `.claude/skills/exobrain.md` ; current ExoBrain skill interface
- `templates/` ; frameworks to migrate into skill folders

**ADRs to read:**
- `docs/adr/004-claude-code-first-ui.md` ; Claude Code as primary UI
- `docs/adr/006-information-centric-computing-vision.md` ; everything is an object

**Areas to explore:**
- MCP protocol specification at modelcontextprotocol.io
- FastMCP Python library for server implementation
- Existing FastAPI endpoints in `engine/src/api/`

## Problem Statement

**User Persona:** Knowledge worker using Claude Code CLI for research, ideation, and content generation on top of ExoBrain.

**Pain Points:**
1. Skill library will grow to hundreds of content generation skills (report types, visualization styles, writing voices)
2. Development workflows need different agents than content creation workflows
3. Supporting materials (frameworks, templates, example outputs) live in `templates/` separate from the skills that use them
4. No mechanism to dynamically surface relevant skills based on what the user is working on
5. Context budget (15K characters for skill descriptions) limits how many skills can be available simultaneously

**Current State:**
- 14 commands in `.claude/commands/` (flat structure)
- 4 skills in `.claude/skills/` (flat structure)
- 3 agents in `.claude/agents/` (flat structure)
- Rich frameworks in `templates/` disconnected from skills

**Desired State:**
- Skills organized by domain in subdirectories
- Frameworks co-located with skills that use them
- MCP server queries ExoBrain to discover relevant skills dynamically
- Skills themselves are ExoBrain objects, managed like any other knowledge

## Key Concepts

### 1. Subdirectory Organization

Claude Code supports nested directories within `.claude/skills/`, `.claude/commands/`, and `.claude/agents/`. Skills in subdirectories are automatically discovered.

**Proposed structure:**

```
.claude/
├── CLAUDE.md
├── skills/
│   ├── content-generation/
│   │   ├── generate-view/
│   │   │   ├── SKILL.md
│   │   │   └── voices/
│   │   │       ├── true-self.md
│   │   │       ├── podcast.md
│   │   │       └── professional.md
│   │   ├── generate-academic-infographic/
│   │   │   ├── SKILL.md
│   │   │   └── framework.md
│   │   ├── generate-poem/
│   │   │   ├── SKILL.md
│   │   │   └── poetry-framework.md
│   │   └── generate-transcript/
│   │       └── SKILL.md
│   ├── ideation/
│   │   ├── ideate/
│   │   │   └── SKILL.md
│   │   └── instantiate-idea/
│   │       └── SKILL.md
│   ├── repo-admin/
│   │   ├── create-adr/
│   │   │   └── SKILL.md
│   │   └── generate-feature-plan/
│   │       └── SKILL.md
│   └── exobrain/
│       ├── SKILL.md
│       └── reference/
│           ├── cli-reference.md
│           └── json-schemas.md
├── agents/
│   ├── content/
│   │   ├── transcript-summary-generator.md
│   │   └── transcript-raw-generator.md
│   └── planning/
│       └── adr-generator.md
└── commands/
    └── (legacy, migrating to skills)
```

**Key insight:** Commands have been merged into skills in Claude Code. Both `.claude/commands/review.md` and `.claude/skills/review/SKILL.md` create `/review`. New work should use skills.

### 2. Skill Folder Contents

Each skill folder can contain supporting files alongside `SKILL.md`:

| File | Purpose | Auto-loaded? |
|------|---------|--------------|
| `SKILL.md` | Core instructions + navigation | Yes, when invoked |
| `framework.md` | Detailed methodology | No, referenced |
| `examples/` | Sample outputs | No, referenced |
| `templates/` | Output structure templates | No, referenced |
| `voices/` | Writing style guides | No, referenced |
| `scripts/` | Executable helpers | No, called via bash |

**Best practice:** Keep `SKILL.md` under 500 lines. Move detailed reference material to separate files. Reference them so Claude knows they exist:

```markdown
# In SKILL.md:
For the complete framework methodology, see [framework.md](framework.md).
For output examples, see [examples/](examples/).
```

Claude reads supporting files only when relevant to the task.

### 3. Progressive Disclosure Architecture

Claude Code uses three-layer loading to handle scale:

1. **Metadata (~100 tokens):** Skill name + description loaded at session start
2. **Full instructions (~5K tokens):** Complete SKILL.md loaded when Claude determines relevance
3. **Supporting files:** Loaded on-demand only when needed

This means hundreds of skills can exist without overwhelming context. The 15K character budget applies to aggregated descriptions only.

**Implication:** Write descriptions that clearly signal when to invoke the skill:

```yaml
description: |
  Generate academic infographics from ExoBrain objects.
  Use when user says "infographic", "data visualization",
  "academic poster", or requests visual summary of research.
```

### 4. MCP Dynamic Tool Discovery

MCP servers can expose tools dynamically based on database queries. For ExoBrain integration:

**Architecture:**

```
┌─────────────────────────────────────────────────┐
│         MCP Server (Python FastMCP)             │
│         Wraps existing FastAPI endpoints        │
├─────────────────────────────────────────────────┤
│                                                 │
│  tools/list:                                    │
│    → Query SQLite: SELECT * FROM objects        │
│      WHERE type = 'skill'                       │
│    → Filter by tags matching user context       │
│    → Return as MCP tool definitions             │
│                                                 │
│  tools/call:                                    │
│    → Load skill content from ExoBrain           │
│    → Execute with provided arguments            │
│    → Return structured result                   │
│                                                 │
│  notifications/tools/list_changed:              │
│    → Sent when skills added/modified            │
│    → Claude re-fetches available tools          │
│                                                 │
└─────────────────────────────────────────────────┘
         ↓
      Claude Code
```

**Key capability:** `notifications/tools/list_changed` allows the MCP server to notify Claude when new skills are added to ExoBrain. Claude automatically refreshes its tool list.

### 5. Skills as ExoBrain Objects

Store skills in ExoBrain like any other object:

```bash
exobrain capture "$(cat SKILL.md)" \
  --title "generate-academic-infographic" \
  --type skill \
  --space skills/content-generation \
  --tag report --tag visualization --tag academic
```

**Extended JSON for skill metadata:**

```json
{
  "input_schema": {
    "type": "object",
    "properties": {
      "topic": {"type": "string"},
      "format": {"type": "string", "enum": ["poster", "slide", "card"]}
    }
  },
  "output_format": "markdown",
  "enabled": true,
  "version": "1.0"
}
```

Skills become queryable, taggable, linkable, and projectable like any other knowledge.

### 6. Meta-Tool Composition

Rather than exposing hundreds of individual tools, expose orchestrator tools:

```python
@mcp.tool()
def generate_report(topic: str, include_visuals: bool = True) -> dict:
    """
    Meta-tool: Generate a report by orchestrating relevant skills.

    1. Queries ExoBrain for objects matching topic
    2. Discovers applicable generation skills
    3. Composes output from multiple skill executions
    """
    sources = repo.search(topic)
    skills = repo.list_objects(type="skill", tags=["report", "writing"])
    # Orchestrate and compose...
    return {"report": composed_output, "skills_used": skills}
```

**User journey:**

1. User captures research into ExoBrain
2. User: "Generate a report on distributed systems"
3. MCP server queries for objects tagged #distributed-systems
4. MCP server queries for skills tagged #report, #visualization
5. Claude sees available tools: `generate-academic-report`, `create-infographic`, `render-diagram`
6. Claude orchestrates to produce composed output

## Proposed Phases

### Phase 1: Folder Reorganization (Manual)

Reorganize existing `.claude/` structure into subdirectories:

- Create `skills/content-generation/`, `skills/ideation/`, `skills/repo-admin/`
- Move existing commands/skills into appropriate subdirectories
- Convert flat `.md` files to `skill-name/SKILL.md` structure
- Verify skills still load correctly

### Phase 2: Template Migration (Manual)

Move frameworks from `templates/` into skill folders:

| From | To |
|------|-----|
| `templates/infographics/academic-infographic-framework.md` | `skills/content-generation/generate-academic-infographic/framework.md` |
| `templates/poetry/AI Poetry Generation Framework.md` | `skills/content-generation/generate-poem/poetry-framework.md` |
| `templates/voices/` | `skills/content-generation/generate-view/voices/` |
| `templates/title-generation/` | `skills/exobrain/reference/` or standalone skill |

Update `SKILL.md` files to reference co-located frameworks.

### Phase 3: MCP Server Prototype

Build lightweight MCP server wrapping ExoBrain:

```python
# engine/src/mcp/server.py
from mcp.server.fastmcp import FastMCP
from api.client import ExoBrainClient  # Wrap existing FastAPI

mcp = FastMCP("exobrain-skills")
client = ExoBrainClient("http://localhost:8420")

@mcp.tool()
def discover_skills(tags: list[str] = None, space: str = None) -> list[dict]:
    """Find skills available for the current task."""
    return client.list_objects(type="skill", tags=tags, space=space)

@mcp.tool()
def get_skill_instructions(skill_id: str) -> str:
    """Load full instructions for a skill."""
    return client.get_object(skill_id).content

@mcp.tool()
def execute_skill(skill_name: str, args: dict) -> dict:
    """Execute a skill with provided arguments."""
    skill = client.search(skill_name, type="skill")[0]
    # Implementation depends on skill type
    return {"result": "..."}
```

### Phase 4: Skills as Objects

Define conventions for storing skills in ExoBrain:

- Type: `skill`
- Space: `skills/{category}`
- Tags: capability tags for discovery (`report`, `visualization`, `writing`)
- Content: Full skill instructions (what would be in SKILL.md)
- Extended: Input schema, output format, enabled flag

Create tooling to sync between `.claude/skills/` files and ExoBrain objects (bidirectional, like projection layer).

## Open Questions

| Question | Impact | Notes |
|----------|--------|-------|
| How to handle skill versioning? | Medium | Could use ExoBrain's updated_at or explicit version in extended JSON |
| Should MCP server run in same container as ExoBrain? | Low | Probably yes, for simplicity |
| How to handle skill dependencies? | Medium | Skill A requires Skill B to be available |
| What triggers `list_changed` notification? | Medium | File watcher on skills table? Explicit API call? |
| How to test skills in isolation? | Medium | Need skill testing framework |

## Future Considerations

**Discussed but deferred:**

1. **Skill marketplace** ; share skills between ExoBrain instances
2. **Skill analytics** ; track which skills are used, success rates
3. **Skill permissions** ; some skills only available to certain users/contexts
4. **Skill composition language** ; declarative way to define meta-skills
5. **Vector embeddings for skill discovery** ; semantic search for "I need something that..."

**Related to ADR-006 vision:**

Skills as objects aligns with information-centric computing. A skill is knowledge about how to do something. It should be:
- Addressable (has ID)
- Queryable (searchable, taggable)
- Relatable (links to objects it operates on)
- Projectable (can be materialized as file)
- Composable (can be combined with other skills)

## References

**Internal:**
- `docs/adr/004-claude-code-first-ui.md` ; Claude Code as primary interface
- `docs/adr/006-information-centric-computing-vision.md` ; everything is an object
- `docs/active/20260128-exobrain-projection-layer-plan-claude.md` ; projection pattern for bidirectional sync

**External:**
- [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/claude-code/skills)
- [MCP Tools Specification](https://modelcontextprotocol.io/docs/concepts/tools)
- [FastMCP Python Library](https://github.com/jlowin/fastmcp)
- [Dynamic Tool Discovery in MCP](https://www.speakeasy.com/mcp/tool-design/dynamic-tool-discovery)

**Potential ADR:**

If this architecture is implemented, consider creating:
- `docs/adr/008-skills-as-exobrain-objects.md` ; decision to store skills in SQLite
- `docs/adr/009-mcp-dynamic-tool-discovery.md` ; MCP server architecture
