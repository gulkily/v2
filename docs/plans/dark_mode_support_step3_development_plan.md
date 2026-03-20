## Stage 1
- Goal: add one shared light/dark theme foundation that follows browser `prefers-color-scheme`.
- Dependencies: approved Step 2; existing shared CSS variables and site-wide stylesheet structure.
- Expected changes: introduce canonical dark-mode color/surface tokens in the shared stylesheet; wire the shared shell to switch tokens from light to dark through `prefers-color-scheme`; keep current light-mode values as the default baseline.
- Verification approach: load a representative page with light and dark browser preference states and confirm the shared shell, page background, text, and navigation switch coherently.
- Risks or open questions:
  - hard-coded colors may bypass shared tokens and remain visually incorrect in dark mode
  - some existing gradients may need redesign rather than simple token substitution
- Canonical components/API contracts touched: shared stylesheet `site.css`; shared page shell/header/footer styling.

## Stage 2
- Goal: extend the theme foundation across common content components and high-traffic pages.
- Dependencies: Stage 1.
- Expected changes: update canonical shared components such as panels, section dividers, chips, buttons, links, code surfaces, and details panels to remain legible in both modes; adjust any page markup only where a surface cannot inherit correctly from the shared theme.
- Verification approach: manually smoke-test major pages such as home, thread, post, compose, profile, activity, and instance in dark mode and light mode to confirm readable contrast and consistent component treatment.
- Risks or open questions:
  - isolated template-level inline assumptions may create page-specific contrast regressions
  - emphasis states such as hover, active, muted, and status notes may need separate tuning in dark mode
- Canonical components/API contracts touched: `site.css`; existing templates under `templates/`; shared component classes already used across page templates.

## Stage 3
- Goal: add regression coverage and final accessibility/consistency cleanup for dark mode defaults.
- Dependencies: Stage 2.
- Expected changes: add focused tests for the shared stylesheet or rendered pages to confirm dark-mode support is present and the light-mode baseline remains intact; make any final contrast or readability adjustments discovered during manual review.
- Verification approach: run targeted page tests plus manual browser checks with both light and dark color-scheme preferences; confirm there is no new toggle requirement and dark mode activates automatically from browser preference.
- Risks or open questions:
  - automated tests may prove stronger at checking presence of theme hooks than visual quality, so manual review still matters
  - small decorative surfaces may be missed without broad page sampling
- Canonical components/API contracts touched: page rendering tests for major routes; shared stylesheet/theme hooks; any small template adjustments required by smoke-test findings.
