# Procedure: Extracting Development Transcripts from Claude Code Sessions

This procedure documents how to extract a complete, readable transcript from a Claude Code JSONL conversation file; particularly useful for development sessions with extensive tool usage, subagent spawning, and interactive Q&A.

## When to Use This Procedure

Use this for Claude Code development conversations that include:
- Subagent spawning (research agents, specialist agents)
- Interactive Q&A using AskUserQuestion tool
- File edits, writes, and bash commands
- ASCII diagrams, code blocks, and structured output
- Long planning sessions with back-and-forth dialogue

The standard transcript generators strip too much content from these sessions. This procedure preserves the full substance.

## Step 1: Locate the Conversation JSONL File

Claude Code stores conversation files at:
```
~/.claude/projects/-Users-{username}-projects-{repo-name}/{session-uuid}.jsonl
```

To find a specific conversation:
```bash
# List recent large files in a project
ls -lahS ~/.claude/projects/-Users-tbj-projects-{repo-name}/*.jsonl | head -20

# Search for content within files
grep -l "keyword from conversation" ~/.claude/projects/-Users-tbj-projects-{repo-name}/*.jsonl

# Find files modified in last N hours
find ~/.claude/projects/-Users-tbj-projects-{repo-name} -name "*.jsonl" -mmin -{minutes} -size +1M
```

## Step 2: Run the Extraction Script

Use the Python extraction script that handles:
- User messages (plain text)
- Assistant messages with full content
- AskUserQuestion tool calls (formatted as "Questions for TBJ")
- User answers to questions (formatted as Q:/A: pairs)
- Tool usage markers ([Spawning agent: ...], [Writing file: ...], etc.)
- Consecutive edit consolidation ([Edited file.md (25 changes)])
- System tag cleanup (removes `<system-reminder>`, command tags, etc.)

### Script Location

```
/private/tmp/claude-501/-Users-tbj-projects-claude-writer/{session}/scratchpad/extract_full_transcript_v4.py
```

Or copy the script from the end of this document.

### Usage

```bash
python3 extract_full_transcript.py \
  "/path/to/source.jsonl" \
  "/path/to/output-raw-complete.md"
```

## Step 3: Verify the Output

Check that the transcript includes:

1. **Full user messages** ; your words exactly as spoken/typed
2. **Full Claude responses** ; including tables, ASCII diagrams, code blocks, lists
3. **Questions asked** ; formatted with options displayed
4. **Your answers** ; formatted as Q:/A: pairs after each question set
5. **Agent spawning** ; `[Spawning agent: description]` markers
6. **File operations** ; consolidated edit counts, write markers
7. **No system cruft** ; system reminders, command tags stripped

## Output Format

```markdown
# Full Transcript: {Topic} (Complete)
- person: TBJ
- ai: Claude (Claude Code)
- date: YYYY-MM-DD
- source thread: {session-uuid}

---

**TBJ:**

{user message}

---

**Claude:**

{claude response with full content}

---

**Questions for TBJ:**

**Header:** Question text?
  - Option 1: Description
  - Option 2: Description

---

**TBJ's Answers to Claude's Questions:**

**Q:** Question text?

**A:** Full answer text

---

**Claude:**

{response addressing the answers}

---
```

## Key Design Decisions

### Why preserve AskUserQuestion exchanges?

Development conversations rely heavily on interactive Q&A. Claude asks clarifying questions, you answer, and Claude proceeds based on your answers. Without capturing both sides, the transcript loses critical context about why certain decisions were made.

### Why consolidate edits?

A single logical change to a file often requires 10-30 sequential Edit tool calls. Showing each one adds noise. Consolidating to `[Edited filename.md (25 changes)]` preserves the fact that editing happened without cluttering the transcript.

### Why keep agent spawn markers?

Knowing when Claude delegated to subagents explains gaps in the conversation and shows the orchestration pattern. The markers are brief but informative.

### Why strip system reminders?

System reminders are injected by Claude Code infrastructure and aren't part of the actual conversation. They add noise and distract from the dialogue.

## Extraction Script (v4)

