## Stage 1 - merge-request record model and username-history helpers
- Changes:
  - Added [forum_core/merge_requests.py](/home/wsl/v2/forum_core/merge_requests.py) with canonical merge-request parsing, deterministic request-state derivation, synthetic approved merge-link derivation, and historical-username match helpers built on visible profile-update history.
  - Added [tests/test_merge_requests.py](/home/wsl/v2/tests/test_merge_requests.py) covering request parsing, target approval, moderator approval, dismissal behavior, and same-name discovery from visible username history.
- Verification:
  - Ran `python3 -m unittest tests.test_merge_requests`.
  - Ran `python3 -m py_compile forum_core/merge_requests.py`.
- Notes:
  - The approval rule implemented in the shared state model treats the initial request as requester consent and allows either target approval or moderator approval to activate the merge.
