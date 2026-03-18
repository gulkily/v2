## Problem
The current compose pages do not clearly explain the posting requirements and limitations, especially the ASCII-only constraint and why it exists, while the current `/instance/` page is a narrow facts page rather than a broader project-information surface. The next slice should add concise compose-time guidance about ASCII limitations and rationale, and replace the current instance page with a renamed project-information page that preserves key instance facts while adding explanatory FAQ-style content.

## User Stories
- As a user, I want the compose page to clearly explain the ASCII limitation so that I understand the writing constraints before I submit a post.
- As a user, I want the compose page to explain why ASCII is required so that the rule feels purposeful rather than arbitrary, including readability, easier human handling, and avoiding Unicode obfuscation.
- As a reader, I want a project-information page instead of a narrow instance-facts page so that I can understand what this project is, how it works, and what assumptions it makes.
- As an operator, I want the current public instance facts to remain visible on that page so that the practical deployment details are not lost during the rename.
- As a maintainer, I want the new explanatory content to stay concise and curated so that it improves orientation without turning into a large standalone documentation subsystem.

## Core Requirements
- The slice must add clear posting requirements and limitations to the compose page, including the ASCII limitation.
- The slice must explain why ASCII is required, with rationale such as easier human handling of canonical text records, better readability, and reducing Unicode obfuscation risks.
- The slice must place that guidance directly on compose surfaces rather than only linking away to another page.
- The slice must replace the current instance-info framing with a project-information page or equivalent renamed destination.
- The slice must preserve the most useful existing instance facts on the renamed page, including public metadata already sourced from `records/instance/public.txt` and derived repository facts.
- The slice must add a compact FAQ-style or anticipatory explanatory section to the project-information page.
- The slice must keep the content concise and high-signal rather than expanding into a full multi-page documentation system.

## Shared Component Inventory
- Existing compose surface: extend `render_compose_page(...)` in `forum_web/web.py` and `templates/compose.html` so requirements and rationale appear in the current compose shell.
- Existing browser normalization behavior: align the new guidance with the current ASCII normalization and unsupported-character handling already present in `templates/assets/browser_signing.js`.
- Existing compose tests: extend `tests/test_compose_thread_page.py`, `tests/test_compose_reply_page.py`, and related compose coverage rather than creating separate one-off page contracts.
- Existing instance-info route: adapt `/instance/` in `forum_web/web.py` into the renamed project-information page rather than adding a second overlapping informational route.
- Existing instance template: evolve `templates/instance_info.html` or replace it with a renamed project-information template that can carry both facts and explanatory FAQ content.
- Existing public metadata loader: keep reusing `load_instance_info(...)` and the current repository-derived facts instead of inventing a second data source for the informational page.

## Simple User Flow
1. A user opens a compose page and immediately sees a concise explanation of the posting requirements, including the ASCII limitation and why it exists.
2. The user writes a post with that guidance visible near the compose form and understands how the browser normalization behavior relates to the rule.
3. A reader opens the renamed project-information page and sees a broader explanation of the project, its constraints, and its assumptions.
4. The same page still shows the key public instance facts and adds a compact FAQ-style section that answers likely orientation questions.

## Success Criteria
- Compose pages clearly state the ASCII limitation and its rationale.
- The rationale explicitly mentions human readability or operability and Unicode-obfuscation reduction.
- The current instance page is replaced by a project-information page with clearer framing.
- Key existing instance facts remain visible on the renamed page.
- The renamed page includes compact explanatory FAQ-style content.
- The overall change improves orientation without introducing a large new documentation surface.
