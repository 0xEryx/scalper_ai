#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WATCH_SKILL_DIR = SCRIPT_DIR.parent
WORKSPACE_ROOT = WATCH_SKILL_DIR.parent.parent
WATCH_PLAYBOOK_SCRIPT = SCRIPT_DIR / "watch_playbook.py"
DETECT_EVENTS_SCRIPT = SCRIPT_DIR / "detect_events.py"
DISPATCH_ACTION_SCRIPT = WORKSPACE_ROOT / "skills" / "scalper-executor" / "scripts" / "dispatch_action.py"
RUNTIME_ROOT = WORKSPACE_ROOT / ".scalper-runtime"


def run_json(cmd: list[str]) -> dict | list:
    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "command failed")
    text = completed.stdout.strip()
    return json.loads(text) if text else {}


def emit(result: dict) -> None:
    json.dump(result, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")


def append_jsonl(path: str, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def resolve_snapshot(profile: str, inst_id: str) -> dict:
    ticker_rows = run_json(["okx", "--profile", profile, "market", "ticker", inst_id, "--json"])
    if not isinstance(ticker_rows, list) or not ticker_rows:
        raise RuntimeError("empty ticker response")
    row = ticker_rows[0]
    ts_raw = row.get("ts")
    ts = int(int(ts_raw) / 1000) if ts_raw else None
    return {
        "last_price": float(row["last"]),
        "ts": ts,
        "instId": inst_id,
        "profile": profile,
        "ticker": row,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one deterministic scalper watch cycle without an LLM wrapper.")
    parser.add_argument("--playbook-id", required=True)
    parser.add_argument("--profile")
    parser.add_argument("--inst-id")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--snapshot-file")
    args = parser.parse_args()

    playbook_path = RUNTIME_ROOT / "playbooks" / f"{args.playbook_id}.json"
    if not playbook_path.exists():
        raise SystemExit(f"missing playbook: {playbook_path}")
    playbook = json.loads(playbook_path.read_text(encoding="utf-8"))
    profile = args.profile or playbook.get("profile")
    inst_id = args.inst_id or playbook.get("instId")
    if not profile or not inst_id:
        raise SystemExit("profile and instId must be resolvable from args or playbook")

    if args.snapshot_file:
        snapshot = json.loads(Path(args.snapshot_file).read_text(encoding="utf-8"))
    else:
        snapshot = resolve_snapshot(profile, inst_id)

    watch_payload = run_json(
        [
            "python3",
            str(WATCH_PLAYBOOK_SCRIPT),
            "--playbook-id",
            args.playbook_id,
            "--snapshot-json",
            json.dumps(snapshot, ensure_ascii=True),
        ]
    )

    detect_completed = subprocess.run(
        ["python3", str(DETECT_EVENTS_SCRIPT)],
        input=json.dumps(watch_payload, ensure_ascii=True),
        capture_output=True,
        text=True,
    )
    if detect_completed.returncode != 0:
        raise RuntimeError(detect_completed.stderr.strip() or "detect_events failed")
    detect_payload = json.loads(detect_completed.stdout.strip() or "{}")

    actions = []
    for matched in detect_payload.get("matched_rules", []):
        then = matched.get("action") or {}
        action_name = then.get("action")
        params = then.get("params") or {}
        dispatch_input = {
            "action": action_name,
            "params": params,
            "profile": profile,
            "instId": inst_id,
            "entry": playbook.get("entry") or {},
            "execute": args.execute,
        }
        dispatch_completed = subprocess.run(
            ["python3", str(DISPATCH_ACTION_SCRIPT)],
            input=json.dumps(dispatch_input, ensure_ascii=True),
            capture_output=True,
            text=True,
        )
        action_result = json.loads(dispatch_completed.stdout.strip() or "{}")
        action_result["rule_id"] = matched.get("rule_id")
        actions.append(action_result)

    cycle_result = {
        "ok": True,
        "playbook_id": args.playbook_id,
        "profile": profile,
        "instId": inst_id,
        "snapshot": snapshot,
        "watch": detect_payload,
        "actions": actions,
        "status": "action_executed" if actions else detect_payload.get("status", "watching"),
        "summary": (
            f"Executed {len(actions)} action(s) for {args.playbook_id}" if actions else detect_payload.get("summary")
        ),
    }
    append_jsonl(str(RUNTIME_ROOT / "logs" / "watch-cycles.jsonl"), cycle_result)
    emit(cycle_result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
