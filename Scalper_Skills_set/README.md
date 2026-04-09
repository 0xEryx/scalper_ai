[English](./README.md) | [中文](./README.zh-CN.md)

# OpenClaw Scalper Skills MVP

This directory documents the custom OpenClaw scalper skill bundle built on top of OpenClaw and OKX Agent Trade Kit.

The goal of this bundle is not to replace OKX official skills. The goal is to add a custom trader workflow layer that can:

- run a pre-trade scalper checklist automatically
- compile natural-language trade management instructions into a structured playbook
- execute supported order-management actions through OKX CLI
- watch a playbook and trigger supported follow-up actions

This bundle is currently an MVP / alpha. It is suitable for local testing and demo trading. It is not yet a production-ready real-money trading system.

## Why This Project Fits The OKX AI Ecosystem

We see this bundle as a complement to the OKX AI stack, not a competitor to it.

OKX Agent Trade Kit and the official OKX skills already solve the most important foundation problems:

- market access
- account access
- order placement
- standardized tool surfaces for agent workflows

That foundation is exactly what makes it realistic to build trader-facing AI layers on top.

This project is our attempt to contribute one such layer:

- a scalper-oriented precheck layer
- a playbook layer for translating trader intent into reusable rule structures
- an execution layer for turning supported playbook actions into deterministic OKX commands
- a watcher layer for lightweight follow-through

In other words:

- OKX AI tooling gives us the execution substrate
- this project tries to add a trader workflow layer that feels closer to how discretionary scalpers actually think and manage risk

We believe that kind of specialization is healthy for the OKX AI ecosystem, because it helps move from "AI can place orders" toward "AI can support real trader workflows in a disciplined way."

## What OKX Agent Trade Kit Already Solves Well

This project exists because OKX Agent Trade Kit already does a lot of heavy lifting well.

The official stack is already strong at:

- exposing market and account functionality to agents
- providing a reliable CLI / MCP-style execution surface
- making it easier to query market data, inspect positions, and place or manage orders
- reducing the amount of exchange-plumbing that strategy builders need to write themselves

Without that layer, this project would be much harder to build.

## Where A Playbook Layer Becomes Necessary

At the same time, many trader workflows still need a layer above raw tool access.

For short-term discretionary or semi-systematic scalping, traders often think in terms like:

- "if price reaches this level, move the stop"
- "if the position is stopped, open the opposite side with the same notional"
- "after the first target, change the management logic"
- "if condition A happens first, then start watching for condition B"

Those are not just single orders. They are stateful management plans.

This is where a playbook layer becomes useful.

The role of `scalper-playbook` is to sit between:

- free-form trader intent
- and low-level OKX execution tools

So a fair way to frame this is:

- OKX Agent Trade Kit is excellent at execution primitives
- trader-style, stateful management logic still benefits from a dedicated playbook abstraction

We think this is one of the most important gaps to explore if AI trading agents are going to feel useful to serious active traders rather than only being demo command wrappers.

## What Is Included

The bundle consists of four custom OpenClaw skills:

- `scalper-precheck`
- `scalper-playbook`
- `scalper-executor`
- `scalper-position-watch`

These live in this folder:

- `./scalper-precheck`
- `./scalper-playbook`
- `./scalper-executor`
- `./scalper-position-watch`

## How The Bundle Is Designed

### 1. Precheck

`scalper-precheck` is the first layer.

It uses OKX market data to produce a structured pre-trade report:

- spread
- orderbook depth
- 5m / 15m volatility
- funding
- open interest
- open orders
- existing positions
- a final `pass`, `caution`, or `reject`

### 2. Playbook

`scalper-playbook` turns trader intent into a small structured ruleset.

The current MVP schema supports only a small set of events and actions:

- events:
  - `price_gte`
  - `price_lte`
  - `position_stopped`
- actions:
  - `move_stop`
  - `close_partial`
  - `close_all`
  - `open_opposite_same_notional`

