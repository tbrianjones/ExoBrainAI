"""Insert [[uuid|title]] wiki-links into existing object content.

Scans all objects for title mentions of other objects and replaces them
with inline content references. Designed to be run once as a migration.

Usage: python -m scripts.insert_wikilinks [--dry-run]
"""

import json
import re
import subprocess
import sys


def get_all_objects():
    """Fetch all objects via CLI."""
    result = subprocess.run(
        ["exobrain", "list", "--json", "--limit", "500"],
        capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def get_object_detail(obj_id):
    """Fetch full object detail including content."""
    result = subprocess.run(
        ["exobrain", "get", obj_id, "--json"],
        capture_output=True, text=True,
    )
    return json.loads(result.stdout)


def build_title_map(objects):
    """Build a title -> (uuid, type_name) map for link targets.

    Only includes types that make meaningful link targets.
    Sorts by title length descending to avoid partial replacement.
    """
    LINK_TARGET_TYPES = {
        "Document", "Concept", "Person", "Transcript", "View",
        "Note", "Project", "URL", "Event", "Audience", "Business",
    }

    title_map = {}
    for o in objects:
        # Skip bootstrap objects
        if o["id"].startswith("00000000"):
            continue
        type_name = o.get("type_name", "")
        if type_name not in LINK_TARGET_TYPES:
            continue
        title = o.get("title", "").strip()
        # Skip very short titles that would cause false matches
        if len(title) < 5:
            continue
        title_map[title] = o["id"]

    return title_map


def insert_wikilinks(content, title_map, self_id):
    """Replace title mentions in content with [[uuid|title]] wiki-links.

    Returns (new_content, list_of_replacements).
    """
    if not content:
        return content, []

    replacements = []

    # Sort titles longest-first to avoid partial replacement
    sorted_titles = sorted(title_map.keys(), key=len, reverse=True)

    for title in sorted_titles:
        uuid = title_map[title]

        # Skip self-references
        if uuid == self_id:
            continue

        # Skip if this title's UUID already appears as a wiki-link in the content
        if f"[[{uuid}|" in content:
            continue

        # Use word-boundary matching for exact title
        # Escape regex special chars in the title
        escaped_title = re.escape(title)
        pattern = rf"(?<!\[\[{re.escape(uuid)}\|)\b{escaped_title}\b"

        # Check if the title appears in the content
        match = re.search(pattern, content)
        if match:
            # Only replace the FIRST occurrence to avoid over-linking
            wikilink = f"[[{uuid}|{title}]]"
            content = content[:match.start()] + wikilink + content[match.end():]
            replacements.append((title, uuid))

    return content, replacements


def main():
    dry_run = "--dry-run" in sys.argv

    print(f"{'DRY RUN: ' if dry_run else ''}Scanning objects for inline link opportunities...")
    print()

    objects = get_all_objects()
    title_map = build_title_map(objects)
    print(f"Found {len(title_map)} potential link targets")

    # Track statistics
    total_replacements = 0
    objects_modified = 0

    for obj in objects:
        # Skip bootstrap/system objects
        if obj["id"].startswith("00000000"):
            continue

        # Skip Spaces (they don't have prose content)
        if obj.get("type_name") == "Space":
            continue

        # Get full object detail for content
        detail = get_object_detail(obj["id"])
        content = detail.get("content", "")
        if not content or len(content) < 10:
            continue

        # Try to insert wiki-links
        new_content, replacements = insert_wikilinks(content, title_map, obj["id"])

        if replacements:
            objects_modified += 1
            total_replacements += len(replacements)
            title = obj.get("title", obj["id"][:8])
            print(f"\n{'[DRY RUN] ' if dry_run else ''}Object: {title}")
            print(f"  ID: {obj['id']}")
            for ref_title, ref_uuid in replacements:
                print(f"  + [[{ref_uuid}|{ref_title}]]")

            if not dry_run:
                # Update the object content via CLI
                proc = subprocess.run(
                    ["exobrain", "update", obj["id"], "--content", new_content],
                    capture_output=True, text=True,
                )
                if proc.returncode != 0:
                    print(f"  ERROR: {proc.stderr.strip()}")
                else:
                    print(f"  Updated successfully")

    print(f"\n{'DRY RUN ' if dry_run else ''}Summary:")
    print(f"  Objects modified: {objects_modified}")
    print(f"  Wiki-links inserted: {total_replacements}")


if __name__ == "__main__":
    main()
