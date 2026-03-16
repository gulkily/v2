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
            '<header class="hero">'
            f'<p class="hero-kicker">{html.escape(hero_kicker)}</p>'
            f'<h1 class="hero-title">{html.escape(hero_title)}</h1>'
            f'<p class="hero-text">{html.escape(hero_text)}</p>'
            "</header>"
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
