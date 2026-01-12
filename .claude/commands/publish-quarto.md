---
name: publish-quarto
description: Publish a view to ideas.tbrianjones.com. Converts to Quarto, saves to site/posts/, marks source as published, commits, pushes.
allowed-tools: Read, Write, Glob, Bash, Edit
---

# Publish Quarto

Publish a view from an idea space to ideas.tbrianjones.com. Handles the complete workflow: convert view to Quarto format, save to `site/posts/`, mark the source view as published, commit, and push.

## Process

### 1. Select the view to publish

If a path is provided as an argument, use it. Otherwise:

1. Ask: "Which idea space contains the view?"
2. List available `.md` files in that idea's `views/` folder
3. Ask which one to publish

### 2. Preview the conversion

Read the view file, parse frontmatter and content, then show a preview:

```
## Preview of Quarto Post

**Title:** [title from frontmatter]
**Description:** [subtitle or brief from frontmatter]
**Author:** T. Brian Jones
**Date:** [today's date]
**Categories:** [3-5 categories derived from tags]

---

**Content:**

[Show the Content section that will be published]
```

Ask: "Is there anything you'd like to add or change before publishing?"

Wait for response. If changes requested, incorporate them and show updated preview.

### 3. Determine the slug

- Default: derive from filename (e.g., `brief-machias-token-summary.md` → `machias-token-summary`)
- Ask: "Use slug '[default]' or enter a different one?"
- Final folder will be: `site/posts/YYYY-MM-DD-[slug]/`

### 4. Convert and save to site/posts/

Transform the view to Quarto format and save directly to the site.

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

**Save location:**
- `site/posts/YYYY-MM-DD-[slug]/index.qmd`

**Copy associated data files** from the view's directory:
- `*.csv`, `*.json`, `*.parquet`, `*.xlsx`
- `images/`, `data/`
- `*.js`, `*.png`, `*.jpg`, `*.gif`, `*.svg`

### 5. Mark source view as published

Add `published: true` to the source view's YAML frontmatter:

```yaml
---
title: "Original Title"
published: true
# ... rest of frontmatter
---
```

Use the Edit tool to add this field if not present, or update it if already present.

### 6. Commit and push

```bash
git add site/posts/YYYY-MM-DD-[slug]/
git add [source-view-path]
git commit -m "Publish: [title]"
git push origin main
```

### 7. Report success

Tell the user:
- "Published successfully!"
- "Source view marked as published: [path]"
- "GitHub Actions will deploy in 1-2 minutes"
- "URL: https://ideas.tbrianjones.com/posts/YYYY-MM-DD-[slug]/"

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

## Handling Updates

If the post directory already exists in site/posts/:
1. Ask: "This post already exists. Overwrite?"
2. If yes, replace `index.qmd` and any updated data files
3. Use commit message: "Update: [title]"

## Error Handling

### Git push failure
```
Error: Could not push to GitHub. Please check:
- You have push access to the repo
- The remote is configured correctly
- You're not behind the remote (try git pull first)
```

## Arguments

```
/publish-quarto ideas/0003-economics-of-claude-code/views/brief-machias-token-summary.md
```

Or with custom slug:

```
/publish-quarto --slug custom-slug ideas/0003-economics-of-claude-code/views/brief-token-summary.md
```

## Example

**Input:** `ideas/0003-economics-of-claude-code/views/brief-machias-token-summary.md`

**Creates:** `site/posts/2026-01-12-machias-token-summary/index.qmd`

**Updates source:** Adds `published: true` to the view's frontmatter

**URL:** `https://ideas.tbrianjones.com/posts/2026-01-12-machias-token-summary/`
