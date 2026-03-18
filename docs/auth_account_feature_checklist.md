# Authentication And Account Feature Checklist

This checklist is scoped to the current `v2` model, which is key-based and signed-record-driven rather than password/session based. Scores are:

- `Implementation difficulty`: `0.0` = trivial, `1.0` = very hard
- `User expectation`: `0.0` = niche, `1.0` = most users will expect it

## Current Baseline

The repo already appears to support these account/identity foundations:

- automatic identity bootstrap from a first signed post
- canonical profile pages and `get_profile`
- signed profile updates for display names
- username-based profile routing
- identity linking and key rotation records
- merge request management for consolidating identities
- browser-side "My profile" navigation based on the stored public key

The remaining gaps are mostly around recovery, lifecycle management, richer profile data, safety/privacy controls, and making the unusual key-based model feel understandable to normal users.

## Checklist

| Done | Feature | Why it matters | Implementation difficulty | User expectation |
| --- | --- | --- | ---: | ---: |
| [ ] | Browser key backup and export flow | Users need an obvious way to keep ownership of their identity before device loss. | 0.25 | 0.95 |
| [ ] | Key import / restore UX for a new browser or device | Recovery is incomplete if users cannot reattach an existing identity easily. | 0.30 | 0.95 |
| [ ] | Clear "what is my account?" onboarding copy | This product uses keys and signed records; most users will otherwise not understand the model. | 0.15 | 0.90 |
| [ ] | First-run key creation wizard with warnings and backup guidance | Makes the initial identity bootstrap legible and reduces accidental lockout. | 0.25 | 0.90 |
| [ ] | Account recovery story beyond "keep your key safe" | Without recovery, account loss risk is much higher than users usually tolerate. | 0.85 | 0.90 |
| [ ] | Explicit linked-keys management page | Users should be able to see which keys currently resolve to one profile. | 0.35 | 0.80 |
| [ ] | Browser UX for key rotation | The record model exists, but ordinary users will expect a guided flow. | 0.45 | 0.80 |
| [ ] | Revocation / compromised-key handling | A stolen key needs a visible, authoritative way to stop being trusted. | 0.80 | 0.85 |
| [ ] | Signed proof challenge before sensitive account actions | Helps users verify they are acting with the intended key before merges or rotations. | 0.40 | 0.60 |
| [ ] | Richer profile fields: bio | A minimal profile usually includes more than just a display name. | 0.20 | 0.75 |
| [ ] | Richer profile fields: avatar or profile image | Common expectation on user-profile surfaces. | 0.40 | 0.75 |
| [ ] | Richer profile fields: links / website / social handles | Common account metadata with relatively low product risk. | 0.25 | 0.65 |
| [ ] | Username uniqueness policy and reservation rules | Username routes exist, so collision policy should become explicit and predictable. | 0.55 | 0.85 |
| [ ] | Username availability feedback during profile edits | Users expect immediate feedback before trying a name. | 0.30 | 0.80 |
| [ ] | Visible username history on profile pages | Helpful for trust, continuity, and rename transparency. | 0.20 | 0.55 |
| [ ] | Better merge request explanations and risk warnings | Identity consolidation is unusual and likely confusing without strong copy. | 0.20 | 0.70 |
| [ ] | Cancel / undo path for pending merge requests by requester | Users generally expect they can retract a request they initiated. | 0.35 | 0.75 |
| [ ] | Safer merge review with side-by-side evidence | Reduces mistaken merges, especially for users with similar names. | 0.45 | 0.70 |
| [ ] | Audit view for account-affecting actions | Users should be able to review profile updates, merges, and key changes in one place. | 0.35 | 0.70 |
| [ ] | Device/session-style labeling for local stored keys | Even without server sessions, users benefit from understanding where they are signed in. | 0.45 | 0.70 |
| [ ] | Local sign-out / remove-key flow | Users will expect a way to disconnect the current browser from an identity. | 0.20 | 0.90 |
| [ ] | Multiple-local-account switching in one browser | Important once users manage more than one identity or moderator key. | 0.45 | 0.65 |
| [ ] | Privacy controls for profile visibility | Some users will want to limit discoverability or public metadata. | 0.65 | 0.70 |
| [ ] | Account-level moderation and safety settings | Blocking, muting, or limiting interaction is common account-system surface area. | 0.70 | 0.80 |
| [ ] | Notification preferences for merge requests and account events | Merge approvals and identity actions are easy to miss without notification surfaces. | 0.65 | 0.75 |
| [ ] | In-product alerts for incoming merge requests | High-value workflow notification even without full email support. | 0.35 | 0.70 |
| [ ] | Email or external notification bridge | Not core to identity, but many users expect actionable account emails. | 0.75 | 0.65 |
| [ ] | Account deletion / deactivation policy | Users often expect a clear lifecycle exit, even if full deletion is impossible in git history. | 0.80 | 0.85 |
| [ ] | Data export for profile and account records | Strong trust feature and often expected for account ownership. | 0.35 | 0.75 |
| [ ] | Human-readable security page explaining guarantees and limits | Necessary because the auth model is nonstandard and loss modes matter. | 0.15 | 0.85 |
| [ ] | Admin tooling for account dispute resolution | Important if merges, compromised keys, or impersonation disputes become common. | 0.70 | 0.55 |

## Suggested Priority Order

If the goal is practical user readiness rather than architectural purity, the strongest next cluster is:

1. Browser key backup and export flow
2. Key import / restore UX
3. First-run key creation wizard with clear onboarding copy
4. Local sign-out / remove-key flow
5. Explicit linked-keys management page
6. Browser UX for key rotation
7. Revocation / compromised-key handling
8. Account deletion / deactivation policy

That sequence covers the highest-risk gaps in the current model: user comprehension, recoverability, and key lifecycle safety.
