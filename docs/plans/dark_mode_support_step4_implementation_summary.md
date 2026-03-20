## Stage 1 - Shared theme foundation
- Changes:
  - Added shared light/dark theme tokens to `templates/assets/site.css`.
  - Enabled automatic dark mode through `@media (prefers-color-scheme: dark)` and declared `color-scheme: light dark`.
  - Routed the shared shell and top-level surfaces through theme variables instead of fixed light-only colors.
- Verification:
  - `python -m pytest tests/test_compose_thread_page.py`
- Notes:
  - This stage establishes the shared theme switch but does not yet retune every component that still uses literal warm surface colors deeper in the stylesheet.

## Stage 2 - Shared component dark mode coverage
- Changes:
  - Replaced the remaining light-only shared component surface colors in `templates/assets/site.css` with theme variables.
  - Extended dark-mode coverage across stat cards, chips, thread cards, commit cards, post cards, technical textareas, inputs, buttons, compose cards, task tables, task context panels, and board-index thread rows.
- Verification:
  - `python -m pytest tests/test_board_index_page.py`
  - `python -m pytest tests/test_task_thread_pages.py`
  - `python -m pytest tests/test_username_profile_route.py`
  - `python -m pytest tests/test_instance_info_page.py`
- Notes:
  - The change stays CSS-centric, so template churn remains low while most major pages inherit the new dark-mode treatment automatically.

## Stage 3 - Dark mode regression coverage and final verification
- Changes:
  - Added `tests/test_site_css_asset.py` to assert that the shared stylesheet exposes the dark-mode media query and routes key shared surfaces through theme variables.
  - Completed a final multi-page regression sweep across compose, home, thread, profile, and instance routes after the theme cleanup.
- Verification:
  - `python -m pytest tests/test_site_css_asset.py`
  - `python -m pytest tests/test_compose_thread_page.py tests/test_board_index_page.py tests/test_task_thread_pages.py tests/test_username_profile_route.py tests/test_instance_info_page.py`
- Notes:
  - Automated coverage checks for theme hooks and route stability; visual contrast still benefits from real-browser review during product QA.
