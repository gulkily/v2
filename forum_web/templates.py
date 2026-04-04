from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
import html
import json
import os
from pathlib import Path
from string import Template
from textwrap import dedent, indent
from forum_core.runtime_env import env_flag_enabled as runtime_env_flag_enabled


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
PAGE_SHELL_CONTENT_PATH = TEMPLATE_DIR / "page_shell_content.json"
ASSET_ROUTE_MANIFEST_PATH = TEMPLATE_DIR / "asset_routes.json"
USERNAME_CLAIM_CTA_STORAGE_KEY = "forum_username_claim_cta"
_CURRENT_USERNAME_CLAIM_BANNER_STATE: ContextVar["UsernameClaimBannerState | None"] = ContextVar(
    "current_username_claim_banner_state",
    default=None,
)


@dataclass(frozen=True)
class UsernameClaimBannerState:
    visible: bool
    update_href: str = ""


def load_page_shell_content() -> dict[str, object]:
    loaded = json.loads(PAGE_SHELL_CONTENT_PATH.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("page shell content must decode to an object")
    return loaded


def load_asset_route_manifest() -> list[dict[str, object]]:
    loaded = json.loads(ASSET_ROUTE_MANIFEST_PATH.read_text(encoding="utf-8"))
    if not isinstance(loaded, list):
        raise ValueError("asset route manifest must decode to a list")
    manifest: list[dict[str, object]] = []
    for entry in loaded:
        if isinstance(entry, dict):
            manifest.append(entry)
    return manifest


def resolve_asset_route(path: str) -> tuple[bytes, str] | None:
    for entry in load_asset_route_manifest():
        if str(entry.get("path", "")) != path:
            continue
        asset_name = str(entry["asset"])
        content_kind = str(entry["content_kind"])
        content_type = str(entry["content_type"])
        if content_kind == "bytes":
            return load_asset_bytes(asset_name), content_type
        return load_asset_text(asset_name).encode("utf-8"), content_type
    return None


def env_flag_enabled(name: str, *, default: bool = False) -> bool:
    return runtime_env_flag_enabled(name, default=default)


def merge_feature_enabled(env: dict[str, str] | None = None) -> bool:
    return runtime_env_flag_enabled("FORUM_ENABLE_ACCOUNT_MERGE", env=env)


def username_claim_cta_enabled(env: dict[str, str] | None = None) -> bool:
    return runtime_env_flag_enabled("FORUM_ENABLE_USERNAME_CLAIM_CTA", env=env, default=True)


def site_title(env: dict[str, str] | None = None) -> str:
    source_env = os.environ if env is None else env
    configured = source_env.get("FORUM_SITE_TITLE", "").strip()
    if configured:
        return configured
    return "Forum Reader"


def load_template(name: str) -> Template:
    template_path = TEMPLATE_DIR / name
    return Template(template_path.read_text(encoding="utf-8"))


def _html_block(raw_text: str) -> str:
    return dedent(raw_text).strip()


def _join_html_blocks(*blocks: str) -> str:
    return "\n".join(block.strip() for block in blocks if block and block.strip())


def _indent_html_block(block: str, spaces: int) -> str:
    return indent(block.strip(), " " * spaces)


def render_username_claim_bar_html(
    *,
    href: str,
    data_attribute_html: str = "",
) -> str:
    claim_content = load_page_shell_content()["username_claim"]
    if not isinstance(claim_content, dict):
        raise ValueError("username_claim shell content must be an object")
    data_attribute = f" {data_attribute_html.strip()}" if data_attribute_html.strip() else ""
    return _html_block(
        f"""
        <section class="site-username-claim panel"{data_attribute}>
          <div class="site-username-claim-copy">
            <p class="site-username-claim-kicker">{html.escape(str(claim_content["kicker"]))}</p>
            <p class="site-username-claim-text">{html.escape(str(claim_content["text"]))}</p>
          </div>
          <a class="thread-chip site-username-claim-link" data-username-claim-link href="{html.escape(href, quote=True)}">{html.escape(str(claim_content["action_label"]))}</a>
        </section>
        """
    )


def render_primary_nav(*, aria_label: str = "Primary", active_section: str | None = None) -> str:
    shell_content = load_page_shell_content()
    raw_links = shell_content["primary_nav"]
    if not isinstance(raw_links, list):
        raise ValueError("primary_nav shell content must be a list")
    links = []
    for item in raw_links:
        if not isinstance(item, dict):
            continue
        links.append(
            (
                str(item.get("section", "")),
                str(item["href"]),
                str(item["label"]),
            )
        )
    items = "\n".join(
        (
            f'<a href="{html.escape(path)}" aria-current="page">{html.escape(label)}</a>'
            if section and section == active_section
            else f'<a href="{html.escape(path)}">{html.escape(label)}</a>'
        )
        for section, path, label in links
    )
    items += (
        "\n"
        '<a href="" data-profile-nav-link data-profile-nav-state="unresolved" '
        f'data-merge-feature-enabled="{"1" if merge_feature_enabled() else "0"}" '
        'aria-disabled="true" tabindex="-1">My profile</a>'
    )
    return _html_block(
        f"""
        <nav class="site-header-nav" aria-label="{html.escape(aria_label)}">
        {_indent_html_block(items, 2)}
        </nav>
        """
    )


def render_site_header(
    *,
    hero_kicker: str,
    hero_title: str,
    hero_text: str,
    hero_action_html: str = "",
    include_page_intro: bool = True,
    active_section: str | None = None,
) -> str:
    shell_content = load_page_shell_content()
    intro_html = ""
    header_band_html = ""
    if include_page_intro:
        intro_html = _join_html_blocks(
            _html_block(
                f"""
                <div class="site-header-page-intro">
                  <p class="site-header-kicker">{html.escape(hero_kicker)}</p>
                  <h1 class="site-header-heading">{html.escape(hero_title)}</h1>
                  <p class="site-header-text">{html.escape(hero_text)}</p>
                """
            ),
            hero_action_html,
            "</div>",
        )
    if env_flag_enabled("FORUM_ENABLE_KINDNESS_HEADER", default=False):
        header_band_html = _html_block(
            """
            <div class="site-header-band">
              <p>Kindness first. Clear navigation, readable text, and calm visual rhythm.</p>
            </div>
            """
        )
    return _join_html_blocks(
        '<header class="site-header site-header--page">',
        header_band_html,
        _html_block(
            f"""
            <div class="site-header-main">
              <div class="site-header-lockup">
                  <p class="site-header-mark">(*)</p>
                  <div class="site-header-copy">
                    <p class="site-header-title"><a href="/">{html.escape(site_title())}</a></p>
                  <p class="site-header-tagline">{html.escape(str(shell_content["site_tagline"]))}</p>
                  </div>
                </div>
              {_indent_html_block(render_primary_nav(active_section=active_section), 2)}
            </div>
            """
        ),
        intro_html,
        "</header>",
    )


def render_site_footer() -> str:
    shell_content = load_page_shell_content()
    footer_lines = shell_content["footer_lines"]
    if not isinstance(footer_lines, list):
        raise ValueError("footer_lines shell content must be a list")
    footer_html = "\n".join(f"<p>{html.escape(str(line))}</p>" for line in footer_lines)
    return _html_block(
        f"""
        <footer class="site-footer">
          <div class="site-footer-inner">
            {footer_html}
          </div>
        </footer>
        """
    )


def set_current_username_claim_cta_state(state: UsernameClaimBannerState | None) -> Token:
    return _CURRENT_USERNAME_CLAIM_BANNER_STATE.set(state)


def reset_current_username_claim_cta_state(token: Token) -> None:
    _CURRENT_USERNAME_CLAIM_BANNER_STATE.reset(token)


def render_username_claim_cta_html(state: UsernameClaimBannerState | None = None) -> str:
    current_state = state if state is not None else _CURRENT_USERNAME_CLAIM_BANNER_STATE.get()
    href = current_state.update_href if current_state is not None and current_state.update_href else ""
    return _join_html_blocks(
        render_username_claim_bar_html(href=href, data_attribute_html='data-username-claim-cta'),
        _html_block(
            """
            <script>
            (function () {
              var root = document.querySelector('[data-username-claim-cta]');
              if (!root) { return; }
              var link = root.querySelector('[data-username-claim-link]');
              if (!link) { return; }
              var htmlRoot = document.documentElement;
              var href = htmlRoot.getAttribute('data-username-claim-href') || '';
              link.setAttribute('href', href);
            }());
            </script>
            """
        ),
    )


def render_username_claim_cta_head_bootstrap(state: UsernameClaimBannerState | None = None) -> str:
    current_state = state if state is not None else _CURRENT_USERNAME_CLAIM_BANNER_STATE.get()
    visible = bool(current_state is not None and current_state.visible and current_state.update_href)
    update_href = current_state.update_href if visible else ""
    state_json = json.dumps({"visible": visible, "updateHref": update_href})
    return _html_block(
        f"""
        <script>
        (function () {{
          var serverState = {state_json};
          var storageName = {USERNAME_CLAIM_CTA_STORAGE_KEY!r};
          var htmlRoot = document.documentElement;
          var state = {{ visible: false, updateHref: '' }};
          try {{
            var raw = globalThis.localStorage ? globalThis.localStorage.getItem(storageName) : '';
            if (raw) {{
              var parsed = JSON.parse(raw);
              if (parsed && parsed.visible === true && typeof parsed.updateHref === 'string' && parsed.updateHref !== '') {{
                state = {{ visible: true, updateHref: parsed.updateHref }};
              }}
            }}
          }} catch (_error) {{}}
          if (!state.visible && serverState.visible === true && serverState.updateHref) {{
            state = serverState;
            try {{
              globalThis.localStorage && globalThis.localStorage.setItem(storageName, JSON.stringify(state));
            }} catch (_error) {{}}
          }}
          htmlRoot.setAttribute('data-username-claim-visible', state.visible ? '1' : '0');
          htmlRoot.setAttribute('data-username-claim-href', state.visible ? state.updateHref : '');
        }}());
        </script>
        """
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
    head_extras_html: str = "",
    active_section: str | None = None,
) -> str:
    base = load_template("base.html")
    if page_header_html is None:
        page_header_html = render_site_header(
            hero_kicker=hero_kicker,
            hero_title=hero_title,
            hero_text=hero_text,
            hero_action_html=hero_action_html,
            active_section=active_section,
        )
    if not page_footer_html:
        page_footer_html = render_site_footer()
    cta_enabled = username_claim_cta_enabled()
    if page_banner_html is None and cta_enabled:
        page_banner_html = render_username_claim_cta_html()
    elif page_banner_html is None:
        page_banner_html = ""
    cta_head_html = render_username_claim_cta_head_bootstrap() if cta_enabled else ""
    cta_script_html = render_username_claim_cta_script_tag() if cta_enabled else ""
    head_extras_html = _join_html_blocks(
        cta_head_html,
        head_extras_html,
    )
    page_script_html = _join_html_blocks(
        render_profile_nav_script_tag(),
        cta_script_html,
        render_copy_field_script_tag(),
        page_script_html,
    )
    return base.substitute(
        title=html.escape(title),
        head_extras_html=_indent_html_block(head_extras_html, 2),
        page_header_html=_indent_html_block(page_header_html, 4),
        page_banner_html=_indent_html_block(page_banner_html, 4),
        content_html=content_html,
        page_footer_html=_indent_html_block(page_footer_html, 4),
        page_script_html=_indent_html_block(page_script_html, 2),
        page_shell_class=html.escape(page_shell_class),
    )


def load_asset_text(name: str) -> str:
    asset_path = TEMPLATE_DIR / "assets" / name
    return asset_path.read_text(encoding="utf-8")


def load_asset_bytes(name: str) -> bytes:
    asset_path = TEMPLATE_DIR / "assets" / name
    return asset_path.read_bytes()


def render_profile_nav_script_tag() -> str:
    shell_content = load_page_shell_content()
    script_sources = shell_content["shared_script_sources"]
    if not isinstance(script_sources, list) or not script_sources:
        raise ValueError("shared_script_sources shell content must be a non-empty list")
    return f'<script type="module" src="{html.escape(str(script_sources[0]), quote=True)}"></script>'


def render_copy_field_script_tag() -> str:
    shell_content = load_page_shell_content()
    script_sources = shell_content["shared_script_sources"]
    if not isinstance(script_sources, list) or len(script_sources) < 2:
        raise ValueError("shared_script_sources shell content must include copy_field.js")
    return f'<script type="module" src="{html.escape(str(script_sources[1]), quote=True)}"></script>'


def render_username_claim_cta_script_tag() -> str:
    shell_content = load_page_shell_content()
    return (
        '<script type="module" src="'
        f'{html.escape(str(shell_content["username_claim_script_source"]), quote=True)}'
        '"></script>'
    )
