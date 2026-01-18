# Exobrain – Core Feature Concept (V1)

## Purpose

The goal of this phase is to turn an ad‑hoc writing and ideation repo into a **trusted, durable knowledge workspace** that can safely grow over time and support multiple people working asynchronously.

This phase is not about UI, performance, or advanced AI features.
It is about **structure, trust, and longevity**.

---

## Core Concept

You are defining a **knowledge workspace** where:

- All content is text
- All content has a stable identity
- Structure is intentional and enforced
- Relationships between ideas are explicit
- Future changes will not break past work

Everything else builds on this.

---

## Feature 1: Workspace Specification

Define a clear, explicit structure for how knowledge lives on disk.

Conceptually, this means:
- There is one recognized “workspace”
- The workspace has clear boundaries and rules
- Content is organized into meaningful idea spaces
- Every piece of writing fits predictably into that structure

The workspace spec becomes the **contract** that guarantees:
- content can be understood later
- content can be migrated safely
- tools and people can rely on consistency

---

## Feature 2: CLI That Enforces the Workspace

Instead of relying on discipline or memory, the system enforces structure.

Conceptually, the CLI:
- Creates new content correctly by default
- Prevents invalid or ambiguous states
- Verifies that the workspace remains consistent
- Acts as the single authority for “what is valid”

This removes anxiety about:
- whether files are in the right place
- whether metadata is missing
- whether relationships are broken

The CLI is not just a convenience tool.
It is the **guardian of trust**.

---

## Feature 3: Local Tool Runner

All automated actions run through a single, controlled interface.

Conceptually, the tool runner:
- Executes local tools in a predictable way
- Records what happened and why
- Keeps automation transparent and auditable
- Separates “human intent” from “machine execution”

This creates confidence that:
- automation is not doing hidden damage
- future systems can understand past actions
- the workspace remains explainable

---

## Identity Strategy: UUIDv7 Everywhere

Every piece of content receives a globally unique, time‑sortable identity.

Conceptually, this enables:
- many people working independently
- safe merging without coordination
- long‑term references that never break
- content that outlives filenames or folders

Identity is permanent.
Location is just an organizational choice.

---

## What This Phase Enables Later

By completing this phase, you unlock:

- confident daily use without fear of rework
- safe refactoring and evolution of structure
- multiple interfaces over the same content
- filesystem views, UIs, or agents layered later
- long‑term accumulation of thought without decay

---

## Summary

This phase is about **making thinking safe**.

You are building:
- a trusted place to put ideas
- a structure that enforces itself
- identities that survive collaboration and time
- a foundation that future features can stand on

Once this exists, everything else becomes optional.
