# Action Mapping

This skill maps a small action vocabulary into OKX CLI commands.

## Entry Order

Input:

```json
{
  "profile": "demo",
  "instId": "BTC-USDT-SWAP",
  "entry": {
    "side": "sell",
    "order_type": "limit",
    "entry_price": 82150,
    "size_usdt": 300
  }
}
```

## Supported Follow-up Actions

- `move_stop`
- `close_partial`
- `close_all`
- `open_opposite_same_notional`

## Execution Mode

- By default, the executor scripts return a dry-run command payload.
- Set `"execute": true` in the JSON payload to perform the live demo/write action.
- Every action appends JSONL records under `.scalper-runtime/logs/`.

## Current MVP Mapping

- `move_stop`
  - load current swap position
  - check existing `swap algo orders`
  - amend an existing conditional stop when possible
  - otherwise place a new reduce-only conditional stop

- `close_partial`
  - market-close a percentage of the current position using `okx swap place`

- `close_all`
  - close the full position using `okx swap close`

- `open_opposite_same_notional`
  - place an opposite-side market order using quote-currency notional sizing
