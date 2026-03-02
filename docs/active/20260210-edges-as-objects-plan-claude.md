---
status: Planning
date: 2026-02-10
branch: feature/edges-as-objects
related-adrs:
  - 002-sqlite-core-memory-layer
  - 009-schema-migration-and-data-durability
  - 011-primitive-semantics-and-knowledge-gardening
  - 012-object-versioning-and-backup
  - 013-web-ui-write-operations
  - 014-inline-content-references
generates-adr: 015-edges-as-objects
---

# Edges as Objects: Promoting Links to First-Class Knowledge Entities

## Summary

Promote ExoBrain's links (the only non-object primitive) to full objects of type "Edge." Each edge becomes a UUID-identified, titled, tagged, versioned, searchable, projectable knowledge entity. A lightweight `edge_endpoints` table preserves the from/to/relationship structure for efficient graph queries. During migration, an AI agent enriches each existing link by reading the connected objects and generating contextual content for the new edge object.

## Agent Quick Start

**Files to load first:**
- `engine/src/core/schema.py` — current links table, migrations, FTS5 triggers, versioning triggers
- `engine/src/core/repository.py:821-915` — LinkRepo class (7 methods to refactor)
- `engine/src/core/bootstrap.py:69-78` — RELATIONSHIP_VOCABULARY and inverse lookup
- `engine/src/core/models.py:49-56` — ExoLink data model
- `engine/src/cli/main.py:904-986` — CLI link commands (create, list, remove)
- `engine/src/api/templates/objects/detail.html:130-177` — web UI link display
- `engine/src/api/routes/ui_api.py` — API stats using LinkRepo
- `engine/tests/test_repository.py:464-508,1252-1391` — link tests (9 tests, 5 classes)
- `engine/tests/conftest.py` — test fixtures with sample links

**ADRs to read:**
- [ADR-002](../adr/002-sqlite-core-memory-layer.md) — SQLite core; everything-is-an-object philosophy
- [ADR-009](../adr/009-schema-migration-and-data-durability.md) — Forward-only migrations; init safe on any state
- [ADR-011](../adr/011-primitive-semantics-and-knowledge-gardening.md) — Primitive semantics; links = "how things relate"
- [ADR-012](../adr/012-object-versioning-and-backup.md) — Versioning triggers; soft delete; backup

**Skills:** `exobrain` (CLI interface for testing)

**Explore:** How types and spaces bootstrap themselves as self-referential objects in `bootstrap.py`. The Edge type will follow the same pattern.

## Problem Statement

**User persona:** Brian (knowledge worker) + AI gardening agents that consume and enrich the knowledge base.

**Pain point:** Links are the sole exception to ExoBrain's "everything is an object" philosophy. They live in a separate `links` table with integer primary keys while every other primitive (types, spaces, tags-as-objects) lives in the `objects` table with UUIDs. This means links lack:

| Capability | Objects have it | Links have it |
|---|---|---|
| UUID identity | Yes | No (integer PK) |
| Title / Summary / Content | Yes | Only `context` field |
| Tags | Yes | No |
| FTS5 full-text search | Yes | No |
| Version history | Yes | No |
| Soft delete + recovery | Yes | No (hard delete only) |
| Projection to disk | Yes | No |
| Web UI browsing | Yes | Inline only |
| Spaces | Yes | No |
| Inline references `[[uuid]]` | Yes | No |

**Current state:** The `links` table has: `id INTEGER`, `from_id TEXT`, `to_id TEXT`, `relationship TEXT`, `source TEXT`, `confidence REAL`, `context TEXT`, `created_at TEXT`. Links are created via `exobrain link create`, displayed inline in object detail views, and removed by integer ID.

**Why this matters now:** ExoBrain is an AI-native knowledge system. Research into bleeding-edge AI memory systems (CORE, Graphiti/Zep, HyperGraphRAG) reveals a convergent trend: systems designed for AI consumption are moving toward richer edge representations because AI agents can consume and reason over relationship metadata that would overwhelm human users. Relationships carry knowledge (e.g., "Brian is a board member at CIHS" has temporal, role, and contextual dimensions that belong to the relationship, not to either endpoint). Making edges objects allows AI gardening agents to tag, version, search, and enrich relationships using the same pipeline they use for content objects.

**Business impact:** Completes the "everything is an object" vision (ADR-002). Enables AI agents to garden relationships with the same tools they use for content. Positions ExoBrain ahead of the AI memory curve; no existing system treats relationships with full object richness.