```python
#!/usr/bin/env python3
"""Extract full transcript from Claude Code JSONL with all content preserved."""

import json
import re
import sys
from collections import defaultdict

def clean_content(text: str) -> str:
    """Remove system tags and clean up content."""
    text = re.sub(r'<system-reminder>.*?</system-reminder>', '', text, flags=re.DOTALL)
    text = re.sub(r'<local-command-caveat>.*?</local-command-caveat>', '', text, flags=re.DOTALL)
    text = re.sub(r'<local-command-stdout>.*?</local-command-stdout>', '', text, flags=re.DOTALL)
    text = re.sub(r'<command-name>.*?</command-name>', '', text, flags=re.DOTALL)
    text = re.sub(r'<command-message>.*?</command-message>', '', text, flags=re.DOTALL)
    text = re.sub(r'<command-args>.*?</command-args>', '', text, flags=re.DOTALL)
    text = re.sub(r'<task-notification>', '', text)
    text = re.sub(r'</task-notification>', '', text)
    text = re.sub(r'<task-id>.*?</task-id>', '', text)
    text = re.sub(r'<status>.*?</status>', '', text)
    text = re.sub(r'<summary>.*?</summary>', '', text)
    text = re.sub(r'<result>', '\n**Agent Result:**\n', text)
    text = re.sub(r'</result>', '', text)
    return text.strip()

def parse_question_answers(content: str) -> list:
    """Parse 'User has answered your questions:' format into Q&A pairs."""
    if 'User has answered your questions:' not in content:
        return []
    match = re.search(r'User has answered your questions:\s*(.+?)(?:\.\s*You can now continue|$)', content, re.DOTALL)
    if not match:
        return []
    qa_text = match.group(1)
    pairs = []
    pattern = r'"([^"]+)"="([^"]*)"'
    for m in re.finditer(pattern, qa_text):
        pairs.append((m.group(1), m.group(2)))
    return pairs

def format_qa_section(qa_pairs: list) -> str:
    """Format Q&A pairs into readable markdown."""
    if not qa_pairs:
        return ""
    lines = ["**TBJ's Answers to Claude's Questions:**", ""]
    for q, a in qa_pairs:
        lines.append(f"**Q:** {q}")
        lines.append("")
        lines.append(f"**A:** {a}")
        lines.append("")
    return '\n'.join(lines)

def extract_transcript(jsonl_path: str, output_path: str):
    """Extract full conversation from JSONL file."""
    lines = []
    with open(jsonl_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    lines.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    entries = []
    for entry in lines:
        msg_type = entry.get('type')

        if msg_type == 'user':
            message = entry.get('message', {})
            content = message.get('content', '')

            if isinstance(content, list):
                text_parts = []
                qa_pairs = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get('type') == 'text':
                            text_parts.append(block.get('text', ''))
                        elif block.get('type') == 'tool_result':
                            tool_content = block.get('content', '')
                            pairs = parse_question_answers(tool_content)
                            if pairs:
                                qa_pairs.extend(pairs)
                    elif isinstance(block, str):
                        text_parts.append(block)

                if qa_pairs:
                    qa_formatted = format_qa_section(qa_pairs)
                    entries.append({'type': 'user_qa', 'text': qa_formatted, 'edits': []})

                content = '\n'.join(text_parts)

            content = clean_content(content)
            if content and content.strip() and not content.startswith('{'):
                entries.append({'type': 'user', 'text': content.strip(), 'edits': []})

        elif msg_type == 'assistant':
            message = entry.get('message', {})
            content = message.get('content', [])

            text_parts = []
            edits = []

            for block in content:
                if isinstance(block, dict):
                    block_type = block.get('type')
                    if block_type == 'text':
                        text = block.get('text', '')
                        if text.strip():
                            text_parts.append(text)
                    elif block_type == 'tool_use':
                        tool_name = block.get('name', 'unknown')
                        tool_input = block.get('input', {})

                        if tool_name == 'Task':
                            desc = tool_input.get('description', '')
                            if desc:
                                text_parts.append(f"[Spawning agent: {desc}]")
                        elif tool_name == 'Write':
                            file_path = tool_input.get('file_path', '')
                            if file_path:
                                text_parts.append(f"[Writing file: {file_path}]")
                        elif tool_name == 'Edit':
                            file_path = tool_input.get('file_path', '')
                            if file_path:
                                edits.append(file_path)
                        elif tool_name == 'Bash':
                            desc = tool_input.get('description', '')
                            cmd = tool_input.get('command', '')
                            if desc:
                                text_parts.append(f"[Running: {desc}]")
                            elif cmd and len(cmd) < 150:
                                text_parts.append(f"[Running: `{cmd}`]")
                        elif tool_name == 'AskUserQuestion':
                            questions = tool_input.get('questions', [])
                            if questions:
                                q_text = ["**Questions for TBJ:**", ""]
                                for q in questions:
                                    question = q.get('question', '')
                                    options = q.get('options', [])
                                    q_text.append(f"**{q.get('header', 'Question')}:** {question}")
                                    for opt in options:
                                        label = opt.get('label', '')
                                        desc = opt.get('description', '')
                                        q_text.append(f"  - {label}: {desc}")
                                    q_text.append("")
                                text_parts.append('\n'.join(q_text))
                elif isinstance(block, str):
                    if block.strip():
                        text_parts.append(block)

            combined = '\n\n'.join(text_parts)
            combined = clean_content(combined)
            entries.append({'type': 'assistant', 'text': combined.strip(), 'edits': edits})

    # Consolidate consecutive edit-only messages
    consolidated = []
    pending_edits = defaultdict(int)

    def flush_edits():
        nonlocal pending_edits
        if pending_edits:
            edit_text = []
            for f, count in pending_edits.items():
                short_f = f.split('/')[-1]
                if count > 1:
                    edit_text.append(f"[Edited {short_f} ({count} changes)]")
                else:
                    edit_text.append(f"[Edited {short_f}]")
            consolidated.append({'type': 'assistant', 'text': '\n'.join(edit_text)})
            pending_edits = defaultdict(int)

    for entry in entries:
        if entry['type'] in ('user', 'user_qa'):
            flush_edits()
            if entry['text']:
                consolidated.append(entry)
        else:
            has_text = bool(entry['text'])
            has_edits = bool(entry.get('edits', []))
            if has_text:
                flush_edits()
                consolidated.append(entry)
            elif has_edits:
                for f in entry['edits']:
                    pending_edits[f] += 1

    flush_edits()

    # Output
    output = []
    output.append("# Full Transcript: Topic (Complete)")
    output.append("- person: TBJ")
    output.append("- ai: Claude (Claude Code)")
    output.append("- date: YYYY-MM-DD")
    output.append("- source thread: session-uuid")
    output.append("")
    output.append("---")
    output.append("")

    for entry in consolidated:
        if entry['type'] == 'user':
            output.append("**TBJ:**")
            output.append("")
            output.append(entry['text'])
            output.append("")
            output.append("---")
            output.append("")
        elif entry['type'] == 'user_qa':
            output.append(entry['text'])
            output.append("")
            output.append("---")
            output.append("")
        else:
            if entry['text']:
                output.append("**Claude:**")
                output.append("")
                output.append(entry['text'])
                output.append("")
                output.append("---")
                output.append("")

    while output and output[-1] in ('', '---'):
        output.pop()

    with open(output_path, 'w') as f:
        f.write('\n'.join(output))

    print(f"Wrote {len(output)} lines to {output_path}")

if __name__ == '__main__':
    extract_transcript(sys.argv[1], sys.argv[2])
```

## Future Enhancement: Command/Skill

This procedure could become a `/generate-dev-transcript` command that:
1. Prompts for the JSONL file path (or helps locate it)
2. Prompts for the idea space and topic name
3. Runs the extraction
4. Saves to the appropriate transcripts folder
5. Optionally generates a summary alongside the raw complete version

The key differentiator from `/generate-transcript` is preserving full tool interactions and Q&A exchanges that are essential context in development conversations.
