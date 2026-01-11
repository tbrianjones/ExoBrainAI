# Plan: Separating User Data from Shareable Codebase

## Current State Analysis

**Repository Structure:**
- The repository contains both code (commands, agents, skills, scripts, templates) and user-generated content (ideas/).
- The `ideas/` folder currently has 4 idea spaces with substantial personal content:
  - `0000-agent-ideation-driven-content-production/` ; meta-documentation about the system
  - `0001-consciousness-in-the-age-of-ai/` ; philosophical discussions with personal views
  - `0002-daily-voice-diary/` ; personal diary content
  - `0003-economics-of-claude-code/` ; personal analysis

**What's Already Tracked in Git:**
- All ideas content is already committed to git (confirmed via `git ls-files`)
- Over 15 commits have touched the ideas/ folder
- Transcripts contain highly personal content (conversations, opinions, personal experiences)

**Current .gitignore:**
- Standard ignores (OS files, editor files, temp files, .env, node_modules, __pycache__)
- Does NOT ignore the ideas/ folder

**Templates Situation:**
- `templates/voices/` contains user-specific voice style references (jones-*)
- These voice templates are currently empty placeholder READMEs
- Other templates (poetry, infographics, quarto, command-generation) are shareable frameworks

## Recommended Approach

**Strategy: Gitignore + Template Folder + Documentation**

The cleanest approach involves three parts:

1. Add `ideas/` to .gitignore with a .gitkeep for structure
2. Create `ideas/.gitkeep` to ensure the folder exists on clone
3. Handle existing committed content (either via git filter-branch or accepting history)
4. Document the separation clearly in README

## Step-by-Step Implementation

### Phase 1: Prepare the Separation (Non-Destructive)

1. Update `.gitignore` to add:
```
# User content ; not shared
ideas/*
!ideas/.gitkeep
!ideas/README.md

# User-specific voice templates
templates/voices/*
!templates/voices/.gitkeep
!templates/voices/README.md
```

2. Create `ideas/.gitkeep` (empty file to preserve folder structure)

3. Create `ideas/README.md` with instructions:
```markdown
# Ideas Folder

This folder contains your personal idea spaces. Each idea space has:
- `README.md` ; Summary, origin, open questions
- `assets/` ; Structured entities (characters, settings, concepts)
- `transcripts/` ; Raw ideation captures
- `views/` ; Production content

## Getting Started

Run `/ideate` to create your first idea space.

## Note

This folder's contents are gitignored. Your ideas stay private and won't be pushed to the shared repository.
```

4. Create `templates/voices/.gitkeep` and `templates/voices/README.md`:
```markdown
# Voice Templates

Add your personal writing voice/style reference documents here.

Voice templates help the view generators match your unique writing style.
```

### Phase 2: Handle Existing Git History

Two options exist:

**Option A: Clean Break (Recommended for Sharing)**
Use `git filter-repo` to remove ideas content from history:
```bash
pip install git-filter-repo
git filter-repo --path ideas/ --invert-paths
```

This completely removes ideas content from history. Pros: Clean history for friends. Cons: Rewritten history, force push required, user loses ideas in git history.

**Option B: Keep History, Fresh Start for Friends**
Leave history as-is but document that friends should:
1. Clone the repo
2. Delete the existing ideas/ folder contents (not the folder itself)
3. Their ideas will not be tracked

Pros: No history rewrite. Cons: User's old ideas visible in git history.

**Recommended: Option B with a migration script**

Create `scripts/setup-ideas.sh`:
```bash
#!/bin/bash
# Sets up a clean ideas folder for new users

if [ -d "ideas" ]; then
  # Check if there's personal content (more than just .gitkeep)
  count=$(find ideas -type f ! -name ".gitkeep" ! -name "README.md" | wc -l)
  if [ "$count" -gt "0" ]; then
    echo "Found existing ideas content."
    echo "If this is YOUR repository, keep them."
    echo "If you cloned this to use the tooling, delete them with:"
    echo "  rm -rf ideas/0*"
  fi
fi
```

### Phase 3: Update Documentation

1. Update `README.md` to explain the separation:
```markdown
## For Contributors

Your `ideas/` folder is gitignored. When you clone this repo:
1. You get an empty `ideas/` folder ready for your content
2. Your ideas stay local and private
3. PRs should only contain code changes (commands, agents, skills, scripts, templates)
```

2. Update `CLAUDE.md` to note the separation

### Phase 4: Prevent Accidental Commits

Create a pre-commit hook `.git/hooks/pre-commit`:
```bash
#!/bin/bash
# Prevent accidental commits of ideas content

if git diff --cached --name-only | grep -q "^ideas/0"; then
  echo "ERROR: Attempting to commit files in ideas/"
  echo "The ideas/ folder is for personal content and should not be committed."
  echo ""
  echo "If you're the repository owner and want to commit these files,"
  echo "use: git commit --no-verify"
  exit 1
fi
```

This hook warns but allows override for the repo owner.

## Edge Cases

**What if the user already has ideas committed?**
- The existing commits remain in history (unless Option A is used)
- Once .gitignore is updated, new content won't be tracked
- Friends cloning after the change get a clean start

**How do friends get started with a clean ideas folder?**
1. Clone the repo
2. The `ideas/` folder exists (via .gitkeep) but is empty (or has README only)
3. Run `/ideate` to create their first idea space

**How to prevent accidental commits of ideas content?**
1. The .gitignore prevents `git add ideas/` from staging files
2. The pre-commit hook catches any edge cases
3. Documentation reminds contributors

**What about templates/voices?**
- Voice templates are user-specific (the "jones-*" prefixes are clearly personal)
- Gitignore the contents but keep the folder with instructions
- Users create their own voice references

## Trade-offs

| Consideration | Decision | Rationale |
|---------------|----------|-----------|
| History rewrite? | No (Option B) | Less disruptive; user keeps their git history |
| Gitignore entire ideas/? | No, use `ideas/*` with exceptions | Preserves folder structure and instructions |
| Pre-commit hook? | Yes, but advisory | Catches mistakes without blocking repo owner |
| Voice templates? | Gitignore contents | Clearly user-specific ("jones-*" naming) |

## Implementation Order

1. Create branch `feature/ideas-separation`
2. Add .gitkeep files to ideas/ and templates/voices/
3. Create READMEs for both folders
4. Update .gitignore
5. Update README.md with contributor instructions
6. Create pre-commit hook template (in scripts/)
7. Update init.sh to install the hook
8. Test by cloning to a temp directory
9. Merge to main

## Critical Files for Implementation

- `.gitignore` ; Add ideas/* and templates/voices/* patterns
- `README.md` ; Add contributor instructions about ideas separation
- `scripts/init.sh` ; Add pre-commit hook installation
- `ideas/README.md` (new) ; Instructions for the ideas folder
- `CLAUDE.md` ; Update folder structure documentation
