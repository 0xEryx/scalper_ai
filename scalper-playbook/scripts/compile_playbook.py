#!/usr/bin/env python3
import argparse
import json
import sys
import time

SUPPORTED_EVENTS = {"price_gte", "price_lte", "position_stopped"}
SUPPORTED_ACTIONS = {"move_stop", "close_partial", "close_all", "open_opposite_same_notional"}


def fail(message: str) -> int:
    json.dump({"ok": False, "error": message}, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile a scalper playbook JSON payload.")
    parser.add_argument("--input-file")
    args = parser.parse_args()

    if args.input_file:
        with open(args.input_file, "r", encoding="utf-8") as handle:
            raw = handle.read().strip()
    else:
        raw = sys.stdin.read().strip()
    if not raw:
        return fail("compile_playbook.py expected JSON on stdin")

    payload = json.loads(raw)
    inst_id = payload.get("instId")
    profile = payload.get("profile", "demo")
    rules = payload.get("rules")

    if not inst_id:
        return fail("instId is required")
    if not isinstance(rules, list) or not rules:
        return fail("at least one rule is required")

    for index, rule in enumerate(rules, start=1):
        event = (rule.get("if") or {}).get("event")
        action = (rule.get("then") or {}).get("action")
        if event not in SUPPORTED_EVENTS:
            return fail(f"rule {index} uses unsupported event: {event}")
        if action not in SUPPORTED_ACTIONS:
            return fail(f"rule {index} uses unsupported action: {action}")

    compiled = {
        "ok": True,
        "playbook_id": payload.get("playbook_id") or f"pb_{int(time.time())}",
        "profile": profile,
        "instId": inst_id,
        "position_ref": payload.get("position_ref", "current"),
        "entry": payload.get("entry"),
        "rules": rules,
    }
    json.dump(compiled, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
