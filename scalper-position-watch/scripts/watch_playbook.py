#!/usr/bin/env python3
import argparse
import json
import pathlib
import sys
import time

SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
WATCH_SKILL_DIR = SCRIPT_DIR.parent
WORKSPACE_ROOT = WATCH_SKILL_DIR.parent.parent
RUNTIME_ROOT = WORKSPACE_ROOT / ".scalper-runtime"


def main() -> int:
    parser = argparse.ArgumentParser(description="Load a playbook and a snapshot for MVP watch evaluation.")
    parser.add_argument("--playbook-id", required=True)
    parser.add_argument("--snapshot-json", required=True)
    args = parser.parse_args()

    playbook_path = RUNTIME_ROOT / "playbooks" / f"{args.playbook_id}.json"
    if not playbook_path.exists():
        raise SystemExit(f"missing playbook: {playbook_path}")

    runtime_dir = RUNTIME_ROOT
    playbook = json.loads(playbook_path.read_text(encoding="utf-8"))
    snapshot = json.loads(args.snapshot_json)
    state_dir = runtime_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{args.playbook_id}.json"
    state = {}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    state_meta = state.get("_meta") if isinstance(state, dict) else None
    if not isinstance(state_meta, dict):
        state_meta = {"watch_started_at": int(time.time())}
    state["_meta"] = state_meta
    json.dump(
        {
            "ok": True,
            "playbook": playbook,
            "snapshot": snapshot,
            "state": state,
            "state_path": str(state_path),
            "watch_started_at": state_meta["watch_started_at"],
            "status": "watching",
            "summary": f"Loaded playbook {args.playbook_id} for watcher evaluation.",
        },
        sys.stdout,
        ensure_ascii=True,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
