---
name: gemini
description: Generate images or text using Google Gemini API
allowed-tools: Bash
---

# Gemini

Generate images or text via Google Gemini.

**Free tier**: Text generation works without billing.
**Paid tier**: Image generation requires billing (~$0.03/image).

## How This Skill Is Used

This skill is invoked by other commands or agents that need Gemini capabilities:

- **Images**: Typically saved to an idea folder's views directory (e.g., `ideas/0001-my-idea/views/diagram-concept.png`) alongside or as part of a view. The calling command determines the output path.

- **Text**: Returned to stdout; the calling thread captures and uses the response directly.

## Image Generation

```bash
.venv/bin/python3 scripts/gemini.py image "PROMPT" --output "PATH"
```

Example:
```bash
.venv/bin/python3 scripts/gemini.py image "minimalist diagram of idea flow" --output ideas/0001-example/views/flow-diagram.png
```

## Text Generation

```bash
.venv/bin/python3 scripts/gemini.py text "PROMPT"
```

Example:
```bash
.venv/bin/python3 scripts/gemini.py text "Summarize the key themes of creative collaboration"
```

Output prints to stdout for the calling thread to use.
