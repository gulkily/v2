from __future__ import annotations

import html
from pathlib import Path
from string import Template


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def load_template(name: str) -> Template:
    template_path = TEMPLATE_DIR / name
    return Template(template_path.read_text(encoding="utf-8"))


def render_page(
    *,
    title: str,
    hero_kicker: str,
    hero_title: str,
    hero_text: str,
    content_html: str,
    page_script_html: str = "",
    page_shell_class: str = "",
    page_header_html: str | None = None,
    page_footer_html: str = "",
) -> str:
    base = load_template("base.html")
    if page_header_html is None:
        page_header_html = (
            '<header class="site-header site-header--page">'
            '<div class="site-header-band"><p>Kindness first. Clear navigation, readable text, and calm visual rhythm.</p></div>'
            '<div class="site-header-main">'
            '<div class="site-header-lockup">'
            '<p class="site-header-mark">(*)</p>'
            '<div class="site-header-copy">'
            '<p class="site-header-title"><a href="/">Forum Reader</a></p>'
            '<p class="site-header-tagline">calm threads from canonical text records</p>'
            "</div>"
            "</div>"
            '<nav class="site-header-nav" aria-label="Primary">'
            '<a href="/">Home</a>'
            '<a href="/compose/thread">Post</a>'
            '<a href="/instance/">Instance</a>'
            '<a href="/planning/task-priorities/">Planning</a>'
            "</nav>"
            "</div>"
            '<div class="site-header-page-intro">'
            f'<p class="site-header-kicker">{html.escape(hero_kicker)}</p>'
            f'<h1 class="site-header-heading">{html.escape(hero_title)}</h1>'
            f'<p class="site-header-text">{html.escape(hero_text)}</p>'
            "</header>"
        )
    if not page_footer_html:
        page_footer_html = (
            '<footer class="site-footer">'
            '<div class="site-footer-inner">'
            '<p>Best read with a clear mind and a modest browser window.</p>'
            '<p>[ slow web ]</p>'
            "</div>"
            "</footer>"
        )
    return base.substitute(
        title=html.escape(title),
        page_header_html=page_header_html,
        content_html=content_html,
        page_footer_html=page_footer_html,
        page_script_html=page_script_html,
        page_shell_class=html.escape(page_shell_class),
    )


def load_asset_text(name: str) -> str:
    asset_path = TEMPLATE_DIR / "assets" / name
    return asset_path.read_text(encoding="utf-8")
