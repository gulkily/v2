## Stage 1 - Add shared merge feature flag plumbing
- Changes:
  - added a shared `merge_feature_enabled()` helper and nav data plumbing for merge-flag awareness
  - documented `FORUM_ENABLE_ACCOUNT_MERGE=0` in `.env.example`
  - added focused tests for helper semantics and committed env defaults
- Verification:
  - `python -m pytest tests/test_merge_feature_flag.py`
  - `python -m pytest tests/test_runtime_env.py`
- Notes:
  - this stage only introduces the shared flag contract; merge surfaces still behave normally until the next stages gate them

## Stage 2 - Hide merge UI and routes when the flag is off
- Changes:
  - hid the profile-level merge action link and self-merge suggestion UI unless the merge flag is enabled
  - made `/profiles/<slug>/merge` and `/profiles/<slug>/merge/action` return missing-resource behavior while the flag is off
  - updated `profile_nav.js` so the shared `My profile` nav link no longer fetches merge notifications or redirects into merge management when the flag is off
- Verification:
  - `python -m pytest tests/test_username_profile_route.py`
  - `python -m pytest tests/test_merge_management_page.py`
  - `python -m pytest tests/test_profile_nav_asset.py`
- Notes:
  - this stage gates only web surfaces and nav behavior; merge APIs remain for Stage 3 so the final release posture is not complete yet

## Stage 3 - Gate merge APIs and restore explicit flag-on regression coverage
- Changes:
  - made `/api/get_merge_management` and `/api/merge_request` return missing-resource behavior while the merge flag is off
  - updated merge-specific API tests to assert default-off unavailability and explicit flag-on behavior
  - restored explicit flag-on coverage for merge pages and self-merge suggestion UI so the feature still works when developers enable it locally
- Verification:
  - `python -m pytest tests/test_merge_management_api.py`
  - `python -m pytest tests/test_merge_request_submission.py`
  - `python -m pytest tests/test_merge_management_page.py`
  - `python -m pytest tests/test_username_profile_route.py`
- Notes:
  - underlying merge records and merge-aware identity resolution remain intact; this stage only changes release visibility and endpoint availability
