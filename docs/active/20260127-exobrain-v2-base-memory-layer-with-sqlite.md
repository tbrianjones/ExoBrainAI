# ExoBrain v0 – Minimal Conceptual Data Model (Final Draft)

This document defines the **absolute minimum conceptual data structure** for ExoBrain v0.
It is intentionally simple. It defines *what must exist*, not how it is stored in SQL.

---

## Core Principles

- Everything is an **object**
- SQLite is the **source of truth**
- Files on disk are **raw evidence**, referenced by objects
- CLI enforces structure
- Claude Code is the first UI
- GraphRAG, embeddings, agents are **future integrations**, not core

---

## 1. Object (the only real primitive)

**Everything is an object**, including spaces, tags, and types.

An object has:
- **ID** – globally unique
- **Type** – reference to a *type object*
- **Space** – reference to a *space object*
- **Title** – human-readable name
- **Summary** – short text (explicitly called “summary”, not description)
- **Tags** – zero or more tags (string or object reference)
- **File reference** – zero or one file/blob reference
- **Created at**
- **Updated at**

Rules:
- Every object has exactly one type
- Every object belongs to exactly one space
- An object may have **at most one file**
- Objects may exist without files

Examples of objects:
- Transcript
- Document
- Note
- URL
- Space
- Tag
- Type

---

## 2. Type (object subtype, mandatory)

**Type is always an object.**
Type is never a tag and never free text.

A type object:
- Is an object whose **type is `type`**
- Defines how objects of that type are treated
- Is referenced by other objects via their `type` field

Bootstrapping rule (intentional):
- The first `type` object is **self-referential**
- A type object references itself as its type

Rules:
- Every object has exactly one type
- Types control behavior, not meaning
- Types are slow to add and intentionally few

### Initial required types
Start with only:
- `type`
- `space`
- `tag`
- `document`
- `transcript`
- `note`
- `url`

Do not add more until the system forces it.

---

## 3. Space (object subtype, hierarchical by name)

**A space is an object whose type is `space`.**

A space object has:
- ID
- Type = `space`
- **Name** – hierarchical, slash-delimited path
- Optional summary

Examples:
- `primitives`
- `primitives/type`
- `primitives/space`
- `work`
- `work/exobrain`

Rules:
- Slash structure implies hierarchy
- Parent space is inferred from the name
- No explicit parent field is required
- Every object belongs to exactly one space

---

## 4. Tag (semantic label, optionally an object)

**Tags may or may not be objects. This is intentionally flexible.**

At minimum:
- A tag is a short text label

Optionally:
- A tag can be an object whose type is `tag`
- Tag objects may have summaries and relationships

Rules:
- Objects may have many tags
- Tags describe meaning, not behavior
- The system should not require tags to be objects initially

Open question (intentionally deferred):
- When should a string tag be promoted to a tag object?

---

## 5. File (single attachment per object)

Files are **not objects**.
They are raw data referenced by objects.

Each object may reference **zero or one file**.

A file reference includes:
- Path on disk
- Role (e.g. primary, transcript, summary)
- Optional metadata (type, size, hash)

Rules:
- Files are immutable once ingested
- Files derive meaning only through the object
- Multiple files require multiple objects

---

## 6. Link (relationship between objects)

A link connects two objects.

A link has:
- From object
- To object
- **Relationship text** (short descriptive phrase or sentence)

Examples:
- “derived from”
- “summarizes”
- “related to”
- “evidence for”

Rules:
- Links are optional
- Links provide a minimal explicit graph
- This replaces early GraphRAG needs

---

## 7. Index (derived, optional)

Indexes are **derived artifacts**, never canonical.

Examples:
- Keyword index (BM25 / SQLite FTS)
- Vector embeddings (later)

Rules:
- Indexes are generated explicitly by commands
- Indexes can be deleted and rebuilt
- Indexes are not required for correctness

---

## Required Initial Spaces

To bootstrap system structure:

- `primitives`

Within it:
- `primitives/type` – type objects
- `primitives/space` – space objects
- `primitives/tag` or `primitives/tags` – tag objects (naming TBD)

User content lives outside `primitives`.

---

## Open Question: File Storage Layout

Since humans no longer manage files directly:
- Disk layout does not need to mirror spaces
- UI will present structure by space, tag, or query

Options:
- Flat storage by object ID
- Date-based folders
- Content-addressed storage

Recommendation:
- Start simple
- Optimize later if needed

---

## Locked Mental Model

- Everything is an object
- Types, spaces, and tags are objects
- Objects reference exactly one type and one space
- Objects may reference one file
- SQLite holds meaning
- Disk holds evidence
- CLI enforces structure
- Claude Code is the first UI
- Everything else is an integration
