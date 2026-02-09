# ADR 011: Primitive Semantics and Knowledge Gardening

- **Status:** Accepted
- **Date:** 2026-02-08
- **Tags:** primitives, semantics, knowledge-gardening, taxonomy, spaces
- **Impact:** High

## Context

ExoBrain's data model provides four primitives for organizing knowledge: spaces, types, tags, and links (ADR-002). After migrating content from the file-based `ideas/` folder into ExoBrain, a philosophical tension surfaced; the primitives lack clear guidance on how they should be used by humans and AI agents.

Specific symptoms:

- "Should ExoBrain belong in `ideas/` or `projects/`?" has no principled answer.
- Spaces are treated as immutable in the projection sync layer (ADR-007), but knowledge organization evolves over time and objects need to move.
- Commands handle space selection inconsistently; `/ideate` hard-codes `ideas/`, `/generate-view` reads from `ideas/{space-name}`, and generic captures default to `inbox`.
- Empty spaces (like `work/exobrain`) have no content describing what belongs there, and nothing flags this as a gap.
- There is no model for AI agents to actively tend the knowledge garden; reviewing, organizing, and enriching information over time.

The information-centric vision (ADR-006) establishes that "humans capture; agents organize." This ADR defines the semantic roles of the four primitives and the gardening model that makes that vision operational.

## Decision Drivers

### Emergent Organization

Users should provide content and intent; AI handles classification, tagging, and space assignment. No fixed taxonomy should be imposed upfront. Categories emerge from use patterns and are refined over time.

### Mutable Geography

Knowledge organization evolves. An object captured as a quick note in `inbox` may later belong in `projects/exobrain` or `ideas/memory-palace`. Spaces must be mutable to reflect this evolution; both via CLI and via projection sync.

### Semantic Clarity

Each primitive must have a clear, non-overlapping role. Without explicit semantics, agents and humans use primitives inconsistently; putting classification information in spaces when it belongs in tags, or using tags as substitutes for links.

### AI Agent Autonomy

AI agents should make obvious organizational decisions autonomously (tagging, linking) while escalating uncertain ones (space assignment, taxonomy changes) to the human. The primitives must support this spectrum of autonomy.

### Future Access Control

Spaces will eventually serve as the unit of access control; some private, some shared, some AI-accessible. The primitive semantics defined here must accommodate that future without schema changes.

## Considered Options

### Option 1: Fixed Taxonomy (Rejected)

Bootstrap a set of top-level categories: `ideas/`, `projects/`, `references/`, `work/`, `personal/`. Require all content to fit these categories.

**Pros:** Clear structure from day one; no ambiguity about where things go.
**Cons:** Assumes the right categories are known upfront. Every user's knowledge organization is different. Creates forced choices that produce miscategorized content.

### Option 2: No Spaces; Tags Only (Rejected)

Eliminate spaces entirely. Use tags for all organization. Objects exist in a flat pool, discoverable only through tagging and search.

**Pros:** Simpler model; no debates about where things live.
**Cons:** Loses geographic locality for projection (ADR-007). Tags lack the hierarchical containment needed for future access control. Browsing a directory of related files becomes impossible.

### Option 3: Emergent Taxonomy with Defined Primitive Roles (Selected)

Define clear semantic roles for each primitive but do not prescribe their values. Spaces grow organically as content accumulates. AI agents propose and refine organization; humans confirm when uncertain.

**Pros:** Adapts to any user's knowledge domain. AI agents have clear rules for which primitive to use. Supports both the current projection model and future access control.
**Cons:** Requires discipline to prevent primitive misuse (using spaces like tags, or tags like links). Early system state may feel unstructured until enough content accumulates to reveal natural categories.

## Decision Outcome

**Define explicit semantic roles for the four ExoBrain primitives (spaces, types, tags, links) and establish an emergent organization model where AI agents propose and maintain structure.**

### 1. Primitive Roles

| Primitive | Semantic Role | Mutability | Typical Decision Maker |
|-----------|--------------|------------|----------------------|
| Spaces | Where something lives; its geographic home | Mutable; objects can move between spaces over time | AI proposes; human confirms when uncertain |
| Types | What something is; its ontological class | Fixed at creation; never changes | AI infers from content and context at capture time |
| Tags | What something is about; semantic facets and classification | Freely added and removed | AI generates; human refines |
| Links | How things relate; structural connections between objects | Freely created and removed | AI discovers relationships; human validates |

**Spaces** provide containment and locality. They answer "where does this live?" and serve as the browsing and projection hierarchy. A space is analogous to a folder or namespace; it groups related objects for navigation, projection, and future access control.

