---
title: DSH 会话压缩（Compaction）策略详解：阈值、剪裁、摘要与落盘
date: 2026-10-30 16:30:00
tags: [Agent, DeepSeek, Context]
categories: [Agent]
cover: /images/DSH-会话压缩策略详解/cover.jpg
---

长会话逼近上下文上限时，Agent 该怎么自救？这篇文章按 DSH（DeepSeek Harness）当前仓库 `packages/compaction/` 的实现，说明它"什么时候压、先做什么、怎么压、压完在磁盘上长什么样"。

涉及的主要源码：

| 位置 | 职责 |
|---|---|
| `packages/compaction/compaction` | 能力接缝：`ctx.compaction` 服务定义、工具调用配对检查、checkpoint 构造器 |
| `packages/compaction/compaction-basic` | 自动压缩后端：阈值、保留尾部、摘要调用、事务写入 |
| `packages/compaction/compaction-tool-result-pruner` | 确定性 tool result 剪裁（`ctx.toolResultPruner`） |
| `packages/compaction/command-compact` | `/compact` 手动命令 |
| `packages/llm/token-meter` | token 计量：请求压力与 surface 逐节点定价 |
| `packages/session/*` | 会话日志、surface 投影、JSONL 持久化 |

---

## 1. 一张图看懂

{% mermaid %}
flowchart LR
    subgraph Loop["Agent Loop"]
        PS["agent/pre-step<br/>（每个 step 一次）"]
        RE["agent/request-error<br/>（provider 报超窗）"]
    end

    CMD["/compact 命令"] --> C

    PS --> C["compaction-basic<br/>compactIfNeeded"]
    RE --> C
    C --> M["ctx.tokenMeter<br/>压力测量"]
    C --> P["ctx.toolResultPruner<br/>确定性剪裁"]
    C --> L["ctx.llm.stream<br/>一次性摘要调用"]
    C --> S[("Session JSONL<br/>只追加事件")]
    CMD --> C2["compaction-basic<br/>compactNow"]
    C2 --> L
    C2 --> S
    C2 --> M
{% endmermaid %}

一句话概括策略：

> **先量压力，超阈值才动手；动手时先做不花钱的剪裁，剪完还超才调用模型摘要；摘要必须比被替换的内容更小；整个过程以一对加锁事件写入只追加日志，旧内容不删除、只从可见 surface 中遮蔽。**

---

## 2. 三个触发入口

压缩不是 agent-loop 主循环的一部分，而是挂在扩展点上的可选能力。

| 入口 | 事件/命令 | 触发条件 | 是否判断阈值 | 是否先剪裁 | 尾部保留 |
|---|---|---|---|---|---|
| 自动压力压缩 | `agent/pre-step` | 每个 step（每次模型请求）开始时 | 是 | 是 | `retainRatio`（默认 16%） |
| 溢出恢复 | `agent/request-error` | provider 返回 `CONTEXT_WINDOW_EXCEEDED` | 否（必然执行） | 是 | 0（只保最后一条） |
| 手动压缩 | `/compact` 命令 | 用户显式调用，要求 agent 空闲 | 否 | 否 | 0（只保最后一条） |

关键点：

- `agent/pre-step` 是**每个 step** 触发，不是每个 turn。一个 turn 内的每次工具调用后续都会重新判断一遍。
- 新会话第一次请求前还没有 `request/header`，拿不到 route，`compactIfNeeded` 直接返回 `null`。
- 自动压力压缩失败不会中断本轮：异常被捕获后记 warning，继续执行（`compaction-basic/src/index.ts:148`）。

---

## 3. 压力路径的完整流水线

{% mermaid %}
flowchart TD
    A["agent/pre-step"] --> B{"session 有 request/header?"}
    B -- 否 --> Z["return null（不判断）"]
    B -- 是 --> C["measure(session)"]
    C --> D{"totalTokens >= contextWindow × 0.8 ?"}
    D -- 否 --> Z
    D -- 是 --> E{"挂载了 toolResultPruner?"}
    E -- 是 --> F["pruneSession()"]
    F --> G["重新 measure"]
    G --> H{"仍 >= 阈值?"}
    H -- 否 --> Y["结束：只剪裁，不摘要"]
    H -- 是 --> I["选区间：保留 16% 尾巴<br/>+ 工具配对平衡"]
    E -- 否 --> I
    I --> J{"选到区间?"}
    J -- 否 --> Z2["return null"]
    J -- 是 --> K["摘要调用 + 事务写入"]
    K --> L["重新 measure"]
    L --> M{"低于阈值?"}
    M -- 是 --> X["返回 CompactionResult"]
    M -- 否 --> N{"还有重试次数?<br/>compactionRetries 默认 1"}
    N -- 是 --> I
    N -- 否 --> ERR["抛错：仍高于阈值<br/>pre-step 记 warning，本轮继续"]
{% endmermaid %}

