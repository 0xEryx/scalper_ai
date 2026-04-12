[中文](./README.md) | [English](./README.en.md)

# Scalper Skills v2 Alpha

这个目录是一套基于 OKX Agent Trade Kit 构建的当前版本 scalper agent skills 组合。

这套项目的目标，是补一层更贴近真实交易员工作流的能力，帮助 agent：

- 自动完成开仓前的 scalper 风险检查
- 将自然语言的交易管理思路编译成结构化 playbook
- 通过 OKX CLI 执行当前已支持的订单管理动作
- 在 playbook 存在时继续做轻量级的后续跟踪

当前版本属于 v2 alpha，更适合本地测试、模拟盘验证和 playbook 迭代，还不是一个可直接用于真实资金的生产级交易系统。

## 为什么这套项目适合放在 OKX AI 生态里

我们把这套 skills 看成是对 OKX AI 生态的补充，而不是与之竞争。

OKX Agent Trade Kit 与官方 OKX skills 已经解决了很多最重要的底层问题：

- 市场数据访问
- 账户数据访问
- 下单与改单能力
- 面向 agent 的标准化工具接口

正是因为这些基础能力已经存在，我们才有可能在其之上继续构建更面向交易员的 AI 工作流。

这个项目想贡献的，正是这样一层：

- 一个偏 scalper 的 precheck 层
- 一个把交易员自然语言管理意图转成结构化规则的 playbook 层
- 一个把 playbook 动作映射成确定性 OKX 命令的 execution 层
- 一个做轻量后续触发的 watcher 层

换句话说：

- OKX AI 工具链提供的是执行底座
- 这个项目尝试补的是更接近交易员真实思考方式的 workflow layer

我们认为这种分工对 OKX AI 生态是有价值的，因为它推动的不只是“AI 会下单”，而是“AI 能以更有纪律的方式支持真实交易流程”。

## OKX Agent Trade Kit 已经做得很好的部分

这个项目之所以成立，是因为 OKX Agent Trade Kit 本身已经做了很多重活。

官方这套基础设施已经非常适合：

- 向 agent 暴露市场、账户和交易能力
- 提供稳定的 CLI / MCP 式执行接口
- 降低策略开发者自己重写交易所接入层的成本
- 让市场查询、仓位查询、订单执行更容易被上层 workflow 复用

如果没有这层基础，这个项目会难做很多。

## 为什么还需要一层 Playbook 抽象

同时，很多交易员的真实工作流仍然不只是单次工具调用。

对于短线、scalper、半主观半系统化的交易方式，交易员常常会这样表达：

- “价格到这个位置就把止损上移”
- “如果这一单止损了，就按等价值反向开仓”
- “第一目标到之后，再切换管理逻辑”
- “如果 A 先发生，再开始观察 B”

这些不只是单个订单动作，而是带有状态、条件和阶段的管理计划。

这正是 playbook 层的意义所在。

`scalper-playbook` 的角色，就是处在：

- 交易员自然语言意图
- 与底层 OKX 执行工具

之间的那一层中间抽象。

所以更公平、也更适合官方生态的说法是：

- OKX Agent Trade Kit 非常擅长执行原子能力
- 更贴近交易员风格的、带状态的管理逻辑，仍然适合通过 playbook abstraction 来补齐

我们认为，这正是 AI 交易 agent 从“能演示”走向“对活跃交易员真正有帮助”时非常值得继续探索的一层。

## 包含哪些内容

当前这套 bundle 包含四个自定义 agent skills：

- `scalper-precheck`
- `scalper-playbook`
- `scalper-executor`
- `scalper-position-watch`

它们都在当前目录下：

- `./scalper-precheck`
- `./scalper-playbook`
- `./scalper-executor`
- `./scalper-position-watch`

## 整体设计

### 1. Precheck

`scalper-precheck` 是第一层。

它会使用 OKX 市场数据生成结构化的开仓前报告：

- spread
- orderbook depth
- 5m / 15m 波动
- funding
- open interest
- open orders
- existing positions
- 最终总结为 `pass`、`caution` 或 `reject`

