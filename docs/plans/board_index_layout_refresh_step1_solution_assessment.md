## Problem Statement
Choose the smallest useful way to replace the current board-index homepage with the cleaner, friendlier ZenMemes-style layout from `/home/wsl/zenmemes` without turning the next loop into a separate marketing site or a full-app visual rewrite.

### Option A: Rework the existing `/` board index into the new layout
- Pros:
  - Best fit for "implement this layout instead of the current one" because the current homepage already lives at `/`.
  - Reuses the existing board-index route, repository-backed thread data, and tested destination links such as compose, instance info, moderation, and task priorities.
  - Keeps scope focused on one surface: the homepage structure, copy, and styling.
  - Lets the ZenMemes mock be adapted to real product capabilities instead of copying placeholder content literally.
- Cons:
  - The current shared hero-based shell may need light reshaping or homepage-specific treatment.
  - Some mock elements will need translation into existing concepts because the repo does not currently expose all of the sample nav, voting, or ranking behaviors shown in `~/zenmemes`.

### Option B: Add a separate ZenMemes landing page and keep the current board index elsewhere
- Pros:
  - Easiest way to match the generated mock closely with a dedicated template and isolated CSS.
  - Minimizes immediate pressure on existing shared templates.
- Cons:
  - Does not satisfy the request as directly because it adds a new front door instead of replacing the current homepage.
  - Splits user entry points between a marketing-like page and the real board index.
  - Risks duplicating navigation, thread summaries, and action links across two home surfaces.

### Option C: Use the ZenMemes design as the start of a full-site visual system rewrite
- Pros:
  - Produces the most consistent visual language across board, thread, compose, and profile pages.
  - Avoids a homepage that looks unrelated to the rest of the app.
- Cons:
  - Much larger scope than the user story.
  - Pulls Step 2 and Step 3 into cross-page design-system work instead of a focused homepage replacement.
  - Increases regression risk across established pages and tests before the new front-page direction is proven.

## Recommendation
Recommend Option A: rework the existing `/` board index into the new layout.

This is the smallest coherent slice and matches the request most directly. The `~/zenmemes` output is useful as a structural and tonal reference: persistent header/navigation, text-first ranked thread rows, calmer typography, and a right-rail sidebar. The next steps should treat it as an adaptation target, not a literal spec. That means preserving current forum capabilities and tested links, mapping live repository data into the new layout, and deferring unsupported behaviors such as full vote mechanics, fictional topic taxonomies, or a broader site-wide redesign.
