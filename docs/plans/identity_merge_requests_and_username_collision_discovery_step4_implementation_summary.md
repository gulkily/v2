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