### 2. Playbook

`scalper-playbook` 会把交易员的自然语言管理逻辑，编译成一个小型结构化规则集。

当前 v2 alpha schema 支持：

- 事件：
  - `price_gte`
  - `price_lte`
  - `position_stopped`
  - `entry_filled`
  - `tp_hit`
  - `sl_hit`
  - `time_elapsed`
  - `sequence`
- 动作：
  - `move_stop`
  - `move_stop_to_break_even`
  - `close_partial`
  - `close_all`
  - `open_opposite_same_notional`
  - `add_same_side_position`
  - `notify_only`
- 规则控制字段：
  - `id`
  - `enabled`
  - `once`

这意味着当前版本现在能支持的是：

- 价格触发型管理
- 止损后触发型管理
- 轻量 lifecycle 事件管理
- 第一类两段式 sequence 规则
  - 例如“先到 A，再反弹到 B，然后同向加仓”

但还不支持更复杂的多阶段状态机，例如：

- “TP1 到了以后，如果价格回到 X，再执行 Y”
- “第一次减仓后，如果 5m RSI 上穿 72，再执行下一步”
- “止损后，等待 reclaim，再重新入场”

我们有时会把这些尚未支持的形态称为：

- 有状态的多阶段 playbook
- 阶梯式管理逻辑
- 链式策略组合

而这些，恰恰是我们认为未来 playbook 层最值得继续扩展的方向。

### 3. Executor

`scalper-executor` 会把当前已支持的动作映射为 OKX CLI 命令。

目前已经做过真实验证或脚本验证的动作包括：

- market / limit 入场
- 通过 OKX conditional algo order 移动止损
- 移动到保本止损
- 全部平仓
- 部分平仓
- 按等价值反向开仓
- 按 `notional_usdt`、`size_pct` 或 `margin_pct * leverage` 同向加仓
- 仅通知类动作 `notify_only`

### 4. Position Watch

`scalper-position-watch` 是 watcher 层。

当前版本已经升级成 script-first watcher 架构：

- `run_watch_cycle.py`
  - 执行一轮确定性的 watcher cycle
  - 读取 playbook
  - 拉实时 ticker 或读取外部 snapshot
  - 在脚本里完成规则判断，不需要每轮都让 LLM 参与
  - 直接 dispatch 已支持的 action
- `run_watch_service.py`
  - 把单轮 cycle 包装成后台服务入口
  - 只有真的触发时才输出结构化 watcher event
  - 把事件写到 `.scalper-runtime/events/watch-events.jsonl`
- `notify_watch_event.py`
  - 把 watcher 触发事件桥接回本地 agent 的消息层
  - 让 LLM 只在“有值得告诉用户的事情发生时”再参与

也就是说 watcher 路径现在更接近：

- scheduler / cron / service
- 脚本 watcher 逻辑
- action dispatch
- 只有触发时再走本地 message bridge

而不是每一轮轮询都依赖 LLM。

它依然应该被理解为 alpha 级 workflow 组件，但已经明显强于早期那种“辅助性质的 watcher 脚本”版本。

## 依赖项

本地环境至少需要这些：

- 一个兼容的本地 agent runtime
- Python 3
- OKX Trade CLI
- 正确配置好的 `~/.okx/config.toml`
- 本地 runtime workspace：`~/.openclaw/workspace`

至少应当先保证下面两条能跑通：

```bash
okx --version
okx --profile demo account balance
```

如果这两条都不通，应该先修好 OKX 本地环境，再测试这套 skills。

## 如何安装到本地 Workspace

在当前目录下执行：

```bash
bash install-to-workspace.sh
```

这个脚本会把四个 custom skills 安装到：

```text
~/.openclaw/workspace/skills
```

这也是当前本地 agent 环境真正会看到的 workspace skills 目录。

你可以用下面这条命令确认是否已加载：

```bash
node openclaw.mjs skills list | rg "scalper-(precheck|playbook|executor|position-watch)"
```

## 推荐的本地测试顺序

