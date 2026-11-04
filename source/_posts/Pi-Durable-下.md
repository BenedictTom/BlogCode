---
title: Pi Durable（下）：谁在跑，谁在看
date: 2026-11-05 03:20:00
categories:
  - Pi
tags:
  - Pi
  - pi-durable
  - Durable
  - Extension
cover: /images/Pi-Durable-下/cover.png
description: 讲 durable 的另一半：任务所有权与后台任务的边界、文档的同事务 fork、扩展的五类内容与钩子链语义、多客户端 watch 视图，以及为什么这里能"边聊边压缩"。
---

上半篇回答"怎么活过崩溃"。但那只是基础设施——真正让 `pi-durable` 像一个服务而不是一个库的，是这一篇的东西：**任务怎么分层、状态怎么共享、多个客户端怎么同时看**。

先说一个必须纠正的预设：我原本以为扩展只有四类内容（工具、段、钩子、任务）。读了 `types.ts:424-432` 才知道是**五类**：

```ts
tools? / sections? / hooks? / wraps? / tasks?
```

多出来的 `wraps` 是"包装已有工具"，跟 `tools` 不是一回事。这类细节就是"读文档不如读类型"的典型例子。

## 1. 任务所有权：两种 parent，两种命运

每个任务都有一个 `ownership`（`spec.md:2090-2091`）：

```ts
type TaskOwnership =
  | { readonly kind: "conversation" }
  | { readonly kind: "task"; readonly taskId: TaskId };
```

要么"我属于这个会话"，要么"我属于那个任务"。看着像只是个字段，实际决定了三件事：**谁的中止会带上我、谁的空闲要等我、级联取消时我在不在链上。**

`spec.md:2247` 说得很清楚：会话拥有的任务，**被排除在会话的中止、空闲判定和级联之外**。

于是"后台任务"其实不是一个新的类型，而是一个**边界**（`README.md:727-757`）：

> A task created with `{ background: true }` is a boundary: work it owns survives the parent's abort and does not keep the parent busy.

两句话两个效果：

- **survives the parent's abort**：父任务被取消，后台任务继续跑
- **does not keep the parent busy**：父任务不等它

这两条恰好是"后台"这个词的两个含义：不被连坐、不被等待。

{% mermaid %}
flowchart TD
  C["Conversation<br/>（一次会话）"] --> T1["GenerationTask<br/>ownership: conversation"]
  C --> T2["ToolTask<br/>ownership: conversation"]
  T1 --> T3["子任务 A<br/>ownership: task"]
  T1 --> B["后台任务 B<br/>background: true"]
  T2 --> T4["子任务 C<br/>ownership: task"]
  B -.不受 T1 中止影响.-> X["独立完成"]
  T3 -.随 T1 级联.-> Y["一起取消"]
{% endmermaid %}

这个设计的价值在长任务里才显出来：主回合要等"生成 + 工具"，但如果用户让你"顺手跑个十分钟的测试"，那件事就该挂在后台——否则一次会话的中止会把十分钟的工作一起杀掉，而一次会话的"空闲"判定会被它卡住十分钟。

## 2. `onYield`：回合边界的唯一钩子

agent 有个经典难题：模型答完了，该不该让它继续？

`onYield` 就是这个位置（`types.ts:1004`）：

```ts
onYield(answer: AssistantMessage, api: HookApi, context: Context): HookResult<{ readonly continue: UserInput }>
```

模型给出最终答案后触发，返回 `continue` 就"再跑一轮"。实现里**第一个返回 continuation 的钩子生效**（`generation.ts:855-883`）。

有个副作用要注意：注释里写着

> The continuation starts the run's turn count over: bounding onYield loops is the extension's job.

**续跑会把回合计数清零。** 如果你的回合上限是 10，模型每轮都用 `onYield` 续一次，那这个上限就永远触发不了。这是故意的——续跑在语义上是"用户又说了句话"，不是"同一个回合的第 11 步"。但代价是：**防死循环的责任落到扩展作者身上**。

这类"把控制权交出去，同时把责任也交出去"的设计，在 agent 框架里很常见，也确实是唯一能支持"自动继续"这类功能的方式。

## 3. 文档：同事务写入，fork 有三种拷法

`defineDoc`（`documents.ts:39`）定义一个文档类型，文档内容由 Chord 追踪。关键性质在 `types.ts:263-299`：

> A returned state replaces the task's state in the same commit

以及 `spec.md:2259-2261`：

> the checkpoint or outcome is atomic with the callback's entries, documents, and child tasks

