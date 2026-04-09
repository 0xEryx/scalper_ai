#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]


def run_python(script: Path, payload: dict | None = None, args: list[str] | None = None) -> dict:
    cmd = ["python3", str(script)]
    if args:
        cmd.extend(args)
    completed = subprocess.run(
        cmd,
        input=(json.dumps(payload, ensure_ascii=True) + "\n") if payload is not None else None,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or f"failed: {' '.join(cmd)}")
    text = completed.stdout.strip()
    return json.loads(text) if text else {}


def build_playbook(args: argparse.Namespace) -> dict:
    rule = {
        "if": {
            "event": "price_lte" if args.entry_side == "sell" else "price_gte",
            "params": {"price": args.trigger_price},
        },
        "then": {
            "action": "move_stop",
            "params": {"stop_price": args.new_stop_price},
        },
    }
    if args.include_reverse:
        rule2 = {
            "if": {"event": "position_stopped", "params": {}},
            "then": {"action": "open_opposite_same_notional", "params": {}},
        }
        rules = [rule, rule2]
    else:
        rules = [rule]
    return {
        "profile": args.profile,
        "instId": args.inst_id,
        "position_ref": "current",
        "entry": {
            "side": args.entry_side,
            "order_type": args.order_type,
            "entry_price": args.entry_price,
            "size_usdt": args.size_usdt,
        },
        "rules": rules,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the full OpenClaw scalper MVP demo flow.")
    parser.add_argument("--profile", default="demo")
    parser.add_argument("--inst-id", default="BTC-USDT-SWAP")
    parser.add_argument("--entry-side", choices=["buy", "sell"], default="sell")
    parser.add_argument("--order-type", choices=["limit", "market"], default="limit")
    parser.add_argument("--entry-price", type=float, default=82150.0)
    parser.add_argument("--size-usdt", type=float, default=300.0)
    parser.add_argument("--trigger-price", type=float, default=81500.0)
    parser.add_argument("--new-stop-price", type=float, default=82100.0)
    parser.add_argument("--watch-price", type=float, default=81490.0)
    parser.add_argument("--include-reverse", action="store_true")
    args = parser.parse_args()

    precheck_script = ROOT / "skills/scalper-precheck/scripts/run_precheck.py"
    compile_script = ROOT / "skills/scalper-playbook/scripts/compile_playbook.py"
    save_script = ROOT / "skills/scalper-playbook/scripts/save_playbook.py"
    entry_script = ROOT / "skills/scalper-executor/scripts/place_entry_order.py"
    detect_script = ROOT / "skills/scalper-position-watch/scripts/detect_events.py"
    dispatch_script = ROOT / "skills/scalper-executor/scripts/dispatch_action.py"

    summary: dict[str, object] = {"ok": True}

    precheck = run_python(precheck_script, args=["--inst-id", args.inst_id, "--profile", args.profile])
    summary["precheck"] = precheck

    playbook_request = build_playbook(args)
    compiled = run_python(compile_script, payload=playbook_request)
    summary["compiled_playbook"] = compiled

    saved = run_python(save_script, payload=compiled)
    summary["saved_playbook"] = saved

    entry_payload = {
        "profile": args.profile,
        "instId": args.inst_id,
        "entry": playbook_request["entry"],
        "execute": False,
    }
    entry_order = run_python(entry_script, payload=entry_payload)
    summary["entry_order"] = entry_order

    detector_input = {
        "playbook": compiled,
        "snapshot": {"last_price": args.watch_price, "position_stopped": False},
    }
    detected = run_python(detect_script, payload=detector_input)
    summary["detected_events"] = detected

    dispatched = []
    for match in detected.get("matched_rules", []):
        action_payload = {
            "profile": args.profile,
            "instId": args.inst_id,
            "entry": playbook_request["entry"],
            "action": match["action"]["action"],
            "params": match["action"].get("params", {}),
            "execute": False,
        }
        if action_payload["action"] == "move_stop":
            action_payload["params"].update(
                {
                    "position_side": "short" if args.entry_side == "sell" else "long",
                    "position_size": 1,
                    "td_mode": "cross",
                }
            )
        dispatched.append(run_python(dispatch_script, payload=action_payload))
    summary["dispatched_actions"] = dispatched

    if args.include_reverse:
        reverse_payload = {
            "profile": args.profile,
            "instId": args.inst_id,
            "entry": playbook_request["entry"],
            "action": "open_opposite_same_notional",
            "params": {},
            "execute": False,
        }
        summary["reverse_preview"] = run_python(dispatch_script, payload=reverse_payload)

    json.dump(summary, sys.stdout, ensure_ascii=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
