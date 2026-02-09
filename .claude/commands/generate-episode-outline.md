---
name: generate-episode-outline
description: Generate Zengineering podcast pre-production outlines from brainstorm transcripts or idea space content. Produces three layers of depth from quick-scan to full narrative.
allowed-tools: Read, Write, Glob, Bash
---

# Zengineering Episode Outline Generator

Generate pre-production outlines for the Zengineering podcast. The outline is structured in three layers of increasing depth so the producer can scan at whatever level of detail they need.

## CRITICAL: Load Context First

Before any interaction with the user, load the episode's content from ExoBrain:

1. **Refresh projection**: `docker compose exec exobrain exobrain project`

2. **Read `.env`** to determine `EXOBRAIN_DATA_DIR`

3. **Read the space's CLAUDE.md index**: `$EXOBRAIN_DATA_DIR/projected/ideas/zengineering/episodes/{episode-name}/CLAUDE.md`

4. **Read ALL projected files** in the episode directory: `$EXOBRAIN_DATA_DIR/projected/ideas/zengineering/episodes/{episode-name}/*.md`
   - Transcripts, brainstorm notes, concept objects; all are source material
   - Look for existing outlines to revise rather than starting from scratch

If no episode space exists yet, ask which idea space or transcript to work from.

## About Zengineering

Zengineering is a podcast about the intersection of science, technology, engineering, philosophy, art, and spirituality. Hosts are Brian and Adam. The show structure for engineering episodes:

- **Quick intro**: Name the topic, hook the listener
- **Back up to first principles**: Foundational context; cultural, scientific, philosophical
- **Build forward**: Connect first principles to the modern technological or sociological reason the topic matters
- **Wrap**: Revisit central tension, tease what's next

## Output Format: Three Layers of Depth

The outline has three sections, ordered from most compressed to most detailed. The producer reads top-down; the quick scan tells you the shape, the story beats give you the improv cues, and the full narrative gives you the context if you need it.

### Layer 1: Quick Scan (the one-pager)

The highest level view. Just the acts and their major beats; nothing else. This is what you glance at to remember the shape of the episode.

- Act headings (### level)
- 2-5 **bolded beat titles** per act; no sub-bullets, no explanation
- The entire quick scan should fit in a single screen

Example:

```
## Quick Scan

### ACT 1: First Principles
- **Taste vs. judgment**
- **The apprenticeship grind**
- **Middle management filter**

### ACT 2: The Execution Collapse
- **Cost trends to zero**
- **CTO becomes CEO**
- **Talent pipeline tension**
- **The freak artist factor**

### ACT 3: The Education Question
- **What do I teach 19 year olds?**
- **Education becomes humanity**

### WRAP
- **The central tension**
```

### Layer 2: Story Beats (the note cards)

Expanded version of the quick scan. Same act headings, same bolded beats, but now each beat has up to 3 sub-bullets of 2-3 words each. These are the improv cue cards Adam uses while recording.

Rules:
- **Each story beat is a bolded bullet** corresponding to a major topic
- **No more than 3 sub-bullets** under each beat
- **Sub-bullets are 2-3 words max**; terse thematic prompts, not sentences
- If a specific quote is worth hitting, include it as a beat with sub-bullets explaining how the conversation arrived there
- Keep the story beats to one page if possible

Example:

```
## Story Beats

### ACT 1: First Principles

- **Taste vs. judgment**
  - aesthetic knowing
  - decisional knowing
  - apprenticeship model

### ACT 2: The Modern Context

- **Execution cost collapse**
  - commodity pricing
  - UI layers vanish
  - data layer stays

- **"The CTO will be the CEO"** (Brian)
  - agents eat business ops
  - technical fluency rises
  - more people can build
```

### Layer 3: Full Narrative (the read-through)

The complete narrative outline with acts, numbered topics, explanatory prose, and key quotes. This is for pre-read before recording; understanding the full argument and having context for each beat. Include:

- Episode structure (cold open, acts, wrap)
- Numbered topic descriptions with enough context to understand the argument
- Key quotes from the brainstorm worth hitting on air (collected in their own section)
- References or props to have handy

## Process

1. **Load context** (projected files, transcripts, brainstorm notes)

2. **Confirm the episode** with the user:
   - Which episode / topic?
   - Any specific angles to emphasize or cut?
   - Approximate target runtime? (affects how many beats)

3. **Generate the outline**:
   - Write the full narrative first (Layer 3) to understand the episode
   - Distill into story beats (Layer 2)
   - Compress into quick scan (Layer 1)
   - Present in order: Layer 1, Layer 2, Key Quotes, Layer 3

4. **Present to the user for feedback**

5. **Save to ExoBrain**:
   ```bash
   cat <<'CONTENT' | docker compose exec -T exobrain exobrain capture \
     --title "Episode Outline: [Episode Title]" \
     --type document \
     --space "ideas/zengineering/episodes/[episode-name]" \
     --tag episode-outline --tag zengineering --tag producer-notes \
     --always-project \
     --json
   [outline content]
   CONTENT
   ```
   Then refresh: `docker compose exec exobrain exobrain project`

6. **Create links** between the outline and its source material:
   - Outline → `derived-from` → Transcript (if derived from a brainstorm)
   - Outline → `derived-from` → Concept (if the episode concept exists)
   - Cross-space `related-to` links for topics that connect to other idea spaces

## Content Guidelines

- **No dashes or double dashes.** Use semicolons or restructure.
- Preserve the hosts' phrasing when it captures an idea well.
- Story beat sub-bullets are fragments, not sentences. Two to three words.
- Pull quotes should be verbatim from the brainstorm transcript.
- Keep the tone of the full narrative conversational; these are notes between collaborators, not a script.
