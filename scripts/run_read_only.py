from __future__ import annotations

import os
import sys
from pathlib import Path
from wsgiref.simple_server import make_server

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from forum_core.runtime_env import load_repo_env

load_repo_env(repo_root=REPO_ROOT)

from forum_read_only.web import application


def main() -> None:
    host = os.environ.get("FORUM_HOST", "127.0.0.1")
    port = int(os.environ.get("FORUM_PORT", "8000"))
    with make_server(host, port, application) as server:
        print(f"Serving read-only forum on http://{host}:{port}")
        server.serve_forever()


if __name__ == "__main__":
    main()
