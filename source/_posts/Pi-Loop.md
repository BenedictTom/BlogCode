---
title: "Pi 的 Agent Loop：一次请求转几圈，它凭什么知道该停了"
date: 2026-11-05 01:40:00
categories: [Pi]
tags: [Pi, Agent, 源码解析]
cover: /images/Pi-Loop/cover.png
description: 整份代码里最短也最关键的 159 行：双层循环、四种终止条件、两种工具并发策略，以及"截断的工具调用为什么一个都不许执行"。
---

## 0. 一句话概括

Agent 的"智能"在模型那边，工程上的全部难点其实是一个问题：**什么时候让循环再转一圈，什么时候让它停**。

Pi 把这个问题压缩进了 `packages/agent/src/agent-loop.ts` 的 `runLoop()`——159 行，两个 `while`。第一个管"这一圈里的工具要不要继续跑"，第二个管"模型说完了，但用户又插了一句话"。

这篇按执行顺序拆开：输入怎么进来、每圈里发生什么、工具怎么并发、什么时候停、以及那些看起来多余的钩子到底是给谁留的。

## 1. 入口：三个函数，一个循环

`agent-loop.ts` 对外只暴露三个东西：

```ts
agentLoop(prompts, context, config, signal, streamFn)        // 新的一句话，开跑
agentLoopContinue(context, config, signal, streamFn)          // 不给新消息，接着跑
runAgentLoop(...) / runAgentLoopContinue(...)                 // 上面两个的实现
```

后两个是同一件事的两个入口，区别只在**要不要先塞一条新消息进上下文**。`agentLoopContinue` 的用途写得很直白（73-79 行注释）：重试。上下文里已经有用户消息或工具结果了，只是上一轮失败了，接着跑就行。

它有一道前置检查，很能说明这套设计的严格程度：

```ts
// agent-loop.ts:90-92
if (context.messages[context.messages.length - 1].role === "assistant") {
	throw new Error("Cannot continue from message role: assistant");
}
```

**不允许从一条助手消息后面接着跑。** 因为模型的规矩是"你说完轮到我，我说完轮到你说"，如果最后一轮是助手在说话，再发一次请求等于让它自问自答——有的供应商会直接 400，有的会静默插入一条空的 user 消息，两种都很讨厌。这里选择在本地就炸掉，早失败。

### 开跑之前先声明"工具变了"

`runAgentLoop` 做的第一件事不是发请求，是调 `declareToolChanges()`（342-372）：

```ts
const initialMessages = declareToolChanges(context, prompts);
```

这东西解决的是一个很实际的问题：**会话中途工具集合变了**（比如刚刚连上一个 MCP server，或者某个扩展动态注册了工具），模型怎么知道？

Pi 的答案是：在消息流里插一条 `role: "system"` 的消息，带上 `toolsAdded` 和 `toolsRemoved` 两个字段。这两个字段记录的是"相对上一轮，工具多了什么、少了什么"。

为什么不用"改系统提示词"？因为系统提示词在会话开头，改它意味着重写历史。而**追加一条系统消息**是 O(1) 的，还能被回放——会话重开时，把这条消息也回放一遍，模型看到的工具集合和当初一模一样。

注释里那句话是关键（335-340 行）：`context.tools` 是**运行时能执行**的工具，转录里的系统消息是**模型能调用**的工具。两者不一致就会出乱子，所以每次请求前都要对齐一次。

## 2. 两个 while，四种出口

核心就是这段骨架：

```ts
// agent-loop.ts:188
while (true) {
	let hasMoreToolCalls = true;

	// 内层：跑工具、收打断
	while (hasMoreToolCalls || pendingMessages.length > 0) {
		// ... 一轮对话
	}

	// 模型说完了，看有没有排队的新消息
	const followUpMessages = (await config.getFollowUpMessages?.()) || [];
	if (followUpMessages.length > 0) { ... continue; }

	// 没有任何理由再转了
	break;
}
```

{% mermaid %}
flowchart TD
  A["外层 while(true)"] --> B["内层 while<br/>跑工具 / 收打断"]
  B --> C{"模型这一轮<br/>还有工具调用?"}
  C -->|有| B
  C -->|没有| D{"有排队的<br/>follow-up 消息?"}
  D -->|有| A
  D -->|没有| E["break：循环结束"]
  B -.AbortSignal.-> F["中止：收尾后退出"]
{% endmermaid %}

内层管"工具链"，外层管"用户插话"。四种离开的方式：

1. **模型不再要工具**，`hasMoreToolCalls` 为 false，内层退出。
2. **工具结果说"到此为止"**（`terminate`），整个批次算终止，同样退出内层。
3. **出错或被打断**（`stopReason` 是 `error` / `aborted`），直接 `agent_end` 返回，连外层都不进（254-265 行）。
4. **外层也没有排队消息**，`break`。

