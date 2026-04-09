# Watcher Contract

The watcher MVP is deterministic and file-based.

## Inputs

- one playbook JSON file
- one market/position snapshot JSON object

## Outputs

`detect_events.py` returns:

```json
{
  "ok": true,
  "playbook_id": "pb_20260410_001",
  "matched_rules": [
    {
      "rule_index": 1,
      "event": "price_lte",
      "action": {
        "action": "move_stop",
        "params": { "stop_price": 82100 }
      }
    }
  ]
}
```
