## Problem
Thread titles are currently derived from the root post subject and behave as immutable content, which prevents both thread owners and operators from correcting or improving a thread title after publication. The next slice should add a canonical way to change the current displayed thread title while keeping title resolution consistent across all existing read surfaces.

## User Stories
- As a user, I want to rename a thread I created so that I can correct mistakes or make the thread easier for others to understand.
- As an operator, I want to rename a thread when needed so that I can improve clarity, safety, or organization without deleting and recreating content.
- As an operator, I want an optional feature flag that allows any user to rename any thread so that communities that prefer looser ownership rules can opt into that policy explicitly.
- As a reader, I want the current thread title to be consistent everywhere it appears so that indexes, thread pages, and API reads do not disagree about what a thread is called.
- As a maintainer, I want title changes to remain auditable so that mutable thread metadata does not weaken the repository's append-only record model.

## Core Requirements
- The product must support changing the current displayed title of an existing thread for both the thread owner and an authorized operator.
- The product must provide one shared feature flag that, when enabled, allows any user to change the title of any thread; when disabled, normal ownership/operator rules remain in effect.
- The feature must preserve the original root post record as immutable canonical content while exposing one resolved current title for reads.
- All existing thread-title read surfaces must show the same resolved current title for a thread after a valid rename.
- The feature must enforce clear authority rules in both flag states so rename eligibility is predictable and consistent across all entry points.
- The slice must stay focused on thread-title changes only and must not expand into broader thread editing, reply editing, or post-body editing.

## Shared Component Inventory
- Existing canonical thread read model in `forum_web.repository` and related loaders: extend this canonical thread data flow because thread titles already originate from `root.subject` and all higher-level read surfaces depend on it.
- Existing thread page, board index, and task/planning thread pages in `forum_web.web`: reuse and extend these canonical renderers so they display one resolved current title instead of inventing per-page title logic.
- Existing text read surface in `forum_web.api_text`: extend the same canonical title resolution so API consumers receive the same current title as HTML readers.
- Existing PHP/native read path in `forum_core.php_native_reads`: extend it to use the same resolved title so alternate hosts do not drift from the main Python read path.
- Existing signed metadata-update precedent in the profile update flow: reuse this product pattern for mutable metadata because it already demonstrates how the system handles auditable updates without rewriting original records.
- Existing compose/profile update affordances: extend with one canonical title-change entry point rather than creating parallel rename flows for the same authority class.
- Existing environment-driven feature-flag pattern used across web and API surfaces: reuse one shared flag so permissive rename policy can be switched on deliberately without inventing a separate release-control mechanism.

## Simple User Flow
1. A user or operator opens an existing thread they are allowed to rename.
2. They choose the thread-title change action and submit a new title through the canonical rename flow.
3. The system accepts the valid title change and records it as the current title for that thread.
4. The user returns to the thread page, board index, or another read surface.
5. Every existing thread-title read surface shows the same updated title for that thread.

## Success Criteria
- A thread owner can successfully change the title of their own thread.
- An authorized operator can successfully change the title of a thread they are allowed to manage.
- With the permissive feature flag disabled, a non-owner non-operator cannot change the title of another user's thread.
- With the permissive feature flag enabled, any user can successfully change the title of any thread through the same canonical rename flow.
- After a valid rename, thread page, board/task indexes, PHP/native reads, and the text API all show the same updated title.
- The feature preserves an auditable history of title changes without rewriting the original root post record.
