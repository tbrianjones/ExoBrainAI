---
name: publish-quarto
description: Publish a view to ideas.tbrianjones.com. Converts to Quarto (.qmd), saves to site/posts/, marks source as published, commits, pushes.
allowed-tools: Read, Write, Glob, Bash, Edit
---

# Publish Quarto

Publish a view from ExoBrain to ideas.tbrianjones.com. Handles the complete workflow: fetch content from ExoBrain, convert to Quarto format, save to `site/posts/`, tag the source as published, commit, and push.

## Process

### 1. Select the view to publish

If an object ID or prefix is provided as an argument, use it. Otherwise:

1. Ask: "Which idea space contains the view?"
   - List spaces: `docker compose exec exobrain exobrain space list --json` (filter for `ideas/`)
2. List view objects in that space:
   ```bash
   docker compose exec exobrain exobrain list --space "ideas/[space-name]" --tag view --json
   ```
3. Ask which one to publish

### 2. Fetch the object content

```bash
docker compose exec exobrain exobrain get <id> --json
```

Parse the JSON response. The `content` field contains the full view content with YAML frontmatter.

### 3. Preview the conversion

Show a preview:

```
## Preview of Quarto Post

**Title:** [title from object]
**Description:** [subtitle or brief from content frontmatter]
**Author:** T. Brian Jones
**Date:** [today's date]
**Categories:** [3-5 categories derived from tags]

---

**Content:**

[Show the Content section that will be published]
```

Ask: "Is there anything you'd like to add or change before publishing?"

Wait for response. If changes requested, incorporate them and show updated preview.

### 4. Determine the slug

- Default: derive from object title (kebab-case, lowercase)
- Ask: "Use slug '[default]' or enter a different one?"
- Final folder will be: `site/posts/YYYY-MM-DD-[slug]/`

### 5. Convert and save to site/posts/

Transform the view to Quarto format and save directly to the site.

**Frontmatter mapping:**
- `title` from object title
- `description` from subtitle or brief in content frontmatter
- Add `author: "T. Brian Jones"`
- Add `date: "YYYY-MM-DD"` (today)
- `tags` from object tags -> `categories` (pick 3-5 most relevant, lowercase, hyphenated)

**Content extraction:**
- Extract only the `## Content` section from the object content
- Drop `## Outline`, `## Tags`, `## Hashtags` sections
- Keep all markdown formatting, tables, code blocks

**Save location:**
- `site/posts/YYYY-MM-DD-[slug]/index.qmd`

### 6. Mark source as published

Tag the ExoBrain object:
```bash
docker compose exec exobrain exobrain tag add <id> "published" --json
```

### 7. Commit and push

```bash
git add site/posts/YYYY-MM-DD-[slug]/
git commit -m "Publish: [title]"
git push origin main
```

### 8. Report success

Tell the user:
- "Published successfully!"
- "Source object tagged as published: [id]"
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
/publish-quarto <object-id-or-prefix>
```

Or without an argument to browse interactively.
