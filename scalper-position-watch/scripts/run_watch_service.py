#!/usr/bin/env python3
import argparse
import json
import shlex
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WATCH_SKILL_DIR = SCRIPT_DIR.parent
WORKSPACE_ROOT = WATCH_SKILL_DIR.parent.parent
RUN_WATCH_CYCLE_SCRIPT = SCRIPT_DIR / "run_watch_cycle.py"
RUNTIME_ROOT = WORKSPACE_ROOT / ".scalper-runtime"


def append_jsonl(path: str, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def load_json(path: str) -> dict | list:
    target = Path(path)
    if not target.exists():
        return {}
    text = target.read_text(encoding="utf-8").strip()
    return json.loads(text) if text else {}


def run_cycle(playbook_id: str, execute: bool, snapshot_file: str | None = None) -> dict:
    cmd = ["python3", str(RUN_WATCH_CYCLE_SCRIPT), "--playbook-id", playbook_id]
    if execute:
        cmd.append("--execute")
    if snapshot_file:
        cmd.extend(["--snapshot-file", snapshot_file])
    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "run_watch_cycle failed")
    return json.loads(completed.stdout.strip() or "{}")


def to_event(result: dict) -> dict | None:
    actions = result.get("actions") or []
    if not actions:
        return None
    event = {
        "kind": "scalper.watch.triggered",
        "playbook_id": result.get("playbook_id"),
        "profile": result.get("profile"),
        "instId": result.get("instId"),
        "status": result.get("status"),
        "summary": result.get("summary"),
        "action_count": len(actions),
        "actions": [
            {
                "name": action.get("action"),
                "status": action.get("status"),
                "ok": action.get("ok"),
                "rule_id": action.get("rule_id"),
                "shell": action.get("shell"),
                "stdout": action.get("stdout"),
                "stderr": action.get("stderr"),
            }
            for action in actions
        ],
        "snapshot": result.get("snapshot"),
        "watch": {
            "matched_rules": (result.get("watch") or {}).get("matched_rules"),
            "state": (result.get("watch") or {}).get("state"),
        },
        "ts": int(time.time()),
    }
    return event


def maybe_notify(event: dict, notify_command: str | None) -> dict | None:
    if not notify_command:
        return None
    payload = json.dumps(event, ensure_ascii=True)
    base_cmd = shlex.split(notify_command)
    completed = subprocess.run(base_cmd + [payload], capture_output=True, text=True)
    return {
        "ok": completed.returncode == 0,
        "command": notify_command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Background-friendly watcher service entrypoint.")
    parser.add_argument("--playbook-id", required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--emit-file", default=str(RUNTIME_ROOT / "events" / "watch-events.jsonl"))
    parser.add_argument("--notify-command")
    parser.add_argument("--snapshot-file")
    args = parser.parse_args()

    result = run_cycle(args.playbook_id, args.execute, args.snapshot_file)
    event = to_event(result)

    service_result = {
        "ok": True,
        "playbook_id": args.playbook_id,
        "cycle": result,
        "event_emitted": bool(event),
        "event": event,
        "notify": None,
        "ts": int(time.time()),
    }
    if event:
        append_jsonl(args.emit_file, event)
        service_result["notify"] = maybe_notify(event, args.notify_command)
    json.dump(service_result, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