## Success Metrics

| Metric | Baseline | Target | Measurement |
|---|---|---|---|
| Primitives that are objects | 3 of 4 (types, spaces, tags) | 4 of 4 | Schema inspection |
| Edge-specific features | context field only | title, summary, content, tags, versioning, FTS5, projection | Feature checklist |
| Existing links migrated | 0 edge objects | 100% of existing links | Migration script output |
| Enriched edges (have content beyond bare relationship) | 0 | >50% of migrated edges | Query: edges where content IS NOT NULL |
| All existing tests pass | 308 passing | 308+ passing | `pytest tests/ -v` |
| CLI backwards-compatible | N/A | `exobrain link create/list/remove` still works | Manual + agentic test |

## Feature Overview

Promote links to objects of type "Edge." Each edge is a regular object in the `objects` table with a type_id pointing to the Edge bootstrap type. A lightweight `edge_endpoints` junction table stores the directional relationship (from_id, to_id, relationship) for efficient graph queries. All object features (versioning, soft delete, FTS5, tags, projection) automatically apply to edges through existing triggers and infrastructure.

### Core Flow

1. User runs `exobrain link create FROM_ID TO_ID references --context "Cites the methodology"`
2. System creates a new object of type "Edge" with auto-generated title (e.g., "references: Object A -> Object B"), the context as content, and metadata fields
3. System inserts a row in `edge_endpoints` linking the edge object to its from/to targets
4. Edge object automatically gets: UUID, versioning, FTS5 indexing, soft delete support
5. User can now: tag the edge, update its content, search for it, view its version history, see it in projections
6. AI gardening agents can discover, enrich, and maintain edges using the same tools they use for all objects

## Scope

### In scope
- New Edge bootstrap type in `primitives/` space
- New `edge_endpoints` table with FK to objects
- Migration of all existing `links` rows to edge objects
- AI-assisted enrichment during migration (read linked objects, generate richer content)
- Refactored `LinkRepo` (or new `EdgeRepo`) operating on objects + edge_endpoints
- Updated CLI commands (`link create`, `link list`, `link remove` maintain interface)
- Updated web UI detail page for edge display
- Updated web UI to allow browsing edges as objects
- Updated API stats
- Updated tests
- Projection of edge objects to disk
- Backup before migration

### Out of scope (do not build)
- Edges linking to other edges (meta-relationships); future consideration
- Vector embeddings on edge objects; separate initiative
- Automatic edge discovery via content similarity; separate initiative (A-MEM pattern)
- Contradiction detection between edges; future consideration
- Bi-temporal model (valid_at/invalid_at); future consideration inspired by Graphiti/Zep
- Changes to the inline reference syntax `[[uuid|text]]`
- Changes to GraphRAG integration (ADR-001)

### Dependencies
- ADR-009 migration framework must support the new migration
- Bootstrap system must handle Edge type creation
- Existing versioning triggers must fire for edge objects (they will; they apply to all objects)

## User Stories + Acceptance Criteria

### US-1: Create an edge with rich content
**As a** knowledge worker, **I want to** create an edge between two objects with a title, content, and tags, **so that** the relationship itself becomes a searchable knowledge artifact.

**Given** two existing objects A and B
**When** I run `exobrain link create A B references --context "Cites the methodology from the 2024 paper"`
**Then** a new object of type Edge is created with a UUID, the context as content, an auto-generated title, and a row in edge_endpoints

### US-2: Search for edges
**As a** knowledge worker, **I want to** search edge content via FTS5, **so that** I can find relationships by their contextual descriptions.

**Given** edges with content describing relationships
**When** I run `exobrain search "methodology"`
**Then** edge objects appear in search results alongside regular objects

### US-3: Tag and enrich edges
**As an** AI gardening agent, **I want to** add tags to edges and update their content, **so that** relationships are classified and enriched over time.

**Given** an existing edge object
**When** I run `exobrain tag add EDGE_ID "auto-generated"` and `exobrain update EDGE_ID --content "Detailed explanation..."`
**Then** the edge is tagged and its content is updated, with version history tracked

### US-4: View edge version history
**As a** knowledge worker, **I want to** see how an edge's description has evolved, **so that** I can understand how my understanding of a relationship has changed.

**Given** an edge object that has been updated multiple times
**When** I run `exobrain history EDGE_ID`
**Then** I see the version history of the edge, including changes to content and metadata

