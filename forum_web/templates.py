from __future__ import annotations

import html
from pathlib import Path
from string import Template


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def load_template(name: str) -> Template:
    template_path = TEMPLATE_DIR / name
    return Template(template_path.read_text(encoding="utf-8"))


def render_primary_nav(*, aria_label: str = "Primary") -> str:
    links = [
        ("/", "Home"),
        ("/compose/thread", "Post"),
        ("/instance/", "Project info"),
        ("/activity/", "Activity"),
    ]
    items = "".join(
        f'<a href="{html.escape(path)}">{html.escape(label)}</a>'
        for path, label in links
    )
    items += '<a href="" data-profile-nav-link hidden>My profile</a>'
    return f'<nav class="site-header-nav" aria-label="{html.escape(aria_label)}">{items}</nav>'


def render_site_header(
    *,
    hero_kicker: str,
    hero_title: str,
    hero_text: str,
    include_page_intro: bool = True,
) -> str:
    intro_html = ""
    if include_page_intro:
        intro_html = (
            '<div class="site-header-page-intro">'
            f'<p class="site-header-kicker">{html.escape(hero_kicker)}</p>'
            f'<h1 class="site-header-heading">{html.escape(hero_title)}</h1>'
            f'<p class="site-header-text">{html.escape(hero_text)}</p>'
            "</div>"
        )
    return (
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
        f"{render_primary_nav()}"
        "</div>"
        f"{intro_html}"
        "</header>"
    )


def render_site_footer() -> str:
    return (
        '<footer class="site-footer">'
        '<div class="site-footer-inner">'
        '<p>Best read with a clear mind and a modest browser window.</p>'
        '<p>[ slow web ]</p>'
        "</div>"
        "</footer>"
    )


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
        page_header_html = render_site_header(
            hero_kicker=hero_kicker,
            hero_title=hero_title,
            hero_text=hero_text,
        )
    if not page_footer_html:
        page_footer_html = render_site_footer()
    page_script_html = render_profile_nav_script_tag() + page_script_html
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


def render_profile_nav_script_tag() -> str:
    return '<script type="module" src="/assets/profile_nav.js"></script>'
