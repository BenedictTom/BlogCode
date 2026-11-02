---
title: DSH 上下文装配全解：一次模型请求到底是怎么拼出来的
date: 2026-10-30 21:10:00
categories: [Agent]
tags: [Agent, DeepSeek, DSH, Context]
cover: /images/DSH-上下文装配全解/cover.png
---

上一篇《[DSH 会话压缩（Compaction）策略详解](/2026/10/30/DSH-会话压缩策略详解/)》把"上下文快满了怎么办"讲透了。但它留下一个更前置的问题：

> 压缩改写的那个"上下文"，一开始到底是怎么拼出来的？

这篇就来拆装配（assembly）。所有结论都不是从文档抄的——我把装好的 `app.asar` 拆开，读了 `dsh-agent-loop`、`dsh-system-prompt`、`dsh-session`、`dsh-token-meter`、`dsh-compaction-basic` 这几个包的实际产物，下面引用的每一行代码、每一个错误字符串都可以复现。

## 0. 一句话概括

> **一次请求的正文不是"一个消息数组"，而是五样东西在 agent-loop 里被拼成一个信封：按段位序号排序的系统提示词注册表、作为额外一条 user 消息插入的动态上下文、自注册且显式排序的工具 schema、只含 `config`/`adapterDefaults`/`tools` 三个字段的请求头，以及从只追加日志投影出来的消息序列。**

这五样东西的名字和归属，就是这篇要讲的全部：

| 拼装件 | 谁产出 | 进到哪 | 长什么样 |
|---|---|---|---|
| 系统提示词 | `systemPrompt.assemble()` | 表面里的 `system/message` | 若干段按 `order` 升序拼接 |
| 动态上下文 | `assembly.contexts` | **额外一条 user-role 消息** | 工作目录、沙箱策略、审批策略…… |
| 工具 schema | `toolProviders` + `toolOrder` | 请求头 `tools` | 有序数组，顺序即身份 |
| 请求头 | `canonicalHeader()` | `request/header` 事件 | `{config, adapterDefaults?, tools?}` |
| 消息序列 | `session.deriveMessages()` | `request.messages` | surface 投影，深冻结 |

![一次请求的完整装配链路](/images/DSH-上下文装配全解/hero.png "六个步骤与四块细节面板")

先交代我读的源码清单（体积是解包后的真实大小，便于你定位）：

| 包 | 文件 | 大小 |
|---|---|---|
| `@deepseek-ai/dsh-agent-loop` | `lib/index.js` | 74,599 B |
| `@deepseek-ai/dsh-system-prompt` | `lib/index.js` | 19,817 B |
| `@deepseek-ai/dsh-session` | `lib/index.js` | 94,982 B |
| `@deepseek-ai/dsh-session` | `lib/types/surface.js` | 26,100 B |
| `@deepseek-ai/dsh-token-meter` | `lib/index.js` | 35,095 B |
| `@deepseek-ai/dsh-compaction-basic` | `lib/index.js` | 49,452 B |
| `@deepseek-ai/dsh-compaction-tool-result-pruner` | `lib/index.js` | 7,570 B |

## 1. 三个流传很广的误解

先破后立。这三个说法我都见过，源码里都不成立。

### 误解一：`context/*` 在装配上下文

听起来天经地义，但 `context/*` 这些包（时间上下文、文件引用、会话引用）里没有一个在做装配。它们的全部工作是在 `agent/pre-step` 上挂一个瀑布：

```js
// dsh-session-reference/lib/types/index.js:112
ctx.on('agent/pre-step', async ({ agent, signal }, next) => { /* … */ });
```

它们只是"再塞一句话"的扩展点。真正的装配入口在 agent-loop 里，只有一行：

```js
// dsh-agent-loop/lib/index.js:907（preStep 方法内）
const assembly = await this.loopCtx.systemPrompt.assemble(assembleContextFor(this, signal));
```

装配的主体是 **agent-loop**。`context/*` 是它的输入提供者，不是它。

### 误解二：系统提示词是一段常量字符串

很多人以为它是启动时拼好的一个大字符串，然后每次请求原样塞进去。实际它是一个**按段位序号排序的注册表**：身份在 `-1000`，人格后缀在 `10200`，中间夹着二十多个工具说明段。谁激活、谁不激活，是每个请求现场算的。

