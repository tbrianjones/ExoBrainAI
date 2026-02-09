---
name: instantiate-idea
description: Create a new idea space in ExoBrain
allowed-tools: Read, Write, Glob, Bash
---

# Instantiate Idea

Create a new idea space in ExoBrain. This is the scaffolding command; it creates the ExoBrain space and concept object without conducting an interview.

## When Called

This command can be invoked two ways:

1. **From `/ideate`** ; Called automatically when a new idea is being explored. The thread already has rich context from the conversation, so the concept content can be generated automatically.

2. **Standalone** ; Called directly by the user. Will need to gather minimal information to create the structure.

## Process

1. **Get or confirm the idea title**:
   - If called from `/ideate`: suggest a title based on the conversation
   - If standalone: ask for a title
   - Let the human approve or revise
   - Convert to kebab-case for the space name (lowercase, hyphens for spaces)

2. **Create the ExoBrain space**:
   ```bash
   docker compose exec exobrain exobrain space create "ideas/[kebab-case-title]" --json
   ```

3. **Create the concept object** (the README equivalent):
   ```bash
   docker compose exec exobrain exobrain capture "[concept content]" \
     --title "[Idea Title]" \
     --type concept \
     --space "ideas/[kebab-case-title]" \
     --tag idea-readme \
     --tag [topic-tag-1] \
     --tag [topic-tag-2] \
     --always-project \
     --json
   ```

   Content should follow this template:

   ```markdown
   # [Idea Title]

   **Status**: seed

   ## Summary

   [2-4 sentences describing the core idea and what makes it interesting]

   ## Origin

   [Brief note on where this idea came from; a conversation topic, a question, a spark]

   ## Open Questions

   - [Question or uncertainty to explore]
   - [Question or uncertainty to explore]
   ```

   - If called from `/ideate`: use conversation context to write a rich summary
   - If standalone: ask for a brief description, or write a minimal placeholder

4. **Refresh projection** so the new space is immediately visible:
   ```bash
   docker compose exec exobrain exobrain project
   ```

## Naming Convention

- Space name: `ideas/kebab-case-title` (e.g., `ideas/memory-palace-narrative`)
- Lowercase, hyphens instead of spaces, no special characters
- No numeric prefixes; ExoBrain uses created_at for ordering

## After Creation

- If called from `/ideate`: return control to ideate, which will continue with the interview
- If standalone: confirm creation and suggest next steps ("You can now run `/ideate` to explore this idea, or capture content directly via `exobrain capture`")
