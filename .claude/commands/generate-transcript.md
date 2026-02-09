---
name: generate-transcript
description: Capture the current conversation as a transcript. Runs summary generator and raw generator, then verifies output.
allowed-tools: Task, AskUserQuestion, Read, Glob, Bash
---

# Generate Transcript

Capture the current ideation conversation as both a synthesized summary and verbatim raw transcript, stored as ExoBrain objects.

## Process

1. Ask the user which idea space (list spaces with `docker compose exec exobrain exobrain space list --json`, filter for `ideas/` spaces) and topic name
2. Run `transcript-summary-generator` agent; it creates a Transcript object in ExoBrain via CLI
3. Run `transcript-raw-generator` agent; it creates a Transcript object in ExoBrain via CLI
4. Create a `derived-from` link between the summary and raw objects
5. Refresh projection: `docker compose exec exobrain exobrain project`
6. Verify both objects exist

## Agent Invocation

Pass each agent:
- The ExoBrain space name (e.g., `ideas/exobrain`)
- A topic name (kebab-case, e.g., `exobrain-core-vision`)
- Today's date (YYYY-MM-DD)

The agents will:
- Create ExoBrain objects via `docker compose exec exobrain exobrain capture` (piping content via stdin)
- Use `--type transcript --space "ideas/space-name" --always-project --json`
- The summary agent tags with `transcript`, `summary`
- The raw agent tags with `transcript`, `raw`
- Both use `--created-at` with today's date

## After Both Agents Complete

1. Create a link between summary and raw:
   ```bash
   docker compose exec exobrain exobrain link create <summary-id> <raw-id> "derived-from" --json
   ```

2. Refresh projection:
   ```bash
   docker compose exec exobrain exobrain project
   ```

3. Verify by listing the space:
   ```bash
   docker compose exec exobrain exobrain list --space "ideas/space-name" --tag transcript --json
   ```

## Verification

**For the summary object:**
- Has title containing the topic name
- Tagged with `transcript` and `summary`
- Content has Ideas & Themes section and Transcript Summary section
- Content is synthesized/distilled, not verbatim

**For the raw object:**
- Has title containing the topic name
- Tagged with `transcript` and `raw`
- Body is verbatim dialogue with speaker labels and separators
- Human's words are their actual words, not paraphrased

If verification fails, report what's wrong.
