from __future__ import annotations

import unittest

from forum_web.templates import render_page, render_primary_nav, render_site_header


class PrimaryNavActiveStateTests(unittest.TestCase):
    def test_render_primary_nav_marks_only_matching_section_active(self) -> None:
        html = render_primary_nav(active_section="activity")

        self.assertEqual(html.count('aria-current="page"'), 1)
        self.assertIn('<a href="/activity/" aria-current="page">Activity</a>', html)
        self.assertNotIn('<a href="/" aria-current="page">Home</a>', html)
        self.assertNotIn('<a href="/compose/thread" aria-current="page">Post</a>', html)
        self.assertNotIn('<a href="/instance/" aria-current="page">Project info</a>', html)
        self.assertNotIn('data-profile-nav-link aria-current="page"', html)

    def test_render_site_header_leaves_nav_inactive_without_active_section(self) -> None:
        html = render_site_header(
            hero_kicker="Read",
            hero_title="Home",
            hero_text="Shared shell",
        )

        self.assertNotIn('aria-current="page"', html)

    def test_render_page_passes_active_section_to_default_header(self) -> None:
        html = render_page(
            title="Compose",
            hero_kicker="Write",
            hero_title="Compose",
            hero_text="Start a thread",
            content_html="<section>Body</section>",
            active_section="post",
        )

        self.assertEqual(html.count('aria-current="page"'), 1)
        self.assertIn('<a href="/compose/thread" aria-current="page">Post</a>', html)


if __name__ == "__main__":
    unittest.main()
