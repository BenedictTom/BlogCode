---
title: ClaudeCode-OpenClaw-OpenCode 上下文管理
date: 2026-04-25 12:34:16
tags: [Agent]
categories: [Agent]
cover: https://free.picui.cn/free/2026/04/25/69eccad3e8440.png
---

## 前言

在使用 Claude Code、OpenClaw 和 OpenCode 等 AI 编程工具时，上下文管理是一个至关重要的话题。本文从**源码实现**角度，深入剖析这三个 Agent 的上下文管理机制，揭示它们设计上的本质差异。

三个项目都面临同一个核心矛盾：**LLM 上下文窗口有限，但对话历史会持续增长**。它们的解法在宏观上一致（LLM 摘要 + 规则裁剪），但在工程细节上各有取舍。

---

## 一、全局架构概览

### 1.1 三种压缩范式

```
opencode              OpenClaw              Claude Code
┌─────────────┐    ┌──────────────┐    ┌──────────────────┐
│  两阶段压缩    │    │ 多阶段分块摘要  │    │ 六层渐进式压缩     │
│ Prune + LLM  │    │ Split+Merge  │    │ Budget→Snip→MC   │
└─────────────┘    └──────────────┘    │ →Compact→API→CC  │
       │                  │            └──────────────────┘
  ┌────┼─────┐      ┌─────┼──────┐           │
  │    │     │      │     │      │      ┌────┼────────┐
Prune  LLM  Replay Split Sum  Merge   6层渐进式防御
旧工具  摘要  溢出   按Token 逐块  合并   每层独立触发
输出   生成  重放   分块  摘要  摘要   条件与处理逻辑
```

### 1.2 设计哲学对比

| 维度 | Claude Code | OpenClaw | opencode |
|------|-------------|----------|----------|
| 设计目标 | 极致优化、Cache 感知 | 鲁棒性、安全优先 | 简洁、易懂 |
| 压缩层级 | 六层渐进式 | 多阶段分块 + 降级 | 两阶段（Prune + LLM） |
| 触发策略 | 精确阈值 + 熔断器 | 动态预算 + 自适应比例 | Token 阈值 + 20K 缓冲 |
| 子 Agent 设计 | 两种模式（Fork/Standard） | 裁剪历史传递 | 全新 Session 隔离 |
| 记忆持久化 | 四层记忆架构 | 会话归档 | 依赖 MCP |

---

## 二、何时触发压缩？

### 2.1 opencode: Token 阈值 + 20K 缓冲区

opencode 的触发逻辑最简洁。每次 LLM 返回响应后，检查已用 token 是否到达上限：

```typescript
// packages/opencode/src/session/overflow.ts
const COMPACTION_BUFFER = 20_000

export function isOverflow(input) {
  if (input.cfg.compaction?.auto === false) return false

  const count = input.tokens.total ||
    (input.tokens.input + input.tokens.output +
     input.tokens.cache.read + input.tokens.cache.write)

  const reserved = input.cfg.compaction?.reserved ??
    Math.min(COMPACTION_BUFFER, maxOutputTokens(input.model))

  const context = input.model.limit.context  // 总上下文限制，如 200000
  const usable = input.model.limit.input
    ? input.model.limit.input - reserved
    : context - maxOutputTokens(input.model)

  return count >= usable  // 到达可用上限即触发
}
```

**触发链路**：LLM 响应完成 -> `processor.ts` 中 `finish-step` 事件 -> 调用 `isOverflow()` -> 设置 `ctx.needsCompaction = true` -> 终止当前流 -> 进入压缩流程。此外，当 LLM 返回 `ContextOverflowError` 时也会触发（被动兜底）。

### 2.2 OpenClaw: 动态上下文预算 + 自适应比例

OpenClaw 没有单一阈值，而是根据上下文窗口动态计算预算：

```typescript
// src/agents/compaction.ts
export const BASE_CHUNK_RATIO = 0.4    // 每次保留 40%
export const MIN_CHUNK_RATIO = 0.15    // 最少保留 15%
export const SAFETY_MARGIN = 1.2       // 20% 安全余量

// 自适应: 消息越大，保留比例越低
export function computeAdaptiveChunkRatio(messages, contextWindow) {
  const avgTokens = estimateMessagesTokens(messages) / messages.length
  const avgRatio = (avgTokens * SAFETY_MARGIN) / contextWindow
  if (avgRatio > 0.1) {  // 单条消息占上下文 >10%
    const reduction = Math.min(
      avgRatio * 2,
      BASE_CHUNK_RATIO - MIN_CHUNK_RATIO
    )
    return Math.max(MIN_CHUNK_RATIO, BASE_CHUNK_RATIO - reduction)
  }
  return BASE_CHUNK_RATIO
}
```

