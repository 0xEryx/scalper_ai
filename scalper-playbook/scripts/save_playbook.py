#!/usr/bin/env python3
import argparse
import json
import pathlib
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Save a compiled scalper playbook JSON payload.")
    parser.add_argument("--input-file")
    args = parser.parse_args()

    if args.input_file:
        raw = pathlib.Path(args.input_file).read_text(encoding="utf-8").strip()
    else:
        raw = sys.stdin.read().strip()
    if not raw:
        raise SystemExit("save_playbook.py expected JSON on stdin")

    payload = json.loads(raw)
    if not payload.get("playbook_id"):
        raise SystemExit("playbook_id is required")

    root = pathlib.Path(".scalper-runtime/playbooks")
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"{payload['playbook_id']}.json"
    target.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")

    json.dump({"ok": True, "path": str(target), "playbook_id": payload["playbook_id"]}, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
