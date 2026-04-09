---
name: scalper-position-watch
description: Use this custom OpenClaw skill for watching compiled scalper playbooks and triggering deterministic follow-up actions from simple events such as price_gte, price_lte, and position_stopped. Trigger when a playbook already exists and the agent should continue monitoring, checking rule hits, and dispatching actions. Use for requests like '继续盯这笔单', '按 playbook 继续监控', '检查这个 playbook 有没有命中', or when another custom skill needs watcher behavior. Do not use for natural-language playbook design or direct execution without an existing playbook.
version: "1.0.0"
user-invocable: false
metadata:
  {
    "openclaw":
      {
        "emoji": "👁️",
        "requires": { "bins": ["python3"] },
      },
  }
---

# OpenClaw Scalper Position Watch

This is a custom OpenClaw watcher skill for compiled playbooks.

## Use This Skill When

- a compiled playbook already exists
- the agent needs to detect rule hits and emit follow-up actions
- another custom skill or script needs watcher semantics
- a user says things like:
  - "继续盯这笔单"
  - "按 playbook 继续监控"
  - "检查这个规则有没有命中"
  - "这笔单后面按剧本继续跑"

## Do Not Use This Skill When

- the user is still describing the trade in prose
- a plain order placement is enough
- the request requires unsupported indicator-driven triggers
- there is no existing playbook id or playbook payload to watch

## Workflow Position

This skill is usually the final ongoing-monitoring step in the custom scalper workflow.

## Before Using This Skill

- Before using this skill, a compiled playbook should already exist.
- If the user is still writing the rules in prose, go back to `scalper-playbook`.
- If the user only needs a one-off write action, prefer `scalper-executor`.

## After This Skill

- After a rule hit is detected, route the resulting action to `scalper-executor`.
- After watcher output is reported, keep monitoring only if the playbook is still active.
- If the playbook is unsupported or missing, stop and explain what is needed next.

## Routing Priority

- Prefer `scalper-playbook` before this skill when the user is still defining the rules.
- Prefer `scalper-executor` before this skill when the task is a one-off write action with no ongoing monitoring.
- Use this skill only after a playbook exists.

## Workflow

1. Load the playbook file from `.scalper-runtime/playbooks/<playbook_id>.json`.
2. Fetch or receive the current market and position snapshot.
3. Run `scripts/detect_events.py` to determine which rule conditions are satisfied.
4. If any rule fires, pass the emitted action into `../scalper-executor/scripts/dispatch_action.py`.
5. Append detected events and actions into the runtime logs.

## User Request Examples

- "继续按这个 playbook 盯 BTC-USDT-SWAP"
- "检查 pb_20260410_001 现在有没有命中规则"
- "这笔单后面继续按剧本跑"

## Ambiguity And Unsupported Requests

- If no playbook id is provided, stop and ask for it.
- If the playbook uses unsupported events or actions, stop and say the current watcher MVP cannot handle it yet.
- Never invent watcher behavior not defined in the stored playbook.

## References

- Watcher contract: `references/watcher-contract.md`
- Shared runtime layout: `../scalper-playbook/references/runtime-layout.md`
