---
title: Pi 的上下文工程：每次请求，模型到底看到了什么
date: 2026-11-05 01:05:00
categories:
  - Pi
tags:
  - Pi
  - Agent
  - Context
  - Prompt
cover: /images/Pi-上下文/cover.jpg
description: 把一次请求的输入拆成五层：system prompt 拼装、项目约定、技能索引、会话投影、消息规范化，最后才是 token 预算与压缩。
---

上一篇讲了会话树：历史怎么存。这一篇讲它的上半截——**历史怎么变成"这次请求的输入"**。

很多人以为上下文就是"把历史消息数组交给模型"。跑通一个 demo 确实如此，但真跑起来，问题立刻变成三件事：system prompt 里到底该写什么、项目里的 `AGENTS.md` 什么时候进入、上下文快满时靠什么判断"快满了"。

Pi 的答案是：**输入不是存出来的，是每次现拼的**。整个拼装过程可以拆成五层，每一层都有自己的开关和失效条件。

## 0. 结论先摆

一次模型请求的输入，由五层叠起来（`packages/coding-agent/src/core/system-prompt.ts:128` 的 `buildSystemPromptSections` 覆盖前三层，后两层在 agent 核心里）：

| 层 | 内容 | 什么时候变 |
| --- | --- | --- |
| ① system prompt | 身份、可用工具、规则、文档索引 | 工具集变了才重拼 |
| ② 项目约定 | `AGENTS.md` / `CLAUDE.md` | 目录变了才重读 |
| ③ 技能索引 | 每个 skill 的名字 + 一句话 | 装了新 skill |
| ④ 会话投影 | 从 `leafId` 往上走到根 | 每回合 |
| ⑤ 消息规范化 | 转成 LLM 消息、折叠 system | 每次请求前 |

前四层是"内容"，第五层是"形状"。

{% mermaid %}
flowchart LR
  A["① system prompt<br/>身份·工具·规则·文档索引"] --> B["② project context<br/>AGENTS.md 沿目录收集"]
  B --> C["③ skills 索引<br/>仅当有 read/bash"]
  C --> D["④ 会话投影<br/>leafId → 根路径"]
  D --> E["⑤ 规范化<br/>convertToLlm + normalizeContext"]
  E --> F["provider.stream()"]
{% endmermaid %}

下面逐层看。

## 1. 第一层：system prompt 是被拼出来的

Pi 的 system prompt 不是一个大字符串常量，而是一个**分节的结构**。`buildSystemPromptSections` 返回的是一个 `Record<string, string>`，每个 key 是一节：

```ts
const promptSections: Record<string, string> = {};
promptSections.preamble = "You are a coding assistant running inside pi, a coding agent harness. ...";
promptSections.tools = `${tools}\n\nAdditional tools may be available.`;
promptSections.rules = buildRules(declaredTools, toolGuidelines, promptGuidelines);
promptSections.docs = `Pi documentation (read only when the user asks about the harness itself...)`;
```

后面还跟着 `project_context`、`skills`、`cwd`，以及扩展自定义的 section（同名 key 直接覆盖）。

拼完之后做一件事：**除 preamble 外，每一节都用 XML 标签包起来**（`system-prompt.ts:190-196`）：

```ts
for (const [name, content] of Object.entries(promptSections)) {
  if (name !== "preamble") sections[name] = `<${name}>\n${content}\n</${name}>`;
}
```

为什么要包标签？因为模型是靠"边界"理解结构的。`<tools>` 里列的是工具，`<project_context>` 里是项目约定——同样的文字放在不同标签下,权重完全不同。而且包了标签之后，模型可以明确判断"这一段结束了"，不容易把 `AGENTS.md` 里的话当成系统指令。

一个细节值得注意：`docs` 这一节只写了**文档路径索引**，还特意加了一句 `read only when the user asks about the harness itself`。也就是说，Pi 不会把 15 万字的文档塞进 prompt，只告诉模型"文档在哪、什么时候该去读"。这是上下文工程里最省 token 的一招：**索引比内容便宜**。

`preamble` 是唯一不打包的一节，且可以被 `customPrompt` 整段替换。这给了使用者一个很明确的分级：想改人格就换 preamble，想加约束就加 section。

## 2. 第二层：项目约定怎么进来

`<project_context>` 来自 `contextFiles`，由 resource-loader 收集（`core/resource-loader.ts:213`）：

```ts
const candidates = ["AGENTS.override.md", "AGENTS.md", "AGENTS.MD", "CLAUDE.md", "CLAUDE.MD"];
```

按顺序找，`AGENTS.override.md` 优先——这是给"个人本地覆盖"留的口子：仓库里提交 `AGENTS.md` 给所有人用，本地想临时加两句就放一个 override，不用改仓库文件（也避免误提交）。

更重要的设计在**加载范围**：它是从当前工作目录往上找，还是一层层往下继承？Pi 的做法和大多数 agent 一致——**沿目录向上收集，越具体越靠后**，于是"仓库级约定"和"子目录级约定"可以同时生效，且后者能覆盖前者。

