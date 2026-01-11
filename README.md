# Claude Writer

Talk through your ideas; Claude interviews you and produces written content.

## Two Ways to Use Claude Writer

### Option 1: Claude Skill (Recommended)

Use Claude Writer directly in Claude.ai with your Pro or Max subscription. No terminal needed.

**Setup:**
1. Go to Claude.ai Settings → Skills
2. Create a new skill named "Claude Writer"
3. Paste the contents of `skill/SKILL.md`
4. In any chat, click "+" to connect your GitHub repository
5. Say "Let's ideate on [topic]" to start

**How it works:**
- Claude interviews you through guided conversation
- Transcripts and content are saved directly to your GitHub repo
- Use the web GUI (see below) to browse your ideas

See `skill/SETUP.md` for detailed instructions.

### Option 2: Claude Code (Desktop App)

Use the Claude Code terminal app for a more hands-on experience.

**Setup:**
1. Download Claude Code from [claude.ai/download](https://claude.ai/download)
2. Open the `claude_writer` folder in Claude Code
3. Run `./scripts/init.sh` to install dependencies
4. Type `/ideate` to start exploring ideas

---

## Web GUI

Browse and view your ideas through a web interface.

**Running locally:**
```bash
python app.py
```

**Features:**
- Homepage listing all idea spaces
- Detail pages for transcripts, views, and assets
- Markdown rendering with syntax highlighting
- GitHub sync (see below)

### GitHub Sync

Sync ideas from your GitHub repository to the web GUI:

1. Set the `GITHUB_REPO_URL` environment variable:
   - For public repos: `https://github.com/username/repo.git`
   - For private repos: `https://<token>@github.com/username/repo.git`

2. Click "Sync from GitHub" on the homepage

3. Your ideas will be pulled from GitHub and displayed in the GUI

**Tip:** Store tokens securely using environment variables or your platform's secrets manager.

---

## Commands (Claude Code)

| Command | What it does |
|---------|--------------|
| `/ideate` | Explore an idea through guided conversation |
| `/generate-transcript` | Save the current conversation |
| `/generate-view` | Create content (blog post, brief, essay, etc.) |
| `/generate-poem-view` | Generate poetry |
| `/generate-academic-infographic-view` | Create infographic specifications |
| `/generate-new-view-command` | Build a new view generator command |
| `/generate-quarto-post` | Convert an existing view to Quarto format |
| `/publish-quarto` | Deploy a Quarto view to ideas.tbrianjones.com |

---

## Project Structure

```
claude_writer/
├── app.py               # Flask web application
├── ideas/               # Your idea spaces
├── skill/               # Claude Skill package
│   ├── SKILL.md         # Main skill definition
│   ├── SETUP.md         # Setup guide
│   └── templates/       # Voice and format templates
├── templates/           # HTML templates for web GUI
├── static/              # CSS styles
├── scripts/             # Setup and utility scripts
└── .claude/
    ├── commands/        # User-invoked commands
    ├── agents/          # Autonomous subagents
    └── skills/          # Utilities (gemini, etc.)
```

---

## Idea Space Structure

Each idea gets its own folder:

```
ideas/0001-my-idea/
├── README.md        # Idea summary and open questions
├── transcripts/     # Raw conversation captures
├── views/           # Generated content (blog posts, essays, etc.)
└── assets/          # Supporting files (images, data, etc.)
```

---

## Voice Templates

Claude Writer includes voice templates for consistent content generation:

| Voice | Best For |
|-------|----------|
| Professional Communication | Business writing, reports |
| Conversational Expert | Blog posts, tutorials |
| Exploratory Thinker | Essays, thought pieces |

Find templates in `skill/templates/voices/`.

---

## Specialized Frameworks

For specific content types:

- **Poetry Framework**: Poetic Inquiry methodology with lineation rules
- **Infographic Framework**: Visual content specifications

Find frameworks in `skill/templates/specialized/`.

---

## Configuration

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Optional. Enables Gemini text/image generation |
| `GITHUB_REPO_URL` | Optional. Enables GitHub sync in web GUI |

### Gemini API (Optional)

For text and image generation features:

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create an API key
3. Set `GEMINI_API_KEY` environment variable

**Free tier**: 1000 text requests/day
**Paid tier**: Image generation (~$0.03 per image)

---

## Principles

**Filesystem is the database.** Ideas live in folders. Git versions everything.

**Interview, don't lecture.** Claude asks questions to draw out your thinking.

**Transcripts are raw material.** Every conversation can become multiple views.

**Infrastructure as code.** Configuration lives in the repo, not in cloud consoles.
