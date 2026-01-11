---
name: publish-quarto
description: Publish a Quarto document to ideas.tbrianjones.com. Copies to writing-site, renders, commits, and pushes.
allowed-tools: Read, Write, Glob, Bash
---

# Publish Quarto

Publish a Quarto document from an idea space to the writing site. Handles the full workflow: copy, render, commit, push.

## Prerequisites

- The writing-site repo must exist at `~/projects/writing-site`
- The writing-site repo must be connected to GitHub
- (Optional) Quarto installed locally for preview (`brew install quarto`)

## Process

### 1. Identify the document to publish

If arguments provided, use them. Otherwise:

1. Ask: "Which idea space contains the document?"
2. List available `.qmd` files in that idea's `views/` folder
3. Ask which one to publish

### 2. Determine the post slug

- Default: derive from filename (e.g., `quarto-memory-palace.qmd` → `memory-palace`)
- Ask if user wants a different slug
- Final folder will be: `posts/YYYY-MM-DD-[slug]/`

### 3. Copy files to writing-site

```bash
# Create the post directory
mkdir -p ~/projects/writing-site/posts/YYYY-MM-DD-[slug]

# Copy the .qmd file as index.qmd
cp [source-path]/quarto-[title].qmd ~/projects/writing-site/posts/YYYY-MM-DD-[slug]/index.qmd

# Copy any associated data files (same directory as .qmd)
# Look for: .csv, .json, .parquet, images/, data/
```

### 4. (Optional) Preview locally

If Quarto is installed, you can preview before pushing:
```bash
cd ~/projects/writing-site
quarto preview
```
Opens at localhost:4321 with live reload.

### 5. Commit and push

```bash
cd ~/projects/writing-site
git add posts/YYYY-MM-DD-[slug]/
git commit -m "Add post: [title]"
git push origin main
```

### 6. Report success

Tell the user:
- "Post published successfully"
- "GitHub Actions will deploy it shortly (1-2 minutes)"
- "URL will be: https://ideas.tbrianjones.com/posts/YYYY-MM-DD-[slug]/"

## Handling Data Files

When copying, check for associated files in the same directory as the `.qmd`:

```bash
# Files to look for and copy:
*.csv
*.json
*.parquet
*.xlsx
images/
data/
*.js (for embedded apps)
*.png, *.jpg, *.gif, *.svg
```

Copy all of these to the post directory.

## Handling Updates

If the post directory already exists:
1. Ask: "This post already exists. Overwrite?"
2. If yes, replace `index.qmd` and any updated data files
3. Use a commit message like "Update post: [title]"

## Error Handling

### Quarto not installed
```
Error: Quarto is not installed. Run `brew install quarto` to install it.
```

### Writing-site repo not found
```
Error: writing-site repo not found at ~/projects/writing-site
Please clone or create it first.
```

### Render failure
```
Error: Quarto render failed. Please fix the following errors before publishing:
[error output]
```

### Git push failure
```
Error: Could not push to GitHub. Please check:
- You have push access to the repo
- The remote is configured correctly
- You're not behind the remote (try git pull first)
```

## Arguments

The command can accept arguments:

```
/publish-quarto ideas/0001-example/views/quarto-my-post.qmd
```

Or:

```
/publish-quarto --slug custom-slug ideas/0001-example/views/quarto-my-post.qmd
```

## Quick Reference

Full workflow in one go:

```bash
# 1. Create post directory
mkdir -p ~/projects/writing-site/posts/2026-01-10-my-post

# 2. Copy files
cp ideas/0001-example/views/quarto-my-post.qmd ~/projects/writing-site/posts/2026-01-10-my-post/index.qmd

# 3. Render to verify
cd ~/projects/writing-site && quarto render posts/2026-01-10-my-post/index.qmd

# 4. Commit and push
git add posts/2026-01-10-my-post/ && git commit -m "Add post: My Post" && git push origin main
```

## After Publishing

The GitHub Actions workflow will:
1. Check out the repo
2. Install Quarto
3. Run `quarto render` on the entire site
4. Deploy to GitHub Pages

This typically takes 1-2 minutes. The user can check progress in the Actions tab on GitHub.
