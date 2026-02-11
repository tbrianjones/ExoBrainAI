# ADR-015: Documentation Generation System

- **Status:** Accepted
- **Date:** 2026-02-11
- **Impact:** High
- **Tags:** documentation, agents, skills, generation
- **Related ADRs:** ADR-004 (Claude Code as First UI)

## Context and Problem Statement

ExoBrain needs a systematic approach to generating and maintaining documentation. The current root CLAUDE.md is hand-maintained and will drift from code as the system evolves. ADRs capture architectural decisions but the operational documentation (AGENTS.md, README.md, skills) that agents and humans rely on must be synthesized from those decisions and from code state.

A documentation generation system adapted from a mature system in another project uses ADRs as the source of truth and generates skills, AGENTS.md, and README.md via specialized agents. The central question: how should ExoBrain generate and maintain documentation so that it stays in sync with code and architectural decisions without manual upkeep?

## Decision Drivers

- ADRs are the authoritative source of truth for architectural decisions; operational documentation should be derived from them
- Documentation should be regeneratable from code state; not hand-maintained
- Agent-optimized documentation (AGENTS.md) is distinct from human documentation (README.md); agents need structured reference material, humans need narrative context
- Skills should only exist for procedural workflows; reference content belongs in AGENTS.md
- Cross-platform compatibility: CLAUDE.md references AGENTS.md; Gemini gets its own config via `.gemini/settings.json`

## Decision

### ADR-Centric Documentation Generation

Documentation is generated from ADRs (the "why") and code (the "what") through a 4-phase workflow. Each phase is implemented as an agent or skill that reads from disk and writes to disk, with a plan file as the contract between phases.

### Phase 1: Plan (docs-planner agent)

The planner agent analyzes the codebase and produces a human-readable plan file in `docs/active/`. The plan file describes what will be generated, which ADRs are inputs, and what the expected outputs are. This creates a review checkpoint before generation begins.

### Phase 2: Generate (docs-adr-skill-generator + docs-area-batch-generator + docs-generator)

Generation proceeds in three stages:

1. **ADR skill generation** (`docs-adr-skill-generator`): Scans ADRs for `## Generated Skills` sections and produces skill files. Only ADRs with that section produce skills; most ADRs produce none.
2. **Area batch generation** (`docs-area-batch-generator`): Generates AGENTS.md files bottom-up, starting from the deepest directories and working toward the root. Each area's AGENTS.md synthesizes the ADR content relevant to that area.
3. **Root generation** (`docs-generator`): Produces the root-level documentation last, incorporating summaries from all area docs.

### Phase 3: Review (docs-reviewer agent)

The reviewer validates all generated documentation against the rules defined in this ADR. It checks for completeness, consistency with ADRs, adherence to size limits, and correct cross-references.

### Phase 4: Harmonize (docs-harmonizer agent)

The harmonizer removes redundancy across generated documents, elevates shared patterns into higher-level docs, and adds cross-references between related sections. This phase ensures the documentation reads as a coherent whole rather than a collection of generated fragments.

### Key Design Decisions

**Root CLAUDE.md is regenerated.** The root CLAUDE.md becomes a single-line file referencing `@AGENTS.md`. All source content that currently lives in CLAUDE.md must exist in ADRs before generation can replace it.

**Skill folder structure.** ADR-generated skills use a `{adr-id}-{skill-name}/SKILL.md` folder structure (e.g., `013-add-web-ui-write-operation/SKILL.md`). This makes provenance clear and avoids naming collisions.

**Hand-maintained skills are preserved.** Flat `.md` skills in `.claude/skills/` (title-generation.md, summary-generation.md, tag-generation.md, exobrain.md) are not touched by the generator. These coexist with generated skills.

**Plan file as contract.** The plan file in `docs/active/` is the contract between phases. Agents read from disk and write to disk; there is no in-memory state passing between phases. After generation completes, plan files are archived to `docs/archive/`.

**Directory structure:**

| Path | Purpose |
|------|---------|
| `docs/active/` | Plan files during active generation |
| `docs/archive/` | Completed plan files |
| `docs/resources/` | Reference materials for generation (e.g., skills creation best practices) |

