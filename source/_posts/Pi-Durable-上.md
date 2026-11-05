---
title: Pi Durable（上）：先落盘，再显示
date: 2026-11-05 02:45:00
categories:
  - Pi
tags:
  - Pi
  - pi-durable
  - Durable
  - Agent
cover: /images/Pi-Durable-上/cover.jpg
description: pi-durable 把"一次模型回合"变成一串可恢复的相位：提交、checkpoint、resume、replay、幂等。这一篇只讲它怎么活过崩溃。
---

前面几篇都是 `pi`——一个人、一个终端、一个进程。进程一挂，对话就没了；进程一卡，用户只能看着。

`pi-durable` 是同一批人给出的另一个答案：**把它变成一个服务**。多客户端、任意运行时、进程随时可以死。

这个包在 README 第 3 行就给自己贴了警告：

> **Experimental.** The API changes without notice between releases.

这句话我原样保留。下面的内容对应 HEAD `395f3e0`（`packages/durable`，v1.5.0），**只用于理解设计，不要照抄 API**。

## 0. 一句话概括

README 第 5 行：

> A durable agent harness. Conversations, model turns, tool calls, and your own state are committed to storage before anything is shown.

"committed before anything is shown"——**先落盘，再显示**。整个包的所有设计都从这一句推出来。

如果只能理解一个区别，就是这个：

| | `pi`（coding-agent） | `pi-durable` |
| --- | --- | --- |
| 真相在哪 | 内存里的 agent state | 存储里已提交的记录 |
| 崩溃后 | 丢这一轮 | 从 checkpoint 续上 |
| 客户端 | 一个终端 | 多个 watcher |
| 会话线 | 就是进程 | 一条可被接管的提交线 |

## 1. 什么算"完成"：一个 commit 三条记录

`spec.md:37-39` 有一条总规则：

> A Session atomically commits immutable entries, full task records, and Chord-tracked documents. Only committed state is observable.

一次提交里同时落三样东西：**不可变 entry**（就是上一篇讲的会话树节点）、**完整的 task 记录**、**文档的变更**。三者要么全进去，要么全不进去。

"Only committed state is observable"是更狠的一句：**没有中间态可被观察**。你不能"看到一个正在写的任务"——要么它已提交，要么它还不可见。

这条规则带来一个反直觉的性质：**UI 上看到的东西，永远是"已经付费"的东西**。这跟大多数人的直觉相反（先显示、后保存），但正是这个顺序让"崩溃恢复"变成可定义的问题——恢复时只需要问"最后一条已提交的记录是什么"，而不是"内存里那半个状态该算到哪一步"。

{% mermaid %}
flowchart TD
  TX["一个 tx / 一次 commit"] --> A["用户消息 entry"]
  TX --> B["GenerationTask 记录"]
  TX --> C["文档变更"]
  TX --> D["子任务创建"]
  A --> OK["全部可见"]
  B --> OK
  C --> OK
  D --> OK
  TX -.中途崩溃.-> X["一条都不可见<br/>重来即可"]
{% endmermaid %}

写单位是 commit，但落盘不是一次 commit 一次 `Storage.commit()`。`spec.md:1837-1845` 描述的是**组提交**：

> a writer off the line sends every commit admitted while no storage call is in flight as one Storage.commit() call ... each with its own seq, and publishes them one by one, in line order

一次存储调用可以带上多个 commit，但**发布顺序严格按线序**。这是典型的"批量写、顺序读"：吞吐靠合并，语义靠顺序。

## 2. 一次提交去哪了

用户按下回车，链路是这样的（`harness.ts:111` → ... → `generation.ts:1183`）：

```
ConversationImpl.submit
  └→ Submissions.submit(conversationId, draft, context)   // submissions.ts:34
       └→ 在同一个 commit 内：admitSubmission(tx, ...)      // submissions.ts:212
            └→ startRun(tx, conversationId, live, run)     // generation.ts:1164
                 └→ tx.createTask(GenerationTask, {}, { ownership: { kind: "conversation" }, ... })
```

注意每一步都带 `tx`。**提交是把"用户消息 + 任务创建"放进同一个事务**，不是"先存消息，再建任务"。如果进程在中间死掉，要么两者都在，要么两者都不在——不会出现"有消息但没有任务在跑"这种要人去点一下才能修的半残状态。

