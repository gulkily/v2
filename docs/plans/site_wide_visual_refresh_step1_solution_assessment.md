## Problem Statement
Choose the smallest useful way to redesign the rest of the site to match the new homepage style, while also removing the homepage's "Browse by board tag" section, without turning the next loop into an open-ended design-system rewrite.

### Option A: Extend the new homepage style into a shared site-wide shell and update the remaining templates
- Pros:
  - Best fit for the request because the homepage style already exists and the remaining pages mostly flow through the same shared renderer and template set.
  - Keeps the work coherent: thread, post, compose, profile, moderation, instance, and planning pages can align around one visual language instead of drifting page by page.
  - Lets the homepage board-tag section be removed as part of the same layout cleanup rather than treated as a separate feature.
  - Encourages reuse of shared shell, typography, spacing, and panel treatments instead of creating parallel styling patterns.
- Cons:
  - Still touches many pages, so careful scope control is needed.
  - Some specialized surfaces such as compose and task-priority tables may need page-specific adaptations to fit the new style cleanly.

### Option B: Restyle each remaining page independently while leaving the shared shell mostly as-is
- Pros:
  - Allows highly tailored treatment for each surface.
  - Can reduce pressure to settle shared patterns up front.
- Cons:
  - Higher risk of visual inconsistency across the app.
  - Duplicates effort across templates and CSS because the same structural decisions get solved repeatedly.
  - Makes the "match this style" goal harder to enforce since each page can drift.

### Option C: Pause and do a broader design-system/framework pass before restyling the remaining pages
- Pros:
  - Could produce the cleanest long-term foundation if many more UI changes are expected soon.
  - Gives maximum control over tokens, component naming, and layout conventions.
- Cons:
  - Larger scope than the current request.
  - Delays the visible redesign of the remaining pages.
  - Risks turning a concrete restyle request into architecture work that is not yet proven necessary.

## Recommendation
Recommend Option A: extend the new homepage style into a shared site-wide shell and update the remaining templates.

This is the smallest coherent slice that matches the request directly. The site already has a workable shared renderer and a new homepage visual direction, so the next loop should standardize that direction across the existing pages, remove the now-unneeded homepage board-tag directory, and keep the work focused on presentation alignment rather than a larger UI architecture rewrite.
