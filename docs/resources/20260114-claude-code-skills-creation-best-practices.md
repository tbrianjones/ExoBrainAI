# Claude Code Skills Authoring Reference

A guide for creating effective skills based on Anthropic's official best practices and engineering patterns.

---

## How Skills Work (Architecture)

Understanding the loading mechanism is essential for writing effective skills.

### Two-Phase Loading

1. **Startup (metadata only)**: Only `name` and `description` from YAML frontmatter are loaded into the system prompt
2. **On-demand (full content)**: Claude reads SKILL.md body only when it decides the skill is relevant

**Critical implication**: The `description` field is the **primary triggering mechanism**. If Claude doesn't recognize your skill from its description, the body content is never loaded.

### Token Economics

- Metadata (name + description): Always in context
- SKILL.md body: Loaded only when triggered
- Reference files: Loaded only when Claude reads them
- Scripts: Executed without loading into context (only output consumes tokens)

---

## YAML Frontmatter (Required)

Every SKILL.md must start with YAML frontmatter containing exactly two fields:

```yaml
---
name: your-skill-name
description: What it does and when to use it
---
```

### `name` Field Rules

| Constraint | Requirement |
|------------|-------------|
| Max length | 64 characters |
| Allowed chars | Lowercase letters, numbers, hyphens only |
| Forbidden | XML tags, spaces, underscores |
| Reserved words | Cannot contain "anthropic" or "claude" |

**Naming convention**: Use gerund form (verb + -ing) for clarity.

```
✓ processing-pdfs
✓ analyzing-spreadsheets  
✓ generating-reports
✓ managing-databases

✗ pdf-helper
✗ utils
✗ my_skill
✗ Claude-Assistant
```

### `description` Field Rules

| Constraint | Requirement |
|------------|-------------|
| Max length | 1024 characters |
| Min length | Non-empty (required) |
| Forbidden | XML tags |
| Point of view | Always third person |

---

## Writing Effective Descriptions

The description is **the most important part of your skill**. Claude uses it to decide whether to invoke the skill from potentially 100+ available skills.

### Required Components

Every description must include:

1. **What** the skill does (capabilities)
2. **When** to use it (trigger conditions)

### Formula

```
[Capabilities summary]. Use when [specific trigger conditions].
```

### Third Person Only

The description is injected into the system prompt. Inconsistent point-of-view causes discovery problems.

```
✓ "Processes Excel files and generates reports"
✗ "I can help you process Excel files"
✗ "You can use this to process Excel files"
```

### Include Trigger Keywords

Include specific terms users might mention that should activate this skill.

```yaml
# Good: Specific triggers included
description: >
  Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDF files or when the user mentions PDFs, forms,
  or document extraction.

# Bad: Vague, no triggers
description: Helps with documents
```

### Anthropic's Pattern for Complex Skills

For skills with multiple use cases, enumerate them:

```yaml
description: >
  Comprehensive document creation, editing, and analysis with support for
  tracked changes, comments, formatting preservation, and text extraction.
  Use when Claude needs to work with professional documents (.docx files) for:
  (1) Creating new documents,
  (2) Modifying or editing content,
  (3) Working with tracked changes,
  (4) Adding comments,
  or any other document tasks.
```

### Real Examples from Anthropic Skills

**PDF Processing:**
```yaml
description: >
  Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDF files or when the user mentions PDFs, forms,
  or document extraction.
```

**Excel Analysis:**
```yaml
description: >
  Analyze Excel spreadsheets, create pivot tables, generate charts.
  Use when analyzing Excel files, spreadsheets, tabular data, or .xlsx files.
```

**Git Commit Helper:**
```yaml
description: >
  Generate descriptive commit messages by analyzing git diffs.
  Use when the user asks for help writing commit messages or reviewing
  staged changes.
```

**Skill Creator (meta-skill):**
```yaml
description: >
  Guide for creating effective skills. This skill should be used when
  users want to create a new skill (or update an existing skill) that
  extends Claude's capabilities with specialized knowledge, workflows,
  or tool integrations.
```

### Anti-Patterns

```yaml
# Too vague
description: Helps with documents

# No trigger conditions  
description: Processes data files

# Missing capabilities
description: Use when working with spreadsheets

# First person
description: I help you analyze code

# Too generic
description: Does stuff with files
```

---

## SKILL.md Body Structure

After the YAML frontmatter, the markdown body provides implementation details.

### Recommended Structure

```markdown
---
name: your-skill-name
description: [Capabilities]. Use when [triggers].
---

# Skill Title

## Quick Start
[Minimal example to get started immediately]

## Core Instructions
[Step-by-step guidance for the main workflow]

## Reference Files
[Links to additional documentation if needed]
**Detailed guide**: See [REFERENCE.md](REFERENCE.md)
**Examples**: See [EXAMPLES.md](EXAMPLES.md)

## Utility Scripts
[Documentation for bundled scripts]

## Common Patterns
[Examples of expected inputs/outputs]
```

