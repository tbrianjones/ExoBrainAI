# Claude Writer

## Working in This Repo

This is a writing system where the filesystem is the database. Content is versioned via git. Your job is to interview, generate, and refine writing through conversation.

## Command and Agents

| Name | Type | Purpose |
|------|------|---------|
| `/generate-idea` | Command | Start a new idea through guided interview; creates folder structure, spins up agents |
| `transcript-generator` | Agent | Capture ideation conversations as transcripts |
| `view-generator` | Agent | Create production content; loads full idea context before generating |

## Folder Structure

```
├── .claude/
│   ├── agents/           # Agent definitions (transcript-generator, view-generator)
│   └── commands/         # Command definitions (generate-idea)
├── ideas/                # Idea spaces (NNNN-name format)
│   └── NNNN-name/
│       ├── README.md     # Idea summary, origin, open questions
│       ├── assets/       # Characters, settings, concepts, objects
│       ├── transcripts/  # Raw ideation captures
│       └── views/        # Production content
├── templates/styles/     # Writing style references
└── doc_load/             # Source material and writing samples
```

## Working in Idea Spaces

When working in `ideas/NNNN-name/`:
- **Load the full context first**: README, all transcripts, all assets
- Assets inform voice, details, and consistency across all views
- The view-generator agent does this automatically; if working manually, do it yourself

## Content Production Guidelines

**Style rules for all generated prose:**

- **Avoid dashes and double dashes.** Telltale AI pattern. Use semicolons or restructure.
- **Use semicolons** to join related independent clauses or pivot thoughts.
- **Use ellipses (...)** sparingly for trailing off or unfinished thinking.
- Write in the voice and style defined in the view's metadata.
- Preserve the human's phrasing when it captures the idea well.
- Keep prose grounded; avoid flowery or overwrought language.

**View file structure:**

```yaml
---
title: [Title]
type: [blog-post | brief | video-script | essay | infographic | ...]
status: [outline | draft | review | final]
audience: [who this is for]
voice: [description of tone, personality, perspective]
style:
  [attribute]: [0-100]
  [attribute]: [0-100]
---
```

```markdown
## Outline
[Structural skeleton]

## Content
[Prose organized by section]
```

## Transcripts

Transcripts capture the creative essence of conversations. Focus on:
- Concepts and ideas as they emerged
- Reasoning and thought processes
- Emotional threads and key realizations
- The human's voice and phrasing

Ignore: tool calls, file operations, implementation details, debugging.
