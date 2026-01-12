---
name: tag-generation
description: Generate effective tags, hashtags, and topic classifications for any platform
allowed-tools: Read
---

# Tag Generation

Generate tags and hashtags optimized for specific platforms, content types, and discovery goals.

## How This Skill Is Used

This skill is invoked by view-generation commands or any workflow that produces content requiring tags, hashtags, or topic classifications. When invoked, Claude reads the framework and applies it to generate appropriate tags.

## Framework Location

```
templates/tag-generation/tag-generation-framework.md
```

Read this framework before generating tags. It contains platform-specific limits, strategic mix guidelines, and common pitfalls.

## Generation Process

### 1. Identify Platform

Determine where content will be published and apply platform limits:

| Platform | Optimal # | Format |
|----------|-----------|--------|
| Instagram | 3-5 | #lowercase or #PascalCase |
| Twitter/X | 1-2 | #lowercase |
| LinkedIn | 3-5 | #PascalCase |
| TikTok | 3-5 | #lowercase |
| YouTube | 5-12 tags | Plain text (metadata) |
| Blog | 3-7 tags | Plain text |
| Academic | 3-6 keywords | Plain text |

### 2. Analyze Content

Extract:
- Primary topic (1-2 tags)
- Secondary topics (1-2 tags)
- Audience/niche (1 tag)
- Trending relevance (if applicable)

### 3. Build Strategic Mix

| Category | Purpose | Example |
|----------|---------|---------|
| Broad | Maximum reach | #marketing |
| Niche | Targeted audience | #b2bsaasmarketing |
| Trending | Current visibility | #AI2026 |
| Branded | Brand recognition | #YourBrandName |
| Evergreen | Long-term discovery | #contentcreation |

**Recommended Mix**: 60% evergreen, 30% trending, 10% experimental

### 4. Present Output

Format output as:

```
## Tags

**Platform**: [Instagram / Twitter / LinkedIn / etc.]
**Count**: [X tags]

### Recommended Tags
1. [tag] - [category: broad/niche/trending] - [rationale]
2. [tag] - [category] - [rationale]
3. [tag] - [category] - [rationale]

### Alternative Options
- [tag] - [when to use instead]
- [tag] - [when to use instead]

### Avoid
- [problematic tag] - [reason: banned/oversaturated/irrelevant]
```

## Platform-Specific Notes

**Instagram**:
- Check for banned hashtags before recommending
- Place in caption for small accounts; first comment for large accounts
- Avoid generic tags like #love #instagood (too saturated)

**Twitter/X**:
- Maximum 2 hashtags; more appears spammy
- Trend relevance matters; timing is critical
- No hashtag-jacking (irrelevant trending tags)

**LinkedIn**:
- Always use PascalCase for accessibility
- Place at end of post
- Combine with keyword strategy for algorithm

**TikTok**:
- Never recommend generic #fyp #foryou (diminishing returns)
- Check TikTok Creative Center for trends
- Niche tags outperform broad ones

**YouTube**:
- Tags are metadata, not hashtags
- First tag should be primary keyword
- Don't duplicate title content in tags

**Blog/CMS**:
- Never create tags used by only one post
- Categories are hierarchical; tags are flat
- Avoid both singular and plural versions

## Quality Checklist

Before presenting, verify each tag:

1. Relevant to content (no hashtag-jacking)
2. Active (has recent posts/searches)
3. Not banned or problematic
4. Appropriate reach level (not too saturated)
5. Correctly formatted for platform
6. Count within platform guidelines

## Example Invocation

A command might invoke this skill as:

```
Generate hashtags for this LinkedIn post about remote work productivity.
Platform: LinkedIn
Audience: HR professionals and managers
Tone: Professional
```

The skill then reads the framework and produces platform-appropriate tags with rationale.
