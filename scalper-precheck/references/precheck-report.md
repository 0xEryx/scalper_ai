# Precheck Report

`run_precheck.py` should return one JSON object.

## Output Shape

```json
{
  "ok": true,
  "instId": "BTC-USDT-SWAP",
  "profile": "demo",
  "status": "caution",
  "snapshot": {
    "last_price": 82150.5,
    "spread": 0.5,
    "spread_bps": 0.06,
    "depth_bid_top5_notional": 125000.0,
    "depth_ask_top5_notional": 117000.0,
    "volatility_5m_pct": 0.82,
    "volatility_15m_pct": 1.43,
    "funding_rate": 0.0008,
    "open_interest": 1250000.0,
    "session_liquidity": "normal",
    "open_order_count": 0,
    "position_count": 0
  },
  "checks": [
    {"name": "spread", "status": "pass"},
    {"name": "depth", "status": "pass"}
  ],
  "warnings": [
    "Spread is acceptable for MVP.",
    "Funding is elevated but not blocked."
  ]
}
```

## Status Meaning

- `pass`: no major warning for the current MVP checks
- `caution`: tradable, but the agent should surface warnings before continuing
- `reject`: the agent should stop and ask the trader to revise the plan

## Current Backing Data

The current MVP pulls live data through the OKX CLI:

- `okx market ticker`
- `okx market orderbook`
- `okx market candles`
- `okx market funding-rate`
- `okx market open-interest`
- `okx swap orders`
- `okx swap positions`