也就是说：**任务状态的落盘、它写的 entry、它改的文档、它建的子任务，全在同一个 `tx`、同一次 commit 里。** 这是"恢复"能可靠的前提——不存在"状态更新了但文档没更新"这种半残。

fork 更有意思（`spec.md:1767-1786`），有三种策略：

| 策略 | 拷什么 |
| --- | --- |
| `"asOf"` | 父在 fork 点 `E` 所属那次 commit 的值 |
| `"current"` | fork 提交那一刻父的当前值 |
| `"initial"` | 不拷贝，用初始值 |

再加一条硬规则：`Task documents and tasks are never copied.` —— 任务和任务文档永远不跟着复制。

为什么 `asOf` 要精确到"fork 点所属的 commit"，而不是"fork 那一刻的当前值"？因为**分叉必须基于一个确定的历史点**。如果拿"当前值"，那 fork 出来的两个分支可能看到不同的父状态，取决于谁的提交先到——这种不确定性会让"同样输入同样输出"彻底失效。

## 4. 五类扩展与钩子链语义

扩展对象长这样（`types.ts:424-432`）：`tools` / `sections` / `hooks` / `wraps` / `tasks`。前两个是"往模型看的东西里加内容"（工具声明、system prompt 段），后三个是"往运行时里加行为"。

钩子的语义差异值得单列一张表（`spec.md:3322-3345`，代码印证在 `tool.ts:152-170`）：

| 钩子 | 链的语义 | 谁说了算 |
| --- | --- | --- |
| `beforeTool` | 参数替换链 | **首个 block 生效**（后面不跑） |
| `afterTool` | 结果替换链 | 全链传下去，最后一个的结果生效 |
| `afterTools` / `afterRun` / `afterResponse` | 观察 | **全跑**，返回值忽略 |
| `onYield` | 续跑请求 | **首个 continuation 生效** |

一句话：**改东西的钩子是链，看东西的钩子是全跑。**

`beforeTool` 里"首个 block 生效"这个语义很关键——它意味着权限钩子应该注册在前面。如果注册在后面，前面那个没 block 的钩子已经把参数改了。这是顺序敏感的设计，必须写文档里，光看代码看不出来。

还有一条：`Hooks use task memos for durable first-writer-wins decisions.` 钩子的决策用"任务级备忘（memo）"来保证**首次写入者胜出**。这是为了恢复：如果一次钩子决策已经做过（记为 memo），恢复后不会重新做一遍——否则同一个"是否批准"可能得到不同答案。

## 5. 多客户端：`watch()` 给你一份视图，不是事件流

一个会话被多个客户端看（Web、CLI、手机），要怎么同步？

`README.md:477-497` 的答案是 `watch()`：返回**会话结构视图**，内容是"attach 时的值 + 之后每个触及它的 commit（带 Chord ops）"。

注意这不是"事件流"，而是"**结构 + 增量操作**"。区别在于：事件流要求客户端自己重放和纠错；结构 + ops 要求客户端把 ops 应用到当前结构上，**错了可以重新 attach 拿全量**。

流式内容放在一个叫 `pi.live` 的文档里：partial 响应、retry 状态、deferred 标记、工具输出、压缩记录、`runFailure`。

窗口大小有个明确策略：默认 50 条，超过 100 就一次性 splice 回 50。也就是**一次删一半**，而不是每次删一条。这是很典型的"摊还"思路——避免每来一条就触发一次数组搬移。

顺便纠正一个我最初的误记：**没有 `viewState` 这个 API**（全仓无此标识符）。对应的是 `watch()` / `observeConversation()` / `watchDoc()` / `watchTaskGraph()` 这几个。

{% mermaid %}
sequenceDiagram
  participant C1 as 客户端 A
  participant S as Session
  participant C2 as 客户端 B
  C1->>S: watch(conversationId)
  S-->>C1: 当前结构（全量）
  C2->>S: watch(conversationId)
  S-->>C2: 当前结构（全量）
  S->>S: 提交一条 entry
  S-->>C1: commit + Chord ops
  S-->>C2: commit + Chord ops
  Note over C1,C2: 落后太多或断线<br/>重新 attach 拿全量即可
{% endmermaid %}

## 6. 后台压缩：为什么这里能"边聊边压缩"

`pi` 的压缩是阻塞的：超阈值，先把摘要做出来，再做下一次请求。用户看着等待。

`pi-durable` 有两条线（`src/harness/agent.ts:30,32`）：`reserveTokens: 16384`、`backgroundTokens: 32768`。计算在 `generation.ts:464-467`：

