## Stage 1
- Goal: establish the minimal canonical repository layout for post storage and sample data.
- Dependencies: approved Step 2 only.
- Expected changes: add the initial directories and any small orientation docs needed so contributors can find canonical post records; no UI, API, signing, moderation, or derived indexes.
- Verification approach: manually inspect the tree and confirm a new contributor can identify where canonical post files belong.
- Risks or open questions:
  - deciding too much future record structure too early
  - leaving the layout too vague for later loops
- Canonical components/API contracts touched: canonical repository layout only.

## Stage 2
- Goal: define the minimal canonical post record shape for this first slice.
- Dependencies: Stage 1.
- Expected changes: document the raw post text form used by the sample dataset, including header/body separation, ASCII-only expectations, and the minimum fields needed to show thread root, reply linkage, and board tags; no signing or transport envelopes.
- Verification approach: manually read the format description and confirm it is understandable without custom tooling.
- Risks or open questions:
  - overfitting the first draft to later protocol details
  - underspecifying fields needed by future readers
- Canonical components/API contracts touched: canonical post record format.

## Stage 3
- Goal: add a tiny hand-authored sample dataset that proves the layout and record shape work in git.
- Dependencies: Stage 2.
- Expected changes: create at least one thread root and one reply as canonical ASCII post files using the agreed layout and format; include board tags and obvious reply relationships.
- Verification approach: open the sample files directly, inspect them in git, and confirm the raw text alone makes the thread structure understandable.
- Risks or open questions:
  - sample data may accidentally imply unapproved future behaviors
  - naming and placement conventions may need refinement in later loops
- Canonical components/API contracts touched: canonical repository layout and canonical post record format.
