---
name: scalper-executor
description: Use this custom OpenClaw skill for deterministic OKX trade execution after precheck and playbook validation. Trigger when the agent already has a clear structured order or playbook action such as place entry, move stop, close partial, close all, or open opposite same notional, including requests like '执行这笔单', '把这个 action 发给 OKX', '现在下这个 demo 单', or '按这个结构化 payload 执行'. Prefer this skill only after the request is already explicit and structured. Do not use for ambiguous trader requests or unsupported strategy logic.
version: "1.0.0"
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "⚙️",
        "requires": { "bins": ["okx", "python3"] },
      },
  }
---

# OpenClaw Scalper Executor

This is a custom OpenClaw skill for deterministic OKX execution. It is not an OKX official skill.

## Use This Skill When

- the order details are already structured
- a compiled playbook rule has emitted a concrete action
- the agent needs to turn a validated action into an OKX CLI command
- a user says things like:
  - "执行这笔单"
  - "按这个 payload 下单"
  - "现在把这个 action 发给 OKX"
  - "把止损真的改掉"

## Do Not Use This Skill When

- the request is ambiguous or missing execution parameters
- the task is only to compile a playbook
- the task is only to keep watching an existing position
- the user is still brainstorming or asking whether a trade is good enough

## Workflow Position

This skill is usually the concrete write-action step in the custom scalper workflow.

## Before Using This Skill

- Before using this skill for a new trade idea, the agent should usually run `scalper-precheck`.
- Before using this skill for rule-based management, the agent should usually run `scalper-playbook` first.
- If precheck has not been run for a fresh idea, or if the user is still describing logic in prose, do not execute yet.
- If required fields are missing, stop and ask for clarification instead of guessing.

## After This Skill

- After placing an entry order with ongoing rules, route to `scalper-position-watch`.
- After a one-off action such as `move_stop` or `close_partial`, report the result clearly and do not invent follow-up behavior.
- If execution is rejected or unsupported, stop and explain the limitation.

## Routing Priority

- Prefer `scalper-precheck` first when the user is still evaluating a trade.
- Prefer `scalper-playbook` first when the user is still describing rules in prose.
- Use this skill only when the next step is an actual OKX write action.

## Workflow

1. Accept only structured payloads that already identify `instId`, `profile`, and `action`.
2. If required fields are missing, stop and tell the user the request is not executable in the current MVP.
3. For entry orders, run `scripts/place_entry_order.py`.
4. For follow-up actions, run `scripts/dispatch_action.py`.
5. Log any successful write into `.scalper-runtime/logs/orders.jsonl`.

## User Request Examples

- "按这个结构化空单参数执行 demo 下单"
- "把这笔单的 stop move 到 82100"
- "把这笔仓位先平掉一半"
- "如果 playbook 命中，就执行动作"

## Ambiguity And Unsupported Requests

- If the order request is ambiguous, stop and ask for clarification.
- If the action cannot be mapped to the supported MVP action set, say that this version does not support it yet.
- Never guess price, side, size, or profile.

## References

- Action mapping: `references/action-mapping.md`
- Shared runtime layout: `../scalper-playbook/references/runtime-layout.md`
