# Joined Profile Page By Username Step 1: Solution Assessment

## Problem statement
Choose the smallest useful way to add a public `/user/<username>` profile route for merged identities, without dragging this cycle into username-approval policy, collision adjudication, or a full rewrite of profile naming semantics.

## Option A — Add `/user/<username>` only for the latest current username when it maps unambiguously to one resolved identity set
- Pros: Smallest read-surface slice; fits the existing resolved-profile model; respects the user's preference that only the latest current username should resolve; lets the joined page show all usernames in the merged set if they still differ.
- Cons: Ambiguous usernames still fail instead of resolving cleanly; does not solve username approval/collision workflow yet; needs an explicit no-result behavior when no single preferred username exists.

## Option B — Add `/user/<username>` plus a chooser page when multiple profiles match
- Pros: Gives readers a direct username-based route even before approval policy exists; handles collisions without hard failure; could expose multiple merged candidates using current or historical usernames.
- Cons: Reopens product questions about what counts as a valid match; risks turning the route into a public identity-disambiguation surface before approval policy is defined; heavier UX than the user story requires.

## Option C — Defer username-based profile routes until username approval/collision policy exists
- Pros: Keeps public username routing aligned with an explicit ownership or approval rule; avoids shipping a route whose failure cases may feel arbitrary; cleanest long-term semantics if approved usernames become the public key.
- Cons: Delays the joined username-based profile page entirely; blocks a useful read improvement on a broader future cycle; provides no incremental value now.

## Recommendation
Recommend Option A: add `/user/<username>` only for the latest current username when it maps unambiguously to one resolved identity set.

This is the smallest coherent slice given the answers so far:

- Use a new public username-based route such as `/user/<username>`.
- Resolve only the latest current username, not old aliases after rename.
- If a merged set still has conflicting usernames, do not invent one preferred name automatically; the joined page may show all of them until a unified choice exists.
- Treat username approval and collision adjudication as a separate future FDP cycle instead of solving them implicitly here.
- Fail conservatively when a username does not map cleanly to one resolved identity set.

That gives the product a real joined profile page by username now, while keeping approval, moderation, and dispute policy scoped for later.
