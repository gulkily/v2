from __future__ import annotations

from pathlib import Path
from string import Template


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"


def load_template(name: str) -> Template:
    template_path = TEMPLATE_DIR / name
    return Template(template_path.read_text(encoding="utf-8"))


def render_page(*, title: str, hero_kicker: str, hero_title: str, hero_text: str, content_html: str) -> str:
    base = load_template("base.html")
    return base.substitute(
        title=title,
        hero_kicker=hero_kicker,
        hero_title=hero_title,
        hero_text=hero_text,
        content_html=content_html,
    )


def load_asset_text(name: str) -> str:
    asset_path = TEMPLATE_DIR / "assets" / name
    return asset_path.read_text(encoding="utf-8")