{% mermaid %}
flowchart TD
  s["agent_start"] --> t1["turn_start"]
  t1 --> pn{"有上一轮吗"}
  pn -->|"有"| prep["prepareNextTurn<br/>压缩 / 打补丁"]
  pn -->|"没有"| req
  prep --> req["prepareRequest"]
  req --> sst["streamAssistantResponse"]
  sst --> err{"stopReason<br/>error 或 aborted"}
  err -->|"是"| end1["turn_end + agent_end"]
  err -->|"否"| tc{"有工具调用吗"}
  tc -->|"有"| exec["执行工具<br/>并行或串行"]
  exec --> te["turn_end"]
  tc -->|"没有"| te
  te --> more{"还要转吗"}
  more -->|"有工具 / 有插话"| t1
  more -->|"没有"| fu{"有排队消息吗"}
  fu -->|"有"| t1
  fu -->|"没有"| end2["agent_end"]
{% endmermaid %}

**注意这里没有最大轮数限制。** 没有 `maxTurns`，没有超时熔断。理论上一段对话可以无限转下去，只要模型还在要工具。

这不是漏了。在 agent 里加轮数上限通常弊大于利：一个正常的重构任务可能二十轮，一个病态的死循环可能两百轮也停不下来——固定上限要么误伤前者，要么放过后者。Pi 把"停下来"的责任交给三处：模型自己（`stop`）、工具自己（`terminate`）、用户自己（Esc 或插话）。上下文胀了由压缩兜底（第四篇）。

## 3. 一圈里到底发生了什么

按 `runLoop` 的代码顺序走一遍。

### 3.1 先看有没有人插话

```ts
// agent-loop.ts:185
let pendingMessages: AgentMessage[] = (await config.getSteeringMessages?.()) || [];
```

`steering` 是"引导"：用户在 agent 干活的时候又打了一句话，比如"别动测试文件"。这句话不该等这一轮跑完——它应该**立刻**影响下一圈。

所以每圈开始前都去拉一次队列。而且注意一个细节（210-215 行）：

```ts
// Preparation can be long-running (for example, compaction). Pick up steering
// queued while it ran. Only poll again if the earlier poll returned nothing;
// otherwise one-at-a-time mode would deliver two messages in this turn.
if (pendingMessages.length === 0) {
	pendingMessages = (await config.getSteeringMessages?.()) || [];
}
```

`prepareNextTurn` 可能很慢（里面会做压缩，也就是再发一次模型请求）。等它回来，队列里可能又多了消息。但这里**只在之前没拿到消息时才再拉一次**——因为 `steering` 有个 `one-at-a-time` 模式，如果无脑拉两次，用户会发现自己打的一句话在一轮里被投递了两遍。

这种"多拉一次还是少拉一次"的细节，是这类系统里最容易写错、也最难测出来的地方。

### 3.2 准备下一轮：压缩与提示词补丁

```ts
// agent-loop.ts:194
if (lastCompletedTurn) {
	const nextTurnSnapshot = await config.prepareNextTurn?.(lastCompletedTurn);
	...
}
```

`prepareNextTurn` 是循环里最肥的一个钩子。它返回一个"快照"，可以改三样东西：上下文、模型、思考档位。

`coding-agent` 在这个钩子上挂了两个东西（`core/agent-session.ts:918-957`）：

1. **压缩**（`_compactBeforeNextAssistantResponse`）——上下文快满了，就把前半段总结掉。
2. **系统提示词补丁**——把当前该有的提示词和模型手里那份比对，只在有差异时发一条"改这几段"的系统消息。

也就是说：**面板上看起来"每轮都重新拼一遍提示词"，实际上大多数轮次什么都不发**。第四篇细讲。

### 3.3 发请求

```ts
// agent-loop.ts:228
const requestUpdate = await config.prepareRequest?.({ context, model, thinkingLevel }, signal);
```

`prepareRequest` 是最后一道关卡：请求发出去之前的**最后一次**改上下文、换模型的机会。压缩和提示词补丁在上一站，这里是"临门一脚"。

然后就是 `streamAssistantResponse`（390-479）：

```
transformContext（可选）→ convertToLlm → normalizeContext → streamFn → 消费事件流
```

三个转换里，`convertToLlm` 是重点。它把内部表示 `AgentMessage` 转成供应商能吃的 `Message`。为什么要有两种表示？因为内部要能表达"压缩摘要""分支摘要""自定义消息"这些供应商不存在的东西，而供应商只认 user / assistant / tool 三种。**转换只在这一个地方发生**，别的任何位置都不许出现供应商格式。

