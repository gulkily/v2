## Problem Statement
Choose the smallest useful way to publish retention policy, moderation settings, admin/contact info, commit ID, install date, and other instance-level facts in one obvious place without scattering the data across docs, templates, and ad hoc status surfaces.

### Option A: Add one dedicated instance status/configuration page in the product and link it from the main page
- Pros:
  - Gives admins and readers one obvious place to inspect instance-level facts.
  - Fits the requirement that the information reflect current configuration rather than stale documentation.
  - Lets the feature grow coherently as more instance metadata is added later.
  - Keeps policy, operator identity, and build/deploy facts together instead of forcing users to hunt through multiple views.
- Cons:
  - Requires defining which facts are canonical and how missing values are represented.
  - Introduces a new public-facing surface that must stay aligned with runtime configuration and repository state.
  - Needs a clear boundary between safe-to-publish instance facts and private operational data.

### Option B: Publish the same information in repository docs or a tracked text record only
- Pros:
  - Smallest documentation-only change.
  - Easy to version and review in git.
  - Avoids adding a new UI surface right away.
- Cons:
  - Does not create an obvious in-product location for users.
  - Drifts easily from live runtime settings and deployment facts.
  - Makes “real-time” updates dependent on manual edits and commits.

### Option C: Expose instance facts piecemeal through footer text, headers, and separate admin-oriented views
- Pros:
  - Allows incremental rollout of individual facts.
  - Some items such as commit ID or moderation state could be surfaced close to where they matter.
  - Can support machine-readable consumers if some facts also appear in API responses.
- Cons:
  - Fails the “one obvious place” requirement.
  - Produces fragmented ownership and inconsistent presentation.
  - Makes it harder to understand the full instance posture at a glance.

## Recommendation
Recommend Option A: add one dedicated instance status/configuration page in the product and link it from the main page.

This is the smallest coherent solution that satisfies the story as written. The next loop should stay strict about scope:

- publish only instance-level facts that are safe and useful to expose publicly,
- treat the page as the canonical human-facing summary of current instance configuration and deployment identity,
- keep static docs and scattered badges as supporting surfaces rather than the primary destination,
- leave deeper operational telemetry, private admin controls, and historical audit views for later work.
