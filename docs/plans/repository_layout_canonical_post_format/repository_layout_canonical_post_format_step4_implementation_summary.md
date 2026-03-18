## Stage 1 - Minimal repository layout
- Changes:
  - Added the `records/` root for canonical forum records.
  - Added `records/posts/` as the minimal location for canonical post payload files.
  - Added orientation docs so contributors can find the canonical post storage path immediately.
- Verification:
  - Manually inspected the new `records/` tree and confirmed the post storage location is discoverable from the repository alone.
- Notes:
  - This stage intentionally avoids defining the post payload format or adding sample post data.

## Stage 2 - Minimal canonical post record shape
- Changes:
  - Added a standalone spec for the first-slice post file format in `docs/specs/`.
  - Defined the minimal header/body shape needed to represent thread roots, replies, and board tags.
  - Kept hashing, signing, transport, and moderation out of scope for this slice.
- Verification:
  - Manually read the spec and confirmed the root and reply examples are understandable from raw text alone.
- Notes:
  - The identifiers in this slice are simple local post IDs for sample data, not the final long-term identity scheme.

## Stage 3 - Sample canonical post dataset
- Changes:
  - Added one thread root sample file in `records/posts/root-001.txt`.
  - Added one reply sample file in `records/posts/reply-001.txt`.
  - Kept the dataset hand-authored and small enough to inspect directly in raw text and git history.
- Verification:
  - Opened both sample files directly and confirmed the root, reply linkage, and board tags are understandable without custom tooling.
  - Checked the `records/posts/` directory to confirm the dataset is easy to locate from the repository tree.
- Notes:
  - The sample dataset is illustrative only and should not be treated as the final canonical identifier scheme.