### 误解三：请求头里包含系统提示词

也不是。请求头只有三个字段，系统提示词根本不在里面——它是作为一条 `system/message` 进入会话表面的。这条规则在源码里是硬校验：

```js
// dsh-session/lib/types/surface.js:158
throw new Error(`${subject} must omit header.system; use system/message`);
```

为什么要这么分？因为头是"这次请求的技术参数"，而系统提示词是"模型看到的内容"。前者要能便宜地比较和去重，后者要能进表面参与缓存与压缩。混在一起，两件事都做不好。

## 2. 装配主链路：preStep 的五步

一个 step 开始时，`preStep()` 做的事可以拆成五步（源码 `dsh-agent-loop/lib/index.js:902-927`、`:1214`）：

```js
// 1. 取本轮新消息
const claimed = this.inbox.claim(target, position.turn);

// 2. 装配：提示词段 + 动态上下文 + 工具 schema + 变量
const assembly = await this.loopCtx.systemPrompt.assemble(assembleContextFor(this, signal));

// 3. 过瀑布，默认实现把 contexts 渲染成文本并插入
const decision = await this.dispatch.waterfall("agent/pre-step", {
  messages: claimed, ...position, signal
}, () => {
  const sections  = renderContextSections(assembly);
  const context   = this.runtimeContext.project(joinContextSections(sections), sections);
  return Promise.resolve({
    kind: "enter",
    messages: context === void 0 ? claimed : [...claimed, context]
  });
});

// 4. 组装请求信封（头 + 消息 + 工具）
const request = this.buildRequest(config, preparedCall, assembly.tools, {...}, startsRequestSeries, signal);
```

第 2 步和第 4 步是这篇的主角。第 3 步里有个容易被忽略的细节：`messages: [...claimed, context]` 是**追加**，不是替换。动态上下文不是"改写某条消息"，而是"在消息列表末尾再挂一条 user-role 消息"。

{% mermaid %}
sequenceDiagram
    autonumber
    participant L as agent-loop
    participant SP as systemPrompt
    participant W as 瀑布 agent/pre-step
    participant S as Session（日志）
    participant P as Provider

    L->>L: inbox.claim() 取本轮消息
    L->>SP: assemble(assembleContextFor(agent, signal))
    SP->>SP: 排序 sections / 收集 contexts / 排工具
    SP-->>L: assembly {sections, contexts, tools, variables}
    L->>W: waterfall("agent/pre-step", {messages: claimed})
    W->>W: 默认实现：renderContextSections → project
    W-->>L: {kind:"enter", messages:[...claimed, context]}
    L->>S: append request/header（reason: initial|resume|change|series）
    L->>S: deriveMessages() 投影出 messages
    L->>P: request {config, messages, tools}
{% endmermaid %}

注意这里消息是分两条路走的：**新消息来自 inbox，历史消息来自 surface 投影**。两者拼接成最终 `messages`，任何一条都不是"上一轮的请求原样复用"。

## 3. 系统提示词是一张带段位的注册表

这是整个装配里最精妙的一层。`dsh-system-prompt` 把提示词切成"段（section）"，每段有自己的 `order`，装配时按 `order` 升序拼。源码里那张表是这样的（`lib/index.js:10-43`，我按原值抄的）：

