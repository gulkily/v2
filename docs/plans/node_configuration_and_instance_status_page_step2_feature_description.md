## Problem
The forum exposes some instance behavior indirectly through `.env`, moderation behavior, and repository-backed pages, but there is no single in-product place that tells a reader or operator what this instance is, who runs it, what moderation/retention posture it uses, or which build and install state is currently live. The next slice should add one obvious public page for current instance-level facts without turning it into a broader admin console or operational dashboard.

## User Stories
- As a reader, I want one obvious page that explains this instance's policies and operator identity so I can evaluate the forum before participating.
- As an admin, I want current instance facts published from canonical local configuration and repository state so I do not have to keep separate documentation in sync by hand.
- As a moderator or reviewer, I want moderation settings and related operator contact details visible in one place so public-instance governance is legible.
- As a future implementer, I want the instance-info surface to reuse existing page and routing patterns so the feature does not fork into a separate UI system.

## Core Requirements
- The slice must add one public-facing instance status/configuration page that is easy to reach from the main board index.
- The page must publish a defined set of instance-level facts, including retention policy, moderation settings, admin or contact information, current commit ID, install date, and other explicitly chosen public instance metadata.
- The page must render current values from canonical local sources such as runtime configuration, repository state, or tracked instance metadata rather than from hand-maintained prose alone.
- The page must represent missing or unset public values explicitly instead of silently omitting them.
- The slice must stay read-only and informational; it must not add private admin controls, editing workflows, or deeper operational telemetry.

## Shared Component Inventory
- Existing main entry surface: extend the board index action row in [templates/board_index.html](/home/wsl/v2/templates/board_index.html) so the new page is linked from the main page instead of hidden behind a new navigation system.
- Existing page shell: reuse the shared page rendering flow in [forum_read_only/web.py](/home/wsl/v2/forum_read_only/web.py) and [templates/base.html](/home/wsl/v2/templates/base.html) so the instance page follows the same public read-only presentation model as the board index, thread view, and moderation log.
- Existing public read-only route set: extend the current read-only web app with one new canonical route for instance information rather than creating a separate admin-only app or standalone static file.
- Existing configuration surfaces: reuse runtime environment loading from [forum_core/runtime_env.py](/home/wsl/v2/forum_core/runtime_env.py), the moderator allowlist contract in [forum_core/moderation.py](/home/wsl/v2/forum_core/moderation.py), and repository-backed metadata where available; new instance facts should plug into these canonical sources instead of duplicating them in templates.
- Existing supporting surfaces: keep docs and `.env.example` as supporting operator references only; they are not the canonical human-facing instance summary and should not replace the new page.

## Simple User Flow
1. A reader lands on the board index and sees a clear link to the instance status/configuration page.
2. The reader opens that page and sees the current public instance facts grouped in one place.
3. The page shows the instance's policy and operator facts, including moderation and retention posture, contact/admin details, and deployment identity such as commit ID and install date.
4. When the local canonical configuration or instance metadata changes, the page reflects the updated values on the next render without requiring a manually rewritten overview page.

## Success Criteria
- A first-time reader can find the instance information page directly from the board index in one click.
- The page shows the agreed public fact set in one place, including retention policy, moderation settings, admin/contact information, commit ID, and install date.
- Published values come from canonical local sources, and unset values are labeled clearly rather than disappearing.
- The feature reuses the existing public read-only page stack and does not introduce admin mutation controls or a second UI system.