### US-5: Soft delete and recover edges
**As a** knowledge worker, **I want to** soft-delete an edge and recover it later, **so that** removing a relationship is reversible.

**Given** an existing edge object
**When** I run `exobrain delete EDGE_ID`
**Then** the edge is soft-deleted (deleted_at set) and recoverable via `exobrain undelete EDGE_ID`

### US-6: Browse edges in web UI
**As a** knowledge worker, **I want to** see edges displayed in the web UI with their full content, **so that** I can browse relationship knowledge alongside content objects.

**Given** edge objects exist in the database
**When** I visit the object browser and filter by type "Edge"
**Then** edges are listed with titles, and clicking one shows the full edge detail including from/to endpoints, relationship type, content, tags, and version info

### US-7: Migrate existing links
**As a** system administrator, **I want** existing links automatically migrated to edge objects during the upgrade, **so that** no relationship data is lost.

**Given** an existing ExoBrain database with links in the old `links` table
**When** I run `exobrain init` (or a dedicated migration)
**Then** all existing links are converted to edge objects with AI-generated enrichment, and the old `links` table is preserved as backup

## Key Decisions

| Decision | Choice | Alternatives Considered | Rationale |
|---|---|---|---|
| Edge endpoint storage | Separate `edge_endpoints` table | Columns on objects table; JSON in content | Keeps objects table clean; explicit FK constraints; efficient graph queries via dedicated indexes |
| Type name | "Edge" | "Relationship", "Link" | Graph theory term; neutral; used by Graphiti/CORE; avoids overloading "link" (which also means HTML links, inline references) |
| Migration strategy | Backup + migrate all at once | Parallel tables with gradual migration | Single ExoBrain instance; no need for zero-downtime. Backup provides safety net. Simpler implementation. |
| Migration enrichment | AI reads linked objects and generates content | Migrate context field as-is | AI-native system should use AI during migration. Linked object content provides rich context for generating meaningful edge descriptions. |
| Projection | Project all edges by default | Opt-in only; separate directory | Aligns with "everything is an object" philosophy. AI agents consume projected files. Edges are knowledge. |
| Uniqueness constraint | Business rule in EdgeRepo | DB constraint on edge_endpoints | UNIQUE(from_id, to_id, relationship) moves to edge_endpoints table; EdgeRepo enforces it with check-before-insert |

### Decision Detail: Separate Endpoints Table

The `edge_endpoints` table design:

```sql
CREATE TABLE IF NOT EXISTS edge_endpoints (
    edge_id TEXT PRIMARY KEY REFERENCES objects(id) ON DELETE CASCADE,
    from_id TEXT NOT NULL REFERENCES objects(id),
    to_id TEXT NOT NULL REFERENCES objects(id),
    relationship TEXT NOT NULL,
    UNIQUE(from_id, to_id, relationship)
);

CREATE INDEX idx_edge_endpoints_from ON edge_endpoints(from_id);
CREATE INDEX idx_edge_endpoints_to ON edge_endpoints(to_id);
CREATE INDEX idx_edge_endpoints_relationship ON edge_endpoints(relationship);
```

Query pattern for outgoing edges:

```sql
SELECT o.*, ee.from_id, ee.to_id, ee.relationship, target.title as to_title
FROM objects o
JOIN edge_endpoints ee ON o.id = ee.edge_id
JOIN objects target ON ee.to_id = target.id
WHERE ee.from_id = ? AND o.deleted_at IS NULL
ORDER BY o.created_at;
```

### Decision Detail: Why Edges as Objects (Research-Backed)

The conventional wisdom ("edges are just edges") comes from human-browsed systems. Research into AI-native memory systems reveals a convergent trend toward richer edges:

| System | Edge Richness | Production Status |
|---|---|---|
| A-MEM (NeurIPS 2025) | Bare pointers | Research |
| Mem0 ($24M Series A) | Typed labels + semantic search | Production |
| GraphRAG (Microsoft) | NL descriptions + weight + provenance | Production |
| Graphiti/Zep (YC) | Fact text + embedding + bi-temporal + custom properties | Production |
| CORE (getcore.me) | Full reification: facts as first-class nodes | Early production |
| **ExoBrain (this plan)** | Full objects: type, tags, space, content, versioning, FTS5, projection | Planned |

