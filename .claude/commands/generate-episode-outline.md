---
name: generate-episode-outline
description: Generate Zengineering podcast pre-production outlines from brainstorm transcripts or idea space content. Produces story beats with terse note-card prompts for improvised delivery.
allowed-tools: Read, Write, Glob, Bash
---

# Zengineering Episode Outline Generator

Generate pre-production outlines for the Zengineering podcast. These outlines are producer notes; structured story beats that let the hosts improv their way back to the key ideas from a brainstorm session.

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

## Output Format

The outline has two sections: a **Read-Through Context** section and a **Story Beats** distillate.

### Section 1: Read-Through Context

A narrative outline with acts, numbered topics, and explanatory prose. This is for pre-read; understanding the episode arc before recording. Include:

- Episode structure (cold open, acts, wrap)
- Numbered topic descriptions with enough context to understand the argument
- Key quotes from the brainstorm worth hitting on air
- References or props to have handy

### Section 2: Story Beats (the note cards)

This is the distillate Adam actually uses while recording. Rules:

- **Each story beat is a bolded bullet** corresponding to a major topic from the read-through
- **No more than 3 sub-bullets** under each beat
- **Sub-bullets are 2-3 words max**; terse thematic prompts, not sentences
- The goal is to trigger recall, not explain; these are improv cue cards
- If a specific quote is worth hitting, include it as a beat with 2-3 word sub-bullets explaining how the conversation arrived there

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

### ACT 3: Where This Leads

- **Education shifts**
  - skills to humanity
  - writing becomes like Latin
  - cognitive vs. vocational
```

Act headings in the story beats section mirror the acts from the read-through context, so the producer can see the episode structure at a glance while scanning the note cards.

Keep the story beats to one page if possible. Brevity is the entire point.

## Process

1. **Load context** (projected files, transcripts, brainstorm notes)

2. **Confirm the episode** with the user:
   - Which episode / topic?
   - Any specific angles to emphasize or cut?
   - Approximate target runtime? (affects how many beats)

3. **Generate the outline**:
   - Write the read-through context first (narrative structure)
   - Then distill into story beats (the note cards)
   - Include a key quotes section between the two

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

## Content Guidelines

- **No dashes or double dashes.** Use semicolons or restructure.
- Preserve the hosts' phrasing when it captures an idea well.
- Story beat sub-bullets are fragments, not sentences. Two to three words.
- Pull quotes should be verbatim from the brainstorm transcript.
- Keep the tone of the read-through conversational; these are notes between collaborators, not a script.
