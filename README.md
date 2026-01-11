# Idea Writer

Talk through your ideas; Claude interviews you and produces written content.

## Two Ways to Use Idea Writer

Choose the approach that fits how you prefer to work.

### Option A: Claude Projects (Browser)

Use Idea Writer in your web browser at claude.ai. Ideas persist through the Project's Knowledge Base.

**How it works:**
1. Create a Claude Project
2. Add Custom Instructions from `skill/CUSTOM_INSTRUCTIONS.md`
3. Ideate through conversation
4. Claude creates artifacts (transcripts, views)
5. Download artifacts and upload to Knowledge Base for future sessions

**Best for:** Browser-based workflow, no local setup required.

**Requires:** Claude Pro or Max subscription

**Setup guide:** [skill/SETUP.md](skill/SETUP.md)

---

### Option B: Claude Code (Terminal)

Use Idea Writer with the Claude Code desktop app. Ideas persist in local folders managed by git.

**How it works:**
1. Open this project in Claude Code
2. Run `/ideate` to explore ideas
3. Claude saves transcripts directly to `ideas/` folder
4. Run `/generate-view` to create content
5. Everything is versioned with git

**Best for:** Terminal workflow, local file management, git version control.

**Requires:** Claude Code desktop app (free with Claude subscription)

**Setup guide:** See "Claude Code Setup" section below

---

## Claude Projects Setup

### Step 1: Create Project

1. Go to [claude.ai](https://claude.ai)
2. Click **Projects** in the sidebar
3. Click **New Project**
4. Name it "Idea Writer" (or your preference)

### Step 2: Add Custom Instructions

1. Click **Edit project details** (pencil icon)
2. Open `skill/CUSTOM_INSTRUCTIONS.md` from this repo
3. Copy everything below the `---` line
4. Paste into the Custom Instructions field
5. Save

### Step 3: Add Voice Templates (Optional)

Upload files from `skill/templates/voices/` to your Project's Knowledge Base:
- `professional-communication.md`
- `conversational-expert.md`
- `exploratory-thinker.md`

### Step 4: Start Ideating

Start a new chat in your project and say:

> "Let's ideate on [your topic]"

When finished, say:

> "Capture this as a transcript"

Download the artifact and upload to your Knowledge Base for future reference.

---

## Claude Code Setup

### Step 1: Install Claude Code

Download from [claude.ai/download](https://claude.ai/download)

### Step 2: Open This Project

Launch Claude Code and open the `idea-writer` folder.

### Step 3: Run Setup (First Time)

```
./scripts/init.sh
```

### Step 4: Start Ideating

Type `/ideate` and describe what you want to explore.

---

## Commands Reference

### Claude Projects (Natural Language)

| Say This | Claude Will |
|----------|-------------|
| "Let's ideate on X" | Start an ideation interview |
| "Continue working on X" | Resume an existing idea |
| "Capture this as a transcript" | Create a transcript artifact |
| "Generate a blog post about X" | Create content from your transcripts |
| "Use the conversational voice" | Apply a voice template |

### Claude Code (Slash Commands)

| Command | What It Does |
|---------|--------------|
| `/ideate` | Explore an idea through conversation |
| `/generate-transcript` | Save the current conversation |
| `/generate-view` | Create content from an idea space |
| `/generate-poem-view` | Generate poetry |
| `/generate-academic-infographic-view` | Create infographic specs |

---

## Web GUI (Optional)

Browse your ideas through a web interface. Works with either workflow.

```bash
python app.py
```

The web GUI reads from the `ideas/` folder. Organize your downloaded artifacts (Claude Projects) or let Claude Code save directly there.

---

## Project Structure

```
idea-writer/
├── skill/
│   ├── CUSTOM_INSTRUCTIONS.md  # For Claude Projects
│   ├── SETUP.md                # Claude Projects setup guide
│   └── templates/
│       ├── voices/             # Writing style templates
│       └── specialized/        # Poetry, infographics
├── .claude/
│   ├── commands/               # For Claude Code
│   ├── agents/
│   └── skills/
├── ideas/                      # Your idea spaces
├── app.py                      # Web GUI
├── templates/                  # HTML templates
└── static/                     # CSS styles
```

---

## Voice Templates

Three voices are included:

| Voice | Best For |
|-------|----------|
| Professional Communication | Business writing, reports |
| Conversational Expert | Blog posts, tutorials |
| Exploratory Thinker | Essays, thought pieces |

**Claude Projects:** Upload to Knowledge Base, then say "Use the [name] voice"

**Claude Code:** Templates are available automatically via `/generate-view`

---

## Specialized Frameworks

For specific content types:

- **Poetry Framework** - Poetic Inquiry methodology
- **Infographic Framework** - Visual content specifications

Find these in `skill/templates/specialized/`.

---

## Organizing Your Ideas

Both workflows use the same folder structure:

```
ideas/
├── 0001-my-first-idea/
│   ├── README.md
│   ├── transcripts/
│   │   └── transcript-2026-01-11.md
│   └── views/
│       └── view-blog-post.md
└── 0002-another-idea/
    └── ...
```

---

## Tips

**Build context over time**: Multiple ideation sessions on one topic create richer content.

**One project per major topic**: Keep unrelated ideas separate.

**Revisit and refine**: Ideas improve with multiple passes.

**Download and organize**: (Claude Projects) Artifacts don't auto-persist; download what you want to keep.

---

## Requirements

| Workflow | Requirements |
|----------|--------------|
| Claude Projects | Claude Pro or Max subscription |
| Claude Code | Claude Code app (free with subscription) |
| Web GUI | Python 3.11 |
