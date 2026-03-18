## Stage 1
- Goal: define the canonical merge-request state model, moderator-approval state, and historical-username discovery helpers.
- Dependencies: approved Step 2; existing profile-update history, identity-link resolution, moderation authority model, and signed-record parsing patterns.
- Expected changes: add one canonical record family for merge-request lifecycle events such as request, approve, moderator_approve, and dismiss; add shared helpers that derive visible username-history matches from profile-update records; define deterministic resolution rules that distinguish pending requests from active merged identities under both user-approval and moderator-approval paths; planned contracts such as `loadMergeRequestRecords(records_dir) -> list[MergeRequestRecord]`, `deriveHistoricalUsernameMatches(identity_id, context) -> tuple[MergeCandidate, ...]`, and `deriveMergeRequestState(...) -> MergeRequestState`.
- Verification approach: parse sample merge-request records, confirm repeated reads over the same visible repo state yield the same pending/incoming/dismissed/moderator-approved state, and confirm historical username matching returns the expected candidate identities from visible profile-update history.
- Risks or open questions:
  - deciding whether dismissed requests should suppress only the exact request record or all future requests between the same identity pair until a new request is issued
  - keeping historical-username matching deterministic when multiple identities reuse common names over time
  - choosing the precise moderator approval rule so it is auditable and narrow without undermining the two-party approval model
- Canonical components/API contracts touched: merge-request record shape; moderator-approval state; historical-username discovery rules; derived merge-request state model.

## Stage 2
- Goal: implement the signed merge-request write contract and combined user/moderator activation rules.
- Dependencies: Stage 1.
- Expected changes: add one explicit write contract for merge-request actions that verifies the signer, validates the target identity, stores canonical records under a dedicated records directory, and activates an identity merge only when the configured approval condition is satisfied by user approvals or a moderator approval event; planned contracts such as `validateMergeRequestPayload(text) -> MergeRequestRecord`, `submitMergeRequest(...) -> MergeRequestSubmissionResult`, and `deriveApprovedMergeLinks(...) -> list[IdentityLinkRecord]` or equivalent derived approval output.
- Verification approach: submit valid signed request, approve, moderator-approve, and dismiss actions between visible identities; confirm one-sided approval does not activate a merge; confirm mutual approval does; confirm the moderator path follows the chosen rule; confirm dismissed requests no longer appear as pending for the dismissing identity; confirm invalid signer/target combinations return stable plain-text errors.
- Risks or open questions:
  - choosing the narrowest lifecycle model that supports mutual approval without duplicating the existing identity-link semantics unnecessarily
  - ensuring request and approval ordering remains deterministic if records are written concurrently or arrive after dismissal
  - keeping moderator approval narrow enough that it remains an exception path rather than the default merge mechanism
- Canonical components/API contracts touched: merge-request write endpoint; success/error response shape; merge activation rule for approved identity pairs; moderator-approval contract.

## Stage 3
- Goal: expose merge discovery, pending approval state, and moderator-approved state through canonical read surfaces.
- Dependencies: Stage 2.
- Expected changes: extend profile or identity read helpers so the system can return historical username matches, outgoing requests, incoming requests, moderator-approved requests, and dismissed/request status for one managed identity; add any needed API read surface for the dedicated web flow while reusing the existing identity context and profile-update history loaders; planned contracts such as `loadMergeManagementState(identity_id) -> MergeManagementSummary` and `renderApiGetMergeManagement(identity_id) -> str` or equivalent JSON/text response shape.
- Verification approach: request merge-management state for identities with outgoing, incoming, approved, moderator-approved, and dismissed records; confirm same-name candidates are derived from visible history; confirm approved pairs no longer appear as merely pending; confirm repeated reads over unchanged state are deterministic.
- Risks or open questions:
  - deciding how much candidate metadata to expose without turning the read model into a general account inbox
  - keeping the read shape understandable when many identities share one reused historical username
  - deciding whether moderator-approved requests should be visible differently from user-approved requests in the management summary
- Canonical components/API contracts touched: merge-management read model; API discovery text; canonical read response for merge workflow state; moderator-visible approval state.

## Stage 4
- Goal: add the dedicated web merge-management page plus user and moderator actions.
- Dependencies: Stage 3.
- Expected changes: add one focused web page linked from the profile surface that shows historical-username matches plus outgoing and incoming requests, and supports signed request, approve, and dismiss actions through the existing browser signing pattern; add the moderator-facing approval affordance through the existing moderation-aware web path if available or a tightly scoped adjacent control; planned contracts such as `render_merge_management_page(identity_id) -> str` and small browser-signing payload builders for merge-request actions.
- Verification approach: open the merge-management page for a visible identity, confirm candidate matches render from username history, submit a request through the browser flow, then confirm the target identity sees an incoming request that can be approved or dismissed; separately confirm a moderator can approve using the defined moderation path and that the chosen approval rule resolves both profiles to one logical identity.
- Risks or open questions:
  - keeping the page clear when the same viewer has multiple local keys and multiple manageable identities
  - avoiding UI confusion between public duplicate-name discovery and private signer-authorized actions
  - keeping moderator controls clearly distinct from normal user approvals so operator authority is explicit
- Canonical components/API contracts touched: dedicated merge-management web surface; profile-page linkout; browser signed-action flow for merge requests; moderator-facing merge approval control.