事件流有十一种：`start`、`text_start/delta/end`、`thinking_start/delta/end`、`toolcall_start/delta/end`、`done`、`error`。

流式的好处是 TUI 能一个字一个字地画；代价是**你永远不知道下一条消息会不会被截断**。这就引出下面这个设计。

### 3.4 工具调用：并行还是串行

拿到助手消息后，把 `content` 里所有 `type === "toolCall"` 的块挑出来（268 行）。

执行策略有两条路（518-533）：

```ts
const hasSequentialToolCall = toolCalls.some(
	(tc) => currentContext.tools?.find((t) => t.name === tc.name)?.executionMode === "sequential",
);
if (config.toolExecution === "sequential" || hasSequentialToolCall) { ... 串行 }
return executeToolCallsParallel(...);
```

默认并行，但只要**其中一个**工具声明了 `executionMode: "sequential"`，整批退化成串行。为什么不是"能并行的并行、该串行的串行"？因为顺序本身可能就是语义：`bash` 里改文件、`edit` 里读文件，两个同时跑会读到半截状态。

串行和并行的代码几乎是两份，差别在并行版把每个调用包成闭包先攒起来，最后 `Promise.all`（656-658）。但**结果的顺序仍然是模型的调用顺序**——并行的是执行，不是结果。

还有个细节：并行版在执行前先检查 `signal.aborted`（629-638），已经中止的调用直接返回 `"Operation aborted"` 的错误结果，不会白跑一趟。

### 3.5 一个工具调用的四步

不管并行串行，每个调用都走 `prepareToolCall` → `execute` → `finalizeExecutedToolCall` 三步（串行版在 559-577）。

**第一步 `prepareToolCall`（718-787）**，这里有三道关：

1. 工具不存在？返回错误结果，不抛异常。
2. 参数校验失败？`validateToolArguments` 抛，被 `catch` 接住转成错误结果。
3. `beforeToolCall` 钩子想拦？返回 `{ block: true, reason }`，同样变成错误结果。

注意全部是**变成一条错误消息回给模型**，而不是中断循环。模型收到"你这个参数不对"通常会自己改，这比把整个会话打断有用得多。

**第二步执行**（831-867）。这里有个容易被忽略的细节：结果里的 `durationMs` 是在 `performance.now()` 前后夹出来的，`onUpdate` 回调会在执行过程中被反复调用（长命令的进度就靠它），而 `acceptingUpdates` 这个开关保证"结果已经返回之后，迟到的进度更新被丢弃"。

**第三步收尾**（869-920）。`afterToolCall` 钩子可以改结果的内容、详情、用量，甚至把非错误改成错误。还有一个很细的处理：

```ts
// agent-loop.ts:894-896
// Structured content not replaced along with the content may no longer match it.
const structuredContent =
	afterResult.structuredContent ?? (afterResult.content ? undefined : result.structuredContent);
```

如果钩子改了 `content` 但没给 `structuredContent`，那份结构化数据就**删掉**，而不是留着。因为它描述的已经不是现在这段文字了，留着就是撒谎。

## 4. 两种情况特别处理

### 4.1 输出被截断：一个工具都不许跑

这是整个文件里我最喜欢的一段（272-279、488-513）：

```ts
// A "length" stop means the output was cut off by the token limit, so
// every tool call in the message may carry truncated arguments.
const executedToolBatch =
	message.stopReason === "length"
		? await failToolCallsFromTruncatedMessage(toolCalls, emit)
		: await executeToolCalls(...);
```

`stopReason === "length"` 意味着模型的输出撞到了 token 上限。这时消息里那些工具调用，参数可能是**被截断的 JSON**。

而 Pi 在解析流式参数时用了"尽力抢救"的解析器——它会尽量把半截 JSON 补成一个合法对象。于是你会得到一个**语法合法、语义缺半**的参数：`{"path": "src/index.ts"}` 变成了 `{"path": "src/"}`，校验能过，执行就出事。

所以这里的规矩是：**只要整条消息被截断了，里面的工具调用一个都不执行**，全部回一条错误让模型重发。

```ts
`Tool call "${toolCall.name}" was not executed: the response hit the output token limit, so its arguments may be truncated. Re-issue the tool call with complete arguments.`
```

这条错误消息写得很具体：说清了原因（撞上限）、后果（参数可能残缺）、该怎么办（重发）。给模型的错误提示就该这么写——不是"失败了"，而是"为什么失败、下一步做什么"。

### 4.2 `terminate`：工具自己说"别转了"

工具的结果里有个 `terminate` 字段。语义是：这次调用完成后，**这一批不用再继续了**。

判定在 `shouldTerminateToolBatch`（700-702）：

```ts
return finalizedCalls.length > 0 && finalizedCalls.every((finalized) => finalized.result.terminate === true);
```