**特色**：除了溢出触发外，**生成子 Agent 时也会主动触发**裁剪（`pruneHistoryForContextShare`），将父 Agent 的历史裁剪到上下文窗口的 50% 以内再传递。

### 2.3 Claude Code: 精确阈值 + 熔断器

Claude Code 的触发最精密，有多层防护：

```typescript
// src/services/compact/autoCompact.ts
const AUTOCOMPACT_BUFFER_TOKENS = 13_000
const MAX_OUTPUT_TOKENS_FOR_SUMMARY = 20_000
const MAX_CONSECUTIVE_AUTOCOMPACT_FAILURES = 3  // 连续失败 3 次后停止

export function getAutoCompactThreshold(model) {
  const effectiveContextWindow =
    getContextWindowForModel(model) - MAX_OUTPUT_TOKENS_FOR_SUMMARY
  return effectiveContextWindow - AUTOCOMPACT_BUFFER_TOKENS
}
// 例: 200K 模型 -> 有效窗口 180K -> 触发阈值 167K tokens
```

**独特设计——熔断器模式**：如果压缩连续失败 3 次（同一错误类型），系统停止尝试，避免浪费 API 调用。这源于真实的线上教训——曾有 session 连续失败 3,272 次，每天浪费约 25 万次 API 调用。

**防递归机制**：压缩本身也调用 LLM，所以需要防止"压缩触发压缩"的死循环：

```typescript
// 当 querySource 是压缩/session_memory/context_collapse 时，跳过自动压缩
if (querySource === 'session_memory' || querySource === 'compact') return false
if (querySource === 'marble_origami') return false  // context collapse 系统
```

### 2.4 触发时机对比表

| 维度 | opencode | OpenClaw | Claude Code |
|------|----------|----------|-------------|
| **触发方式** | Token >= 可用上限 | 动态预算 + 自适应 | Token >= 有效窗口的 ~93%（约总窗口的 83%） |
| **安全缓冲** | 20,000 tokens | 20% 安全余量(1.2x) | 13,000 + 20,000 tokens |
| **被动触发** | ContextOverflowError | LLM 调用溢出 | prompt_too_long 错误 |
| **子 Agent 触发** | 不触发 | 主动裁剪到 50% | 不触发 |
| **防递归** | 模式标记(compaction) | 状态标记(compactionInFlight) | querySource 过滤 |
| **熔断保护** | 无 | 无 | 连续 3 次失败后停止 |
| **可禁用** | `compaction.auto = false` | 无配置 | `DISABLE_AUTO_COMPACT` 环境变量 |

---

## 三、Claude Code 六层渐进式压缩体系（2026 最新版）

这是本文的**核心内容**。Claude Code 的上下文管理不是单一策略，而是 **6 层递进式防御体系**，每一层都有独立的触发条件和处理逻辑。

**关键设计思想**：

- 前三层是**独立触发**的，不是"第一层不够才到第二层"，三层可以在同一个查询周期内**同时触发**
- 第四层是**条件式**，减去前三层已释放的 token 后，只有还不够时才启动
- 第五层是**服务端保险**，第六层是**终极手段**

### 3.1 第 1 层：Tool Result Budget（工具结果预算裁剪）

**一句话解释**：单个工具输出太大了？先按字数截断再说。

你可能没意识到，一个工具调用就能吃掉 10-20% 的上下文。跑个 `pytest` 输出 80,000 字符，来个 `grep -r` 搜索返回 60,000 字符。如果不在第一时间截断，后续每一轮 API 调用都要拖着这些庞大的工具输出一起发到服务器。

**触发条件**：单个工具结果 > 50K 字符（默认阈值）

**不同工具的上限不同**：

| 工具 | 上限 | 为什么 |
|------|------|--------|
| 默认 | 50,000 字符 | 系统默认上限 |
| Bash | 30,000 字符 | 命令输出通常更短，更早截 |
| Grep | 20,000 字符 | 搜索结果可以更精简 |
| FileRead | ∞（不限制） | 文件内容是后续操作的基础，不能截 |

> FileRead 为什么不限制大小？因为文件内容是后续所有操作（Edit、分析、重构）的基础。如果你读了一个 2000 行的文件然后被截到 500 行，后续 Edit 可能改错位置。

```
源码位置：
toolLimits.ts:13 - DEFAULT_MAX_RESULT_SIZE_CHARS = 50000
toolLimits.ts:22 - MAX_TOOL_RESULT_SIZE_CHARS
query.ts:379    - applyToolResultBudget()
```

### 3.2 第 2 层：Snip Compact（历史裁剪）

