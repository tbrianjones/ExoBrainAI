# ADR-014: Inline Content References

- **Status:** Accepted
- **Date:** 2026-02-10
- **Impact:** Medium
- **Related ADRs:** ADR-002 (SQLite Core Memory Layer), ADR-010 (Web UI Architecture), ADR-011 (Primitive Semantics)

## Context and Problem Statement

ExoBrain has "hard links" (explicit relationship records in the `links` table with named relationship types like `derived-from` and `references`) but no standard for embedding references to other objects *within markdown content*. Every major knowledge system (MediaWiki, Obsidian, Roam, Logseq, Org-mode) has converged on `[[...]]` as the convention for internal references. ExoBrain needs an equivalent that works with its UUID-based object model.

The central question: what syntax should ExoBrain use for inline content references, and how should they be rendered?

## Decision Drivers

- UUIDs are stable identifiers that survive renames; title-based references would break when objects are retitled
- Display text is essential for human readability; a bare UUID in prose is unreadable
- The web UI (ADR-010) already renders markdown to HTML; inline references should integrate with that pipeline
- Projected files (ADR-007) are plain markdown; raw `[[...]]` syntax should be preserved in projections for portability
- Hard links (structural relationships in the `links` table) and inline references (contextual, embedded in prose) serve different purposes and should coexist

## Decision

### Syntax: `[[uuid|display text]]`

Inline content references use the following syntax:

```
[[<uuid>|<display text>]]
```

Where:
- `<uuid>` is a 36-character hyphenated UUID (e.g., `069abc12-3456-7890-abcd-ef1234567890`)
- `|` separates the UUID from the display text
- `<display text>` is mandatory human-readable text (typically the object's title at time of writing)

Example in prose:

```markdown
This builds on the framework described in [[069abc12-3456-7890-abcd-ef1234567890|Dynamic Skill Architecture Plan]],
which established the pattern for skill composition.
```

### Regex Pattern

```
\[\[([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\|([^\]]+)\]\]
```

This pattern:
- Matches exactly 36-character hyphenated UUIDs (lowercase hex)
- Requires display text (one or more characters that are not `]`)
- Avoids false positives on standard markdown link syntax

### Rendering: Web UI Only

The web UI's `_render_markdown()` function converts wiki-links to clickable HTML links:

```
[[uuid|display text]]  →  <a href="/ui/objects/uuid">display text</a>
```

Implementation: a post-sanitization regex substitution in `_render_markdown()`. The replacement runs after nh3 sanitization to avoid conflicts with the `url_schemes` restriction on relative URLs. The UUID is validated by the regex pattern (only hex characters and hyphens), and the display text is HTML-escaped before insertion.

Projected files retain the raw `[[uuid|display text]]` syntax. No transformation is applied during projection or sync.

### Relationship to Hard Links

| Aspect | Hard Links (`links` table) | Inline Content References |
|--------|---------------------------|--------------------------|
| Storage | Dedicated table with `from_id`, `to_id`, `relationship` | Embedded in object content text |
| Purpose | Structural; named relationship types (`derived-from`, `references`, `related-to`) | Contextual; reference appears in prose where it's relevant |
| Semantics | Explicit relationship type chosen by the author | Implicit "mentions" relationship |
| Visibility | Shown in object detail sidebar | Rendered as clickable links in content body |
| Coexistence | Both can reference the same target object | Both can reference the same target object |

Authors should use both: hard links for structural provenance (e.g., a view is `derived-from` a transcript) and inline references for contextual mentions within content.

### Stale Display Text Policy

Display text captures the author's intent at write time and is not automatically updated when the referenced object's title changes. This is intentional:

- The display text may differ from the title for contextual reasons (e.g., "the architecture plan" instead of "ADR-014: Inline Content References")
- Automatic updates would require scanning all object content on every title change
- The UUID ensures the link target is always correct regardless of display text

### Future: Content Reference Indexing

A dedicated `content_references` table for indexing which objects reference which other objects is deferred to a future ADR. The current implementation renders references at display time without maintaining an index.

## Alternatives Considered

### Title-Based References (`[[Object Title]]`)

- **Pro:** Simpler syntax; no UUID needed
- **Con:** Breaks on rename; ambiguous when multiple objects share similar titles; requires title resolution logic
- **Verdict:** Rejected. UUID-based references are stable and unambiguous.

### Bare UUID References (`[[uuid]]`)

- **Pro:** Simpler; no display text to maintain
- **Con:** Unreadable in raw text; requires title lookup at render time (introduces DB dependency in the rendering pipeline)
- **Verdict:** Rejected. Display text is essential for readability in raw markdown and projected files.

### Markdown Link Syntax (`[text](/ui/objects/uuid)`)

- **Pro:** Standard markdown; no custom parsing needed
- **Con:** Couples content to the web UI URL scheme; breaks if the URL structure changes; not recognizable as an internal reference
- **Verdict:** Rejected. A distinct syntax makes internal references identifiable and URL-scheme-independent.

### Pre-Sanitization Replacement (Convert to Markdown Links Before nh3)

- **Pro:** Leverages the markdown library's link rendering
- **Con:** nh3's `url_schemes` restriction strips relative URLs like `/ui/objects/uuid`; would require relaxing security config
- **Verdict:** Rejected. Post-sanitization replacement avoids weakening the HTML sanitization policy.

## Consequences

### Positive

- Objects can reference each other contextually within prose, creating a richer knowledge graph
- The syntax is familiar to users of Obsidian, Roam, and other wiki-style tools
- UUID-based references are stable across renames and unambiguous
- No database schema changes required; references live in existing content fields

### Negative

- Display text can become stale if the referenced object is renamed (accepted trade-off)
- No index of content references exists yet; finding "what references this object?" requires full-text search
- Wiki-links inside fenced code blocks will also be converted (documented as a known limitation for MVP)

### Neutral

- Commands and agents that create content should use `[[uuid|title]]` syntax when referencing other ExoBrain objects
- Future work may add a `content_references` table for bidirectional reference tracking

## Agent Rules

- MUST use `[[uuid|display text]]` syntax when embedding references to ExoBrain objects in content
- MUST include display text; bare `[[uuid]]` references are not valid
- MUST use the full 36-character hyphenated UUID; short prefixes are not supported in wiki-link syntax
- SHOULD use the object's current title as display text unless a contextual alternative is more appropriate
- SHOULD create hard links (`link create`) for structural relationships in addition to inline references
- MUST NOT rely on display text being current; always treat the UUID as the authoritative identifier