| 段位 | order | 干什么 |
|---|---|---|
| `HARNESS_IDENTITY` | -1000 | 你是一个 AI agent |
| `DEPLOYMENT_PERSONA_PREFIX` | 0 | 部署方人格前缀 |
| `PLAN_POLICY` | 500 | 计划模式规则 |
| `TEAM_POLICY` | 600 | 团队协作规则 |
| `PTC_ONLY` | 800 | 仅程序化调用模式 |
| `FILE_REFERENCE` | 900 | 文件引用约定 |
| `TOOL_BASH` | 1000 | bash 工具说明 |
| `TOOL_PWSH` | 1010 | PowerShell 工具说明 |
| `TOOL_READ` | 1100 | read 工具说明 |
| `TOOL_WRITE` | 1200 | write |
| `TOOL_EDIT` | 1300 | edit |
| `TOOL_GLOB` | 1400 | glob |
| `TOOL_GREP` | 1500 | grep |
| `TOOL_JOBS` | 1600 | 后台任务 |
| `TOOL_PTY` | 1700 | 交互式终端 |
| `TOOL_WEB_SEARCH` | 2000 | 联网搜索 |
| `TOOL_WEB_FETCH` | 2100 | 抓取网页 |
| `TOOL_LSP` | 2200 | 语言服务 |
| `TOOL_SESSION_QUERY` | 2300 | 查询历史会话 |
| `TOOL_GOAL` | 2400 | 长目标 |
| `TOOL_WORKFLOW` | 2600 | 工作流编排 |
| `TOOL_RALPH` | 2700 | Ralph 循环 |
| `TOOL_SUBAGENT` | 2800 | 子代理 |
| `TOOL_REPORT` | 2900 | 回报 |
| `TOOL_COMPUTER_USE` | 3000 | 电脑操作 |
| `MCP_SERVERS` | 3100 | MCP 服务器清单 |
| `TOOLS_SDK` | 5000 | SDK 用法长文 |
| `DELIVERABLE_FILE_REFERENCES` | 9000 | 产物引用 |
| `STRUCTURED_OUTPUT` | 9900 | 结构化输出契约 |
| `HARNESS_SOURCE` | 10000 | 框架源码附录 |
| `WEB_SURFACE` | 10100 | Web 界面事实 |
| `DEPLOYMENT_PERSONA_SUFFIX` | 10200 | 部署方人格后缀 |

为什么是这个顺序？几条能读出来的设计意图：

- **身份必须是负数**。它要排在所有东西之前，包括部署方的人格前缀（`0`）。人格是"部署方在此之上加的修饰"，不是"覆盖身份"。
- **工具说明集中在 1000–3000**，而且顺序就是模型的工作流顺序：先 bash（动手），再 read/write/edit（改文件），再 glob/grep（找东西），再联网、再查历史、再开子代理。模型读提示词是顺序读的，越靠前的工具越"默认会想到"。
- **SDK 文档被放到 5000**，远在工具说明之后。它是"查手册"性质的内容，不该抢日常工具的注意力。
- **`STRUCTURED_OUTPUT` 在 9900、`HARNESS_SOURCE` 在 10000**：这类"约束性/附录性"内容压到最后，既保证模型结尾还看到硬约束，又不干扰前半段的角色设定。
- **人格后缀 `10200` 收尾**，跟开头的 `0` 前缀把整段包起来。

动态上下文另有自己的一张表（`CONTEXT_ORDERS`，`lib/index.js:44-52`），编号小得多，因为它们是"每次请求重新算的一小段"：

| 上下文段 | order | 内容 |
|---|---|---|
| `WORKING_DIRECTORY` | 100 | 当前工作目录 |
| `SANDBOX_POLICY` | 110 | 文件沙箱策略 |
| `APPROVAL_POLICY` | 115 | 审批策略 |
| `SUBAGENT_DELEGATION` | 120 | 子代理委派说明 |
| `TEAM_IDENTITY` | 125 | 团队身份 |
| `HARNESS_SOURCE` | 200 | 框架源码位置 |
| `WEB_SURFACE` | 210 | Web 界面事实 |

排序规则本身也有讲究。`assemble()` 里先 `sectionDefinitions.sort(comparePromptSections)`，`order` 相同的时候用 `compareNames` 按 Unicode 码点比较——不是 `localeCompare`：

```js
// 用码点而不是本地化排序，结果跟语言环境无关
sectionDefinitions.sort(comparePromptSections);
```

这条看着吹毛求疵，其实是可复现性的地基：同一份配置在任何机器、任何 locale 下拼出来的提示词必须逐字节相同，否则 prefix cache 会莫名其妙失效，diff 也没法审。

{% mermaid %}
flowchart TB
    A["-1000 身份<br/>You are an AI agent…"] --> B["0 人格前缀"]
    B --> C["500–900 策略 / 引用约定"]
    C --> D["1000–1700<br/>本地文件工具<br/>bash → read → write → edit → glob → grep"]
    D --> E["2000–2900<br/>联网 / 历史 / 目标 / 工作流 / 子代理"]
    E --> F["3100 MCP 服务器"]
    F --> G["5000 SDK 长文"]
    G --> H["9000–9900<br/>产物引用 / 结构化输出"]
    H --> I["10000–10100<br/>源码附录 / Web 事实"]
    I --> J["10200 人格后缀"]
{% endmermaid %}

## 4. 三条硬规则，和一条文档没写的例外

