# Command Generation Best Practices

*Research compiled by autonomous agent on 2026-01-10. Sources include prompt engineering guides, meta-prompting research, and codebase pattern analysis.*

A comprehensive framework for creating AI commands that generate structured outputs through interview-style interactions.

## 1. Interview Phase Patterns

### Question Sequencing Strategies

**The Flipped Interaction Pattern**
Rather than users asking questions, the command asks the user a series of questions aimed at achieving a specific outcome. This is the dominant pattern in interview-style prompts.

**Question Type Sequencing**
Effective interview sequences follow this progression:

1. **Motivation questions**: "What draws you to this?"
2. **Grounding questions**: "Can you give me an example?"
3. **Challenge questions**: "What's the hardest part of this?"
4. **Audience questions**: "Who is this for?"
5. **Vision questions**: "What would success look like?"
6. **Edge questions**: "What are you unsure about?"

**Selection Tables**
Present options via structured tables:

```markdown
| Form | Best For | Characteristics |
|------|----------|-----------------|
| **Option A** | [Use case] | [Details] |
| **Option B** | [Use case] | [Details] |
```

This pattern:
- Provides clear options without overwhelming
- Shows tradeoffs explicitly
- Allows quick selection with informed choice
- Reduces back-and-forth clarification

### Interview Guidelines

- **One question at a time**: Never stack questions
- **Listen first**: Follow-ups should respond to what they said
- **Go deeper before going wider**: Exhaust a thread before moving on
- **Maximum 10 questions/topics**: Respect user time
- **Be curious, not leading**: Draw out their thinking, don't impose yours
- **Note emotional cues**: Enthusiasm, hesitation, uncertainty are signals

### Balancing Thoroughness with Efficiency

1. **Phased disclosure**: Not all questions upfront; reveal complexity as needed
2. **Sensible defaults**: Allow skipping if user is satisfied with default
3. **Hierarchical questions**: Ask high-level first, drill down only if needed

---

## 2. Multi-Phase Process Design

### Phase Architecture Pattern

**Phase 1: Source Material / Context Loading**
- Determine what material to work with
- Load all relevant context before proceeding
- Non-negotiable; skip it and outputs suffer

**Phase 2: Requirements Gathering / Interview**
- Understand purpose, audience, goals
- Gather preferences for form, style, approach
- Use selection tables for structured choices

**Phase 3: Extraction / Analysis (Show This Work)**
- Analyze source material systematically
- Extract key elements, themes, data points
- **Critical: Show this work to the user** for transparency

**Phase 4: Structural Plan (Get Approval)**
- Propose the architecture before drafting
- Show the outline/structure explicitly
- Get user approval before proceeding to generation

**Phase 5: Generation / Drafting**
- Execute the plan following established constraints
- Apply style rules and quality guidelines
- Draw on extracted material

**Phase 6: Revision / Quality Review (Show This Work)**
- Systematic review against criteria
- Show what changed and why
- Verify against checklist

**Phase 7: Output**
- Present final result
- Write to appropriate location
- Include all required metadata

### Why Phases Matter

Key benefits:
1. **Checkpoints**: User can correct course early
2. **Transparency**: User sees reasoning, builds trust
3. **Quality**: Each phase has focused quality criteria
4. **Maintainability**: Phases can be modified independently

---

## 3. Output Specification Structure

### YAML Frontmatter Pattern

Standard frontmatter fields:

```yaml
---
title: [Title]
subtitle: [Single line expanding on title]
brief: [1-5 sentences capturing core thesis]
type: [content type]
subtype: [specific variant]
status: [draft | review | final]
audience: [who this is for]
voice: [description of tone]
style:
  [attribute]: [0-100]
  [attribute]: [0-100]
source: [where content came from]
---
```

### Working Notes Section

Include a "Working Notes" section that captures extraction phase output:
- Core Themes / Core Message
- Key elements extracted
- Structural decisions made

This serves dual purposes:
1. **Audit trail**: How decisions were made
2. **Context for iteration**: Future edits can reference original analysis

### Tags and Hashtags

Require 10 tags and 10 hashtags:
- **Tags**: Lowercase, spaces allowed, for categorization
- **Hashtags**: No spaces, social media ready, for distribution

---

## 4. Meta-Command Patterns

### Conductor-Expert Architecture

A central command directs multiple specialized tasks. Separation of concerns allows:
- Focused expertise per command
- Orchestration of multi-step workflows
- Reuse of specialized components

### Template Inheritance Pattern

Layer simpler prompts into more complex ones, creating a hierarchy of reusable components:
- **Base pattern**: Context loading, interview, extraction, generation, output
- **Specialized variants**: Add domain-specific phases

### Creating New View-Generating Commands

1. **Copy structure** from existing generators
2. **Identify domain-specific** constraints, frameworks, forbidden patterns
3. **Define extraction criteria** specific to the content type
4. **Create quality checklist** based on domain expertise
5. **Design output format** with appropriate frontmatter and sections
6. **Establish persona** that brings domain expertise

