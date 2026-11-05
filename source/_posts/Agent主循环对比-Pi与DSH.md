---
title: "同一个 Agent 主循环，两种工程答案：Pi 与 DSH 对照解剖"
date: 2026-11-05 12:00:00
categories: [Agent]
tags: [Agent, Pi, DSH, 源码解析]
cover: /images/Agent主循环对比/cover.jpg
description: 把 Pi 和 DSH 的 agent loop 摆在一起，逐条对六个真问题：工具集合中途变了怎么办、用户在跑的时候插话怎么办、上下文撑爆了怎么压、内部消息怎么变成供应商能吃的格式、中止时那些跑到一半的工具调用怎么收尾，以及两套循环在"真相"的定义上有什么根本分歧。
---

## 0. 一句话概括

Agent 的主循环，就是一句 `while (true)` 里面塞三件事：**把上下文喂给模型、把模型吐出的工具调用执行掉、判断还要不要转下一圈**。

这句话两个项目都会背。真正的差异全在那些"看起来像边角料"的地方——工具集合在会话中途变了、用户在模型正在跑的时候又发了一句话、上下文快撑爆了、内部的消息结构要翻译成某家供应商的 wire 格式、用户按了 Esc。这些情况每一个都会把一个天真的 `while` 循环撕碎。

我最近把 Pi（`earendil-works/pi`，MIT，HEAD `395f3e0`，`packages/coding-agent` v1.5.0）和 DSH（DeepSeek Harness，编译产物，从 `app.asar` 里解出来的 `@deepseek-ai/dsh-*`）两边的循环都读了一遍。它们是同一族设计的两支：都把模型调用抽成流、把工具执行抽成调度、都靠 abort signal 收场。但在这六件事上，两边给出的答案几乎每一条都不同——而且不同的方向高度一致，指向两种不同的世界观。

下面按"问题"组织，每个问题先摆两边的做法，再给源码坐标，最后说这个选择换来了什么、代价是什么。

## 1. 先把两副骨架摆出来

Pi 的循环在 `packages/agent/src/agent-loop.ts` 的 `runLoop`（`:171`）里，是**两层嵌套**：

```text
while (true) {                    // 外层：还有没有人补话
  while (hasMoreToolCalls || pendingMessages.length > 0) {   // 内层：工具与插话
     …注入插话消息 → 发请求 → 流式收助手消息 → 执行工具…
  }
  // 内层退出的唯一条件：没有工具调用、也没有待处理消息
}
```

内层的条件写得很直白：**只要还有工具调用，或者还有排队的话没说完，就再转一圈**（`agent-loop.ts:192`）。外层的注释是 `continues when queued follow-up messages arrive after agent would stop`——内层已经打算停了，结果又有人说话，外层把它捞回来再转（`:187`、`:305`）。

DSH 的循环长得像 React：一个 `kick()`（`dsh-agent-loop/lib/index.js:887`）里只有一句 `while (await this.turn());`（`:889`）——**每一步返回"还有没有下一步"，循环本身不关心里面发生了工具调用还是别的**。真正干活的是 `turn()`/`step()`，以及一个显式的相位状态机：`idle | running | maintenance`（`:791`）。

这个差别不是审美。Pi 把"要不要继续"编码成了循环条件里的两个布尔量；DSH 把它编码成了状态机的一次相变，并且额外给了第三个相位 `maintenance`——**用于那些"我需要独占这个 agent 干一件不进对话的事"的场景，压缩就在里面跑**（`:825-845`）。

{% mermaid %}
graph LR
  subgraph PI["Pi：两层循环"]
    A1["外层 while(true)"] --> A2["内层<br/>hasMoreToolCalls || pendingMessages"]
    A2 --> A3["取插话 → 发请求 → 执行工具"]
    A3 --> A2
    A2 -->|"都空了"| A1
  end
  subgraph DSH["DSH：相变循环"]
    B1["kick()"] --> B2["while (await turn())"]
    B2 --> B3["phase = running<br/>step / turn"]
    B3 --> B4["phase = maintenance<br/>压缩、维护"]
    B4 --> B2
    B2 -->|"turn() 返回 false"| B5["phase = idle"]
  end
{% endmermaid %}

一个后果可以先记下来：**Pi 的插话是"轮询"进来的，DSH 的插话是"投递"进来的**。这条差别会在第 3 节炸开。

## 2. 工具集合在会话中途变了

