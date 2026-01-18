---
description: Update an existing ADR with changes from current work
argument-hint: <id>
allowed-tools: Read, Glob, Grep, Edit, AskUserQuestion, Task
---

# Update ADR

Lightweight update for existing ADRs during active development. For fundamental decision changes, use `/create-adr` to supersede.

## Process

### 1. Load ADR

Find and read `docs/adr/$ARGUMENTS-*.md`. Briefly show title and key metadata so user confirms correct ADR.

### 2. Gather Context

Scan the conversation thread for relevant changes - implementation details, new patterns discovered, problems solved, pending items addressed.

### 3. Research

Spawn Explore sub-agents as needed to verify claims, find file paths, or gather context from the codebase. Don't assume - verify.

### 4. Propose Changes and Ask Questions

Present a brief summary of what appears to have changed. Then actively ask questions:
- Use AskUserQuestion for anything unclear or ambiguous
- Probe for additional context on architecturally critical changes
- Ask if there's anything else that changed
- Don't let the user just "OK" through - prompt for explicit input on important changes

### 5. Verify

Confirm all new claims:
- File paths exist
- Patterns match actual code
- Rules are testable and specific

### 6. Present Formal Diff

Show complete before/after for each section being modified. If possible, open the diff in VS Code for easier review. Otherwise display inline diff clearly.

### 7. Apply Changes

After approval:
- Update `updated: YYYY-MM-DD` in frontmatter
- Edit the ADR file

## Context

!`ls docs/adr/$ARGUMENTS-*.md 2>/dev/null || echo "ADR not found - check ID"`
