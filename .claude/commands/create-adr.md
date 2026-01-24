---
description: Creates new Architecture Decision Records (ADRs) documenting significant architectural choices. Use when user mentions create ADR, new ADR, document decision, record architecture choice, why did we choose, capture rationale, or architectural decision. Produces MADR-format ADRs with Agent Rules that flow into generated documentation.
argument-hint: [topic]
allowed-tools: Task
disable-model-invocation: true
---

# Create ADR

Spawn the adr-generator agent to create a new ADR.

Topic context: $ARGUMENTS

## Decision Triggers (Quick Reference)

Create an ADR when your decision:
- Affects multiple team members
- Has long-term consequences or trade-offs
- Is architecturally significant (not just implementation detail)
- Has security implications
- Would be hard to reverse

**If someone asked "why?" twice about this decision, write an ADR.**

See `docs/reference/20260120-adr-best-practices.md` for comprehensive guidance.

## Related Commands

- `/update-adr <id>` - Update or deprecate existing ADRs
