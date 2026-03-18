# Unattended FDP Guidelines

Purpose: define a stripped-down FDP process that can be run unattended for a checklist of tightly related loops, while preserving the same style of decisions the repo has already made in prior planning work.

This is intended for one-shot execution of a checklist such as [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md), where the main risk is inconsistent local decisions rather than lack of direction.

## Goal

Produce a sequence of small, visible, testable loops without stopping for repeated human clarification unless a new conflict appears that cannot be resolved from existing repo decisions.

## When To Use This Process

Use this stripped-down FDP when all of these are true:

- the loops belong to one coherent feature area
- prior planning docs already define the product direction well enough
- most remaining decisions are local implementation choices rather than new product policy
- shipping the full checklist in one pass is more valuable than preserving full Step 1-4 ceremony for every loop

Do not use it when:

- the feature area still has unresolved policy conflicts
- the next loop could easily invalidate earlier loop choices
- the work affects cross-implementation canonical behavior without enough existing guidance
- safety, moderation, identity, or deletion semantics are still genuinely undecided

## Core Algorithm

For each loop in the checklist:

1. Read the checklist item and its stated goal.
2. Read the closest existing planning docs and working notes for that area.
3. Extract any already-settled decisions before making local choices.
4. Choose the smallest implementation that produces a visible, testable result.
5. Prefer reuse of existing models, routes, caches, and workflows over new abstractions.
6. Preserve current canonical rules unless a prior planning doc already says to change them.
7. Defer polish, optional safeguards, and broad generalization unless the loop explicitly needs them.
8. Implement.
9. Add or update focused regression coverage.
10. Record any new decisions or deferred questions in the relevant working-notes doc.

## Decision Rubric

When multiple reasonable choices exist, prefer the one that scores best on these repo-specific rules.

### 1. Follow Existing Recorded Decisions

Previously logged plans and working notes are the source of truth.

- If a prior doc settled the policy, reuse it directly.
- If multiple docs exist, prefer the newer and more specific one.
- Do not reopen an answered question inside an unattended loop.

### 2. Prefer The Smallest Visible Slice

Choose the smallest change that produces a user-visible or API-visible result.

- avoid broad refactors before the first visible outcome
- avoid solving future loops inside the current loop
- keep each loop independently demonstrable

### 3. Prefer Existing Rules Over New Rules

If current graph, chronology, routing, moderation, or cache rules already answer the question, use them.

- derive from existing state instead of inventing side policy
- recompute from current graph rather than carrying custom exception state
- prefer “same rendering rules as other current read surfaces” over special-case handling

### 4. Assume Good Will And Community Trust

When a question can be answered either by restriction or by trust, prefer trust if it does not break determinism or safety too badly.

- avoid rejecting user input unless there is a strong reason
- prefer disambiguation over refusal
- prefer one-sided recovery paths over bureaucratic approval chains
- do not add suspicion-driven policy until abuse cases actually require it

### 5. Keep Append-Only Semantics Honest

For identity, profile, merge, moderation, and similar record families:

- add forward records instead of mutating old history
- let current visible state come from replaying records under deterministic rules
- if something changes, model the change as a later event rather than a rewritten fact

### 6. Reuse Existing Surfaces

Prefer extending current surfaces before adding new ones.

- reuse `/user/<username>`, `/profiles/...`, and `My profile` before inventing new hubs
- attach notifications to the existing nav before building inbox systems
- extend the existing SQLite cache before creating separate persistence layers

### 7. Keep Derived State Derived

Derived indexes and caches are conveniences, not authority.

- canonical repository records remain authoritative
- cache schema may expand, but cache behavior must not redefine canonical logic
- if cache and canonical logic disagree, canonical logic wins

### 8. Bias Toward Determinism And Repo Chronology

When ordering or ownership must be decided:

- prefer repository commit chronology over payload timestamps
- prefer explicit graph recomputation over ad hoc local mutation
- choose rule shapes that can be implemented the same way again later

## Default Answers For Common Openings

These defaults are compiled from the repo’s recent planning decisions and should be reused unless a later doc overrides them.

- Username collisions: accept the input when possible; disambiguate in public rendering rather than reject.
- Canonical username root: earliest username claim in repository commit chronology.
- Duplicate-name public rendering: one root set plus `other users with this name`.
- Merge evidence: username overlap alone is enough for auto-issued merge requests for now.
- Merge scope: one approval applies to the whole resolved set.
- Merge revocation: one-sided, immediate, append-only, implemented as a later record that deactivates a specific approved merge edge.
- Revocation aftermath: recompute the graph using existing rules; no special second system.
- Notifications: attach to `My profile`, not a full inbox.
- Cache strategy: extend the existing SQLite cache database before splitting into separate files.
- Historical edge cases: prefer current graph-derived visible state over extra side rules.

## Required Outputs Per Loop

Each unattended loop should still leave behind these artifacts:

- at least one commit for the completed loop
- code changes or doc changes that implement the loop
- focused tests or verification covering the new visible behavior
- an implementation summary note or checklist update if the loop changed policy-adjacent behavior
- any newly deferred questions appended to the relevant working-notes file

## Branch Discipline

- Run the full unattended checklist on a dedicated feature branch.
- Create that branch before starting implementation work for the checklist whenever possible.
- Keep all loop commits for that checklist on the same branch until the run is complete or intentionally paused.
- Do not mix unrelated feature work into the unattended-run branch.
- Record the branch name in the unattended run log.
- If the run was started on the wrong branch, switch to a dedicated branch from the current HEAD and continue there rather than reopening settled loop decisions.

## Commit Discipline

- Each completed loop should produce at least one commit.
- Prefer one commit per meaningful internal step when the loop naturally breaks into visible, testable stages.
- If a loop is too small or too coupled to split cleanly, one loop-level commit is acceptable.
- Do not batch multiple unrelated loops into one commit.
- Prefer each commit to leave the branch in a locally verifiable state.
- If a loop is not split into multiple commits despite having multiple obvious steps, record the reason in the run log.

## Stop Conditions

Pause unattended execution only if one of these happens:

- two prior planning docs give incompatible answers
- the next implementation choice would introduce new product policy rather than apply existing policy
- the smallest useful slice is unclear
- the loop would force a rewrite of already-landed behavior outside its stated scope
- verification fails in a way that suggests the checklist order is wrong

## Applying This To The Username Collision Checklist

For [username_collision_fdp_loop_checklist.md](/home/wsl/v2/docs/plans/username_collision_fdp_loop_checklist.md), the unattended process should behave like this:

- start with the SQLite identity and username-root cache because later loops need one cheap derived source
- implement read semantics before write-side automation
- expose root/non-root behavior publicly before adding notification and suggestion polish
- add auto-issued merge requests and nav notifications before advanced warning UX
- add `revoke_merge` before deeper trust or moderation refinements
- leave optional warning, debug, and manual-merge expansions for later unless they become necessary to complete a listed loop

## Suggested One-Shot Execution Pattern

For a ten-loop checklist:

1. Lock the checklist order.
2. Create and switch to a dedicated feature branch for the run.
3. Gather all controlling planning docs up front.
4. Create one short “unattended run” note listing the default answers that apply.
5. Execute loops in order without reopening settled questions.
6. Commit at least once per loop, and more often when the loop has clear internal stages.
7. After each loop, update checklist state and record only newly discovered unresolved items.
8. Continue until a stop condition is hit or the checklist is complete.

The main idea is simple: reuse the repo’s previous judgment instead of re-litigating each small decision.
