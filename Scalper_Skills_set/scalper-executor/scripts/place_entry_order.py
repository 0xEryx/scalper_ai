#!/usr/bin/env python3
import json
import shlex
import subprocess
import sys
from pathlib import Path


def append_jsonl(path: str, payload: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def main() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        raise SystemExit("place_entry_order.py expected JSON on stdin")

    payload = json.loads(raw)
    entry = payload.get("entry") or {}
    profile = payload.get("profile", "demo")
    inst_id = payload.get("instId")
    side = entry.get("side")
    order_type = entry.get("order_type", "limit")
    size_usdt = entry.get("size_usdt")
    price = entry.get("entry_price")

    if not inst_id or not side or not size_usdt:
        raise SystemExit("instId, entry.side, and entry.size_usdt are required")

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
        order_type,
        "--sz",
        str(size_usdt),
        "--tgtCcy",
        "quote_ccy",
        "--tdMode",
        "cross",
        "--posSide",
        "short" if side == "sell" else "long",
    ]
    if order_type == "limit":
        if price is None:
            raise SystemExit("limit order requires entry.entry_price")
        cmd.extend(["--px", str(price)])

    execute = bool(payload.get("execute"))
    result = {"ok": True, "execute": execute, "command": cmd, "shell": " ".join(shlex.quote(x) for x in cmd)}
    if execute:
        completed = subprocess.run(cmd + ["--json"], capture_output=True, text=True)
        result["ok"] = completed.returncode == 0
        result["stdout"] = completed.stdout
        result["stderr"] = completed.stderr
        result["returncode"] = completed.returncode
    append_jsonl(".scalper-runtime/logs/orders.jsonl", {"type": "entry_order", **result})
    json.dump(result, sys.stdout)
    sys.stdout.write("\n")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
