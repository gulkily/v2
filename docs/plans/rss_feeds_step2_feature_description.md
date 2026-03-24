# RSS Feeds Step 2: Feature Description

## Problem
The site already has useful read surfaces for instance activity, board browsing, and thread reading, but users cannot subscribe to those views in feed readers. The next slice should add RSS to the existing read model so people can follow forum activity without turning this into a separate publishing system.

## User stories
- As a reader, I want an RSS feed for overall site activity so I can follow new content and visible instance events without manually checking the site.
- As a board-focused reader, I want an RSS feed for a board view so I can subscribe only to threads relevant to that topic area.
- As a thread participant, I want an RSS feed for an individual thread so I can track replies in my feed reader.
- As a maintainer, I want RSS to reuse the current read-side visibility and ordering rules so the feed output matches what the site already shows.

## Core requirements
- The slice must expose RSS for the existing canonical read surfaces that matter most for subscriptions: site activity, board index views, and individual thread views.
- Each RSS feed must reflect the same visible repository state, moderation effects, and ordering rules already used by the corresponding HTML page.
- Feed items must link back to the existing canonical web URLs for the underlying activity item, thread, or post rather than introducing feed-only destinations.
- The slice must keep RSS as an alternate read representation of current pages, not a separate content pipeline, export workflow, or new storage model.
- The site must make feed discovery possible from the related HTML surfaces so users can find the subscription URL from the page they are already viewing.

## Shared component inventory
- `/activity/`: extend the canonical combined activity page with an RSS representation because it already serves as the instance-wide timeline for content, moderation, and code activity.
- `/` and board-filtered index views: extend the existing board index read surface with RSS because it already represents the canonical thread listing users browse by topic.
- `/threads/{thread-id}`: extend the canonical thread page with RSS because it is the natural subscription surface for reply activity within one discussion.
- `/posts/{post-id}`: keep as an item destination, not a separate feed surface, because posts are the targets that feed items should open rather than standalone subscription streams.
- Existing plain-text API read surfaces: reuse the same repository-backed read logic conceptually for alignment, but do not make the RSS feature depend on creating new API-first contracts.

## Simple user flow
1. A reader opens the activity page, a board view, or a thread page.
2. The page exposes a discoverable RSS link for that same scope.
3. The reader subscribes in a feed reader using that URL.
4. New visible activity, threads, or replies appear in the reader with links back to the existing web pages.

## Success criteria
- Users can subscribe to RSS for site activity, a board view, and an individual thread.
- Feed entries match the same visible items and ordering the corresponding HTML pages already present.
- Feed items open the current canonical thread, post, or activity URLs rather than a parallel feed-only UI.
- The feature adds no new record format, background export step, or separate publication workflow.
