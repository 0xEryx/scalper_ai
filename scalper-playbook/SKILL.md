---
name: scalper-playbook
description: Use this custom OpenClaw skill when a trader gives a natural-language scalper plan that should be converted into a structured playbook for later execution and watching. Trigger for instructions like '到 81500 把止损挪到 82100', '如果这单止损了就反手', '第一目标到就保本', '给这单加一个管理剧本', '把这句话编译成 playbook', '为这笔单写交易管理规则', or any request to turn short-term trade management prose into structured events and actions. Prefer this skill after scalper-precheck and before scalper-executor when the user is describing rules rather than asking for immediate raw execution. Do not use for direct raw OKX execution without playbook compilation.
version: "1.0.0"
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "🧠",
        "requires": { "bins": ["python3"] },
      },
  }
---

# OpenClaw Scalper Playbook

This is a custom OpenClaw skill for compiling trader intent into a structured playbook. It is not an OKX official skill.

## Use This Skill When

- a trader describes trade management logic in natural language
- a request contains price-triggered or position-triggered follow-up actions
- the agent needs a structured playbook JSON for the watcher and executor
- a user says things like:
  - "到 81500 把止损放到 82100"
  - "如果这单止损了就反手"
  - "第一目标到就保本"
  - "给这笔单加一个 playbook"
  - "把这句话编译成交易规则"

## Do Not Use This Skill When

- the request is only to fetch market data
- the request is only to place a plain one-off order
- the request needs a long-running watcher to continue an already compiled playbook
- the request is already a fully structured execution payload and no compilation is needed

## Workflow Position

This skill is usually the second step in the custom scalper workflow, after precheck and before execution or watching.

## Before Using This Skill

- For a fresh trade idea, usually run `scalper-precheck` first.
- Use this skill only when the trader is still describing rules in prose and those rules need to be compiled.
- If the request is already a structured payload or a concrete OKX write action, skip this skill and use `scalper-executor`.

## After This Skill

- After successful compilation, route to `scalper-executor` when the next step is to place or modify an order.
- After successful compilation, route to `scalper-position-watch` when the next step is ongoing monitoring.
- If compilation fails or the request is outside the schema, stop and explain what is unsupported.

## Routing Priority

- Prefer this skill after `scalper-precheck` when the trader is describing management logic in prose.
- Prefer this skill before `scalper-executor` when rules still need to be compiled.
- Do not skip directly to executor if the user request still contains phrases like "如果", "到某个位置", "止损了就", or "达到目标后".

## Workflow

1. Extract the exact `instId`, `profile`, side, and any playbook rules from the user request.
2. If the request is missing a clear instrument, side, position reference, or trigger value, stop and ask for clarification.
3. Only compile requests that fit the MVP schema in `references/playbook-schema.md`.
4. Write the candidate playbook JSON to a temporary file under `.scalper-runtime/playbooks/`.
5. Run `scripts/compile_playbook.py --input-file <path>`.
6. If compilation succeeds, persist it using `scripts/save_playbook.py --input-file <path>`.
7. Return the compiled playbook summary to the user and hand off to executor or watcher as needed.
8. If the playbook includes unsupported events or actions, stop and explain that the current MVP does not support that strategy shape yet.

## Ambiguity And Unsupported Requests

- If the request is ambiguous, ask a concise clarification question.
- If the request exceeds the MVP schema, state that the current version does not support that behavior yet.
- Do not invent new event names or action names outside the schema.
- Never claim that a playbook was created if validation failed.

## Supported v2 Alpha Concepts

- Events: `price_gte`, `price_lte`, `position_stopped`, `entry_filled`, `tp_hit`, `sl_hit`, `time_elapsed`, `sequence`
- Actions: `move_stop`, `move_stop_to_break_even`, `close_partial`, `close_all`, `open_opposite_same_notional`, `add_same_side_position`, `notify_only`
- Rule controls: `id`, `enabled`, `once`

## User Request Examples

- "82150 的空单，到 81500 把止损挪到 82100"
- "如果这单止损了，就开等价值反向单"
- "给这笔 BTC perp 空单写一个管理剧本"
- "帮我把这句话编译成 scalper playbook"

## Script Entrypoints

Compile:

```bash
python3 skills/scalper-playbook/scripts/compile_playbook.py \
  --input-file .scalper-runtime/playbooks/example-playbook-input.json
```

Save:

```bash
python3 skills/scalper-playbook/scripts/save_playbook.py \
  --input-file .scalper-runtime/playbooks/example-playbook-compiled.json
```

Full demo flow:

```bash
python3 skills/scalper-playbook/scripts/run_demo_flow.py \
  --profile demo \
  --inst-id BTC-USDT-SWAP \
  --entry-side sell \
  --entry-price 82150 \
  --size-usdt 300 \
  --trigger-price 81500 \
  --new-stop-price 82100 \
  --watch-price 81490 \
  --include-reverse
```

## References

- Playbook schema: `references/playbook-schema.md`
- Runtime layout and logs: `references/runtime-layout.md`
