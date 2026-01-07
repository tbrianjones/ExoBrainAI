# Claude Writer

An AI-native writing system where ideas evolve through conversation and content is managed at every layer of the writing stack.

## The Gold Standard: Talk, Don't Type

The primary focus of this library is that **you should not be doing anything yourself**. You ideate; the system produces.

More specifically: you should be *talking* to your computer. This works fine if you type at the command line, but I strongly encourage using a voice interface like [Wispr Flow](https://wispr.flow). Speaking is more fluid; you get your ideas out better; you share more. In my own use, I've found I produce up to 10x more content when speaking versus typing.

The interview-driven approach is built for this. You talk through your ideas. Claude asks questions. The system captures, structures, and refines. Your job is to think out loud.

## Quick Start

1. Clone this repo locally
2. Open Claude Code in the repo directory
3. Say: "I want to generate a new idea"

Claude will run `/generate-idea` and interview you about your concept. The conversation draws out your thinking; you don't need to come with a fully formed pitch. Just bring a spark.

After the interview, Claude creates the idea folder structure and automatically spins up agents to:
- Capture the conversation as a transcript (this happens automatically; transcripts are persistent idea memory)
- Optionally create views (blog post, brief, video script, etc.) if you're ready for production content

## Command and Agents

| Name | Type | What It Does |
|------|------|--------------|
| `/generate-idea` | Command | Interviews you about a concept, creates the idea folder structure, spins up transcript-generator, optionally spins up view-generator |
| `transcript-generator` | Agent | Captures ideation conversations as transcripts; has access to conversation context; preserves ideas, reasoning, emotional threads |
| `view-generator` | Agent | Creates production content; loads full idea folder (README, transcripts, assets) before generating; walks through voice and style |

**Why agents instead of commands for transcript and view?**

Agents run in their own context. This means:
- A long ideation conversation won't overflow context when capturing the transcript
- View generation can happen in a fresh thread and still have full idea context (the agent loads it from files)
- You can say "spin up view-generator for the consciousness idea" in any thread and it works

## How It Works

**The filesystem is the database.** All content lives in markdown files tracked by git. Edits are commits. History is preserved.

**Writing is layered.** Content exists as a stack: topic → outline → sections → paragraphs → sentences. You can edit at any layer. Change the outline and regenerate prose. Change a sentence and leave everything else alone.

**Ideas are interview-driven.** You don't write; you talk. Claude asks questions and draws out your thinking. The raw conversation becomes a transcript; the refined output becomes views.

**Views are structured content.** Each view has metadata (type, audience, voice, style scores) plus an outline and content. The outline and content stay linked; change one and regenerate the other.

## File Structure

```
claude_writer/
├── .claude/
│   ├── agents/              # Agent definitions
│   │   ├── transcript-generator.md
│   │   └── view-generator.md
│   └── commands/            # Command definitions
│       └── generate-idea.md
├── ideas/                   # Idea spaces
│   └── NNNN-name/           # Numbered, kebab-case
│       ├── README.md        # Summary, origin, open questions
│       ├── assets/          # Characters, settings, concepts, objects
│       ├── transcripts/     # Raw ideation captures
│       └── views/           # Production content
├── templates/
│   └── styles/              # Writing style references
├── doc_load/                # Source material, writing samples
├── CLAUDE.md                # Agent context and guidelines
└── README.md                # This file
```

### ideas/

Each idea gets a numbered folder (`0000-name`, `0001-name`, etc.). Inside:

- **README.md** summarizes the idea, its origin, and open questions
- **assets/** holds structured entities: characters, settings, concepts, objects that persist across the idea space
- **transcripts/** stores raw ideation captures from conversations
- **views/** contains production content; each view is a markdown file with metadata, outline, and prose

### templates/styles/

Writing style references. Drop examples of writing styles here for Claude to learn from and apply.

### doc_load/

Source material and writing samples for voice/style learning. Reference documents that inform content production.

## Why It's Built This Way

**Writing is thinking made visible.** The best writing captures how ideas evolved, not just their final form. This system preserves the ideation process alongside the output.

**Layers enable iteration.** When you can edit at any level; topic, outline, paragraph, sentence; you can refine without rewriting. Change your thesis and regenerate the supporting structure. Move a section and let the prose follow.

**Conversation beats blank pages.** Most people think better in dialogue. The interview-driven approach draws out ideas you didn't know you had.

**Git tracks creative work.** Version control isn't just for code. Seeing how a piece evolved; what got cut, what got refined; is part of the creative record.

## Future

- A document editor interface where agents can comment, suggest, and edit
- Multiple agents with different voices (journalist, specific writer styles, your personal voice)
- Style learning from samples in `doc_load/` and `templates/styles/`
- Propagation: edit an outline and auto-regenerate affected prose
