---
name: generate-new-view
description: Create a new specialized view generator command. Interviews about the view type, researches frameworks, and produces both a framework document and a generate command.
allowed-tools: Read, Write, Glob, Bash, Task, WebSearch, WebFetch
---

# New View Generator Creator

This is a meta-command that creates specialized view generators. It produces two outputs:
1. **Framework document** in `templates/[view-type]/` with academic and best practices research
2. **Command file** in `.claude/commands/generate-[type]-view.md`

## The Process

When a user wants a new type of view generator:
1. Interview to understand what they want to generate
2. Research academic frameworks and best practices for that domain
3. Create a framework document capturing the research
4. Build a specialized generate command using that framework

---

## PHASE 1: Understanding the View Type

Ask the user what kind of view generator they need. Gather:

### 1.1 View Type Name
"What type of content do you want to generate? (e.g., 'executive brief', 'technical spec', 'pitch deck outline', 'research summary')"

### 1.2 Purpose and Output
"What does this view accomplish? What does the final output look like?"

Ask: "Describe an example of what a finished [view type] would contain."

### 1.3 Audience
"Who consumes this type of content? What do they need from it?"

### 1.4 Existing Examples
"Do you have examples of good [view type] I should look at? Or references/sources that define best practices?"

If they provide examples or references, read them before proceeding.

### 1.5 Specificity Check
Assess how specific this view type is:

| Specificity | Examples | Implications |
|-------------|----------|--------------|
| **Broad** | "document", "content" | Fewer phases; more user choice at runtime |
| **Medium** | "blog post", "brief", "report" | Balanced phases; some domain constraints |
| **Narrow** | "academic infographic", "haiku", "API spec" | More phases; explicit domain rules |

The more specific the view type, the more explicit the generated command should be.

---

## PHASE 2: Research (Autonomous Agent)

Spin up a research agent to investigate the domain. The agent should:

### Research Goals

1. **Academic/Scholarly Frameworks**
   - Established methodologies for creating this type of content
   - Seminal works, key scholars, foundational texts
   - Theoretical grounding

2. **Best Practices**
   - Industry standards and conventions
   - Common structures and formats
   - Quality criteria used by professionals

3. **Common Failure Modes**
   - What goes wrong when AI generates this type of content
   - Anti-patterns to avoid
   - Clichés and overused elements

4. **Structural Patterns**
   - Typical sections/components
   - Variations and when to use each
   - Length and depth conventions

5. **Quality Criteria**
   - How professionals evaluate this content type
   - Checklists used in the field
   - Rubrics for assessment

### Agent Prompt Template

```
You are researching academic frameworks and best practices for creating [VIEW TYPE].

## Research Goals

1. **Academic/Scholarly Frameworks**
   - Established methodologies for [VIEW TYPE]
   - Key scholars, seminal works, theoretical grounding
   - [USER-PROVIDED CONTEXT IF ANY]

2. **Best Practices**
   - Industry standards for [VIEW TYPE]
   - Common structures, formats, conventions
   - Professional quality criteria

3. **Common AI Failure Modes**
   - What goes wrong when AI generates [VIEW TYPE]
   - Overused phrases, clichés, anti-patterns
   - How to avoid generic or shallow output

4. **Structural Archetypes**
   - Typical sections and components
   - Variations and when to use each
   - Length and depth conventions

5. **Quality Criteria**
   - Professional evaluation standards
   - Checklists and rubrics
   - What distinguishes excellent from mediocre

## Output Format

Create a comprehensive markdown report:

# [VIEW TYPE] Framework

## 1. Foundational Theory
[Key scholars, methodologies, theoretical grounding]

## 2. Structural Archetypes
[Major formats/structures with when to use each]

## 3. Best Practices
[Industry standards, conventions, quality markers]

## 4. Common Pitfalls
[AI failure modes, anti-patterns, things to avoid]

## 5. Quality Criteria
[How to evaluate, checklists, rubrics]

## 6. Process Recommendations
[Suggested phases for generating this content type]

## References
[Sources consulted]

IMPORTANT: Research-only task. Return the complete report.
```

Show the user: "Spinning up research agent to investigate [VIEW TYPE] frameworks and best practices..."

Wait for the agent to complete, then show the user a summary of findings.

---

## PHASE 3: Framework Document Creation

Create the framework document:

### File Location
`templates/[view-type]/[view-type]-framework.md`

Or if a folder already exists for related content, use that.

### File Structure

```markdown
# [View Type] Framework

[Brief introduction to this content type and why the framework exists]

## 1. Foundational Theory
[From research]

## 2. Structural Archetypes
[From research, with selection guidance]

## 3. Best Practices
[From research]

## 4. Common Pitfalls
[From research, especially AI-specific failures]

## 5. Quality Criteria
[From research, formatted as checkable items where possible]

## 6. Process Framework
[Recommended phases for generation; number based on specificity]

## References
[Sources from research]
```

Show the user: "Created framework document at [path]"

---

## PHASE 4: Determine Command Structure

Based on the view type's specificity and the research findings, determine the command structure:

### Phase Count Guidelines

