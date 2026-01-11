# Claude Writer

Talk through your ideas; Claude interviews you and produces written content.

## Overview

Claude Writer now supports two workflows:

1. **Claude Skill** (for Claude.ai web) - Use Claude with your Max subscription to ideate, with GitHub for storage
2. **Web GUI** (Flask app) - Browse and view your ideas, transcripts, and generated content

The primary workflow is: use the Claude Writer skill in Claude.ai to explore ideas → Claude saves to your GitHub repo → sync to the web GUI to browse.

## Project Structure

```
claude_writer/
├── app.py               # Flask web application
├── templates/           # HTML templates for web GUI
├── static/              # CSS styles
├── ideas/               # Your idea spaces (transcripts, views, assets)
├── skill/               # Claude Skill package for Claude.ai
│   ├── SKILL.md         # Main skill definition
│   ├── SETUP.md         # Setup guide
│   └── templates/       # Skill templates (voices, formats)
├── scripts/             # Python utilities (gemini.py)
├── docs/                # Documentation
├── CLAUDE.md            # Claude Code instructions (legacy)
└── README.md            # User documentation
```

## Technical Setup

- **Language**: Python 3.11
- **Web Framework**: Flask
- **Dependencies**: Flask, Markdown, Pygments, google-genai, python-dotenv, Pillow
- **Port**: 5000

## Key Files

- `app.py` - Flask web application with GitHub sync capability
- `skill/SKILL.md` - Claude Skill definition for Claude.ai
- `skill/SETUP.md` - Setup guide for users
- `scripts/gemini.py` - Gemini API utility for image and text generation
- `CLAUDE.md` - Instructions for Claude Code commands (legacy approach)

## Running the Project

The Flask web app runs on port 5000 and provides:
- Homepage listing all idea spaces
- Idea detail pages with README, transcripts, views, and assets
- GitHub sync button (when GITHUB_REPO_URL is configured)
- Setup guide for configuration

For development:
```bash
python app.py
```

For production (deployment):
```bash
gunicorn --bind=0.0.0.0:5000 --reuse-port app:app
```

## Environment Variables

- `GEMINI_API_KEY` - Optional, for Gemini text/image generation features
- `GITHUB_REPO_URL` - Optional, enables sync from GitHub. For private repos use: `https://<token>@github.com/user/repo.git`

## Workflow Options

### Option 1: Claude Skill (Recommended for Max subscribers)
1. Enable the Claude Writer skill in Claude.ai
2. Connect your GitHub repo in Claude settings
3. Ideate through chat - Claude saves to GitHub
4. Sync to web GUI to browse

### Option 2: Claude Code (Legacy)
1. Use Claude Code desktop app with /ideate command
2. Content saved locally to ideas/ folder
3. Browse through web GUI

## Recent Changes

- 2026-01-11: Added Claude Skill package for Claude.ai with native GitHub integration
- 2026-01-11: Added GitHub sync capability to web GUI
- 2026-01-11: Added voice templates and specialized frameworks (poetry, infographics)
- 2026-01-11: Added Flask web GUI for browsing ideas, setup page with configuration guides
- 2026-01-11: Initial import to Replit, Python 3.11 environment configured
