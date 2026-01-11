# Claude Writer

Talk through your ideas; Claude interviews you and produces written content.

## Overview

Claude Writer combines:
1. **Claude Code** (desktop app) for AI-powered ideation and content creation
2. **Web GUI** (Flask app) for browsing and viewing your ideas and generated content

The workflow is: use Claude Code to explore ideas with `/ideate`, generate transcripts and views, then browse everything through the web interface.

## Project Structure

```
claude_writer/
├── app.py               # Flask web application
├── templates/           # HTML templates for web GUI
├── static/              # CSS styles
├── ideas/               # Your idea spaces (transcripts, views, assets)
├── templates/           # Voice and format references (for Claude Code)
├── scripts/             # Python utilities (gemini.py)
├── docs/                # Documentation
├── CLAUDE.md            # Claude Code instructions
└── README.md            # User documentation
```

## Technical Setup

- **Language**: Python 3.11
- **Web Framework**: Flask
- **Dependencies**: Flask, Markdown, Pygments, google-genai, python-dotenv, Pillow
- **API Integration**: Google Gemini (optional, for image/text generation)
- **Port**: 5000

## Key Files

- `app.py` - Flask web application for browsing ideas
- `scripts/gemini.py` - Gemini API utility for image and text generation
- `CLAUDE.md` - Instructions for Claude Code commands
- `requirements.txt` - Python dependencies

## Running the Project

The Flask web app runs on port 5000 and provides:
- Homepage listing all idea spaces
- Idea detail pages with README, transcripts, views, and assets
- Setup guide for configuring Claude Code and Gemini API

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

## Recent Changes

- 2026-01-11: Added Flask web GUI for browsing ideas, setup page with configuration guides
- 2026-01-11: Initial import to Replit, Python 3.11 environment configured