`assemble()` 的实现（`lib/index.js:356-410`）不长，但每条规则都很硬。

### 规则一：空段直接丢，不占空行

```js
// lib/index.js:19
assembly.sections
  .map(section => section.interpolate === false ? section.text : interpolate(...))
  .filter(text => text.length > 0)
  .join("\n\n");
```

没激活的工具说明段会被整个丢掉，而不是留个空段落。否则每关一个工具，提示词里就多一堆空行，白花 token。

### 规则二：插值失败就炸，绝不静默

`{{variable}}` 的解析是严格模式，四种情况全部 `throw`：

| 情况 | 报错原文 |
|---|---|
| 变量没注册 | `unknown prompt variable "{{name}}" in ${kind} "${input.name}"; registered variables: …` |
| 注册了但这次没值 | `prompt variable "{{name}}" has no value for this assembly (${kind} "${input.name}")` |
| 括号残缺 | `malformed prompt variable reference at "…" in ${kind} "${input.name}" (references are complete simple {{name}} groups)` |
| 变量名不合法 | `malformed prompt variable reference "{{…}}" in ${kind} "${input.name}" (variable names match …)` |

大多数模板引擎遇到未定义变量会渲染成空字符串，让请求照发。这里反过来：宁可让这个 step 失败。理由是——提示词里少一个变量名，模型可能整段行为都跑偏，而这种偏差在输出里看不出来，比直接报错昂贵得多。

### 规则三：`complete: true` 的段只能有一个

```js
// lib/index.js:381-382
const completeSections = sectionDefinitions.filter(s => s.complete === true);
if (completeSections.length > 1)
  throw new Error(`multiple complete prompt sections are active: ${...}`);
```

而且在过完 `system-prompt/assemble` 瀑布之后，这个段会被**恢复成唯一的 sections**：

```js
return { ...transformed,
  sections: completeSection === void 0 ? transformed.sections : [completeSection],
  ... };
```

也就是说 `complete` 不是一个"特殊段"，而是一种"整段替换"的语义：谁标了它，谁的文本就是全部提示词。这是给"自定义 agent 完全接管人格"留的口子——替换，而不是叠加。

### 例外：`required: true` 的上下文能穿过 suppress

文档说 `suppressRuntimeContext` 会关掉动态上下文。源码里的过滤条件是：

```js
contexts: [...contextByName.values()]
  .filter(entry => !runtimeContextSuppressed || entry.required === true)
  .sort((a, b) => a.order - b.order)
```

标了 `required: true` 的段在 suppress 下**依然保留**，末尾还有一道同样的过滤兜底：

```js
contexts: runtimeContextSuppressed
  ? transformed.contexts.filter(entry => requiredContexts.has(entry.name))
  : transformed.contexts
```

为什么？因为有些上下文不是"锦上添花"，而是"不给就会误操作"——沙箱范围和审批策略就属于这类。用户说"别给我塞动态上下文"时，他的意思通常是不想看到工作目录的碎碎念，而不是允许 agent 无视沙箱。

## 5. 动态上下文为什么是"额外一条 user 消息"

回到第 2 步的瀑布默认实现：

```js
const sections = renderContextSections(assembly);
const context  = this.runtimeContext.project(joinContextSections(sections), sections);
return Promise.resolve({ kind: "enter",
  messages: context === void 0 ? claimed : [...claimed, context] });
```

三个设计后果，全都能在行为里观察到：

1. **系统提示词保持稳定**。它只由"激活了哪些段"决定，跟工作目录、时间、文件列表无关。这些每天变几十次的东西不会污染提示词前缀——prefix cache 才有意义。
2. **动态内容一遍遍重复**。每个 step 都插一条新的上下文消息，所以长会话里"工作目录是 X、沙箱是 Y"会出现很多次。这是有意的：模型对最近的消息更敏感，靠得近的约束更管用。
3. **插件可以整步拦截**。瀑布的返回若为 `{kind: "reject"}`，这个 step 直接不进入：

```js
if (decision.kind === "reject") return decision;  // :922
// 上层：turnEnds = { kind: "blocked" }; return false;
```

这就是 `/compact` 之外很多"先别发请求"能力的实现方式。

