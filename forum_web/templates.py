from __future__ import annotations

import html
import os
from pathlib import Path
from string import Template


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def env_flag_enabled(name: str, *, default: bool = False) -> bool:
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def merge_feature_enabled(env: dict[str, str] | None = None) -> bool:
    source_env = os.environ if env is None else env
    raw_value = source_env.get("FORUM_ENABLE_ACCOUNT_MERGE", "").strip().lower()
    return raw_value in {"1", "true", "yes", "on"}


def site_title(env: dict[str, str] | None = None) -> str:
    source_env = os.environ if env is None else env
    configured = source_env.get("FORUM_SITE_TITLE", "").strip()
    if configured:
        return configured
    return "Forum Reader"


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
    items += (
        '<a href="" data-profile-nav-link data-profile-nav-state="unresolved" '
        f'data-merge-feature-enabled="{"1" if merge_feature_enabled() else "0"}" '
        'aria-disabled="true" tabindex="-1">My profile</a>'
    )
    return f'<nav class="site-header-nav" aria-label="{html.escape(aria_label)}">{items}</nav>'


def render_site_header(
    *,
    hero_kicker: str,
    hero_title: str,
    hero_text: str,
    hero_action_html: str = "",
    include_page_intro: bool = True,
) -> str:
    intro_html = ""
    header_band_html = ""
    if include_page_intro:
        intro_html = (
            '<div class="site-header-page-intro">'
            f'<p class="site-header-kicker">{html.escape(hero_kicker)}</p>'
            f'<h1 class="site-header-heading">{html.escape(hero_title)}</h1>'
            f'<p class="site-header-text">{html.escape(hero_text)}</p>'
            f"{hero_action_html}"
            "</div>"
        )
    if env_flag_enabled("FORUM_ENABLE_KINDNESS_HEADER", default=False):
        header_band_html = (
            '<div class="site-header-band"><p>Kindness first. Clear navigation, readable text, and calm visual rhythm.</p></div>'
        )
    return (
        '<header class="site-header site-header--page">'
        f"{header_band_html}"
        '<div class="site-header-main">'
        '<div class="site-header-lockup">'
        '<p class="site-header-mark">(*)</p>'
        '<div class="site-header-copy">'
        f'<p class="site-header-title"><a href="/">{html.escape(site_title())}</a></p>'
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


def render_username_claim_cta_html() -> str:
    return (
        '<section class="site-username-claim panel" data-username-claim-cta hidden>'
        '<div class="site-username-claim-copy">'
        '<p class="site-username-claim-kicker">Account setup</p>'
        '<p class="site-username-claim-text">Now that you\'re participating, you can choose a username.</p>'
        "</div>"
        '<a class="thread-chip site-username-claim-link" data-username-claim-link href="">Choose your username</a>'
        "</section>"
    )


def render_page(
    *,
    title: str,
    hero_kicker: str,
    hero_title: str,
    hero_text: str,
    hero_action_html: str = "",
    content_html: str,
    page_script_html: str = "",
    page_shell_class: str = "",
    page_header_html: str | None = None,
    page_banner_html: str | None = None,
    page_footer_html: str = "",
) -> str:
    base = load_template("base.html")
    if page_header_html is None:
        page_header_html = render_site_header(
            hero_kicker=hero_kicker,
            hero_title=hero_title,
            hero_text=hero_text,
            hero_action_html=hero_action_html,
        )
    if not page_footer_html:
        page_footer_html = render_site_footer()
    if page_banner_html is None:
        page_banner_html = render_username_claim_cta_html()
    page_script_html = (
        render_profile_nav_script_tag()
        + render_copy_field_script_tag()
        + render_username_claim_cta_script_tag()
        + page_script_html
    )
    return base.substitute(
        title=html.escape(title),
        page_header_html=page_header_html,
        page_banner_html=page_banner_html,
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


def render_copy_field_script_tag() -> str:
    return '<script type="module" src="/assets/copy_field.js"></script>'


def render_username_claim_cta_script_tag() -> str:
    return '<script type="module" src="/assets/username_claim_cta.js"></script>'
