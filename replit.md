# Idea Writer

Talk through your ideas; Claude interviews you and produces written content.

## Overview

Idea Writer uses Claude Projects on claude.ai for ideation and content generation. Transcripts and views are created as artifacts, downloaded, and uploaded to the Project's Knowledge Base for persistence across conversations.

## Architecture

1. **Claude Project** - Persistent workspace on claude.ai with Custom Instructions and Knowledge Base
2. **Artifacts** - Transcripts and views generated during conversations
3. **Web GUI** - Optional Flask app for browsing downloaded ideas locally

## Project Structure

```
idea-writer/
├── app.py                      # Flask web application
├── templates/                  # HTML templates for web GUI
├── static/                     # CSS styles
├── ideas/                      # Downloaded idea spaces
├── skill/
│   ├── CUSTOM_INSTRUCTIONS.md  # Paste into Claude Project settings
│   ├── SETUP.md                # Step-by-step setup guide
│   └── templates/
│       ├── voices/             # Writing style templates
│       └── specialized/        # Poetry, infographics frameworks
├── scripts/                    # Python utilities
└── docs/                       # Additional documentation
```

## Technical Setup

- **Language**: Python 3.11
- **Web Framework**: Flask
- **Dependencies**: Flask, Markdown, Pygments, python-dotenv, Pillow
- **Port**: 5000

## Running the Project

**Web GUI (optional):**
```bash
python app.py
```

**Production:**
```bash
gunicorn --bind=0.0.0.0:5000 --reuse-port app:app
```

## Environment Variables

- `GEMINI_API_KEY` - Optional, for Gemini text/image generation features

## Key Files

- `skill/CUSTOM_INSTRUCTIONS.md` - The main instructions to paste into a Claude Project
- `skill/SETUP.md` - User-facing setup documentation
- `app.py` - Flask web application for browsing ideas

## Workflow

1. User creates a Claude Project and pastes Custom Instructions
2. User uploads voice templates to Knowledge Base
3. User ideates through conversation; Claude creates transcript artifacts
4. User downloads artifacts and uploads to Knowledge Base for persistence
5. User generates views (blog posts, essays, etc.) from accumulated context
6. Optionally, user organizes downloads in ideas/ folder for web GUI browsing

## Recent Changes

- 2026-01-11: Reworked to use Claude Projects + Artifacts instead of GitHub integration
- 2026-01-11: Created CUSTOM_INSTRUCTIONS.md for easy project setup
- 2026-01-11: Simplified SETUP.md with step-by-step guide
- 2026-01-11: Updated README with new workflow
