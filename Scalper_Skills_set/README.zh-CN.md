[English](./README.md) | [中文](./README.zh-CN.md)

# OpenClaw Scalper Skills MVP

这个目录是一套基于 OpenClaw 与 OKX Agent Trade Kit 构建的自定义 scalper skills 组合。

这套项目的目标不是替代 OKX 官方 skills，而是在它们之上补一层更贴近真实交易员工作流的能力，帮助 agent：

- 自动完成开仓前的 scalper 风险检查
- 将自然语言的交易管理思路编译成结构化 playbook
- 通过 OKX CLI 执行当前已支持的订单管理动作
- 在 playbook 存在时继续做轻量级的后续跟踪

当前版本属于 MVP / alpha，更适合本地测试与模拟盘验证，还不是一个可直接用于真实资金的生产级交易系统。

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

当前这套 bundle 包含四个自定义 OpenClaw skills：

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

当前 MVP schema 只支持少量事件与动作：

- 事件：
  - `price_gte`
  - `price_lte`
  - `position_stopped`
- 动作：
  - `move_stop`
  - `close_partial`
  - `close_all`
  - `open_opposite_same_notional`

这意味着当前版本能支持的是：

- 价格触发型管理
- 止损后触发型管理

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

目前已经做过真实验证的动作包括：

- market / limit 入场
- 通过 OKX conditional algo order 移动止损
- 全部平仓
- 部分平仓
- 按等价值反向开仓

### 4. Position Watch

`scalper-position-watch` 是 watcher 层。

当前它仍然是脚本驱动的 watcher，而不是一个长期稳定、完全产品化的后台守护进程。对 MVP 测试来说已经够用，但更适合被理解为 alpha 级 workflow 组件，而不是生产级事件引擎。

## 依赖项

本地环境至少需要这些：

- OpenClaw
- Python 3
- OKX Trade CLI
- 正确配置好的 `~/.okx/config.toml`
- OpenClaw runtime workspace：`~/.openclaw/workspace`

至少应当先保证下面两条能跑通：

```bash
okx --version
okx --profile demo account balance
```

如果这两条都不通，应该先修好 OKX 本地环境，再测试这套 skills。

## 如何安装到本地 OpenClaw Workspace

在当前目录下执行：

```bash
bash install-to-workspace.sh
```

这个脚本会把四个 custom skills 安装到：

```text
~/.openclaw/workspace/skills
```

这也是 OpenClaw 本地运行时真正会看到的 workspace skills 目录。

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

如果你想一键走完整个本地 MVP 流程，也可以运行：

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

## 一个当前支持的 MVP 策略示例

当前 schema 可以支持这样的策略：

- 开一笔多单
- 如果价格达到某个目标，把止损移动到新的固定位置
- 如果仓位最终被止损，则开一个等价值的反向单

因为它只依赖：

- `price_gte`
- `position_stopped`
- `move_stop`
- `open_opposite_same_notional`

## 一个当前还不支持的策略示例

当前 schema 还不支持类似这样的逻辑：

- “如果 TP1 先到了，然后价格回踩到 81820，减半仓；如果之后 funding 再翻转，就反手做空”

因为这种逻辑需要：

- 状态标记
- 条件链
- 多阶段事件记忆
- 更强的 watcher 表达能力

这些属于后续 schema 版本应该扩展的方向，而不是当前 MVP 已经解决的部分。

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

- 一个小型 MVP schema

逐步发展为：

- 一个建立在 OKX AI 生态上的、更丰富的 trader-native playbook library

## Discord / 自然语言使用现状

这套 custom skills 已经能通过 OpenClaw 使用，但目前的路由仍然属于 alpha 阶段。

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
- 不要把当前版本当成生产级系统
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
- precheck skill：
  - `./scalper-precheck/SKILL.md`
- playbook schema：
  - `./scalper-playbook/references/playbook-schema.md`

## 当前状态

这套 bundle 已经完成过一次真实的 demo-trading MVP 闭环验证：

- 用真实 OKX 市场数据跑 precheck
- 成功编译并保存 playbook
- 成功下了一笔真实 demo 市价单
- 成功挂上真实 conditional stop
- 最后成功平仓

这意味着它已经具备了作为 alpha / MVP skill collection 被公开发布、供本地使用与模拟盘测试的基础。

## 建议如何定位这个项目

如果你要对外展示或参与评选，我认为目前最诚实、也最有说服力的定位是：

- 一个面向 OpenClaw + OKX Agent Trade Kit 的 alpha custom skill bundle
- 聚焦于 trader-native 的 precheck 与 playbook workflow
- 用来探索 OKX AI tooling 如何进一步支持更丰富的 scalper 管理逻辑

这比直接把它称为“完整 autonomous trading system”更强，因为它更准确地区分了：

- 今天已经真实成立的部分
- 和下一阶段还需要继续扩展的部分
