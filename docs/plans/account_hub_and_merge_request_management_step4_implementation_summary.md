## Stage 1 - current-profile target derivation asset
- Changes:
  - Added the new shared browser asset [profile_nav.js](/home/wsl/v2/templates/assets/profile_nav.js) to derive a profile href from the stored OpenPGP public key.
  - Added the asset route in [web.py](/home/wsl/v2/forum_web/web.py) so the profile-nav enhancement can be served like the existing browser-signing assets.
  - Added a small shared script-tag helper in [templates.py](/home/wsl/v2/forum_web/templates.py) for later page wiring.
- Verification:
  - Ran `python -c "from forum_web.templates import render_profile_nav_script_tag; print(render_profile_nav_script_tag())"` and confirmed it returns the expected `/assets/profile_nav.js` module tag.
  - Ran `python -c "from forum_web.web import load_asset_text; text = load_asset_text('profile_nav.js'); print('profileHrefFromPublicKey' in text and 'enhanceProfileNav' in text)"` and confirmed the new helper functions are present.
- Notes:
  - The actual `My profile` nav affordance is not visible yet in this stage; this stage only establishes the reusable client-side derivation path because normal page requests still lack server-visible user identity.

## Stage 2 - shared header my-profile affordance
- Changes:
  - Extended the shared primary nav in [templates.py](/home/wsl/v2/forum_web/templates.py) with a hidden `My profile` placeholder link marked by `data-profile-nav-link`.
  - Updated the shared page renderer in [templates.py](/home/wsl/v2/forum_web/templates.py) to load `/assets/profile_nav.js` on rendered pages so the nav link can be activated when a stored browser key is present.
  - Kept the existing profile page as the destination surface for `update username` and `manage merges`; no duplicate account hub or secondary settings page was introduced.
- Verification:
  - Ran `python -c "from forum_web.templates import render_primary_nav; html = render_primary_nav(); print('data-profile-nav-link' in html and 'My profile' in html and 'hidden' in html)"` and confirmed the shared nav now includes the hidden placeholder.
  - Ran `python -c "from forum_web.templates import render_page; html = render_page(title='x', hero_kicker='k', hero_title='t', hero_text='z', content_html='body'); print('/assets/profile_nav.js' in html and 'data-profile-nav-link' in html)"` and confirmed rendered pages include both the nav placeholder and the new shared module script.
- Notes:
  - This remains a browser-side enhancement: the link is only exposed when the browser already has the stored signing public key, which matches the product’s existing local-key model.

## Stage 3 - regression coverage and browser-safe asset behavior
- Changes:
  - Extended [test_board_index_page.py](/home/wsl/v2/tests/test_board_index_page.py) to verify the shared header now renders the hidden `My profile` placeholder and loads `/assets/profile_nav.js`.
  - Added [test_profile_nav_asset.py](/home/wsl/v2/tests/test_profile_nav_asset.py) to verify the asset can derive the canonical `/profiles/openpgp-<fingerprint>` href from a generated OpenPGP public key.
  - Hardened [profile_nav.js](/home/wsl/v2/templates/assets/profile_nav.js) so it no-ops cleanly when `document` is unavailable instead of throwing during module import outside a browser.
- Verification:
  - Ran `python -m unittest tests.test_board_index_page tests.test_profile_nav_asset tests.test_profile_update_page tests.test_merge_management_page`.
  - Result: `Ran 9 tests ... OK`.
- Notes:
  - The coverage is intentionally targeted: it proves the shared nav markup, the public-key-to-profile-href derivation, and that existing profile update plus merge-management pages still render successfully alongside the new shared asset.
