# Idea Writer

Talk through your ideas; Claude interviews you and produces written content.

## How It Works

Idea Writer runs inside a Claude Project on claude.ai. Your ideas persist across conversations through uploaded transcripts and the Knowledge Base.

**The workflow:**
1. **Ideate** - Claude interviews you to explore an idea
2. **Capture** - Claude creates a transcript artifact
3. **Save** - Download the artifact and upload to your Project's Knowledge Base
4. **Generate** - Claude reads your transcripts and creates polished content

## Quick Start

### 1. Create a Claude Project

1. Go to [claude.ai](https://claude.ai)
2. Click **Projects** → **New Project**
3. Name it "Idea Writer" (or whatever you prefer)

### 2. Add Custom Instructions

1. Click **Edit project details** (pencil icon)
2. Open `skill/CUSTOM_INSTRUCTIONS.md` from this repo
3. Copy the instructions (everything below the `---` line)
4. Paste into the Custom Instructions field
5. Save

### 3. Add Voice Templates (Optional)

Upload files from `skill/templates/voices/` to your Project's Knowledge Base:
- `professional-communication.md`
- `conversational-expert.md`
- `exploratory-thinker.md`

### 4. Start Ideating

In your project, start a new chat and say:

> "Let's ideate on [your topic]"

Claude will interview you. When finished, say:

> "Capture this as a transcript"

Download the artifact and upload it to your Knowledge Base for future reference.

---

## Commands

| Say This | Claude Will |
|----------|-------------|
| "Let's ideate on X" | Start an ideation interview |
| "Continue working on X" | Resume an existing idea |
| "Capture this as a transcript" | Create a transcript artifact |
| "Generate a blog post about X" | Create content from your transcripts |
| "Use the conversational voice" | Apply a voice template |
| "What ideas do I have?" | List ideas in Knowledge Base |

---

## Web GUI (Optional)

Browse your ideas locally with a simple web interface.

**Running:**
```bash
python app.py
```

**Features:**
- Homepage listing all idea spaces
- Detail pages for transcripts and views
- Markdown rendering with syntax highlighting

The web GUI reads from the `ideas/` folder. Organize your downloaded artifacts there if you want to browse them locally.

---

## Project Structure

```
idea-writer/
├── skill/
│   ├── CUSTOM_INSTRUCTIONS.md  # Paste into Claude Project
│   ├── SETUP.md                # Detailed setup guide
│   └── templates/
│       ├── voices/             # Writing style templates
│       └── specialized/        # Poetry, infographics, etc.
├── ideas/                      # Your downloaded idea spaces
├── app.py                      # Flask web GUI
├── templates/                  # HTML templates
└── static/                     # CSS styles
```

---

## Organizing Your Ideas

Recommended folder structure for downloaded artifacts:

```
ideas/
├── 0001-my-first-idea/
│   ├── readme.md
│   ├── transcripts/
│   │   └── transcript-2026-01-11.md
│   └── views/
│       └── view-blog-post.md
└── 0002-another-idea/
    └── ...
```

---

## Voice Templates

Three voices are included:

| Voice | Best For |
|-------|----------|
| Professional Communication | Business writing, reports |
| Conversational Expert | Blog posts, tutorials |
| Exploratory Thinker | Essays, thought pieces |

Upload them to your Knowledge Base, then say "Use the [name] voice" when generating content.

---

## Specialized Frameworks

For specific content types:

- **Poetry Framework** - Poetic Inquiry methodology
- **Infographic Framework** - Visual content specifications

Find these in `skill/templates/specialized/`.

---

## Tips

**Build context over time**: The more transcripts you upload, the richer your generated content becomes.

**One project per major topic**: Keep unrelated ideas in separate projects.

**Download and organize**: Artifacts in chat don't automatically persist. Download what you want to keep.

**Revisit and refine**: Multiple ideation sessions on one topic build depth.

---

## Requirements

- Claude Pro or Max subscription (for Projects)
- Python 3.11 (for optional web GUI)
