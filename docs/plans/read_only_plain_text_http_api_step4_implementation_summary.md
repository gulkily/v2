## Stage 1 - API shell and text serializers
- Changes:
  - Added a dedicated plain-text API serializer module for deterministic read responses.
  - Added an `/api/` route shell to the existing WSGI app.
  - Added a shared repository-state loader so browser and API surfaces reuse the same canonical read path.
- Verification:
  - Called the WSGI app for `/api/` and confirmed a `200 OK` plain-text response with deterministic counts and the planned route list.
- Notes:
  - This stage intentionally stops at the API shell and serialization helpers; the actual `list_index`, `get_thread`, and `get_post` routes land in later stages.
