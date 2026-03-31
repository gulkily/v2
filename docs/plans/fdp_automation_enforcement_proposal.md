# FDP Automation Enforcement Proposal

## Problem

The current Feature Development Process relies too heavily on the assistant remembering and correctly sequencing procedural rules from prompt text. That works until it does not. The recurring failure mode is Step 4: implementation starts before the branch/commit gates are satisfied, stage boundaries are not enforced, and the process is followed socially instead of mechanically.

## Goal

Move the critical FDP controls out of prose-only instructions and into executable repository automation so Step 4 cannot begin or advance incorrectly without producing an explicit validation failure.

## Proposed Solution

Introduce three FDP task-runner commands plus one machine-readable state file:

1. `./forum fdp-step4-begin <feature_name>`
2. `./forum fdp-stage-complete <feature_name> --stage N`
3. `./forum fdp-verify <feature_name>`
4. `state/fdp/<feature_name>.json`

These become the canonical enforcement path for Step 4. If they exist, the assistant must use them rather than emulating the workflow manually.

## State File

Location:
- `state/fdp/<feature_name>.json`

Suggested fields:
- `feature_name`
- `approved_step`
- `step_docs.step1`
- `step_docs.step2`
- `step_docs.step3`
- `step_docs.step4`
- `step4.branch`
- `step4.started`
- `step4.planning_commit`
- `step4.stages_expected`
- `step4.stages_completed`
- `step4.current_stage`
- `step4.last_verified_at`

Purpose:
- make FDP state explicit instead of inferred from chat memory
- give both humans and automation one source of truth
- allow verification commands and CI to reason about allowed next actions

## Command Design

### `./forum fdp-step4-begin <feature_name>`

Responsibilities:
- require `approved_step >= 3`
- verify Step 1-3 docs exist
- create or switch to the Step 4 branch
- verify planning docs are the only files included in the initial Step 4 commit
- create the planning-doc commit
- record branch, planning commit, and expected stage count in the state file

Expected output:
- branch name
- planning commit hash
- next allowed action (`stage 1`)

### `./forum fdp-stage-complete <feature_name> --stage N`

Responsibilities:
- require Step 4 to be started
- require current branch to match recorded Step 4 branch
- require `N` to be the next incomplete stage
- verify the Step 4 summary contains a `## Stage N - ...` section
- verify that staged changes include the Step 4 summary and stage implementation files
- create the stage-scoped commit
- append `N` to `stages_completed` in the state file

Expected output:
- new commit hash
- completed stage list
- next allowed stage

### `./forum fdp-verify <feature_name>`

Responsibilities:
- validate branch, state file, and planning-doc commit presence
- validate Step 4 summary structure
- validate stage completion ordering
- validate commit count is at least `1 + number_of_completed_stages`
- validate the planning-doc commit is the first Step 4 commit
- support `--json` output for CI

Expected output:
- pass/fail summary
- concrete failure reasons

## Validation Scope

Automate only what can be checked reliably:
- branch name
- file existence
- state transitions
- Step 4 summary structure
- commit ordering/count
- stage numbering

Do not try to infer semantic correctness of a stage from diff content. That remains a review concern.

## Repository Integration

Suggested implementation locations:
- `scripts/forum_tasks.py` for the CLI surface
- `forum_core/fdp_state.py` for reading/writing the state file
- `forum_core/fdp_verify.py` for reusable verification logic

Optional CI follow-up:
- run `./forum fdp-verify <feature_name>` in CI for active FDP branches

## Prompting Change

Update the FDP system prompt to say:

- if FDP automation commands exist, use them
- do not emulate Step 4 branch/commit/stage workflow manually when the commands are available
- if an FDP automation command fails, stop and report the failure instead of continuing

This keeps the prompt short while moving the real enforcement into code.

## Recommended Rollout

### Phase 1
- implement `fdp-step4-begin`
- implement `fdp-verify`
- add the FDP state file
- add Step 4 summary structure checks

### Phase 2
- implement `fdp-stage-complete`
- enforce stage sequencing and commit cadence
- add CI integration

## Expected Outcome

The assistant should no longer be able to “accidentally” start or advance Step 4 incorrectly without either:
- the automation refusing the action, or
- the verification command exposing the violation immediately.