这是最容易被忽略、但几乎必踩的一件事。会话跑到第十轮，某个插件注册了一个新工具，或者 `tool_search` 把一个工具从"延迟加载"变成"已加载"。此时**请求里能带的工具清单变了**。

供应商那边对这件事的容忍度天差地别：有的允许你在对话中途改工具列表，有的要求工具声明在整段对话里保持稳定，还有的（比如某些走 prompt 缓存的路由）一旦声明变了就整段缓存失效。所以两个项目都必须回答三个问题：**变化记在哪、谁来决定怎么表达、什么时候让模型知道**。

**Pi 的做法是盖章。** `declareToolChanges(context, pendingMessages)`（`agent-loop.ts:342-372`）在每次发请求前，把"上下文里已经声明过的工具集合"（`getCurrentTools([...context.messages, ...pendingMessages])`，`:357`）和"当前真正生效的工具声明"（`context.tools.map(toToolDeclaration)`，`:358`）做一次 diff，得到 `toolsAdded` / `toolsRemoved`；有变化就往消息流里**插一条 `system` 消息**，把这次变化盖上（`:368`）。如果待发的消息里本来就有 system 消息，就把它改写成带变化字段的那条（`:362-366`），保证一次请求里最多一条盖章消息、而且盖在用户消息前面（`:369-371`）。

注意 `getCurrentTools` 是**从 transcript 反推**的——Pi 的"当前工具集"不是某个全局 registry 的即时快照，而是"这批消息一路声明下来的结果"。这跟它整个项目"会话记录是唯一真相"的取向一致。

**DSH 的做法是记账 + 投影。** 循环在 `buildRequest()` 里对比本次请求头与上一次落盘的 `request/header`（`dsh-agent-loop/lib/index.js:1219-1240`）：头变了就追加一条 `request/header`（`reason: "change"`），然后按名字 diff 出增删，**追加一条 `developer/message`**，内容是 `tool-addition` / `tool-removal` 块，来源标记为 `{ kind: "tool-registry" }`（`:1240-1258`）。工具**增加**时还会把新 `headerSeq` 挂在这条消息上，用于把"从哪一版请求头开始生效"钉死。

真正把它翻译给供应商的是 `dsh-llm` 里的 `projectToolUpdates(messages, tools, toolUpdate, history)`（`dsh-llm/lib/index.js:786-858`）：

- 路由声明 `modelInfo.toolUpdate === undefined` 时，它直接把 `developer` 消息**全部丢掉**、工具清单原样给出（`:787-796`）——也就是说，**这条路由根本不允许中途改工具**，那就当无事发生；
- 路由支持 `"in-history"` 时，它按历史逐条重放：`tool-addition` 只保留第一次出现的那个（`offered` 集合去重，`:812-817`），`tool-removal` 从已发放集合里删掉（`:818-819`）；
- 带 `deferLoading` 的工具（就是 `tool_search` 那套延迟加载）默认**不发放**，要等它第一次被"增补"过才进清单（`:809`）。

{% mermaid %}
flowchart TD
  T["本次要发的工具清单<br/>vs 上次"] --> P{"Pi"}
  T --> D{"DSH"}
  P --> P1["diff transcript 反推的集合"]
  P1 --> P2["插入 / 改写一条 system 消息<br/>toolsAdded / toolsRemoved"]
  P2 --> P3["所有供应商收到同样的东西"]
  D --> D1["追加 request/header (reason: change)"]
  D1 --> D2["追加 developer/message<br/>tool-addition / tool-removal"]
  D2 --> D3{"路由的 toolUpdate 能力"}
  D3 -->|"undefined"| D4["丢掉 developer 消息<br/>工具按当前快照直发"]
  D3 -->|"in-history"| D5["逐条重放增删<br/>deferLoading 只发已加载的"]
{% endmermaid %}

对照一下："改工具"这件事，Pi 认为是**对话的一部分**（所以做成消息、写进 transcript、任何后端都看得见），DSH 认为是**路由能力问题**（所以先记账存证，再按每条路由的容忍度投影出三种形态）。前者简单、一致；后者多一层，但能让同一条会话在"容忍中途改工具"和"不容忍"的路由之间切换而不炸。

## 3. 运行时插话

用户在模型正在跑的时候又敲进来一句话，是 agent 产品里最高频的操作。两边的处理方式差异极大。

