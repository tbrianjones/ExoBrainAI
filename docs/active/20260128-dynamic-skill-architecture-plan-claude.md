---
status: Planning
date: 2026-01-28
updated: 2026-02-09
branch: n/a
related-adrs:
  - docs/adr/004-claude-code-first-ui.md
  - docs/adr/006-information-centric-computing-vision.md
  - docs/adr/011-primitive-semantics-and-knowledge-gardening.md
---

# Dynamic Skill Architecture

Plan for storing commands, agents, and skills as ExoBrain objects; discovering them contextually based on the space being worked in; and evolving toward MCP-based dynamic tool exposure.

## Summary

As the tool library grows, the current flat `.claude/` structure becomes unmanageable and tools can't be discovered contextually. This plan captures: (1) a near-term "read and follow" pattern where Claude loads tool definitions from ExoBrain mid-conversation, (2) link-based space association so tools are discovered based on what the user is working on, (3) folder reorganization and co-location of supporting materials, and (4) MCP servers for dynamic tool exposure as a future evolution. The vision: agents discover, propose, and "just know" which tools are relevant. When working on zengineering, the system should just know to query for skills and commands and project them into the workspace.

## Agent Quick Start

**Files to load:**
- `.claude/CLAUDE.md` ; folder structure documentation
- `.claude/skills/exobrain.md` ; current ExoBrain skill interface
- `engine/src/core/bootstrap.py` ; relationship vocabulary, types, spaces
- `templates/` ; frameworks to migrate into skill folders

**ADRs to read:**
- `docs/adr/004-claude-code-first-ui.md` ; Claude Code as primary UI
- `docs/adr/006-information-centric-computing-vision.md` ; everything is an object
- `docs/adr/011-primitive-semantics-and-knowledge-gardening.md` ; primitive semantics (types, spaces, tags, links)

**Areas to explore:**
- MCP protocol specification at modelcontextprotocol.io
- FastMCP Python library for server implementation
- Existing FastAPI endpoints in `engine/src/api/`
- Current projection layer in `engine/src/core/projection.py`

## Problem Statement

**User Persona:** Knowledge worker using Claude Code CLI for research, ideation, and content generation on top of ExoBrain.

**Pain Points:**
1. Tool library will grow to hundreds of content generation skills, commands, and agents
2. Development workflows need different tools than content creation workflows
3. Supporting materials (frameworks, templates, example outputs) live in `templates/` separate from the skills that use them
4. No mechanism to dynamically surface relevant tools based on what the user is working on
5. Context budget (15K characters for skill descriptions) limits how many skills can be available simultaneously
6. Tools can't be associated with specific idea spaces (e.g., podcast tools for `ideas/zengineering`)

**Current State:**
- 14 commands in `.claude/commands/` (flat structure)
- 4 skills in `.claude/skills/` (flat structure)
- 3 agents in `.claude/agents/` (flat structure)
- Rich frameworks in `templates/` disconnected from skills
- No tool-to-space relationships

**Desired State:**
- Commands, agents, and skills stored as ExoBrain objects
- Tools linked to spaces they're relevant to via `tool-for` relationships
- Contextual discovery: entering a space surfaces its associated tools
- Tools organized by domain in subdirectories with co-located frameworks
- MCP server queries ExoBrain to discover relevant tools dynamically (future)

## Key Concepts

### 1. Near-Term Read-and-Follow Pattern

Claude can already load a tool definition mid-conversation by reading its content. No MCP server or new infrastructure needed.

**How it works:**
1. Store tool definitions as ExoBrain objects (type: `Skill`/`Command`/`Agent`)
2. Link tools to spaces via `tool-for` relationship
3. When entering a space, query ExoBrain for linked tools
4. Read tool content into Claude's context
5. Follow the loaded instructions as if formally invoked

**Example flow:**
```bash
# Query for tools linked to the zengineering space
exobrain link list $ZENGINEERING_SPACE_ID --json
# Filter for tool-for relationships, get tool IDs
# Read each tool's content
exobrain get $TOOL_ID --json
# Content field contains full markdown instructions
```

**Key insight:** The formal `Skill` tool only works with skills registered at conversation start. But reading a markdown file with instructions and following them is functionally equivalent. The difference is discoverability; ExoBrain provides the discovery layer.

