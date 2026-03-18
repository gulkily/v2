## Problem Statement
Choose the smallest coherent way to add clear compose-time posting requirements, especially ASCII limitations and rationale, while replacing the current instance-info page with a broader project-information page that keeps core instance facts and adds explanatory FAQ-style content.

### Option A: Treat this as one documentation-focused information architecture slice
- Pros:
  - Best fit for the request because it updates both user-facing explanation surfaces together: compose guidance where users write, and a broader project-information page where users orient themselves.
  - Keeps the messaging consistent across the app about ASCII limits, canonical text records, human readability, and anti-obfuscation goals.
  - Reuses the existing compose page and instance-info route/page instead of introducing more destinations.
  - Lets the current instance facts survive as one section inside a renamed, more explanatory page.
- Cons:
  - Requires deciding how much policy text belongs inline on compose versus on the project-information page.
  - Slightly broader than a single-page copy edit because it changes page framing and naming in two places.

### Option B: Limit the slice to compose-page guidance only and defer the project-information page
- Pros:
  - Smallest implementation scope.
  - Solves the most immediate user need at the exact moment of writing a post.
- Cons:
  - Does not satisfy the request to replace the instance page with a broader project-information page.
  - Leaves the app with split or incomplete explanatory content about the project’s rules and rationale.
  - Misses the chance to rename the current “Instance” concept into something more understandable for regular users.

### Option C: Build a new project-information page and keep compose guidance minimal with links out
- Pros:
  - Keeps the compose page visually lighter.
  - Creates one obvious place for long-form rationale, limitations, and explanatory FAQ content.
- Cons:
  - Does not satisfy the request as directly because the compose page itself would still lack clear requirements and limitations.
  - Forces users to leave the writing flow to understand basic posting constraints.
  - Risks making the posting rules feel optional instead of part of the compose contract.

## Recommendation
Recommend Option A: treat this as one documentation-focused information architecture slice.

This is the smallest approach that fully satisfies the request. The next steps should keep it disciplined: add concise high-signal ASCII requirements and rationale directly on the compose page, rename the instance page into a broader project-information page, preserve the most useful existing instance facts there, and add a compact explanatory FAQ rather than a large general documentation section.