```ts
const blocking = contextWindow - policy.reserveTokens;
const background = blocking - policy.backgroundTokens;
```

于是有三个区间：

- `< background`：正常聊
- `≥ background`：**开始后台压缩，对话继续**
- `≥ blocking`：压缩还没做完就阻塞等待

`README.md:606-635` 那句话就是这里的注解：`The conversation keeps working while the summary is made.`

{% mermaid %}
flowchart LR
  A["contextWindow"] --> B["blocking<br/>= 窗口 − 16K"]
  B --> C["background<br/>= blocking − 32K"]
  C --> D["正常对话区"]
  C -.超过.-> E["后台压缩<br/>对话不中断"]
  B -.超过.-> F["阻塞等待摘要"]
{% endmermaid %}

为什么 `pi` 不能这么做？因为它在终端里——**没有地方放"压缩期间的新消息"**。durable 能这么做，是因为它有提交线：压缩任务和对话任务是两条独立的任务记录，各自提交，互不阻塞。

这就是"服务形态"带来的自由度：**同一套 compaction 逻辑，只因为有了持久化的任务模型，就能从"停顿"变成"并行"**。

## 7. registry：热替换，边界交接

`registry.ts:9` 是内置任务清单：

```ts
const BUILTIN_TASKS = [GenerationTask, ToolTask, CompactionTask];
```

`install`（`registry.ts:70-80`）按 `findIndex(name)` 同名**就地替换**。

`spec.md:4326-4360` 描述了它的语义：

> The host installs the new extension object under the installed name, which replaces the old one in place in one publication. The Harness keeps running; no close or reopen is required.

"in one publication"是重点——替换是一次原子发布，不是"卸载旧的、装载新的"两步。于是不存在"中间那一瞬间既没有旧扩展也没有新扩展"。

代价是：**运行中的调用不会立刻换代码**，而是在**下一个相位边界**换新。这一点很好理解：如果在一个相位中途换了扩展，那么这个相位前半段用的是旧逻辑、后半段用新逻辑，checkpoint 就说不清是哪个版本写的了。

可跑的样例在 `test/examples/09-registry-reload.ts`（热替换）和 `12-recovery.ts`（恢复 + memo 防重复副作用）。

## 8. 存储：五种实现，三种语义

我原本以为只有三种后端。实际 README 列了五种（`README.md:850-858`）：Memory、IndexedDB、SQLite、JSONL、Cloudflare DO。

但 `spec.md` 第 11 节只规范了三种——Memory、SQLite、JSONL——称之为"语义后端"。另外 SQLite 有 Cloudflare 变体，而 `store` 是"durable 的 Storage 建在 Chord 的 store 上"（`src/storage/store/storage.ts:1-3` 的注释），不是第四种语义。

这个区分有用：**能跑的实现可以很多，需要保证语义一致的只有少数几个。** 一份 spec 里写清楚"哪些是语义等价的"，读者才不会以为五种后端行为各不相同。

写入粒度也有个细节：SQLite 里 `One SQL transaction is one storage call`——一个事务就是一次存储调用。这跟前面讲的组提交是同一件事的两面。

## 9. 小结

下半篇的六个答案：

1. **任务所有权决定命运**：会话拥有的任务被排除在中止、空闲、级联之外；`background: true` 是一个"不被连坐、不被等待"的边界。
2. **`onYield` 是回合边界的唯一钩子**，首个 continuation 生效，且续跑清零回合计数——防循环的责任在扩展。
3. **文档与任务状态同事务**，fork 支持 `asOf`/`current`/`initial` 三种拷法，任务永远不复制。
4. **扩展五类**（多一个 `wraps`），钩子里"改东西的链式、看东西的全跑"。
5. **`watch()` 给结构 + 增量 ops**，不是事件流；窗口 50/100 摊还。
6. **后台压缩靠两条阈值线**，之所以能"边聊边压"，是因为有持久化任务模型。

两篇合起来看，durable 的设计逻辑其实很单一：**把每一步都变成一个可提交的对象，然后所有能力都从"对象可以被安全地重放"里长出来**——恢复、多端、热替换、后台压缩，全是同一件事的不同侧面。

---

**相关阅读**

- [Pi Durable（上）：先落盘，再显示](/2026/11/05/Pi-Durable-上/)
- [Pi 的会话树：一条对话为什么不是一条线](/2026/11/05/Pi-会话树/)
- [Pi-Codemode：让模型写一段脚本去调工具](/2026/11/05/Pi-Codemode/)
