## Stage 1 - Add dedicated account key page
- Changes:
  - added a dedicated `/account/key/` page that renders browser-stored key status plus private/public key textareas
  - reused the existing key viewer asset by making it work with either the legacy profile IDs or the new account-page IDs
  - added focused route coverage for the new page
- Verification:
  - `python -m pytest tests/test_account_key_page.py`
  - `python -m pytest tests/test_username_profile_route.py`
- Notes:
  - profile pages still render the existing key block in this stage; removal and canonical redirection are deferred to Stage 2