**Pi 是轮询。** 循环手里没有队列，只有三个查询点：进入 `runLoop` 时先拉一次（`agent-loop.ts:184`，注释写着 `Check for steering messages at start (user may have typed while waiting)`）；每一轮开始前，如果上一轮已完成，调 `prepareNextTurn` 之后**再拉一次**（`:210-217`）；拉到的东西在下一次请求**之前**逐条塞进上下文（`:219-226`）。拉到的消息就是普通的用户消息，跟历史消息一视同仁。

这里有一段注释很值得抄下来（`:210-217`）：

> Preparation can be long-running (for example, compaction). Pick up steering queued while it ran. Only poll again if the earlier poll returned nothing; otherwise one-at-a-time mode would deliver two messages in this turn.

翻译：压缩可能跑很久，跑的时候用户说的话不能丢，所以要补拉一次；但如果第一次就拉到了，这次就**不要再拉**，否则"一次一条"的模式会一轮塞进两条。这类细节只有在真实产品里被咬过才会写下来。

Pi 的插话还分两层语义：`pendingMessages` 在内层循环里消化（**下一轮请求前生效**），而"内层已经要退出了才来的话"由外层循环接住（`:305`）——**下一轮对话生效**。两种粒度不需要额外的 API，靠循环结构天然分开。

**DSH 是投递。** 每个 agent 有一个 inbox，`send(message, target, wakeup)`（`dsh-agent-loop/lib/index.js:800-807`）决定消息插到哪个位置，而三个公开方法把语义写死在了名字里：

| 方法 | target | wakeup | 含义 |
|---|---|---|---|
| `followup(input)`（`:806`） | `next-turn` | 是 | 这一轮干完再说（排队进下一轮） |
| `steer(input)`（`:809`） | `next-step` | 是 | 下一步之前插进去（模型还没发下一句就先看到） |
| `inject(input)`（`:812`） | `next-step` | 否 | 只塞进上下文，**不唤起**沉睡的循环 |

`wakeup` 的语义是"如果 agent 正闲着，要不要把它叫起来"。`inject` 不唤起，就是"我先把这段话放进上下文，等你下次自己醒过来时看见"。这个区分 Pi 没有——Pi 的插话只在循环活着的时候有意义。

还有两个更细的设计，只有在并发/中断场景下才看得出价值：

一是**中止后的重新分类**。`send` 里有一句 `const wakingAfterAbort = wakeup && this.phase.kind !== "idle" && this.phase.abort.signal.aborted; const resolvedTarget = wakingAfterAbort ? "next-turn" : target;`（`:801-804`）。意思是：如果这个 agent 刚刚被你按了 Esc 正在收尾，你这时候发的"steer"会被降级成"next-turn"——因为当前这一轮已经废了，硬插进"下一步"没有下一步可插。

二是**取消时收件箱清不清**。`cancel(cause, options)`（`:815-821`）默认 `this.inbox.clear()`，但给了 `keepInbox` 选项：想保留用户排队的话、只中止当前这一轮，就传 `{ keepInbox: true }`。

{% mermaid %}
flowchart LR
  U["用户输入"] --> S{"send(target, wakeup)"}
  S -->|"followup"| Q1["inbox: next-turn"]
  S -->|"steer"| Q2["inbox: next-step"]
  S -->|"inject"| Q3["inbox: next-step, 不唤醒"]
  Q2 --> W{"agent 正被中止？"}
  W -->|"是"| Q1
  W -->|"否"| R["下一步请求前注入"]
  Q1 --> R2["本轮结束后开新轮"]
  Q3 --> R
{% endmermaid %}

一句话总结这段：**Pi 的插话是"循环问用户有没有话说"，DSH 的插话是"用户告诉循环该什么时候看"**。前者实现极简（一个回调、三个查询点），后者把"何时生效"变成了显式契约，代价是接口变多。

## 4. 压缩

上下文撑爆时的处理，是两套设计哲学分歧最刺眼的地方。

**Pi 的触发条件是绝对量**：`shouldCompact(contextTokens, contextWindow, settings)` 就一行——`contextTokens > contextWindow - settings.reserveTokens`（`packages/coding-agent/src/core/compaction/compaction.ts:267-269`），`reserveTokens` 默认 **16384**（`:128`）。也就是"给最后的回复留 16K，其余都能用"。

