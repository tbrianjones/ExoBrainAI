# Plan: Merging writing-site into claude_writer

## Context

The `writing-site` repository was created as a separate repo to host the Quarto-based static site at ideas.tbrianjones.com. After implementation, it became clear that this repo is extremely simple (~150 lines of config) and the separation creates overhead without clear benefit.

**Current State:**
- `~/projects/claude_writer/` ; Main project with commands, ideas, and all tooling
- `~/projects/writing-site/` ; Quarto site config, GitHub Actions workflow, and posts
- Two commands bridge them: `/generate-quarto-post` (converts views) and `/publish-quarto` (copies and pushes)

**The Question:** Should writing-site remain separate, or be merged into claude_writer?

## Analysis

### Arguments for Merging

1. **Single Source of Truth**
   - All project code lives in one place
   - No context-switching between repos
   - Git history tells one complete story

2. **Simpler `/publish-quarto` Workflow**
   - Currently: copy file to different repo, cd there, commit, push
   - After merge: just commit and push from same repo
   - Eliminates cross-repo file operations

3. **Aligns with Infrastructure-as-Code Principle**
   - The site config is infrastructure for publishing ideas
   - Ideas live in claude_writer; their publishing infrastructure should too
   - Everything in one version-controlled place

4. **Reduced Maintenance**
   - One repo to clone, one to keep updated
   - No risk of repos drifting out of sync
   - Simpler onboarding for anyone using the system

5. **writing-site is Trivially Small**
   - ~150 lines of meaningful config
   - Just a Quarto project definition
   - Doesn't justify its own repo

### Arguments Against Merging

1. **GitHub Pages Deployment Complexity**
   - GitHub Pages deploys from a repo's root or `docs/` folder
   - Deploying from a subdirectory requires workflow changes
   - More complex Actions workflow needed

2. **Separation of Concerns**
   - claude_writer = content creation tooling
   - writing-site = publishing destination
   - Conceptually distinct purposes

3. **Deploy Independence**
   - Currently, pushing to writing-site only deploys the site
   - After merge, any push to main could trigger site rebuild
   - Need careful workflow conditions

4. **Repo Size Over Time**
   - Posts accumulate with data files, images, assets
   - claude_writer repo grows with published content
   - Could slow down cloning (minor concern; posts are small)

## Recommendation

**Merge the repos.**

The benefits (simplicity, single source of truth, reduced maintenance) outweigh the costs (workflow complexity). The separation of concerns argument is weak; the site exists to publish ideas from this system. They're one system.

## Technical Approach

### Directory Structure After Merge

```
claude_writer/
├── .claude/
│   ├── commands/
│   ├── agents/
│   └── skills/
├── ideas/
├── templates/
├── scripts/
├── site/                    # <-- writing-site content moves here
│   ├── _quarto.yml
│   ├── index.qmd
│   ├── about.qmd
│   ├── styles.css
│   ├── CNAME
│   └── posts/
│       └── YYYY-MM-DD-slug/
│           └── index.qmd
└── .github/
    └── workflows/
        └── publish-site.yml  # Updated workflow
```

### Updated GitHub Actions Workflow

```yaml
name: Publish Site to GitHub Pages

on:
  push:
    branches: [main]
    paths:
      - 'site/**'           # Only trigger on site changes
  workflow_dispatch:         # Manual trigger

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Quarto
        uses: quarto-dev/quarto-actions/setup@v2

      - name: Render
        run: |
          cd site
          quarto render

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: site/_site

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

Key changes:
- `paths: ['site/**']` ensures only site changes trigger builds
- `cd site` before render
- Upload from `site/_site`

### Updated `/publish-quarto` Command

Simplified workflow:
1. Copy `.qmd` from `ideas/NNNN-name/views/` to `site/posts/YYYY-MM-DD-slug/`
2. `git add site/posts/...`
3. `git commit -m "Add post: [title]"`
4. `git push`

No cross-repo operations. Just standard git within the same repo.

### GitHub Pages Configuration

Two options:

**Option A: Deploy from claude_writer repo**
- Enable GitHub Pages on claude_writer
- Configure custom domain (ideas.tbrianjones.com)
- Archive or delete writing-site repo

**Option B: Keep writing-site as deploy target**
- claude_writer workflow pushes built `_site` to writing-site
- writing-site serves static files only (no Quarto)
- More complex but separates source from deploy

**Recommended: Option A** ; simpler, aligns with goals.

## Migration Steps

### Phase 1: Prepare claude_writer

1. Create `site/` directory
2. Copy all files from writing-site:
   - `_quarto.yml`
   - `index.qmd`, `about.qmd`, `styles.css`
   - `CNAME`
   - `posts/` (all content)
3. Update `_quarto.yml` if any paths need adjusting
4. Create new `.github/workflows/publish-site.yml`

### Phase 2: Update Commands

1. Update `/publish-quarto` command:
   - Change destination from `~/projects/writing-site/posts/` to `site/posts/`
   - Remove cross-repo operations
   - Simplify commit/push logic

2. Update any documentation referencing writing-site path

### Phase 3: Configure GitHub Pages

1. Enable GitHub Pages on claude_writer repo
2. Set custom domain to ideas.tbrianjones.com
3. Verify CNAME file is in `site/` and gets deployed

### Phase 4: Test and Validate

1. Push to main
2. Verify GitHub Actions workflow runs
3. Verify site deploys to ideas.tbrianjones.com
4. Test `/publish-quarto` with a new post

### Phase 5: Clean Up

1. Archive writing-site repo (or delete if confident)
2. Update any bookmarks or documentation
3. Remove writing-site from local projects if desired

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| GitHub Pages doesn't work from subdirectory | Workflow uploads `site/_site`; Pages serves from artifact |
| DNS issues during migration | Test with GitHub-provided URL first |
| Workflow triggers too often | `paths` filter limits to site changes |
| Loss of writing-site history | It's minimal; can keep repo archived |

## Decision

Proceed with merge? This plan can be implemented in one session.

**To implement:** Create feature branch, execute phases 1-4, merge to main, then phase 5.
