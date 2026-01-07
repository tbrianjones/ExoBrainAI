# Claude Writer

Filesystem is the database. Git versions content.

## Commands vs Agents

**Commands** interview the user, have dialogue, require input.
**Agents** run autonomously in their own context, no further input needed.

## Commands

| Command | When to Use |
|---------|-------------|
| `/ideate` | User wants to explore an idea (new or existing) |
| `/instantiate-idea` | Create folder structure; usually called by /ideate |
| `/generate-view` | User wants production content from an idea |
| `/generate-poem-view` | User wants poetry; uses Poetic Inquiry methodology |

## Agents

| Agent | Invocation |
|-------|------------|
| `transcript-generator` | Spun up after /ideate to capture conversation |

## Folder Structure

```
├── .claude/
│   ├── agents/           # transcript-generator
│   └── commands/         # ideate, instantiate-idea, generate-view, generate-poem-view
├── ideas/NNNN-name/
│   ├── README.md         # Idea summary, origin, open questions
│   ├── assets/           # Structured entities (characters, settings, concepts)
│   ├── transcripts/      # Raw ideation captures
│   └── views/            # Production content
└── templates/styles/     # Writing style references
```

## Working in Idea Spaces

Before generating content in `ideas/NNNN-name/`:

1. Read `README.md`
2. Read all files in `transcripts/`
3. Read all files in `assets/`
4. Scan `views/` for existing voice/style patterns

Commands `/generate-view` and `/generate-poem-view` do this automatically.

## View File Format

```yaml
---
title: [Title]
type: [blog-post | brief | video-script | essay | poem | ...]
status: [outline | draft | review | final]
audience: [who this is for]
voice: [tone, personality, perspective]
style:
  [attribute]: [0-100]
---
```

```markdown
## Outline
[Structural skeleton]

## Content
[Prose by section]
```

## Transcript File Format

```markdown
# [Topic Title]
- person: [name]
- ai: [model]
- emotional analysis: [tags]

## Ideas & Themes
## Transcript Summary
## Full Transcript
```

## Style Rules

- **No dashes or double dashes.** Use semicolons or restructure.
- **Semicolons** join related independent clauses.
- **Ellipses** for trailing off (use sparingly).
- Preserve human's phrasing when it captures the idea.
- Avoid flowery language.
