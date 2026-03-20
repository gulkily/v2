## Problem Statement
Choose the simplest way to add site-wide dark mode that follows the user’s device/browser preference by default without creating inconsistent page-by-page styling.

### Option A: Add shared light/dark design tokens and switch them with `prefers-color-scheme`
- Pros:
  - Best fit for the request because it enables dark mode automatically when the browser/device prefers it.
  - Keeps the change site-wide and consistent by reusing the existing shared CSS variables and common templates.
  - Small enough to ship without introducing new account settings or client-state complexity.
- Cons:
  - Requires auditing existing hard-coded colors so they all flow through shared tokens.
  - Some decorative gradients and panel treatments may need light redesign rather than simple inversion.

### Option B: Add a manual dark-mode toggle with saved local preference, plus browser-preference fallback
- Pros:
  - Gives users explicit control in addition to automatic defaulting.
  - Creates a foundation for future appearance settings.
- Cons:
  - Larger scope than requested because it adds new UI, persistence, and preference-resolution rules.
  - Increases testing surface across pages and navigation states.

### Option C: Apply dark mode only to a few high-traffic pages first
- Pros:
  - Lowest immediate effort.
  - Can surface obvious contrast issues quickly.
- Cons:
  - Produces an inconsistent experience because shared chrome and secondary pages would remain light.
  - Conflicts with the expectation that the site respects system dark mode broadly, not only in selected views.

## Recommendation
Recommend Option A: add shared light/dark design tokens and switch them with `prefers-color-scheme`.

This matches the requested behavior directly, keeps the implementation focused on shared styling instead of new preference UI, and avoids shipping a partial dark mode that feels inconsistent across the site.