**Types** provide ontological identity. They answer "what is this?" and are permanent. A Note captured during a conversation stays a Note even if it later inspires a Document. Types control behavior (how the system processes an object) and should not be confused with classification (which is what tags do).

**Tags** provide semantic classification. They answer "what is this about?" and are ephemeral. Tags can be added, removed, and refined freely. AI agents should actively tag objects during capture and revisit tags as understanding of the knowledge base evolves.

**Links** provide structural relationships. They answer "how does this connect to other things?" and use the relationship vocabulary defined in `engine/src/core/bootstrap.py` (`RELATIONSHIP_VOCABULARY`: references, derived-from, supersedes, related-to, part-of, broader-than, responds-to, blocks). AI agents should discover and propose links; humans validate.

### 2. Emergent Taxonomy

No fixed top-level categories are prescribed. Spaces grow organically:

- `inbox` remains the universal default for unclassified captures (defined in `engine/src/core/bootstrap.py`).
- AI agents derive space names from workflow context. The `/ideate` command creates `ideas/{topic-name}`; other workflows may create `projects/`, `references/`, or entirely new hierarchies as usage patterns warrant.
- New top-level categories emerge when patterns warrant them. The system does not need to know all categories upfront.
- Space creation remains via CLI: `exobrain space create "path/name"` (ADR-003).

### 3. Space Mutability in Projection Sync

The current implementation in `engine/src/core/projection.py` (`sync_from_file`, lines 559-567) rejects changes to the `space` field in projected files. This constraint will be removed:

- Editing the `space` field in a projected file's YAML frontmatter and running `exobrain sync` will move the object to the specified space.
- The CLI `update --space` path (`engine/src/cli/main.py`, line 496) already supports space movement and remains the canonical mutation path.
- ADR-007 rule #3 ("MUST NOT edit `id` or `space` fields in projected files") will be updated to apply only to `id`. The `space` field becomes mutable in projected files.
- The `id` field remains permanently immutable in all contexts (ADR-006; identity is permanent).

### 4. Space Descriptions

Every space should have a meaningful concept object describing what belongs there. The `idea-readme` pattern from `/instantiate-idea` (`.claude/commands/instantiate-idea.md`, line 41) generalizes to all spaces:

- Each space SHOULD have a concept object tagged `space-readme` that describes the space's purpose, what belongs there, and any conventions.
- Bootstrap spaces in `engine/src/core/bootstrap.py` have minimal descriptions (e.g., "Default space for user captures"). These should be enriched over time.
- Empty or undescribed spaces are quality signals that knowledge gardening agents should surface.

### 5. Knowledge Gardening Model (Vision)

*This documents a planned capability not yet implemented.*

The vision is a living system where AI agents continuously review, organize, and enrich information; making obvious decisions autonomously, asking humans when uncertain, and surfacing tasks for the human to engage with.

**Quality signals agents should detect:**
- Spaces with no `space-readme` concept object (undescribed spaces)
- Objects in `inbox` that have accumulated enough context to be classified into a space
- Tags that overlap semantically (consolidation candidates)
- Sparse idea spaces that need fleshing out
- Objects with no tags or links (under-connected knowledge)
- Stale objects that may need archiving

**Autonomy spectrum:**
- **Autonomous:** Adding tags, creating links between related objects, generating summaries
- **Propose and confirm:** Moving objects between spaces, merging tags, creating new spaces
- **Surface for human:** Archiving or deprecating objects, resolving ambiguous classification, reorganizing space hierarchy

**Surfacing model:** Quality signals surface as tasks or questions for the human; a gamified inbox that engages the human in gardening activities. The system's intelligence enriches itself through this feedback loop.

### 6. Permissions Model (Vision)

*This documents a planned need not yet designed.*

Spaces will eventually serve as the unit of access control:
- Some spaces may be private (personal reflections)
- Some spaces may be shared (collaborative projects)
- Some spaces may restrict AI access (sensitive content)

The primitive semantics defined in this ADR accommodate this future by establishing spaces as the containment and access boundary. No schema changes are needed; permissions would be metadata on space objects.

## Consequences

### Positive

- **Clear guidance for agents.** AI agents now have explicit rules for when to use each primitive, reducing inconsistent classification across commands.
- **Flexible organization.** Users are not forced into predetermined categories. The system adapts to any knowledge domain.
- **Space mobility.** Objects can be reorganized as understanding evolves, both via CLI and via projected file edits.
- **Foundation for gardening.** The primitive roles and quality signals provide a concrete starting point for autonomous knowledge maintenance agents.

### Negative