压缩的执行时机藏在 `prepareNextTurn` 里——就是第 3 节那个每轮开始前调用的回调。`agent-loop.ts:210` 的注释直接点名 `for example, compaction`。压缩结果写成会话里的一种条目 `type: "compaction"`（`core/session-manager.ts:92`），之后构造上下文时遇到它就知道"从这条往前的东西都被一段摘要替代了"（`:302`、`:374`、`:461`）。

**DSH 的触发条件是比例加两个预留**：`resolveCompactSpec()` 先算 `messageBudgetTokens = contextWindow - reservedCompletionTokens`，再算 `pressureBudgetTokens = messageBudgetTokens - policy.headroomTokens`，最后 `thresholdTokens = min(contextWindow * thresholdRatio, pressureBudgetTokens)`（`dsh-compaction-basic/lib/index.js:124-132`）。默认 `thresholdRatio = 0.8`（`:15`）、`headroomTokens = 65536`（`:63`）。三个数的含义是：**用掉 80% 就压；但无论如何要给回复留出 maxTokens、给突发留 64K 余量**。

更关键的是执行位置。DSH 的压缩挂在 `agent/pre-step` 这个 waterfall 上（`dsh-compaction-basic/lib/index.js:839`），超过阈值就 `agent.runMaintenance(...)`（`:988`）——**整个 agent 进入 `maintenance` 相位**，这期间新的一轮开不起来，压缩独占。压完的产物是"把选定的那段历史替换成一个摘要节点"，而且契约里专门规定了 `toolPairingBalancedBefore/After`（`dsh-compaction/lib/index.js` 导出）——**不许从工具调用与结果的中间切开**，否则下一条请求就是非法消息序列。

两边在这里的分野可以概括成一句话：

- Pi 的压缩是**对话内的一个条目**，位置由会话结构自己表达（"这里有个 compaction 标记"），压缩跑在轮次边界上，用户还能在它跑的时候插话（第 3 节那条注释就是为此写的）。
- DSH 的压缩是**一次独占的维护作业**，位置由"替换哪段 surface"显式指定，跑的时候这个 agent 不接受新一轮，但记录本身是原子的——要么整段被替换，要么完全没有发生。

代价也对称：Pi 的模型更轻，但"压缩正在进行"这件事对调用方是隐式的（只是 `prepareNextTurn` 慢了点）；DSH 的重，但外部能看见 `status: idle/running` 之外的一段 `maintenance`，UI 上可以老实显示"正在整理上下文"。

## 5. 内部消息怎么变成供应商能吃的格式

两边的内部消息都比"供应商消息"富：Pi 有 `bashExecution`、`custom`、`branchSummary` 这些只在 Pi 内部存在的角色；DSH 有 `developer` 角色、`tool-addition` 块、图片/文件引用、被 offload 的大图。把它们变成某家 API 能吃的 `messages`，是每次请求都要过的关。

**Pi 是一个函数。** `convertToLlm(messages: AgentMessage[]): Message[]`（`packages/coding-agent/src/core/messages.ts:148`）纯函数式地把每种内部消息映射成一个标准 `Message`：`bashExecution` 变成一段 user 文本（还顺手实现了 `!!` 前缀的"不进上下文"语义）、`custom` 变成 user 内容、`branchSummary` 包上前缀后缀变成 user 文本。agent 层只在每次请求前调它一次：`const llmMessages = await config.convertToLlm(messages)`（`agent-loop.ts:404`），注释还写着"每个 turn 只调一次，所以这里没法校验"（`:77-78`）。

它的契约只有一句，但很硬：`convertToLlm` **`must not throw or reject. Return a safe fallback value instead.`**（`packages/agent/src/types.ts:222`）。意思是转换层是"绝不会失败的降级层"，宁可把一个奇怪的内部消息变成一句占位文本，也不许在请求路径上抛异常。

供应商特定的 shaping（Anthropic 的 thinking 块、OpenAI 的 reasoning 字段、Google 的 schema 限制）**不在这里做**，而在 `pi-ai` 的 43 个 api 实现里各自处理——`convertToLlm` 只负责"内部 → 通用"，"通用 → 某家 wire"是另一层。

**DSH 是一条投影流水线。** `LlmRuntime.stream()` 在派发给 adapter 之前，依次做三次投影（`dsh-llm/lib/index.js:2335-2338`）：

1. 有文件引用 → `projectFilesToText()` 把文件摊成文本；
2. 模型 `inputModalities` 里没有 `image` → `projectImagesForTextModel()` 把图片降级成文字描述（`offloadedImageText` / `textOnlyImageText` 那一族）；
3. 工具变更 → `projectToolUpdates()`（第 2 节）。

