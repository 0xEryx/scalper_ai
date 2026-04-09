#!/usr/bin/env python3
import argparse
import json
import pathlib
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Load a playbook and a snapshot for MVP watch evaluation.")
    parser.add_argument("--playbook-id", required=True)
    parser.add_argument("--snapshot-json", required=True)
    args = parser.parse_args()

    playbook_path = pathlib.Path(".scalper-runtime/playbooks") / f"{args.playbook_id}.json"
    if not playbook_path.exists():
        raise SystemExit(f"missing playbook: {playbook_path}")

    playbook = json.loads(playbook_path.read_text(encoding="utf-8"))
    snapshot = json.loads(args.snapshot_json)
    json.dump({"playbook": playbook, "snapshot": snapshot}, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
