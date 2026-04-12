#!/usr/bin/env python3
import json
import sys
from pathlib import Path


def matches(
    rule_if: dict,
    snapshot: dict,
    state: dict | None = None,
    watcher_started_at: int | float | None = None,
) -> tuple[bool, dict | None]:
    event = rule_if.get("event")
    params = rule_if.get("params") or {}
    last_price = snapshot.get("last_price")
    position_stopped = snapshot.get("position_stopped", False)
    entry_filled = snapshot.get("entry_filled", False)
    tp_hit = snapshot.get("tp_hit", False)
    sl_hit = snapshot.get("sl_hit", False)
    elapsed_seconds = snapshot.get("elapsed_seconds")
    state = state or {}

    if event == "price_lte":
        return (last_price is not None and last_price <= params.get("price"), None)
    if event == "price_gte":
        return (last_price is not None and last_price >= params.get("price"), None)
    if event == "position_stopped":
        return (bool(position_stopped), None)
    if event == "entry_filled":
        return (bool(entry_filled), None)
    if event == "tp_hit":
        return (bool(tp_hit), None)
    if event == "sl_hit":
        return (bool(sl_hit), None)
    if event == "time_elapsed":
        target_seconds = params.get("seconds")
        base_elapsed = elapsed_seconds
        if base_elapsed is None and watcher_started_at is not None:
            current_ts = snapshot.get("ts") or watcher_started_at
            base_elapsed = max(0, int(current_ts - watcher_started_at))
        return (base_elapsed is not None and base_elapsed >= target_seconds, None)
    if event == "sequence":
        steps = params.get("steps") or []
        progress = int(state.get("progress", 0))
        next_state = {
            "progress": progress,
            "status": state.get("status", "waiting"),
            "armed_at": state.get("armed_at"),
        }
        if progress >= len(steps):
            return (False, next_state)
        current_step = steps[progress]
        matched, _ = matches(current_step, snapshot, None, watcher_started_at)
        if matched:
            next_state["progress"] = progress + 1
            next_state["status"] = "armed" if next_state["progress"] < len(steps) else "triggered"
            next_state["last_step_index"] = progress + 1
            if next_state["status"] == "armed" and next_state["armed_at"] is None:
                next_state["armed_at"] = snapshot.get("ts")
            return (next_state["progress"] >= len(steps), next_state)
        return (False, next_state)
    return (False, None)


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        raise SystemExit("detect_events.py expected JSON on stdin")
    payload = json.loads(raw)
    playbook = payload["playbook"]
    snapshot = payload["snapshot"]
    playbook_state = payload.get("state") or {}
    state_path = payload.get("state_path")
    watcher_started_at = payload.get("watch_started_at")

    matched = []
    next_state = {}
    meta_state = playbook_state.get("_meta") if isinstance(playbook_state, dict) else None
    if isinstance(meta_state, dict):
        next_state["_meta"] = meta_state
    for idx, rule in enumerate(playbook.get("rules", []), start=1):
        rule_state = playbook_state.get(str(idx)) or {}
        if not rule.get("enabled", True):
            next_state[str(idx)] = {**rule_state, "status": "disabled"}
            continue
        did_match, updated_state = matches(rule.get("if") or {}, snapshot, rule_state, watcher_started_at)
        final_state = updated_state or rule_state
        if did_match and rule.get("once", True):
            final_state = {**final_state, "status": "done"}
        next_state[str(idx)] = final_state
        if did_match:
            matched.append(
                {
                    "rule_index": idx,
                    "rule_id": rule.get("id") or f"rule_{idx}",
                    "event": (rule.get("if") or {}).get("event"),
                    "action": rule.get("then"),
                }
            )

    if state_path:
        target = Path(state_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(next_state, ensure_ascii=True, indent=2), encoding="utf-8")

    json.dump(
        {
            "ok": True,
            "playbook_id": playbook.get("playbook_id"),
            "matched_rules": matched,
            "state": next_state,
            "state_path": state_path,
            "status": "rule_triggered" if matched else "watching",
            "summary": (
                f"{len(matched)} rule(s) triggered for {playbook.get('playbook_id')}"
                if matched
                else f"No rules triggered for {playbook.get('playbook_id')}"
            ),
        },
        sys.stdout,
        ensure_ascii=True,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
