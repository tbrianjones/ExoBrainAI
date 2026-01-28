# ADR 006: Information-Centric Computing Vision for ExoBrain

- **Status:** Accepted
- **Date:** 2026-01-28
- **Tags:** vision, architecture, information-centric
- **Impact:** High

## Context

The dominant computing paradigm for fifty years has been application-centric:

```
Operating System → Applications → Data (siloed per application)
```

Each application owns its data. Your notes live in Apple Notes, your tasks in Things, your bookmarks in Safari, your documents in Google Docs. Every piece of information has a home, and that home is an application. Applications do not share data; they export and import. Moving information between applications requires explicit translation, and relationships between data in different applications are impossible to express.

This model made sense when humans were the primary interface to computers. Applications provided specialized UIs tailored to specific tasks. The cost of data silos was acceptable because humans are slow; we interact with one application at a time, and switching contexts is normal.

AI changes this equation. AI agents do not care about applications; they care about information. When an agent needs to understand your work, it must query five different applications, each with its own API, authentication, data model, and query language. The application-centric model is hostile to AI because every tool is a walled garden. Agents spend more time navigating silos than reasoning about information.

The unfulfilled promise of decades of computing research; Semantic Web, personal knowledge graphs, federated data, linked data; was an information-centric model:

```
Operating System → Information Layer (unified, canonical) → Applications (views into the data)
```

In this model, information exists independently of applications. Applications are interfaces into a shared substrate, not owners of private databases. A note, a task, a bookmark, a document; these are all objects in a universal information layer with stable identities and explicit relationships.

This vision failed repeatedly because humans were still the primary interface. Building and maintaining a unified information layer required more discipline than applications provided. The benefits (cross-application queries, universal relationships) did not justify the costs for human users who were satisfied with copy-paste.

AI makes the information-centric model viable. Agents are the new primary interface. They need unified access, stable identities, and universal relationships. The discipline required to maintain an information layer is exactly what AI agents excel at. Humans capture; agents organize.

ExoBrain is an implementation of this vision for personal knowledge. It is not a note-taking application. It is an information substrate that note-taking applications, AI agents, query interfaces, and future tools we cannot yet imagine all interface with through stable, well-defined contracts.

## Decision Drivers

### Universal Identity

Every piece of information has a stable, globally unique identifier (UUIDv7). This ID never changes. It survives application migrations, format conversions, and technology upgrades. When an agent references an object, that reference remains valid forever. There is no "this bookmark used to be in Pinboard but now it's in Raindrop and the URL changed"; there is an object with a permanent ID that may have been captured via Pinboard originally.

### Universal Relationships

Links between objects are first-class entities, not application-specific metadata. A note can reference a document, which cites a URL, which is tagged with concepts that also appear in tasks. These relationships exist in the information layer, not in any single application's database. Any consumer can traverse them.

### Universal Access

The same data is accessible through multiple interfaces: CLI, API, file projection, SQL query, natural language search. The interface is a view into the data, not a gateway to it. Grep works. SQL works. Claude Code works. A future web UI will work. All see the same objects, the same relationships, the same identities.

### Controlled Mutation

Not every interface can write. The information layer has a single source of truth (SQLite database) with a single controlled write path (CLI). This prevents the corruption that arises when multiple applications each maintain their own version of shared data. Read interfaces are many; write interfaces are few and validated.

### Interface Flexibility

Different consumers need different shapes of the same data. AI agents work best with projected text files they can grep. Humans work best with formatted terminal output. Future UIs will need JSON APIs. GraphRAG needs staged documents with aggregated metadata. The information layer provides projection mechanisms that present data in whatever form consumers need, without duplicating the source of truth.

## Considered Options

This ADR is more vision than alternatives analysis. The alternative is the status quo: continue using application-centric tools, accept data silos, and build ad-hoc integrations when AI agents need access. That approach is rejected not because it fails today, but because it fails to scale to a future where AI agents are the primary computing interface.

The specific implementation choices (SQLite, CLI-first, projection layers) are documented in ADRs 002-005. This ADR frames why those choices serve a larger vision.

## Decision Outcome

**ExoBrain is an information substrate, not a note-taking application.**

The architectural implications:

1. **The data model is sacred.** Objects, types, spaces, tags, links, files. Every piece of information fits this model. New features are expressed as objects and relationships, not new tables or special cases.

2. **Interfaces are adapters.** The CLI, API, file projections, GraphRAG staging; these are adapters between the canonical data model and specific consumers. They can be added, removed, or replaced without changing the information layer.

3. **Identity is permanent.** UUIDv7 IDs are assigned at creation and never change. External systems can build indexes, caches, or references against these IDs with confidence they will remain valid.

4. **Relationships are explicit.** The `links` table captures relationships between objects. These are not hidden in application-specific metadata; they are first-class queryable entities.

5. **Projection is transformation, not duplication.** When files are projected for AI agent consumption, or staged for GraphRAG indexing, these are derived views. The source of truth remains the SQLite database.

### The ExoBrain Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Consumers                               │
│  Claude Code │ Terminal │ Future Web UI │ GraphRAG │ Webhooks  │
└──────────────┬──────────┬───────────────┬──────────┬───────────┘
               │          │               │          │
               ▼          ▼               ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Interface Adapters                           │
│     CLI      │   API    │ File Projection │  MCP Server         │
│  (read/write)│(read-only)│   (read-only)  │   (future)          │
└──────────────┴──────────┴───────────────┴──────────┴───────────┘
               │          │               │          │
               ▼          ▼               ▼          ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Information Substrate                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    SQLite Database                        │  │