## Alternatives Considered

### Hand-Maintained Documentation (Current State)

- **Pro:** Simple; no tooling required; authors have full control
- **Con:** Documentation drifts from code over time. CLAUDE.md is already large and difficult to keep synchronized with the 14 existing ADRs.
- **Verdict:** Rejected. The drift problem is already observable and will worsen as ADR count grows.

### Code-First Generation (Extract from Code Comments)

- **Pro:** Documentation stays close to the code; standard approach in many projects
- **Con:** Misses architectural intent. Code comments describe "what" and "how" but not "why." ADRs capture the decision rationale, trade-offs, and rejected alternatives that agents need to make informed decisions.
- **Verdict:** Rejected. Code-first generation would produce documentation that lacks the architectural context that makes ExoBrain's docs valuable.

### ADR-Centric Generation (Chosen)

- **Pro:** ADRs capture "why"; code provides "what"; generation synthesizes both. Documentation is always regeneratable. The plan-review-harmonize workflow catches errors before they reach users.
- **Con:** Initial setup cost is nontrivial. ADRs must be comprehensive enough to serve as generation inputs; sparse ADRs produce sparse documentation.
- **Verdict:** Accepted. The investment in comprehensive ADRs pays dividends across all generated documentation.

## Consequences

### Positive

- Documentation is always in sync with code; regeneratable from ADRs and code state
- ADR-grounded documentation preserves architectural intent and decision rationale
- Agent-optimized AGENTS.md and human-optimized README.md serve their respective audiences
- Cross-platform compatibility via `.gemini/settings.json` alongside CLAUDE.md

### Negative

- Initial setup cost: agents, skills, and directory structure must be created
- ADRs must be comprehensive; a sparse ADR produces sparse or missing documentation
- Generation adds a workflow step that did not previously exist

### Neutral

- The plan file adds a human review step before generation proceeds
- Hand-maintained skills continue to coexist with generated skills indefinitely

## Generated Skills

### `docs-management`

Reference skill for documentation system commands and conventions. Use when user mentions generate docs, regenerate documentation, update AGENTS.md, create skills, refresh README, documentation is stale, or sync docs with code.

**Workflow:**
1. Run the docs-planner agent to analyze codebase and produce a plan file in `docs/active/`
2. Review the plan file; approve or request changes
3. Run docs-adr-skill-generator to produce skills from ADRs with `## Generated Skills` sections
4. Run docs-area-batch-generator to produce AGENTS.md files bottom-up (deepest directories first, root last)
5. Run docs-generator to produce root-level documentation
6. Run docs-reviewer agent to validate generated docs against rules
7. Run docs-harmonizer agent to remove redundancy, elevate shared patterns, add cross-references
8. Archive plan file from `docs/active/` to `docs/archive/`

## Agent Rules

1. MUST treat ADRs as immutable source of truth during documentation generation; never modify ADRs
2. MUST generate root CLAUDE.md as `@AGENTS.md` (single line referencing AGENTS.md)
3. MUST use bottom-up generation order: deepest directories first, root last
4. MUST NOT modify hand-maintained flat `.md` skills in `.claude/skills/` (title-generation.md, summary-generation.md, tag-generation.md, exobrain.md until replaced)
5. MUST only generate skills from ADRs that have a `## Generated Skills` section; most ADRs produce no skills
6. SHOULD keep AGENTS.md files under 150 lines; Skills under 500 lines
7. MUST archive plan files to `docs/archive/` after generation completes
8. MUST always work in feature branches; never generate docs directly on main
9. MUST use infrastructure-as-code approach: all configuration in repository files, version controlled
10. SHOULD create `.gemini/settings.json` with `{"context": {"fileName": ["AGENTS.md"]}}` for cross-platform compatibility

## References

- Skills reference: `docs/resources/20260114-claude-code-skills-creation-best-practices.md`
- ADR-004: Claude Code as first UI (commands/agents/skills distinction)
- Agents: `.claude/agents/docs-*.md`
- Command: `.claude/commands/generate-docs.md`