{% mermaid %}
flowchart LR
    subgraph 稳定前缀["稳定前缀（可缓存）"]
        SP["system/message<br/>注册表拼出来的提示词"]
    end
    subgraph 每次都变["每次都新算（不可缓存）"]
        C1["user: 工作目录 / 沙箱 / 审批"]
        C2["user: 工作目录 / 沙箱 / 审批"]
    end
    SP --> M1["第 1 个 step 的 messages"]
    C1 --> M1
    SP --> M2["第 2 个 step 的 messages"]
    C1 --> M2
    C2 --> M2
{% endmermaid %}

## 6. 请求头：三个字段与四种 reason

`buildRequest`（`:1214-1288`）先把头规范化，再决定这次要不要记一条新的 `request/header`：

```js
const header = canonicalHeader({
  config,
  ...preparedCall?.adapterDefaults,
  ...(tools.length > 0 ? { tools } : {})
});
```

`canonicalHeader`（`dsh-session/lib/types/request-header.js`）做三件事，全是为了"能便宜地比较"：

- 空 `tools: []` 折叠成**缺省字段**（否则空数组和不存在永远不相等）；
- `adapterDefaults` 只在 `reasoningEffort === true` 或 `maxTokens === true` 时才保留；
- 其余原样。

比较函数也很朴素——config 用 `callConfigEquals`，adapterDefaults 逐字段比，tools **按顺序**逐条 `JSON.stringify` 相等：

```js
return at.length === bt.length && at.every((tool, i) => sameSchema(tool, bt[i]));
```

顺序也算身份，因为顺序就是提示词里工具说明的顺序。换个顺序，模型看到的东西就变了，不能算"同一个头"。

然后是四种 reason，决定这次请求"算不算新纪元"：

| reason | 触发条件 | prefix cache 影响 |
|---|---|---|
| `initial` | 会话第一次请求，没有基线 | 无缓存可用 |
| `resume` | 有基线但之前没记过头 | 从头建立 |
| `change` | 头与基线不等（换模型、换工具集） | 失效 |
| `series` | 头相等，但**显式开新系列** | 不失效 |

`series` 的判定是这一段的精华：

```js
const startsSeries = startsRequestSeries || this.requestSurfaceGeneration !== surfaceGeneration;
```

两种情况会开新系列：调用方显式要求，或者**表面换了一代**（`surface.contentGeneration` 变了）。典型场景就是压缩——头一个字没改，但消息序列已经被折叠过了，此时再拿旧缓存就是错的；可头的技术参数又确实没变，不该记成 `change` 让下游去重建一切。`series` 就是这个中间态。

{% mermaid %}
stateDiagram-v2
    [*] --> 无基線
    无基線 --> initial: 首次请求
    initial --> change: 头变了（换模型 / 工具集变了）
    initial --> series: 头没变，但表面换代
    series --> series: 又换代，头仍没变
    series --> change: 头变了
    change --> change: 继续变
    change --> series: 头稳住但表面换代
    initial --> resume: 有日志无基线（重放/接管）
{% endmermaid %}

另外有个 `request/context` 事件，只在四个字段任一变化时才追加：

```js
provider · model · contextWindow · systemPromptUpdate
```

`systemPromptUpdate: 'in-history'` 就是"系统提示词变了，但变化记录在历史里而不是头里"——正好呼应第 1 节那个误解三。

## 7. 工具 schema 也是装配物

工具不是"注册了就完事"，它同时影响三处：提示词里的说明段、请求头的 `tools` 数组、以及表面里的工具增删记录。

**呈现方式**由挂载 scope 声明（`dsh-agent-tool-presentation/lib/index.js:31`）：

```js
const Config = z.object({ mode: z.union(["native", "ptc"]).required() });
```

`native` 是把工具当普通函数调用暴露；`ptc` 是程序化调用（模型写一段程序去编排工具）。源码里这两个分支的实现差别不小——`ptc` 还得先 `inject(["ptcRuntime"])` 再 `presentAs(mode)`。

**工具集变了怎么办**？不推翻会话，而是往表面里追加一条 `developer/message`（`:1241-1259`）：

```js
session.append('developer/message', {
  message: {
    role: 'developer',
    content: [{ type: 'tool-addition', toolName }]   // 或 tool-removal
  },
  source: { kind: 'tool-registry' },
  ...(additions.length > 0 ? { headerSeq } : {})
}, { surfaceOp: 'append' });
```

