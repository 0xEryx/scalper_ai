# Watcher Contract

The watcher MVP is deterministic and file-based.

## Inputs

- one playbook JSON file
- one market/position snapshot JSON object

## Modes

### Low-level mode

- `watch_playbook.py` loads the playbook and persisted watcher state
- `detect_events.py` evaluates rules and writes next state
- callers decide whether to execute actions

### Script-first cycle mode

- `run_watch_cycle.py` performs one complete watcher cycle
- it fetches ticker data directly from OKX unless a snapshot file is supplied
- it evaluates rule hits and can dispatch actions immediately with `--execute`
- it appends a structured cycle record into `.scalper-runtime/logs/watch-cycles.jsonl`

### Service mode

- `run_watch_service.py` wraps one cycle for background execution
- when no rule fires, it stays quiet except for the returned service envelope
- when a rule fires, it emits one stable event record into `.scalper-runtime/events/watch-events.jsonl`
- optional notifier hooks can forward that event to a messaging or LLM layer
- `notify_watch_event.py` is the default bridge script in this workspace and converts the event into an OpenClaw system event so chat delivery can stay LLM-light

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

`run_watch_cycle.py` returns:

```json
{
  "ok": true,
  "playbook_id": "pb_20260410_001",
  "profile": "A",
  "instId": "ETH-USDT-SWAP",
  "snapshot": {
    "last_price": 2232.1,
    "ts": 1775965000
  },
  "watch": {
    "status": "rule_triggered"
  },
  "actions": [
    {
      "ok": true,
      "action": "add_same_side_position",
      "status": "executed"
    }
  ],
  "status": "action_executed",
  "summary": "Executed 1 action(s) for pb_20260410_001"
}
```

`run_watch_service.py` returns and emits:

```json
{
  "ok": true,
  "playbook_id": "pb_20260410_001",
  "event_emitted": true,
  "event": {
    "kind": "scalper.watch.triggered",
    "playbook_id": "pb_20260410_001",
    "profile": "A",
    "instId": "ETH-USDT-SWAP",
    "action": {
      "name": "add_same_side_position",
      "status": "executed",
      "ok": true
    },
    "snapshot": {
      "last_price": 2255,
      "ts": 1775965720
    },
    "watch": {
      "matched_rules": [
        { "rule_id": "rule_1" }
      ]
    }
  }
}
```
