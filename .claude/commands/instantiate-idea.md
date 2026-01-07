---
name: instantiate-idea
description: Create the folder structure for a new idea space
allowed-tools: Read, Write, Glob, Bash
---

# Instantiate Idea

Create the folder structure for a new idea space. This is the scaffolding command; it creates the infrastructure without conducting an interview.

## When Called

This command can be invoked two ways:

1. **From `/ideate`** - Called automatically when a new idea is being explored. The thread already has rich context from the conversation, so the README can be generated automatically.

2. **Standalone** - Called directly by the user. Will need to gather minimal information to create the structure.

## Process

1. **Determine the next idea number**:
   - Look at existing folders in `ideas/`
   - Find the highest numbered folder (format: `NNNN-title`)
   - Increment by 1, zero-padded to 4 digits

2. **Get or confirm the idea title**:
   - If called from `/ideate`: suggest a title based on the conversation
   - If standalone: ask for a title
   - Let the human approve or revise
   - Convert to kebab-case (lowercase, hyphens for spaces)

3. **Create the folder structure**:
   ```
   ideas/
   └── NNNN-title/
       ├── README.md
       ├── assets/
       │   └── .gitkeep
       ├── transcripts/
       │   └── .gitkeep
       └── views/
           └── .gitkeep
   ```

4. **Generate the README**:
   - If called from `/ideate`: use conversation context to write a rich summary
   - If standalone: ask for a brief description, or write a minimal placeholder

## README Template

```markdown
# [Idea Title]

**Created**: [YYYY-MM-DD]
**Status**: seed

## Summary

[2-4 sentences describing the core idea and what makes it interesting]

## Origin

[Brief note on where this idea came from—a conversation topic, a question, a spark]

## Open Questions

- [Question or uncertainty to explore]
- [Question or uncertainty to explore]
```

## Folder Structure

| Folder | Purpose |
|--------|---------|
| `assets/` | Structured ideas: characters, settings, objects, concepts extracted from transcripts |
| `transcripts/` | Raw ideation captures from conversations |
| `views/` | Production content derived from this idea space |

## Naming Convention

- Folder: `NNNN-kebab-case-title` (e.g., `0003-memory-palace-narrative`)
- Number: 4 digits, zero-padded
- Title: lowercase, hyphens instead of spaces, no special characters

## After Creation

- If called from `/ideate`: return control to ideate, which will continue with the interview
- If standalone: confirm creation and suggest next steps ("You can now run `/ideate` to explore this idea, or add content directly to the folder")
