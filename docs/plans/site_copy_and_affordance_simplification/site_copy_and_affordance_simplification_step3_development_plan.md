## Stage 1
- Goal: remove or hide unfinished homepage affordances and other shared low-value navigation cues that do not lead to real user outcomes.
- Dependencies: approved Step 2; existing homepage renderer/template; shared shell helpers.
- Expected changes: simplify homepage header/sidebar affordances so non-functional tag-link navigation and similar misleading cues are hidden or replaced with inert copy-free presentation; lightly simplify shared helper output where the same unfinished affordance appears in more than one place.
- Verification approach: manually load `/` and confirm the homepage still exposes the core actions while no longer showing tag links or other misleading navigation hints.
- Risks or open questions:
  - avoiding over-pruning homepage context until the remaining primary actions still feel obvious
  - deciding whether a non-functional affordance should be removed entirely or rendered as plain text
- Canonical components/API contracts touched: `render_board_index_header(...)`; `templates/board_index.html`; shared affordance markup in `forum_web/web.py`.

## Stage 2
- Goal: simplify read and planning pages by removing repeated section copy, low-value headings, and metadata text that the layout already communicates.
- Dependencies: Stage 1; existing thread, profile, moderation, instance, and planning templates.
- Expected changes: reduce repeated descriptive copy and non-essential section framing across representative read/planning templates while preserving key actions, facts, and routing context; likely surfaces include thread, profile, instance info, task priorities, and task detail pages.
- Verification approach: manually open representative read/planning pages and confirm they remain understandable while showing less repeated explanation and fewer redundant labels.
- Risks or open questions:
  - preserving enough context for structured pages like profiles and task planning without leaving them verbose
  - deciding which explanatory text is still useful for first-time readers versus regular users
- Canonical components/API contracts touched: read/planning templates in `templates/*.html`; shared metadata/action render helpers used by those pages.

## Stage 3
- Goal: simplify write surfaces so compose and profile-update flows focus on the main action while hiding secondary scaffolding unless it is truly needed.
- Dependencies: Stage 1; existing compose/profile-update templates and browser-signing DOM hooks.
- Expected changes: trim explanatory copy around compose and profile-update flows, reduce redundant labels, and hide optional technical scaffolding by default where that keeps the main action clearer without changing hooks or behavior.
- Verification approach: manually open compose thread/reply/task and profile-update pages, confirm the primary action remains obvious, and confirm required ids/data attributes still render.
- Risks or open questions:
  - keeping enough guidance for users who do need to understand signing behavior
  - avoiding any copy changes that make error or status states feel ambiguous
- Canonical components/API contracts touched: `templates/compose.html`; `templates/profile_update.html`; browser-signing DOM contract and related helper copy.

## Stage 4
- Goal: add focused regression coverage for the removed affordances and simplified page framing.
- Dependencies: Stage 1 through Stage 3.
- Expected changes: update or add representative tests that assert unfinished homepage affordances are absent and that simplified read/write/planning pages still expose their key actions and hooks without the removed low-value text.
- Verification approach: run targeted unittest modules for homepage, compose, profile-update, task pages, and any representative read-page coverage, then do one manual smoke pass across the main routes.
- Risks or open questions:
  - keeping assertions stable when the goal is subtractive cleanup rather than new feature output
  - choosing representative copy/absence checks that catch regressions without becoming brittle
- Canonical components/API contracts touched: representative HTML responses across homepage, read, write, and planning routes; existing page test modules.