**一句话解释**：对话轮次太多了？把最旧的**整组 round** 直接移除，腾出空间给新对话。

**关键概念**：一个 round = 一条 `assistant` 消息 + 它对应的所有工具调用和结果。**整组删除，不会拆散**，避免"工具结果还在但对应的推理已经没了"的断裂感。

```
裁剪前（50 轮）：
┌──────────┬──────────┬──────────┐
│ Round 1-20 │ Round 21-35 │ Round 36-50 │ ← 正在用
└──────────┴──────────┴──────────┘

裁剪后：
                      ┌──────────┐
                      │ Round 36-50 │ ← 保留最近 15 轮
                      └──────────┘
```

**独特设计：SnipTool**——除了自动触发，还有一个 `SnipTool` 让模型**主动决定**移除哪些消息。每条消息会被注入 `[id:xxx]` 标签（8 字符短 ID），模型调用 SnipTool 时引用这些 ID。

**与 Auto Compact 联动**：Snip 释放的 token 数（`snipTokensFreed`）会传给第 4 层 Auto Compact。Auto Compact 减去这个数后再判断是否需要触发——**避免不必要的二次压缩**。

### 3.3 第 3 层：Microcompact（微压缩）

**一句话解释**：旧的只读类工具结果还占着 token？保留最近 5 个，其余掏空。

**关键设计：只读 vs 写入**

| 可以清 | 永远不清 |
|--------|----------|
| FileRead · Bash · Grep · Glob | FileEdit · FileWrite · NotebookEdit |
| 只读类——结果可随时重新获取 | 写入型——不可重现的修改动作 |

**触发条件**（两个独立触发器，任一满足）：工具调用次数超过阈值；或闲置 > 60 分钟（利用 Prompt Cache 过期的窗口）。

**与 Prompt Cache 的关系**：Prompt Cache 闲置 ~5 分钟就过期，过期后 token 要全价处理。Microcompact 的闲置触发器利用这个：**既然 Cache 都过期了，不如趁机清掉旧内容**。

Claude Code 还有一个高级机制——**cache_edits API**（目前仅限 first-party 使用）。核心思想：**不修改本地消息，而是告诉 API "请在服务端忽略这些工具结果"**，从而在不破坏 prompt cache 前缀的情况下释放上下文空间。

```typescript
// src/services/api/claude.ts
type CachedMCEditsBlock = {
  type: 'cache_edits'
  edits: { type: 'delete'; cache_reference: string }[]
  // ↑ 值 = tool_use_id，指向要删除的工具结果
}
```

两层微压缩的协作关系：

```
每次 API 调用前
       │
       ▼
距上次消息 > 60 分钟?
       │
   ┌───┴───┐
  YES     NO
   │       │
   ▼       ▼
Time-Based MC    cache_edits MC（如果可用）
修改本地消息      不修改消息，通过 API 层面删除
破坏缓存（已冷）   保留缓存（仍热）
```

### 3.4 第 4 层：Auto Compact（自动摘要压缩）

**一句话解释**：前三层都是机械操作，这一层是**用 LLM 智能摘要**，是唯一"理解内容"的压缩。

**触发条件**：前三层跑完后仍 > 167K token（83%）

```
公式：contextWindow - min(maxOutput, 20K) - 13K
    = 200K - 20K - 13K = 167K
减去前三层已释放的 snipTokensFreed，只有还不够时才启动
```

**独特的 `<analysis>` + `<summary>` 双段式输出**：

Claude Code 让 LLM 生成两段内容：

```xml
<analysis>
[LLM 的内部推理过程 —— 用于提高摘要质量]
</analysis>
<summary>
[最终摘要 —— 只有这部分会保留]
</summary>
```

`formatCompactSummary()` 会**剥掉 `<analysis>` 段**，只保留 `<summary>`。这是一种"让 LLM 先思考再总结"的技巧，提高摘要质量但不浪费后续上下文。

**为什么 `<analysis>` 能提高摘要质量？**

根本原因在于 LLM 是 **autoregressive（自回归）模型**：逐 token 从左到右生成，每个 token 只能 attend to 前面已生成的 token。如果直接输出结构化摘要，写第 1 段时还没有"审视"过整段对话的全貌。加入 `<analysis>` 后，生成顺序变成：

```
输入: [几万 token 的对话历史] + [压缩指令]
       │
       ▼
生成 <analysis>  ← 第一遍: 按时间线"重走"对话
"用户一开始要求实现登录页面... 然后发现了 CORS 错误...
 改用了 proxy 方案... 最近在调样式..."
       │
       │ 每生成一句，后续 token 都能 attend to 这些中间结果
       │ 相当于扩展了模型的"工作记忆"
       ▼
生成 <summary>   ← 第二遍: 基于 analysis 综合输出
"1. Primary Request: ..."  ← analysis 中已梳理过，不会遗漏
"3. Files: login.tsx, proxy.ts..."  ← 可以直接引用 analysis 中的细节
```

