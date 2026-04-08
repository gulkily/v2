from __future__ import annotations

import unittest

from forum_web.templates import render_page, render_primary_nav, render_site_header


class PrimaryNavActiveStateTests(unittest.TestCase):
    def test_render_primary_nav_marks_only_matching_section_active(self) -> None:
        html = render_primary_nav(active_section="activity")

        self.assertEqual(html.count('aria-current="page"'), 1)
        self.assertIn('<nav class="site-header-nav" data-primary-nav aria-label="Primary">', html)
        self.assertIn('<a data-primary-nav-link href="/activity/" aria-current="page">Activity</a>', html)
        self.assertNotIn('<a data-primary-nav-link href="/" aria-current="page">Home</a>', html)
        self.assertNotIn('<a data-primary-nav-link href="/compose/thread" aria-current="page">Post</a>', html)
        self.assertNotIn('<a data-primary-nav-link href="/instance/" aria-current="page">Project info</a>', html)
        self.assertNotIn('data-profile-nav-link aria-current="page"', html)

    def test_render_site_header_leaves_nav_inactive_without_active_section(self) -> None:
        html = render_site_header(
            hero_kicker="Read",
            hero_title="Home",
            hero_text="Shared shell",
        )

        self.assertNotIn('aria-current="page"', html)

    def test_render_primary_nav_can_mark_profile_link_active(self) -> None:
        html = render_primary_nav(active_section="profile", current_profile_href="/profiles/openpgp-alpha?self=1")

        self.assertEqual(html.count('aria-current="page"'), 1)
        self.assertIn(
            '<a data-primary-nav-link data-profile-nav-link data-profile-nav-state="resolved" data-merge-feature-enabled="0" '
            'aria-current="page" href="/profiles/openpgp-alpha?self=1">My profile</a>',
            html,
        )
        self.assertNotIn('<a data-primary-nav-link href="/" aria-current="page">Home</a>', html)

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
        self.assertIn('<a data-primary-nav-link href="/compose/thread" aria-current="page">Post</a>', html)


if __name__ == "__main__":
    unittest.main()
