## Stage 1
- Goal: add one dedicated browser key page as the canonical surface for local key viewing.
- Dependencies: approved Step 2; existing shared page/header rendering; existing browser key viewer pattern from compose-style pages.
- Expected changes: add one focused route and page renderer such as `/account/key/` or `/account/keys/`; introduce a dedicated template/context for local key status plus private/public key display; reuse the existing browser-storage data source and key-viewer presentation baseline rather than inventing a second key model; planned contracts such as `render_account_key_page() -> str`.
- Verification approach: load the new page directly, confirm it renders the key viewer/status area, and confirm it behaves as a local browser page even when no browser key is present.
- Risks or open questions:
  - choosing the narrowest stable route/copy so the page reads as account-local rather than public profile content
  - deciding whether the page needs any profile identity context or should stay purely device-local
- Canonical components/API contracts touched: shared page renderer; browser key storage/viewer asset contract; new dedicated account/key route.

## Stage 2
- Goal: remove key material from public profile pages and point existing account-related flows to the new canonical key page.
- Dependencies: Stage 1; existing profile page, profile update page, and merge-request action page surfaces.
- Expected changes: strip the key-material block from `/profiles/<identity-slug>`; add one clear link or affordance from the relevant account-related surfaces to the dedicated key page; keep compose-style key presentation canonical on pages that actively require signing, while avoiding duplicate long-term “home” pages for passive key viewing; planned contracts such as `render_profile_page(..., key_page_href: str | None = None) -> str`.
- Verification approach: open a public profile and confirm key material is gone; open the profile-update and merge-related surfaces and confirm they offer a stable path to the dedicated key page; confirm the new destination remains the only passive key-viewing page.
- Risks or open questions:
  - choosing which existing account-related pages should link to the key page without adding clutter
  - keeping the distinction clear between action-oriented signing flows and the passive key-viewing destination
- Canonical components/API contracts touched: `/profiles/<identity-slug>`; `/profiles/<identity-slug>/update`; merge-request action surface; canonical account/key page destination.

## Stage 3
- Goal: add regression coverage for the new key page and the removal of profile-page key material.
- Dependencies: Stage 2.
- Expected changes: add focused route/page tests for the dedicated key page; update profile-page assertions so key material no longer appears there; add narrow coverage proving the account-related surfaces point to the canonical key page rather than rendering their own passive key viewer; planned contracts such as `test_account_key_page_renders_key_material_viewer()` and `test_profile_page_hides_key_material()`.
- Verification approach: run the targeted page and asset tests, confirm the dedicated key page renders, confirm public profiles no longer show key material, and confirm the linking surfaces keep one canonical destination.
- Risks or open questions:
  - avoiding brittle assertions if surrounding account-page copy changes during nearby simplification work
  - choosing the smallest test set that proves canonical-destination behavior without overfitting markup
- Canonical components/API contracts touched: page-route tests for the new account/key page; profile-page tests; existing account-related page link contracts.