然后才交给 `LlmAdapter` 的实现（`dsh-llm-deepseek` 或 `dsh-llm-pi-ai`）去变成真正的 wire 格式。而且消息在离开循环时就被**冻结**了：`buildRequest` 里 `deepFreeze(header)`、对每条 boundary message 做 `deepFreeze` 并记进 `frozenMessages` WeakSet（`dsh-agent-loop/lib/index.js:1264-1271`）——之后任何一层想改消息都改不动。

{% mermaid %}
flowchart LR
  subgraph PI2["Pi"]
    I1["AgentMessage<br/>bashExecution / custom / branchSummary"] --> C1["convertToLlm()<br/>纯函数，绝不抛错"]
    C1 --> C2["Message<br/>通用"]
    C2 --> C3["pi-ai 的 api 实现<br/>43 个，各自 shaping"]
  end
  subgraph DSH2["DSH"]
    I2["Session 派生的消息<br/>developer / tool-addition / 图片引用"] --> P1["projectFilesToText"]
    P1 --> P2["projectImagesForTextModel<br/>按 inputModalities"]
    P2 --> P3["projectToolUpdates<br/>按路由能力"]
    P3 --> P4["LlmAdapter<br/>deepseek / pi-ai"]
  end
{% endmermaid %}

这个差别的实际影响是**可替换性**。Pi 想加一家供应商，只要在 `pi-ai` 里写一个 api 实现——`convertToLlm` 不用动。DSH 想加一家，除了写 adapter，还得回答"这条路由的 `toolUpdate` 是什么、支不支持图片、要不要降级"——能力矩阵是显式的，代价是每接一家都要填一张表。

顺便一提，DSH 里有一个包叫 `dsh-llm-pi-ai`——**它把 Pi 的 `pi-ai` 当作自己的 provider 层来用**。也就是说，同一套 Pi 供应商代码，在 Pi 里是"我的 api 层"，在 DSH 里是"我的 adapter 实现之一"。这件事本身就是对第 5 节最好的注解：两家在"通用消息 → wire"这一层的边界划得不一样，以至于一家的通用层可以直接嵌进另一家的专用层。

## 6. 中止

用户按 Esc（或父 agent 被取消、或进程要退出）时，最危险的不是"停下来"，而是**停在半路**：三个工具并发执行，两个已经改了文件、第三个还在跑，会话记录里到底该记什么？下次恢复时这条记录还能不能重放？

**Pi 靠 signal 检查 + 合成结果。**

`signal: AbortSignal | undefined` 一路传到每个执行函数里。开始执行工具前查 `signal?.aborted`（`agent-loop.ts:585`、`:623`），已经开始执行的在结束时再查（`:630`），被中止的那一批里没跑的工具直接合成一个错误结果：

```text
result: createErrorToolResult("Operation aborted")
```

（`:633`、`:751`、`:770`）——**保证"每个工具调用都有对应的结果消息"这条不变量**，因为下一轮请求时，一个只有调用没有结果的历史会被供应商直接判非法。

然后助手消息的 `stopReason` 是 `"aborted"` 时，循环把这一轮当作完成收尾：`turn_end` → `agent_end` → 返回（`:254-262`）。

**DSH 靠 cancel cause + 显式收尾。**

取消的入口是 `cancel(cause, options)`，`cause` 是一个封闭联合：`{kind: "user"} | {kind: "parent"} | {kind: "disposed"} | {kind: "hook", reason}`（`dsh-agent-loop/lib/index.js:731-748`）。四种来源意味着四种不同的下游处理：用户取消可以重试、父 agent 取消要级联、进程销毁不要试图写盘、hook 取消要保留原因。这些信息最后会被写进 `turn/end`，而且代码里专门做了"只拷贝能进 JSON 的字段"的处理，因为 `AbortSignal.reason` 上会被 Node 的 fetch 挂一个 `stack` 属性，直接进 `Session.append` 会被当成不可序列化的数据拒掉（`:725-729` 的注释写得很细）。

工具侧的约定写在循环顶部的文档注释里（`:479-491`）：**中止会停止发起新工具、把已发起的跑完、然后为被跳过的调用提交合成失败结果——这样重放仍然一致**。合成结果长这样（`:665-676`）：

```json
{"text": "Error: tool call aborted before dispatch", "isError": true, "name": "AbortError"}
```