阈值来自 `resolveCompactSpec()`（`compaction-basic/src/config.ts:133`）：

```
thresholdTokens = floor(contextWindow × thresholdRatio)   // 默认 0.8
retainTokens    = floor(contextWindow × retainRatio)      // 默认 0.16，可被 retainTokens 覆盖
```

`contextWindow` 由 `ctx.llm.resolveModelInfo(provider, model)` 提供，是**适配器声明的模型容量**。拿不到容量会抛 `TargetPressureConfigError`，同类目标只警告一次。

---

## 4. 计量底座：tokenMeter 与 surface

### 4.1 日志与 surface 是两回事

- **会话日志**：只追加的 JSONL 事件流，永不修改、永不删除。
- **surface**：从日志投影出来的"当前模型可见消息序列"。`compaction/start` 之类事件不产生消息；带 `surfaceOp: replace` 的消息会顶替旧节点。

tokenMeter 在内部维护一个增量 fold（`packages/llm/token-meter/src/index.ts:218`）：

```ts
while (state.consumedEvents < session.seq) {
  this._foldEvent(state, eventAt(consumedEvents))
  state.consumedEvents += 1
}
```

每条 surface 事件都会：

1. `deriveEventMessage(event)` 翻译成一条 `Message`；
2. `analyzeNode()` 估算该消息 token 并记录图片/文件附件；
3. 按 `surfaceOp` 追加到尾部，或 `splice` 掉旧区间插入新节点（`surface-fold.ts:114-149`）。

得到的"计价状态"是：当前 surface 的**有序节点数组**，每个节点带 `seq / tokens / heuristicTokens / 附件`，外加最近一次请求头与 usage 锚点。

### 4.2 为什么这样设计

| 需求 | 这个设计的回答 |
|---|---|
| 每个 step 都要判断，必须便宜 | 增量 fold：只处理新增事件；`measure()` 主要开销是 O(可见消息数) 的定位与克隆 |
| 压缩必须真的降低压力 | 只有 surface 投影正确，`replace` 后总量才会下降；按日志原文算永远降不下来 |
| 尽量用真实用量 | 上一次成功请求返回的 `usage` 可作为基准，再叠加上之后的 surface 增量；不匹配或偏小时退回启发式估算 |
| 多处使用同一份数字 | 阈值、选区、摘要缩小校验、剪裁影子定价、UI 用量条全部读同一个 fold |
| 重放可复现 | `measure()` 返回冻结快照，从 JSONL 重放能得到与当时一致的结果 |

### 4.3 定价的两种口径

- `tokens`（路由价）：按当前路由模型真正发送的形态计价，图片按模型声明的视觉价格。**阈值判断、尾部保留、区间定价都用它。**
- `heuristicTokens`（固定启发式）：与路由无关的保守估算。**影子计价协议用它**，保证 O(1) 投影 fold 与自身追加的事件一致。

---

## 5. 第一步：确定性剪裁 tool result

实现在 `compaction-tool-result-pruner/src/index.ts`。这是**纯本地、不调用模型**的操作，所以放在摘要之前。

{% mermaid %}
flowchart LR
    A["tool result 内容"] --> B{"累计 code point > 8192?"}
    B -- 否 --> Z["保持不变"]
    B -- 是 --> C["保留头部 4096 字符"]
    C --> D["插入标记<br/>[... tool result middle pruned ...]"]
    D --> E["保留尾部 1024 字符"]
    E --> F["其余文本块按原顺序保留"]
{% endmermaid %}

默认参数（`compaction-tool-result-pruner/src/config.ts:10`）：

```
thresholdChars = 8192   // 超过才剪
headChars      = 4096   // 保留开头
tailChars      = 1024   // 保留结尾
```

细节：

- 只统计 `text` 块；图片等富内容块原样保留且不打乱顺序。
- 按 **Unicode code point** 切片（`Array.from`），不会劈开代理对；grapheme cluster 仍可能被切开。
- 加载时校验 `headChars + marker + tailChars <= thresholdChars`，保证一次剪裁必能落到阈值内。
- 每个被剪的 tool result 会追加两条事件：先 `compaction/prune`（影子计价，记录被遮蔽节点的价格），再 `tool/result` 替换节点，带 `surfaceOp: {op:'replace', start: seq, end: seq}`。
- 剪裁后的内容必然 ≤ 阈值，下一轮不会再被剪。

