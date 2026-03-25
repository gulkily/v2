# Presentable Page Source HTML Step 1: Solution Assessment

## Problem Statement
Choose the smallest coherent way to make page source meaningfully more readable for technical users when much of the current HTML is emitted as one long line or other low-presentability output.

### Option A: Make HTML responses structurally readable by default across normal page renders
- Pros:
  - Directly satisfies the user story because browser source views become more readable without needing a separate mode.
  - Improves the output of both template-based pages and string-built responses if the app adopts one presentability standard.
  - Creates a better baseline for future debugging, diffing, and manual inspection of generated pages.
- Cons:
  - Touches a wider surface because every HTML-producing path needs to follow the same readability rules.
  - Requires care around whitespace-sensitive content, inline scripts, and streamed responses so readability changes do not alter behavior.

### Option B: Keep normal responses as they are and add a dedicated readable source view for pages
- Pros:
  - Smaller immediate blast radius because the presentability work stays in an explicit inspection mode.
  - Leaves existing page delivery unchanged while giving technical users a better reading surface.
  - Makes it easier to add extra inspection aids beyond line breaks, such as clear section boundaries or response metadata.
- Cons:
  - Does not fix the actual page source returned by normal requests, so native browser "view source" remains hard to read.
  - Introduces two representations of the same page that can drift if not kept tightly aligned.

### Option C: Add a global post-render HTML prettifier pass
- Pros:
  - Centralizes the formatting policy instead of relying on each renderer to emit readable markup on its own.
  - Could improve consistency quickly across mixed template and string-built responses.
- Cons:
  - Adds dependency and output-stability risk to every HTML response.
  - A generic prettifier can obscure ownership of markup quality and behave poorly on partial, malformed, or streaming-oriented responses.

## Recommendation
Recommend Option A: make HTML responses structurally readable by default across normal page renders.

This is the smallest approach that truly fixes the problem the user described. A separate source-inspection mode is useful, but it leaves the underlying response unreadable; a generic prettifier is broader than needed and adds avoidable risk. The next step should define one readable-output standard for the app's HTML responses and identify the few response types that may need explicit exceptions.
