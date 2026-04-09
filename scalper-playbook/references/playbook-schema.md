# Scalper Playbook Schema v1

This MVP schema is intentionally small. If a trader request cannot be represented here, the skill should refuse and explain that the current version does not support it yet.

## Root Object

```json
{
  "playbook_id": "pb_20260410_001",
  "profile": "demo",
  "instId": "BTC-USDT-SWAP",
  "position_ref": "current",
  "entry": {
    "side": "sell",
    "order_type": "limit",
    "entry_price": 82150,
    "size_usdt": 300
  },
  "rules": []
}
```

## Supported Events

- `price_gte`
- `price_lte`
- `position_stopped`

## Supported Actions

- `move_stop`
- `close_partial`
- `close_all`
- `open_opposite_same_notional`

## Rule Shape

```json
{
  "if": {
    "event": "price_lte",
    "params": { "price": 81500 }
  },
  "then": {
    "action": "move_stop",
    "params": { "stop_price": 82100 }
  }
}
```

## Notes

- `move_stop` requires `stop_price`
- `close_partial` requires `size_pct`
- `open_opposite_same_notional` requires no extra params in v1
- `position_ref` stays `current` in MVP
