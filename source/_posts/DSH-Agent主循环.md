---
title: DSH Agent 主循环：一条用户消息的完整旅程
date: 2026-10-30 21:55:00
categories:
  - Agent
tags:
  - Agent
  - DeepSeek
  - DSH
  - agent-loop
cover: /images/DSH-Agent主循环/cover.png
---

前两篇分别讲了[上下文怎么装配](/2026/10/30/DSH-上下文装配全解/)和[压缩怎么发生](/2026/10/30/DSH-会话压缩策略详解/)，但那都是"零件"。这篇讲把它们转起来的那台发动机：`dsh-agent-loop`。

结论先放这：DSH 里**只有一个包**真的实现了"调模型、跑工具、再循环"，其余全是插件。理解它，你就理解了"你敲下回车之后，到底发生了什么"。

<p align="center">
  <img src="/images/DSH-Agent主循环/maid.png" width="300" alt="DeepSeek 鲸娘" style="border-radius:12px;">
</p>

<p align="center" style="color:#888;font-size:0.85em;margin-top:-8px;">
  本系列的围观群众：DeepSeek 鲸娘 · 同人形象，MIT 许可（<a href="https://github.com/GarfieldZhung/DeepSeek-Whale-Girl" target="_blank" rel="nofollow noopener">GarfieldZhung/DeepSeek-Whale-Girl</a>）
</p>

## 0. 一句话概括

> 一次对话 = 若干**轮次**；一个轮次 = 若干**步骤**；一个步骤 = **一次模型调用**，外加它要求的那批**工具调用**。
>
> 循环只做三件事：把消息认领成一个步骤、把步骤变成一次请求、把工具结果写回日志然后回到第一步。剩下的"要不要压缩、要不要重试、要不要问人"，全挂在事件上由插件决定。

下面这张图就是这个循环的心跳，看一眼再往下读：

![一个轮次里，循环是怎么转的](/images/DSH-Agent主循环/step-loop.gif)

<span style="display:block;text-align:center;color:#888;font-size:0.9em;margin-top:-10px;">动图：消息被认领 → 模型推理 → 工具执行 → 判定，有工具就回到模型，没有就收尾</span>

## 1. 先把三层名字对齐：会话 / 轮次 / 步骤

这三个词在本系列里反复出现，先钉死：

| 层级 | 生命周期 | 边界事件 | 谁决定它 |
|---|---|---|---|
| **会话** | 跨进程，可 `resume`、可 `fork` | `session/created` | 持久化后端 + `ctx.agents` |
| **轮次 turn** | 一条消息进来，到 agent 完整回应 | `turn/start` → `turn/end` | 驱动自己在空闲时开启 |
| **步骤 step** | 轮次内部的一次推进 | `step/start` → `step/end` | 每次"模型回包"都开一个 |

{% mermaid %}
flowchart LR
  subgraph S["会话（持久化，可 resume）"]
    direction TB
    subgraph T1["轮次 1"]
      direction LR
      A1["step 1<br/>模型"] --> A2["step 2<br/>工具"]
      A2 --> A3["step 3<br/>模型"]
    end
    subgraph T2["轮次 2"]
      direction LR
      B1["step 1<br/>模型"] --> B2["step 2<br/>工具"]
    end
    T1 --> T2
  end
  S --> L[("session log<br/>只追加")]
{% endmermaid %}

关键点：**步骤不是"工具调用"，而是"一次模型往返"**。模型一次吐出三个工具调用，那还是一个 step；工具跑完再问模型，才是下一个 step。

## 2. 为什么这个循环这么薄

`dsh-agent-loop` 的 README 里有一句话，几乎定义了整个 harness 的架构边界：

> 这是 harness 中唯一包含具体循环逻辑的包。其他所有内容要么是抽象服务，要么是针对扩展点的插件：**新行为应放入插件，而不是这里**。

翻译成人话：

- 它**不替你想**"要不要搜一下""上下文是不是快满了""要不要问用户确认"；
- 它只负责把"一次模型调用 + 它的工具"跑完，然后问一句"还有活吗"；
- 任何"想改循环"的需求，99% 应该挂到事件上，而不是改这个包。

