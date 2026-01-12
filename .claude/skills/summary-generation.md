---
name: summary-generation
description: Generate effective summaries and briefs for any content type
allowed-tools: Read
---

# Summary Generation

Generate summaries optimized for specific content types, platforms, and audiences.

## How This Skill Is Used

This skill is invoked by view-generation commands or any workflow that produces content requiring summaries, abstracts, or briefs. When invoked, Claude reads the framework and applies it to generate appropriate summaries.

## Framework Location

```
templates/summary-generation/summary-generation-framework.md
```

Read this framework before generating summaries. It contains type-specific guidelines, cognitive principles, and quality criteria.

## Generation Process

### 1. Determine Summary Type

Identify what kind of summary is needed:

| Type | When to Use |
|------|-------------|
| Article summary | Blog posts, news, features |
| Executive summary | Reports, proposals, business docs |
| Abstract | Academic papers, research |
| Meta description | SEO, search results |
| Social summary | Platform-specific sharing |
| Email preheader | Email preview text |
| TL;DR | Quick internet-style summary |

### 2. Apply Length Constraints

| Type | Target Length |
|------|---------------|
| Article summary | 50-100 words |
| Executive summary | 1-2 pages (max 10% of doc) |
| Abstract | 150-250 words |
| Meta description | 150-160 characters |
| Twitter/X | 71-100 characters |
| LinkedIn | ~100 characters |
| Email preheader | 40-100 characters |
| TL;DR | 1-2 sentences |

### 3. Generate Summary

Follow the inverted pyramid:
1. **Lead**: Most important information first
2. **Support**: Key evidence and context
3. **Background**: Details that can be cut

### 4. Present Output

Format output as:

```
## Summary

[Type]: [Article Summary / Executive Summary / Abstract / etc.]
Length: [X words / X characters]

---

[Summary content here]

---

**Key Points Captured**:
- [Point 1]
- [Point 2]
- [Point 3]
```

## Summary Styles

Adjust based on context:

- **Informative**: States findings and conclusions (default for most content)
- **Descriptive**: States purpose and scope only (when results are unavailable)
- **Teaser**: Creates curiosity (marketing, social media)
- **Technical**: Precise, jargon-appropriate (academic, documentation)

## Quality Checklist

Before presenting, verify:

1. Contains the single most important takeaway
2. Makes sense without reading the original
3. Uses own words (not verbatim copying)
4. Respects length constraints
5. Front-loads the key information
6. Excludes examples, anecdotes, qualifications
7. Answers "so what?" (why it matters)

## Platform-Specific Notes

**SEO (Meta Descriptions)**:
- Key info in first 100 characters
- Include primary keyword naturally
- Unique for every page
- Call-to-action if appropriate

**Social Media**:
- Hook in first line (visible before "see more")
- Engagement prompt at end
- Platform-appropriate tone

**Academic (Abstracts)**:
- Follow IMRAD structure
- Include 3-5 keywords
- No citations or new information
- Write after completing paper

## Example Invocation

A command might invoke this skill as:

```
Generate a summary for this blog post about AI ethics.
Type: Article summary + Meta description
Audience: General tech readers
```

The skill then reads the framework and produces summaries matching the requested types.
