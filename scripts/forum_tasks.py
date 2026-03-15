#!/usr/bin/env python3
"""Reference task runner for common repo commands."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class TaskRequest:
    command: str
    test_pattern: str | None = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="forum",
        description="Forum task runner.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("help", help="Show help output.")
    subparsers.add_parser("start", help="Start the local read-only forum server.")

    test_parser = subparsers.add_parser("test", help="Run the unittest suite.")
    test_parser.add_argument(
        "pattern",
        nargs="?",
        help="Optional unittest discovery pattern (example: test_profile_update_page.py).",
    )

    return parser


def parse_task_args(argv: list[str] | None = None) -> tuple[argparse.ArgumentParser, TaskRequest | None]:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command in (None, "help"):
        return parser, None
    if args.command == "start":
        return parser, TaskRequest(command="start")
    if args.command == "test":
        return parser, TaskRequest(command="test", test_pattern=args.pattern)
    raise AssertionError(f"Unhandled command: {args.command}")


def run_task(request: TaskRequest) -> int:
    if request.command == "start":
        print("start is not implemented yet.", file=sys.stderr)
        return 1
    if request.command == "test":
        print("test is not implemented yet.", file=sys.stderr)
        return 1
    print(f"Unknown command: {request.command}", file=sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    parser, request = parse_task_args(argv)
    if request is None:
        parser.print_help()
        return 0
    return run_task(request)


if __name__ == "__main__":
    raise SystemExit(main())
