#!/usr/bin/env python3
"""Install the Codex harness into a new or existing project without overwrites.

Usage: py -3 init.py new D:\\Projects\\my-app --name "My App"
       py -3 init.py install D:\\Projects\\existing-app --name "Existing App"
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "template"
SKIP = {"__pycache__", ".DS_Store"}


def is_link(p: Path) -> bool:
    return p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())


def verify_destination(raw: str) -> Path:
    p = Path(raw).expanduser().absolute()
    for part in [p, *p.parents]:
        if part.exists() and is_link(part):
            raise ValueError(f"Refusing path through symlink/junction: {part}")
    resolved = p.resolve(strict=False)
    source = HERE.resolve()
    if resolved == source or source in resolved.parents or resolved in source.parents:
        raise ValueError("Destination must be separate from harness-devkit source")
    if resolved == Path(resolved.anchor):
        raise ValueError("Cannot install in filesystem root")
    return resolved


def collect_files() -> dict[str, bytes]:
    files = {}
    for item in TEMPLATE.rglob("*"):
        if is_link(item):
            raise ValueError(f"Refusing template symlink/junction: {item}")
        if not item.is_file() or any(x in SKIP for x in item.parts):
            continue
        files[item.relative_to(TEMPLATE).as_posix()] = item.read_bytes()
    if not files:
        raise ValueError("Template files missing")
    return files


def setup(dest: Path, name: str, mode: str, init_git: bool) -> None:
    files = collect_files()
    if mode == "new" and dest.exists() and any(dest.iterdir()):
        raise ValueError("New destination is not empty. Use install for existing project (no overwrites).")
    if mode == "install" and not dest.is_dir():
        raise ValueError("Existing project directory not found")
    state = {
        "schema": 1, "name": name, "goal": "", "tasks": [], "decisions": [],
    }
    generated = {
        "tracking/state.json": (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode(),
        "tracking/events.jsonl": b"",
        "tracking/handoff.json": (json.dumps({"schema": 1, "task": "", "done": "Harness installed", "next_action": "Define project goal and approved backlog", "files": [], "tests": "Not yet run"}, indent=2) + "\n").encode(),
        "docs/SESSION_HANDOFF.md": f"# Session handoff — {name}\n\n- Current task: none\n- Next: Define goal, milestones and approved backlog.\n- Source of truth: tracking/state.json and tracking/handoff.json\n",
        "docs/PROJECT_STATUS.md": f"# {name} — Project status\n\nNo tasks yet.\n",
    }
    generated = {k: (v.encode("utf-8") if isinstance(v, str) else v) for k, v in generated.items()}
    files.update(generated)
    # Preflight ALL conflicts before creating anything. Never overwrite or delete existing files.
    collisions = [p for p in sorted(files) if (dest / p).exists() or is_link(dest / p)]
    if collisions:
        raise ValueError("Refusing to overwrite existing paths:\n  " + "\n  ".join(collisions))
    for rel in files:
        path = dest / rel
        for parent in path.parents:
            if parent == dest.parent:
                break
            if parent.exists() and is_link(parent):
                raise ValueError(f"Refusing path through symlink/junction: {parent}")
    dest.mkdir(parents=True, exist_ok=True)
    for rel, data in sorted(files.items()):
        path = dest / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as fh:
            fh.write(data)
    if init_git and not (dest / ".git").exists():
        try:
            subprocess.run(["git", "init", "-b", "main"], cwd=dest, check=True, capture_output=True, text=True)
            print("Initialized local Git repository (no commit/push performed).")
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            print(f"Git init skipped: {exc}", file=sys.stderr)
    print(f"Harness installed in {dest} ({len(files)} files)")
    print(f"Next: open this folder in Codex Desktop; run py -3 tools/project_control.py dashboard")
    print("Then read START-CODEX.md and start the Orchestrator thread.")


def main() -> int:
    p = argparse.ArgumentParser(description="Initialize reusable Codex AI team in a project")
    sub = p.add_subparsers(dest="command", required=True)
    for command in ("new", "install"):
        sp = sub.add_parser(command)
        sp.add_argument("project_path")
        sp.add_argument("--name", default=None)
        sp.add_argument("--no-git", action="store_true", help="Do not run git init")
    a = p.parse_args()
    try:
        dest = verify_destination(a.project_path)
        setup(dest, a.name or dest.name, a.command, not a.no_git)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
