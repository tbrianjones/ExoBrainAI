---
name: test-system
description: Run an end-to-end integration test that simulates a real user session across all ExoBrain features
allowed-tools: Bash, Read, Write, Edit, Glob, AskUserQuestion
---

# Test System

Run a comprehensive, narrative integration test of ExoBrain. This simulates a real user session; capturing ideas, organizing knowledge, projecting to disk, editing, and syncing back.

All test objects are tagged with `_system-test` for easy identification and cleanup.

**Important**: Report results visually as you go. The user should be able to watch and follow along.

## Pre-flight

Before starting, set up:

```bash
EXEC="docker compose exec exobrain-test exobrain"
```

All CLI commands use this prefix. Always use `--json` when you need to parse output programmatically. Use human-readable output when reporting to the user.

## Phase 0: Test Environment Setup

**Goal**: Start an isolated test container with a fresh, disposable data directory.

1. Create the test data directory if it doesn't exist:
   ```bash
   mkdir -p test-data
   ```

2. Start the test container:
   ```bash
   docker compose --profile test up -d exobrain-test
   ```

3. Wait for the container to become healthy. Poll `docker compose ps` until `exobrain-test` shows `healthy` (up to 60 seconds, checking every 5 seconds). If it doesn't become healthy, report the error and abort.

4. Initialize a fresh database:
   ```bash
   docker compose exec exobrain-test exobrain init
   ```

**Report format**:
```
Phase 0: Test Environment Setup
  Directory:  [OK] test-data/ created
  Container:  [OK] exobrain-test started (profile: test)
  Health:     [OK] healthy after Ns
  Init:       [OK] database initialized with bootstrap objects
```

## Phase 1: System Health Check

**Goal**: Verify the system is running and healthy.

1. Run `docker compose ps` and verify the `exobrain-test` service is healthy
2. Run `$EXEC status --json` and capture the baseline:
   - Record `object_count`, `tag_count`, `link_count`, `file_count`
   - Record `db_size_bytes`
   - Verify `integrity` is `"ok"`
3. Run `$EXEC doctor --json` and verify all checks pass
4. Check the API health endpoint from inside the container:
   ```
   docker compose exec exobrain-test python -c "import urllib.request, json; r=urllib.request.urlopen('http://localhost:8420/health'); d=json.loads(r.read()); print(json.dumps(d))"
   ```
   Verify `status: "ok"`

**Report format**:
```
Phase 1: System Health Check
  Docker:     [OK] exobrain-test is healthy
  Status:     [OK] 25 objects, 11 tags, 2 links, 0 files
  Doctor:     [OK] integrity passed, FTS5 passed, no orphans
  API:        [OK] health endpoint responsive
  Baseline recorded.
```

## Phase 2: Knowledge Capture

**Goal**: Create diverse objects that exercise all object types, spaces, and tagging.

Create the following objects (capture the IDs from `--json` output for later use):

1. **Create a custom space**:
   ```
   $EXEC space create "testing/integration"
   ```

2. **Note** (inbox):
   ```
   $EXEC capture "Personal knowledge systems should mirror how the brain actually works: associative, contextual, and weighted by relevance rather than recency alone." \
     --title "Associative Knowledge Architecture" --type note --tag _system-test --tag knowledge --tag architecture
   ```

3. **Concept** (inbox):
   ```
   $EXEC capture "The hot tier projection model: surface the top N objects by a composite score of recency, access frequency, and link density. Below N objects, project everything. Complexity scales with data, not onboarding." \
     --title "Hot Tier Projection" --type concept --tag _system-test --tag projection --tag scoring
   ```

4. **Document** (testing/integration space):
   ```
   $EXEC capture "$(cat engine/tests/fixtures/sample-blog-post.md)" \
     --title "Blog Draft: Knowledge Systems That Think Back" --type document --space "testing/integration" --tag _system-test --tag writing --tag draft
   ```

5. **Transcript** (testing/integration space):
   ```
   $EXEC capture "$(cat engine/tests/fixtures/sample-transcript.md)" \
     --title "Transcript: Future of Personal Knowledge Systems" --type transcript --space "testing/integration" --tag _system-test --tag conversation --tag knowledge
   ```

6. **URL** (inbox):
   ```
   $EXEC capture "https://en.wikipedia.org/wiki/Personal_knowledge_management" \
     --title "Wikipedia: Personal Knowledge Management" --type url --tag _system-test --tag reference
   ```