**为什么不用 Anthropic 原生的 extended thinking？**

| 维度 | `<analysis>` XML 块 | 原生 extended thinking |
|------|---------------------|----------------------|
| **可控性** | prompt 里精确指定"分析什么" | 模型自行决定思考内容 |
| **成本** | 输出 token（较便宜） | thinking token（某些模型更贵） |
| **cache 兼容** | 不改变 thinkingConfig，不破坏 cache key | 改变 config 使 prompt cache 失效 |
| **可剥离** | 简单正则即可移除 | 需 API 层面处理 |
| **跨模型** | 任何模型都支持 | 仅支持 thinking 的模型 |

**压缩 Prompt 9 段结构化模板**：

```
1. Primary Request and Intent → 用户的所有明确请求
2. Key Technical Concepts     → 涉及的技术概念
3. Files and Code Sections    → 文件和代码片段(完整代码)
4. Errors and Fixes           → 错误和修复方案
5. Problem Solving            → 解决了什么问题
6. All User Messages          → 所有非工具结果的用户消息(逐条)
7. Pending Tasks              → 未完成的任务
8. Current Work               → 压缩前正在做什么
9. Optional Next Step         → 下一步(含原文引用)
```

**Post-Compact 重注入（核心差异化设计）**：

摘要是有损的，但 Re-injection 把关键状态**无损补回来**：

```
压缩后的消息 = [
  BoundaryMarker      // 系统标记: 时间戳、压缩前token数、最后消息UUID
  + Summary            // LLM 生成的摘要
  + Top-5 Files        // 最常用的5个文件内容（每个最多5000 tokens，共50K预算）
  + Recent Skills      // 最近调用的 Skill（每个5000 tokens，共25K预算）
  + Tool Deltas        // 完整的工具集声明（MCP工具、Agent列表）
  + Plan State         // 如果在 plan mode 中，重注入计划
  + Hook Results       // SessionStart hook 的上下文
]
```

```typescript
// src/services/compact/compact.ts
// 压缩前保存文件缓存，压缩后恢复最重要的文件
const preCompactReadFileState = cacheToObject(context.readFileState)
context.readFileState.clear()

// 重注入: 最多5个文件，每个最多5000 tokens
const POST_COMPACT_MAX_FILES_TO_RESTORE = 5
const POST_COMPACT_MAX_TOKENS_PER_FILE = 5_000
const POST_COMPACT_TOKEN_BUDGET = 50_000
```

**防工具幻觉的三重保护**：

在三个层面防止压缩 LLM 调用工具（因为较新版本的 Sonnet 模型更容易在看到工具定义后尝试调用）：

```
层 1: Prompt 开头 (NO_TOOLS_PREAMBLE)
    "CRITICAL: Respond with TEXT ONLY. Do NOT call any tools."

层 2: Prompt 结尾 (NO_TOOLS_TRAILER)
    "REMINDER: Do NOT call any tools..."

层 3: 代码层 (canUseTool 回调)
    createCompactCanUseTool() → 返回 { behavior: 'deny', message: '...' }
```

### 3.5 第 5 层：API Native（API 原生上下文管理）

**一句话解释**：前四层都在你的机器上跑，这一层是 **Anthropic 服务端的独立安全网**。

| 客户端（第 1-4 层） | 服务端（第 5 层） |
|---------------------|-------------------|
| 在你的机器上跑 | 在 Anthropic 服务器跑 |
| 发送前压缩 | 收到后清理 |
| 修改 local 对话历史 | **不改 local 对话历史** |

类比：前 4 层是你自己在家做垃圾分类（主动管理），第 5 层是垃圾处理厂收到你的垃圾后发现太多了，**替你分拣掉一部分**——但你家里的垃圾桶状态没变。

```typescript
// src/services/compact/apiMicrocompact.ts
const DEFAULT_MAX_INPUT_TOKENS = 180_000  // 输入 token 达到 180K 触发
const DEFAULT_TARGET_INPUT_TOKENS = 40_000 // 目标: 保留最近 40K
// → 至少需要清除 140K tokens
```

### 3.6 第 6 层：Context Collapse（上下文坍塌）

**一句话解释**：所有压缩都到极限了——**存档重启，从摘要重新开始**，就像游戏里的 checkpoint save。

| 90% → 开始保存 | 95% → 阻塞保存 |
|-----------------|-----------------|
| 后台启动 commit 保存 granular 上下文到磁盘，**不阻塞当前操作** | **阻塞一切操作直到保存完成**，然后从摘要重新开始——干净的上下文 |

