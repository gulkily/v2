## Stage 1
- Goal: define the minimal read model for “current signed user profile” lookup without introducing a server-side account session.
- Dependencies: approved Step 2; existing identity resolution/profile summary helpers; existing browser-local signing key behavior.
- Expected changes: add one narrow helper path that derives a canonical profile target for the locally managed identity or returns no target when the app cannot determine one; thread that resolved profile slug or identity ID into page-render context without changing profile, merge, or username-update semantics; planned contracts such as `resolve_current_profile_target(environ, identity_context) -> CurrentProfileTarget | None` and `build_current_profile_link(target) -> tuple[str, str] | None`.
- Verification approach: exercise the resolution path with a known manageable identity, confirm it returns the canonical profile slug for a resolved identity set, and confirm anonymous or unknown-identity cases return no profile target instead of a broken link.
- Risks or open questions:
  - choosing the smallest trustworthy source for “current user” in a product that does not have a normal auth/session model
  - making sure linked identities resolve to the canonical profile slug rather than a member alias
- Canonical components/API contracts touched: profile-summary resolution; identity canonicalization helpers; request/page context for shared layout rendering.

## Stage 2
- Goal: expose the `My profile` affordance through the shared site header/navigation using the Stage 1 target.
- Dependencies: Stage 1; existing shared header renderer in `forum_web/templates.py`; existing page renderers that already rely on the shared header.
- Expected changes: extend the shared primary navigation/header contract so it can optionally render a signed-user `My profile` link when a current profile target is available, keep the rest of the global nav unchanged, and ensure the link resolves to `/profiles/<identity-slug>` as the canonical self-service home; planned contracts such as `render_primary_nav(*, current_profile_href: str | None = None) -> str` and `render_site_header(..., current_profile_href: str | None = None) -> str`.
- Verification approach: load representative pages with and without a current profile target, confirm the `My profile` link appears only for the signed-user case, and confirm the link lands on the existing profile page where `update username` and `manage merges` remain available.
- Risks or open questions:
  - deciding which page flows should carry the signed-user profile target without creating inconsistent navigation across the app
  - preserving current header layout and copy when the optional nav item is absent
- Canonical components/API contracts touched: shared site header; primary navigation HTML contract; canonical `/profiles/<identity-slug>` profile route.

## Stage 3
- Goal: add regression coverage for profile-link rendering across signed-user, anonymous, and profile-led page flows.
- Dependencies: Stage 2.
- Expected changes: add focused tests covering the shared header/nav output, at least one general app page with a current profile target, and no-target cases where `My profile` should stay hidden; extend existing profile-page tests only where needed to prove the new entry point complements rather than replaces the current `update username` and `manage merges` links; planned contracts such as `test_page_renders_my_profile_link_for_current_identity()` and `test_page_hides_my_profile_link_without_current_identity()`.
- Verification approach: run the targeted page tests, confirm signed-user pages render one `My profile` link to the canonical slug, confirm anonymous pages do not render it, and confirm profile/update/merge routes keep their current links and behavior.
- Risks or open questions:
  - avoiding brittle tests if the shared header markup changes in unrelated visual work
  - choosing the smallest fixture setup that still proves canonical-slug resolution for linked identities
- Canonical components/API contracts touched: shared page/header test coverage; existing profile page route; profile-update and merge-management page link contracts.
