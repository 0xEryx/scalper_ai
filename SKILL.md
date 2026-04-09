---
name: scalper-agent
description: A top-level router skill for a scalper-oriented OKX trading workflow built on OpenClaw and OKX Agent Trade Kit. Use this skill when a trader is working with the overall system and the agent needs to decide whether to run precheck, compile a playbook, execute a supported action, or continue watching an existing playbook.
version: "1.0.0"
user-invocable: true
metadata:
  {
    "openclaw":
      {
        "emoji": "🧭",
      },
  }
---

# Scalper Agent

This is the top-level router skill for the Scalper Skills Set.

Use this skill when the user is interacting with the overall scalper trading system and the agent should decide which specialized sub-skill to use.

This skill does not replace the four sub-skills. Its job is to:

- explain the overall capability of the bundle
- identify the user's intent
- route the request to the correct sub-skill
- keep the workflow in the right order

## Overall Capability

This bundle is designed to support a scalper-style OKX trading workflow on top of OpenClaw and OKX Agent Trade Kit.

At a high level, the system can:

- run a pre-trade checklist before entry
- compile trader-style management logic into a structured playbook
- execute supported OKX order actions deterministically
- continue watching a compiled playbook and trigger supported follow-up actions

The system is strongest when the request falls into one of these shapes:

- "先帮我看这单能不能做"
- "把这句交易管理逻辑编译成 playbook"
- "执行这个已确定的订单动作"
- "继续盯这笔单"

## Use This Skill When

- the user is speaking to the scalper system as a whole
- the correct sub-skill is not yet obvious
- the request could belong to more than one scalper sub-skill
- the agent should preserve workflow order instead of jumping straight to execution
- the user says things like:
  - "帮我处理这笔 scalper 单"
  - "看看这笔单该怎么走"
  - "给我做这笔单的完整流程"
  - "这个策略应该怎么交给 agent"

## Do Not Use This Skill When

- the user already explicitly requested one sub-skill and that request is unambiguous
- the agent is already inside a downstream sub-skill and only needs to complete a single known action
- the request is unrelated to this scalper bundle

## Routing Guide

### Route to `scalper-precheck`

Use `scalper-precheck` when:

- the trader is still evaluating whether to take a trade
- the user wants a quick market-quality and risk summary
- the system should report spread, depth, volatility, funding, OI, open orders, or current exposure

Typical requests:

- "先做个 precheck"
- "这单能不能做"
- "开仓前帮我检查一下"
- "先看看 spread、depth、funding、OI"

### Route to `scalper-playbook`

Use `scalper-playbook` when:

- the trader is describing management rules in prose
- the request includes conditions or follow-up logic
- the request contains phrases like:
  - "如果...就..."
  - "到某个位置就..."
  - "止损后..."
  - "达到目标后..."

Typical requests:

- "到 81500 把止损挪到 82100"
- "如果这单止损了，就开等价值反向单"
- "把这句话编译成 playbook"
- "给这笔单加一个管理规则"

### Route to `scalper-executor`

Use `scalper-executor` when:

- the request is already a concrete execution action
- no prose compilation is needed
- the trader wants one-off entry, stop movement, partial close, full close, or reverse action

Typical requests:

- "执行这笔 demo 市价多单"
- "把这笔仓位全部平掉"
- "把止损移到 82100"
- "按等价值开反向单"

For fresh trade ideas, do not route straight here before considering `scalper-precheck`.

### Route to `scalper-position-watch`

Use `scalper-position-watch` when:

- a compiled playbook already exists
- the next step is ongoing monitoring
- the agent should keep watching for supported rule hits

Typical requests:

- "继续盯这笔单"
- "按这个 playbook 继续监控"
- "如果命中条件就执行下一步"

Do not route here unless there is already a compiled playbook or clearly structured watcher context.

## Recommended Workflow Order

For most fresh trade ideas, prefer this order:

1. `scalper-precheck`
2. `scalper-playbook`
3. `scalper-executor`
4. `scalper-position-watch`

Not every request needs all four steps, but the agent should respect the logic of the workflow instead of skipping directly to execution when the user is still describing a setup.

## Local Vs External Data Policy

- Prefer local scalper skills and OKX-native tooling first for requests about precheck, playbook compilation, execution, positions, open orders, or market data that OKX already provides.
- Do not default to `web_search` for normal scalper workflow requests if the task can be completed with local skills plus OKX CLI / MCP-backed data.
- Use external search only when the local stack is clearly insufficient, such as:
  - project news
  - token narrative or ecosystem context
  - listing / delisting information
  - unlock schedules
  - cross-exchange context
  - other external information that OKX-native tooling does not provide
- If both local execution context and external context are needed, prefer a combined workflow:
  - first use the local scalper / OKX skills for the trading side
  - then add external context only where needed
- If the user explicitly asks to search the web, it is acceptable to use `web_search`.

## Ambiguity And Unsupported Requests

- If the request is ambiguous, ask a concise clarification question.
- If the request exceeds the current MVP schema, say that the current version of the scalper bundle does not support that strategy shape yet.
- Do not invent unsupported events or actions.
- Do not silently route to execution when the user is still describing conditional logic.

## Sub-Skills In This Bundle

- `./scalper-precheck/SKILL.md`
- `./scalper-playbook/SKILL.md`
- `./scalper-executor/SKILL.md`
- `./scalper-position-watch/SKILL.md`

## User Request Examples

- "帮我处理这笔 scalper 单，先看看风险"
- "把这笔交易思路变成 agent 能执行的规则"
- "这笔单现在应该先 precheck 还是直接执行"
- "继续按这个 playbook 盯盘"