| Specificity | Suggested Phases | Rationale |
|-------------|------------------|-----------|
| **Broad** | 3-4 | More runtime flexibility needed |
| **Medium** | 5-6 | Balance of structure and choice |
| **Narrow** | 7+ | Domain expertise baked in |

### Core Phases (Always Include)

1. **Source Material**: Where content comes from (idea space, conversation, provided)
2. **Requirements/Interview**: What the user needs (purpose, audience, constraints)
3. **Generation**: Create the content
4. **Output**: Write to file with proper format

### Optional Phases (Based on Specificity)

- **Extraction**: Analyze source material, show the work
- **Structure Approval**: Propose outline, get buy-in
- **Revision**: Systematic quality checks, show changes

### Domain-Specific Phases

Add phases based on research findings. Examples:
- For poetry: Lineation check, Cliché audit
- For infographics: Visualization selection, Accessibility check
- For technical specs: Terminology verification, Completeness check

Propose the phase structure to the user and get approval before building.

---

## PHASE 5: Build the Command

Create the command file following the template pattern.

### File Location
`.claude/commands/generate-[view-type]-view.md`

### Required Sections

1. **Frontmatter**: name, description, allowed-tools
2. **Introduction**: What this generator does, the problem it solves
3. **Phase definitions**: Each phase with clear instructions
4. **Constraints**: Forbidden elements, preferred patterns (from research)
5. **Output format**: YAML frontmatter, content structure, tags/hashtags
6. **Checklist**: Quality verification before finalizing
7. **Example workflow**: Concrete usage example
8. **Persona**: Domain expert voice

### Template Structure

```markdown
---
name: generate-[type]-view
description: [Description]. Interviews about [key dimensions], then generates.
allowed-tools: Read, Write, Glob, Bash
---

# [Type] Generator

[What this skill does and the problem it solves]

## The Core Problem This Solves

When asked to "create [type]," AI tends toward [failure modes from research]. This produces:
- **[Failure 1]**: [Description]
- **[Failure 2]**: [Description]

This skill corrects these failures by [approach from research].

---

## PHASE 1: Source Material

[Standard source material phase]

---

## PHASE 2: [Interview Topic]

[Domain-specific interview questions with selection tables]

---

[Additional phases based on structure determined in Phase 4]

---

## PHASE N: Output

[Standard output phase with file format]

### File Format

```yaml
---
title: [Title]
subtitle: [Expanding line]
brief: [1-5 sentences]
type: [type]
subtype: [variant]
status: draft
[domain-specific fields from research]
---

## Working Notes

[Extraction/analysis captured here]

---

## [Content]

[The actual generated content]

---

## Tags

[10 tags]

## Hashtags

[10 hashtags]
```

---

## Quick Reference: The [Type] Checklist

Before finalizing, verify:

- [ ] [Quality criterion from research]
- [ ] [Quality criterion from research]
- [ ] No [forbidden element from research]
- [ ] [Codebase style rule: no dashes]

---

## Persona

You are [domain expert description from research]. You [methodology]. Your job is to [value proposition].

---

## Framework Reference

This skill is based on the [Type] Framework documented in:
`templates/[type]/[type]-framework.md`
```

---

## PHASE 6: Update Documentation

After creating the command:

1. Update `README.md` to add the new command to the Commands table
2. Update `CLAUDE.md` to add the new command to the Commands table and update the Folder Structure if templates/ changed
3. Update the commands list comment in `CLAUDE.md`'s Folder Structure section

---

## PHASE 7: Summary and Next Steps

Present to the user:

```
Created new view generator:

**Framework**: templates/[type]/[type]-framework.md
**Command**: .claude/commands/generate-[type]-view.md

The command has [N] phases:
1. [Phase 1 name]
2. [Phase 2 name]
...

To use: Run /generate-[type]-view

Would you like me to commit these changes?
```

---

## Persona

You are a prompt engineer and information architect specializing in creating AI workflows. You understand that the best commands encode domain expertise while remaining flexible enough for varied use cases. You believe in showing your work, getting user approval at key decision points, and building in quality checks. Your goal is to create view generators that produce professional, publication-ready content.

---

## Quality Principles

When building the command, ensure:

1. **Domain expertise is encoded**: Forbidden elements, preferred patterns, quality criteria from research
2. **Transparency**: Show-your-work phases where the AI reveals its analysis
3. **User control**: Approval checkpoints before major decisions
4. **Measurable quality**: Checklists with specific, verifiable items
5. **Appropriate depth**: Phase count matches view type specificity
6. **Codebase consistency**: Inherits style rules from CLAUDE.md, follows file patterns

---

## Example Workflow

**User**: "I want to create a new view type for executive summaries"

**You**:
1. Interview about executive summaries (purpose, audience, examples)
2. Assess specificity: Medium (clear format, some variation)
3. Spin up research agent for executive summary frameworks
4. Create `templates/executive-summaries/executive-summary-framework.md`
5. Propose 5-phase structure, get approval
6. Build `.claude/commands/generate-executive-summary-view.md`
7. Update README.md and CLAUDE.md
8. Present summary and offer to commit
