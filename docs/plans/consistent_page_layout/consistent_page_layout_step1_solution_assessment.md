## Problem Statement
Choose the smallest useful way to give all web pages a consistent layout without turning the next loop into a full visual redesign or a broad frontend rewrite.

### Option A: Standardize every page on one shared page shell and refit outlier pages into it
- Pros:
  - Best fit for the user story because it targets consistency across all pages rather than polishing one surface at a time.
  - Matches the current app shape, which already has a shared base template plus distinct front-page treatment that can be unified.
  - Keeps the next steps focused on layout structure, shared header/footer/navigation, and page-width rules instead of deeper feature work.
  - Reduces the chance that future pages drift again because the common shell becomes the default path.
- Cons:
  - Requires touching multiple templates in one loop.
  - Some homepage and activity-specific styling will need adaptation so the pages keep their content priorities while aligning to the shared shell.

### Option B: Normalize pages incrementally, starting with the most visibly inconsistent screens
- Pros:
  - Smallest immediate implementation slice because only a subset of templates changes first.
  - Lowers short-term regression risk on pages that already look acceptable.
- Cons:
  - Only partially satisfies the user story because the product will still have mixed layouts after the next loop.
  - Makes it easier to keep carrying multiple layout patterns while the cleanup remains unfinished.
  - Creates ambiguity about which pages count as complete enough before calling the work done.

### Option C: Start a broader site-wide design-system and visual refresh effort
- Pros:
  - Could produce the strongest long-term consistency across layout, typography, spacing, and components.
  - Gives future features a more explicit UI foundation.
- Cons:
  - Larger scope than the current user story requires.
  - Pulls the next planning steps toward branding and component-library decisions instead of solving the concrete layout inconsistency.
  - Increases delivery time and regression surface before proving that the shared-shell cleanup is enough.

## Recommendation
Recommend Option A: standardize every page on one shared page shell and refit outlier pages into it.

This is the smallest coherent approach that actually fulfills "consistent layout on all pages." The repo already has a reusable base template and shared site CSS, so the next step should define one canonical shell for header, footer, navigation, and page-width behavior, then list the page-specific exceptions that still need to fit inside that structure.
