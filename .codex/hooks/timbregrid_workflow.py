#!/usr/bin/env python3
"""Advisory Codex hook for TimbreGrid roadmap hygiene."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROADMAP_CONTEXT = (
    "TimbreGrid workflow: use README.md as the roadmap source of truth; "
    "check Current MVP Scope, Development Roadmap, First Milestone, and Next Milestones "
    "before planning milestone work; update README only after implementation and validation justify it."
)


def _git_root(cwd: str) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return Path(result.stdout.strip())
    return Path(cwd)


def _changed_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _is_roadmap_relevant(path: str) -> bool:
    prefixes = (
        "src/",
        "tests/",
        "manifests/",
        "schemas/",
        "benchmarks/",
        "registry/",
        "Dockerfile",
        "docker-compose.yml",
    )
    return path.startswith(prefixes)


def _session_start() -> None:
    print(
        json.dumps(
            {
                "continue": True,
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": ROADMAP_CONTEXT,
                },
            }
        )
    )


def _stop(payload: dict[str, object]) -> None:
    if payload.get("stop_hook_active"):
        print(json.dumps({"continue": True}))
        return

    root = _git_root(str(payload.get("cwd") or "."))
    changed = _changed_files(root)
    changed_roadmap_relevant = any(_is_roadmap_relevant(path) for path in changed)
    readme_changed = "README.md" in changed

    output: dict[str, object] = {"continue": True}
    if changed_roadmap_relevant and not readme_changed:
        output["systemMessage"] = (
            "TimbreGrid roadmap reminder: implementation files changed but README.md did not. "
            "If this completed or changed a roadmap item, update README.md before finalizing."
        )
    print(json.dumps(output))


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        payload = {}

    event_name = str(payload.get("hook_event_name") or "")
    if event_name == "SessionStart":
        _session_start()
    elif event_name == "Stop":
        _stop(payload)
    else:
        print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
