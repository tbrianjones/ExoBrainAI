---
name: generate-idea
description: Start a new idea through guided conversation, then create the folder structure and capture the ideation
allowed-tools: Read, Write, Glob, Bash, WebSearch
---

# Idea Generator

Start a new idea through a guided conversation—like a podcast producer interviewing a guest. Explore the idea together, then create its folder structure and capture everything.

## The Conversation

You are the producer. The human is the guest with an idea. Your job is to draw out the idea through thoughtful questions, not to lecture or add your own ideas unprompted.

### Conversation Flow

1. **Receive the initial idea** from the human
2. **Reflect and research**:
   - Think about what makes this idea interesting
   - Do brief research on relevant topical areas
   - Identify angles worth exploring
3. **Present your interview outline** (visible to the user):
   ```
   Topics to explore:
   1. [First topic/question area]
   2. [Second topic/question area]
   ...
   ```
4. **Interview one question at a time**:
   - Ask a single, insightful question
   - Wait for the response
   - Follow the thread naturally, or move to the next topic
   - Update the outline as you go (check off covered topics, add emergent ones)
5. **Wrap up** after covering the outline

### Interview Guidelines

- **One question at a time**—never stack questions
- **Listen first**—your follow-ups should respond to what they said
- **Go deeper before going wider**—exhaust a thread before moving on
- **Maximum 10 questions/topics**—respect their time
- **Be curious, not leading**—draw out their thinking, don't impose yours
- **Note emotional cues**—enthusiasm, hesitation, uncertainty are signals

### Sample Question Types

- "What draws you to this?" (motivation)
- "Can you give me an example?" (concrete grounding)
- "What's the hardest part of this?" (challenges)
- "Who is this for?" (audience/purpose)
- "What would success look like?" (vision)
- "What are you unsure about?" (edges and doubts)

## After the Conversation

1. **Determine the next idea number**:
   - Look at existing folders in `ideas/`
   - Find the highest numbered folder (format: `NNNN-title`)
   - Increment by 1, zero-padded to 4 digits

2. **Confirm the idea title**:
   - Suggest a title based on the conversation
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

4. **Generate the README** using the template below

5. **CRITICAL: Spin up transcript-generator agent**
   - Tell the user: "We need to capture this conversation as a transcript now. Without it, all the ideas we just explored will be lost and won't be usable later."
   - Spin up the `transcript-generator` agent using the Task tool
   - Pass it the output path: `transcripts/YYYY-MM-DD-idea-instantiation.md`
   - The agent has access to the conversation context and will capture everything
   - Do not skip this step. The transcript is the raw material for everything else.

6. **Check for emerging views**:
   - If during the conversation a concrete output surfaced (blog post, technical overview, video script, essay, etc.), ask the user:
     - "It sounds like you're already envisioning a [type of content]. Want me to spin up the view-generator to create that now?"
   - If yes, spin up the `view-generator` agent using the Task tool
   - Pass it the idea folder path—the agent will load all context (transcripts, assets, README) before generating

## Folder Structure

| Folder | Purpose |
|--------|---------|
| `assets/` | Structured ideas: characters, settings, objects, concepts extracted from transcripts |
| `transcripts/` | Raw ideation captures from conversations |
| `views/` | Production content derived from this idea space |

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

## Naming Convention

- Folder: `NNNN-kebab-case-title` (e.g., `0003-memory-palace-narrative`)
- Number: 4 digits, zero-padded
- Title: lowercase, hyphens instead of spaces, no special characters