CORE explicitly adopted "facts as first-class nodes" and reports the 3x node overhead is "non-negotiable" for temporal knowledge. Graphiti/Zep stores bi-temporal metadata, vector embeddings, and custom typed properties on every edge. The ICLR 2026 MemAgents Workshop (April, Rio) focuses on this space, and the Dec 2025 "Memory in the Age of AI Agents" survey identifies edge enrichment as underexplored.

ExoBrain promoting edges to full objects would be genuinely novel; no existing system gives relationships their own tags, version history, spaces, and AI-gardened content pipeline.

## Technical Approach

### Schema Changes (New Migration)

**Migration N (forward-only per ADR-009):**

1. Bootstrap Edge type object (follows existing pattern for Type, Space, etc.)
2. Create `edge_endpoints` table
3. Migrate existing `links` rows:
   a. For each link: create an object of type Edge
   b. Set title = auto-generated from relationship + endpoint titles
   c. Set content = existing `context` field (if any)
   d. Set source = link's `source` field
   e. Insert edge_endpoints row
   f. Preserve created_at from original link
4. Rename `links` table to `links_legacy` (safety backup)
5. Drop old link indexes

**AI enrichment runs as a separate post-migration step** (not in the SQL migration itself):
- For each edge with minimal content, read from_object.content and to_object.content
- LLM generates: title, summary, and enriched content describing the relationship
- Update the edge object with enriched fields
- Tag auto-enriched edges with `ai-enriched` for transparency

### Repository Changes

**New `EdgeRepo` class** (replaces `LinkRepo`):
- `create(from_id, to_id, relationship, title=None, content=None, source='human', confidence=1.0, tags=None)` — creates Edge object + edge_endpoints row
- `get(edge_id: str)` — returns Edge object with endpoint info
- `delete(edge_id: str)` — soft-deletes the Edge object (not hard delete)
- `hard_delete(edge_id: str)` — permanent removal
- `list_from(object_id: str)` — outgoing edges
- `list_to(object_id: str)` — incoming edges
- `list_all_for(object_id: str)` — both directions with inverse relationship logic
- `count()` — total active edges

**Backwards compatibility:** The `confidence` and `source` fields currently on links need a home. Options:
- `confidence` → stored in edge object metadata (JSON field or dedicated column on edge_endpoints)
- `source` → already exists on the objects table

### CLI Changes

Minimal interface changes; the `link` subcommand continues to work:
- `exobrain link create FROM TO REL [--context] [--title] [--tag] [--json]` — now creates an Edge object
- `exobrain link list ID [--json]` — queries edge_endpoints + objects
- `exobrain link remove EDGE_UUID [--json]` — soft-deletes the Edge object
- New: `exobrain link remove` accepts UUID (not integer ID)

### Web UI Changes

- Object detail page: edge section queries edge_endpoints instead of links table
- Edge objects appear in object browser (filterable by type "Edge")
- Edge detail page: shows from/to endpoints, relationship, full content, tags, history
- Stats dashboard: edge count from `ObjectRepo` filtered by type

### Projection Changes

- Edge objects project like any other object
- Frontmatter includes: id, type (Edge), space, title, summary, tags, relationship, from_id, to_id
- Content body contains the edge's description/context
- Projected into the space of the edge object (defaults to TBD; possibly `primitives/edge` or the space of the from_object)

### Bootstrap Changes

