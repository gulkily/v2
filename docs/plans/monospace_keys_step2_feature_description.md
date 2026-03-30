# Step 2: Feature Description – Monospace Keys on Compose Thread Page

## Problem
Key data and technical information displayed across the frontend (PGP keys, signatures, payload previews, server responses) should consistently use monospace font across all pages for professional appearance and better readability.

## User Stories
- As a user viewing or entering key material, I want all key displays to use monospace font so they're clearly distinguished as technical/binary content and easier to read and copy.
- As a developer reviewing the code, I want all technical data fields to follow a consistent styling convention across all pages so the site maintains visual coherence.

## Core Requirements
- All key material textareas (private key input, public key output) display in monospace font across all pages
- Derived payload textareas (canonical payload, detached signature, server response) display in monospace font across all pages
- Monospace styling is applied consistently across all technical data sections on all frontend templates
- Styling works across browsers and respects dark/light mode preferences

## Shared Component Inventory
- **`.technical-textarea` class** (site.css): Existing CSS class already applies monospace font (`"Courier New", Courier, monospace`) at 0.82rem/1.45 line height
- **`.key-display` class** (site.css): Existing CSS class for key-specific styling, also monospace
- **`.profile-public-key-textarea` class** (site.css): Public key specific styling for full-width display
- **HTML elements across 6 templates** contain key/technical data:
  - `templates/compose.html` — 5 textareas (private-key-input, public-key-output, payload-output, signature-output, response-output)
  - `templates/account_key.html` — 2 textareas (key-private-key-output, key-public-key-output)
  - `templates/profile.html` — 1 textarea (profile-public-key-block)
  - `templates/profile_update.html` — 5 textareas (same IDs as compose.html)
  - `templates/merge_request_action.html` — 5 textareas (same IDs as compose.html)
  - `templates/thread_title_update.html` — 5 textareas (same IDs as compose.html)

**Reuse decision**: Extend existing `.technical-textarea` and `.key-display` classes if any elements lack them; no new CSS classes needed. Audit all 18 textarea elements for class coverage.

## Simple User Flow
1. User navigates to any page with key or technical data (compose, account key, profile, profile update, etc.)
2. User views key material section
3. All key and technical data appears in readable monospace font

## Success Criteria
- All 18 technical data textareas across 6 templates render in monospace font
- Styling is consistent with site-wide technical data presentation
- No visual regressions or broken layouts
- Verification: Screenshots of each page showing all technical sections visible and properly styled
