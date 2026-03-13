## Problem
The project now has canonical post files and sample data in git, but there is no human-facing way to browse them as a forum. The next slice should prove that the text-native repository can be rendered into useful read-only web views without adding write paths, APIs, or heavier indexing machinery.

## User Stories
- As a human reader, I want a board-tag index so that I can discover available threads from the sample repository.
- As a human reader, I want a thread view so that I can read a root post and its replies in one place.
- As a human reader, I want post permalinks so that I can open a specific post directly.
- As a future backend implementer, I want the renderer to read the canonical post files directly so that later API and alternate implementations build on the same repository truth.

## Core Requirements
- The slice must render read-only web views directly from the canonical post files already stored in `records/posts/`.
- The slice must provide at least a board-tag index, a thread view, and a post permalink view over the existing sample dataset.
- The slice must present deterministic grouping and ordering from the current repository state.
- The slice must avoid introducing write flows, HTTP API surfaces, signing logic, moderation logic, or durable derived index policy.

## Shared Component Inventory
- Existing UI surfaces: none; this slice creates the first canonical human-facing read interface.
- Existing API surfaces: none; API work remains deferred to the next checklist item.
- Existing data surfaces: reuse the canonical post files in `records/posts/` and the baseline record shape in `docs/specs/canonical_post_record_v1.md` as the source of truth for rendering.
- Existing backend surfaces: none; the reader logic created here should stay close to the canonical file format so later shared read logic can grow from it.

## Simple User Flow
1. A user opens the local read-only web interface.
2. The user views a board-tag index and chooses a thread.
3. The interface renders the thread root and replies from the canonical post files.
4. The user opens a permalink for a specific post within the thread.

## Success Criteria
- A user can browse the sample dataset through normal web pages rather than raw file inspection only.
- The board-tag index clearly exposes threads from the existing repository content.
- A thread page clearly renders at least one root post and its replies from the canonical files.
- A permalink page can locate and show an individual post from the sample dataset.