这在源码里是肉眼可见的：整个驱动类 `ReactLoopAgent` 的核心循环只有几十行（`lib/index.js:887` 起）：

```js
async kick() {
  try {
    while (await this.turn());     // 只要还有活，就一直转
  } catch (_error) { /* 关停阶段 */ }
}
```

真正干活的 `turn()` 从 `lib/index.js:938` 开始，`step()` 从 `1043` 开始。这就是全部。剩下的两万行是这个骨架上的扶手和护栏。

## 3. 消息怎么进来：inbox 与三发子弹

消息**不是**直接塞给模型的。先进 `inbox`（两个 FIFO 队列：下一轮、下一步），再由循环在合适的时机"认领"。

三个发送原语，其实是同一个 `send()` 的三个别名（`lib/index.js:800-814`）：

```js
send(message, target, wakeup) {
  const wakingAfterAbort = wakeup && this.phase.kind !== "idle" && this.phase.abort.signal.aborted;
  const resolvedTarget = wakingAfterAbort ? "next-turn" : target;
  this.inbox.splice(resolvedTarget, Infinity, 0, [message]);
  if (wakeup) this.wakeDriver(wakingAfterAbort);
}
followup(input) { this.send(input, "next-turn", true); }   // 下一轮，并唤醒
steer(input)    { this.send(input, "next-step", true); }   // 下一步，并唤醒
inject(input)   { this.send(input, "next-step", false); }  // 下一步，不唤醒
```

| 原语 | 落到哪个队列 | 是否唤醒 | 典型用途 |
|---|---|---|---|
| `followup` | next-turn | 是 | 你排队发的下一条消息 |
| `steer` | next-step | 是 | 跑到一半追加"顺便把 X 也改了" |
| `inject` | next-step | 否 | 工具上下文，搭下一班车 |

{% mermaid %}
flowchart LR
  U["用户消息"] -->|followup| Q1["next-turn 队列"]
  S2["中途插话"] -->|steer| Q2["next-step 队列"]
  C["工具上下文"] -->|inject| Q2
  Q1 -->|轮次边界一次性认领| CLAIM["claim"]
  Q2 -->|每个 step 边界认领| CLAIM
  CLAIM --> STEP["进入 step"]
{% endmermaid %}

两个细节值得记住：

1. **队列是事件化的**。每次变动先落一条 `agent/inbox/spliced` 事件，投影再同步折叠，所以"查看 inbox"和"写入日志"看到的是同一份真相。
2. **取消之后再唤醒会改道**。`send()` 里那行 `wakingAfterAbort ? "next-turn" : target`——如果当前轮次已经被 abort，这条"下一步"的消息会被改投到下一轮，避免往一具尸体里塞东西。

## 4. 一次 step 里到底发生了什么

这是全篇最该看的一节。`step()`（`lib/index.js:1043-1173`）按顺序做这些事：

{% mermaid %}
sequenceDiagram
  autonumber
  participant D as 驱动 turn/step
  participant SP as systemPrompt
  participant S as 会话日志
  participant P as Provider
  participant T as 工具调度器

  D->>SP: renderPrompt(assembly)
  D->>S: append system/message（需要变更时）
  D->>S: append user/message 批次
  D->>P: stream(request: header.config + deriveMessages + tools)
  P-->>D: 流式 chunk
  D->>S: append assistant/message（成功）或 assistant/attempt（失败）
  alt 有 tool-call
    D->>T: executeToolCalls（屏障 / 滚动池）
    T-->>S: tool/call + tool/result 按模型序落盘
    Note over D: 回到循环头，开下一个 step
  else 没有 tool-call
    D-->>D: 返回 completed，轮次收尾
  end
{% endmermaid %}

拆开说：

**第一步，把"系统提示词"落成一条消息。** 注意它不在请求头里，而是作为 `system/message` 写进会话表面（`lib/index.js:1057-1065`）：

```js
const commits = this.systemPrompt.project(renderedPrompt, {
  inHistory: preparedCall?.systemPromptUpdate === "in-history",
  startsSeries: startsRequestSeries || this.requestSurfaceGeneration !== this.session.surface.contentGeneration
                || preparedCall?.toolUpdate === void 0 && this.toolsChanged(assembly.tools)
});
for (const { message, intent } of commits) this.session.append("system/message", { turn, step, message }, intent);
```

