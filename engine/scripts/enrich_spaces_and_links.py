"""One-time data enrichment script: port idea-readme concepts to space objects,
enrich space and type descriptions, and create links between idea space objects.

Run inside container: docker compose exec exobrain python scripts/enrich_spaces_and_links.py

This script is idempotent; it uses UPDATE and INSERT OR IGNORE to avoid duplicates.
"""

import sqlite3
import sys

from src.config import settings
from src.core.bootstrap import BOOTSTRAP_IDS


def main():
    db_path = settings.db_path
    if not db_path.exists():
        print(f"Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")

    try:
        # ---------------------------------------------------------------
        # Part 1: Create derived-from, references, responds-to links
        # (BEFORE deleting concepts, so all objects still exist)
        # ---------------------------------------------------------------
        print("Creating links between idea space objects...")

        # Helper: resolve object ID by title within a space
        def find_id(title, space_name):
            row = conn.execute(
                """SELECT o.id FROM objects o
                   JOIN objects s ON o.space_id = s.id
                   WHERE o.title = ? AND s.title = ?""",
                (title, space_name),
            ).fetchone()
            if row is None:
                print(f"  WARNING: Could not find '{title}' in {space_name}", file=sys.stderr)
                return None
            return row["id"]

        # Helper: resolve space object ID by path
        def find_space_id(space_path):
            row = conn.execute(
                "SELECT id FROM objects WHERE title = ? AND type_id = ?",
                (space_path, BOOTSTRAP_IDS["space"]),
            ).fetchone()
            if row is None:
                print(f"  WARNING: Could not find space '{space_path}'", file=sys.stderr)
                return None
            return row["id"]

        def create_link(from_id, to_id, relationship):
            if from_id is None or to_id is None:
                return False
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO links (from_id, to_id, relationship, source, confidence) VALUES (?, ?, ?, 'system', 1.0)",
                    (from_id, to_id, relationship),
                )
                return True
            except sqlite3.IntegrityError:
                return False

        links_created = 0

        # Within ideas/exobrain
        s = "ideas/exobrain"
        if create_link(find_id("ExoBrain Core Vision", s), find_id("ExoBrain Core Vision (Summary)", s), "derived-from"):
            links_created += 1

        # Within ideas/consciousness-in-the-age-of-ai
        s = "ideas/consciousness-in-the-age-of-ai"
        link_defs = [
            ("Ubiquitous Consciousness Field Theory", "UCFT (Extended)", "derived-from"),
            ("Consciousness and AI", "Initial Ideation: Consciousness and AI", "derived-from"),
            ("Who Is Talking?", "Ubiquitous Consciousness Field Theory", "derived-from"),
            ("Consciousness as Information", "Initial Ideation: Consciousness and AI", "derived-from"),
            ("UCFT Technical Overview", "Ubiquitous Consciousness Field Theory", "derived-from"),
            ("UCFT Research Papers", "Ubiquitous Consciousness Field Theory", "derived-from"),
            ("The Equation", "Ubiquitous Consciousness Field Theory", "derived-from"),
            ("The Silicon Singers of Verath", "Ubiquitous Consciousness Field Theory", "derived-from"),
            ("The Augmentation Map", "Initial Ideation: Consciousness and AI", "derived-from"),
        ]
        for from_title, to_title, rel in link_defs:
            if create_link(find_id(from_title, s), find_id(to_title, s), rel):
                links_created += 1

        # Within ideas/economics-of-claude-code
        s = "ideas/economics-of-claude-code"
        if create_link(find_id("Hey Machias: Look At These Ridiculous Numbers", s), find_id("Economics of Claude Code: Initial Ideation", s), "derived-from"):
            links_created += 1
        if create_link(find_id("Pricing Correction", s), find_id("Economics of Claude Code: Initial Ideation", s), "responds-to"):
            links_created += 1

        # Within ideas/agentic-development-process
        s = "ideas/agentic-development-process"
        if create_link(find_id("Procedure: Extracting Development Transcripts", s), find_id("SP API Pipeline Planning (Summary)", s), "derived-from"):
            links_created += 1

        # Within ideas/trade-policy-and-epistemic-humility
        s = "ideas/trade-policy-and-epistemic-humility"
        blog_id = find_id("Epistemic Humility in Trade Policy", s)
        if create_link(blog_id, find_id("Epistemic Limits of Economics", s), "derived-from"):
            links_created += 1
        if create_link(blog_id, find_id("Trade Policy Research Report", s), "derived-from"):
            links_created += 1
        if create_link(blog_id, find_id("Lutnick All-In Podcast Reference", s), "references"):
            links_created += 1

        # Within ideas/daily-voice-diary
        s = "ideas/daily-voice-diary"
        if create_link(find_id("Daily Partner Summary Template", s), find_id("Daily Voice Diary: Kickoff", s), "derived-from"):
            links_created += 1

        # Within ideas/agent-ideation-driven-content-production
        s = "ideas/agent-ideation-driven-content-production"
        if create_link(find_id("AI Content Creation Landscape: Research Report", s), find_id("System Setup", s), "derived-from"):
            links_created += 1

        # Cross-space links
        exobrain_vision_id = find_id("ExoBrain Core Vision", "ideas/exobrain")
        ucft_transcript_id = find_id("Ubiquitous Consciousness Field Theory", "ideas/consciousness-in-the-age-of-ai")
        if create_link(exobrain_vision_id, ucft_transcript_id, "references"):
            links_created += 1

        print(f"  Created {links_created} links")

        # ---------------------------------------------------------------
        # Part 2: Port idea-readme concepts to space objects
        # ---------------------------------------------------------------
        print("Porting idea-readme concept content to space objects...")

        concept_to_space = {
            "069897b1-3bf3-78b2-8000-411b73de7bb4": "069897a6-00eb-789c-8000-30e01b5dcfe0",  # exobrain
            "069897b0-fb22-7c9a-8000-382fa7c60b4e": "069897a5-ed49-7116-8000-58f09f12daca",  # consciousness
            "069897b1-24bd-73d2-8000-a201cfa8d3b6": "069897a5-f6ee-76c4-8000-7fa59117b3b4",  # economics
            "069897b1-514b-7ea9-8000-1a318ef18c32": "069897a6-0586-7f0c-8000-77313fafed35",  # agentic-dev
            "069897b1-2ede-7a31-8000-37a5a8d5f631": "069897a5-fb1a-779f-8000-d3277d31b9e5",  # trade-policy
            "069897b1-1d29-71fb-8000-72e50a1decbf": "069897a5-f2cd-7742-8000-bca44a04810d",  # daily-voice
        }

        concepts_ported = 0
        for concept_id, space_id in concept_to_space.items():
            concept = conn.execute(
                "SELECT summary, content FROM objects WHERE id = ?", (concept_id,)
            ).fetchone()
            if concept is None:
                print(f"  Concept {concept_id} not found (already deleted?)")
                continue

            conn.execute(
                "UPDATE objects SET summary = ?, content = ? WHERE id = ?",
                (concept["summary"], concept["content"], space_id),
            )
            concepts_ported += 1

        print(f"  Ported {concepts_ported} concept objects to space objects")

        # Delete concept objects (CASCADE will remove their tags and any links FROM/TO them)
        print("Deleting ported concept objects...")
        concepts_deleted = 0
        for concept_id in concept_to_space:
            cursor = conn.execute("DELETE FROM objects WHERE id = ?", (concept_id,))
            concepts_deleted += cursor.rowcount

        print(f"  Deleted {concepts_deleted} concept objects")

        # ---------------------------------------------------------------
        # Part 2b: Create space-to-space related-to links
        # (AFTER deleting concepts, since the old concept-to-concept link is now gone)
        # ---------------------------------------------------------------
        print("Creating space-to-space links...")
        space_links = 0
        exobrain_space = find_space_id("ideas/exobrain")
        consciousness_space = find_space_id("ideas/consciousness-in-the-age-of-ai")
        agentic_space = find_space_id("ideas/agentic-development-process")

        if create_link(exobrain_space, consciousness_space, "related-to"):
            space_links += 1
        if create_link(exobrain_space, agentic_space, "related-to"):
            space_links += 1

        print(f"  Created {space_links} space-to-space links")

        # ---------------------------------------------------------------
        # Part 3: Enrich ideas/agent-ideation-driven-content-production
        # (no concept to port; generate from space contents)
        # ---------------------------------------------------------------
        print("Enriching agent-ideation-driven-content-production space...")
        agent_ideation_space_id = "069897a5-e83e-78fa-8000-5b02a0638b1f"
        conn.execute(
            "UPDATE objects SET summary = ?, content = ? WHERE id = ?",
            (
                "Explores the thesis that AI agents can drive the entire content production pipeline from ideation through publication, using the ExoBrain system as a living experiment. Investigates multi-agent architectures, voice-first capture, and the economics of agentic content creation.",
                "# Agent-Ideation-Driven Content Production\n\n"
                "**Status**: developing\n\n"
                "## Summary\n\n"
                "The core premise: content creation should flow naturally from thinking. "
                "A human ideates through conversation; AI agents handle everything downstream; structuring, drafting, editing, and publishing. "
                "The ExoBrain system serves as both the test case and the platform for this vision.\n\n"
                "## Key Threads\n\n"
                "- **Voice-first capture**: Natural speech as the primary input modality, with AI-mediated transcription and routing\n"
                "- **Multi-agent architecture**: Specialized agents for different stages of content production (research, drafting, editing, publishing)\n"
                "- **Platform vision**: Multi-user idea sharing where idea spaces are the primary artifact and published views are exhaust\n"
                "- **Landscape analysis**: Survey of existing AI content creation systems and their architectural patterns\n",
                agent_ideation_space_id,
            ),
        )

        # ---------------------------------------------------------------
        # Part 4: Enrich non-idea space descriptions
        # ---------------------------------------------------------------
        print("Enriching non-idea space descriptions...")

        space_enrichments = {
            "00000000-0000-7000-8000-000000000101": (
                "System bootstrap namespace; contains type definitions, space definitions, tag definitions, and relationship vocabulary",
                None,
            ),
            "00000000-0000-7000-8000-000000000102": (
                "Bootstrap and user-created type definitions that control object behavior",
                None,
            ),
            "00000000-0000-7000-8000-000000000103": (
                "Bootstrap and user-created space definitions that organize the namespace hierarchy",
                None,
            ),
            "00000000-0000-7000-8000-000000000104": (
                "Reserved for future tag objects; currently unused (tags are inline strings)",
                None,
            ),
            "00000000-0000-7000-8000-000000000105": (
                "Standard relationship type vocabulary used by the links system",
                None,
            ),
            "00000000-0000-7000-8000-000000000201": (
                "Default capture space; objects land here when no space is specified and get organized later",
                None,
            ),
            # User-created spaces (by title lookup)
        }

        for space_obj_id, (summary, content) in space_enrichments.items():
            conn.execute(
                "UPDATE objects SET summary = ? WHERE id = ?",
                (summary, space_obj_id),
            )
            if content is not None:
                conn.execute(
                    "UPDATE objects SET content = ? WHERE id = ?",
                    (content, space_obj_id),
                )

        # User-created spaces (resolved by title)
        user_space_enrichments = {
            "ideas": "Parent namespace for idea exploration spaces",
            "projects": "Parent namespace for bounded project workspaces",
            "projects/exobrain": "Development workspace for the ExoBrain system itself",
            "research": "Parent namespace for research collections",
            "research/architecture": "Architectural research: patterns, precedents, and landscape analysis",
        }

        for space_title, summary in user_space_enrichments.items():
            conn.execute(
                "UPDATE objects SET summary = ? WHERE title = ? AND type_id = ?",
                (summary, space_title, BOOTSTRAP_IDS["space"]),
            )

        print("  Done")

        # ---------------------------------------------------------------
        # Part 5: Enrich type descriptions (bootstrap handles new installs;
        # this handles existing databases)
        # ---------------------------------------------------------------
        print("Enriching type descriptions...")

        type_enrichments = {
            BOOTSTRAP_IDS["type"]: "Object type definition; controls how the system processes and displays an object",
            BOOTSTRAP_IDS["space"]: "Hierarchical namespace; groups related objects for browsing, projection, and access control",
            BOOTSTRAP_IDS["tag"]: "Semantic label for faceted classification; freely added and removed",
            BOOTSTRAP_IDS["document"]: "Long-form written content: essays, reports, procedures, reference material. Use View for rendered output from idea spaces",
            BOOTSTRAP_IDS["transcript"]: "Verbatim or summarized record of a conversation, interview, or ideation session",
            BOOTSTRAP_IDS["note"]: "Brief thought, observation, or fragment; the atomic unit of capture",
            BOOTSTRAP_IDS["url"]: "Web resource reference with optional annotation",
            BOOTSTRAP_IDS["person"]: "Individual referenced in the knowledge base; author, contact, collaborator, or subject",
            BOOTSTRAP_IDS["project"]: "Bounded initiative with defined scope, timeline, and deliverables",
            BOOTSTRAP_IDS["event"]: "Time-bounded occurrence: meeting, conference, milestone, or deadline",
            BOOTSTRAP_IDS["concept"]: "Abstract idea, term definition, or framework; the conceptual backbone of an idea space",
            BOOTSTRAP_IDS["view"]: "Rendered content produced from source material in an idea space; poems, blog posts, briefs, infographics, and other publication-ready output",
        }

        for type_id, summary in type_enrichments.items():
            conn.execute(
                "UPDATE objects SET summary = ? WHERE id = ?",
                (summary, type_id),
            )

        print("  Done")

        # ---------------------------------------------------------------
        # Commit
        # ---------------------------------------------------------------
        conn.commit()
        print("\nAll changes committed successfully.")

        # Summary stats
        total_links = conn.execute("SELECT COUNT(*) as cnt FROM links").fetchone()["cnt"]
        total_objects = conn.execute("SELECT COUNT(*) as cnt FROM objects WHERE is_system_object = 0").fetchone()["cnt"]
        print(f"Total links: {total_links}")
        print(f"Total user objects: {total_objects}")

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
