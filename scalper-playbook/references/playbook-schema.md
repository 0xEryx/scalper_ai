# Scalper Playbook Schema v2

This schema is intentionally compact but no longer limited to one-step rules. If
a trader request still cannot be represented here, the skill should refuse and
explain that the current version does not support that strategy shape yet.

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

## Rule Metadata

Each rule may include lightweight control metadata:

```json
{
  "id": "rule_move_stop_after_rebound",
  "enabled": true,
  "once": true,
  "if": {},
  "then": {}
}
```

- `id`: optional stable rule identifier
- `enabled`: optional boolean, defaults to `true`
- `once`: optional boolean, defaults to `true`

## Supported Events

- `price_gte`
- `price_lte`
- `position_stopped`
- `entry_filled`
- `tp_hit`
- `sl_hit`
- `time_elapsed`
- `sequence`

## Supported Actions

- `move_stop`
- `close_partial`
- `close_all`
- `open_opposite_same_notional`
- `add_same_side_position`
- `move_stop_to_break_even`
- `notify_only`

## Rule Shape

```json
{
  "id": "rule_move_stop",
  "enabled": true,
  "once": true,
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

## Sequential Rule Shape

Use `sequence` for simple stateful two-step logic where one price condition must
arm the rule before a second price condition can fire the action.

```json
{
  "id": "rule_add_short_after_rebound",
  "enabled": true,
  "once": true,
  "if": {
    "event": "sequence",
    "params": {
      "steps": [
        { "event": "price_lte", "params": { "price": 2122 } },
        { "event": "price_gte", "params": { "price": 2144 } }
      ]
    }
  },
  "then": {
    "action": "add_same_side_position",
    "params": {
      "margin_pct": 3,
      "leverage": 20
    }
  }
}
```

## Lifecycle Rule Examples

Break-even after TP1:

```json
{
  "id": "rule_break_even_after_tp1",
  "if": {
    "event": "tp_hit",
    "params": { "target": "tp1" }
  },
  "then": {
    "action": "move_stop_to_break_even",
    "params": {}
  }
}
```

Notify after entry fill:

```json
{
  "id": "rule_notify_entry",
  "if": {
    "event": "entry_filled",
    "params": {}
  },
  "then": {
    "action": "notify_only",
    "params": {
      "message": "Entry filled. Continue monitoring for the next stage."
    }
  }
}
```

## Notes

- `move_stop` requires `stop_price`
- `close_partial` requires `size_pct`
- `open_opposite_same_notional` requires no extra params in v1
- `add_same_side_position` adds to the current/entry side instead of reversing
- `move_stop_to_break_even` uses the live position average price when available
- `notify_only` does not place or amend any OKX order
- `add_same_side_position` accepts:
  - `margin_pct`: percent of available USDT margin to allocate
  - `size_pct`: percent of available USDT to use as notional directly
  - `leverage`: leverage multiplier used with `margin_pct`
  - `notional_usdt`: explicit notional override
- `sequence` currently supports only a linear two-step trigger chain
- `tp_hit`, `sl_hit`, and `entry_filled` are watcher lifecycle events derived from
  the incoming snapshot, not directly from raw market ticks
- `time_elapsed` expects `params.seconds` and uses persisted watcher state
- `position_ref` stays `current` in MVP