这也解释了为什么模型请求发生在"Session line 之外"：**发 HTTP 请求不是持久化的一部分**。请求可能失败、可能超时、可能进程死掉，这些都不该影响"用户提交了这句话"这个事实。

## 3. 一次回合的七个相位

任务建好之后，`scheduler` 逐相位推进（`generation.ts:73-135`）：

```
prepare → request → retry → poll → tools → finish → drain
```

每个相位做一件事，做完提交一次 checkpoint。`spec.md:2252-2253` 强调了一件重要的事：

> The phase map is exhaustive and phase-narrowed. A handler may perform several commits around one effect, but each durable checkpoint is a full replacement.

**checkpoint 是全量替换，不是增量补丁。** 相位内部可以有多次 commit（比如写几条 entry），但每次真正落 checkpoint 时，写的是这个相位的完整状态。

为什么不做增量？因为增量就要处理"补丁基于哪个版本"，而版本一多，恢复逻辑会迅速变成分布式系统里最难调的那种 bug。全量替换的代价是每次多写几百字节，换来的是**恢复时只读一个对象就知道该干什么**。对一个实验性、正确性优先的组件，这个取舍是对的。

{% mermaid %}
stateDiagram-v2
  [*] --> prepare
  prepare --> request: 提交 checkpoint
  request --> retry: 请求失败
  retry --> request: 退避后重试
  request --> poll: 长任务/流式
  poll --> tools: 有工具调用
  tools --> request: 有了工具结果
  poll --> finish: 生成完毕
  tools --> finish: 无后续
  finish --> drain: 收尾
  drain --> [*]
  note right of request: 进程在这里死掉<br/>恢复时记为一次失败尝试<br/>不重发同一条请求
{% endmermaid %}

## 4. 恢复：`open` 只对账，`resume` 才干活

这是整个设计里我最喜欢的一处分工。

进程重启后先把会话 `open` 起来。但 `open` **不派发任何东西**——它只做对账（`scheduler.ts:435-471`）：

- 把状态为 `running` 的任务改回 `pending`
- 把它的 `restarts` 计数 +1
- 注释原文：`Dispatches nothing`

真正开始干活要显式调 `resume()`（`scheduler.ts:481-486`）。

这个两步拆分的价值在于：**"知道有什么没做完"和"决定现在开始做"是两件事**。服务启动时你可能想先做健康检查、先接流量、先等其他依赖就绪；如果 `open` 就自动开跑，启动顺序就没法控制了。

更妙的是"把 running 改回 pending 并 +1"这个动作。**崩溃不会被当成异常，而是被当成一次不完整的尝试，然后重新排队。** 于是恢复逻辑里没有"异常路径"，只有"正常路径再来一遍"。

## 5. 那个死掉的模型请求：不重发

上一个相位死在哪里，决定了恢复后做什么。前面几个相位重跑都很安全（它们只是算数据），但 `request` 相位不安全——**一次已经发出去的模型请求，可能已经产生了费用，也可能已经让服务端开始生成**。

Pi 的选择（`generation.ts:265-268`）：

```ts
// The host stopped while this request was in flight: a failed attempt, not a resend
```

**记成一次失败尝试，不重发。** partial 响应存成一条 aborted entry，然后按退避策略重试（`generation.ts:500-512`）。

这个判断很克制：宁可多花一次请求的钱，也不假装"上次那个请求没发生过"。因为一旦重发，同一个 prompt 可能产生两份回复、两份计费、两条消息记录——而"重复"比"缺失"更难修。

连续被切断怎么办？`restarts` 有上限，默认 `DEFAULT_RESTART_LIMIT = 5`（`src/harness/agent.ts:59`），到顶后按策略收束（`scheduler.ts:1935-1946`）。这也是为什么前面要"restarts + 1"——它同时是账本和刹车。

## 6. 工具重放：`replay: "safe"` 的双层校验

工具这一侧的问题更尖锐：一个 `bash` 命令跑到一半进程死了，恢复后要不要重跑？

有些工具重跑无害（读文件、搜代码），有些重跑会出人命（发邮件、转账、`rm -rf`）。Pi 把决定权交给工具声明（`types.ts:352-357`）：

```ts
readonly replay?: "safe" | "unsafe";
// Whether an interrupted execution may rerun on recovery. Default unsafe.
```