注意是 `every` 不是 `some`：一批里三个工具，只有一个说停，不算停。因为并行时它们是同时跑的，没法"半路取消"其他兄弟。

什么工具会用它？典型的是"任务完成"类工具，或者某个扩展想让 agent 在给出最终答案后立刻收手，而不是再转一圈浪费 token。

`beforeToolCall` 钩子也能设 `terminate`（757-759），这就给了扩展一种能力：**拦下某个调用，并且顺手结束这一批**。

## 5. 事件：给 TUI 看的，也是给扩展看的

循环一路上都在 `emit`：

```
agent_start → turn_start → message_start / message_update… / message_end
           → tool_execution_start / update… / end
           → turn_end → … → agent_end
```

这些事件有两个消费者：TUI（画界面）和扩展（钩子）。第三篇会讲它们在会话里怎么落盘，这里只说一个设计后果——

**因为一切都要走事件，循环本身不能有"顺手做点别的"的代码。** 想在每轮结束插一句话？挂 `finishTurn`，别改循环。想在请求前改上下文？挂 `prepareRequest`。

`AgentSession` 就是这么干的：它没有 fork 一份循环，而是把 `agent.finishTurn` 和 `agent.prepareNextTurnWithContext` **包一层**（`core/agent-session.ts:906-957`），先跑自己的逻辑，再调原来的。

这个"包装而不是修改"的套路，在整个仓库里反复出现。好处是循环永远是那 159 行，任何人读一遍就能确信"没有隐藏行为"；坏处是钩子的执行顺序变成了一种隐式契约——谁先谁后，得从包装的嵌套顺序去推。

## 6. `finishTurn` 的三种返回值

一轮结束时调 `finishTurn`，它能回三样东西，语义各不相同：

| 返回 | 含义 | 循环行为 |
| --- | --- | --- |
| `{ action: "end" }` | 我说完了，别再转 | 立刻 `agent_end` |
| `{ action: "continue" }` | 虽然模型没要工具，但还得再问一次 | 空转一轮（不塞新消息） |
| `undefined` | 没意见 | 看有没有工具/插话决定 |

`"continue"` 这个分支最容易看漏（303-307、320-323）：

```ts
explicitContinuation = decision?.action === "continue";
pendingMessages = (await config.getSteeringMessages?.()) || [];
if (hasMoreToolCalls || pendingMessages.length > 0) {
	explicitContinuation = false;   // 有正经事要干，就别空转了
}
```

它是给谁用的？给那种"模型停下来说了句话，但扩展知道还有活没干"的场景——比如某个校验钩子发现还有编译错误，想再给模型一轮机会，但又不想伪造一条用户消息污染转录。

注意那句 `explicitContinuation = false`：如果同时还有工具要跑或有消息要投递，就取消空转。否则会变成"干完活再空转一轮"，白烧一次请求。

## 7. 中止

用户按 Esc，`agent-session.ts` 调 `abort()`，`AbortSignal` 一路传下去。

信号在循环里有五六个检查点：`prepareToolCall` 前后、每个工具执行前后、并行版每个闭包开头。设计原则是**宁可多查，不可漏查**——一旦信号 abort，每个还没开始的工具都立刻返回 `"Operation aborted"` 的结果。

被打断的那一轮仍然会走完 `turn_end` 和 `agent_end`，只是 `stopReason` 是 `aborted`（254-265）。**会话不会留下半条消息**，这是第三篇讲会话树时会用到的性质。

## 8. 小结

- 两个 `while`：内层跑工具和插话，外层等用户排队消息。没有轮数上限。
- 每圈五站：拉插话 → `prepareNextTurn`（压缩 + 提示词补丁）→ `prepareRequest`（临门一脚）→ 流式请求 → 工具执行。
- 工具默认并行，遇到 `executionMode: "sequential"` 整批退化成串行，但结果顺序永远等于调用顺序。
- 三种"停"：模型不要工具了、工具 `terminate`、`finishTurn` 说 end。还有一种"再转一圈"：`finishTurn` 说 continue。
- 输出被截断时，整条消息里的工具调用**全部不执行**——因为抢救式解析可能给出"合法但残缺"的参数。
- 所有扩展点都是钩子，循环本体永远是那 159 行。

下一篇讲这条循环留下的东西存在哪：为什么 Pi 的会话是一棵树，`/tree` 回退时那半条分支去哪了，压缩又为什么要在树上切一刀。

---

**相关阅读**

- [Pi 入门：一个把"极简"当真了的 agent](/2026/11/05/Pi-入门/)
- [Pi 的会话树：一条对话为什么不是一条线](/2026/11/05/Pi-会话树/)
- [Pi 怎么定义一个工具：一张卡片上的十个字段](/2026/11/05/Pi-工具/)
