## Problem Statement
Choose the smallest useful way to make PHP-host installation less brittle and more repeatable now that the current shim-based deployment path works in practice.

### Option A: Add one repo-managed host setup generator and config template for the existing PHP shim
- Pros:
  - Keeps the current PHP shim architecture intact while removing the most error-prone manual edits.
  - Can generate or sync the exact `index.php`, `.htaccess`, and host-specific path configuration an operator needs.
  - Reduces ambiguity around absolute paths, required capabilities, and writable directories without inventing a new runtime model.
  - Fits the existing `./forum` operator-command direction already used for env setup.
- Cons:
  - Still depends on the same PHP plus Python plus git host prerequisites.
  - Needs a clear boundary so generated host config does not become a second general-purpose deployment framework.

### Option B: Expand the documentation only with a more prescriptive copy-paste deployment guide
- Pros:
  - Smallest immediate change.
  - Low implementation risk.
  - Could still eliminate some confusion around absolute paths and required host features.
- Cons:
  - Leaves operators manually editing deployment files and repeating brittle steps.
  - Does not materially reduce configuration drift between the app checkout and public web root.
  - Keeps verification and path wiring mostly human-driven.

### Option C: Move more deployment logic into the PHP front controller itself through autodiscovery and fallback behavior
- Pros:
  - Could reduce the amount of required host configuration further.
  - Might let more PHP-host installs work with fewer explicit steps.
- Cons:
  - Pushes deployment-specific complexity into request-time code.
  - Risks turning the thin shim into a configuration-heavy adapter layer.
  - Makes failures harder to reason about when autodiscovery guesses wrong.

## Recommendation
Recommend Option A: add one repo-managed host setup generator and config template for the existing PHP shim.

This is the smallest coherent improvement over the current working deployment path. The next steps should stay strict: keep the PHP shim thin, move path/config repetition into one explicit operator workflow, and treat generated host files as deployment glue rather than a new application layer.
