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