│  │  objects │ object_tags │ links │ files │ objects_fts     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    File Storage                           │  │
│  │  files/{shard}/{shard}/{uuid}.{ext}                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**SQLite as source of truth:** Atomic transactions, relational integrity, full-text search. The database is a single file that can be copied, backed up, and versioned. All object metadata, relationships, and searchable content live here.

**CLI as mutation gateway:** All writes flow through validated CLI commands. This ensures data integrity, enforces business rules, and provides a complete audit trail. The CLI is the API for writes; everything else is read-only.

**Projection layer for diverse consumers:** AI agents expect files they can grep. GraphRAG expects staged documents with aggregated metadata. Future UIs expect JSON. Projection adapters transform the canonical data model into whatever form consumers need.

**File storage for binary evidence:** PDFs, images, source documents. These are referenced by objects in the database but stored as files for efficient access. The database tracks metadata; the filesystem holds bytes.

## Consequences

### Positive

- **AI-native architecture.** Any AI agent can query ExoBrain through CLI, API, or file projection. No application-specific integration required. The entire knowledge base is accessible through standard interfaces.

- **Technology independence.** The information layer survives application changes. When a better note-taking UI appears, it connects to ExoBrain; it does not import/export data. When GraphRAG is superseded by a better search technology, only the adapter changes.

- **Universal relationships.** Cross-domain connections that are impossible in application silos become natural. A note references a document references a URL references a concept. All queryable, all traversable.

- **Versioning and federation potential.** Because objects have stable IDs and explicit relationships, the data model supports versioning (track changes over time) and federation (merge knowledge bases) as future capabilities without schema changes.

- **Multiple interface paradigms.** The same data supports CLI workflows, conversational AI, future GUIs, and programmatic access. Users are not locked into a single interaction model.

### Negative

- **More infrastructure than a simple app.** Running ExoBrain requires Docker, understanding the CLI, and maintaining the system. This is more complex than downloading a note-taking app from the App Store.

- **Discipline required.** The information-centric model only works if information is captured into ExoBrain. Returning to application silos for convenience undermines the vision. This requires behavioral change.

- **No off-the-shelf UI.** Until interfaces are built, interaction is CLI-only (via Claude Code). Users accustomed to polished applications may find this limiting.

- **Single-user architecture.** The current design assumes one user, one machine. Multi-user or collaborative scenarios require significant architectural changes.

### Neutral

- **This is a bet on AI.** The information-centric model is valuable primarily because AI agents are becoming the primary computing interface. If that bet is wrong, ExoBrain is over-engineered. If that bet is right, ExoBrain is ahead of the curve.

- **Scope limitation.** ExoBrain manages personal knowledge, not all information. It is not trying to replace databases, file systems, or application-specific data stores. It captures knowledge; information worth remembering and connecting.

## Agent Rules

1. **MUST** route all mutations through the CLI. Never write directly to the SQLite database or file storage, even for convenience or performance. The CLI enforces validation, maintains integrity, and provides audit capability. Bypassing it corrupts the source of truth.

2. **MUST** understand projection sync semantics. Projected markdown files support bidirectional sync: edits to mutable fields (title, summary, content, tags) are synced back to SQLite via the file watcher. However, `id` and `space` are immutable in projections; changing these fields logs an error and the edit is rejected. Staged documents and API responses remain read-only. For complex mutations (moving objects between spaces, deleting), use the CLI.

3. **MUST** preserve ID stability. Object IDs (UUIDv7) are permanent identifiers. Never change an object's ID. Never create a "new version" of an object with a different ID. Updates modify objects in place; they do not create copies.

4. **MUST NOT** require core schema changes for new interface adapters. The data model (objects, types, spaces, tags, links, files) is stable. New interfaces transform this model into their required shapes; they do not extend the schema to accommodate their needs.

5. **SHOULD** express new features as objects and relationships. Before adding a new table or column, consider whether the feature can be expressed using existing primitives. A new "project" concept might be a space. A new "priority" concept might be a tag. A new "blocks" relationship might be a link. The data model is more expressive than it first appears.

6. **SHOULD** prefer projection over duplication. When a consumer needs data in a different form, build a projection adapter that transforms the canonical data. Do not maintain separate copies that can drift from the source of truth.

7. **MUST** document interface contracts. Each adapter (CLI, API, file projection, MCP server) has a contract with its consumers. Document what data is exposed, in what format, with what guarantees. Consumers depend on these contracts; changing them requires coordination.

8. **SHOULD** consider AI agents as first-class consumers. When designing interfaces or projections, ask: "How would an AI agent use this?" Structured output, stable identifiers, greppable formats, and explicit relationships all serve AI consumption.

## References

- ADR 002: `docs/adr/002-sqlite-core-memory-layer.md` (SQLite as source of truth)
- ADR 003: `docs/adr/003-exobrain-cli-architecture.md` (CLI as mutation gateway)
- ADR 004: `docs/adr/004-claude-code-first-ui.md` (AI agent as primary consumer)
- ADR 005: `docs/adr/005-api-layer-deferred.md` (Interface adapters added as needed)
- Semantic Web: https://www.w3.org/standards/semanticweb/
- Personal Knowledge Graphs: https://personalknowledgegraphs.com/
- UUIDv7 RFC: https://www.rfc-editor.org/rfc/rfc9562.html
