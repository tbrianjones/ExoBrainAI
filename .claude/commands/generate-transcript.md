---
name: generate-transcript
description: Capture the current conversation as a transcript. Spins up transcript-generator agent.
allowed-tools: Task
---

# Generate Transcript

Capture the current ideation conversation as a transcript.

## Usage

Ask the user which idea space this transcript belongs to, then spin up the `transcript-generator` agent with:
- Output path: `ideas/NNNN-name/transcripts/YYYY-MM-DD-[topic].md`
- The agent has access to conversation context and will handle the rest