**vs Auto Compact：压缩 vs 重启**

| Auto Compact | Context Collapse |
|-------------|-----------------|
| 在同一个对话内继续 | **接受对话需要"重启"** |
| 压缩历史，保留会话 | 归档到磁盘，从摘要开始新状态 |
| 一个是**修缮房子** | 一个是**搬新家** |

### 3.7 六层总览：精确阈值

| 层 | 参数 | 值 | 源码 |
|----|------|-----|------|
| **1 Tool Budget** | 单工具上限（默认） | 50,000 字符 | `toolLimits.ts:13` |
| | Bash / Grep / FileRead | 30K / 20K / ∞ | `BashTool.ts` / `GrepTool.ts` |
| **2 Snip** | SNIP_THRESHOLD | 缺失（ant-only） | `snipCompact.ts` |
| **3 Microcompact** | keepRecent | 5 个 | `timeBasedPMConfig.ts:23` |
| | 闲置阈值 | 60 分钟 | `timeBasedPMConfig.ts:32` |
| | 默认启用 | `false` | `timeBasedPMConfig.ts:31` |
| **4 Auto Compact** | 缓冲区 | 13,000 token | `autoCompact.ts:62` |
| | 摘要预留 | 20,000 token | `autoCompact.ts:31` |
| | 熔断 | 3 次 | `autoCompact.ts:70` |
| **5 API Native** | 触发阈值 | 180,000 token | `apiMicrocompact.ts:16` |
| | 保留目标 | 40,000 token | `apiMicrocompact.ts:17` |
| **6 Collapse** | commit / 阻塞 | 90% / 95% | `autoCompact.ts:202` |

**统计**：7.4K 代码行数，29 个源文件，1.4% 占总代码，6 层压缩。

---

## 四、如何决定保留什么？

### 4.1 opencode: 两阶段——先剪枝再摘要

**阶段一: Prune（规则裁剪旧工具输出）**

```typescript
// packages/opencode/src/session/compaction.ts
const PRUNE_MINIMUM = 20_000       // 至少裁掉 20K tokens 才执行
const PRUNE_PROTECT = 40_000       // 累积超过 40K 的部分才开始裁
const PRUNE_PROTECTED_TOOLS = ["skill"]  // skill 工具永不裁剪

const prune = function* (input) {
  let total = 0, pruned = 0, turns = 0
  const toPrune = []

  // 从后往前遍历
  for (let i = msgs.length - 1; i >= 0; i--) {
    if (msgs[i].info.role === "user") turns++
    if (turns < 2) continue        // 跳过最近 2 轮用户消息
    if (msgs[i].info.summary) break // 遇到上次摘要则停止

    for (const part of msgs[i].parts.reverse()) {
      if (part.type === "tool" && part.state.status === "completed") {
        if (PRUNE_PROTECTED_TOOLS.includes(part.tool)) continue
        if (part.state.time.compacted) break  // 已裁剪过

        const estimate = Token.estimate(part.state.output)
        total += estimate
        if (total > PRUNE_PROTECT) {
          pruned += estimate
          toPrune.push(part)  // 标记待裁剪
        }
      }
    }
  }

  if (pruned > PRUNE_MINIMUM) {
    for (const part of toPrune) {
      part.state.time.compacted = Date.now()  // 标记时间戳，不删除
      yield* session.updatePart(part)
    }
  }
}
```

被 prune 的工具输出不会被物理删除，而是在后续消息构建时替换为 `"[Old tool result content cleared]"`。

**阶段二: LLM 摘要（结构化模板）**

```
压缩 prompt 模板:
---
## Goal          → 用户想完成什么
## Instructions  → 用户给的重要指令
## Discoveries   → 过程中学到了什么
## Accomplished  → 完成了什么，还剩什么
## Relevant files/directories → 相关文件列表
---
```

压缩时：创建一个专用的 `compaction` agent -> 剥离所有媒体附件(`stripMedia: true`) -> 发送全部历史给 LLM -> LLM 生成摘要 -> 摘要存为特殊消息 -> 后续对话从摘要点继续。

### 4.2 OpenClaw: 分块 + 多阶段合并 + 安全过滤

**核心算法: 按 Token 均分 -> 逐块摘要 -> 合并**

```
消息历史 [M1, M2, M3, ..., Mn]
              │
  splitMessagesByTokenShare(messages, 2)
              │
     ┌────────┴────────┐
     │  Chunk A         │  Chunk B
     │  (50% token)     │  (50% token)
     └────────┬────────┘────┬────────┘
              │              │
       summarize(A)    summarize(B)
              │              │
     ┌────────┴──────────────┴────────┐
     │      Merge Summaries           │
     │  (MERGE_SUMMARIES_INSTR)       │
     └────────────────────────────────┘
```

