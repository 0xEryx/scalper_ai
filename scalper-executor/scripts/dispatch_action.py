#!/usr/bin/env python3
import json
import shlex
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EXECUTOR_SKILL_DIR = SCRIPT_DIR.parent
WORKSPACE_ROOT = EXECUTOR_SKILL_DIR.parent.parent
RUNTIME_ROOT = WORKSPACE_ROOT / ".scalper-runtime"

SUPPORTED = {
    "move_stop",
    "move_stop_to_break_even",
    "close_partial",
    "close_all",
    "open_opposite_same_notional",
    "add_same_side_position",
    "notify_only",
}


def append_jsonl(path: str, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def run_okx(cmd: list[str], execute: bool) -> dict:
    shell = " ".join(shlex.quote(x) for x in cmd)
    if not execute:
        return {"ok": True, "execute": False, "command": cmd, "shell": shell}
    completed = subprocess.run(cmd + ["--json"], capture_output=True, text=True)
    return {
        "ok": completed.returncode == 0,
        "execute": True,
        "command": cmd,
        "shell": shell,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def load_positions(profile: str, inst_id: str) -> list[dict]:
    completed = subprocess.run(
        ["okx", "--profile", profile, "swap", "positions", inst_id, "--json"],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "failed to load positions")
    text = completed.stdout.strip()
    return json.loads(text) if text else []


def load_algo_orders(profile: str, inst_id: str) -> list[dict]:
    completed = subprocess.run(
        [
            "okx",
            "--profile",
            profile,
            "swap",
            "algo",
            "orders",
            "--instId",
            inst_id,
            "--ordType",
            "conditional",
            "--json",
        ],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "failed to load algo orders")
    text = completed.stdout.strip()
    return json.loads(text) if text else []


def load_balance(profile: str) -> dict:
    completed = subprocess.run(
        ["okx", "--profile", profile, "account", "balance", "--json"],
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or "failed to load balance")
    text = completed.stdout.strip()
    rows = json.loads(text) if text else []
    if not rows:
        raise RuntimeError("empty balance response")
    details = []
    for row in rows:
        if isinstance(row.get("details"), list):
            details.extend(row["details"])
        else:
            details.append(row)
    for row in details:
        ccy = (row.get("ccy") or "").upper()
        if ccy == "USDT":
            return row
    return details[0]


def infer_position(profile: str, inst_id: str, payload: dict) -> dict:
    params = payload.get("params") or {}
    if params.get("position_side") and params.get("position_size"):
        return {
            "posSide": params["position_side"],
            "size": str(params["position_size"]),
            "tdMode": params.get("td_mode", "cross"),
        }
    positions = load_positions(profile, inst_id)
    if not positions:
        raise RuntimeError("no non-zero position found for this instrument")
    if len(positions) > 1:
        desired = params.get("position_side")
        if desired:
            for position in positions:
                if position.get("posSide") == desired or position.get("side") == desired:
                    return position
        raise RuntimeError("multiple positions found; specify params.position_side")
    return positions[0]


def normalize_pos_side(position: dict) -> str:
    side = position.get("posSide") or position.get("side")
    if side in {"long", "short"}:
        return side
    raise RuntimeError(f"unsupported position side: {side}")


def build_move_stop(payload: dict, execute: bool) -> dict:
    profile = payload["profile"]
    inst_id = payload["instId"]
    params = payload.get("params") or {}
    stop_price = params.get("stop_price")
    if stop_price is None:
        raise RuntimeError("move_stop requires params.stop_price")

    position = infer_position(profile, inst_id, payload)
    pos_side = normalize_pos_side(position)
    size = str(position.get("size") or position.get("availPos") or "")
    td_mode = position.get("mgnMode") or position.get("tdMode") or params.get("td_mode") or "cross"
    if not size:
        raise RuntimeError("unable to determine current position size")
    close_side = "sell" if pos_side == "long" else "buy"

    algo_orders = load_algo_orders(profile, inst_id)
    active = None
    for order in algo_orders:
        if order.get("state") in {"live", "effective"} and (order.get("posSide") == pos_side or not order.get("posSide")):
            active = order
            break

    if active and active.get("algoId"):
        cmd = [
            "okx",
            "--profile",
            profile,
            "swap",
            "algo",
            "amend",
            "--instId",
            inst_id,
            "--algoId",
            str(active["algoId"]),
            "--newSlTriggerPx",
            str(stop_price),
            "--newSlOrdPx=-1",
        ]
    else:
        cmd = [
            "okx",
            "--profile",
            profile,
            "swap",
            "algo",
            "place",
            "--instId",
            inst_id,
            "--side",
            close_side,
            "--ordType",
            "conditional",
            "--sz",
            size,
            "--tdMode",
            td_mode,
            "--posSide",
            pos_side,
            "--reduceOnly",
            "--slTriggerPx",
            str(stop_price),
            "--slOrdPx=-1",
        ]
    return run_okx(cmd, execute)


def build_move_stop_to_break_even(payload: dict, execute: bool) -> dict:
    profile = payload["profile"]
    inst_id = payload["instId"]
    params = dict(payload.get("params") or {})
    entry_price = params.get("entry_price")
    if entry_price is None:
        position = infer_position(profile, inst_id, payload)
        entry_price = position.get("avgPx") or position.get("avgPxUsd") or position.get("markPx")
    if entry_price is None:
        raise RuntimeError("move_stop_to_break_even requires an entry price or live position average price")
    delegated_payload = {
        **payload,
        "action": "move_stop",
        "params": {
            **params,
            "stop_price": float(entry_price),
        },
    }
    result = build_move_stop(delegated_payload, execute)
    result["delegated_action"] = "move_stop"
    result["break_even_price"] = float(entry_price)
    return result


def build_close_partial(payload: dict, execute: bool) -> dict:
    profile = payload["profile"]
    inst_id = payload["instId"]
    params = payload.get("params") or {}
    size_pct = params.get("size_pct")
    if size_pct is None:
        raise RuntimeError("close_partial requires params.size_pct")

    position = infer_position(profile, inst_id, payload)
    pos_side = normalize_pos_side(position)
    current_size = float(position.get("size") or 0)
    if current_size <= 0:
        raise RuntimeError("position size must be positive")
    close_size = max(round(current_size * (float(size_pct) / 100.0), 8), 0.00000001)
    close_side = "sell" if pos_side == "long" else "buy"
    td_mode = position.get("mgnMode") or position.get("tdMode") or params.get("td_mode") or "cross"

    cmd = [
        "okx",
        "--profile",
        profile,
        "swap",
        "place",
        "--instId",
        inst_id,
        "--side",
        close_side,
        "--ordType",
        "market",
        "--sz",
        str(close_size),
        "--tdMode",
        td_mode,
        "--posSide",
        pos_side,
    ]
    return run_okx(cmd, execute)


def build_close_all(payload: dict, execute: bool) -> dict:
    profile = payload["profile"]
    inst_id = payload["instId"]
    position = infer_position(profile, inst_id, payload)
    pos_side = normalize_pos_side(position)
    td_mode = position.get("mgnMode") or position.get("tdMode") or "cross"
    cmd = [
        "okx",
        "--profile",
        profile,
        "swap",
        "close",
        "--instId",
        inst_id,
        "--mgnMode",
        td_mode,
        "--posSide",
        pos_side,
        "--autoCxl",
    ]
    return run_okx(cmd, execute)


def build_open_opposite_same_notional(payload: dict, execute: bool) -> dict:
    profile = payload["profile"]
    inst_id = payload["instId"]
    params = payload.get("params") or {}
    reference_side = params.get("reference_side")
    size_usdt = params.get("notional_usdt")
    if reference_side is None:
        entry = payload.get("entry") or {}
        reference_side = entry.get("side")
    if size_usdt is None:
        entry = payload.get("entry") or {}
        size_usdt = entry.get("size_usdt")
    if reference_side not in {"buy", "sell", "long", "short"}:
        raise RuntimeError("open_opposite_same_notional requires params.reference_side or entry.side")
    if size_usdt is None:
        raise RuntimeError("open_opposite_same_notional requires params.notional_usdt or entry.size_usdt")

    normalized = "buy" if reference_side in {"buy", "long"} else "sell"
    opposite_side = "sell" if normalized == "buy" else "buy"
    pos_side = "short" if opposite_side == "sell" else "long"
    td_mode = params.get("td_mode", "cross")
    cmd = [
        "okx",
        "--profile",
        profile,
        "swap",
        "place",
        "--instId",
        inst_id,
        "--side",
        opposite_side,
        "--ordType",
        "market",
        "--sz",
        str(size_usdt),
        "--tgtCcy",
        "quote_ccy",
        "--tdMode",
        td_mode,
        "--posSide",
        pos_side,
    ]
    return run_okx(cmd, execute)


def resolve_same_side_params(payload: dict) -> tuple[str, str, str, float]:
    profile = payload["profile"]
    inst_id = payload["instId"]
    params = payload.get("params") or {}
    td_mode = params.get("td_mode", "cross")

    reference_side = params.get("reference_side")
    if reference_side is None:
        entry = payload.get("entry") or {}
        reference_side = entry.get("side")
    if reference_side is None:
        position = infer_position(profile, inst_id, payload)
        reference_side = normalize_pos_side(position)
    normalized = "buy" if reference_side in {"buy", "long"} else "sell"
    pos_side = "long" if normalized == "buy" else "short"

    if params.get("notional_usdt") is not None:
        notional = float(params["notional_usdt"])
    else:
        balance = load_balance(profile)
        avail = float(balance.get("availBal") or balance.get("availEq") or balance.get("cashBal") or 0)
        if avail <= 0:
            raise RuntimeError("unable to determine available balance for add_same_side_position")
        if params.get("margin_pct") is not None:
            leverage = float(params.get("leverage") or 1)
            notional = avail * (float(params["margin_pct"]) / 100.0) * leverage
        elif params.get("size_pct") is not None:
            notional = avail * (float(params["size_pct"]) / 100.0)
        else:
            raise RuntimeError(
                "add_same_side_position requires params.notional_usdt, params.margin_pct, or params.size_pct"
            )
    return normalized, pos_side, td_mode, notional


def build_add_same_side_position(payload: dict, execute: bool) -> dict:
    profile = payload["profile"]
    inst_id = payload["instId"]
    side, pos_side, td_mode, notional = resolve_same_side_params(payload)
    cmd = [
        "okx",
        "--profile",
        profile,
        "swap",
        "place",
        "--instId",
        inst_id,
        "--side",
        side,
        "--ordType",
        "market",
        "--sz",
        str(round(notional, 8)),
        "--tgtCcy",
        "quote_ccy",
        "--tdMode",
        td_mode,
        "--posSide",
        pos_side,
    ]
    return run_okx(cmd, execute)


def build_notify_only(payload: dict, execute: bool) -> dict:
    params = payload.get("params") or {}
    message = params.get("message")
    if not message:
        raise RuntimeError("notify_only requires params.message")
    return {
        "ok": True,
        "execute": execute,
        "action": "notify_only",
        "status": "notified",
        "summary": message,
        "message": message,
    }


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        raise SystemExit("dispatch_action.py expected JSON on stdin")
    payload = json.loads(raw)
    action = payload.get("action")
    if action not in SUPPORTED:
        raise SystemExit(f"unsupported action: {action}")

    execute = bool(payload.get("execute"))
    try:
        if action == "move_stop":
            result = build_move_stop(payload, execute)
        elif action == "move_stop_to_break_even":
            result = build_move_stop_to_break_even(payload, execute)
        elif action == "close_partial":
            result = build_close_partial(payload, execute)
        elif action == "close_all":
            result = build_close_all(payload, execute)
        elif action == "add_same_side_position":
            result = build_add_same_side_position(payload, execute)
        elif action == "notify_only":
            result = build_notify_only(payload, execute)
        else:
            result = build_open_opposite_same_notional(payload, execute)
    except Exception as exc:
        result = {"ok": False, "execute": execute, "action": action, "error": str(exc)}

    result["action"] = action
    result.setdefault("status", "executed" if result.get("ok") else "failed")
    result.setdefault("summary", f"{action} {'succeeded' if result.get('ok') else 'failed'}")
    append_jsonl(str(RUNTIME_ROOT / "logs" / "actions.jsonl"), result)
    if any(token in action for token in ["close", "open", "move_stop"]):
        append_jsonl(str(RUNTIME_ROOT / "logs" / "orders.jsonl"), result)

    json.dump(result, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
