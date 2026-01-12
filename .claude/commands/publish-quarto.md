---
name: publish-quarto
description: Publish a view to ideas.tbrianjones.com. Converts to Quarto format, copies to writing-site, commits, and pushes.
allowed-tools: Read, Write, Glob, Bash
---

# Publish Quarto

Publish a view from an idea space to the writing site. Handles the full workflow: convert to Quarto format, save locally, copy to writing-site, commit, and push.

## Prerequisites

- The writing-site repo must exist at `~/projects/writing-site`
- The writing-site repo must be connected to GitHub

## Process

### 1. Select the view to publish

If a path is provided as an argument, use it. Otherwise:

1. Ask: "Which idea space contains the view?"
2. List available `.md` files in that idea's `views/` folder (exclude `.qmd` files)
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
- Final folder will be: `posts/YYYY-MM-DD-[slug]/`

### 4. Convert and save locally

Transform the view to Quarto format.

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

**Save locally:**
- Same directory as input
- Same base filename with `.qmd` extension
- Example: `brief-machias-token-summary.md` → `brief-machias-token-summary.qmd`

### 5. Copy to writing-site

```bash
# Create the post directory
mkdir -p ~/projects/writing-site/posts/YYYY-MM-DD-[slug]

# Copy the .qmd file as index.qmd
cp [source-path]/[filename].qmd ~/projects/writing-site/posts/YYYY-MM-DD-[slug]/index.qmd

# Copy any associated data files from the same directory
# Look for: .csv, .json, .parquet, .xlsx, images/, data/, *.js, *.png, *.jpg, *.gif, *.svg
```

### 6. Commit and push

```bash
cd ~/projects/writing-site
git add posts/YYYY-MM-DD-[slug]/
git commit -m "Add post: [title]"
git push origin main
```

### 7. Report success

Tell the user:
- "Published successfully!"
- "Local copy saved: [path to .qmd in idea space]"
- "GitHub Actions will deploy it shortly (1-2 minutes)"
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

If the post directory already exists in writing-site:
1. Ask: "This post already exists. Overwrite?"
2. If yes, replace `index.qmd` and any updated data files
3. Use commit message: "Update post: [title]"

## Error Handling

### Writing-site repo not found
```
Error: writing-site repo not found at ~/projects/writing-site
Please clone or create it first.
```

### Git push failure
```
Error: Could not push to GitHub. Please check:
- You have push access to the repo
- The remote is configured correctly
- You're not behind the remote (try git pull first)
```

## Arguments

The command accepts a path argument:

```
/publish-quarto ideas/0003-economics-of-claude-code/views/brief-machias-token-summary.md
```

Or with custom slug:

```
/publish-quarto --slug custom-slug ideas/0003-economics-of-claude-code/views/brief-machias-token-summary.md
```

## Example

**Input:** `ideas/0003-economics-of-claude-code/views/brief-machias-token-summary.md`

**Creates locally:** `ideas/0003-economics-of-claude-code/views/brief-machias-token-summary.qmd`

**Publishes to:** `~/projects/writing-site/posts/2026-01-12-machias-token-summary/index.qmd`

**URL:** `https://ideas.tbrianjones.com/posts/2026-01-12-machias-token-summary/`
