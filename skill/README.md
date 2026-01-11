# Claude Writer Skill

A Claude Skill for exploring ideas through guided conversation and producing written content. Works with your Claude Max subscription and stores everything in your GitHub repository.

## Quick Start

1. **Enable the skill** in Claude.ai Settings → Skills
2. **Connect your GitHub repo** using the "+" button in chat
3. **Start ideating**: "Let's explore an idea about [topic]"

See [SETUP.md](SETUP.md) for detailed instructions.

## What's Included

```
skill/
├── SKILL.md              # Main skill definition (install this)
├── SETUP.md              # Setup guide
├── README.md             # This file
└── templates/
    ├── transcript-template.md
    ├── view-template.md
    ├── idea-readme-template.md
    └── voices/
        ├── professional-communication.md
        ├── conversational-expert.md
        └── exploratory-thinker.md
```

## How It Works

1. **You talk, Claude interviews** - Share your ideas; Claude asks thoughtful questions
2. **Transcripts capture everything** - Your words and thinking, preserved
3. **Views become content** - Blog posts, essays, briefs from your idea spaces

## Key Features

- Works with Claude Pro/Max subscription (no API costs)
- Native GitHub integration for file storage
- Interview-style ideation (podcast producer approach)
- Multiple voice templates for different writing styles
- Structured idea spaces with transcripts, assets, and views

## Installation

Copy the contents of `SKILL.md` into a new Claude Skill, or ask Claude to create a skill from this file.

## Usage Examples

| You Say | Claude Does |
|---------|-------------|
| "Let's ideate on consciousness and AI" | Starts interview, creates idea space |
| "Save this conversation" | Creates transcript in your repo |
| "Generate a blog post from my consciousness idea" | Loads context, interviews about style, writes content |
| "Show me what views exist" | Lists all content in your idea spaces |

## License

MIT - Use freely, modify as needed.
