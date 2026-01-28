# ADR 004: Claude Code as First UI for ExoBrain

- **Status:** Accepted
- **Date:** 2026-01-27
- **Tags:** architecture, ui, claude-code
- **Impact:** Medium

## Context

ExoBrain needs a user interface for capture, query, and annotation workflows. Several options were considered: a custom web UI, a desktop application, a terminal UI (TUI), or leveraging Claude Code, which is already the user's primary development and writing environment via the claude_writer project.

The user's existing workflow is entirely within Claude Code. Commands like `/ideate`, `/generate-view`, and `/generate-transcript` already orchestrate complex multi-step processes. Adding ExoBrain interactions to this same environment means zero context switching and immediate access to the full knowledge system during ideation and writing.

## Decision Drivers

1. **Zero context switching**: The user already lives in Claude Code for writing and ideation; ExoBrain should meet them there
2. **Rapid iteration**: Claude Code commands and skills can be updated in minutes, not days
3. **AI-native interface**: Claude can propose titles, summaries, and tags during capture; a traditional UI cannot
4. **No new infrastructure**: No web server, no frontend build pipeline, no additional containers
5. **CLI as stable contract**: The ExoBrain CLI provides a well-defined interface that Claude Code invokes; this keeps concerns separated

## Considered Options

### 1. Custom Web UI

- Rejected: Requires building and maintaining a frontend application, adding a new container, and designing API endpoints. No current consumer justifies this cost.

### 2. Desktop Application (Electron/Tauri)

- Rejected: Significant development effort for a single user system. Adds a new technology stack to maintain.

### 3. Terminal UI (textual/rich)

- Rejected: Better than a web UI for a terminal workflow, but still requires building a standalone application. Does not leverage Claude's ability to propose metadata.

### 4. Claude Code via ExoBrain Skill (chosen)

- Uses the existing `.claude/skills/exobrain.md` skill to invoke CLI commands
- Claude proposes titles, summaries, and tags during capture; the user confirms or adjusts
- Structured output via `--json` flag enables Claude to parse responses reliably
- No new infrastructure; just skill files and command definitions

## Decision Outcome

Chosen option: **Claude Code as first UI, invoking ExoBrain CLI through the exobrain skill**

Claude Code acts as the intelligent frontend layer. It invokes the ExoBrain CLI for all operations (capture, query, annotate, stage, index) and parses structured JSON output. During capture workflows, Claude proposes metadata (titles, summaries, tags with confidence scores) that the user can accept, modify, or reject.

This is explicitly a "first UI" decision, not a "only UI" decision. A web UI or API layer can be added later when there is a real consumer. The CLI remains the stable contract between any UI and the ExoBrain engine.

### How It Works

1. User initiates a workflow in Claude Code (e.g., "capture this thought" or "what themes emerge?")
2. The exobrain skill translates the request into CLI commands with `--json` output
3. Claude parses the JSON response and presents results conversationally
4. For capture workflows, Claude generates proposed metadata (title, summary, tags) and confirms with the user before writing overlays

## Consequences

### Positive

- **Immediate availability**: No new application to build; works today with skill files
- **AI-augmented capture**: Claude proposes metadata that would be tedious to type manually
- **Single environment**: Writing, ideation, and memory all happen in the same context
- **Rapid iteration**: Updating a skill file is faster than shipping a new UI version
- **CLI as contract**: Any future UI can use the same CLI; Claude Code is not special-cased

### Negative

- **Single user**: Claude Code is inherently a single-user, single-session tool; this UI cannot serve multiple users or concurrent access
- **No persistent UI state**: Each Claude Code session starts fresh; there is no dashboard or persistent view of the knowledge graph
- **Requires Claude Code**: Users without Claude Code cannot interact with ExoBrain through this interface (mitigated by CLI being directly usable)
- **LLM cost**: Every interaction involves Claude API calls, even for simple queries that a traditional UI would handle locally

### Neutral

- **Skill file maintenance**: The exobrain skill must be updated when CLI output schemas change, but this is comparable to maintaining API client code

## Agent Rules

1. **MUST** invoke ExoBrain CLI commands through the exobrain skill; never access the SQLite database or file system directly for ExoBrain operations.

2. **MUST** use the `--json` flag when parsing CLI output programmatically. Human-readable output is for display only; structured operations require JSON.

3. **SHOULD** propose titles, summaries, and tags during capture workflows. Present these to the user for confirmation before writing overlay records.

4. **MUST** document `--json` output schemas in the exobrain skill file (`.claude/skills/exobrain.md`) whenever new CLI commands are added or output formats change.

5. **MUST NOT** bypass the CLI to read or write files in `$EXOBRAIN_DATA_DIR` directly. The CLI enforces validation, ID generation, and overlay semantics.

6. **SHOULD** surface query results conversationally, summarizing themes and connections rather than dumping raw output.

7. **MUST** handle CLI errors gracefully. If a command fails, present the error to the user with suggested remediation (e.g., "ExoBrain container may not be running; try `docker compose up -d`").

## References

- ExoBrain Skill: `.claude/skills/exobrain.md`
- ADR 001: `docs/adr/001-exobrain-v2-graphrag-memory-engine.md`
- Claude Code Commands: `.claude/commands/`
