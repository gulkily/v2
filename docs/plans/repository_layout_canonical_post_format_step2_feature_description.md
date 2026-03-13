## Problem
The project needs a smallest useful first slice that proves its text-native, git-native forum model works in practice before read APIs, rendering, identity richness, or moderation are introduced.

## User Stories
- As a builder, I want a canonical on-disk layout for posts so that later implementations read and write the same repository structure.
- As a human reviewer, I want sample forum records to be understandable directly in raw text so that the data model can be judged without special tooling.
- As a future backend implementer, I want a minimal canonical post format so that Perl, Python, and other implementations can target the same baseline behavior.
- As a future UI or API author, I want stable sample data in git so that early readers and fixtures can be built on top of something concrete.

## Core Requirements
- The slice must define the minimal repository layout needed to store canonical post records in ASCII text files tracked by git.
- The slice must define a canonical post record shape that is readable in raw form and suitable for stable identification later.
- The slice must include a tiny sample dataset of hand-authored posts that demonstrates thread roots, replies, and board tags.
- The slice must avoid introducing read APIs, HTML rendering, signing workflows, moderation flows, or derived indexes beyond what is strictly needed for the sample data.

## Shared Component Inventory
- Existing UI surfaces: none; this slice creates data that later UI work will consume.
- Existing API surfaces: none; this slice creates data and structure that later API work will expose.
- Existing backend surfaces: none; this slice defines the baseline repository and record conventions that future backends must reuse.
- Existing auth surfaces: none; signing and identity are intentionally deferred beyond the minimal record shape needed for future compatibility.

## Simple User Flow
1. A builder creates the minimal repository directories for canonical post storage.
2. The builder writes a small set of sample post files using the canonical text format.
3. The sample files are committed to git as inspectable baseline forum data.
4. A reviewer opens the files directly and confirms that thread structure and board tagging are understandable from raw text alone.

## Success Criteria
- A new contributor can inspect the repository and immediately find where canonical post records live.
- Sample post files are readable as plain ASCII text without custom tooling.
- The sample dataset clearly demonstrates at least one thread root and one reply.
- Later loops can reference this dataset as the baseline for read-only UI, API, and parser work without redefining the storage shape.
