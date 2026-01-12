# Claude Writer

Filesystem is the database. Git versions content.

## Commands vs Agents vs Skills

**Commands** interview the user, have dialogue, require input.
**Agents** run autonomously in their own context, no further input needed.
**Skills** are utilities invoked by commands or agents (not directly by users).

## Commands

| Command | When to Use |
|---------|-------------|
| `/ideate` | User wants to explore an idea (new or existing) |
| `/instantiate-idea` | Create folder structure; usually called by /ideate |
| `/generate-transcript` | User wants to capture current conversation |
| `/generate-view` | User wants production content from an idea |
| `/generate-poem-view` | User wants poetry; uses Poetic Inquiry methodology |
| `/generate-academic-infographic-view` | User wants data-focused, academically rigorous infographic specs |
| `/generate-new-view-command` | User wants to create a new specialized view generator |
| `/publish-quarto` | Publish a view to ideas.tbrianjones.com (converts to Quarto, saves to site/posts/, marks source as published) |

## Agents

| Agent | Invocation |
|-------|------------|
| `transcript-generator` | Called by `/generate-transcript` or spun up directly in a thread after `/ideate` to capture conversation |

## Skills

| Skill | Purpose |
|-------|---------|
| `gemini` | Generate images (saved to idea views/) or text (returned to caller) via Google Gemini API |
| `title-generation` | Generate effective titles and headlines for any content type |
| `summary-generation` | Generate summaries, abstracts, briefs, and meta descriptions |
| `tag-generation` | Generate tags, hashtags, and topic classifications for any platform |

## Folder Structure

```
├── .claude/
│   ├── agents/           # transcript-generator
│   ├── commands/         # ideate, instantiate-idea, generate-transcript, generate-view, etc.
│   └── skills/           # gemini, title-generation, summary-generation, tag-generation
├── scripts/              # Python utilities (gemini.py)
├── ideas/NNNN-name/
│   ├── README.md         # Idea summary, origin, open questions
│   ├── assets/           # Structured entities (characters, settings, concepts)
│   ├── transcripts/      # Raw ideation captures
│   └── views/            # Production content
├── site/                 # Quarto site for ideas.tbrianjones.com
│   ├── _quarto.yml       # Site config
│   └── posts/            # Published posts
└── templates/
    ├── voices/             # Writing voice/style references
    ├── poetry/             # Poetry generation frameworks
    ├── infographics/       # Infographic generation frameworks
    ├── title-generation/   # Title and headline generation framework
    ├── summary-generation/ # Summary, abstract, and brief framework
    ├── tag-generation/     # Tags, hashtags, and classification framework
    ├── quarto/             # Quarto post framework and reference
    └── command-generation/ # Meta-command frameworks
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
- **Infrastructure as code.** Never configure infrastructure manually via cloud consoles or CLI calls to services. All configuration should be defined in repository files, version controlled, and deployed via push. If something needs to change in GitHub, cloud services, or any external system, express it in code.