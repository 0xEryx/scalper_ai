# Runtime Layout

The custom scalper suite uses a shared runtime directory outside the skills themselves:

```text
.scalper-runtime/
  playbooks/
  state/
  logs/
  journal/
```

## Recommended Files

- `playbooks/<playbook_id>.json` — compiled playbook definition
- `state/active-playbooks.json` — active watcher set
- `state/positions-cache.json` — latest known positions snapshot
- `logs/events.jsonl` — detected events
- `logs/actions.jsonl` — dispatched actions
- `logs/orders.jsonl` — order placement / modification results
- `journal/YYYY-MM-DD.md` — daily trading journal

## Logging Rules

- Every detected event should append one line to `logs/events.jsonl`
- Every dispatched action should append one line to `logs/actions.jsonl`
- Every OKX order write should append one line to `logs/orders.jsonl`
- Logs should be append-only JSONL for MVP
