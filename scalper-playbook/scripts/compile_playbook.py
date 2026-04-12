#!/usr/bin/env python3
import argparse
import json
import re
import sys
import time

SUPPORTED_EVENTS = {
    "price_gte",
    "price_lte",
    "position_stopped",
    "entry_filled",
    "tp_hit",
    "sl_hit",
    "time_elapsed",
    "sequence",
}
SUPPORTED_ACTIONS = {
    "move_stop",
    "close_partial",
    "close_all",
    "open_opposite_same_notional",
    "add_same_side_position",
    "move_stop_to_break_even",
    "notify_only",
}


def fail(message: str) -> int:
    json.dump({"ok": False, "error": message}, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 1


def parse_number(token):
    if token is None:
        return None
    value = float(token)
    return int(value) if value.is_integer() else value


def parse_natural_language(payload: dict) -> dict | None:
    text = payload.get("request_text") or payload.get("text") or payload.get("instruction")
    if not isinstance(text, str) or not text.strip():
        return None

    lowered = text.replace("％", "%")
    seq_match = re.search(
        r"(?:到达|跌到|到)\s*([0-9]+(?:\.[0-9]+)?)"
        r".{0,20}?(?:反弹到|反弹至|回到|再次反弹到)\s*([0-9]+(?:\.[0-9]+)?)"
        r".{0,20}?(?:再)?加仓\s*([0-9]+(?:\.[0-9]+)?)\s*%",
        lowered,
    )
    if not seq_match:
        return None

    first_price, second_price, pct = seq_match.groups()
    leverage_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*[x×倍]", lowered, re.IGNORECASE)
    side = "sell" if any(word in lowered.lower() for word in ["空单", "做空", "加空", "short"]) else "buy"

    payload = {
        **payload,
        "rules": [
            {
                "if": {
                    "event": "sequence",
                    "params": {
                        "steps": [
                            {"event": "price_lte", "params": {"price": parse_number(first_price)}},
                            {"event": "price_gte", "params": {"price": parse_number(second_price)}},
                        ]
                    },
                },
                "then": {
                    "action": "add_same_side_position",
                    "params": {
                        "margin_pct": parse_number(pct),
                        **(
                            {"leverage": parse_number(leverage_match.group(1))}
                            if leverage_match
                            else {}
                        ),
                        "reference_side": side,
                    },
                },
            }
        ],
    }
    if not payload.get("entry"):
        payload["entry"] = {"side": side}
    return payload


def validate_event(event_if: dict, rule_index: int) -> str | None:
    event = event_if.get("event")
    params = event_if.get("params") or {}
    if event not in SUPPORTED_EVENTS:
        return f"rule {rule_index} uses unsupported event: {event}"
    if event == "sequence":
        steps = params.get("steps")
        if not isinstance(steps, list) or len(steps) < 2:
            return f"rule {rule_index} sequence requires at least two steps"
        for step_index, step in enumerate(steps, start=1):
            step_event = step.get("event")
            if step_event not in {"price_gte", "price_lte"}:
                return f"rule {rule_index} sequence step {step_index} uses unsupported event: {step_event}"
    if event == "time_elapsed" and params.get("seconds") is None:
        return f"rule {rule_index} time_elapsed requires params.seconds"
    return None


def validate_action(action_then: dict, rule_index: int) -> str | None:
    action = action_then.get("action")
    params = action_then.get("params") or {}
    if action not in SUPPORTED_ACTIONS:
        return f"rule {rule_index} uses unsupported action: {action}"
    if action == "add_same_side_position":
        if not any(key in params for key in ("margin_pct", "size_pct", "notional_usdt")):
            return (
                f"rule {rule_index} add_same_side_position requires one of "
                "params.margin_pct, params.size_pct, or params.notional_usdt"
            )
    if action == "close_partial" and params.get("size_pct") is None:
        return f"rule {rule_index} close_partial requires params.size_pct"
    if action == "move_stop" and params.get("stop_price") is None:
        return f"rule {rule_index} move_stop requires params.stop_price"
    if action == "notify_only" and not params.get("message"):
        return f"rule {rule_index} notify_only requires params.message"
    return None


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
    if not payload.get("rules"):
        parsed = parse_natural_language(payload)
        if parsed is not None:
            payload = parsed
    inst_id = payload.get("instId")
    profile = payload.get("profile", "demo")
    rules = payload.get("rules")

    if not inst_id:
        return fail("instId is required")
    if not isinstance(rules, list) or not rules:
        return fail("at least one rule is required")

    for index, rule in enumerate(rules, start=1):
        rule.setdefault("id", f"rule_{index}")
        rule.setdefault("enabled", True)
        rule.setdefault("once", True)
        event_error = validate_event(rule.get("if") or {}, index)
        if event_error:
            return fail(event_error)
        action_error = validate_action(rule.get("then") or {}, index)
        if action_error:
            return fail(action_error)

    compiled = {
        "ok": True,
        "playbook_id": payload.get("playbook_id") or f"pb_{int(time.time())}",
        "schema_version": "2.0.0-alpha",
        "profile": profile,
        "instId": inst_id,
        "position_ref": payload.get("position_ref", "current"),
        "entry": payload.get("entry"),
        "rules": rules,
        "source_text": payload.get("request_text") or payload.get("text") or payload.get("instruction"),
        "status": "supported",
        "summary": f"Compiled {len(rules)} playbook rule(s) for {inst_id}.",
        "next_step": "scalper-executor" if payload.get("entry") else "scalper-position-watch",
    }
    json.dump(compiled, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