`inHistory` 这个参数很关键：如果 provider 支持"提示词改了就追加在历史后面"，那前缀缓存不会失效；否则就只能改写头部那条 system 节点，缓存从那里开始重算。这就是[上下文篇](/2026/10/30/DSH-上下文装配全解/)里讲过的 KV cache 效应，在循环里的落地。

**第二步，把这一轮的用户消息追加进表面**（`1067-1073`），顺序是"先消息、后运行时上下文"，而且只在第一次尝试时做——重试不会重复追加，这是幂等性。

**第三步，起流**（`1084-1091`）：

```js
const stream = preparedCall?.stream(request) ?? this.loopCtx.llm.stream(request);
live.start();
for await (const chunk of stream) { signal.throwIfAborted(); live.push(chunk); }
```

**第四步，落锚点。** 成功就写 `assistant/message` 并带上 usage 与 stream（`1156`）；失败或中断则写 `assistant/attempt`——**故意不伪造一条模型说过的话**，只留下"这次尝试发生过"（`1131`）。被取消时如果已经吐了一部分字，就落一条 `interrupted: true` 的完整消息，保证"用户看到过的内容"永远在历史里（`1098`）。

**第五步，看模型要不要工具**（`1163-1167`）：

```js
if (finish.kind === "max-tokens") return { kind: "max-tokens" };
const toolCalls = message.content.filter((block) => block.type === "tool-call");
if (toolCalls.length === 0) return { kind: "completed" };
const { concluded } = await executeToolCalls(...);
return concluded ? { kind: "completed" } : null;
```

返回 `null` 就意味着"这一步还没完，接着开下一个 step"。

## 5. 工具怎么跑：屏障与滚动池

模型一次可能吐 5 个工具调用。它们不是一锅端并行，而是按"并发模式"分组（`executeToolCalls`，`lib/index.js:506-533`）：

```js
const mode = ctx.tools.executionMode(first.exec).kind;
const outcome = await runGroup(ctx, turn, step,
  mode === "parallel" ? planned.slice(next) : [first], mode, signal, acceptContext);
```

- **exclusive（独占）**：自成一组，前后都是屏障，一次只跑一个——因为它的安全依赖"没有兄弟并发"。
- **parallel（并行安全）**：进滚动池，最多同时 `maxParallelToolCalls` 个（默认 10，`lib/index.js:1297`）。

滚动池的实现就是一个"填满—等一个—再填一个"的循环（`618-640`）：

```js
while (!aborted && nextToStart < group.length && inFlight.size < maxParallelToolCalls) {
  const nextCall = group[nextToStart];
  if (nextToStart > 0 && mode === "parallel" && ctx.tools.executionMode(nextCall.exec).kind !== "parallel") break;
  await startCall(nextToStart); nextToStart++;
  await commitReady();
  ...
}
```

注意 `621` 行：**每起一个都要重新分类**。前一个调用可能改动了某个全局状态，让后一个不再并行安全——那就立刻收手，等池子排空。

还有一条铁律：**只有 dispatch 是并行的，policy、结果、结果上下文全部按模型顺序提交**。因为模型是按顺序理解世界的，结果乱序它会精神错乱。

{% mermaid %}
flowchart TB
  M["模型：5 个 tool-call"] --> C1{"调用 1 的并发模式"}
  C1 -->|exclusive| E["单独跑完<br/>屏障"]
  C1 -->|parallel| POOL["滚动池，上限 N"]
  POOL --> R1["调用 2 起跑"]
  POOL --> R2["调用 3 起跑"]
  R1 -.->|谁先完事先占位| COMMIT
  R2 -.-> COMMIT
  COMMIT["按模型顺序提交 tool/result"] --> NEXT["回到模型"]
  E --> NEXT
{% endmermaid %}

## 6. 失败了怎么办：两条路，两种命运

这是最容易误解的地方。失败分两类，走向完全不同：

| 失败来源 | 去哪 | 后果 |
|---|---|---|
| adapter 选择 / dispatch / 迭代失败 | `agent/request-error` 瀑布 | **可能被救活**：监听器返回 `{kind:'retry'}` |
| 中间件 / 结果处理 / 工具 / 其它插件 | 直接抛 | **关掉当前轮次**，循环本身不死 |