7. **Verify each was created** by running `$EXEC get <id> --json` for each object.

**Report format**:
```
Phase 2: Knowledge Capture (6 objects)
  [OK] Space created: testing/integration
  [OK] Note: Associative Knowledge Architecture (id: 069...)
  [OK] Concept: Hot Tier Projection (id: 069...)
  [OK] Document: Blog Draft (id: 069...) [space: testing/integration]
  [OK] Transcript: Future of PKS (id: 069...) [space: testing/integration]
  [OK] URL: Wikipedia PKM (id: 069...)
  All objects verified via get.
```

## Phase 3: Search and Discovery

**Goal**: Verify that FTS5 search, filtering, and tag queries all work.

1. **Full-text search**: `$EXEC search "knowledge" --json`
   - Should find at least the Note and Transcript (both contain "knowledge")
   - Verify result count >= 2

2. **Type filter**: `$EXEC list --type transcript --json`
   - Should include the test transcript

3. **Space filter**: `$EXEC list --space "testing/integration" --json`
   - Should return exactly 2 objects (Document + Transcript)

4. **Tag filter**: `$EXEC list --tag _system-test --json`
   - Should return all 5 test objects

5. **Tag list**: `$EXEC tag list --json`
   - Should include `_system-test` with count 5

**Report format**:
```
Phase 3: Search and Discovery
  [OK] FTS "knowledge": found 4 results (expected >= 2)
  [OK] Type filter (transcript): found 1 result
  [OK] Space filter (testing/integration): found 2 results
  [OK] Tag filter (_system-test): found 5 results
  [OK] Tag list includes _system-test (count: 5)
```

## Phase 4: Links and Relationships

**Goal**: Create a relationship network between test objects.

Using the IDs captured in Phase 2:

1. Link Transcript -> Note with "inspired"
2. Link Note -> Concept with "formalized-as"
3. Link Concept -> Document with "elaborated-in"
4. Link Document -> Transcript with "derived-from"

This creates a cycle: Transcript -> Note -> Concept -> Document -> Transcript

5. **Verify links**: `$EXEC link list <transcript_id>`
   - Should show both outgoing "inspired" and incoming "derived-from"

6. **Verify link count**: `$EXEC status --json`
   - link_count should have increased by 4

**Report format**:
```
Phase 4: Links and Relationships
  [OK] Transcript --[inspired]--> Note
  [OK] Note --[formalized-as]--> Concept
  [OK] Concept --[elaborated-in]--> Document
  [OK] Document --[derived-from]--> Transcript
  [OK] Link verification: Transcript has 2 links (1 outgoing, 1 incoming)
  [OK] Total links increased by 4
```

## Phase 5: Projection Cycle

**Goal**: Project objects to disk, verify files, and test bidirectional sync.

1. **Project**: `$EXEC project --json`
   - Record projected count and space count

2. **Verify files on disk**: Check that projected files exist for test objects
   ```
   docker compose exec exobrain-test find /data/projected -name "*_system-test*" -o -name "*associative*" -o -name "*hot-tier*"
   ```
   Or list all projected files and check for test objects.

3. **Verify frontmatter**: Read one projected file and verify:
   - Has valid YAML frontmatter with id, type, space, title, tags
   - Content body matches what was captured
   - Tags include `_system-test`

4. **Tier status**: `$EXEC tier status --json`
   - Verify projected count matches expectations

5. **Edit a projected file**: Using the Note's projected file:
   - Add a new tag (`_edited-by-test`) to the YAML frontmatter
   - Append a paragraph to the content body

6. **Sync back**: `$EXEC sync <path-to-edited-file>`
   - Verify sync succeeds

7. **Verify sync**: `$EXEC get <note_id> --json`
   - Verify the new tag appears
   - Verify the appended content is in the database

8. **Re-project**: `$EXEC project` to update the file after sync

**Report format**:
```
Phase 5: Projection Cycle
  [OK] Projected N objects to M spaces
  [OK] Test object files found on disk
  [OK] Frontmatter valid (Note: Associative Knowledge Architecture)
  [OK] Tier status: N projected, limit 200
  [OK] File edited: added tag + content paragraph
  [OK] Sync: changes written back to database
  [OK] Verified: new tag "_edited-by-test" present in DB
  [OK] Verified: appended content present in DB
  [OK] Re-projected successfully
```