### 2. Tools as ExoBrain Objects

Store all three tool types (commands, agents, skills) in ExoBrain:

```bash
# Store a skill
echo "$(cat .claude/skills/exobrain.md)" | docker compose exec -T exobrain exobrain capture \
  --title "exobrain" \
  --type skill \
  --space "tools/skills" \
  --tag published --tag exobrain --tag cli \
  --always-project --json

# Link it to spaces where it's relevant
exobrain link create $SKILL_ID $TARGET_SPACE_ID "tool-for"
```

**Object structure:**

| Field | Usage |
|-------|-------|
| `type` | `Skill`, `Command`, or `Agent` (custom types) |
| `space` | `tools/skills`, `tools/commands`, or `tools/agents` |
| `title` | Tool name (e.g., `generate-view`, `ideate`, `transcript-summary-generator`) |
| `summary` | When to use this tool; triggers for discovery |
| `content` | Full markdown instructions (what would be in the `.md` file) |
| `tags` | Capability classification: `report`, `visualization`, `writing`, `podcast`, `ideation` |
| `links` | `tool-for` → spaces where this tool is relevant |

### 3. Context-Aware Discovery via Links

Tools are linked to spaces using a new `tool-for` / `has-tool` relationship pair.

**Relationship semantics:**
- `tool-for` (forward): "This skill is a tool for this space"
- `has-tool` (inverse): "This space has this tool available"

**Discovery pattern:**
```
User enters ideas/zengineering
  → Query: links WHERE target = zengineering_space_id AND relationship = "tool-for"
  → Returns: generate-episode-outline, podcast-voice-template, guest-research-agent
  → Also query: links WHERE target = ideas_space_id AND relationship = "tool-for"
    (tools relevant to all idea spaces)
  → Claude reads each tool's content into context
  → Tools are now available for the session
```

**Why links instead of tags or nested spaces:**
- **Links** are the right primitive for spatial relevance (ADR-011: "how things relate")
- **Tags** handle capability classification (what kind of tool: `report`, `visualization`)
- **Spaces** handle tool organization (where the tool definition lives: `tools/skills`)
- A single tool can link to many spaces without duplication

### 4. Subdirectory Organization

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

### 5. Skill Folder Contents

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

### 6. Progressive Disclosure Architecture

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

### 7. MCP Dynamic Tool Discovery (Future)

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
│      WHERE type IN ('skill','command','agent')  │
│    → Filter by links to current space           │
│    → Return as MCP tool definitions             │
│                                                 │
│  tools/call:                                    │
│    → Load tool content from ExoBrain            │
│    → Execute with provided arguments            │
│    → Return structured result                   │
│                                                 │
│  notifications/tools/list_changed:              │
│    → Sent when tools added/modified             │
│    → Claude re-fetches available tools          │
│                                                 │
└─────────────────────────────────────────────────┘
         ↓
      Claude Code