Add to `bootstrap.py`:
- Edge type object (deterministic UUID: `00000000-0000-7000-8000-00000000000a` or next available)
- Edge space: `primitives/edge` (for the type object itself; edge instances go in their from_object's space or a configurable default)

## Implementation Phases

### Phase 1: Schema + Bootstrap + Migration (Core)
1. Create database backup
2. Add Edge type to bootstrap
3. Write migration: create `edge_endpoints` table
4. Write migration logic: convert `links` rows to Edge objects + edge_endpoints rows
5. Rename `links` to `links_legacy`
6. Update `EdgeRepo` (or refactor `LinkRepo`)
7. Update all repository callers
8. Update tests
9. Run full test suite

### Phase 2: CLI + Web UI Updates
1. Update CLI link commands to use EdgeRepo
2. Update web UI detail page
3. Add Edge type to object browser filters
4. Update API stats endpoints
5. Update agentic test (`/test-system`)

### Phase 3: AI-Assisted Migration Enrichment
1. Write enrichment script: for each edge with minimal content, read linked objects
2. Use LLM to generate title, summary, enriched content
3. Tag enriched edges with `ai-enriched`
4. Run enrichment on the live database
5. Verify enrichment quality (spot-check sample)

### Phase 4: Projection + Gardening
1. Ensure edge objects project correctly (frontmatter includes relationship metadata)
2. Test bidirectional sync for edge objects
3. Document edge gardening patterns for AI agents

## Open Questions

| Question | Impact | Notes |
|---|---|---|
| What space should edge objects live in? | Medium | Options: `primitives/edge`, same space as from_object, or a new `edges/` space. Affects browsing and projection paths. |
| How to handle `confidence` field? | Low | Currently on links table. Could go on edge_endpoints or as a tag/metadata on the edge object. |
| Should inverse relationships create two edge objects or one? | High | Currently one link serves both directions via `get_inverse_relationship()`. With edges as objects, could create one edge and compute inverse at query time (current pattern) or create paired edges. |
| What title format for auto-generated edge titles? | Low | Options: "references: Title A -> Title B", "A references B", just the relationship type. |
| Should `exobrain link remove` hard-delete or soft-delete? | Medium | Soft-delete is the new default for objects. But old behavior was hard-delete. Recommend soft-delete with `--hard` flag. |
| How does tombstone purge interact with edge objects? | Medium | Currently purge preserves links (ADR-012). With edges as objects, purging a content object should preserve its edge objects but mark them as connecting to a purged entity. |

## Future Considerations

Items discussed but explicitly deferred:

- **Edges linking to other edges (meta-relationships):** The schema supports this naturally since edges are objects, but the UI and CLI don't need to handle it yet.
- **Bi-temporal model (valid_at/invalid_at):** Inspired by Graphiti/Zep. Would enable "what did I know at time T?" queries. Could be added to edge_endpoints later.
- **Vector embeddings on edges:** Embed edge content for semantic relationship search. Part of the broader embeddings initiative.
- **Automatic edge discovery via content similarity:** A-MEM pattern; when a new object is captured, compute similarity and suggest edges. Separate feature.
- **Contradiction detection:** When new edges conflict with existing ones, flag for review. Inspired by Graphiti and CORE.
- **Custom edge type properties:** Graphiti supports typed edge properties (employment edge has start_date, salary). Could be added as structured metadata.
- **Competitive landscape context:** This plan was informed by deep research into GraphRAG, Graphiti/Zep, CORE, Mem0, A-MEM, MemGPT/Letta, and Cognee. ExoBrain's approach is unique; no existing system treats relationships as full knowledge objects with tags, versioning, and AI-gardened content. A full competitive analysis is available in the conversation that produced this plan.

## Verification

### Automated
```bash
# Unit tests
docker compose exec exobrain python -m pytest tests/ -v

# Specific edge tests
docker compose exec exobrain python -m pytest tests/test_repository.py -v -k "edge or link"

# Agentic integration test
# Run /test-system command
```

### Manual Checks
1. `exobrain link create` creates an Edge object with UUID
2. `exobrain link list ID` shows edges with full detail
3. `exobrain get EDGE_UUID` shows the edge as a regular object with endpoint info
4. `exobrain search "CONTEXT_TEXT"` finds edges by their content
5. `exobrain tag add EDGE_UUID "important"` works
6. `exobrain history EDGE_UUID` shows version history
7. `exobrain delete EDGE_UUID` soft-deletes; `exobrain undelete EDGE_UUID` recovers
8. Web UI object browser shows edges when filtered by type
9. Projected files include edge objects with correct frontmatter
10. AI enrichment script generates meaningful content for edges

### Success Criteria
- All 308+ existing tests pass
- All existing links migrated to edge objects
- CLI interface backwards-compatible (same commands work)
- Edge objects appear in search, browser, projections
- At least 50% of migrated edges have AI-enriched content

## References

- **Related plans:** None directly; [web-ui-explorer](20260210-web-ui-explorer-pages-plan-claude.md) will benefit from edge browsing
- **ADR to generate:** ADR-015 (Edges as Objects) should be created to document this architectural decision
- **Research sources:** A-MEM (NeurIPS 2025), Microsoft GraphRAG, Graphiti/Zep (arXiv 2501.13956), CORE (getcore.me), Mem0, HyperGraphRAG (NeurIPS 2025), MemGPT/Letta, Cognee, ICLR 2026 MemAgents Workshop, metagraph practitioner research (Pavlyshyn 2024-2025)
- **Key external finding:** CORE (10M+ node production system) adopted full reification ("facts as first-class nodes") and reports 3x node overhead as "non-negotiable" for AI-consumed temporal knowledge
