---
description: Updates existing Architecture Decision Records with implementation changes, status updates, or deprecation. Use when user mentions update ADR, modify ADR, change ADR status, deprecate ADR, ADR is outdated, or implementation changed from ADR. Triggers on docs/adr/*.md files. Handles clarifications, status changes, and deprecation workflows.
argument-hint: <id>
allowed-tools: Read, Glob, Grep, Edit, AskUserQuestion, Task
disable-model-invocation: true
---

# Update ADR

Lightweight update for existing ADRs during active development.

**Reference:** See `docs/reference/20260120-adr-best-practices.md` for lifecycle management guidance.

## Update vs Supersede vs Deprecate

| Action | When to Use | Command |
|--------|-------------|---------|
| **Update** | Clarifications, status updates, adding details | This command |
| **Supersede** | Fundamental approach change, different technology | `/create-adr` with `supersedes: [id]` |
| **Deprecate** | Decision no longer relevant (feature removed) | This command (change status) |

**Key principle:** If the user asks for an update and a simple update is appropriate, proceed without asking. Only ask if you believe the changes warrant superseding or deprecation instead.

## Process

### 1. Load ADR

Find and read `docs/adr/$ARGUMENTS-*.md`. Briefly show title and key metadata so user confirms correct ADR.

### 2. Gather Context

Scan the conversation thread for relevant changes - implementation details, new patterns discovered, problems solved, pending items addressed.

### 3. Research

Spawn Explore sub-agents as needed to verify claims, find file paths, or gather context from the codebase. Don't assume - verify.

### 4. Assess Change Type

Evaluate whether the changes are:
- **Minor** (clarifications, status updates, new pending items) → Proceed with update
- **Major** (fundamental approach change) → Ask user if they want to supersede instead
- **Obsolete** (decision no longer applies) → Ask user if they want to deprecate

**Only ask if you're proposing to change the user's intended action.** If user asked for update and update is appropriate, proceed.

### 5. Propose Changes and Ask Questions

Present a brief summary of what appears to have changed. Then actively ask questions:
- Use AskUserQuestion for anything unclear or ambiguous
- Probe for additional context on architecturally critical changes
- Ask if there's anything else that changed
- Don't let the user just "OK" through - prompt for explicit input on important changes

### 6. Verify

Confirm all new claims:
- File paths exist
- Patterns match actual code
- Rules are testable and specific

### 7. Present Formal Diff

Show complete before/after for each section being modified. If possible, open the diff in VS Code for easier review. Otherwise display inline diff clearly.

### 8. Apply Changes

After approval:
- Update `updated: YYYY-MM-DD` in frontmatter
- Edit the ADR file

## Deprecation Workflow

When deprecating an ADR (decision no longer relevant):

1. Change `status: Deprecated` in frontmatter
2. Add deprecation note at start of Context section:
   ```
   **Deprecated (YYYY-MM-DD):** {Reason - e.g., "Feature X was removed" or "Superseded by new architecture"}
   ```
3. Keep the ADR file (historical value)
4. **If the decision is being replaced** (not just removed), prompt user to create a new ADR:
   - "This ADR is being deprecated. Should we create a new ADR to document the replacement approach?"
   - If yes, spawn `/create-adr` with context from the deprecated ADR

## Context

!`ls docs/adr/$ARGUMENTS-*.md 2>/dev/null || echo "ADR not found - check ID"`
