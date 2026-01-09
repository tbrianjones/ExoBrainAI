# Daily Partner Summary Template

**Type**: Reusable template for /generate-view
**Output naming**: `daily-partner-summary-YYYY-MM-DD.md`
**Source**: Single day's transcript from `transcripts/`
**Audience**: Dev partner (front-end/product, writes code, not an architect)
**Length**: 1 page max (~400-500 words)

---

## Template Structure

### Header
```
# [Date] Summary
```

### 1. How It Went (Personal)
2-3 sentences. Tone of the day, energy level, overall feel of the work. Human connection; this is partner to partner, not a status report.

### 2. What Got Done (Technical)
Bullet points. Features shipped, bugs fixed, things that moved. Be specific but brief. If architecture changed, note it here.

### 3. What's Coming / What's Broken
Bullet points. Heads up on incoming changes, known issues, things that might affect his work. Security concerns if any.

### 4. Data Notes (if applicable)
Only include if there were data model changes, schema updates, or design decisions about data. Skip if nothing relevant.

### 5. Business/Admin (if applicable)
Only include if there's partner-level business stuff: decisions made, things to discuss, administrative notes. Skip if nothing relevant.

---

## Generation Instructions

When generating from a transcript:

1. Read the day's transcript in full
2. Extract items that fit each category
3. Write in first person, conversational but concise
4. Prioritize what he needs to know over completeness
5. If a section has nothing, omit it entirely
6. Keep total output under 500 words
7. Don't pad; short days get short summaries

## Example Output

```markdown
# January 9, 2026 Summary

## How It Went
Solid day. Got into flow on the auth refactor and stayed there most of the afternoon. Felt productive; less context switching than usual.

## What Got Done
- Finished JWT refresh token logic
- Fixed the session timeout bug you flagged
- Updated the user model to track last_login

## What's Coming / What's Broken
- Auth middleware changes will hit your components tomorrow; might need to update how you check login state
- There's a race condition in the logout flow I haven't fixed yet; don't ship anything that depends on immediate logout

## Data Notes
- Added `last_login` timestamp to users table
- Considering adding a `sessions` table for multi-device support; will discuss before implementing
```
