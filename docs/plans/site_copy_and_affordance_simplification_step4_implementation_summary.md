## Stage 1 - Homepage affordance cleanup
- Changes:
  - Removed the non-functional homepage tag-link strip from the header and dropped the extra homepage sidebar explainer panels.
  - Simplified the homepage intro copy so the front page keeps only the core thread stream and working action links.
- Verification:
  - Ran `python -m unittest tests.test_board_index_page` and confirmed both homepage tests passed.
  - Ran a direct render smoke check with `python - <<'PY' ... render_board_index() ... PY` and confirmed `front-topic-strip`, `What this view is`, and `House style` are absent while the core action links remain present.
- Notes:
  - This stage removes unfinished or low-value homepage affordances only; broader read/write/planning copy cleanup follows in later stages.