这条消息的作用是告诉模型"你的工具清单变了，这是新增/移除的"，而不是让模型自己从系统提示词的差异里猜。而 `headerSeq` 只在有新增时带——移除不需要指认来源事件，新增需要。

顺带一个校验：`developer/message` 必须配 `developer` 角色，否则：

```js
throw new Error(`${subject} developer/message and developer role must occur together`);
```

## 8. surface：模型看得见的那一版日志

到了这里必须澄清一个容易混淆的点：**日志和表面不是一回事**。

- 日志（`session` 的 append-only 事件流）是"发生过什么"的唯一真相；
- 表面（surface）是"模型这次能看见什么"的投影。

所有事件都进日志，但只有 surface-eligible 的类型能进表面，而且必须显式声明自己是追加还是替换。这条规则由 `surfaceOpOf()` 硬校验（`surface.js:201` 起）：

| 违反情形 | 报错原文 |
|---|---|
| 不可入表面的类型带了 `surfaceOp` | `session event "${type}" is not surface-eligible and cannot carry surfaceOp` |
| 不可入表面的类型带了 `sourceEventSeqs` | `… cannot carry sourceEventSeqs` |
| 可入表面却没标记 | `session event "${type}" is surface-eligible and requires a surfaceOp marker` |
| op 形状不合法 | `… carries an invalid surfaceOp` |
| replace 不合法 | `… carries an invalid replace surfaceOp` |

`replace` 还有一条更隐蔽的约束：它必须配一个"影子价"（shadow price）claim，也就是"你替换掉的这段原来值多少 token"，否则 token-meter 会拒绝：

```
replace at seq 812 over range 640-811 has no adjacent shadow price (armed claim covers 700-811)
```

为什么要这么严？因为一旦允许"无价替换"，上下文压力的账就永远算不平——被遮蔽的内容既不在可见表面里，也不在计费里，token 计量会凭空变小，压缩阈值就失效了。

投影本身是增量的（`dsh-session/lib/index.js:1672`）：

```js
if (generation !== this.derivedGeneration) { this.derived = []; this.derivedNodes = 0; ... }
for (const seq of nodes.slice(this.derivedNodes)) {
  const msg = this.deriveEventMessage(this.log[seq]);
  if (msg) this.derived.push(msg);
}
return [...this.derived];
```

用 `contentGeneration` + `derivedNodes` 两个游标做缓存：表面没换代就只追加新节点，换代了就整个重算。返回的是新数组，但里面的 `Message` 是**共享且深冻结**的——`buildRequest` 里还有一道 `deepFreeze` 兜底。跑一次请求不能顺手改掉历史。

{% mermaid %}
flowchart LR
    subgraph LOG["日志（只追加，真相）"]
        direction TB
        E1["1 · user/message"] ~~~ E2["2 · assistant/message"] ~~~ E3["3 · tool/result"] ~~~ E4["4 · user/message"] ~~~ E5["5 · compaction/summary<br/>replace 1-3"]
    end
    subgraph SURF["表面（模型可见）"]
        direction TB
        V4["原样可见"] ~~~ V5["摘要（遮蔽 1-3）"]
    end
    E1 -.->|被遮蔽| X["不进表面"]
    E2 -.->|被遮蔽| X
    E3 -.->|被遮蔽| X
    E4 --> V4
    E5 --> V5
{% endmermaid %}

## 9. token 是怎么算的：一个拒绝一切配置的计量器

`dsh-token-meter` 的计价口径是固定启发式，只有一行常量（`:16`）：

```js
const CHARS_PER_TOKEN = 4;
```

按 block 类型分别估：文本是 `Math.ceil(block.text.length / 4) + BLOCK_OVERHEAD`，工具调用对 name 和 arguments 各自 `/4`，整体再加固定开销。它就是一句话：**4 个字符算 1 个 token**。

最有意思的是它的配置校验（`:683-684`）：

```js
function validateConfigKeys(config) {
  for (const key of Object.keys(config))
    throw new Error(`TokenMeterConfig: unknown key "${key}" (no settings are supported)`);
}
```

任何配置项都会抛错，一个都不接受。这不是没做完，是有意的：如果允许按部署调系数，那"我的上下文用了 60%"这句话就失去了跨部署意义——A 机器的 60% 和 B 机器的 60% 不是同一个东西。固定 4 字符/token，配合 provider 回来的真实用量做锚点，才能让阈值（第 10 节那个 0.8）在任何环境里都说得通。

