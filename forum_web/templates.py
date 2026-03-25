from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
import html
import json
import os
from pathlib import Path
from string import Template
from textwrap import dedent, indent


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
USERNAME_CLAIM_CTA_STORAGE_KEY = "forum_username_claim_cta"
_CURRENT_USERNAME_CLAIM_BANNER_STATE: ContextVar["UsernameClaimBannerState | None"] = ContextVar(
    "current_username_claim_banner_state",
    default=None,
)


@dataclass(frozen=True)
class UsernameClaimBannerState:
    visible: bool
    update_href: str = ""


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


def _html_block(raw_text: str) -> str:
    return dedent(raw_text).strip()


def _join_html_blocks(*blocks: str) -> str:
    return "\n".join(block.strip() for block in blocks if block and block.strip())


def _indent_html_block(block: str, spaces: int) -> str:
    return indent(block.strip(), " " * spaces)


def render_primary_nav(*, aria_label: str = "Primary") -> str:
    links = [
        ("/", "Home"),
        ("/compose/thread", "Post"),
        ("/instance/", "Project info"),
        ("/activity/", "Activity"),
    ]
    items = "\n".join(
        f'<a href="{html.escape(path)}">{html.escape(label)}</a>'
        for path, label in links
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
) -> str:
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
                  <p class="site-header-tagline">calm threads from canonical text records</p>
                </div>
              </div>
              {_indent_html_block(render_primary_nav(), 2)}
            </div>
            """
        ),
        intro_html,
        "</header>",
    )


def render_site_footer() -> str:
    return _html_block(
        """
        <footer class="site-footer">
          <div class="site-footer-inner">
            <p>Best read with a clear mind and a modest browser window.</p>
            <p>[ slow web ]</p>
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
        _html_block(
            f"""
            <section class="site-username-claim panel" data-username-claim-cta>
              <div class="site-username-claim-copy">
                <p class="site-username-claim-kicker">Account setup</p>
                <p class="site-username-claim-text">Now that you're participating, you can choose a username.</p>
              </div>
              <a class="thread-chip site-username-claim-link" data-username-claim-link href="{html.escape(href, quote=True)}">Choose your username</a>
            </section>
            """
        ),
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
    head_extras_html = _join_html_blocks(
        render_username_claim_cta_head_bootstrap(),
        head_extras_html,
    )
    page_script_html = _join_html_blocks(
        render_profile_nav_script_tag(),
        render_username_claim_cta_script_tag(),
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
    return '<script type="module" src="/assets/profile_nav.js"></script>'


def render_copy_field_script_tag() -> str:
    return '<script type="module" src="/assets/copy_field.js"></script>'


def render_username_claim_cta_script_tag() -> str:
    return '<script type="module" src="/assets/username_claim_cta.js"></script>'
