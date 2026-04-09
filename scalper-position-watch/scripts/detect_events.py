#!/usr/bin/env python3
import json
import sys


def matches(rule_if: dict, snapshot: dict) -> bool:
    event = rule_if.get("event")
    params = rule_if.get("params") or {}
    last_price = snapshot.get("last_price")
    position_stopped = snapshot.get("position_stopped", False)

    if event == "price_lte":
        return last_price is not None and last_price <= params.get("price")
    if event == "price_gte":
        return last_price is not None and last_price >= params.get("price")
    if event == "position_stopped":
        return bool(position_stopped)
    return False


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        raise SystemExit("detect_events.py expected JSON on stdin")
    payload = json.loads(raw)
    playbook = payload["playbook"]
    snapshot = payload["snapshot"]

    matched = []
    for idx, rule in enumerate(playbook.get("rules", []), start=1):
        if matches(rule.get("if") or {}, snapshot):
            matched.append(
                {
                    "rule_index": idx,
                    "event": (rule.get("if") or {}).get("event"),
                    "action": rule.get("then"),
                }
            )

    json.dump(
        {
            "ok": True,
            "playbook_id": playbook.get("playbook_id"),
            "matched_rules": matched,
        },
        sys.stdout,
        ensure_ascii=True,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
