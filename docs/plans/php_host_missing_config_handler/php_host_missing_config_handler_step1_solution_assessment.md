## Problem Statement
Choose the smallest useful way to turn the current missing `forum_host_config.php` failure into an admin-helpful recovery path on PHP-host deployments.

### Option A: Replace the raw error with a dedicated admin diagnostic page and concrete recovery steps
- Pros:
  - Directly improves the current failure mode without changing the PHP shim architecture.
  - Can show the checked paths, the missing file name, the expected setup command, and the likely deployment mistake in one place.
  - Keeps the handler safe for public requests while still being actionable for an operator reading the page.
  - Fits the existing PHP-host setup workflow instead of inventing a second configuration path.
- Cons:
  - Still requires the operator to run setup or fix paths manually.
  - Needs care so the page does not expose more filesystem detail than necessary.

### Option B: Fall back to an example/default config when the real config is missing
- Pros:
  - Could let some partially configured installs keep responding.
  - May reduce operator friction on first deploy if defaults happen to match.
- Cons:
  - Risks masking a broken deployment behind incorrect path assumptions.
  - Can produce harder-to-debug downstream failures than an explicit setup error.
  - Blurs the boundary between tracked example config and required host-local config.

### Option C: Keep the current hard failure but make the text slightly friendlier
- Pros:
  - Smallest code change.
  - Preserves the current explicit failure behavior.
- Cons:
  - Does not materially improve operator recovery.
  - Leaves setup guidance fragmented between the error output and external docs.
  - Misses the chance to turn a common deployment issue into a deterministic recovery loop.

## Recommendation
Recommend Option A: replace the raw error with a dedicated admin diagnostic page and concrete recovery steps.

This is the best fit because it keeps the current explicit-failure behavior while making the failure genuinely useful. The next step should stay narrow: improve the missing-config handler itself, reuse the existing `./forum php-host-setup` workflow, and avoid adding config fallbacks that can hide a broken deployment.
