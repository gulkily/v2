## Stage 1 - Shared theme foundation
- Changes:
  - Added shared light/dark theme tokens to `templates/assets/site.css`.
  - Enabled automatic dark mode through `@media (prefers-color-scheme: dark)` and declared `color-scheme: light dark`.
  - Routed the shared shell and top-level surfaces through theme variables instead of fixed light-only colors.
- Verification:
  - `python -m pytest tests/test_compose_thread_page.py`
- Notes:
  - This stage establishes the shared theme switch but does not yet retune every component that still uses literal warm surface colors deeper in the stylesheet.