对外它给三个投影（projection）：

| 投影 | 回答什么问题 |
|---|---|
| `tokenUsage` | 这次请求用了多少 token |
| `contextPressure` | 离上限还有多远（压缩靠它触发） |
| `contextBreakdown` | 这些 token 花在什么上（哪个工具结果最贵） |

压力值不是每次重新估，而是"provider 样本 + 自采样以来表面增减的启发式重计价"：拿到一次真实 usage 就校准一次，两次采样之间用 4 字符/token 增量推算。这样既不会每步都多花一次真实测量，又不会让估算漂太远。

## 10. 压缩只是"改写装配的输入"

把上面九节连起来看，压缩的定位就很清楚了：它不是装配的一个阶段，而是**对装配输入的一次改写**——把一段旧消息折叠成一条摘要，让 `deriveMessages()` 下次投影出来的表面变短。

阈值和保留比例是两个默认值（`compaction-basic/lib/index.js:15-17`）：

```js
const DEFAULT_THRESHOLD_RATIO = 0.8;   // 压力到 80% 触发
const DEFAULT_RETAIN_RATIO   = 0.16;   // 尾部 16% 逐字保留
```

实际阈值还要跟预算取小：

```js
thresholdTokens = Math.floor(Math.min(
  contextWindow * thresholdRatio,
  messageBudgetTokens - headroomTokens
));
```

也就是"窗口的 80%"和"除掉预留后的可用额度"谁小听谁的——不然给模型留了完成空间，却把它算进压缩阈值，永远压不下来。

摘要调用本身有个很漂亮的细节，源码注释直接说明了目的（`:292`）：

> replay the conversation prefix, then append the compaction instruction as the final user message **so the provider's warm prefix cache is reused**

即：不复用一次全新请求，而是把整段要被压缩的对话原样重放一遍，末尾追加一条"总结它"的用户消息。这样提供方那边的 warm prefix cache 还能命中，摘要成本从"重新读一遍全部"降到"只算新加的那条指令"。

摘要的格式是硬编码的八段模板（`:247-278`），外面包 `<compacted-summary>` 标签：

```
## Primary Request and Intent
## Key Technical Concepts
## Files and Code
## Errors and Fixes
## Pending Jobs
## Current Work
## Next Step
## Critical Context
```

配套的 Rules 里有几条很值得抄进自己的工程习惯：保留精确的文件路径、命令、错误字符串、标识符、数值和函数签名；忠实记录用户反馈，尤其是纠正；**不要提"压缩"这件事**；只输出 checkpoint 文本，不调工具；若已有 `<compacted-summary>` 块那就是上一版，别照抄，保留仍为真的事实、丢掉过时的、合并成单一摘要。

写入后还要包一层前导语（`:280`）：

> This is an automatically generated checkpoint condensing an earlier span of the conversation to free up context. Treat the captured context as established background and build on it without restating it. Continue the task directly from the messages that follow, without acknowledging this checkpoint.

压缩之外还有一道更便宜的工序：确定性剪裁（pruner）。它对超长工具结果做首尾保留、中间挖掉，标记是固定字符串（`compaction-tool-result-pruner/lib/index.js:9`）：

```js
const PRUNE_MARKER = "\n\n[... tool result middle pruned ...]\n\n";
```

默认 8192 阈值、保头 4096、保尾 1024，且 `headChars + marker + tailChars ≤ thresholdChars` 是硬校验——不然"剪裁"反而会变长。

最后一条边界规则：压缩区间不能切开一次工具调用的"请求/结果"配对。

```
compactRegion: start seq 640 is not a balanced boundary (would split a step's tool-call/result pair)
```

模型的训练/推理假设里，tool call 和 tool result 是成对出现的。切开之后，模型会看到"一个调用但没有结果"，行为立刻跑偏。所以压缩从哪切、到哪停，都受这个约束钳制。

压缩的完整流水线（三入口、事务写入、JSONL 落盘、重放恢复）在[上一篇](/2026/10/30/DSH-会话压缩策略详解/)里，这里不再重复。

## 11. 自己动手验证

上面所有引用都可以复现。装好的应用里源码就在 `app.asar` 中，解出来不难，但有个坑。

