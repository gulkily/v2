## Stage 1 - enforce one claim per signer identity
- Changes:
  - Added `has_visible_profile_update_for_source_identity(...)` in [profile_updates.py](/home/wsl/v2/forum_core/profile_updates.py) so write validation can detect an existing visible username claim for a signer identity.
  - Updated [profile_updates.py](/home/wsl/v2/forum_cgi/profile_updates.py) to reject a second `set_display_name` submission from the same signer identity while leaving the signer-match check intact.
  - Extended [test_profile_update_submission.py](/home/wsl/v2/tests/test_profile_update_submission.py) with coverage for first-claim success and second-claim rejection from the same key.
- Verification:
  - `python -m unittest tests.test_profile_update_submission`
- Notes:
  - This stage keeps merged-profile read behavior unchanged; it only constrains repeat writes from one signer identity.