**分块时保证工具调用原子性**：

```typescript
// src/agents/compaction.ts - splitMessagesByTokenShare
// 关键: 不在 tool_use/tool_result 对中间切分
if (message.role === "assistant") {
  const toolCalls = extractToolCallsFromAssistant(message)
  pendingToolCallIds = new Set(toolCalls.map(t => t.id))
  // 如果当前有未完成的工具调用，不切分
}
if (message.role === "toolResult") {
  pendingToolCallIds.delete(resultId)
  // 只有所有工具结果都收到后，才允许切分
}
```

**安全设计: 剥离 toolResult.details**：

```typescript
// SECURITY: toolResult.details can contain untrusted/verbose payloads;
// never include in LLM-facing compaction.
export function estimateMessagesTokens(messages) {
  const safe = stripToolResultDetails(messages)
  return safe.reduce((sum, msg) => sum + estimateTokens(msg), 0)
}
```

**三级降级策略**：

1. 尝试完整摘要
2. 失败 -> 排除超大消息（>50% 上下文窗口的单条消息），摘要其余部分
3. 再失败 -> 返回兜底文本：`"Context contained N messages (K oversized). Summary unavailable."`

### 4.3 保留策略对比

```
         opencode              OpenClaw              Claude Code
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│  Always Keep     │  │  Always Keep     │  │  Always Keep         │
│  System Prompt   │  │  System Prompt   │  │  System Prompt       │
│  Last 2 turns    │  │  Recent msgs     │  │  Recent messages     │
│  Skill tools     │  │  Active tools    │  │  File cache(top5)    │
│  Metadata        │  │  Identifiers     │  │  Tool deltas         │
│                  │  │                  │  │  Skill metadata      │
│                  │  │                  │  │  Plan state          │
│                  │  │                  │  │  Hook context        │
└──────────────────┘  └──────────────────┘  └──────────────────────┘
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│  Discard         │  │  Discard         │  │  Discard             │
│  Old tool out    │  │  Old messages    │  │  Images/docs         │
│  Media files     │  │  tool.details    │  │  Old tool results    │
│  Early history   │  │  Oversized msg   │  │  Thinking blocks     │
│                  │  │                  │  │  Analysis section    │
└──────────────────┘  └──────────────────┘  └──────────────────────┘
```

---

## 五、子 Agent 的上下文 vs 主 Agent

这是三个项目差异最大的地方。

### 5.1 opencode: 全新 Session，只传任务描述

opencode 的子 Agent 获得的是一个**完全干净的新 session**：

```typescript
// packages/opencode/src/tool/task.ts
// 创建新 session，只建立 parentID 链接
const session = await Session.create({
  parentID: ctx.sessionID,  // 记录父关系，但不共享历史
  title: params.description + ` (@${agent.name} subagent)`,
  permission: [/* 权限子集 */],
})

// 只传递任务 prompt，不传历史
const result = await SessionPrompt.prompt({
  messageID,
  sessionID: session.id,   // 新 session
  parts: promptParts,       // 只有任务描述和引用的文件内容
})
```

**子 Agent 不继承**：父 Agent 的消息历史、工具结果、压缩摘要。
**子 Agent 继承**：parentID 关系、权限规则子集、模型配置。

结果通过 `<task_result>` 标签包装返回给父 Agent。

### 5.2 OpenClaw: 裁剪后的历史 + 精简 System Prompt

OpenClaw 的子 Agent 获得**父 Agent 裁剪后的历史**：

```
主 Agent 历史 (可能 150K tokens)
        │
  pruneHistoryForContextShare()
        │
        ▼
子 Agent 获得 (≤50% 上下文窗口)
  ┌─────────────────────────┐
  │ 精简的 System Prompt     │
  │ 裁剪后的关键历史          │
  │ 完整的工具定义            │
  │ 安全过滤后的上下文         │
  └─────────────────────────┘
```

**特色**：生成子 Agent 时主动触发 `pruneHistoryForContextShare`，将父 Agent 的历史裁剪到上下文窗口的 50% 以内再传递，并剥离敏感字段（`toolResult.details`）。

### 5.3 Claude Code: 两种模式——Fork 与 Standard

Claude Code 的子 Agent 有两种创建模式：

**Fork 模式**：复用父 Agent 的完整消息前缀，实现 Prompt Cache 共享。

