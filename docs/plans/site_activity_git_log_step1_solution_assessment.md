# Site Activity Git Log Step 1: Solution Assessment

## Problem statement
The `/activity/` surface currently renders the newest canonical posts but the new requirement is to display chronological items tied to the git commit log, including commit fingerprints and dates, with the git log serving as the source of truth for ordering.

## Option A – Keep the post-based feed and annotate it with git metadata
- Pros: Reuses the existing record-loading helpers and `post-card` markup, so we avoid touching git parsing or ordering logic. We can tack on commit ID/date per card by looking up the commit that created the file and still display draft posts in canonical order.
- Cons: Deriving a commit from each post file is hard to keep accurate, and the “source of truth” is still the record list, which will not reflect the git log order or show commits that add metadata (e.g., moderation records) without new posts.

## Option B – Drive the activity feed from `git log` itself and render each commit as an item
- Pros: The git log already contains the commit fingerprint/date order required by the user, so we can show the true chronological history and include the commit metadata directly; items can point back to the associated post file(s). The git commit becomes the canonical source for everything shown on `/activity/`.
- Cons: We must parse `git log` output, resolve the affected records (maybe by looking at file paths or commit messages), and ensure this still plays nicely with the existing `post-card` markup. It could also be more expensive than the current record query.

## Recommendation
Adopt Option B: stream the git log into `/activity/`, enrich each commit entry with the IPA fingerprint, date, and the canonical post(s) it touched, and render these as the activity items so the git history remains the definitive timeline while still linking back to the post view components.