注意：剪裁的是 **tool result 的内容**，不是工具定义（schema）。工具定义只参与计量，不参与剪裁。

---

## 6. 第二步：选可压缩区间

`selectCompactableRange()`（`compaction-basic/src/region.ts:100`）只读，不改任何状态。

{% mermaid %}
flowchart TD
    A["从头到尾的 surface 节点与路由价"] --> B["从尾部向前累加 token"]
    B --> C{"累计 >= retainTokens?"}
    C -- 否 --> B
    C -- 是 --> D["得到保留尾巴起点 keepFromIdx"]
    D --> E{"keepFromIdx == 0?"}
    E -- 是 --> Z["无可压区间，返回 null"]
    E -- 否 --> F{"keepFromIdx 之前的切口<br/>工具配对平衡?"}
    F -- 否 --> G["keepFromIdx 前移一位<br/>（多保留一些尾巴）"]
    G --> F
    F -- 是 --> H["压缩区间 = [surface[0], surface[keepFromIdx-1]]"]
{% endmermaid %}

三个约束：

1. **从头锚定**：`start` 永远是 surface 的第一条可见节点。
2. **保留尾部**：从尾部往前累计到至少 `retainTokens`，最近一段对话保持原文。
3. **不切断工具配对**：切口处累计未闭合 tool-call 数必须为 0。

工具配对判断（`compaction/src/tool-pairing.ts`）是一个增量折叠：

```
assistant/message 中每个 tool-call 块 → +1
tool/result                          → -1
其他事件                              →  0
```

某个切口处计数为 0 即平衡。计数为负说明出现无对应调用的结果，直接判定 surface 损坏。fold 结果按 `WeakMap<Session, BalanceCache>` 缓存，以 `replaceGeneration` 作废，正常只对新追加的尾部做增量。

最终 `compactSurfaceRegion()` 还会再次校验两个边界：`start` 之前和 `end` 之后都必须平衡，否则拒绝。

因此：**允许切在 turn 中间**（一个超大 turn 里较早关闭的 step 可以被压掉），**不允许切穿一个 tool-call/result 组**。

示意（`[ ]` 为可见节点，竖线为切口）：

```
[user][assistant+2 calls][result][result][user][assistant] ...
        ↑ 不平衡：切口会切断调用组          ↑ 平衡
```

---

## 7. 第三步：摘要调用

`summarizeWithLlm()`（`compaction-basic/src/summarizer.ts:121`）发一次 `ctx.llm.stream()`。

### 7.1 复用 KV cache 的请求构造

摘要请求不是"另起一个摘要专用 conversation"，而是把原对话的前缀原样重放，再把压缩指令作为最后一条 user 消息追加：

{% mermaid %}
flowchart LR
    S["system<br/>（原会话的系统提示）"] --> T["tools<br/>（原会话的工具定义）"]
    T --> M["messages<br/>（被压缩区间的消息，按 surface 顺序）"]
    M --> I["compaction instruction<br/>（唯一的新增输入）"]
    I --> R["路由模型"]
{% endmermaid %}

这样前缀与上一次真实请求一致，provider 的 KV cache 可以命中；只有末尾指令是新的。

### 7.2 摘要输出格式

指令要求输出固定小节结构的 Markdown：Primary Request and Intent / Key Technical Concepts / Files and Code / Errors and Fixes / Pending Jobs / Current Work / Next Step / Critical Context。并明确要求保留精确路径、命令、错误串、标识符与数值；不得提及"压缩"本身；若输入里已有 `<compacted-summary>` 块（先前 checkpoint），要合并而非原样抄写。

### 7.3 目标模型选择

顺序（`summarizer.ts:128`）：

1. 配置里的 `summarizationProvider` / `summarizationModel`（成对出现）；
2. 会话日志里最近一次 `request/header` 的 provider/model；
3. `agent.options` 的 provider/model。

输出上限 `maxTokens` 默认 8192。`finish` 为 `error` / `aborted` / `max-tokens` 都会抛错——被截断的 checkpoint 视为失败，不会写入。

### 7.4 摘要必须更小

```ts
framedSummaryTokenCount = meter.estimateMessage(checkpointMessage)
if (framedSummaryTokenCount >= shadowedRouteTokenCount) throw ...
```

见 `region.ts:384`。用"带框架的替换消息"对比"被遮蔽区间的路由总价"，防止出现"压完反而更大"的情况。

