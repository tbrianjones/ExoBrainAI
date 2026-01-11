# Claude Writer

Talk through your ideas; Claude interviews you and produces written content.

## Overview

This is a Python-based CLI tool designed to work alongside Claude Code (the Claude desktop app). It provides a content creation workflow where you:
1. Explore ideas through guided conversation using `/ideate`
2. Capture conversations with `/generate-transcript`
3. Create polished content with `/generate-view`

## Project Structure

```
claude_writer/
├── ideas/           # Your idea spaces (transcripts, views, assets)
├── templates/       # Voice and format references
├── scripts/         # Python utilities (gemini.py)
├── docs/            # Documentation
├── CLAUDE.md        # Claude Code instructions
└── README.md        # User documentation
```

## Technical Setup

- **Language**: Python 3.11
- **Dependencies**: google-genai, python-dotenv, Pillow (via requirements.txt)
- **API Integration**: Google Gemini (optional, for image/text generation)

## Key Files

- `scripts/gemini.py` - Gemini API utility for image and text generation
- `CLAUDE.md` - Instructions for Claude Code commands
- `requirements.txt` - Python dependencies

## Running the Project

This is a CLI tool, not a web application. The gemini.py script can be run directly:

```bash
python scripts/gemini.py text "Your prompt here"
python scripts/gemini.py image "Image description" --output output.png
```

## Environment Variables

- `GEMINI_API_KEY` - Required for Gemini API features (optional for basic usage)

## Recent Changes

- 2026-01-11: Initial import to Replit, Python 3.11 environment configured