### Token Budget

- **Target**: Under 500 lines for SKILL.md body
- **If exceeding**: Split content into separate reference files
- **Rationale**: Once loaded, every token competes with conversation history

### Writing Style

**Use imperative/infinitive form:**
```
✓ "Extract text using pdfplumber"
✓ "Run the validation script"
✓ "Create the output file"

✗ "You should extract text..."
✗ "The user will want to..."
```

**Assume Claude is smart:**
```
# Good: Concise (assumes knowledge)
## Extract PDF text
Use pdfplumber for text extraction:
```python
import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

# Bad: Over-explained
## Extract PDF text
PDF (Portable Document Format) files are a common file format that
contains text, images, and other content. To extract text from a PDF,
you'll need to use a library. There are many libraries available...
```

---

## Progressive Disclosure Pattern

Don't put everything in SKILL.md. Use separate files that Claude loads only when needed.

### Directory Structure

```
my-skill/
├── SKILL.md              # Main instructions (loaded when triggered)
├── REFERENCE.md          # Detailed documentation (loaded as needed)
├── EXAMPLES.md           # Usage examples (loaded as needed)
├── FORMS.md              # Specific feature guide (loaded as needed)
└── scripts/
    ├── analyze.py        # Utility script (executed, not loaded)
    ├── validate.py       # Validation script
    └── process.py        # Processing script
```

### Referencing Pattern in SKILL.md

```markdown
## Advanced Features

**Form filling**: See [FORMS.md](FORMS.md) for complete guide
**API reference**: See [REFERENCE.md](REFERENCE.md) for all methods
**Examples**: See [EXAMPLES.md](EXAMPLES.md) for common patterns
```

### Critical Rule: One Level Deep

Claude may partially read deeply nested references. Keep all references directly from SKILL.md.

```
✗ Bad: Nested references
SKILL.md → advanced.md → details.md → actual_info.md

✓ Good: Flat references
SKILL.md → advanced.md
SKILL.md → details.md
SKILL.md → actual_info.md
```

### Table of Contents for Long Files

For reference files over 100 lines, add a TOC so Claude can see scope even with partial reads:

```markdown
# API Reference

## Contents
- Authentication and setup
- Core methods (create, read, update, delete)
- Advanced features (batch operations, webhooks)
- Error handling patterns
- Code examples

## Authentication and setup
...
```

---

## Workflows and Feedback Loops

### Workflow Pattern

For multi-step processes, provide a checklist Claude can track:

```markdown
## Document Processing Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Analyze input file
- [ ] Step 2: Extract content
- [ ] Step 3: Validate extraction
- [ ] Step 4: Transform content
- [ ] Step 5: Generate output
- [ ] Step 6: Verify output
```

**Step 1: Analyze input file**
Run: `python scripts/analyze.py input.pdf`
...
```

### Feedback Loop Pattern

For quality-critical operations, build in validation:

```markdown
## Editing Process

1. Make edits to the document
2. **Validate immediately**: `python scripts/validate.py output/`
3. If validation fails:
   - Review the error message
   - Fix the issues
   - Run validation again
4. **Only proceed when validation passes**
5. Finalize output
```

---

## Utility Scripts

### When to Include Scripts

- **Deterministic operations** that must be exact every time
- **Complex validations** that catch errors early
- **Token-efficient operations** (script output vs generated code)

### Script Documentation Pattern

```markdown
## Utility Scripts

**analyze_form.py**: Extract all form fields from PDF
```bash
python scripts/analyze_form.py input.pdf > fields.json
```

Output format:
```json
{
  "field_name": {"type": "text", "x": 100, "y": 200}
}
```

**validate.py**: Check for errors before processing
```bash
python scripts/validate.py fields.json
# Returns: "OK" or lists specific errors
```
```

### Execute vs Read

Make intent explicit:
- **Execute**: "Run `analyze.py` to extract fields"
- **Read as reference**: "See `analyze.py` for the extraction algorithm"

### Error Handling in Scripts

Scripts should solve problems, not punt to Claude:

```python
# Good: Handles errors explicitly
def process_file(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        print(f"File {path} not found, creating default")
        with open(path, 'w') as f:
            f.write('')
        return ''

# Bad: Punts to Claude
def process_file(path):
    return open(path).read()  # Just fails
```

---

## Degrees of Freedom

Match specificity to task fragility.

### High Freedom (Guidelines)

Use when multiple approaches are valid:

```markdown
## Code Review Process

1. Analyze code structure and organization
2. Check for potential bugs or edge cases
3. Suggest improvements for readability
4. Verify adherence to project conventions
```

