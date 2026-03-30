# Step 3: Development Plan – Monospace Keys Across All Frontend Templates

## Stage 1: Audit All Key/Technical Textareas Across Templates
- Goal: Identify all textareas displaying key material or technical information across all 6 templates and determine which are missing `.technical-textarea` class
- Dependencies: None
- Expected changes:
  - Review all 18 textarea elements across 6 templates:
    - `compose.html` (5 textareas)
    - `account_key.html` (2 textareas)
    - `profile.html` (1 textarea)
    - `profile_update.html` (5 textareas)
    - `merge_request_action.html` (5 textareas)
    - `thread_title_update.html` (5 textareas)
  - Document current classes for each textarea
  - Identify any missing `.technical-textarea` or `.key-display` classes
- Verification approach:
  - Create audit checklist of all 18 textareas and their current classes
  - Document findings in implementation summary
- Risks or open questions: None
- Canonical components/API contracts touched:
  - All 6 templates in `templates/` directory

## Stage 2: Apply Monospace Classes to All Technical Textareas
- Goal: Ensure all 18 key/technical data textareas have appropriate monospace CSS classes applied
- Dependencies: Stage 1 (audit complete)
- Expected changes:
  - Add `.technical-textarea` class to any textarea missing it
  - Add `.key-display` class to any key display textarea missing it
  - Add `.profile-public-key-textarea` to profile public key textareas for full-width display if needed
  - Verify no CSS rule conflicts in `templates/assets/site.css`
- Verification approach:
  - Load each of the 6 pages in browser
  - Inspect each textarea element to confirm required classes are present
  - Visually confirm all technical data displays in monospace font
  - Test in both light and dark modes
  - Create screenshots showing all textareas with proper monospace styling
- Risks or open questions: None identified; styling already exists, changes should be straightforward class additions
- Canonical components/API contracts touched:
  - `templates/compose.html`, `account_key.html`, `profile.html`, `profile_update.html`, `merge_request_action.html`, `thread_title_update.html`
  - `templates/assets/site.css` — `.technical-textarea`, `.key-display`, `.profile-public-key-textarea` class definitions