---

## 5. Quality Assurance Embedding

### Anti-Pattern Lists

Preemptive quality control through forbidden elements:

```markdown
**FORBIDDEN [ELEMENTS]**:
- [Common AI failure 1]
- [Common AI failure 2]
- [Domain-specific cliché]
```

Benefits:
- Prevents common AI failure modes
- Encodes domain expertise
- Creates measurable criteria

### Embedded Checklists

End with verification checklists:

```markdown
## Quick Reference Checklist

Before finalizing, verify:
- [ ] [Quality criterion 1]
- [ ] [Quality criterion 2]
- [ ] No [forbidden element]
```

### Show-Your-Work Phases

Mark phases with "(Show This Work)":
- Phase 3: Extraction (Show This Work)
- Phase 6: Revision (Show This Work)

Benefits:
1. **Transparency**: User can verify reasoning
2. **Catchpoint**: Errors visible before final output
3. **Trust building**: Shows the AI isn't black-boxing

### Domain Framework Integration

Integrate academic/professional frameworks as quality criteria:
- Grounds quality in established expertise
- Provides measurable dimensions
- Creates shared vocabulary with users

---

## 6. Specificity and Phase Count

### Specificity Determines Depth

| Specificity | Examples | Phase Count | Rationale |
|-------------|----------|-------------|-----------|
| **Broad** | "document", "content" | 3-4 | More runtime flexibility needed |
| **Medium** | "blog post", "brief" | 5-6 | Balanced structure and choice |
| **Narrow** | "academic infographic", "haiku" | 7+ | Domain expertise baked in |

The more specific the view type, the more explicit the generated command should be.

---

## 7. Template Structure

```markdown
---
name: generate-[type]-view
description: [Description]. Interviews about [key dimensions], then generates.
allowed-tools: Read, Write, Glob, Bash
---

# [Type] Generator

[What this skill does and the problem it solves]

## The Core Problem This Solves

When asked to "create [type]," AI tends toward [failure modes]. This produces:
- **[Failure 1]**: [Description]
- **[Failure 2]**: [Description]

This skill corrects these failures by [approach].

---

## PHASE 1: Source Material

[Standard source material phase]

---

## PHASE 2: [Interview Topic]

[Domain-specific interview with selection tables]

---

[Additional phases based on specificity]

---

## PHASE N: Output

[Output phase with file format specification]

---

## Quick Reference Checklist

Before finalizing, verify:
- [ ] [Quality criterion]
- [ ] [Quality criterion]
- [ ] No [forbidden element]

---

## Persona

You are [domain expert]. You [methodology]. Your job is to [value proposition].
```

---

## References

### Web Research
- [Shadecoder Prompt Engineering Guide](https://www.shadecoder.com/topics/prompt-engineering-a-comprehensive-guide-for-2025)
- [Lakera Ultimate Guide to Prompt Engineering](https://www.lakera.ai/blog/prompt-engineering-guide)
- [Prompt Engineering Best Practices 2025](https://www.news.aakashg.com/p/prompt-engineering)
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [PromptHub Meta Prompting Guide](https://www.prompthub.us/blog/a-complete-guide-to-meta-prompting)
- [PromptHub Prompt Patterns Guide](https://www.prompthub.us/blog/prompt-patterns-what-they-are-and-16-you-should-know)
- [IBM Meta Prompting](https://www.ibm.com/think/topics/meta-prompting)
- [Prompting Guide Meta Prompting](https://www.promptingguide.ai/techniques/meta-prompting)
- [Google Prompt Design Strategies](https://ai.google.dev/gemini-api/docs/prompting-strategies)
- [LlamaIndex Document AI](https://www.llamaindex.ai/blog/document-ai-the-next-evolution-of-intelligent-document-processing)
- [Quality Assurance for Prompts](https://mrebi.com/en/prompt-engineering/quality-assurance/)
- [Chain-of-Verification](https://relevanceai.com/prompt-engineering/implement-chain-of-verification-to-improve-ai-accuracy)
- [Trust But Verify Pattern](https://addyo.substack.com/p/the-trust-but-verify-pattern-for)
- [Prompt Engineering Best Practices 2025 Patterns](https://promptbuilder.cc/blog/prompt-engineering-best-practices-2025)
- [Vanderbilt Prompt Patterns](https://www.vanderbilt.edu/generative-ai/prompt-patterns/)

### Codebase Files Analyzed
- `.claude/commands/generate-view.md`
- `.claude/commands/generate-poem-view.md`
- `.claude/commands/generate-academic-infographic-view.md`
- `.claude/commands/ideate.md`
- `.claude/commands/instantiate-idea.md`
- `.claude/commands/generate-transcript.md`
- `CLAUDE.md`