这里有个容易被忽略的坑，代码注释里写得很清楚（`resource-loader.ts:283`）：

> Compare the directory's real path, not the file's: a worktree AGENTS.md that ...

意思是判断"这个文件属于哪个目录"时要比对目录的真实路径，而不是文件路径。原因是用 git worktree 时，同一个 `AGENTS.md` 可能通过符号链接出现在不同路径下，按文件路径去重会漏判。这种细节不影响功能，但会在"为什么我的约定没生效"上折腾人半天。

## 3. 第三层：skills 只在能用工具时才提示

skills 那一节的条件判断只有几行，但很能说明设计取向（`system-prompt.ts:172-180`）：

```ts
const readers = ["read", "bash"] as const;
const skillFileReadTool =
  readers.find((tool) => declaredTools.includes(tool)) ??
  (readers.some((tool) => selectedTools.includes(tool)) ? "indirect" : undefined);
if (skillFileReadTool && skills.length > 0) { ... }
```

翻译一下：**只有模型手里有 `read` 或 `bash`，才会告诉它"有哪些技能"**。因为技能的本质是"一个 markdown 文件，里面写着做某类事的步骤"，模型必须能读文件，索引才有意义。如果这一轮是只读模式或者工具被裁掉了，这节直接不出现，省掉几百 token。

`indirect` 那个分支处理的是另一种情况：读文件的工具被隐藏了（不在模型可见列表里），但别的工具还能间接读到。这时仍然给技能索引，只是不点名工具。

这就是我说的"每层都有自己的失效条件"——不是所有 prompt 段落永远都在，它们各自看条件。

## 4. 第四层：会话投影

这一层上一篇讲过，这里只补一句关键区别：

**投影产出的是 `AgentMessage[]`，不是 `Message[]`。**

`AgentMessage` 比 `Message` 宽——它允许应用定义自己的消息角色（`packages/agent/src/types.ts:374`）：

```ts
type AgentMessage = Message | CustomAgentMessages[keyof CustomAgentMessages];
```

而 `Message` 在 `pi-ai` 里是严格四元封闭联合：`SystemMessage | UserMessage | AssistantMessage | ToolResultMessage`（`packages/ai/src/types.ts:667`）。

为什么要分两层？因为**应用想存的东西和模型能看的东西不是一回事**。比如扩展可能想记一条"用户点了按钮"的消息，用于自己渲染，但模型不该看到它。于是：会话里存 `AgentMessage`，发给模型前用 `convertToLlm` 过一遍，只留合法的四种。

`convertToLlm` 的契约写得很强硬（`packages/agent/src/types.ts:222`）：

> must not throw or reject. Return a safe fallback value instead.

**不许抛错。** 原因很实际：这个函数在每次请求前都会跑（`agent-loop.ts:404-406`），它一抛，整个对话就卡住。而它处理的输入是用户和扩展自定义的消息，形状不可控。所以宁可降级成一个安全值，也不能让"一条坏消息"变成"会话打不开"。

## 5. 第五层：规范化

`convertToLlm` 之后还有一步 `normalizeContext`（`packages/ai/src/utils/transcript.ts:30`），它做两件不起眼但必须做的事：

1. 把 `Context.systemPrompt` 和 `Context.tools` 折成**第一条 system message**
2. 给结果打上一个 brand 类型 `TranscriptContext`，防止裸的 `Context` 直接漏进 provider

第二条是类型层面的防御。`Context` 是宽松输入（`types.ts:796`），`TranscriptContext` 带 brand（`:810`）——只有 `normalizeContext` 能产出后者。于是"忘记规范化就发请求"这种 bug 在编译期就过不去。

还有一个开关：`collapseSystemMessages`（`transcript.ts:113`）按模型的 `supportsMidConvoSystemMessages` 决定——支持中途 system 消息的模型保留原样（可以利用缓存），不支持的就把它们折叠到第一条里。

{% mermaid %}
flowchart TD
  A["会话树上的路径<br/>AgentMessage[]"] --> B["convertToLlm<br/>自定义角色 → 四种合法消息"]
  B --> C{"模型支持<br/>中途 system 消息?"}
  C -->|支持| D["保留原顺序<br/>前缀稳定利于缓存"]
  C -->|不支持| E["collapseSystemMessages<br/>折叠进首条 system"]
  D --> F["normalizeContext<br/>systemPrompt+tools 折成首条 system"]
  E --> F
  F --> G["TranscriptContext（带 brand）<br/>provider.stream()"]
{% endmermaid %}

## 6. token 预算：混合估算

上下文工程最后一定要回答"现在用了多少 token"。这里有个诚实的工程妥协。

纯估算（字数 / 4）不准，尤其中文和代码；纯实测（等 API 返回 usage）又太晚——你要在发请求**之前**决定压不压。

Pi 用的是混合法（`core/compaction/compaction.ts:196`）：