```

**Key capability:** `notifications/tools/list_changed` allows the MCP server to notify Claude when new tools are added to ExoBrain. Claude automatically refreshes its tool list.

### 8. Meta-Tool Composition

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

## Implementation Phases

### Phase 1: Tools as Objects

Store existing commands, agents, and skills as ExoBrain objects:

- Create custom types: `Skill`, `Command`, `Agent` (via `exobrain type create`)
- Create tool spaces: `tools/skills`, `tools/commands`, `tools/agents`
- Add `tool-for` / `has-tool` to `RELATIONSHIP_VOCABULARY` in `engine/src/core/bootstrap.py`
- Import existing `.claude/` tool definitions into ExoBrain as objects
- Tag each tool with capability classifications
- Set `--always-project` so tool definitions are always available as files

### Phase 2: Space-Linked Discovery

Link tools to the spaces they're relevant to:

- Audit each tool: which idea spaces benefit from it?
- Create `tool-for` links (e.g., `generate-episode-outline` → `ideas/zengineering`)
- Build a query pattern: "given a space, find all tools linked to it (and its parents)"
- Document the discovery query in the ExoBrain skill

### Phase 3: Projection Integration

Make projected tools readable from within the repo where Claude Code runs:

- Explore symlink from repo to `$EXOBRAIN_DATA_DIR/projected/tools/`
- Or: mount projected directory into repo via Docker volume
- Or: project tools into a `.claude/projected/` directory
- Goal: Claude can `Read` projected tool files without knowing `$EXOBRAIN_DATA_DIR`

### Phase 4: Auto-Discovery

Bake discovery into space-loading commands:

- Extend `/ideate`, `/generate-view`, and other space-aware commands
- When loading a space's context, also query for `tool-for` links
- Read discovered tool content into context automatically
- User doesn't need to think about which tools are available

### Phase 5: MCP Server

Full dynamic tool exposure via MCP (see Key Concepts section 7):

- Build lightweight MCP server wrapping ExoBrain API
- `discover_tools()`, `get_tool_instructions()`, `execute_tool()`
- `notifications/tools/list_changed` for real-time updates
- Meta-tool composition layer

### Phase 6: Folder Reorganization

Restructure `.claude/` directories (deferred; objects-first approach reduces urgency):

- Create subdirectory structure per Key Concepts section 4
- Migrate templates from `templates/` into skill folders
- Update `SKILL.md` files to reference co-located frameworks
- Verify skills still load correctly

## Open Questions

| Question | Impact | Notes |
|----------|--------|-------|
| Auto-discovery trigger | High | How/when does the system scan for relevant tools? Vision: agents discover, propose, and "just know." User shouldn't have to think about it. Probably baked into space-loading commands. |
| Projection-repo bridge | High | Projected tools need to be readable from within the repo where Claude Code runs. Current projection goes to `$EXOBRAIN_DATA_DIR/projected/` which is outside the repo. Symlink? Mount? `.claude/projected/` directory? |
| Type granularity | Medium | One `Tool` type with tag-based distinction (skill vs command vs agent), or three separate types? Three types aligns with ADR-011 (type = what something IS, immutable). |
| Bootstrapping strategy | Medium | How to initially import existing `.claude/` files into ExoBrain objects? Script? Manual? Gradual migration? |
| Tool versioning | Medium | Use ExoBrain's built-in object versioning (ADR-012) or explicit version field in content? |
| Parent space inheritance | Medium | Should `tool-for → ideas` mean "available in ALL idea sub-spaces"? Link query would need to walk up the space hierarchy. |
| MCP server container | Low | Run MCP server in same container as ExoBrain? Probably yes, for simplicity. |
| Tool dependencies | Medium | Skill A requires Skill B to be available. Express as `blocks`/`blocked-by` links? |
| Testing tools in isolation | Medium | Need a framework for testing individual tool definitions |

## Future Considerations

**Discussed but deferred:**

1. **Tool marketplace** ; share tools between ExoBrain instances
2. **Tool analytics** ; track which tools are used, success rates
3. **Tool permissions** ; some tools only available to certain users/contexts
4. **Skill composition language** ; declarative way to define meta-tools
5. **Vector embeddings for tool discovery** ; semantic search for "I need something that..."

**Related to ADR-006 vision:**

Tools as objects aligns with information-centric computing. A tool is knowledge about how to do something. It should be:
- Addressable (has ID)
- Queryable (searchable, taggable)
- Relatable (links to objects it operates on)
- Projectable (can be materialized as file)
- Composable (can be combined with other tools)

## References

**Internal:**
- `docs/adr/004-claude-code-first-ui.md` ; Claude Code as primary interface
- `docs/adr/006-information-centric-computing-vision.md` ; everything is an object
- `docs/adr/011-primitive-semantics-and-knowledge-gardening.md` ; primitive semantics for organizing tools
- `docs/active/20260128-exobrain-projection-layer-plan-claude.md` ; projection pattern for bidirectional sync

**External:**
- [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/claude-code/skills)
- [MCP Tools Specification](https://modelcontextprotocol.io/docs/concepts/tools)
- [FastMCP Python Library](https://github.com/jlowin/fastmcp)
- [Dynamic Tool Discovery in MCP](https://www.speakeasy.com/mcp/tool-design/dynamic-tool-discovery)

**Potential ADR:**

When implementation begins, consider creating:
- ADR for tools-as-ExoBrain-objects decision
- ADR for MCP dynamic tool discovery architecture