### 第一步：运行 Precheck

```bash
python3 scalper-precheck/scripts/run_precheck.py \
  --inst-id SOL-USDT-SWAP \
  --profile demo
```

你应该会拿到这样的 JSON 结构：

- `status`
- `snapshot`
- `checks`
- `warnings`

### 第二步：编译一个简单 Playbook

使用示例输入：

```bash
python3 scalper-playbook/scripts/compile_playbook.py \
  --input-file examples/sol-simple-playbook-input.json \
  > /tmp/sol-simple-playbook-compiled.json
```

然后保存：

```bash
python3 scalper-playbook/scripts/save_playbook.py \
  --input-file /tmp/sol-simple-playbook-compiled.json
```

### 第三步：运行一轮 Script-First Watch Cycle

如果你已经有保存好的 playbook，并且想测试“不经过 LLM”的 watcher cycle，可以运行：

```bash
python3 scalper-position-watch/scripts/run_watch_cycle.py \
  --playbook-id pb_test_script_watch \
  --snapshot-file /Users/wiggins/.openclaw/workspace/tmp/pb_trigger_none.json
```

cycle 结果会写到：

```text
~/.openclaw/workspace/.scalper-runtime/logs/watch-cycles.jsonl
```

### 第四步：运行 Watch Service 与事件桥接

如果你要测试 service wrapper 和通知桥：

```bash
python3 scalper-position-watch/scripts/run_watch_service.py \
  --playbook-id pb_test_script_watch \
  --snapshot-file /Users/wiggins/.openclaw/workspace/tmp/pb_trigger_step2.json \
  --notify-command "python3 scalper-position-watch/scripts/notify_watch_event.py"
```

触发后的结构化事件会写到：

```text
~/.openclaw/workspace/.scalper-runtime/events/watch-events.jsonl
```

如果你想一键走完整个本地流程，也可以运行：

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

### 第二步补充：编译一个 v2 Sequence Playbook

当前目录还包含一个最小 v2 sequence 示例：

```bash
python3 scalper-playbook/scripts/compile_playbook.py \
  --input-file examples/sequence-add-short-input.json
```

这个示例表达的是：

- 先到一个价格
- 再等一次反弹
- 然后同向加仓

### 第三步：下一个小仓位的 Demo 单

先 dry-run：

```bash
printf '%s\n' '{"profile":"demo","instId":"SOL-USDT-SWAP","entry":{"side":"buy","order_type":"market","size_usdt":90},"execute":false}' \
| python3 scalper-executor/scripts/place_entry_order.py
```

再真实执行：

```bash
printf '%s\n' '{"profile":"demo","instId":"SOL-USDT-SWAP","entry":{"side":"buy","order_type":"market","size_usdt":90},"execute":true}' \
| python3 scalper-executor/scripts/place_entry_order.py
```

需要注意：

- notional 必须足够买到至少 1 张合约
- 某些标的用 `20 USDT` 是不够的
- 我们自己的测试里，`SOL-USDT-SWAP` 大概需要 `84 USDT` 左右才能满足最小 1 张合约

### 第四步：移动止损或平仓

移动止损：

```bash
printf '%s\n' '{"profile":"demo","instId":"SOL-USDT-SWAP","action":"move_stop","params":{"stop_price":84.05},"execute":true}' \
| python3 scalper-executor/scripts/dispatch_action.py
```

全部平仓：

```bash
printf '%s\n' '{"profile":"demo","instId":"SOL-USDT-SWAP","action":"close_all","execute":true}' \
| python3 scalper-executor/scripts/dispatch_action.py
```

## 日志与运行时产物

MVP 会把运行时文件写到：

```text
.scalper-runtime/
```

重要位置包括：

- playbooks：
  - `.scalper-runtime/playbooks/`
- action log：
  - `.scalper-runtime/logs/actions.jsonl`
- order log：
  - `.scalper-runtime/logs/orders.jsonl`

这些都是本地运行态文件，默认不应该提交到 git。

## 一个当前支持的 v2 Alpha 策略示例

