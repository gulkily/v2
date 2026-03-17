## Stage 1 - merge-request record model and username-history helpers
- Changes:
  - Added [forum_core/merge_requests.py](/home/wsl/v2/forum_core/merge_requests.py) with canonical merge-request parsing, deterministic request-state derivation, synthetic approved merge-link derivation, and historical-username match helpers built on visible profile-update history.
  - Added [tests/test_merge_requests.py](/home/wsl/v2/tests/test_merge_requests.py) covering request parsing, target approval, moderator approval, dismissal behavior, and same-name discovery from visible username history.
- Verification:
  - Ran `python3 -m unittest tests.test_merge_requests`.
  - Ran `python3 -m py_compile forum_core/merge_requests.py`.
- Notes:
  - The approval rule implemented in the shared state model treats the initial request as requester consent and allows either target approval or moderator approval to activate the merge.

## Stage 2 - signed merge-request write contract
- Changes:
  - Added [forum_cgi/merge_requests.py](/home/wsl/v2/forum_cgi/merge_requests.py) with signed request, approve, dismiss, and moderator-approve submission handling, including visible-identity validation and pending-request checks.
  - Extended [forum_cgi/text.py](/home/wsl/v2/forum_cgi/text.py) and [forum_web/web.py](/home/wsl/v2/forum_web/web.py) so `POST /api/merge_request` returns stable plain-text preview/success output through the main WSGI app.
  - Added [tests/test_merge_request_submission.py](/home/wsl/v2/tests/test_merge_request_submission.py) covering target approval and moderator approval through the API route.
- Verification:
  - Ran `python3 -m unittest tests.test_merge_request_submission`.
  - Re-ran `python3 -m unittest tests.test_merge_requests`.
  - Ran `python3 -m py_compile forum_cgi/merge_requests.py forum_cgi/text.py forum_web/web.py`.
- Notes:
  - The route currently enforces the narrow rule chosen for this loop: only a pending requester-originated request can be approved, dismissed, or moderator-approved.

## Stage 3 - merge-management read model and resolved profile activation
- Changes:
  - Extended [forum_web/profiles.py](/home/wsl/v2/forum_web/profiles.py) so approved merge requests synthesize active merge links during identity resolution, letting approved request pairs resolve through the existing canonical profile model.
  - Extended [forum_core/merge_requests.py](/home/wsl/v2/forum_core/merge_requests.py) and [forum_web/api_text.py](/home/wsl/v2/forum_web/api_text.py) with a canonical merge-management summary that groups historical username matches, outgoing requests, incoming requests, dismissed requests, and approved requests.
  - Added `GET /api/get_merge_management?identity_id=<identity-id>` in [forum_web/web.py](/home/wsl/v2/forum_web/web.py) and regression coverage in [tests/test_merge_management_api.py](/home/wsl/v2/tests/test_merge_management_api.py).
- Verification:
  - Ran `python3 -m unittest tests.test_merge_management_api`.
  - Re-ran `python3 -m unittest tests.test_merge_request_submission tests.test_merge_requests`.
  - Ran `python3 -m py_compile forum_core/merge_requests.py forum_web/profiles.py forum_web/api_text.py forum_web/web.py`.
- Notes:
  - Approved merge requests now affect the same canonical identity-resolution path used by profile reads, while pending and dismissed requests remain read-only workflow state.

## Stage 4 - merge-management web flow and signer-facing actions
- Changes:
  - Extended [forum_web/web.py](/home/wsl/v2/forum_web/web.py) so profile pages link to a dedicated merge-management page, and added web routes for `/profiles/<identity-slug>/merge` plus `/profiles/<identity-slug>/merge/action`.
  - Added [templates/merge_management.html](/home/wsl/v2/templates/merge_management.html), [templates/merge_request_action.html](/home/wsl/v2/templates/merge_request_action.html), and [templates/assets/merge_request_signing.js](/home/wsl/v2/templates/assets/merge_request_signing.js) for candidate discovery, incoming-request review, and signed request/approve/dismiss/moderator-approve submissions through the browser.
  - Added [tests/test_merge_management_page.py](/home/wsl/v2/tests/test_merge_management_page.py) covering the profile linkout, merge-management page rendering, and merge-action signing page.
- Verification:
  - Ran `python3 -m unittest tests.test_merge_management_page tests.test_merge_management_api tests.test_merge_request_submission tests.test_merge_requests`.
  - Re-ran `python3 -m unittest tests.test_profile_update_page`.
  - Ran `python3 -m py_compile forum_web/web.py`.
- Notes:
  - The browser action page derives `Actor-Identity-ID` from the imported signing key at submit time, which keeps moderator approvals possible without pretending the moderator is the target identity being viewed.