**默认 unsafe。** 这个默认值是对的：安全必须显式声明，危险必须是默认。

执行之前先落"意图"（`tool.ts:196`）：

```ts
const intent = { phase: "execute", arguments: final, replay: tool.replay ?? "unsafe" };
```

恢复时做**双层校验**（`tool.ts:208-225`）：既要存储里的 intent 说 safe，也要**当前的工具定义**说 safe，两者都满足才重跑：

```ts
if (replay === "safe" && tool?.replay === "safe") return run(...);
```

否则写一条 `Tool ${call.name} was interrupted and may have partially run`。

为什么校验两次？因为**存储里的意图是过去，工具定义是现在**。如果这期间扩展升级了、`replay` 从 safe 改成了 unsafe，那就得听现在的。反过来，如果存储说 unsafe 而现在说 safe，也不能重跑——因为那次执行用的是旧代码。

内置工具里只有两处声明 safe：`src/codemode/codemode.ts:248` 和 `src/tool-search/tool-search.ts:63`。都是"纯查询"性质。

## 7. 幂等：`requestId` 与一条"没有唯一索引"的线

客户端重试提交时，怎么避免同一句话被记两次？靠 `requestId`。

键的构造（`src/session/keys.ts:61-62`）：

```ts
`req:${conversationId}:${requestId}`
```

去重是**同一个 commit 内"先查后写"**（`submissions.ts:232-241`）：

```ts
if (draft.requestId !== undefined) {
  const existing = await tx.submissionByRequest(conversationId, draft.requestId);
  // 类型不符则抛错
}
```

这里有个容易被忽略的细节：`src/storage/sqlite/migrations.ts:63` 建的是**普通索引，不是 UNIQUE**：

```sql
CREATE INDEX ... submissions_by_request
```

也就是说，exactly-once **不是数据库约束兜的**，而是"单写线串行 + 事务内读后写"兜的。

这在单写线架构里是成立的（同一时刻只有一个 writer，读和写之间不会插进别人），但它和"用唯一索引兜底"是两种不同的可靠性假设：

| | 唯一索引兜底 | 单写线 + 读后写 |
| --- | --- | --- |
| 正确性来源 | 数据库约束 | 架构约束（只有一条写线） |
| 扩展成多写线 | 天然支持 | 需要重新设计 |
| 违反时的表现 | 插入失败，可重试 | 静默重复 |

在实验性阶段选前者，是因为**它的前提被写死在架构里**（写线只有一条）。但如果哪天要做多写线，这就是第一个要改的地方。这类"隐含前提"值得在读代码时专门标出来。

## 8. 为什么这些机制必须一起存在

单看每个机制都不新鲜：checkpoint、幂等键、重放策略、相位状态机，分布式系统里到处都是。pi-durable 有意思的地方在于**它们是互相支撑的**：

- 没有"先落盘再显示"，checkpoint 就没有权威版本
- 没有"checkpoint 全量替换"，恢复时就要处理补丁叠加
- 没有"记成失败尝试不重发"，请求就可能被执行两次
- 没有"默认 unsafe 的双层校验"，恢复可能重放危险操作
- 没有"单写线"，`requestId` 的去重就不成立

抽掉任何一个，剩下的都要加复杂度去补。

## 9. 小结

上半篇只回答一个问题：**它怎么活过崩溃。**

五个答案：

1. **提交是一个原子动作**：entry + task 记录 + 文档变更，要么全有要么全无。
2. **相位化**：`prepare → request → retry → poll → tools → finish → drain`，每相位一个全量 checkpoint。
3. **`open` 只对账，`resume` 才干活**：崩溃被重解释成"一次未完成的尝试"。
4. **在飞的请求不重发**：记 aborted，退避重试，`restarts` 封顶。
5. **工具重放要双层同意**：存储意图 + 当前定义，默认 unsafe。

下一篇讲另一半：谁在跑、谁在看——任务所有权、文档、扩展、多客户端视图，以及为什么这里的压缩可以是"后台"的。

---

**相关阅读**

- [Pi 的会话树：一条对话为什么不是一条线](/2026/11/05/Pi-会话树/)
- [pi-ai：43 个供应商，10 种协议，一套流](/2026/11/05/Pi-ai/)
