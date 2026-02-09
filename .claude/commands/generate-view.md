---
name: generate-view
description: Create production content (blog post, brief, video script, etc.) within an idea space. Interviews about voice and style, then generates.
allowed-tools: Read, Write, Glob, Bash
---

# View Generator

Create production content within an idea space. If working from an existing idea, load the full context first before interacting with the user.

## CRITICAL: Load Context First

Before any interaction with the user, you MUST load the idea's content from ExoBrain's projected files:

1. **Refresh projection**: `docker compose exec exobrain exobrain project`

2. **Read `.env`** to determine `EXOBRAIN_DATA_DIR`

3. **Read the space's CLAUDE.md index**: `$EXOBRAIN_DATA_DIR/projected/ideas/{space-name}/CLAUDE.md`
   - This provides an overview of all objects in the space

4. **Read ALL projected files** in the space directory: `$EXOBRAIN_DATA_DIR/projected/ideas/{space-name}/*.md`
   - Each file has YAML frontmatter (id, type, space, title, summary, tags, dates) + markdown content
   - Transcripts contain the raw ideation; the source material for views
   - Concept objects (tagged `idea-readme`) contain the idea summary and open questions
   - Existing views show voice and style patterns already established

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
   - Draw on transcript material; use the human's own words when powerful
   - Keep outline and content as separate sections

6. **Save to ExoBrain**:
   Pipe the content via stdin to avoid CLI issues with frontmatter:
   ```bash
   echo "[content]" | docker compose exec -T exobrain exobrain capture \
     --title "[Title]" \
     --type view \
     --space "ideas/[space-name]" \
     --tag view --tag [content-type] --tag draft \
     --always-project \
     --json
   ```
   Then refresh: `docker compose exec exobrain exobrain project`

## File Structure

The content should begin with YAML frontmatter:

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

---

## Tags

[tag1], [tag2], [tag3], [tag4], [tag5], [tag6], [tag7], [tag8], [tag9], [tag10]

## Hashtags

#[hashtag1], #[hashtag2], #[hashtag3], #[hashtag4], #[hashtag5], #[hashtag6], #[hashtag7], #[hashtag8], #[hashtag9], #[hashtag10]
```

### Tags and Hashtags

Generate 10 of each, ordered by importance/relevancy:

**Tags**: Lowercase, spaces allowed. Describe core concepts, themes, and subjects. Mix broad and specific terms.

**Hashtags**: No spaces, social media ready. Include both broad reach terms and niche community tags.

## Updating Views

Views can be edited at either layer:

**Edit the projected file directly**: The file watcher auto-syncs changes back to SQLite. Edit the markdown file at `$EXOBRAIN_DATA_DIR/projected/ideas/{space-name}/{filename}.md`.

**Outline changed -> Update content**: Reprocess content to match new structure. Preserve prose that still fits.

**Content changed -> Update outline**: Regenerate outline to reflect new structure.

Always make minimal changes; preserve what works.

## For Poetry

If the user wants to generate a poem, suggest using `/generate-poem-view` instead. That command has specialized methodology for poetry (Poetic Inquiry, Objective Correlative, lineation rules, forbidden word lists) that produces much better verse than generic view generation.
