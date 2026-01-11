---
name: generate-quarto-post
description: Convert an existing view to Quarto format for publishing to ideas.tbrianjones.com
allowed-tools: Read, Write, Glob
---

# Generate Quarto Post

Convert an existing view file to Quarto format (`.qmd`) for publishing.

## Process

### 1. Accept path to existing view

If a path is provided as an argument, use it. Otherwise:
1. Ask which idea space contains the view
2. List available `.md` files in that idea's `views/` folder (exclude any `.qmd` files)
3. Ask which one to convert

### 2. Read the view file

Parse the YAML frontmatter and content sections.

### 3. Show preview

Display what the Quarto post will look like:

```
## Preview of Quarto Post

**Title:** [title from frontmatter]
**Description:** [subtitle or brief from frontmatter]
**Author:** T. Brian Jones
**Date:** [today's date]
**Categories:** [3-5 categories derived from tags]

---

**Content:**

[Show the Content section that will be included]
```

### 4. Ask for additions

Ask: "Is there anything you'd like to add or change before I create the post?"

Wait for user response. If they have additions:
- Incorporate them into the content or frontmatter as appropriate
- Show updated preview if significant changes

### 5. Create the Quarto file

Transform to Quarto format:

**Frontmatter mapping:**
- `title` → `title` (keep as-is)
- `subtitle` or `brief` → `description`
- Add `author: "T. Brian Jones"`
- Add `date: "YYYY-MM-DD"` (today)
- `tags` → `categories` (pick 3-5 most relevant, lowercase, hyphenated)

**Content extraction:**
- Extract only the `## Content` section
- Drop `## Outline`, `## Tags`, `## Hashtags` sections
- Keep all markdown formatting, tables, code blocks

**Output file:**
- Same directory as input
- Same base filename with `.qmd` extension
- Example: `brief-machias-token-summary.md` → `brief-machias-token-summary.qmd`

### 6. Report completion

Tell the user:
- "Created: [path to .qmd file]"
- "To publish: run `/publish-quarto [path]`"

## Quarto Output Format

```qmd
---
title: "[title]"
description: "[subtitle or brief]"
author: "T. Brian Jones"
date: "YYYY-MM-DD"
categories: [category1, category2, category3]
---

[Content section from original view]
```

## Example

**Input:** `ideas/0003-economics-of-claude-code/views/brief-machias-token-summary.md`

**Output:** `ideas/0003-economics-of-claude-code/views/brief-machias-token-summary.qmd`

```qmd
---
title: "Hey Machias: Look At These Ridiculous Numbers"
description: "Two months of Claude Code usage and what it would've cost me at API rates"
author: "T. Brian Jones"
date: "2026-01-11"
categories: [claude-code, economics, api-pricing]
---

Machias. I ran out of Claude Code credits and fell down a rabbit hole. Here's the damage.

### What I Actually Used (8 weeks)
...
```

## Notes

- This command does NOT generate new content; it converts existing views
- The view should already have been created by `/generate-view` or another view generator
- After creating the `.qmd`, use `/publish-quarto` to deploy it to ideas.tbrianjones.com
