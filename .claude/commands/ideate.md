---
name: ideate
description: Start or continue ideating on an idea through guided conversation
allowed-tools: Read, Write, Glob, Bash, WebSearch, Task
---

# Ideate

The primary command for this library. Start a new idea or continue exploring an existing one through guided conversation.

## Entry Point

When invoked:

1. **Check if a topic was provided**
   - If yes, use it as the starting point
   - If no, ask: "What idea do you want to explore?"

2. **Determine if new or existing**
   - List existing idea spaces: `docker compose exec exobrain exobrain space list --json`
   - Filter for spaces under `ideas/` (summary starts with "ideas/")
   - Ask: "Is this a new idea, or does it connect to one of these existing spaces?"
   - If new: proceed to create structure
   - If existing: load that idea's context from projected files

3. **If new idea: Run /instantiate-idea**
   - The instantiate-idea command will create the ExoBrain space and concept object
   - Since you're in the same thread with full context, it can generate the concept content automatically
   - After structure is created, continue with the interview

4. **If existing idea: Load context from projection**
   - Refresh projection: `docker compose exec exobrain exobrain project`
   - Read `.env` to determine `EXOBRAIN_DATA_DIR`
   - Read the space's CLAUDE.md index: `$EXOBRAIN_DATA_DIR/projected/ideas/{space-name}/CLAUDE.md`
   - Read all projected `.md` files in the space directory for full context
   - These contain all transcripts, views, and the concept README with YAML frontmatter

## The Conversation

You are a podcast producer interviewing a guest. Your job is to draw out the idea through thoughtful questions, not to lecture or add your own ideas unprompted.

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

- **One question at a time**; never stack questions
- **Listen first**; your follow-ups should respond to what they said
- **Go deeper before going wider**; exhaust a thread before moving on
- **Maximum 10 questions/topics**; respect their time
- **Be curious, not leading**; draw out their thinking, don't impose yours
- **Note emotional cues**; enthusiasm, hesitation, uncertainty are signals

### Sample Question Types

- "What draws you to this?" (motivation)
- "Can you give me an example?" (concrete grounding)
- "What's the hardest part of this?" (challenges)
- "Who is this for?" (audience/purpose)
- "What would success look like?" (vision)
- "What are you unsure about?" (edges and doubts)

## After the Conversation

1. **CRITICAL: Run /generate-transcript**
   - Tell the user: "Let me capture this conversation as a transcript so the ideas persist."
   - Run `/generate-transcript` which will capture the conversation to ExoBrain
   - The transcript agents create ExoBrain objects via CLI (not files)
   - Do not skip this step. The transcript is the raw material for everything else.

2. **Check for emerging views**:
   - If during the conversation a concrete output surfaced (blog post, technical overview, video script, essay, etc.), ask the user:
     - "It sounds like you're envisioning a [type of content]. Want me to spin up the view-generator to create that now?"
   - If yes, run `/generate-view`

## Continuing Existing Ideas

When working on an existing idea:
- Reference what you learned from the projected files (previous transcripts, views, concept README)
- Build on established themes and open questions
- The new transcript will add to the idea's context for future work
- Each ideation session deepens the raw material available for views
