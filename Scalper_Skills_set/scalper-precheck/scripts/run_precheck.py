#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import subprocess
import sys


def run_okx(args: list[str]) -> object:
    cmd = ["okx", *args, "--json"]
    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or f"command failed: {' '.join(cmd)}")
    text = completed.stdout.strip()
    if not text:
        return []
    return json.loads(text)


def to_float(value: str | float | int | None) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def compute_window_volatility(candles: list[list[str]], count: int) -> float:
    window = candles[:count]
    if not window:
        return 0.0
    highs = [to_float(row[2]) for row in window]
    lows = [to_float(row[3]) for row in window]
    closes = [to_float(row[4]) for row in window]
    denom = closes[0] if closes and closes[0] else 1.0
    return round(((max(highs) - min(lows)) / denom) * 100, 4)


def session_liquidity_label(now: dt.datetime) -> str:
    hour = now.hour
    if 0 <= hour < 7:
        return "low"
    if 7 <= hour < 9:
        return "transition"
    return "normal"


def build_checks(snapshot: dict) -> tuple[list[dict], list[str], str]:
    checks: list[dict] = []
    warnings: list[str] = []

    spread_bps = snapshot["spread_bps"]
    if spread_bps > 4:
        checks.append({"name": "spread", "status": "reject", "reason": "spread is too wide"})
    elif spread_bps > 1.5:
        checks.append({"name": "spread", "status": "caution", "reason": "spread is elevated"})
        warnings.append("Bid/ask spread is elevated for a tight scalper entry.")
    else:
        checks.append({"name": "spread", "status": "pass"})

    depth_floor = min(snapshot["depth_bid_top5_notional"], snapshot["depth_ask_top5_notional"])
    if depth_floor < 8000:
        checks.append({"name": "depth", "status": "reject", "reason": "top-5 depth is thin"})
    elif depth_floor < 20000:
        checks.append({"name": "depth", "status": "caution", "reason": "top-5 depth is moderate"})
        warnings.append("Orderbook depth is moderate; watch slippage on aggressive execution.")
    else:
        checks.append({"name": "depth", "status": "pass"})

    vol_5m = snapshot["volatility_5m_pct"]
    if vol_5m > 2.0:
        checks.append({"name": "volatility", "status": "reject", "reason": "5m volatility is extreme"})
    elif vol_5m > 1.2 or vol_5m < 0.15:
        reason = "5m volatility is elevated" if vol_5m > 1.2 else "5m volatility is compressed"
        checks.append({"name": "volatility", "status": "caution", "reason": reason})
        warnings.append(f"{reason.capitalize()} for the current scalper setup.")
    else:
        checks.append({"name": "volatility", "status": "pass"})

    funding_abs = abs(snapshot["funding_rate"])
    if funding_abs >= 0.03:
        checks.append({"name": "funding", "status": "reject", "reason": "funding is extreme"})
    elif funding_abs >= 0.01:
        checks.append({"name": "funding", "status": "caution", "reason": "funding is elevated"})
        warnings.append("Funding is elevated and may signal a crowded perp direction.")
    else:
        checks.append({"name": "funding", "status": "pass"})

    checks.append({"name": "oi", "status": "pass"})

    if snapshot["session_liquidity"] == "low":
        checks.append({"name": "session", "status": "caution", "reason": "low-liquidity session"})
        warnings.append("Current time window is a low-liquidity session.")
    else:
        checks.append({"name": "session", "status": "pass"})

    if snapshot["open_order_count"] > 0:
        checks.append(
            {
                "name": "open_orders",
                "status": "caution",
                "reason": f"{snapshot['open_order_count']} live order(s) already exist",
            }
        )
        warnings.append("There are already live swap orders on this instrument.")
    else:
        checks.append({"name": "open_orders", "status": "pass"})

    if snapshot["position_count"] > 0:
        checks.append(
            {
                "name": "positions",
                "status": "caution",
                "reason": f"{snapshot['position_count']} non-zero position(s) already exist",
            }
        )
        warnings.append("There is already an open position on this instrument.")
    else:
        checks.append({"name": "positions", "status": "pass"})

    status = "pass"
    if any(item["status"] == "reject" for item in checks):
        status = "reject"
    elif any(item["status"] == "caution" for item in checks):
        status = "caution"
    return checks, warnings, status


def build_snapshot(inst_id: str, profile: str) -> dict:
    ticker_rows = run_okx(["market", "ticker", inst_id])
    orderbook_rows = run_okx(["market", "orderbook", inst_id, "--sz", "5"])
    candles = run_okx(["market", "candles", inst_id, "--bar", "1m", "--limit", "20"])
    funding_rows = run_okx(["market", "funding-rate", inst_id]) if inst_id.endswith("-SWAP") else []
    oi_rows = (
        run_okx(["market", "open-interest", "--instType", "SWAP", "--instId", inst_id])
        if inst_id.endswith("-SWAP")
        else []
    )
    orders_rows = run_okx(["swap", "orders", "--instId", inst_id]) if inst_id.endswith("-SWAP") else []
    positions_rows = run_okx(["swap", "positions", inst_id]) if inst_id.endswith("-SWAP") else []

    ticker = ticker_rows[0]
    book = orderbook_rows[0]
    funding = funding_rows[0] if funding_rows else {}
    oi = oi_rows[0] if oi_rows else {}

    best_ask = to_float(ticker.get("askPx"))
    best_bid = to_float(ticker.get("bidPx"))
    spread = round(best_ask - best_bid, 8)
    mid = (best_ask + best_bid) / 2 if best_ask and best_bid else max(best_ask, best_bid, 1.0)
    spread_bps = round((spread / mid) * 10000, 4)

    asks = book.get("asks", [])
    bids = book.get("bids", [])
    depth_bid = round(sum(to_float(px) * to_float(sz) for px, sz, *_ in bids), 2)
    depth_ask = round(sum(to_float(px) * to_float(sz) for px, sz, *_ in asks), 2)

    now = dt.datetime.now().astimezone()
    snapshot = {
        "last_price": to_float(ticker.get("last")),
        "spread": spread,
        "spread_bps": spread_bps,
        "depth_bid_top5_notional": depth_bid,
        "depth_ask_top5_notional": depth_ask,
        "volatility_5m_pct": compute_window_volatility(candles, 5),
        "volatility_15m_pct": compute_window_volatility(candles, 15),
        "funding_rate": to_float(funding.get("fundingRate")),
        "open_interest": to_float(oi.get("oiUsd") or oi.get("oi")),
        "session_liquidity": session_liquidity_label(now),
        "open_order_count": len(orders_rows),
        "position_count": len(positions_rows),
    }
    checks, warnings, status = build_checks(snapshot)
    return {
        "ok": True,
        "instId": inst_id,
        "profile": profile,
        "status": status,
        "snapshot": snapshot,
        "checks": checks,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a live OKX-backed scalper precheck snapshot.")
    parser.add_argument("--inst-id", required=True)
    parser.add_argument("--profile", default="demo")
    args = parser.parse_args()

    try:
        payload = build_snapshot(args.inst_id, args.profile)
    except Exception as exc:
        json.dump({"ok": False, "instId": args.inst_id, "profile": args.profile, "error": str(exc)}, sys.stdout, ensure_ascii=True)
        sys.stdout.write("\n")
        return 1

    json.dump(payload, sys.stdout, ensure_ascii=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