```ts
const usageInfo = getLastAssistantUsageInfo(messages);
if (!usageInfo) { /* 全估算 */ }
const usageTokens = calculateContextTokens(usageInfo.usage);
let trailingTokens = 0;
for (let i = usageInfo.index + 1; i < messages.length; i++) trailingTokens += estimateTokens(messages[i]);
return { tokens: usageTokens + trailingTokens, ... };
```

即：**上一次请求 API 回报的真实 usage + 它之后新增消息的估算**。

这个组合很聪明。真实 usage 是准确的（服务端算的），新增的几条消息用估算误差也很小。等于把昂贵的精确度用在长历史那一头，把便宜的估算用在短尾巴那一头。

估算里还有个常数：图片按 **4800 字符**算（`compaction.ts:276` 的 `ESTIMATED_IMAGE_CHARS`）。因为图片在请求里是 base64，实际 token 消耗和分辨率挂钩，4800 是个保底偏保守的经验值。

## 7. 什么时候压缩

判断只有一行（`compaction.ts:267`）：

```ts
export function shouldCompact(contextTokens, contextWindow, settings) {
  if (!settings.enabled) return false;
  return contextTokens > contextWindow - settings.reserveTokens;
}
```

注意是 `contextWindow - reserveTokens`，**不是** `contextWindow`。`reserveTokens` 默认 16384（`core/settings-defaults.ts:11`）——留出 16K 的余量，是给"这一轮还要生成的输出 + 工具结果"用的。如果你把窗口用到 100% 再压，下一次请求根本没地方放输出。

另一个参数是 `keepRecentTokens: 20000`：压缩时保留最近约 2 万 token 的原文，只把更早的部分摘要掉。这解释了上一篇里 `firstKeptEntryId` 的来历——**压缩的粒度是"保留尾部 + 摘要头部"，不是"全压成一段"**。

{% mermaid %}
flowchart LR
  A["0"] --> B["contextWindow − reserveTokens<br/>（16384）触发压缩"]
  B --> C["压缩：摘要头部 + 保留尾部<br/>keepRecentTokens 20000"]
  C --> D["腾出空间，继续对话"]
  B -.压完仍超.-> E["尾部本身过大<br/>只能继续压或报错"]
{% endmermaid %}

这样就有一个安全区间的概念：

- `contextWindow - reserveTokens` 以下：正常聊
- 超过它：该压了，压完腾出 `keepRecentTokens` 的空间
- 压完还超：说明尾部本身太大，只能继续压，或者报错

值得一提的是，**后台压缩**是另一个产品（`pi-durable`）才有的能力，它的 `backgroundTokens: 32768` 让"摘要还在生成时对话继续跑"。在 coding-agent 里压缩是阻塞的——这个区别后面写到 durable 时再展开。

## 8. 一个反直觉的点：上下文不是"越多越好"

写到这里可以回答一个常见疑问：既然窗口那么大，为什么不把整个 `AGENTS.md`、所有 skill 全文、全部历史都塞进去？

三个原因，都可以在这套代码里找到对应设计：

**成本。** 索引比内容便宜一个数量级。`<docs>` 那节只给路径，让模型按需 `read`。

**噪声。** 上下文越长，模型对"哪句是约束、哪句是参考"的区分越弱。所以 system prompt 分节、打包标签、`project_context` 单独一节——**结构本身就是信号**。

**缓存。** 这是最容易被忽略的一条。Pi 的 `preamble` 不打包、且在所有会话里字面一致（除非你自定义），就是为了让前缀命中 provider 的 prompt cache。system prompt 前面那几千 token 稳定不变，价格能差好几倍。这也是为什么 model 目录里每个模型都有 `promptCache` 字段。

换句话说：**上下文工程不只是"写什么"，还包括"按什么顺序写、哪些保持稳定"**。

## 9. 小结

五层，各管一段：

1. **system prompt**：分节拼装，除 preamble 外都打包标签，稳定前缀利于缓存。
2. **project context**：`AGENTS.override.md` → `AGENTS.md` → `CLAUDE.md` 候选择优，沿目录收集。
3. **skills**：只在模型有 `read`/`bash` 时出现，索引而非全文。
4. **会话投影**：树 → 路径 → `AgentMessage[]`，压缩节点切出有效区间。
5. **规范化**：`convertToLlm`（绝不抛错）→ `normalizeContext`（折 system、打 brand）。

再加一条预算规则：`contextWindow - reserveTokens` 触发压缩，保留 `keepRecentTokens` 的尾部原文，token 数用"真实 usage + 尾部估算"的混合法。

如果只记一句话：**上下文是每回合现拼的，而"拼什么"和"拼多少"是两个独立的设计维度**。

---

**相关阅读**

- [Pi 入门：一个把"极简"当真了的 agent](/2026/11/05/Pi-入门/)
- [Pi 的一次请求：agent loop 里到底发生了什么](/2026/11/05/Pi-Loop/)
- [Pi 的会话树：一条对话为什么不是一条线](/2026/11/05/Pi-会话树/)
