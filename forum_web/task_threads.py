from __future__ import annotations

from forum_core.moderation import thread_is_hidden
from forum_web.repository import Thread, is_task_root


def load_task_threads(threads: list[Thread], moderation_state) -> list[Thread]:
    return sorted(
        [
            thread
            for thread in threads
            if is_task_root(thread.root) and not thread_is_hidden(moderation_state, thread.root.post_id)
        ],
        key=lambda thread: thread.root.post_id,
    )


def index_task_threads(threads: list[Thread]) -> dict[str, Thread]:
    return {thread.root.post_id: thread for thread in threads}
