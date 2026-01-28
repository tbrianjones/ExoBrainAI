"""Bootstrap the ExoBrain type system with initial types and spaces.

Uses hardcoded deterministic UUIDs so bootstrap objects are stable across installations.
The bootstrap is idempotent: running it multiple times produces no duplicates.
"""

import sqlite3

# Deterministic UUIDs for bootstrap objects.
# These are fixed so every ExoBrain installation has identical primitive IDs.
# NOTE: These are synthetic UUIDs with valid v7 version/variant bits but zero
# timestamps. They are intentionally not real UUIDv7 values; their purpose is
# stable, deterministic identity across installations.
BOOTSTRAP_IDS = {
    # Types
    "type": "00000000-0000-7000-8000-000000000001",
    "space": "00000000-0000-7000-8000-000000000002",
    "tag": "00000000-0000-7000-8000-000000000003",
    "document": "00000000-0000-7000-8000-000000000004",
    "transcript": "00000000-0000-7000-8000-000000000005",
    "note": "00000000-0000-7000-8000-000000000006",
    "url": "00000000-0000-7000-8000-000000000007",
    "person": "00000000-0000-7000-8000-000000000008",
    "project": "00000000-0000-7000-8000-000000000009",
    "event": "00000000-0000-7000-8000-00000000000a",
    "concept": "00000000-0000-7000-8000-00000000000b",
    # Spaces
    "primitives": "00000000-0000-7000-8000-000000000101",
    "primitives/type": "00000000-0000-7000-8000-000000000102",
    "primitives/space": "00000000-0000-7000-8000-000000000103",
    "primitives/tag": "00000000-0000-7000-8000-000000000104",
    "primitives/relationship": "00000000-0000-7000-8000-000000000105",
    "inbox": "00000000-0000-7000-8000-000000000201",
}

# Initial type definitions
BOOTSTRAP_TYPES = [
    ("type", "Type", "Object type definition; controls behavior"),
    ("space", "Space", "Hierarchical organizational unit"),
    ("tag", "Tag", "Semantic label for classification"),
    ("document", "Document", "General purpose document"),
    ("transcript", "Transcript", "Conversation or interview transcript"),
    ("note", "Note", "Short thought or observation"),
    ("url", "URL", "Web resource reference"),
    ("person", "Person", "Contact, author, or speaker reference"),
    ("project", "Project", "Bounded initiative with defined scope"),
    ("event", "Event", "Time-bounded occurrence like meeting or conference"),
    ("concept", "Concept", "Abstract idea or term definition"),
]

# Initial space definitions
BOOTSTRAP_SPACES = [
    ("primitives", "Primitives", "System primitive objects"),
    ("primitives/type", "Types", "Type definitions"),
    ("primitives/space", "Spaces", "Space definitions"),
    ("primitives/tag", "Tags", "Tag definitions"),
    ("primitives/relationship", "Relationships", "Standard relationship type vocabulary"),
    ("inbox", "Inbox", "Default space for user captures"),
]

# Standard relationship vocabulary for use with links
# Each is (relationship_name, inverse_name, description)
RELATIONSHIP_VOCABULARY = [
    ("references", "referenced-by", "Citation or mention"),
    ("derived-from", "source-of", "Content provenance chain"),
    ("supersedes", "superseded-by", "Version replacement"),
    ("related-to", "related-to", "Symmetric association"),
    ("part-of", "contains", "Composition hierarchy"),
    ("broader-than", "narrower-than", "Taxonomic hierarchy"),
    ("responds-to", "has-response", "Q&A or reply chain"),
    ("blocks", "blocked-by", "Dependency relationship"),
]


def bootstrap(conn: sqlite3.Connection) -> dict:
    """Create all bootstrap types and spaces.

    Temporarily disables foreign keys to allow self-referential inserts.
    Runs INSERT OR IGNORE for idempotency.

    Returns:
        Dict with counts of types and spaces created.
    """
    type_type_id = BOOTSTRAP_IDS["type"]
    space_type_id = BOOTSTRAP_IDS["space"]
    primitives_type_space = BOOTSTRAP_IDS["primitives/type"]
    primitives_space_space = BOOTSTRAP_IDS["primitives/space"]

    # Temporarily disable FK checks for self-referential bootstrap.
    # The finally block guarantees FKs are re-enabled even on error.
    conn.execute("PRAGMA foreign_keys=OFF")

    types_created = 0
    spaces_created = 0

    try:
        # 1. Create type objects (type_id = type's own ID for the 'type' type)
        for key, title, summary in BOOTSTRAP_TYPES:
            obj_id = BOOTSTRAP_IDS[key]
            cursor = conn.execute(
                """INSERT OR IGNORE INTO objects (id, type_id, space_id, title, summary, source, is_system_object)
                   VALUES (?, ?, ?, ?, ?, 'system', 1)""",
                (obj_id, type_type_id, primitives_type_space, title, summary),
            )
            types_created += cursor.rowcount

        # 2. Create space objects
        for key, title, summary in BOOTSTRAP_SPACES:
            obj_id = BOOTSTRAP_IDS[key]
            cursor = conn.execute(
                """INSERT OR IGNORE INTO objects (id, type_id, space_id, title, summary, source, is_system_object)
                   VALUES (?, ?, ?, ?, ?, 'system', 1)""",
                (obj_id, space_type_id, primitives_space_space, title, summary),
            )
            spaces_created += cursor.rowcount

        # 3. Mark existing bootstrap objects as system (for upgrades)
        all_bootstrap_ids = list(BOOTSTRAP_IDS.values())
        placeholders = ",".join("?" for _ in all_bootstrap_ids)
        conn.execute(
            f"UPDATE objects SET is_system_object = 1, source = 'system' WHERE id IN ({placeholders})",
            all_bootstrap_ids,
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        # Re-enable FK checks unconditionally
        conn.execute("PRAGMA foreign_keys=ON")

    # Verify integrity after bootstrap
    fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk_check:
        raise RuntimeError(
            f"Foreign key violations after bootstrap: {len(fk_check)} violations"
        )

    return {
        "types_created": types_created,
        "spaces_created": spaces_created,
        "total_bootstrap_objects": len(BOOTSTRAP_IDS),
    }


def get_type_id(name: str) -> str:
    """Get the bootstrap UUID for a named type.

    Args:
        name: Type name (e.g., 'document', 'note', 'transcript').

    Returns:
        The deterministic UUID for the type.

    Raises:
        KeyError: If the type name is not a bootstrap type.
    """
    return BOOTSTRAP_IDS[name]


def get_space_id(name: str) -> str:
    """Get the bootstrap UUID for a named space.

    Args:
        name: Space name (e.g., 'primitives', 'primitives/type').

    Returns:
        The deterministic UUID for the space.

    Raises:
        KeyError: If the space name is not a bootstrap space.
    """
    return BOOTSTRAP_IDS[name]