跟 Pi 的 `"Operation aborted"` 是同一个思路的两种说法：**中止不是"什么都没发生"，而是"发生了一次可记录的失败"**。差别在于 DSH 把它写成了有类型的合成事件（还带 `sourceEventSeqs` 指回原始调用），Pi 只保证结果消息存在。

## 7. 重试：是把决定记下来再等，还是等完再说

供应商 429、网关 502、流到一半断了——重试几乎是每套 agent 的标配，但"重试这件事记不记账"分出了又一处分歧。

**Pi 把重试包在"产生一条助手消息"这件事外面。** `retryAssistantCall(produce, policy, signal, callbacks)`（`packages/ai/src/utils/retry.ts:207`）的契约是：成功立刻返回；`stopReason === "aborted"` 是终态、**永不重试**（就算中止发生在退避睡眠途中，也会被归一成一条 aborted 消息，调用方不需要关心取消发生在哪一步，`:199-206`）；非重试错误（含额度/欠费）立刻返回，快速失败；其余按 `maxRetries` 指数退避，并在三个位置抛出回调 `onRetryScheduled` / `onRetryAttemptStart` / `onRetryFinished`（`:214-218`），让上层能显示"正在重试第 2 次"。

对主循环来说，重试是**透明的**：`streamAssistantResponse` 拿到的永远是"一条最终的 assistant 消息"，重试了几次它不关心。

**DSH 把重试做成日志里的一件事。** `dsh-llm-retry` 的模块注释只有一句，但信息量很大：

> Each scheduled retry is durable before its cancellable wait.

（`dsh-llm-retry/lib/index.js:16-17`）——**每一次"打算重试"的决定，都在开始等待之前先落盘**。它挂在主循环的 `agent/request-error` 扩展点上（也就是第 3 节里 `kick` 那条恢复链），退避是带抖动的指数退避：`initialDelayMs * 2^(retry-1)` 封顶 `maxDelayMs`，再乘 `1 - jitterRatio + 2 * jitterRatio * random()`（`localDelay`，`:44-49`）。策略必须配在**每个 provider 下面**（`:28` 明确禁止把它写在顶层），并用 `retryPolicyKey()` 把策略序列化成一个稳定身份（`:50-60`），这样同一条重试链在日志里能被认出来。

差别在崩溃边界上最明显：**Pi 的重试被打断，就只是一次 aborted；DSH 的重试被打断，恢复后知道自己欠一次重试**。前者简单，后者在"跑一整夜的长任务"里更靠谱。这也解释了为什么 DSH 把重试做成一个可插拔的扩展点（`agent/request-error` 是 waterfall，谁都可以接管），而 Pi 把它写死在 `retry.ts` 里、只留一个 `RetryPolicy` 配置口。

## 8. 顺带看两个维度

**并发调度。** Pi 的策略是"整批一致"：一批工具调用里只要有一个声明了 `sequential`，整批就走串行（`agent-loop.ts:526-532`）；否则并行。内置工具基本不声明，所以默认并行，写冲突靠按文件的串行队列（`withFileMutationQueue`）兜住——**不同文件仍然并行**。

DSH 是一个真正的调度器：`maxParallelToolCalls` 控制窗口（`:619`），`executionMode(call)` 逐条决定能否进并发组，遇到非并行工具就断开当前组、开始新组（`:621`）。而且它是"边跑边补"的（`replenishment`，`:479` 那段注释），不是先切好批再跑。

**状态落盘。** Pi 的会话是树（第 3 篇讲过），压缩、分支摘要都是树上的节点。DSH 的会话是**事件日志**：每一次请求头变化、每一条开发者消息、每一个工具结果，都是日志里一条带 seq 的事件，消息由 `session.deriveMessages()` 从日志现推（`dsh-agent-loop/lib/index.js:1265`）。

这个差别决定了恢复语义：Pi 恢复靠"重放树到某个节点"，DSH 恢复靠"重放到最后一个 commit"。DSH 的代价是日志只增不减（要靠压缩把它变短），收益是**任何时刻的状态都能由日志唯一确定**——包括"当时工具集合是什么""当时是哪条路由"。

## 9. 一张对照总表