`app.asar` 的头部是 Chromium 的 Pickle 格式，前 16 字节是四个 u32：`4`、header pickle 大小、`header pickle 大小 - 4`、**JSON 字节长度**。真正可靠的边界只有最后一个字段：

```js
const fd  = fs.openSync(asar, 'r');
const buf = Buffer.alloc(16); fs.readSync(fd, buf, 0, 16, 0);
const jsonLen = buf.readUInt32LE(12);          // ← 唯一可信的长度
const dataBase = 8 + buf.readUInt32LE(4);      // ← 文件内容起点
const index = JSON.parse(scan(fd, 16, jsonLen).toString('utf8')).files;
```

我自己第一次是拿大括号配对去扫 header 找 JSON 边界，`JSON.parse` 直接抛错，还把整段原文吐进 stderr（两次、每次十几 KB）。改成读 `u32@12` 一次就对。**这个格式的边界只能信长度字段，不能靠内容扫描猜。**

拿到索引后，按路径把 `lib/*.js` 读出来就行。判断"谁在装配"最快的办法不是读文档，而是：

```bash
# 1. 谁调用了 assemble？
grep -rn "systemPrompt.assemble" lib/
# 2. 装配结果怎么进请求的？
grep -n "buildRequest" lib/index.js
# 3. 表面里到底有什么？
grep -n "surfaceOp" lib/types/surface.js
```

第二个可做的验证是改一个 `order` 再看输出。把 `TOOL_GREP` 的 `order` 从 1500 改成 999，重建后看提示词里工具说明的位置——它能直接证明"段位表就是真实排序依据"，而不是某种约定俗成的写法。

在会话日志里搜 `request/header`，你还能看到 `reason` 从 `initial` 一路变成 `series` 的完整轨迹——那是最省事的实证。

## 12. 设计取舍：为什么装配要长成这样

拆完这一遍，我最想记下来的不是那张段位表，而是几个贯穿始终的取舍。

**一、宁可炸，也不静默降级。** 插值找不到变量就抛错，表面事件少个 `surfaceOp` 就抛错，替换没有影子价就抛错，两个 `complete` 段就抛错。这四处都在做同一件事：把"配置错了"从"模型表现奇怪"里剥离出来。前者十分钟能修，后者能查一天。

**二、替换，而不是叠加。** `complete: true` 段不是"再加一段"，而是"整段就是它"。人格、模式这类东西如果允许叠加，最终会拼出一个谁都没设计过的人格；允许替换，语义就清楚了——谁声明，谁负责。

**三、把"记下的"和"看见的"分开。** 日志只追加、表面靠投影、压缩只遮蔽不删除。这三条让"撤销一次压缩"变成可能（重新投影），也让"这次请求到底看了什么"变成可审计的问题。代价是所有读日志的人都得先理解 surface 这一层——但换来的是可重放、可对比、可回滚。

**四、稳定的往前放，易变的往后放，一次性的事不进系统提示词。** 段位表把身份和工具说明固定在前，把工作目录这类每步都变的东西做成"额外一条消息"。这条纪律直接决定了 prefix cache 的命中率，也决定了长会话的成本曲线。

**五、分散是模块化的代价。** 装配横跨 agent-loop（编排）、system-prompt（段注册）、session（表面投影）、token-meter（计量）四个包，没有一个"看看就懂"的入口。唯一的对冲办法是——真去读一遍产物代码，把那条链自己在纸上画一遍。

画完这张链路图，我对"上下文"这个词的理解变了：它不是一份文档，而是一条**每次请求都重新走一遍的流水线**——注册表决定骨架，扩展点决定此刻的事实，投影决定模型能看见多少历史，计量器决定这条流水线什么时候需要瘦身。

---

**相关阅读**：

- [DSH 会话压缩（Compaction）策略详解](/2026/10/30/DSH-会话压缩策略详解/)——这条流水线什么时候需要瘦身、怎么瘦身、瘦完怎么落盘与重放。
- [DSH Agent 主循环：一条用户消息的完整旅程](/2026/10/30/DSH-Agent主循环/)——把这些零件转起来的那台发动机：轮次、步骤、工具池与取消。
- [DSH 沙箱设计：一次 bash 调用，到底被关进了什么](/2026/11/02/DSH-沙箱设计/)——真正跑命令的时候，是谁按着闸刀：同世界围栏、三条缝与升级阶梯。
