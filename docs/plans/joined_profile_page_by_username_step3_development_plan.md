## Stage 1
- Goal: define the canonical username-to-profile resolution helper for latest current usernames across resolved identity sets.
- Dependencies: approved Step 2; existing identity resolution in `forum_web/profiles.py`; existing profile-update record family and current display-name derivation.
- Expected changes: add one narrow read helper that derives the latest current username for each resolved identity set, normalizes the public username-route token, and resolves a `/user/<username>` request only when it maps unambiguously to one canonical profile; planned contracts such as `resolve_profile_by_username(username, *, repo_root, posts, identity_context) -> ProfileSummary | None` and `username_route_token(display_name) -> str`.
- Verification approach: build fixtures with merged identities and current profile updates, confirm a latest current username resolves to one canonical profile summary, confirm renamed-away usernames stop resolving, and confirm ambiguous matches return no profile result instead of guessing.
- Risks or open questions:
  - defining the smallest deterministic normalization rule for username route tokens without reopening full username policy
  - keeping resolution conservative when multiple resolved identity sets currently share one visible username
- Canonical components/API contracts touched: resolved profile-summary derivation; profile-update current-name resolution; new username-route lookup contract.

## Stage 2
- Goal: add the public `/user/<username>` page and render joined profile data, including multiple usernames when merged members still differ.
- Dependencies: Stage 1; existing profile page/template contract; existing profile summary and identity context loaders.
- Expected changes: add one new public route such as `/user/<username>`, render the same underlying joined profile information as `/profiles/<identity-slug>`, and extend the profile page data contract so the joined page can show all usernames in the merged set when no single unified name has been explicitly chosen; planned contracts such as `render_username_profile(username) -> str` and `load_profile_usernames(summary, identity_context) -> tuple[str, ...]`.
- Verification approach: load `/user/<username>` for a merged profile with one current username and for a merged profile whose member identities still imply multiple usernames, confirm the page renders the joined profile in both cases, and confirm unknown or ambiguous usernames return the current missing-resource behavior.
- Risks or open questions:
  - choosing the smallest joined-page presentation for multiple usernames without redesigning the full profile layout
  - avoiding drift between the username-based page and the identity-based profile page if both render the same underlying summary
- Canonical components/API contracts touched: `/profiles/<identity-slug>` profile renderer/template; new `/user/<username>` route; joined profile username-display contract.

## Stage 3
- Goal: update attribution links so normal browsing prefers the username-based route when it is safe, with fallback to identity-based profile links.
- Dependencies: Stage 2.
- Expected changes: extend post and moderation attribution link generation so they prefer `/user/<username>` when the resolved profile has one unambiguous latest current username and otherwise continue linking to `/profiles/<identity-slug>`; add focused regression coverage for both the username-first and fallback cases; planned contracts such as `preferred_profile_href(identity_id, *, identity_context, repo_root, posts) -> str` and `preferred_profile_label(...) -> str`.
- Verification approach: render posts and moderation cards for profiles with one unambiguous latest current username, confirm attribution links point to `/user/<username>`; render fixtures with ambiguous or unresolved username mappings, confirm attribution links still point to `/profiles/<identity-slug>`; confirm direct `/user/<username>` reads and existing `/profiles/<identity-slug>` reads stay consistent.
- Risks or open questions:
  - keeping attribution behavior deterministic when username state changes after merges or renames
  - avoiding accidental broken links if username normalization and page routing diverge
- Canonical components/API contracts touched: post attribution links; moderation attribution links; canonical profile href selection logic; username-route regression coverage.