源码里就是这段（`lib/index.js:1130-1146`）：

```js
if (finish.kind === "error" || finish.kind === "aborted") {
  live.settle("assistant/attempt", () => this.session.append("assistant/attempt", {...}));
  const action = await this.dispatch.waterfall("agent/request-error", {
    turn, step, provider: request.provider, failure: finish.failure, retryPolicy: preparedCall?.retryPolicy, signal
  }, () => Promise.resolve(void 0));
  if (action?.kind !== "retry") throw new LlmError(finish.failure.message, finish.failure.code, finish.failure);
  continue;  // ← 救活了，原地重试
}
```

那个 `continue` 很关键：重试**复用同一个 assembly**，不会重新跑 `agent/pre-step`、不会重复装配提示词、不会重复接纳用户消息。失败的是网络，不是用户的话。

真正的重试策略在 `dsh-llm-retry` 里：它挂在 `agent/request-error`，按 provider 的 `retryPolicy` 算指数退避加抖动（`initialDelayMs * 2^n`，封顶 `maxDelayMs`，乘一个抖动因子），并且**先把 `llm/retry` 事件写进日志，再开始等**——所以就算进程这时被 kill，重启后也能看出"我上次是准备重试第几次"。

{% mermaid %}
flowchart LR
  F["模型调用失败"] --> Q{"失败来自哪一层"}
  Q -->|adapter / dispatch / 迭代| W["agent/request-error 瀑布"]
  W -->|有监听器返回 retry| BACK["同一个 assembly 原地重试"]
  W -->|没人处理| T1["终态失败，轮次 error 收尾"]
  Q -->|插件 / 工具 / 中间件| T2["直接抛出，轮次关闭"]
  T2 --> LOOP["循环仍然活着，等下一条消息"]
{% endmermaid %}

一句话：**插件把轮次作死，循环不会跟着死。**

## 7. 取消：把"已经说出口的话"留住

`agent.cancel(cause, { keepInbox })`（`lib/index.js:815-821`）做两件事：清队列（除非 `keepInbox`）、abort 当前信号。

```js
cancel(cause, options = {}) {
  if (!options.keepInbox) {
    this.inbox.clear();
    if (this.phase.kind !== "idle") this.phase.wakeRequested = false;
  }
  if (this.phase.kind !== "idle") this.phase.abort.abort(cause);
}
```

取消的语义细节，比想象中讲究：

- **空闲时取消是 no-op**——没有活可取消，不制造噪音。
- **已经吐出来的字不丢**。上面 §4 说的 `interruptedBlocks()` 会把收到的前缀落成 `interrupted: true` 的 assistant 消息，下一个请求里模型能看到"我刚才说到哪了"。
- **没派发的工具调用拿一张"死亡证明"**（`appendSkippedToolCall`，`663-678`）：`Error: tool call aborted before dispatch`，错误码 `ABORTED_BEFORE_DISPATCH`。否则模型下一步会对着"凭空消失的调用"发懵。
- **abort 之后到的唤醒会被锁存**（`wakeRequested`），等驱动收敛到 idle 时再补发，不用你再喊一次。

状态机长这样：

{% mermaid %}
stateDiagram-v2
  [*] --> idle
  idle --> running: 有活被唤醒
  running --> idle: 队列空且无待办
  idle --> maintenance: runMaintenance
  maintenance --> idle: job 完成
  running --> running: 下一步 / 下一轮
{% endmermaid %}

## 8. 轮次什么时候结束

轮次不是"模型不再要工具"就立刻结束，它还要过一道关（`lib/index.js:1000-1008`）：

```js
if (turnEnds && this.inbox.nextStep.length === 0) {
  await this.dispatch.serial("agent/turn-stopping", { turn, signal });
  signal.throwIfAborted();
}
if (turnEnds && this.inbox.nextStep.length === 0) break;
target = "next-step";
```

两个条件同时成立才收尾：**这一步已经给出终局判定**，并且**下一步队列是空的**。哪怕模型说"我完事了"，只要队列里还有 `steer`/`inject` 进来的东西，循环就继续跑同一个轮次。