```
父 Agent: [System + 100 条消息] ← 已缓存
                 │
         fork()  │
                 ▼
子 Agent: [System + 100 条消息 + 子任务指令]
           └── 前缀完全一致 ──┘  └── 新增 ──┘
                                    ↓
                        Cache 命中率极高
```

**Standard 模式**：只传递精简的 System Prompt + 任务描述。

| 维度 | Fork 模式 | Standard 模式 |
|------|-----------|--------------|
| System Prompt | 完整应用 prompt | 精简 1 句话 |
| 目的 | Cache 命中 | 干净简洁 |
| 工具集 | 继承全部（但禁止调用） | 仅 FileReadTool（但禁止调用） |
| Thinking | 继承（不敢改，怕坏 cache key） | 显式关闭（节省 token） |

### 5.4 子 Agent 上下文对比表

| 维度 | opencode | OpenClaw | Claude Code |
|------|----------|----------|-------------|
| **历史继承** | 不继承，全新 session | 裁剪到 50% 传递 | Fork: 完整前缀; Standard: 不传 |
| **System Prompt** | 继承 agent 配置 | 精简版 | Fork: 完整; Standard: 精简 |
| **工具集** | 继承权限子集 | 完整继承 | 继承但禁止调用 |
| **结果回传** | `<task_result>` 文本 | 结构化回传 | 摘要回传到主上下文 |
| **Cache 优化** | 无 | 无 | Fork 核心目标就是 cache hit |

---

## 六、压缩 Prompt 设计深度对比

### 6.1 opencode: "信任 LLM" 策略

- System prompt 直接说"总结对话"，user prompt 给模板但不强制
- 不做分段式推理，不做后处理，LLM 输出就是最终摘要
- 禁止工具：`tools: {}` + system prompt 说明
- 优点：简单、好维护、对 prompt 质量依赖低
- 风险：摘要质量完全取决于 LLM，无法控制输出结构

### 6.2 OpenClaw: "安全第一" 策略

- 把摘要调用委托给专用库，自己只关心安全过滤
- 三道安全防线确保敏感数据不泄露
- 标识符保护解决了 UUID 被"优化"的实际痛点：`"Preserve all opaque identifiers..."`
- 合并指令明确说"优先近期上下文"——来自实际使用中的教训
- 降级策略：完整摘要（含 3 次指数退避重试）-> 排除大消息 -> 兜底文本

### 6.3 Claude Code: "极致工程" 策略

- **双路径设计**：cache 优先(fork) + 简洁备用(streaming)
- **`<analysis>` 代替原生 thinking**：更可控、可定制、可剥离
- **三重工具禁令**：应对较新版本 Sonnet 模型的工具幻觉问题
- **PTL 重试**：压缩请求自身溢出时，渐进式截断而非直接失败
- **9 段模板中 "All user messages" 独特**：确保用户反馈不丢失（源自摘要丢失用户指令导致重复工作的 bug）

### 6.4 Prompt 设计对比总表

| 维度 | opencode | OpenClaw | Claude Code |
|------|----------|----------|-------------|
| **System Prompt** | 专用 ~15 行 | 委托库内部 | Fork: 继承完整; Streaming: 1 句话 |
| **User Prompt** | 5 段模板 | 委托库 + 安全指令 | 9 段模板 + analysis/summary |
| **禁止工具** | `tools: {}` | 由库决定 | 三重防护 |
| **输出格式** | 自由文本 | 自由文本 | XML: `<analysis>` + `<summary>` |
| **输出后处理** | 直接使用 | 直接使用 | 删 analysis + 提取 summary |
| **重试策略** | 无重试 | 3 次指数退避 | PTL 重试 (截断头部, 最多 3 次) |
| **降级策略** | 溢出时返回 "stop" | 排除大消息 -> 兜底文本 | 截断最早消息组 |
| **缓存考量** | 无 | 无 | Fork 路径核心目标就是 cache hit |
| **多段合并** | 不支持 | 分块摘要 + 合并指令 | 不支持 (单次摘要) |

---

## 七、记忆系统

### 7.1 Claude Code: 四层记忆架构

| 层级 | 文件路径 | 谁来写 | 跨会话？ | 跨机器？ |
|------|---------|--------|---------|---------|
| 全局偏好 | `~/.claude/CLAUDE.md` | 你 | 是 | 否（本机） |
| 项目规范 | `<项目根>/CLAUDE.md` | 你 + 团队 | 是 | 是（通过 Git） |
| 模块规则 | `.claude/rules/*.md` | 你 | 是 | 是（通过 Git） |
| 自动记忆 | `~/.claude/projects/<hash>/MEMORY.md` | Claude 自动 | 是 | 否（本机） |

CLAUDE.md 在每次对话启动时会自动注入为对话的**第一条消息**，用 `<system-reminder>` 标签包裹，**优先级极高**。

