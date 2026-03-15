from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from forum_cgi.wsgi_gateway import render_cgi_response
from forum_core.runtime_env import load_repo_env, notify_missing_env_defaults
from forum_read_only.web import application


load_repo_env()
notify_missing_env_defaults()


if __name__ == "__main__":
    sys.stdout.buffer.write(render_cgi_response(application))