This means the current version supports simple price-triggered and stop-triggered management rules, but not multi-stage state machines such as:

- "after TP1, if price comes back to X, then do Y"
- "if RSI on 5m crosses above 72 after the first reduction"
- "if stop-loss hits, then wait for reclaim before re-entering"

We sometimes refer to those unsupported patterns as:

- stateful multi-stage playbooks
- laddered management logic
- chained strategy combinations

Those patterns are exactly the kind of thing we believe a future playbook layer should make much easier to express on top of OKX AI tooling.

### 3. Executor

`scalper-executor` maps supported actions to OKX CLI commands.

Current tested actions:

- place market / limit entry orders
- move stop via OKX conditional algo order
- close all
- close partial
- open opposite same-notional order

### 4. Position Watch

`scalper-position-watch` is the watcher layer.

Right now it is a script-driven watcher rather than a long-running, battle-hardened daemon. It is enough for MVP testing, but you should treat it as an alpha workflow component rather than a production event engine.

## What This Bundle Depends On

You need all of the following on the local machine:

- OpenClaw
- Python 3
- OKX Trade CLI
- a valid local OKX config in `~/.okx/config.toml`
- OpenClaw runtime workspace at `~/.openclaw/workspace`

You should already be able to run:

```bash
okx --version
okx --profile demo account balance
```

If those fail, fix the OKX environment before testing these skills.

## Install The Skills Into Your Local OpenClaw Workspace

From this folder root, run:

```bash
bash install-to-workspace.sh
```

That script copies the four custom skills into:

```text
~/.openclaw/workspace/skills
```

This is the runtime workspace that OpenClaw actually sees while running locally.

If you want to verify they are visible, run:

```bash
node openclaw.mjs skills list | rg "scalper-(precheck|playbook|executor|position-watch)"
```

## Recommended Local Test Sequence

### Step 1. Run A Precheck

```bash
python3 scalper-precheck/scripts/run_precheck.py \
  --inst-id SOL-USDT-SWAP \
  --profile demo
```

You should get JSON with:

- `status`
- `snapshot`
- `checks`
- `warnings`

### Step 2. Compile A Simple Playbook

Use the example input:

```bash
python3 scalper-playbook/scripts/compile_playbook.py \
  --input-file examples/sol-simple-playbook-input.json \
  > /tmp/sol-simple-playbook-compiled.json
```

Then save it:

```bash
python3 scalper-playbook/scripts/save_playbook.py \
  --input-file /tmp/sol-simple-playbook-compiled.json
```

If you want a one-shot path for local MVP flow testing, run:

```bash
python3 scalper-playbook/scripts/run_demo_flow.py \
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

### Step 3. Place A Small Demo Entry

Dry-run first:

```bash
printf '%s\n' '{"profile":"demo","instId":"SOL-USDT-SWAP","entry":{"side":"buy","order_type":"market","size_usdt":90},"execute":false}' \
| python3 scalper-executor/scripts/place_entry_order.py
```

Then actually execute:

```bash
printf '%s\n' '{"profile":"demo","instId":"SOL-USDT-SWAP","entry":{"side":"buy","order_type":"market","size_usdt":90},"execute":true}' \
| python3 scalper-executor/scripts/place_entry_order.py
```

Important:

- the minimum notional must be large enough to buy at least one contract
- for some instruments, `20 USDT` is too small
- in our own test, `SOL-USDT-SWAP` required about `84 USDT` minimum for 1 contract

### Step 4. Move Stop Or Close The Position

Move stop:

```bash
printf '%s\n' '{"profile":"demo","instId":"SOL-USDT-SWAP","action":"move_stop","params":{"stop_price":84.05},"execute":true}' \
| python3 scalper-executor/scripts/dispatch_action.py
```

Close all:

```bash
printf '%s\n' '{"profile":"demo","instId":"SOL-USDT-SWAP","action":"close_all","execute":true}' \
| python3 scalper-executor/scripts/dispatch_action.py
```

## Logs And Runtime Artifacts

The MVP writes runtime files to:

```text
.scalper-runtime/
```

Important locations:

- playbooks:
  - `.scalper-runtime/playbooks/`
- action log:
  - `.scalper-runtime/logs/actions.jsonl`
- order log:
  - `.scalper-runtime/logs/orders.jsonl`

These are local runtime artifacts and are intentionally ignored by git.

## Example Of A Supported MVP Strategy

This is the type of strategy the current schema can support:

- open a long position
- if price reaches a target, move stop to a new fixed level
- if the position is stopped out, open an opposite same-notional position

This shape is supported because it only needs:

- `price_gte`
- `position_stopped`
- `move_stop`
- `open_opposite_same_notional`

## Example Of A Strategy That Is Not Yet Supported

This is not yet supported by the current schema:

- "if TP1 hits, then if price retests 81820, close half, and if funding flips after that, reverse short"

That requires:

- state markers
- chained conditions
- multi-stage event memory
- more expressive watcher logic

Those are planned for a later schema version, not this MVP.

## Why We Want More Trader-Contributed Playbooks

We do not want this project to be a one-off demo with one frozen strategy shape.

The long-term value of a playbook layer comes from variety:

- different entry-management styles
- different stop movement philosophies
- different reversal logic
- different scalper checklists
- different market-regime filters

So one of the most important things for this project is trader feedback and trader-contributed playbook patterns.

If you are a trader, strategist, or builder working with OKX AI tooling, the most valuable contribution is not only code. It is also examples of how you naturally describe risk and position management.

Examples of helpful contributions:

- "when price reaches X, I usually do Y"
- "after partial take-profit, my next rule is usually Z"
- "here is the exact wording I use for a reversal setup"
- "this is the checklist I run before opening a scalp"

Those kinds of real workflows help enrich playbook variety and make the project more durable over time.

Our goal is for this bundle to evolve from:

- a small MVP schema

into:

- a richer library of reusable trader-native playbook patterns built on top of the OKX AI ecosystem

## Discord / Natural Language Expectations

The custom skills are already usable through OpenClaw, but the routing is still alpha-quality.

Current reality:

- `precheck` can be hit successfully by natural language
- `playbook` can be hit for complex rule-like requests
- direct order requests can still bypass the custom workflow and hit more direct execution paths

Because of that, early usage should prefer semi-structured prompts such as:

- `先做个 precheck。SOL-USDT-SWAP，这单能不能做？`
- `给这笔单编译一个 playbook：82150 的空单，到 81500 把止损挪到 82100，如果这单止损了，就开等价值反向单。`

This is more reliable than completely free-form trader chat at the current stage.

## Safety Notes

- Use `demo` first.
- Do not treat this MVP as production-ready.
- Do not assume complex laddered strategies are supported unless the schema clearly supports them.
- Always inspect open positions before testing on an instrument.
- Always use small size while validating execution flow.

## Files You Probably Want To Open First

- bundle README:
  - `./README.md`
- installer:
  - `./install-to-workspace.sh`
- example input:
  - `./examples/sol-simple-playbook-input.json`
- precheck skill:
  - `./scalper-precheck/SKILL.md`
- playbook schema:
  - `./scalper-playbook/references/playbook-schema.md`

## Current Status

The current bundle has already completed a real demo-trading MVP validation loop:

- precheck run on live OKX market data
- playbook compiled and saved
- real demo market entry placed
- real conditional stop placed
- position closed successfully

That means the bundle is ready to publish as an alpha / MVP skill collection for local use and demo testing.

## Suggested Positioning For This Project

If you are presenting or submitting this project, the most honest positioning is:

- an alpha custom skill bundle for OpenClaw + OKX Agent Trade Kit
- focused on trader-native precheck and playbook workflows
- intended to explore how OKX AI tooling can support richer scalper management logic over time

That framing is stronger than calling it a complete autonomous trading system, and it better reflects what is already real today versus what still belongs in the next iteration.