**CLAUDE.md 编写三大原则**：

1. **控制在 200 行以内**——超过 200 行会大量消耗上下文 token，Claude 对后半部分的遵从度明显下降
2. **结构清晰，分块明确**——技术栈、编码规范、常用命令、禁止行为
3. **用 `.claude/rules/` 做模块化拆分**——通过 Frontmatter 的 `paths` 字段限定生效范围，访问后端文件时，前端规则不会占用上下文，按需加载省 token

### 7.2 OpenClaw: Agent 定位驱动的多文件记忆

OpenClaw 是"私人助理"定位，因此有 AGENT.md、SOUL.md、IDENTITY.md、USER.md、TOOLS.md 等多种文件类型。这与 Claude Code 只需要"项目要求"的单一 CLAUDE.md 形成鲜明对比。设计自己的 Agent 系统时，应根据 Agent 定位来设计 .md 文件类型。

### 7.3 opencode: MCP 驱动的可扩展记忆

opencode 通过 MCP 服务器管理外部上下文，可以通过配置 MCP 记忆服务器来实现持久化记忆。灵活性高但需要额外配置。

---

## 八、实战建议

### 8.1 Claude Code 最佳实践

```bash
# 1. 主动 /compact 压缩
# 当你感觉对话开始"跑偏"或已经聊了很久，主动触发
/compact

# 2. 用 /clear 开启干净会话
# 一个任务完全结束后，重要结论先存入 CLAUDE.md 再 clear

# 3. 任务切换时手动"打快照"
> 在继续之前，请把目前已完成的工作和待办事项总结一下，写到 TASK_STATUS.md

# 4. 会话状态保持与恢复
# 使用 --resume 恢复上次对话
claude --resume

# 5. 记忆文件管理
# 在 .claude/rules/ 下按模块拆分规则
# 通过 Frontmatter paths 字段限定生效范围
```

### 8.2 OpenClaw 优化策略

```yaml
# 1. 利用自适应比例
# OpenClaw 会自动根据消息大小调整保留比例
# 单条消息越大，保留比例越低（从40%降到最低15%）

# 2. 注意安全过滤
# toolResult.details 永远不会进入压缩 prompt
# 标识符（UUID等）会被保护不被"优化"

# 3. 理解三级降级
# 完整摘要 -> 排除大消息 -> 兜底文本
# 如果看到 "Summary unavailable" 说明降级到了最低级别
```

### 8.3 opencode 扩展方案

```typescript
// 1. 配置压缩选项
// opencode.config.ts
export default {
  compaction: {
    auto: true,           // 启用自动压缩
    reserved: 20000,      // 保留缓冲区
  }
}

// 2. skill 工具的特殊保护
// skill 工具的输出永远不会被 prune
// 利用这一点，重要信息可以通过 skill 传递

// 3. 配置 MCP 记忆服务器
// 用于跨会话的记忆持久化
```

---

## 九、总结

### 9.1 核心差异

| 维度 | Claude Code | OpenClaw | opencode |
|------|-------------|----------|----------|
| **压缩架构** | 六层渐进式 | 多阶段分块 + 降级 | 两阶段 Prune+LLM |
| **触发精度** | 精确阈值 + 熔断 | 自适应动态预算 | 固定阈值 |
| **Cache 感知** | 核心设计目标 | 无 | 无 |
| **安全考量** | 三重工具禁令 | 安全过滤 + 标识符保护 | 基础保护 |
| **子 Agent** | Fork/Standard 双模式 | 裁剪传递 | 完全隔离 |
| **降级策略** | PTL 重试 + Context Collapse | 三级降级 | 溢出停止 |
| **成本效率** | 最优（cache-aware） | 中等 | 简洁 |

### 9.2 选择建议

- **追求性能和成本优化** → Claude Code（六层压缩 + cache-aware 设计）
- **追求安全和鲁棒性** → OpenClaw（分块+降级+安全过滤）
- **追求简单易懂** → opencode（两阶段分离，易于定制）

### 9.3 设计启示

三个项目在上下文压缩上的设计，反映了各自的工程优先级。Claude Code 追求极致优化——prompt cache 感知设计、重注入恢复关键上下文、熔断器防失控。OpenClaw 追求鲁棒性——多级降级策略、安全优先、工具调用原子性保证最严格。opencode 追求简洁——两阶段分离（规则 + LLM），子 Agent 完全隔离，配置选项少但够用。

---

**参考资料：**
- Claude Code 源码分析：https://nangongwentian-fe.github.io/learn-claude-source/
- OpenClaw 源码：https://github.com/openclawai/OpenClaw
- opencode 文档：https://opencode.ai/docs