当前 schema 可以支持这样的策略：

- 开一笔多单
- 如果价格达到某个目标，把止损移动到新的固定位置
- 如果仓位最终被止损，则开一个等价值的反向单

因为它只依赖：

- `price_gte`
- `position_stopped`
- `move_stop`
- `open_opposite_same_notional`

另外，现在还支持一种 v2 alpha 形态：

- 先到 2122
- 再反弹到 2144
- 然后按 3% 仓位、20x 同向加空

因为它依赖的是：

- `sequence`
- `add_same_side_position`
- `margin_pct`
- `leverage`

## 一个当前还未完全支持的策略示例

当前 schema 还不支持类似这样的逻辑：

- “如果 TP1 先到了，然后价格回踩到 81820，减半仓；如果之后 funding 再翻转，就反手做空”

因为这种逻辑需要：

- 状态标记
- 条件链
- 多阶段事件记忆
- 更强的 watcher 表达能力

这些属于后续 schema 版本应该继续扩展的方向，而不是当前 v2 alpha 已经完全解决的部分。

## 为什么我们希望更多交易员来贡献 Playbook

我们不希望这个项目只是一个昙花一现、只演示一种策略形状的 demo。

playbook 层的长期价值，来自“多样性”：

- 不同的进场后管理习惯
- 不同的止损移动哲学
- 不同的反手逻辑
- 不同的 scalper checklist
- 不同的市场状态过滤规则

所以这个项目非常需要交易员的反馈与贡献。

如果你是交易员、策略研究者、或者正在使用 OKX AI 工具链的 builder，最有价值的贡献不一定只是代码，也包括你如何自然地描述风险控制与仓位管理。

例如这些都非常有帮助：

- “价格到 X 的时候，我通常会做 Y”
- “第一次止盈后，我下一步一般会做 Z”
- “这是我对 reversal setup 的自然表达方式”
- “这是我开 scalp 之前的固定检查清单”

这些真实 workflow 会帮助 playbook variety 持续被 enrich，也会让项目更像一个能长期成长的体系，而不是一次性的概念展示。

我们的目标是让这套 bundle 从：

- 一个更早期的小型 schema

逐步发展为：

- 一个建立在 OKX AI 生态上的、更丰富的 trader-native playbook library

## 当前 v2 Alpha 的重点方向

当前正在继续推进的方向包括：

- 更丰富的 playbook schema
- 更强的 sequence / 状态规则支持
- lifecycle 事件驱动的 watcher
- 更完整的 executor 动作覆盖
- 面向交易员的清晰回报，同时保留稳定的结构化 JSON 契约

## Discord / 自然语言使用现状

这套 custom skills 已经能通过当前本地 agent 环境使用，但目前的路由仍然属于 alpha 阶段。

当前现实是：

- `precheck` 已经能通过自然语言较稳定地被命中
- `playbook` 已经能对复杂规则型请求做出合理响应
- 但直接下单请求仍有可能绕过这套 custom workflow，命中更直接的执行路径

所以在当前阶段，更推荐用半结构化说法，例如：

- `先做个 precheck。SOL-USDT-SWAP，这单能不能做？`
- `给这笔单编译一个 playbook：82150 的空单，到 81500 把止损挪到 82100，如果这单止损了，就开等价值反向单。`

这会比完全自由发挥的交易员聊天式输入更加稳定。

## 安全提醒

- 优先使用 `demo`
- 不要把当前 v2 alpha 当成生产级系统
- 不要默认认为复杂阶梯式策略已经支持，除非 schema 明确支持
- 测试前先确认当前标的是否已有仓位
- 在验证执行流时始终从小仓位开始

## 建议先看哪些文件

- 总 README：
  - `./README.md`
- 安装脚本：
  - `./install-to-workspace.sh`
- 示例输入：
  - `./examples/sol-simple-playbook-input.json`
  - `./examples/sequence-add-short-input.json`
- precheck skill：
  - `./scalper-precheck/SKILL.md`
- playbook schema：
  - `./scalper-playbook/references/playbook-schema.md`
