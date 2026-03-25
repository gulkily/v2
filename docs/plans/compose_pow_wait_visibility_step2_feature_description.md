## Problem
When browser compose needs to solve proof-of-work before a signed post can be submitted, the user is currently informed only by a status note low on the page. New users can miss that message and interpret the delay as an unresponsive form rather than an active security step.

## User Stories
- As a new signed user, I want the compose page to clearly show when proof-of-work is actively being solved so that I understand why submission is taking longer.
- As a signed user, I want the waiting feedback to appear near the main submit action so that I can notice it without scanning the whole page.
- As a returning user, I want proof-of-work, signing, and submit feedback to stay in one consistent compose status area so that the flow feels predictable.
- As a maintainer, I want this slice to reuse the canonical browser compose status surface so that visibility improves without introducing a second submission-state UI.

## Core Requirements
- The compose experience must present active proof-of-work solving as a prominent in-form waiting state rather than only a low-visibility status line below the form content.
- The waiting state must live near the primary compose action area where users focus during submission.
- The same canonical compose status surface must continue to communicate other submission phases such as signing, submit success, and failures.
- The feature must distinguish active proof-of-work work from idle or completed states so the important waiting message stands out.
- The slice must stay within the existing browser compose experience and avoid turning into a broader onboarding, anti-abuse, or submission-flow redesign.

## Shared Component Inventory
- Existing signed compose page in `templates/compose.html`: extend this canonical compose surface because the problem is where submission feedback is presented during the current posting flow.
- Existing browser signing submit flow in `templates/assets/browser_signing.js`: reuse and extend the canonical status updates that already announce proof-of-work, signing, and submission phases rather than creating a parallel state source.
- Existing shared status styling in `templates/assets/site.css`: extend the current status treatment so the active proof-of-work state becomes visually prominent without adding a separate widget system.
- Existing create-thread and create-reply API flow: reuse unchanged as the canonical backend contract because the issue is user awareness during the client-side waiting period, not server behavior.
- Existing technical-details and key-material sections in compose: keep available, but do not rely on those lower-page surfaces as the primary place to explain an active proof-of-work wait.

## Simple User Flow
1. A signed user fills out the compose form and submits a post that requires proof-of-work.
2. The compose page enters the existing browser submission flow.
3. When proof-of-work solving begins, the user sees a prominent waiting state near the primary submit area explaining that the browser is working.
4. The same status surface continues to reflect later phases such as signing, submission, success, or failure.
5. The post finishes submission without the user needing to guess whether the form is stalled.

## Success Criteria
- A new user can immediately notice that proof-of-work solving is in progress during signed compose submission.
- The active waiting message appears in the main compose action area instead of being easy to miss at the bottom of the form.
- Proof-of-work, signing, and submit outcomes continue to use one shared compose status surface.
- The slice improves visibility without adding a modal, overlay, or separate submission workflow.
