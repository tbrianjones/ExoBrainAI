---
name: title-generation
description: Generate effective titles and headlines for any content type
allowed-tools: Read
---

# Title Generation

Generate titles optimized for specific media types, audiences, and goals.

## How This Skill Is Used

This skill is invoked by view-generation commands (`/generate-view`, `/generate-poem-view`, etc.) or any workflow that produces titled content. When invoked, Claude reads the framework and applies it to generate title options.

## Framework Location

```
templates/title-generation/title-generation-framework.md
```

Read this framework before generating titles. It contains media-specific guidelines, psychological principles, formulas, and quality criteria.

## Generation Process

### 1. Determine Context

Identify before generating:
- **Content type**: blog post, email, social post, academic paper, marketing, etc.
- **Platform**: where it will be published (web, email, YouTube, LinkedIn, etc.)
- **Tone**: serious, fun, professional, casual, urgent, curious
- **Goal**: inform, persuade, entertain, convert, share

### 2. Generate Title Options

Produce **5 title options** in different styles:

| Style | Description |
|-------|-------------|
| **Straightforward** | Clear, accurate, no cleverness; states what it is |
| **Curious** | Creates genuine curiosity; makes reader want to know more |
| **Benefit-Focused** | Emphasizes what reader gains |
| **Formula-Based** | Uses proven structure (How-To, Listicle, Question, etc.) |
| **Platform-Optimized** | Tailored for specific platform constraints and conventions |

### 3. Present Options

Format output as:

```
## Title Options

1. **[Straightforward]**: "Title here"
2. **[Curious]**: "Title here"
3. **[Benefit-Focused]**: "Title here"
4. **[Formula-Based]**: "Title here"
5. **[Platform-Optimized]**: "Title here"

**Recommendation**: Option [N] because [brief rationale based on context].
```

### 4. Quality Check

Before presenting, verify each title:
- Accurately represents content (no misleading)
- Fits platform character limits
- Uses appropriate tone for audience
- Contains keywords if SEO matters
- Would you click on it?

## Platform Quick Reference

| Platform | Max Length | Priority |
|----------|-----------|----------|
| Blog/SEO | 50-60 chars | Keywords front-loaded |
| Email | 35-50 chars | Personalization, no spam words |
| YouTube | 50-60 chars | Searchability + engagement |
| Twitter/X | Concise | Immediate clarity |
| LinkedIn | Professional | Industry keywords |
| Academic | Fewest words possible | Precision, keywords |

## Tone Modifiers

When the caller specifies tone, adjust accordingly:

- **Fun/Funny**: Allow puns, wordplay, personality; prioritize memorability over SEO
- **Professional**: Formal, clear, authoritative; no cleverness
- **Urgent**: Time-sensitive language; action-oriented
- **Curious**: Open loops; "secret," "surprising," question formats
- **Authoritative**: "Complete Guide," "Expert," "Definitive"

## Example Invocation

A command might invoke this skill as:

```
Generate titles for this blog post about remote work productivity.
Context: Educational blog, SEO matters, professional audience.
Tone: Helpful, authoritative.
```

The skill then reads the framework and produces 5 options with a recommendation.
