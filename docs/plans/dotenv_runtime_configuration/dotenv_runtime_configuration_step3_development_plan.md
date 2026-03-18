## Stage 1
- Goal: establish the shared repo env/catalog helpers and the authoritative `.env.example` surface.
- Dependencies: approved Step 2; current `FORUM_*` environment-variable usage; current repo-root `./forum` command surface.
- Expected changes: add the committed `.env.example` and `.env` ignore rule, introduce one shared env helper module that knows the repo env paths and can analyze missing defaults from `.env.example`, and define the minimal dependency surface for `.env` loading; planned helpers such as `repo_env_paths(repo_root: Path | None = None) -> tuple[Path, Path]`, `get_missing_env_defaults(env_path: Path, env_example_path: Path) -> dict[str, object]`, and `load_repo_env(*, override: bool = False) -> bool`.
- Verification approach: run focused temp-directory checks against sample `.env` and `.env.example` content, confirm documented assignment lines are detected as settings, confirm plain prose comments are ignored, and confirm the committed `.env.example` covers the currently supported `FORUM_*` variables.
- Risks or open questions:
  - deciding where to declare the minimal `python-dotenv` dependency in a repo that does not yet have an install manifest
  - keeping the first `.env.example` small enough that it documents only settings this project actually uses today
- Canonical components/API contracts touched: `.env.example`; `.gitignore`; shared env helper contract; current `FORUM_MODERATOR_FINGERPRINTS`, `FORUM_REPO_ROOT`, `FORUM_HOST`, and `FORUM_PORT` config catalog.

## Stage 2
- Goal: add explicit `.env` synchronization through `./forum`.
- Dependencies: Stage 1; existing `./forum` wrapper and `scripts/forum_tasks.py` parser/dispatch flow.
- Expected changes: extend the repo task runner with an `env-sync` subcommand, add a shared sync helper that creates `.env` when missing and appends only missing documented keys from `.env.example`, and define stable CLI result messages and exit behavior; planned helpers such as `sync_env_defaults(env_path: Path, env_example_path: Path) -> dict[str, int | bool]` and `run_env_sync() -> int`.
- Verification approach: run `./forum env-sync` against a temp repo state with and without an existing `.env`, confirm missing keys are appended once, confirm existing values are preserved, and confirm repeated runs are idempotent.
- Risks or open questions:
  - deciding whether the sync output should include a marker comment before appended keys or stay completely minimal
  - keeping the command behavior straightforward enough that a later non-Python task runner can mirror it exactly
- Canonical components/API contracts touched: `./forum` subcommand contract; `scripts/forum_tasks.py`; `.env` mutation rules; append-only sync result surface.

## Stage 3
- Goal: integrate `.env` loading and missing-key notices across the current runtime entrypoints without mutating `.env` on launch.
- Dependencies: Stage 1; Stage 2 for the canonical `./forum env-sync` command hint.
- Expected changes: call the shared loader and missing-key notice helpers early enough in the read-only server path, the WSGI import path, the CGI write entrypoint path, and the `./forum` runner so `.env` values are available before `FORUM_*` reads occur; keep explicit process environment values authoritative by using non-overriding load behavior; planned helpers such as `notify_missing_env_defaults(*, command_hint: str = "./forum env-sync") -> None` and `load_repo_env(*, override: bool = False) -> bool`.
- Verification approach: start the app through `./forum start`, direct `scripts/run_read_only.py`, and CGI-style entrypoints with settings present only in `.env`; confirm host/port, repo-root selection, and moderator allowlist behavior reflect `.env`; confirm missing-key notices point to `./forum env-sync` and do not edit `.env`.
- Risks or open questions:
  - avoiding duplicate missing-key notices when one startup path imports another module that also initializes env support
  - choosing the narrowest integration points that still cover direct WSGI and CGI usage rather than only the convenience wrappers
- Canonical components/API contracts touched: `./forum`; `scripts/run_read_only.py`; `forum_read_only.web`; `forum_cgi.entrypoint`; shared `.env` loading and notice contract.

## Stage 4
- Goal: lock the new env workflow into the repo’s tests and operator docs.
- Dependencies: Stages 1-3.
- Expected changes: add focused unittest coverage for env parsing/sync and the new CLI subcommand behavior, update `docs/developer_commands.md` to document `./forum env-sync`, restart expectations, and direct-entrypoint parity, and align the `.env.example` header comments with the documented workflow.
- Verification approach: run targeted unittest discovery patterns for the env helper and CLI runner, run `./forum help` and `./forum env-sync` manually, and confirm the docs/examples match the actual command contract.
- Risks or open questions:
  - choosing stable test seams around the repo-root constants in `scripts/forum_tasks.py` and related startup files
  - keeping the documentation surface small in a repo that still relies mostly on direct scripts and planning artifacts
- Canonical components/API contracts touched: unittest-based `tests/` workflow; `docs/developer_commands.md`; `./forum` help/examples; `.env.example` operator guidance.
