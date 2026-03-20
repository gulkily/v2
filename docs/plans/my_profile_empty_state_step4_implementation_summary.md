## Stage 1 - Self-request empty-state route handling
- Changes:
  - Added a dedicated unpublished-profile rendering path in [web.py](/home/wsl/v2/forum_web/web.py) so `/profiles/<identity-slug>` can return a profile-aware empty state when the request explicitly marks itself as the signed user’s own profile.
  - Added [profile_empty_state.html](/home/wsl/v2/templates/profile_empty_state.html) for the first-visit `My profile` content, including next actions for publishing a first signed post or reviewing the browser key.
  - Kept the existing generic missing-resource response for ordinary unknown profile requests that do not carry the self marker.
- Verification:
  - Ran `python -c '...PATH_INFO=\"/profiles/openpgp-alpha\"; QUERY_STRING=\"self=1\"...'` against a temporary empty repo and confirmed `200 OK`, `data-profile-empty-state`, and `publish your first signed post` are present while `This record could not be located` is absent.
  - Ran `python -c '...PATH_INFO=\"/profiles/openpgp-alpha\"; QUERY_STRING=\"\"...'` against a temporary empty repo and confirmed `404 Not Found` still returns the generic missing-resource page without the new empty-state markup.
- Notes:
  - This stage intentionally relies on an explicit self-request marker because the server cannot infer browser-held identity for unpublished profiles on its own.
