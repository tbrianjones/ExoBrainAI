---
name: generate-transcript
description: Capture the current conversation as a transcript. Runs summary generator and raw generator, then verifies output.
allowed-tools: Task, AskUserQuestion, Read, Glob
---

# Generate Transcript

Capture the current ideation conversation as both a synthesized summary and verbatim raw transcript.

## Process

1. Ask the user which idea space and topic name
2. Run `transcript-summary-generator` → writes `-summary.md`
3. Run `transcript-raw-generator` → writes `-raw.md`
4. Verify both files

## File Naming

Both files go to `ideas/NNNN-name/transcripts/` with the same base name:
- `YYYY-MM-DD-topic-summary.md`
- `YYYY-MM-DD-topic-raw.md`

## Verification

After both agents complete, read both files and verify:

**For the summary file:**
- Has header with metadata (person, ai, emotional analysis, source thread)
- Has Ideas & Themes section with bolded titles and summaries
- Has Transcript Summary section with topical headings
- Content is synthesized/distilled, not verbatim

**For the raw file:**
- Has minimal header (title, person, ai, date, source thread)
- Body is verbatim dialogue with speaker labels and separators
- No topic labels, question numbers, or added structure
- Dialogue matches actual conversation (minus stripped tool calls/admin content)
- Human's words are their actual words, not paraphrased

If verification fails, report what's wrong.
