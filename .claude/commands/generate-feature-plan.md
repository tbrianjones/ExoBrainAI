---
description: Generate a feature plan from the current conversation
argument-hint: [feature-name]
allowed-tools: Read, Glob, Grep, Write, AskUserQuestion, Task
---

# Generate Feature Plan

Capture product context, architectural decisions, and implementation details from the current conversation into a structured plan document. The plan serves both human stakeholders and AI agents who will implement the feature.

## Output

`docs/active/{YYYYMMDD}-{topic-kebab-case}-plan-claude.md`

## Process

### 1. Gather Topic

Use `$ARGUMENTS` as feature name. If missing, ask user for the feature name.

### 2. Scan Conversation Context

Extract from the thread:

**Product Context:**
- User personas and who benefits
- Problem being solved and pain points
- Business value or impact discussed
- Success criteria or metrics mentioned
- User flows and edge cases
- What was explicitly deferred or excluded

**Technical Context:**
- Architectural decisions and rationale
- Implementation details discussed
- File paths and services affected
- Phased implementation plan (if developed)
- Open questions and future considerations

### 3. Research

Spawn Explore sub-agents to:
- Verify file paths mentioned in conversation
- Check for related existing plans in docs/active/
- Find related ADRs to reference
- Identify which skills from `.claude/skills/` are relevant to this feature

### 4. Present Extracted Content

Show summary of what was found. Ask user to confirm/correct:
- Problem statement and user value
- Key decisions
- Implementation scope
- Technical approach

### 5. Ask Explicitly for Gaps

Don't generate with empty sections. Probe by category:

**Product Gaps (ask if missing):**
- Who is the user persona for this feature?
- What problem does this solve for them?
- What does success look like? How will we measure it?
- What is explicitly out of scope?
- What's the core user flow?

**Technical Gaps (ask if missing):**
- What database/API changes are needed?
- What services or files are affected?
- What are the performance/security requirements?
- What's the rollback or error handling plan?
- If phased plan wasn't in thread, note it needs development

### 6. Generate Plan

Write to `docs/active/{YYYYMMDD}-{topic-kebab-case}-plan-claude.md` using this template:

```markdown
---
status: Planning
date: {YYYY-MM-DD}
branch: {if applicable}
related-adrs: [{list}]
---

# {Feature Name} Plan

## Summary
{2-3 sentence executive summary - what it does and why it matters}

## Agent Quick Start
> Read this section first if you're an AI agent picking up this plan.

**Load these files:**
- {primary files to modify}
- {related config or types}

**Read these ADRs:**
- ADR-0XX: {relevant decision}

**Relevant skills:**
- `{skill-name}` - {why relevant}

**Explore these areas:**
- `{directory/}` - {what's there}

## Problem Statement
- **User Persona:** {who experiences this problem}
- **Pain Point:** {what problem they face}
- **Current State:** {how they work around it now}
- **Business Impact:** {why this matters}

## Success Metrics
| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| {metric} | {current} | {goal} | {how measured} |

## Feature Overview
{What the feature does - 2-3 sentences}

### Core User Flow
1. User does X
2. System responds with Y
3. User sees Z

## Scope

### In Scope
- ...

### Out of Scope (Do Not Build)
- ...

### Dependencies
- ...

## User Stories + Acceptance Criteria

### Story 1: {Title}
**As a** {persona}, **I want** {action} **so that** {benefit}

**Acceptance Criteria:**
- [ ] Given {setup}, when {action}, then {result}
- [ ] Given {setup}, when {action}, then {result}

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|

### Decision 1: {Title}
**Choice:** {what was decided}
**Alternatives:** {what else was considered}
**Rationale:** {why this choice}

## Technical Approach
{Architecture, code patterns, file paths, services affected}

## Implementation Phases
**Phase 1:** {description}
**Phase 2:** {description}

*If not discussed: "Implementation phases to be defined during planning."*

## Open Questions
| Question | Impact | Notes |
|----------|--------|-------|

## Future Considerations
{Discussed but deferred items}

## Verification
- [ ] {test commands}
- [ ] {manual verification steps}
- [ ] {success criteria check}

## References
- Related plans: ...
- Will generate ADR: ADR-0XX ({topic})
```

### 7. Verify Output

Show file path created and summarize:
- Product context captured
- Technical decisions documented
- Gaps that still need resolution

## Key Behaviors

- **Product first, technical second** - always lead with user value before architecture
- **Don't invent decisions** - only capture what was discussed
- **Ask about gaps by category** - distinguish product vs technical missing info
- **Use Given-When-Then** - acceptance criteria must be testable
- **Explicit out-of-scope** - prevent AI from over-building
- **Keep it scannable** - bullets and tables over prose paragraphs
- **Self-contained for agents** - include enough context (files, ADRs, skills) that a fresh agent can execute without human guidance
- **Verify file paths** - use sub-agents to confirm references exist
- **Link to ADRs** - identify related ADRs
- **Note future ADR** - suggest if this should become an ADR later