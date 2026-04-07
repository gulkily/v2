## Problem Statement
Choose the smallest coherent way to add timestamps to the home page thread listing without disrupting the current compact board index layout or introducing a new data model.

### Option A: Add one visible thread timestamp per row based on thread recency
- Pros:
  - Best fit for the current home page because each row already has a compact metadata line where one timestamp can be added cleanly.
  - Matches the board index's existing recency ordering, so the displayed time explains why a thread appears where it does.
  - Keeps scope narrow for both the server-rendered page and the PHP/native snapshot path.
  - Gives users clear timing context without substantially changing the density of the listing.
- Cons:
  - A single timestamp is less explicit about whether it represents creation time or latest activity.
  - Recently edited older threads can look newer than first-time readers might expect.

### Option B: Show both created and updated timestamps on every row
- Pros:
  - Most explicit presentation because users can distinguish original creation from latest update.
  - Reduces ambiguity for threads that were edited after creation.
- Cons:
  - Heavier visual footprint on the home page and more likely to crowd the existing compact row design.
  - Larger contract change for rendering paths that currently only need lightweight thread metadata.
  - More scope than the request requires.

### Option C: Add only relative ages such as "2h ago" or hide exact times behind secondary UI
- Pros:
  - Keeps the listing visually light.
  - Can feel more scannable than full timestamps.
- Cons:
  - Less direct than the request to include timestamps.
  - Relative time becomes less precise and can drift or feel inconsistent without refresh behavior.
  - Secondary UI such as tooltips or details-on-hover is weaker for static and read-only surfaces.

## Recommendation
Recommend Option A: add one visible thread timestamp per row based on thread recency.

This is the smallest coherent change. The home page already orders threads by indexed recency, so one visible timestamp makes that ordering legible without turning each row into a dense metadata block. In the next step, the feature description should lock down the exact label semantics so the timestamp is unambiguous in the UI.
