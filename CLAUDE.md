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
| `/generate-transcript` | User wants to capture current conversation |
| `/generate-view` | User wants production content from an idea |
| `/generate-poem-view` | User wants poetry; uses Poetic Inquiry methodology |
| `/generate-academic-infographic-view` | User wants data-focused, academically rigorous infographic specs |

## Agents

| Agent | Invocation |
|-------|------------|
| `transcript-generator` | Called by `/genreate-transcript` or spun up directly in a thread after `/ideate` to capture conversation |

## Folder Structure

```
├── .claude/
│   ├── agents/           # transcript-generator
│   └── commands/         # ideate, instantiate-idea, generate-transcript, generate-view, generate-poem-view, generate-academic-infographic-view
├── ideas/NNNN-name/
│   ├── README.md         # Idea summary, origin, open questions
│   ├── assets/           # Structured entities (characters, settings, concepts)
│   ├── transcripts/      # Raw ideation captures
│   └── views/            # Production content
└── templates/
    ├── styles/           # Writing style references
    └── infographics/     # Framework documentation for visual content
```

## Working in Idea Spaces

Before generating content in `ideas/NNNN-name/`:

1. Read `README.md`
2. Read all files in `transcripts/`
3. Read all files in `assets/`
4. Scan `views/` for existing voice/style patterns

Commands `/generate-view`, `/generate-poem-view`, and `/generate-academic-infographic-view` do this automatically.

## Style Rules

- **No dashes or double dashes.** Use semicolons or restructure.
- **Semicolons** join related independent clauses.
- **Ellipses** for trailing off (use sparingly).
- Preserve human's phrasing when it captures the idea.
- Avoid flowery language.

## Behavior

- Always do work in feature branches. Propose this as soon as you launch.