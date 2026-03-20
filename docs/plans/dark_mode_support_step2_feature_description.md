## Problem
The site currently renders only a light theme, which can feel harsh or out of place for users whose device or browser is already configured for dark mode. The next slice should add consistent site-wide dark mode and automatically enable it when the user’s system preference is dark.

## User Stories
- As a user, I want the site to follow my device/browser dark-mode preference so that it feels native without extra setup.
- As a user, I want dark mode to apply consistently across shared site chrome and page content so that pages do not feel mismatched.
- As a maintainer, I want dark mode to reuse shared styling patterns so that future page changes do not require separate light/dark rewrites.

## Core Requirements
- The site must support both light and dark presentation across the shared shell and main page surfaces.
- Dark mode must become active by default when the browser/device reports a dark color-scheme preference.
- The default light-mode experience must remain intact for users whose environment prefers light mode.
- Shared visual elements such as panels, typography, links, dividers, chips, and backgrounds must remain readable and coherent in both modes.
- The feature must use shared styling primitives rather than page-by-page one-off theme handling.

## Shared Component Inventory
- Existing shared stylesheet [site.css](/home/wsl/v2/templates/assets/site.css): extend the canonical color and surface system here because it already controls the site-wide shell, panels, navigation, and common components.
- Existing shared page renderer and header/footer templates in [web.py](/home/wsl/v2/forum_web/web.py) and base templates: reuse unchanged where possible because dark mode should come primarily from shared styling rather than new page-specific markup.
- Existing page templates under [/home/wsl/v2/templates](/home/wsl/v2/templates): reuse the current template set and only adjust markup where a surface cannot inherit dark mode cleanly from shared styles.
- Existing browser assets loaded across account/compose/profile flows: reuse unless a specific asset has hard-coded inline visual assumptions that need extension for theme consistency.

## Simple User Flow
1. A user opens the site in a browser whose preferred color scheme is dark.
2. The site automatically renders in dark mode across the shared shell and page content.
3. The same user opens another major page and sees the same dark presentation patterns applied consistently.
4. A different user whose environment prefers light mode continues to see the current light presentation.

## Success Criteria
- Browsers with dark color-scheme preference render the site in dark mode without any manual toggle.
- Browsers with light color-scheme preference continue to render the current light-mode experience.
- Shared UI surfaces remain legible and visually coherent across major pages in both modes.
- Dark mode is driven by shared styling primitives rather than a patchwork of page-specific overrides.
