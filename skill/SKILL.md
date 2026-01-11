---
name: Claude Writer
description: Talk through your ideas; Claude interviews you and produces written content. Works with your GitHub repo to store ideas, transcripts, and views.
version: 1.0.0
author: T. Brian Jones
---

# Claude Writer

A skill for exploring ideas through guided conversation and producing written content.

## What This Skill Does

Claude Writer transforms the way you develop ideas:

1. **Ideation**: Claude interviews you like a podcast producer, drawing out your thinking through thoughtful questions
2. **Transcripts**: Raw captures of your ideation sessions, preserving your voice and ideas
3. **Views**: Production content (blog posts, essays, briefs, poems) generated from your idea spaces

## Getting Started

Say one of these to begin:

- "Let's ideate on [topic]"
- "I want to explore an idea about [topic]"
- "Start a new idea space for [topic]"
- "Continue working on [existing idea name]"

## How It Works

### Step 1: Connect Your GitHub Repo

Before your first session, connect a GitHub repository where your ideas will be stored:

1. Click the "+" button in this chat
2. Select or paste your ideas repository URL
3. Authenticate with GitHub if prompted

Your repo should have this structure (or Claude Writer will help you create it):

```
your-repo/
├── ideas/
│   └── 0000-example-idea/
│       ├── README.md
│       ├── assets/
│       ├── transcripts/
│       └── views/
└── templates/
    └── voices/
```

### Step 2: Ideate

When you start ideating, Claude will:

1. Check if this is a new idea or connects to an existing one
2. If new: create the folder structure in your repo
3. Interview you with one thoughtful question at a time
4. Draw out your thinking without lecturing or imposing ideas

**Interview guidelines Claude follows:**
- One question at a time (never stacked)
- Go deeper before going wider
- Maximum 10 questions per session
- Listen and respond to what you actually said

### Step 3: Generate Transcript

After the conversation, say:

- "Capture this as a transcript"
- "Save this conversation"

Claude will create a structured transcript in `ideas/NNNN-name/transcripts/` with:
- Emotional analysis of the conversation
- Key ideas and themes extracted
- Full conversation preserved

### Step 4: Generate Views

When you're ready to create content, say:

- "Generate a blog post from this idea"
- "Create a technical brief"
- "Write an essay on [topic from idea space]"
- "Turn this into a video script"

Claude will:
1. Load all context from the idea space (README, transcripts, assets)
2. Ask about voice and style preferences
3. Build an outline for your approval
4. Generate the content

## Folder Structure

| Folder | Purpose |
|--------|---------|
| `ideas/NNNN-name/` | Each idea space, numbered sequentially |
| `assets/` | Structured entities: characters, settings, concepts |
| `transcripts/` | Raw ideation captures from conversations |
| `views/` | Production content derived from the idea space |
| `templates/voices/` | Writing voice/style references |

## Style Rules

When generating content, Claude follows these rules:
- **No dashes or double dashes** (telltale AI pattern); use semicolons or restructure
- **Semicolons** join related independent clauses
- **Ellipses** for trailing off (used sparingly)
- Preserve your phrasing when it captures the idea well
- Avoid flowery language

## Sample Questions Claude Might Ask

During ideation, expect questions like:
- "What draws you to this?"
- "Can you give me an example?"
- "What's the hardest part of this?"
- "Who is this for?"
- "What would success look like?"
- "What are you unsure about?"

## Commands Reference

| Say This | Claude Will |
|----------|-------------|
| "Let's ideate on X" | Start a new ideation session |
| "Continue [idea name]" | Resume work on an existing idea |
| "Capture this as a transcript" | Save the conversation |
| "Generate a [type] from [idea]" | Create production content |
| "Show me my ideas" | List all idea spaces |
| "What views exist for [idea]?" | Show existing content |

## Specialized Templates

For specific content types, Claude Writer includes specialized frameworks:

- **Poetry**: Uses Poetic Inquiry methodology with lineation rules and forbidden word lists
- **Infographics**: Structured specifications for visual content

Ask Claude to "generate a poem" or "create an infographic spec" to use these frameworks.

## Tips for Best Results

1. **Think out loud**: The more you share, the richer the transcript
2. **Embrace tangents**: Unexpected connections often yield the best insights
3. **Be specific**: Examples and stories ground abstract ideas
4. **Revisit ideas**: Multiple sessions on one idea build depth
5. **Trust the process**: Let Claude's questions guide you somewhere new