在真正 `turn/end` 之前，还有一个 `agent/turn-stopping` 串行检查点——这是"你还想让它再干点啥吗"的最后一次机会，插件可以在这里续命或取消。

`turn/end` 的 reason 有四种：`completed`、`blocked`（pre-step 被拒）、`error`、`aborted`（带取消原因）。看过日志的人会注意到 `max-tokens` 也会终结轮次——不是错误，是"这次说不完了"。

顺带说个**没有**的东西：**没有内置的轮次预算**。工具调用和 steering 都能让轮次无限延长，DSH 不拦你；要防跑飞，自己挂 `agent/turn-stopping` 去取消。这是有意的取舍：循环不做策略。

## 9. 该交给插件的，别改循环

这是本文最实用的一张表。想加功能，先在这里找位置：

| 想做的事 | 挂哪 |
|---|---|
| 每条消息先查记忆再回答 | `agent/pre-step` 注入上下文，或 `agent/request` 改装配 |
| 上下文快满时压缩 | `agent/pre-step` 看压力，`agent/request-error` 处理溢出 |
| 请求失败重试 | `agent/request-error` 返回 `{kind:'retry'}` |
| 沙箱 / 权限 / 只读模式 | `tools/pre-execute` 拦，`tools.guard()` |
| 子 Agent 派活 | `ctx.agents.create()` + `ctx.jobs`（编程式） |
| 跑飞了要停 | `agent/turn-stopping` 里取消 |
| UI 实时打字效果 | `agent/assistant-stream` 进程内事件 |
| 持久化 | `session/event` 的观察者 |

反过来，什么时候才该动循环本身？几乎只有一种：**你要改"轮次/步骤"的定义**。其余一律插件。

## 10. 自己动手验证

不用信我，日志都在本地。会话日志是 zstd 压缩的 JSONL（默认在 `~/.dsh/sessions/`），一行一个事件：

```bash
# 1. 看三级结构（turn / step / 模型消息 / 工具）
zstdcat ~/.dsh/sessions/*/*/session.v3.jsonl.zstd \
  | jq -r 'select(.type | test("turn/|step/|assistant/message|tool/call|tool/result")) | [.type, (.seq|tostring)] | @tsv' | head -30

# 2. 看循环自己的事件
zstdcat ~/.dsh/sessions/*/*/session.v3.jsonl.zstd | grep -E "agent/" | head
```

你会看到 `turn/start` → `step/start` → `assistant/message` → `tool/call` → `tool/result` → `step/end` → …… → `turn/end` 这个严格顺序。**日志只有一条时间线，所有"并行"最终都被压回模型顺序**——这正是这套设计最值得抄的地方。

源码对照表（都是编译产物 `dsh-agent-loop/lib/index.js` 里的真实行号）：

| 看什么 | 位置 |
|---|---|
| 驱动主循环 | `kick()` `:887` |
| 轮次机器 | `turn()` `:938-1042` |
| 步骤机器 | `step()` `:1043-1173` |
| 三发子弹 | `send/followup/steer/inject` `:800-814` |
| 取消 | `cancel()` `:815-821` |
| 唤醒锁存 | `wakeDriver()` `:854-869` |
| 工具分组 | `executeToolCalls()` `:506-533` |
| 滚动池 | `runGroup()` `:551-661` |
| 默认并发度 | `:1297` |

---

三篇连起来看，DSH 的骨架就清楚了：**agent-loop 负责转，system-prompt 负责拼，session 负责记**，压缩、重试、沙箱、UI 全挂在这三根柱子的事件上。

下一篇打算拆工具执行那条流水线——`pre-execute` → `execute` → `post-execute` → `finalizeContent` → `result`，看看一个 `bash` 调用到底被几个插件摸过。

**相关阅读**：

- [DSH 上下文装配全解：一次模型请求到底是怎么拼出来的](/2026/10/30/DSH-上下文装配全解/)
- [DSH 会话压缩（Compaction）策略详解](/2026/10/30/DSH-会话压缩策略详解/)
- [DSH 沙箱设计：一次 bash 调用，到底被关进了什么](/2026/11/02/DSH-沙箱设计/)——真正跑命令的时候，是谁按着闸刀：同世界围栏、三条缝与升级阶梯。