---

## 8. 事务、锁与失败语义

{% mermaid %}
sequenceDiagram
    participant L as Agent Loop
    participant C as compaction-basic
    participant S as Session
    participant M as tokenMeter
    participant LLM as 路由模型

    L->>C: pre-step / request-error
    C->>M: measure()
    C->>S: 读取 surface，校验区间与配对
    C->>S: append compaction/start（加锁）
    Note over S: 锁从此刻起生效
    C->>M: prepareCompaction（快照定价）
    C->>LLM: stream(system + tools + 区间消息 + 指令)
    LLM-->>C: summary blocks
    C->>C: 校验摘要更小
    alt 成功
        C->>S: append compaction/summary
        C->>S: append user/message（surfaceOp replace）
        C->>S: append compaction/end（解锁）
    else 失败
        C->>S: append compaction/end（记录 error）
    end
{% endmermaid %}

要点：

- `compaction/start` 与后续异步工作是**同步相邻**的，因此它本身就是锁：任何入口看到"有 start 没 end"都会判定 busy。
- 释放锁放在最后：崩溃会留下孤儿 `start`，这比"end 已写但其实没压完"安全。出现更新的 `session/end-seed` 时，之前未匹配的 start 视为上一个生命周期，可忽略。
- 失败时仍会尽力写一条带 `error` 的 end 事件；写入失败则保留孤儿 start，供下次检测。
- 自动路径的失败只记 warning，本轮继续；溢出路径的失败在有持久 surface 进展时仍允许重试一次。
- 手动路径把失败映射为 `ManualCompactionError`：`busy / cancelled / changed / summary / commit / persistence`。

### 8.1 并发与稳定性

- 自动路径要求"整条 surface 在摘要期间不变"（`assertWholeSurfaceUnchanged`），否则放弃这次结果。
- 手动路径只要求"选中的那段区间不变"（`assertSelectedSpanStable`），期间注入的无关上下文可以保留在区间之外。

---

## 9. 落盘：JSONL 长什么样

压缩不删日志，只追加。一次成功的摘要压缩写入四条事件：

```jsonl
{"type":"compaction/start","data":{"compactionId":"<id>","turn":1}}
{"type":"compaction/summary","data":{
  "compactionId":"<id>",
  "summary":[{"type":"text","text":"..."}],
  "rawOutput":[{"type":"text","text":"..."}],
  "llmStreamCall":true,
  "shadowedRange":{"start":7,"end":8},
  "shadowedSeqs":[7,8],
  "shadowedTokenCount":372,
  "provider":"deepseek-official","model":"deepseek-v4-flash",
  "maxTokens":32,
  "usage":{"inputTokens":20,"outputTokens":4}}}
{"type":"user/message","data":{
  "content":[
    {"type":"text","text":"This is an automatically generated checkpoint ... <compacted-summary>"},
    {"type":"text","text":"<摘要正文>"},
    {"type":"text","text":"</compacted-summary>"}],
  "source":{"kind":"plugin","plugin":"compact","compactionId":"<id>"},
  "role":"user","id":"<msg>"},
 "sourceEventSeqs":[18,19,7,8],
 "surfaceOp":{"op":"replace","start":7,"end":8}}
{"type":"compaction/end","data":{"compactionId":"<id>","turn":1}}
```

字段含义：

| 字段 | 作用 |
|---|---|
| `compactionId` | 整次事务的稳定标识，把 start / summary / 替换消息 / end 串起来 |
| `shadowedRange` | 被替换的 **surface 位置对**（不是数字 seq 区间；先前压缩过时 `start` 可能大于 `end`） |
| `shadowedSeqs` | 被遮蔽节点的全部 seq，按 surface 顺序，权威集合 |
| `shadowedTokenCount` | 被遮蔽内容的启发式 token 数（影子计价口径） |
| `provider` / `model` / `maxTokens` / `usage` | 摘要调用信封，配合代码即可重建这次请求 |
| `rawOutput` + `llmStreamCall: true` | 证明摘要恰好通过本上下文的 `ctx.llm.stream()` 调用了一次 |
| `sourceEventSeqs` | 开始事件、摘要事件与被遮蔽节点的 seq，供重放回溯输入 |
| `surfaceOp: {op:'replace'}` | 投影指令：用这条消息顶替指定区间 |

剪裁路径则是两条一组：

```jsonl
{"type":"compaction/prune","data":{"shadowedRange":{"start":12,"end":12},"shadowedSeqs":[12],"shadowedTokenCount":900}}
{"type":"tool/result","data":{... 被截断的内容 ...},"sourceEventSeqs":[12],"surfaceOp":{"op":"replace","start":12,"end":12}}
```

