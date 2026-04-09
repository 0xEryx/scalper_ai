---
name: scalper-precheck
description: Use this custom OpenClaw skill for automatic pre-trade scalper checks before OKX order planning or execution. Trigger when the user says things like '先做 precheck', '这单能不能做', '开仓前检查一下', '给我做个 scalper 体检', '这个位置能不能上', '先帮我看 spread depth funding OI', or asks to plan, validate, or discuss a short-term OKX trade and the agent should automatically report spread, depth, recent volatility, funding, open interest, open orders, and basic risk warnings before continuing. Prefer this skill before scalper-playbook or scalper-executor whenever the user is still evaluating a trade. Do not use for pure order execution, long-running playbook watching, or raw one-off market data questions that should go straight to okx-cex-market.
version: "1.0.0"
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "🩺",
        "requires": { "bins": ["okx", "python3"] },
      },
  }
---

# OpenClaw Scalper Precheck

This is a custom OpenClaw skill for pre-trade scalper diagnostics. It is not an OKX official skill.

## Use This Skill When

- a user wants to place or plan an OKX trade and pre-trade checks should happen automatically
- a user shares an entry idea and wants quick market-quality feedback
- another custom scalper skill needs a structured market snapshot before execution
- a user says things like:
  - "先做个 precheck"
  - "BTC 这单能不能做"
  - "帮我做一下开仓前检查"
  - "这笔 scalper setup 先体检一下"
  - "下单前先看 spread、depth、funding、OI"

## Do Not Use This Skill When

- the task is only to execute a fully validated order
- the task is only to watch an existing playbook in the background
- the user only wants raw candles, raw RSI, or a plain ticker response
- the user already gave a fully structured follow-up action like `move_stop` and does not need market diagnostics

## Workflow Position

This skill is usually the first step in the custom scalper workflow.

## Before Using This Skill

- Use this skill when a new trade idea is still being evaluated.
- Use this skill before `scalper-playbook` when the trader wants market validation first.
- Use this skill before `scalper-executor` unless the user clearly says precheck was already done or intentionally skipped.

## After This Skill

- If the trader wants to define management rules in prose, route next to `scalper-playbook`.
- If the trader already has a fully structured order and only needs execution, route next to `scalper-executor`.
- If the summary is `reject`, do not continue unless the user explicitly revises or overrides the plan.

## Routing Priority

- Prefer this skill before `scalper-playbook` when the user is still deciding whether a trade is good enough to take.
- Prefer this skill before `scalper-executor` when the request sounds like pre-trade validation rather than immediate execution.
- If the request is only raw market data, prefer `okx-cex-market` instead.

## Workflow

1. Extract the target instrument and profile from the request. Default `profile=demo` if unspecified.
2. If the instrument is missing or ambiguous, stop and ask for the exact `instId`.
3. Run `scripts/run_precheck.py --inst-id <instId> --profile <profile>`.
4. Report the structured precheck summary before any execution skill is used.
5. If the summary status is `reject`, do not continue into execution unless the user explicitly overrides with a revised plan.
6. If the summary status is `pass` or `caution` and the user wants to continue, hand off to `scalper-playbook` or `scalper-executor` as appropriate.

## Ambiguity And Unsupported Requests

- If the request is ambiguous, ask a concise clarification question instead of guessing.
- If the request needs unsupported logic, say that the current scalper MVP does not support it yet.
- Never invent missing execution details.
- Never silently approximate a trading instruction.

## Script Entrypoint

```bash
python3 skills/scalper-precheck/scripts/run_precheck.py \
  --inst-id BTC-USDT-SWAP \
  --profile demo
```

## Output

The script returns a JSON summary with:

- `status`: `pass`, `caution`, or `reject`
- `snapshot`: price, spread, depth, funding, oi, volatility, and current exposure context
- `warnings`: plain-language warnings for the trader

## User Request Examples

- "对 BTC-USDT-SWAP 做一份 scalper precheck"
- "82150 这里想空，先帮我看这单能不能做"
- "不要直接下单，先给我 pass/caution/reject"
- "帮我看下现在做 BTC perp 的 spread、depth、funding 和 OI"

## References

- Precheck report contract: `references/precheck-report.md`
- Shared runtime layout: `../scalper-playbook/references/runtime-layout.md`
