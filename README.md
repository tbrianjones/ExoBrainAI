# Claude Writer

Interview-driven writing system. You talk; Claude interviews; the system captures and produces.

## Quick Start

1. Clone repo, open Claude Code in the directory
2. Run `/ideate` (or say "I want to ideate on something")
3. Talk through your idea; Claude handles the rest

Voice interface recommended: [Wispr Flow](https://wisprflow.ai/) or similar.

## Commands

| Command | Purpose |
|---------|---------|
| `/ideate` | Start or continue exploring an idea through guided interview |
| `/generate-transcript` | Capture current conversation as a transcript |
| `/generate-view` | Create production content (blog post, brief, essay, etc.) |
| `/generate-poem-view` | Generate poetry using Poetic Inquiry methodology |
| `/generate-academic-infographic-view` | Create academically rigorous infographic specifications |

## File Structure

```
claude_writer/
├── .claude/
│   ├── commands/       # Command definitions
│   └── agents/         # Agent definitions
├── ideas/              # Idea spaces (NNNN-name format)
│   └── NNNN-name/
│       ├── README.md   # Summary, origin, open questions
│       ├── assets/     # Characters, settings, concepts
│       ├── transcripts/# Raw ideation captures
│       └── views/      # Production content
└── templates/
    ├── styles/         # Writing style references
    └── infographics/   # Framework documentation
```

## Future

- Document editor interface with agent comments
- Style learning from samples
- Outline-to-prose propagation