### Medium Freedom (Templates with Parameters)

Use when a pattern exists but adaptation is needed:

```markdown
## Generate Report

Use this template and customize as needed:

```python
def generate_report(data, format="markdown", include_charts=True):
    # Process data
    # Generate output in specified format
```
```

### Low Freedom (Exact Scripts)

Use when operations are fragile or consistency is critical:

```markdown
## Database Migration

Run exactly this script:

```bash
python scripts/migrate.py --verify --backup
```

Do not modify the command or add additional flags.
```

---

## Optional Frontmatter: Tool Restrictions

Limit which tools Claude can use when a skill is active:

```yaml
---
name: safe-file-reading
description: Read files without making changes. Use for read-only file access.
allowed-tools:
  - Read
  - Grep
  - Glob
---
```

When active, Claude can only use specified tools without asking permission.

**Use cases:**
- Security-sensitive workflows
- Read-only analysis tasks
- Preventing accidental modifications

---

## Content Guidelines

### Avoid Time-Sensitive Information

```markdown
# Bad: Will become wrong
If you're doing this before August 2025, use the old API.

# Good: Use "old patterns" section
## Current Method
Use the v2 API endpoint.

## Old Patterns
<details>
<summary>Legacy v1 API (deprecated 2025-08)</summary>
The v1 API used different endpoints...
</details>
```

### Consistent Terminology

Pick one term and use it throughout:

```
✓ Consistent: Always "API endpoint", always "field", always "extract"
✗ Inconsistent: Mix of "endpoint/URL/route", "field/box/element", "extract/pull/get"
```

### Provide Concrete Examples

```markdown
## Commit Message Format

**Example 1:**
Input: Added user authentication with JWT tokens
Output:
```
feat(auth): implement JWT-based authentication

Add login endpoint and token validation middleware
```

**Example 2:**
Input: Fixed bug where dates displayed incorrectly
Output:
```
fix(reports): correct date formatting in timezone conversion
```
```

---

## MCP Tool References

If your skill uses MCP tools, always use fully qualified names:

```markdown
Use the BigQuery:bigquery_schema tool to retrieve table schemas.
Use the GitHub:create_issue tool to create issues.
```

Format: `ServerName:tool_name`

---

## Complete SKILL.md Template

```yaml
---
name: your-skill-name
description: >
  [Primary capability 1], [capability 2], and [capability 3].
  Use when [trigger condition 1], [trigger condition 2], or when the user
  mentions [keyword 1], [keyword 2], or [keyword 3].
---

# Skill Title

## Quick Start

[Minimal working example - 5 lines or less]

```python
# Example code
```

## Core Workflow

1. **Step 1**: [Action]
   ```bash
   command here
   ```

2. **Step 2**: [Action]

3. **Step 3**: [Action]

## Reference Files

- **Detailed guide**: See [REFERENCE.md](REFERENCE.md)
- **Examples**: See [EXAMPLES.md](EXAMPLES.md)
- **API docs**: See [API.md](API.md)

## Utility Scripts

**script_name.py**: [What it does]
```bash
python scripts/script_name.py input output
```

## Common Patterns

### Pattern 1: [Name]
[Input/output example]

### Pattern 2: [Name]
[Input/output example]

## Validation

Always validate before finalizing:
```bash
python scripts/validate.py output/
```

If validation fails, review errors and retry.
```

---

## Checklist Before Publishing

### Metadata Quality
- [ ] Name uses gerund form (verb-ing)
- [ ] Name is lowercase with hyphens only
- [ ] Description states what AND when
- [ ] Description uses third person
- [ ] Description includes trigger keywords
- [ ] Description under 1024 characters

### Body Quality
- [ ] SKILL.md under 500 lines
- [ ] Uses imperative/infinitive form
- [ ] No over-explanation of concepts Claude knows
- [ ] Reference files are one level deep
- [ ] Long reference files have TOC
- [ ] Consistent terminology throughout

### Workflows
- [ ] Multi-step processes have checklists
- [ ] Critical operations have validation loops
- [ ] Scripts handle errors explicitly
- [ ] Execute vs read intent is clear

### Testing
- [ ] Tested with target models (Haiku/Sonnet/Opus)
- [ ] Tested with real usage scenarios
- [ ] Skill triggers when expected
- [ ] Instructions are followed correctly

---

## Summary: The Description is Everything

If you remember one thing: **the description determines whether your skill ever gets used**.

Claude sees descriptions of 100+ skills and must decide which to load. Your description must:

1. Clearly state capabilities (what)
2. Specify trigger conditions (when)
3. Include keywords users might say
4. Use third person consistently
5. Be specific, not vague

Everything else in the skill only matters if Claude decides to load it based on the description.