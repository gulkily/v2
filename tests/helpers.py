from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from typing import Any
from unittest import mock

from forum_web.web import application


class ForumRepoTestCase(unittest.TestCase):
    repo_tempdir: tempfile.TemporaryDirectory[str]
    repo_root: Path

    def setUp(self) -> None:
        super().setUp()
        sanitized_env = {key: value for key, value in os.environ.items() if not key.startswith("FORUM_")}
        self._env_patcher = mock.patch.dict(os.environ, sanitized_env, clear=True)
        self._env_patcher.start()
        self.repo_tempdir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.repo_tempdir.name)

    def tearDown(self) -> None:
        self.repo_tempdir.cleanup()
        self._env_patcher.stop()
        super().tearDown()

    def write_record(self, relative_path: str, raw_text: str) -> None:
        path = self.repo_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(dedent(raw_text).lstrip(), encoding="ascii")

    def run_command(
        self,
        command: list[str],
        *,
        cwd: Path | None = None,
        input_text: str | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=cwd,
            input=input_text,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            env=env,
        )

    def run_git(self, *args: str, env: dict[str, str] | None = None) -> str:
        result = self.run_command(
            ["git", "-C", str(self.repo_root), *args],
            env=env,
        )
        return result.stdout.strip()

    def init_git_repo(self, *, user_name: str = "Test User", user_email: str = "test@example.com") -> None:
        self.run_git("init")
        self.run_git("config", "user.name", user_name)
        self.run_git("config", "user.email", user_email)

    def request(
        self,
        path: str,
        *,
        query_string: str = "",
        method: str = "GET",
        body: bytes = b"",
        extra_env: dict[str, str] | None = None,
        extra_environ: dict[str, Any] | None = None,
        decode: bool = True,
    ) -> tuple[str, dict[str, str], str | bytes]:
        environ: dict[str, Any] = {
            "PATH_INFO": path,
            "QUERY_STRING": query_string,
            "REQUEST_METHOD": method,
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": BytesIO(body),
        }
        if extra_environ:
            environ.update(extra_environ)

        response: dict[str, object] = {}

        def start_response(status: str, headers: list[tuple[str, str]]) -> None:
            response["status"] = status
            response["headers"] = headers

        env = {"FORUM_REPO_ROOT": str(self.repo_root)}
        if extra_env:
            env.update(extra_env)

        with mock.patch.dict(os.environ, env, clear=False):
            response_body = b"".join(application(environ, start_response))

        body_value: str | bytes
        if decode:
            body_value = response_body.decode("utf-8")
        else:
            body_value = response_body

        return response["status"], dict(response["headers"]), body_value
