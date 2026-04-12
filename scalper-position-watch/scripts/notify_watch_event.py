#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WATCH_SKILL_DIR = SCRIPT_DIR.parent
WORKSPACE_ROOT = WATCH_SKILL_DIR.parent.parent


def resolve_openclaw_command() -> list[str]:
    env_entry = os.environ.get("OPENCLAW_ENTRY")
    if env_entry:
        return ["node", env_entry]

    cli = shutil.which("openclaw")
    if cli:
        return [cli]

    candidate_roots = [
        Path.cwd(),
        *Path.cwd().parents,
        WORKSPACE_ROOT,
        Path.home() / "Desktop",
    ]
    seen: set[Path] = set()
    for root in candidate_roots:
        if root in seen or not root.exists():
            continue
        seen.add(root)
        direct = root / "openclaw.mjs"
        if direct.exists():
            return ["node", str(direct)]
        if root.name == "Desktop":
            for found in root.glob("*/openclaw.mjs"):
                return ["node", str(found)]

    raise SystemExit(
        "Could not resolve OpenClaw entrypoint. Set OPENCLAW_ENTRY or install the openclaw CLI in PATH."
    )


def build_message(event: dict) -> str:
    actions = event.get("actions") or []
    snapshot = event.get("snapshot") or {}
    lines = [
        "scalper watcher triggered",
        f"playbook_id={event.get('playbook_id')}",
        f"profile={event.get('profile')}",
        f"instId={event.get('instId')}",
        f"action_count={event.get('action_count')}",
        f"last_price={snapshot.get('last_price')}",
        f"summary={event.get('summary')}",
        "Please send one concise user-facing update for this execution result.",
    ]
    for index, action in enumerate(actions, start=1):
        lines.extend(
            [
                f"action_{index}={action.get('name')}",
                f"action_{index}_status={action.get('status')}",
                f"action_{index}_rule_id={action.get('rule_id')}",
            ]
        )
    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("notify_watch_event.py expects one JSON argument")
    event = json.loads(sys.argv[1])
    message = build_message(event)
    openclaw_cmd = resolve_openclaw_command()
    completed = subprocess.run(
        openclaw_cmd + ["system", "event", "--text", message, "--mode", "now"],
        capture_output=True,
        text=True,
    )
    result = {
        "ok": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }
    json.dump(result, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0 if completed.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
