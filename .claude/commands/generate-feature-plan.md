---
description: Captures product context, architectural decisions, and implementation details from conversation into a structured plan document. Use when user mentions create plan, feature plan, capture discussion, document feature, write up plan, implementation plan, or planning document. Produces docs/active/ plans with Agent Quick Start sections for AI handoff.
argument-hint: [feature-name]
allowed-tools: Read, Glob, Grep, Write, AskUserQuestion, Task
permissionMode: acceptEdits
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

Write to `docs/active/{YYYYMMDD}-{topic-kebab-case}-plan-claude.md` using this structure:

**Frontmatter:** `status: Planning`, `date`, `branch` (if applicable), `related-adrs`

**Sections (in order):**
1. **Summary** - 2-3 sentence executive summary
2. **Agent Quick Start** - Files to load, ADRs to read, relevant skills, areas to explore
3. **Problem Statement** - User persona, pain point, current state, business impact
4. **Success Metrics** - Table: metric, baseline, target, measurement
5. **Feature Overview** - What it does + core user flow (numbered steps)
6. **Scope** - In scope, out of scope (do not build), dependencies
7. **User Stories + Acceptance Criteria** - "As a..I want..so that" format with Given-When-Then criteria
8. **Key Decisions** - Table + detail blocks: choice, alternatives, rationale
9. **Technical Approach** - Architecture, code patterns, file paths, services
10. **Implementation Phases** - Phase 1, Phase 2, etc. (or "to be defined")
11. **Open Questions** - Table: question, impact, notes
12. **Future Considerations** - Discussed but deferred items
13. **Verification** - Test commands, manual checks, success criteria
14. **References** - Related plans, ADR to generate

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