| 维度 | Pi | DSH |
|---|---|---|
| 循环形状 | 两层 `while`，条件是布尔量（`agent-loop.ts:171`、`:192`、`:305`） | `while (await turn())` + 相位状态机 idle/running/maintenance（`index.js:889`、`:791`） |
| 工具集合变更 | diff 后插一条 system 消息盖章（`:342-372`） | 记 `request/header change` + `developer/message`，再按路由 `toolUpdate` 投影（`:1240-1258`、`dsh-llm:786`） |
| 运行时插话 | 三个轮询点拉 `getSteeringMessages()`（`:184`、`:210`、`:219`） | inbox + `followup/steer/inject` 三种投递语义（`:806-812`） |
| 中止后的插话 | 无特殊处理（循环已退出，靠外层重开） | 自动降级为 `next-turn`（`:801-804`） |
| 压缩触发 | `contextTokens > window - 16384`（`compaction.ts:267-269`） | `min(window*0.8, window-reserved-65536)`（`compaction-basic:124-132`） |
| 压缩执行 | `prepareNextTurn` 轮次边界，可与插话交错 | `agent/pre-step` → `runMaintenance` 独占相位（`:839`、`:988`） |
| 压缩产物 | 会话里一个 `type:"compaction"` 条目 | 原子替换一段 surface + 摘要节点，强制工具配对平衡 |
| 消息转换 | 单个纯函数 `convertToLlm`，绝不抛错（`messages.ts:148`） | 三级投影 + adapter（`dsh-llm:2335-2338`） |
| 消息可变性 | 普通对象，转换时现算 | 出循环即 `deepFreeze`，WeakSet 记账（`:1273-1279`） |
| 中止语义 | `AbortSignal` + 合成 `"Operation aborted"` 结果 | 封闭 `cause` 联合 + 合成 `AbortError` 结果 + 记 seq |
| 工具并发 | 批内一致：有一个串行就整批串行 | 调度器逐条判定，窗口 + 分组 |
| 状态真相 | 会话树 | 只增事件日志 |

## 10. 两种世界观

把上面每条差异摆在一起看，会发现它们朝同一个方向倒：

**Pi 认为"对话就是全部真相"。** 工具集合的变化做成消息、压缩做成会话里的一个条目、转换是一个纯函数、插话是循环主动去问——所有东西最终都能落到"这条对话里发生了什么"。好处是心智负担极小：任何时刻你只要把 transcript 摊开，就能知道模型看见了什么。代价是有些信息只能"表达进对话"，比如"这条路由不支持图片"这种事没法写进历史，只能在调用时临时投影。

**DSH 认为"日志就是全部真相"。** 请求头、路由、工具清单、压缩、取消原因，全都是事件日志里的记录，消息只是日志的一个投影。好处是任何状态都可追溯、可重放、可审计，而且同一条会话可以在能力不同的路由之间迁移（因为"能力"是投影时才用的参数，不是历史的一部分）。代价是层数多：改一个工具列表要经过记账、投影、adapter 三道门。

没有哪边更"对"。如果你在写一个**给人用的终端 agent**，Pi 那套轻量结构能让你两周内跑起来；如果你在写一个**要托管、要多端、要审计**的 agent 平台，DSH 那套日志优先的投影结构会让后面每一个需求都省力一点。

真正值得抄的是两边都做了、而且做得很坚决的那一条：**中止不是"停下来"，是"记录一次失败并保持一致"**。Pi 合成 `"Operation aborted"`，DSH 合成 `"tool call aborted before dispatch"`——不管哪种，下一轮请求拿到的历史都是合法的。这一条比循环长什么样重要得多。

## 相关阅读

- [Pi 的 Agent Loop：一次请求转几圈，它凭什么知道该停了](/2026/11/05/Pi-Loop/)
- [DSH Agent 主循环：一次请求转几圈](/2026/10/30/DSH-Agent%E4%B8%BB%E5%BE%AA%E7%8E%AF/)
- [Pi 的上下文工程：每次请求，模型到底看到了什么](/2026/11/05/Pi-%E4%B8%8A%E4%B8%8B%E6%96%87/)
- [DSH 上下文装配全解：一次模型请求到底是怎么拼出来的](/2026/10/30/DSH-%E4%B8%8A%E4%B8%8B%E6%96%87%E8%A3%85%E9%85%8D%E5%85%A8%E8%A7%A3/)
- [DSH 会话压缩策略详解](/2026/10/30/DSH-%E4%BC%9A%E8%AF%9D%E5%8E%8B%E7%BC%A9%E7%AD%96%E7%95%A5%E8%AF%A6%E8%A7%A3/)
