# Exobrain / KnowledgeFS – High-Level Design & Product Plan (Clean Summary)

## 1) Core goal

Build a knowledge-first system you can trust for years of thinking, writing, and collaboration.

Priorities:
- Text-only core
- Markdown-first
- Strong structure with validation
- Migration-safe evolution
- CLI-first usage
- Able to grow beyond a single “app”

The immediate focus is trust in the document system, not UI.

## 2) Foundational philosophy

- Knowledge is the truth, not paths.
- Files are a view over structured knowledge.
- Everything is linkable, but not everything is a container.
- Links carry intent and rationale, not just adjacency.
- Structure must be enforceable and migratable.
- UI is optional; infrastructure is not.

## 3) Long-term architecture

Phase A (now): CLI-first foundation
- Canonical Markdown documents
- Strict workspace spec (folders + metadata rules)
- Schemas and validation
- Migrations framework
- Local tool runner (transcription, publishing, agents later)
- Git-based collaboration

Phase B (later): UI as a view
- Optional IDE-like desktop frontend (Theia or similar)
- Views: file tree, doc editor, diff review, agent panel, run logs
- UI calls the same CLI/tool-runner primitives

Phase C (later): KnowledgeFS via FUSE
- Introduce a knowledge-core service that exposes:
  - nodes (docs, spaces, concepts)
  - links (graph)
  - indexes (keyword, optional embeddings)
  - permissions and audit logs
- Use FUSE to present a filesystem projection where:
  - directories are query-driven projections
  - paths are views over knowledge
- Keep Linux/macOS/Windows unchanged (user-space only)

Key idea:
- One substrate
- Multiple frontends (CLI, IDE, filesystem view)
- Canonical truth remains text + metadata, so everything is migratable

## 4) Canonical entity model (text-only V1)

Design rule:
- Everything is a node
- Nodes have kinds
- Links are first-class edges
- Markdown is canonical
- No images or audio stored in-repo (text only). Audio can be used transiently and discarded.

Entity types:

1. Workspace
- Repo-level boundary and configuration
- Owns schema version, defaults, tool config, and global state

2. Space
- A container for related docs (your “idea spaces”)
- Has a stable slug and optional space-level configuration

3. Doc (core unit)
- Atomic authored text artifact
- Has a UUID id and a type
- Stored as Markdown with YAML frontmatter
- Types stay minimal in V1:
  - note
  - transcript (text-only)
  - summary
  - post
  - index

4. Concept (optional but useful)
- Lightweight named entity node for themes/projects/people/characters
- Keeps the graph clean without forcing everything to become a space

5. Link (edge)
- Typed, directed relationship between nodes
- Supports “suggested vs accepted vs rejected”
- Can include rationale and evidence pointers

6. Run receipt (optional but recommended)
- Audit record of tool/agent actions
- Captures what ran, inputs, outputs, and files changed
- Builds trust and reproducibility

## 5) IDs and collaboration

- Use UUIDs for docs and links to support async multi-user collaboration safely.
- Prefer UUIDv7 (time-sortable) for nicer ordering, but UUIDv4 is acceptable.
- Filenames should equal the UUID to avoid renames breaking identity.
- Use short display aliases only for UI/UX; identity remains UUID.

## 6) Links and the “networking” system

Links are more than “connected”:
- They carry type, direction, status, timestamp, and rationale.

Keep link types minimal in V1:
- relates_to
- derived_from
- references
- mentions

Use a uniform reference scheme for endpoints:
- workspace:<id>
- space:<slug>
- doc:<id>
- concept:<slug>

Store links as append-only JSONL for merge friendliness.

## 7) CLI that enforces the system

Core CLI responsibilities:
- Initialize a valid workspace
- Create spaces and docs with correct metadata
- Validate structure and references
- Manage migrations between schema versions
- Provide a safe, consistent tool runner for local processes

Core commands (shape):
- init: create workspace scaffolding and schemas
- space new: create a space
- doc new: create a doc with required frontmatter
- validate: enforce schemas, uniqueness, references
- migrate: scripted upgrades with dry-run support
- link add: add a first-class edge
- run: execute tools via a policy-controlled runner

Validation should check:
- required frontmatter
- unique IDs
- filename matches id
- doc belongs to existing space
- derived_from targets exist
- links point to existing nodes
- no schema drift

## 8) Local tool runner (security + reproducibility boundary)

Unify execution of:
- transcription (local Whisper)
- publishing (Quarto as integration)
- agents (Claude Code, Gemini CLI later)
- future connectors (Gmail/Jira later)

Runner requirements:
- explicit tool manifests (command, args templates)
- environment allowlist (don’t inherit all user env)
- controlled filesystem access policy
- capture stdout/stderr
- write run receipts (optional but recommended)
- secrets live outside the repo and are never passed to the agent prompt

## 9) Transcription strategy (optional integration)

Even though the core is text-only:
- You can ingest audio transiently to produce a transcript doc
- Use local Whisper (whisper.cpp) for offline, predictable, low-cost transcription
- Discard audio after transcription if desired

This keeps the core repository text-only while enabling voice workflows.

## 10) Why this is “more than an app”

- The workspace spec and CLI define a stable, migratable substrate.
- A desktop UI is just one view over that substrate.
- KnowledgeFS (FUSE) becomes a universal compatibility layer, making the substrate usable by existing tools as if it were a filesystem.
- You are building infrastructure for thinking, not a single interface.

## 11) Immediate next steps (foundation V1)

1. Finalize workspace spec:
   - folder layout
   - doc frontmatter requirements
   - link storage format
2. Implement schemas and validation:
   - fail fast on structural issues
3. Implement migration framework:
   - schema_version + repeatable scripts
4. Implement tool runner:
   - manifests + restricted env + run receipts
5. (Optional) add local transcription integration:
   - whisper.cpp invoked via tool runner

Done when:
- You can create and evolve content with confidence
- Validation is strict and automated
- Migrations are scripted and safe
- Future indexing/UI/KnowledgeFS can be layered without breaking old content
