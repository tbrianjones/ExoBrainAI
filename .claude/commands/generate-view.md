---
name: generate-view
description: Create production content (blog post, brief, video script, etc.) within an idea space. Interviews about voice and style, then generates.
allowed-tools: Read, Write, Glob, Bash
---

# View Generator

Create production content within an idea space. If working from an existing idea, load the full context first before interacting with the user.

## CRITICAL: Load Context First

Before any interaction with the user, you MUST load the entire idea folder:

1. **Read the README.md** in the idea folder to understand:
   - What the idea is about
   - Its origin and open questions
   - Any planned views

2. **Load ALL transcripts** from `transcripts/`:
   - Read every `.md` file in the transcripts folder
   - These contain the raw ideation—the source material for views
   - Pay attention to the Ideas & Themes sections and Full Transcript

3. **Load ALL assets** from `assets/`:
   - Read every file in the assets folder
   - These are structured entities: characters, settings, concepts, objects
   - Assets inform voice, details, and consistency

4. **Scan existing views** in `views/`:
   - See what's already been created
   - Understand the voice and style patterns already established

Only AFTER loading this context should you proceed with the user interaction.

## Content Guidelines

When writing prose:
- **No dashes or double dashes.** Telltale AI pattern. Use semicolons or restructure.
- **Use semicolons** to join related independent clauses or pivot thoughts.
- **Use ellipses (...)** sparingly for trailing off or unfinished thinking.
- Keep prose grounded; avoid flowery or overwrought language.
- Preserve the human's phrasing when it captures the idea well.
- Draw on transcript material; use the human's own words when powerful.

## Process (After Loading Context)

1. **Confirm the content type**:
   - What kind of output? (blog post, technical overview, video script, essay, brief, infographic, poem, etc.)
   - Who is the audience?
   - What's the core purpose or thesis?
   - Reference what you learned from transcripts if relevant

2. **Define the voice**:
   - Ask for a description of the voice/tone/personality
   - Or suggest one based on what you read in transcripts
   - Examples: "conversational expert", "curious explorer", "direct and punchy"

3. **Calibrate style attributes**:
   - Discuss relevant style dimensions and assign 0-100 scores
   - Common ones: humor, technical, formality, intensity, warmth, provocative
   - Any term that fits works

4. **Build the outline**:
   - Create structural skeleton first
   - Reference specific ideas/themes from transcripts
   - Get user approval before generating content

5. **Generate content**:
   - Write from the outline
   - Apply voice and style settings
   - Draw on transcript material—use the human's own words when powerful
   - Keep outline and content as separate sections

6. **Write the file** to `ideas/NNNN-name/views/[type]-[title].md`

## File Structure

The file begins with YAML frontmatter:

```yaml
---
title: [Title of the piece]
subtitle: [A single line that expands on the title; optional but recommended]
brief: [1-5 sentences capturing the core thesis or purpose; shorter for short content, longer for long content]
type: [blog-post | technical-overview | video-script | essay | ...]
status: [outline | draft | review | final]
audience: [who this is for]
voice: [description of tone, personality, perspective]
style:
  [attribute]: [0-100]
  [attribute]: [0-100]
---
```

Followed by:

```markdown
## Outline
- [Section]
  - [Key point]
- [Section]
  - [Key point]

## Content

### [Section]
[Prose...]

### [Section]
[Prose...]
```

## Updating Views

Views can be edited at either layer:

**Outline changed → Update content**:
- Reprocess content to match new structure
- Preserve prose that still fits

**Content changed → Update outline**:
- Regenerate outline to reflect new structure

Always make minimal changes—preserve what works.

## Naming Convention

- File: `[type]-[short-title].md` (e.g., `blog-post-memory-palace.md`)
- Lowercase, hyphens for spaces

## For Poetry

If the user wants to generate a poem, suggest using `/generate-poem-view` instead. That command has specialized methodology for poetry (Poetic Inquiry, Objective Correlative, lineation rules, forbidden word lists) that produces much better verse than generic view generation.
