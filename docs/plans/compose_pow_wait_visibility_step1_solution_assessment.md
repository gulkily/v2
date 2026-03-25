## Problem Statement
Choose the smallest useful way to make the compose flow's proof-of-work waiting state obvious to new users instead of burying it in a low-visibility status line at the bottom of the form.

### Option A: Promote the existing submit status into a prominent in-form progress notice near the submit action
- Pros:
  - Keeps the current canonical status surface and browser signing flow instead of inventing a separate UI state machine.
  - Directly solves the discoverability problem by moving or visually elevating the PoW state closer to the submit button and active form area.
  - Leaves existing status messages for signing, submit success, and failures on one shared surface.
  - Smallest likely scope across template, CSS, and browser status updates.
- Cons:
  - Still depends on users noticing a message-based treatment rather than a full-screen interruption.
  - Needs clear active styling rules so routine idle text does not compete visually with PoW progress.

### Option B: Block the form with a modal or overlay while PoW is being computed
- Pros:
  - Makes the waiting state impossible to miss.
  - Prevents conflicting user actions during an active solve.
- Cons:
  - Introduces a separate interaction pattern, accessibility concerns, and extra dismissal or focus-management rules.
  - Heavier than the problem requires because the browser is already tracking status in the existing compose view.
  - Risks feeling more alarming than helpful for a short-lived background computation.

### Option C: Add a richer progress widget with progress bar, phases, and timing hints
- Pros:
  - Gives users more explanation about what the browser is doing while PoW runs.
  - Creates room for future signing or submit-phase progress improvements.
- Cons:
  - Browser PoW currently exposes attempt counts, not true completion progress, so a richer widget could imply precision the system does not have.
  - Larger scope than needed for the immediate visibility issue.
  - More likely to drift into a new component rather than a focused improvement to the current compose surface.

## Recommendation
Recommend Option A: promote the existing submit-status surface into a prominent progress notice near the submit action and give active PoW states a stronger visual treatment.

This is the smallest change that addresses the real problem: users are already being told that PoW is running, but the message is easy to miss because of where and how it is presented. Step 2 should define a shared compose status treatment that stays lightweight, appears in the primary action area, and distinguishes active PoW work from idle or completed submission text.
