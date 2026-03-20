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
