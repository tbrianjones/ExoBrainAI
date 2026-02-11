---
description: Generates Skills, README.md, and AGENTS.md documentation from ADRs and codebase analysis. Use when user mentions generate docs, regenerate documentation, update AGENTS.md, create skills, refresh README, documentation is stale, or sync docs with code. Triggers on docs/adr/*.md, AGENTS.md, README.md, or .claude/skills/. Produces discovery-optimized skills and hierarchical agent documentation.
argument-hint: [scope]
allowed-tools: Read, Glob, Grep, Bash(ls*), Bash(find*), Bash(mkdir*), Bash(rm*), Edit, Write, Task
disable-model-invocation: true
---

<!--
ORCHESTRATOR CRITICAL RULES:

1. PERMISSION MODE (REQUIRED):
   All subagents that write/edit files MUST be spawned with: mode: "acceptEdits"
   Without this, agents cannot write files and will fail.

2. CONCURRENCY LIMIT (REQUIRED):
   NEVER spawn more than 6 agents in parallel.
   Process all work in batches of 6, waiting for each batch to complete.

3. MODEL SELECTION (REQUIRED):
   - Skills generation: model: "sonnet" (templated transformation from ADRs)
   - Area generation: model: "opus" (deep code understanding required)
   - Planning: model: "opus" (architectural analysis)
   - Review: model: "sonnet" (pattern matching against rules)
   - Harmonization: model: "opus" (cross-repo reasoning)
-->

# Documentation Generation Command

Generate Skills, README.md, and AGENTS.md from ADRs and code.

## Architecture

This command uses a **plan file as contract** model:
1. A planner agent writes a human-readable plan to `docs/active/`
2. Human reviews and approves by checking boxes in the plan file
3. Generator agents read from disk and write directly to disk
4. Minimal data passing between components

## Design Principles

1. **ADRs are source of truth** - Skills and AGENTS.md derive from ADRs. Never modify ADRs.
2. **Source of truth hierarchy** - When sources conflict: ADR > Code > Existing docs. Code may be ahead of ADRs; make a judgment call and flag discrepancies.
3. **CLAUDE.md mirrors AGENTS.md** - Root CLAUDE.md contains `@AGENTS.md`; every directory with AGENTS.md gets CLAUDE.md containing `@AGENTS.md`
4. **Single writer per file** - One agent produces all content for a file
5. **No redundancy** - Parent reference chain prevents rule duplication; harmonizer enforces this
6. **Two parallel tracks** - AGENTS.md (for agents) and README.md (for humans) both get harmonized
7. **Line limits** - AGENTS.md < 150 lines (except root, which is comprehensive), Skills < 500 lines
8. **Git is staging area** - Files written directly; use `git diff` to review
9. **Regenerate, don't patch** - Output is fresh synthesis from ADRs + code + existing docs (as input)
10. **Deep understanding** - Agents research tech stack best practices, truly understand the code

**Reference**: `docs/resources/20260114-claude-code-skills-creation-best-practices.md` for skill authoring guidance.

## Arguments

- `$ARGUMENTS` can be:
  - Empty: Run full 4-phase workflow
  - `plan`: Only run planning phase (creates plan file)
  - `<path>`: Generate docs for a specific area only (skips planning)

## Pre-Flight Checks

Before starting:

1. **ADRs exist**: Check `docs/adr/` has files. If empty, warn: "No ADRs found. Skills require ADRs. Proceed with area docs only?"

2. **Git state**: Run `git status`. If dirty, warn: "Working tree has uncommitted changes. Recommend committing first."

3. **Branch**: Check current branch. If `main`, warn: "On main branch. Recommend creating feature branch."

---

## Phase 1: PLAN

**Goal**: Create a human-readable plan file for approval.

### Spawn docs-planner

```
Task parameters:
  subagent_type: "docs-planner"
  mode: "acceptEdits"
  model: "opus"

Prompt:
"Analyze this codebase and create a documentation generation plan.

Write the plan to: docs/active/{YYYYMMDD}-generate-docs-plan.md

See your agent instructions for the plan file template and analysis process."
```

### Agent Output

The agent writes directly to `docs/active/YYYYMMDD-generate-docs-plan.md`

### Present to User

```
Documentation plan created: docs/active/20260211-generate-docs-plan.md

The plan includes:
- {N} skills to generate (from ADRs with ## Generated Skills)
- {N} areas to document (bottom-up order)
- {N} code-ADR mismatches to review

You have two options:
1. **Tell me what to do** - Say which items to include/exclude (e.g., "skip engine/tests, include all skills")
2. **Edit the file directly** - Check/uncheck the `[x]` boxes in the plan file, then say "continue"

What would you like to do?
```

### Wait for Approval

User must explicitly approve. They can:
- **Verbal instructions**: Tell orchestrator what to include/exclude
  - Orchestrator updates the plan file checkboxes accordingly
  - Confirms changes made
  - Proceeds to generation
- **Direct edit**: Edit the plan file to check/uncheck items, then say "continue"
- Add notes or change decisions
- Say "cancel" to abort

**If user provides verbal instructions**: Update the plan file checkboxes, confirm changes, then proceed.

**If user says "cancel"**: Archive plan to `docs/archive/` and stop.

---

## Phase 2: GENERATE (Bounded Batching)

**Goal**: Generate all documentation with predictable context usage and crash recovery.

**EFFICIENCY DESIGN**: Uses bounded batching to reduce agent count:
- Skills: One agent per ADR (handles the skill declared in that ADR)
- Areas: Batched by depth level, max 5 areas per batch
- Checkpoint file tracks progress for crash recovery

**CRITICAL**: Never spawn more than 6 agents in parallel. Wait for each parallel batch to complete.

### Generation Order

1. **Skills** - One agent per ADR with `## Generated Skills` (generates skill folder)
2. **Areas** - Generate by depth (deepest first), max 5 areas per batch agent
3. **Root** - Root AGENTS.md and README.md generate LAST, after all areas complete

CRITICAL: Root files must generate last so they can reference all child areas and aggregate statistics.

### Initialize Progress Tracking

Before starting generation, create a progress file to track status:

```markdown
# Generation Progress

Plan: docs/active/YYYYMMDD-generate-docs-plan.md
Started: {ISO timestamp}
Status: In Progress

## Skills
| ADR | Status |
|-----|--------|
| 003 | ⏳ |
| 009 | ⏳ |
| 010 | ⏳ |
| 013 | ⏳ |
| 015 | ⏳ |
| 016 | ⏳ |

## Areas
| Depth | Batch | Status |
|-------|-------|--------|
| 3 | A | ⏳ |
| 2 | A | ⏳ |
| 1 | A | ⏳ |

## Root
| Task | Status |
|------|--------|
| root | ⏳ |

Legend: ⏳ pending | 🔄 running | ✅ done | ❌ failed
```

Write to: `docs/active/YYYYMMDD-generate-docs-progress.md`

### Pre-Generation Cleanup

Before spawning generators:

**1. Delete stale skill folders:**
- Read plan file for "Stale Skills" section
- For each checked deletion:
  - Run: `rm -rf .claude/skills/{folder}/`
  - Add to "Folders Deleted" manifest for final output

**2. Proceed to generation**

### Read Approved Plan

```python
# Parse the plan file to get approved items
plan_path = "docs/active/YYYYMMDD-generate-docs-plan.md"
# Read skills_to_generate (checked ADRs with ## Generated Skills)
# Read areas_to_document (grouped by depth)
# Read area_batches (max 5 areas per batch)
```

### Generate Skills (One Agent Per ADR, Sonnet)

Process ADRs with `## Generated Skills` in batches of 6. Wait for each batch to complete.

```
Task parameters:
  subagent_type: "docs-adr-skill-generator"
  mode: "acceptEdits"
  model: "sonnet"  # Skills are templated ADR transformation

Prompt:
"Generate the skill for ADR-{id}.

Task: {\"adr_id\": \"{id}\", \"plan_path\": \"{plan_path}\"}

Read the ADR, generate SKILL.md from the ## Generated Skills section.

See your agent instructions for skill format and quality requirements."
```

**Skill folder structure:**

```
.claude/skills/
├── 003-add-cli-command/
│   └── SKILL.md
├── 009-add-database-migration/
│   └── SKILL.md
├── 010-add-web-ui-page/
│   └── SKILL.md
├── 013-add-web-ui-write-operation/
│   └── SKILL.md
├── 015-docs-management/
│   └── SKILL.md
├── 016-exobrain-interface/
│   └── SKILL.md
├── title-generation.md          # Hand-maintained (NOT touched)
├── summary-generation.md        # Hand-maintained (NOT touched)
├── tag-generation.md            # Hand-maintained (NOT touched)
└── exobrain.md                  # Replaced by 016-exobrain-interface/ once verified
```

**Batching example** (6 ADRs with skills):
- Batch 1: ADRs 003, 009, 010, 013, 015, 016 (6 agents) → wait

**Total skill agents: ~6**

### Generate Areas (Depth-Batched, Max 5 Per Batch, Opus)

Process depth levels sequentially (deepest first). Within each depth, run batches in parallel (max 6 parallel).

**Step 1: Group areas by depth from plan file**

```python
depth_3_areas = ["engine/src/core/", "engine/src/cli/", "engine/src/api/", "engine/src/graphrag/", "engine/src/watcher/"]
depth_2_areas = ["engine/src/", "engine/tests/"]
depth_1_areas = ["engine/"]
```

**Step 2: Split into batches of max 5**

**Step 3: Process by depth level**

```
# Depth 3 (spawn batch agents, wait)
Task parameters:
  subagent_type: "docs-area-batch-generator"
  mode: "acceptEdits"
  model: "opus"  # Areas require deep code understanding

Prompt:
"Generate docs for depth-3 areas.

Task: {\"areas\": [\"engine/src/core/\", \"engine/src/cli/\", ...], \"depth\": 3, \"plan_path\": \"{plan_path}\"}

Process each area sequentially, report completion after each.
See your agent instructions for area documentation format."

# Wait for depth 3 to complete before starting depth 2
# Depth 2, then depth 1...
```

**Total area agents: ~3-5** (depending on codebase size)

### Generate Root (After All Areas Complete)

**Wait for ALL area depth levels to complete** before spawning root generation.

```
Task parameters:
  subagent_type: "docs-generator"
  mode: "acceptEdits"
  model: "opus"  # Root requires synthesis across all areas

Prompt:
"Generate root documentation (CLAUDE.md, AGENTS.md, README.md).

Task: {\"task\": \"root\", \"plan_path\": \"{plan_path}\"}

See your agent instructions for root documentation format."
```

### Progress Updates

After each agent completes, display progress:
```
Skills: [████████░░░░] 4/6 ADRs complete
Areas:  [██████░░░░░░] Depth 3 ✓, Depth 2 in progress

Latest:
  ✓ ADR-003: SKILL.md (add-cli-command)
  ✓ Depth 3 Batch A: engine/src/core/, engine/src/cli/, engine/src/api/
```

---

## Phase 3: REVIEW

**Goal**: Validate all generated documentation.

### Spawn docs-reviewer

```
Task parameters:
  subagent_type: "docs-reviewer"
  mode: "default"  # Read-only, no writes needed
  model: "sonnet"  # Pattern matching against rules

Prompt:
"Review all generated documentation for quality issues.

Input: {\"plan_path\": \"{plan_path}\"}

See your agent instructions for validation checks."
```

### Present Issues

If issues found:
```
Review complete. Found {N} issues:

HIGH (must fix):
- engine/src/core/AGENTS.md: Missing Boundaries section
- engine/src/core/: Missing CLAUDE.md file

MEDIUM (should fix):
- engine/src/api/AGENTS.md: Exceeds 150 lines (167)

Do you want to auto-fix these issues? [y/n]
```

### Apply Fixes

If user approves:
- Create missing CLAUDE.md files (content: `@AGENTS.md`)
- For other issues, the generator already wrote files; user can manually edit

---

## Phase 4: HARMONIZE (Top-Down)

**Goal**: Ensure cross-area consistency and remove redundancy.

### Spawn docs-harmonizer

```
Task parameters:
  subagent_type: "docs-harmonizer"
  mode: "acceptEdits"  # Edits existing files
  model: "opus"  # Cross-repo reasoning required

Prompt:
"Harmonize all generated documentation for consistency.

Input: {\"plan_path\": \"{plan_path}\"}

Read all generated docs, identify redundancy, elevate shared patterns,
add cross-references. Edit files directly.

See your agent instructions for harmonization rules."
```

### Display Harmonizer Changes

When harmonizer completes, parse its output and display per-file details:

```
Harmonization changes:

engine/src/core/AGENTS.md:
  - Removed line 39: redundant repository rule (exists in root)
  - Added cross-reference to engine/src/cli/AGENTS.md
```

### Present Summary

```
Harmonization complete:
  - Files modified: {N}
  - Redundancies removed: {N}
  - Patterns elevated to parents: {N}
  - Cross-references added: {N}

Approve these changes? [y/n] (or 'git diff' to review)
```

### User Decision

- **Approve**: Changes are already made, continue to finalize
- **Reject**: User runs `git checkout -- <paths>` to revert
- **Review**: User runs `git diff` to see changes before deciding

---

## Finalize

### Write Platform Files

Write directly (no subagent):

1. **CLAUDE.md in each documented area**:
   - Content: `@AGENTS.md`
   - For each area in plan's generation order

2. **Gemini config**:
   - Path: `.gemini/settings.json`
   - Content: `{"context": {"fileName": ["AGENTS.md"]}}`

3. **Claude directory README** (`.claude/README.md`):
   - Scan all `.claude/` subdirectories: agents/, commands/, skills/
   - For each item, write a concise 1-sentence summary
   - Write consolidated index using template:

```markdown
# Claude Code Configuration

Overview of all Claude Code customizations for this project.

## Agents

Subagents spawned by commands for specialized tasks.

| Agent | Purpose |
|-------|---------|
| [{name}](agents/{filename}) | {1-sentence summary} |

## Commands

Slash commands available via `/command-name`.

| Command | Purpose |
|---------|---------|
| [{name}](commands/{filename}) | {1-sentence summary} |

## Skills

Procedural workflows and reference skills agents can invoke.

| Skill | Purpose |
|-------|---------|
| [{name}](skills/{folder}/SKILL.md) | {1-sentence summary} |

Generated: {YYYY-MM-DD} via /generate-docs
```

### Archive Plan and Progress Files

Move plan and progress files to archive:
```bash
mv docs/active/YYYYMMDD-generate-docs-plan.md docs/archive/
mv docs/active/YYYYMMDD-generate-docs-progress.md docs/archive/
```

### Final Output

When all phases complete, display the full file manifest to user:

```
Documentation generation complete.

**Files Generated/Regenerated:**

Skills ({count}):
- .claude/skills/003-add-cli-command/SKILL.md
- .claude/skills/009-add-database-migration/SKILL.md
- .claude/skills/010-add-web-ui-page/SKILL.md
- .claude/skills/013-add-web-ui-write-operation/SKILL.md
- .claude/skills/015-docs-management/SKILL.md
- .claude/skills/016-exobrain-interface/SKILL.md

Areas ({count}):
- engine/src/core/AGENTS.md, engine/src/core/README.md, engine/src/core/CLAUDE.md
- ... (list all by area)

Root:
- AGENTS.md
- README.md
- CLAUDE.md
- .gemini/settings.json

**Summary:**
- Total files generated: {X}
- Stale skill folders deleted: {Y}

Harmonization:
  - {N} redundancies removed
  - {N} patterns elevated
  - {N} cross-references added

Run `git diff` to review all changes before committing.
```

---

## Scope-Limited Execution

### `plan` scope

Only runs Phase 1. Creates plan file and stops.

```
/generate-docs plan
→ Creates docs/active/YYYYMMDD-generate-docs-plan.md
→ User can review offline and run full generation later
```

### `<path>` scope

Generates docs for one area without full planning:

```
/generate-docs engine/src/core/
→ Spawns docs-area-batch-generator with single-item batch
→ Skips planning, review, harmonization
→ Useful for iterating on one area
```

```
Task parameters:
  subagent_type: "docs-area-batch-generator"
  mode: "acceptEdits"
  model: "opus"

Prompt:
"Generate docs for a single area.

Task: {\"areas\": [\"{path}\"], \"depth\": {calculated}, \"plan_path\": null}

Generate README.md and AGENTS.md for this area."
```

---

## Error Recovery

### If Generation Fails

1. Check the progress file (`docs/active/*-progress.md`) to see what completed vs failed
2. Review generated files: `git status` and `git diff`
3. **Rerun from scratch**: Delete progress file and run `/generate-docs` again

We don't attempt partial recovery. The progress file exists for visibility, not resume.

---

## Data Flow Summary

```
Phase 1: PLAN
  docs-planner → writes → docs/active/plan.md

Phase 2: GENERATE (Bounded Batching)
  orchestrator → creates → docs/active/progress.md (status tracking)

  Skills (one agent per ADR with ## Generated Skills):
    docs-adr-skill-generator ← reads ← ONE ADR
    docs-adr-skill-generator → writes → SKILL.md in skill folder
    orchestrator → updates → progress

  Areas (depth-batched, max 5 per agent):
    docs-area-batch-generator ← reads ← batch of areas at same depth
    docs-area-batch-generator → writes → README.md, AGENTS.md per area
    orchestrator → updates → progress

  Root:
    docs-generator ← reads ← all area docs
    docs-generator → writes → root CLAUDE.md, AGENTS.md, README.md

Phase 3: REVIEW
  docs-reviewer ← reads ← all generated files
  docs-reviewer → returns → issues JSON

Phase 4: HARMONIZE
  docs-harmonizer ← reads ← ADRs, all generated files
  docs-harmonizer → edits → AGENTS.md + README.md files

Finalize:
  orchestrator → writes → CLAUDE.md files, .gemini/settings.json, .claude/README.md
  orchestrator → archives → plan + progress to docs/archive/
```

---

## Agent Spawning Reference

| Phase | Agent | Model | Mode | Batching | Est. Count |
|-------|-------|-------|------|----------|------------|
| 1 | docs-planner | opus | acceptEdits | Single | 1 |
| 2 (skills) | docs-adr-skill-generator | **sonnet** | acceptEdits | 6 parallel, one per ADR | ~6 |
| 2 (areas) | docs-area-batch-generator | opus | acceptEdits | By depth, max 5 areas/batch | ~3 |
| 2 (root) | docs-generator | opus | acceptEdits | Single (after areas) | 1 |
| 3 | docs-reviewer | sonnet | default | Single | 1 |
| 4 | docs-harmonizer | opus | acceptEdits | Single | 1 |

**Total agents: ~13** (much smaller codebase than inventory_manager)

---

## Edge Cases

| Situation | Handling |
|-----------|----------|
| No ADRs found | Warn user, proceed with area docs only (no skills) |
| Area has no code files | Skip with warning |
| Line limits exceeded | Generate anyway, warn user in review phase |
| ADR and code disagree | Use hierarchy: ADR > Code > Docs. Flag discrepancy for review. |
| Plan file missing approved items | Ask user to check boxes before proceeding |
| Subagent timeout | Retry once, then report failure and continue with others |
| Hand-maintained skill in .claude/skills/ | Do NOT modify; these are intentionally hand-maintained |

---

## Context

Project structure:
!`ls -la`

Existing documentation:
!`find . -name "README.md" -o -name "AGENTS.md" -o -name "CLAUDE.md" 2>/dev/null | grep -v node_modules | grep -v .next | head -30`

ADRs:
!`ls docs/adr/ 2>/dev/null || echo "No ADRs yet"`

Skills:
!`ls .claude/skills/ 2>/dev/null || echo "No skills yet"`