- **ADR-007 impact.** Rule #3 of ADR-007 must be updated to reflect that `space` is now mutable in projection sync. The `sync_from_file` function in `engine/src/core/projection.py` (lines 559-567) must be modified to allow space changes.
- **Early ambiguity.** Without a fixed taxonomy, new ExoBrain instances may feel unstructured until enough content accumulates to reveal natural categories.
- **Gardening complexity.** The knowledge gardening model requires careful calibration of the autonomy spectrum to avoid agents making unwanted changes or overwhelming the human with questions.

### Neutral

- **No schema changes required.** All decisions in this ADR work within the existing data model (ADR-002). Spaces, types, tags, and links already exist; this ADR defines their semantics, not their implementation.
- **Commands retain domain-specific space handling.** The `/ideate` command continues to use `ideas/` as its space prefix. This is correct; domain-specific commands know their domain. The guidance here applies to general-purpose commands and future agents.

## Pending Items

| Item | Status | Notes |
|------|--------|-------|
| Remove space immutability in `sync_from_file` | Pending | `engine/src/core/projection.py` lines 559-567 |
| Update ADR-007 rule #3 | Pending | Remove `space` from immutable fields list |
| Generalize `idea-readme` tag to `space-readme` | Pending | Convention for all spaces, not just idea spaces |
| Enrich bootstrap space descriptions | Pending | `engine/src/core/bootstrap.py` lines 52-59 |
| Knowledge gardening agent | Pending | Future capability; vision documented in this ADR |

## Agent Rules

1. **MUST** use spaces for geographic containment (where something lives), types for ontological identity (what something is), tags for semantic classification (what something is about), and links for structural relationships (how things connect). Do not conflate these roles. Primitives are defined in `engine/src/core/bootstrap.py` (types, spaces, relationship vocabulary) and managed via `engine/src/core/repository.py` (ObjectRepo, TagRepo, LinkRepo).

2. **MUST** default to `inbox` space when capturing content without a clear space assignment. The `inbox` space is defined in `engine/src/core/bootstrap.py` (line 33) as the universal default. Commands SHOULD infer the appropriate space from context when possible and fall back to `inbox` when uncertain.

3. **MUST NOT** change an object's type after creation. Types are ontologically fixed. There is no `--type` flag on `exobrain update` (`engine/src/cli/main.py`), and this is intentional. If content evolves beyond its type, create a new object of the correct type and link them with `derived-from`.

4. **SHOULD** actively generate tags during capture operations. AI agents SHOULD propose tags based on content analysis. Tag generation guidance is in `.claude/skills/tag-generation.md`. Tags SHOULD include both broad category terms and specific topic terms.

5. **SHOULD** discover and propose links between related objects. When creating or reviewing content, AI agents SHOULD identify relationships using the vocabulary in `engine/src/core/bootstrap.py` (`RELATIONSHIP_VOCABULARY`: references, derived-from, supersedes, related-to, part-of, broader-than, responds-to, blocks).

6. **MUST** treat space assignment as a human-confirmable decision when uncertain. For well-established patterns (e.g., `/ideate` creates under `ideas/`), agents MAY assign spaces autonomously. For novel content where the appropriate space is ambiguous, agents MUST propose a space and ask the human to confirm.

7. **SHOULD** create a concept object tagged `space-readme` when creating a new space. This generalizes the pattern from `/instantiate-idea` (`.claude/commands/instantiate-idea.md`) where each idea space gets a concept object tagged `idea-readme`. All spaces benefit from a description of their purpose and contents.

8. **MUST NOT** impose a fixed top-level taxonomy. New spaces emerge from usage patterns. Do not create empty spaces preemptively; create them when content needs a home. The only exception is `inbox`, which always exists as the bootstrap default.

9. **SHOULD** surface quality signals rather than making autonomous structural changes to spaces or taxonomy. Undescribed spaces, untagged objects, objects lingering in `inbox`, and semantic tag overlaps are signals to bring to the human's attention; not problems to fix silently. See the quality signals list in Section 5 of Decision Outcome.

10. **MUST** use `exobrain update <id> --space <name>` via CLI (`engine/src/cli/main.py`, line 496) or edit the `space` field in a projected file and run `exobrain sync` to move objects between spaces. Both paths are valid. The `id` field remains permanently immutable in all contexts.

## References

- ADR-002: `docs/adr/002-sqlite-core-memory-layer.md` (data model, schema, space hierarchy convention)
- ADR-003: `docs/adr/003-exobrain-cli-architecture.md` (CLI as sole write interface)
- ADR-006: `docs/adr/006-information-centric-computing-vision.md` (information-centric vision; "humans capture, agents organize")
- ADR-007: `docs/adr/007-projection-layer-architecture.md` (projection layer; rule #3 space immutability to be relaxed per this ADR)