## Phase 6: Update and Lifecycle

**Goal**: Test object updates, projection overrides, and the update workflow.

1. **Update title**: `$EXEC update <concept_id> --title "Hot Tier Projection Model (Revised)"`
   - Verify title changed

2. **Update content**: `$EXEC update <url_id> --content "https://en.wikipedia.org/wiki/Personal_knowledge_management ; See also: Zettelkasten, Memex, Vannevar Bush"`
   - Verify content changed

3. **Projection override**: `$EXEC update <note_id> --always-project`
   - Verify via `$EXEC tier status --json` that always_project list includes the note

4. **Project again**: `$EXEC project --json`
   - Verify projected file reflects updates

**Report format**:
```
Phase 6: Update and Lifecycle
  [OK] Title updated: "Hot Tier Projection Model (Revised)"
  [OK] Content updated: URL now has expanded description
  [OK] Projection override: Note set to always-project
  [OK] Tier status confirms always-project override
  [OK] Re-projection reflects all changes
```

## Phase 7: Integrity Verification

**Goal**: Final system check. Compare against Phase 1 baseline.

1. Run `$EXEC status --json` and compare:
   - object_count should be baseline + 5 (test objects) + number of new spaces
   - tag_count should have increased
   - link_count should be baseline + 4
   - integrity should still be `"ok"`

2. Run `$EXEC doctor --json`:
   - All checks should pass
   - No orphaned files

3. Check the API status endpoint from inside the container:
   ```
   docker compose exec exobrain-test python -c "import urllib.request, json; r=urllib.request.urlopen('http://localhost:8420/health'); d=json.loads(r.read()); print(json.dumps(d))"
   ```
   Verify API is responsive and consistent

**Report format**:
```
Phase 7: Integrity Verification
  [OK] Object count: 25 -> 32 (delta: +7, expected +7)
  [OK] Tag count: 11 -> 22 (delta: +11)
  [OK] Link count: 2 -> 6 (delta: +4)
  [OK] Integrity: ok
  [OK] Doctor: all checks passed
  [OK] API status: projection stats consistent
```

## Phase 8: Cleanup

**Goal**: Remove test artifacts and optionally tear down the test container.

Ask the user before proceeding:

> "All 8 test phases passed (Phase 0 through 7). Would you like me to clean up? Options: (1) Clean up test objects only, (2) Full teardown (stop container + remove test data), (3) Skip cleanup."

**Option 1 or 2; Object cleanup**:

1. List all `_system-test` objects: `$EXEC list --tag _system-test --json`
2. Delete each test object: `$EXEC delete <id> --yes`
3. Also delete any `_edited-by-test` tagged objects if different
4. Delete the test space: Find and delete `testing/integration` and `testing` space objects
5. Run `$EXEC project --cleanup` to remove stale projected files
6. Run `$EXEC status` for final count

**Option 2 only; Container teardown**:

7. Stop the test container and remove its cache volume:
   ```bash
   docker compose --profile test down -v
   ```
8. Remove the local test data directory:
   ```bash
   rm -rf test-data/
   ```

**Report format**:
```
Phase 8: Cleanup
  Deleted 5 test objects
  Deleted 2 test spaces
  Cleaned up projected files
  Container:  [stopped/kept]
  Test data:  [removed/kept]
  Final status: back to baseline (or container removed)
```

## Final Summary

After all phases, present a summary table:

```
ExoBrain Integration Test Results
==================================
Phase 0: Test Environment   [PASS]
Phase 1: System Health      [PASS]
Phase 2: Knowledge Capture  [PASS]
Phase 3: Search/Discovery   [PASS]
Phase 4: Links/Relations    [PASS]
Phase 5: Projection/Sync    [PASS]
Phase 6: Update/Lifecycle   [PASS]
Phase 7: Integrity Check    [PASS]
Phase 8: Cleanup            [PASS/SKIP]

Container:       exobrain-test (isolated)
Objects created: 5
Links created:   4
Projections:     verified
Sync:            bidirectional verified
Duration:        ~2 minutes
```

If any phase fails, report the failure clearly with the error output and continue to the next phase. Do not abort the entire test on a single failure; the point is to assess the full system.
