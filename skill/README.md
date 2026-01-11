# Idea Writer Skill

A Claude Project setup for exploring ideas through guided conversation and producing written content. Works with your Claude Pro/Max subscription.

## Quick Start

1. **Create a Claude Project** on claude.ai
2. **Paste Custom Instructions** from `CUSTOM_INSTRUCTIONS.md`
3. **Upload voice templates** to Knowledge Base (optional)
4. **Start ideating**: "Let's explore an idea about [topic]"

See [SETUP.md](SETUP.md) for detailed instructions.

## What's Included

```
skill/
├── CUSTOM_INSTRUCTIONS.md   # Paste into Claude Project settings
├── SETUP.md                 # Detailed setup guide
├── README.md                # This file
└── templates/
    ├── transcript-template.md
    ├── view-template.md
    ├── idea-readme-template.md
    ├── voices/
    │   ├── professional-communication.md
    │   ├── conversational-expert.md
    │   └── exploratory-thinker.md
    └── specialized/
        ├── poetry-framework.md
        └── infographic-framework.md
```

## How It Works

1. **You talk, Claude interviews** - Share your ideas; Claude asks thoughtful questions
2. **Artifacts capture everything** - Transcripts created as downloadable artifacts
3. **Knowledge Base persists** - Upload artifacts to reference in future conversations
4. **Views become content** - Blog posts, essays, briefs generated from your context

## Key Features

- Works with Claude Pro/Max subscription (no API costs)
- Persistent context through Claude Projects
- Interview-style ideation (podcast producer approach)
- Multiple voice templates for different writing styles
- Artifact-based workflow for transcripts and views

## Setup

1. Create a new Claude Project
2. Copy contents of `CUSTOM_INSTRUCTIONS.md` into the Custom Instructions field
3. Upload voice templates to Knowledge Base (optional)
4. Start a conversation and say "Let's ideate on [topic]"

## Usage Examples

| You Say | Claude Does |
|---------|-------------|
| "Let's ideate on consciousness and AI" | Starts interview, asks questions |
| "Capture this as a transcript" | Creates transcript artifact |
| "Generate a blog post from my ideas" | Reads Knowledge Base, writes content |
| "Use the conversational voice" | Applies voice template to content |

## The Artifact Workflow

1. Claude creates a transcript or view as an artifact
2. Download the artifact (click download icon)
3. Upload to your Project's Knowledge Base
4. Claude references it in future conversations

This gives you persistent context across sessions without needing external integrations.

## License

MIT - Use freely, modify as needed.