`compaction/prune` 是影子计价事件，紧贴在替换之前，让纯消费者可以 O(1) 地从总量里减掉被遮蔽节点的价格，不需要维护逐节点状态。

---

## 10. 重放：下次启动怎么恢复

从 JSONL 按序重放，即可重建完全相同的 surface：

{% mermaid %}
flowchart LR
    J["JSONL 事件"] --> F["fold：逐条 deriveEventMessage"]
    F --> A{"surfaceOp?"}
    A -- append --> P["push 到 surface 尾部"]
    A -- replace --> R["splice 掉旧区间，插入新节点"]
    P --> O["当前可见 surface"]
    R --> O
    O --> T["tokenMeter 定价"]
    T --> Q["阈值 / 选区 / UI 用量"]
{% endmermaid %}

于是：

- 被遮蔽的原文虽然还在文件里，但不会再发给模型；
- 加载后第一次 `measure()` 折一遍全量，之后都是增量；
- 快照测试可以 keyless 重放，得到与录制时一致的 token 数。

---

## 11. 参数速查

`compaction-basic` 配置（cordis.yml 中插件 `config`）：

| 键 | 默认值 | 含义 |
|---|---|---|
| `thresholdRatio` | `0.8` | 压力阈值占上下文窗口的比例 |
| `retainRatio` | `0.16` | 尾部原样保留比例（与 `retainTokens` 互斥） |
| `retainTokens` | 未设置 | 尾部保留的绝对 token 数 |
| `compactionRetries` | `1` | 单次判断内最多额外重试次数 |
| `maxOverflowRetries` | `1` | 溢出恢复最多重试次数 |
| `maxTokens` | `8192` | 摘要输出上限 |
| `summarizationProvider` / `summarizationModel` | 空 | 空则跟随当前路由 |
| `modelPolicies[]` | — | 按 `provider` / `model` 覆盖上述参数 |
| `auto` | `true` | 是否注册自动触发 |

`compaction-tool-result-pruner` 配置：

| 键 | 默认值 | 含义 |
|---|---|---|
| `thresholdChars` | `8192` | 超过该字符数才剪 |
| `headChars` | `4096` | 保留开头字符数 |
| `tailChars` | `1024` | 保留结尾字符数 |

加载期校验：`retainRatio < thresholdRatio`、`headChars + marker + tailChars <= thresholdChars`、`modelPolicies` 不允许重复目标、未知键直接报错。

---

## 12. 设计取舍与已知限制

**为什么先剪裁再摘要？**

剪裁是纯本地、确定性的，零模型成本。很多情况下一次剪裁就能把压力降回阈值以下，直接省掉一次摘要调用；即使仍需摘要，输入也更小。

**为什么摘要必须更小？**

避免"压缩了但下一次请求更大"的死循环。校验对象是带框架的替换消息，比较基线是区间的路由总价。

**为什么允许切在 turn 中间？**

一个 turn 可能包含大量工具调用；如果只允许在 turn 边界压缩，单个超大 turn 永远无法自救。边界约束落在工具调用配对，而不是 turn 边界。

**为什么日志不删除旧内容？**

- 可重放、可审计：任何时刻都能还原当时模型看到的内容；
- 崩溃安全：只追加，没有原地修改；
- 兼容性：日志格式按"后继版本"演进，旧代内容保持原样。

**限制**

- 单个超大保留单元（一条巨大的消息或巨大的 tool result 剪完仍超阈值）无法靠 surface 压缩解决；
- 请求信封本身过大（系统提示 / 工具定义占满窗口）也不在压缩能力范围内；
- 未挂载 `ctx.toolResultPruner` 时，压缩退化为"直接摘要"；
- 手动 `/compact` 不剪裁，只做摘要压缩。
---

**相关阅读**：

- [DSH 上下文装配全解](/2026/10/30/DSH-上下文装配全解/)——被压缩改写的那个"上下文"，一开始到底是怎么在一次请求里被装配出来的。
- [DSH Agent 主循环：一条用户消息的完整旅程](/2026/10/30/DSH-Agent主循环/)——把这些零件转起来的那台发动机：轮次、步骤、工具池与取消。
- [DSH 沙箱设计：一次 bash 调用，到底被关进了什么](/2026/11/02/DSH-沙箱设计/)——真正跑命令的时候，是谁按着闸刀：同世界围栏、三条缝与升级阶梯。
