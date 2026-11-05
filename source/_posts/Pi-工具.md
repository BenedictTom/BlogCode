---
title: Pi 怎么定义一个工具：一张卡片上的十个字段
date: 2026-11-05 01:35:00
categories:
  - Pi
tags:
  - Pi
  - Agent
  - Tool
  - TypeBox
cover: /images/Pi-工具/cover.jpg
description: 从 ToolDefinition 的字段出发，讲清工具的参数校验、执行模式、并发冲突、模型输出的兼容层与结果回传——以及一个工具为什么要带 UI 渲染函数。
---

前三篇讲了循环、会话、上下文。这一篇讲循环里被调用的东西：**工具**。

大多数框架里，工具的形态是一个对象：`{ name, description, parameters, execute }`。够用，但只够用到第二个工具为止。一旦你想要：并行执行、渲染到终端、按需加载、给模型不同的可见性、兼容模型五花八门的参数输出——这四个字段就不够了。

Pi 的 `ToolDefinition` 有十几个字段。这一篇就是把它们一个个拆开，看每个字段对应哪个真实问题。

## 0. 先看全貌

内置 8 个工具（`packages/coding-agent/src/core/tools/index.ts:95`）：

```ts
type ToolName = "read" | "bash" | "powershell" | "edit" | "write" | "grep" | "find" | "ls";
```

三套装配入口：全量（`createAllToolDefinitions`）、编码用（`createCodingToolDefinitions`）、只读用（`createReadOnlyToolDefinitions`）。同一个工具集，按会话模式裁剪——这就是只读模式能"真的只读"而不是"靠提示词自觉"的地方。

一个工具的完整定义长这样（`core/extensions/types.ts:599-688`，省掉注释与泛型细节）：

```ts
interface ToolDefinition<TParams, TDetails, TState> {
  name: string;
  label: string;
  description: string;
  promptSnippet?: string;
  promptGuidelines?: string[];
  parameters: TParams;            // TypeBox schema
  constrainedSampling?: ...;
  renderShell?: ...;
  prepareArguments?(args: unknown): unknown;
  outputSchema?: ...;
  exposure?: "model" | "model-only" | "codemode";
  namespace?: string;
  reachesTools?: boolean;
  defaultActive?: boolean;
  prepareLoadout?(...): ...;
  executionMode?: "parallel" | "sequential";
  execute(toolCallId, params, signal, onUpdate, ctx): Promise<AgentToolResult<TDetails>>;
  renderCall?(...): ...;
  renderResult?(...): ...;
}
```

下面按"这个字段解决什么问题"来分。字段名照抄，细节以源码为准（HEAD `395f3e0`，`pi` 1.5.0）。

## 1. 声明：模型看到的那部分

**`description`** 是给模型看的。它比 name 重要得多——模型选不选这个工具，基本靠这一段。

**`promptSnippet`** 和 **`promptGuidelines`** 进 system prompt 的 `<tools>` 和 `<rules>` 两节。这是上一篇讲的"分节拼装"的下游：工具不只是运行时的一个函数，它还往 system prompt 里**贡献文字**。这个设计很实用——工具的描述和使用禁忌跟着工具走，不用在 prompt 里维护一份平行的说明。

**`parameters`** 的类型是 `TSchema`（TypeBox），注释写得很直白（`:610-611`）：`Parameter schema (TypeBox)`。

这里有个选择值得说：Pi **没有用 zod**。TypeBox 本身产出的就是 JSON Schema，直接能发给模型；而 zod 要先转一道。少一道转换，就少一类"转换后 schema 变形导致模型瞎猜参数"的 bug。

顺带解释一个常见困惑：既然 schema 是 JSON Schema，为什么不能直接把整个工具对象塞给模型？看 `toToolDeclaration`（`packages/ai/src/utils/transcript.ts:123`）干了什么：

```ts
// 只保留 name / description / parameters / constrainedSampling
JSON.parse(JSON.stringify(tool.parameters))   // 剥掉 TypeBox 的非枚举 kind 标记
```

它做了两件事：**白名单**（executable 字段一个不漏地剔掉）和**序列化往返**（把 TypeBox 挂在对象上的 `kind` 之类不可枚举标记洗掉）。第二件事是为了让 `declarationsEqual`（`:141`）能纯靠字符串比较——缓存命中和"工具声明变没变"都靠这个判断。

**`exposure`** 决定这个工具对模型可见不可见。三个值：`model`（默认，能看见能调用）、`model-only`（只在特定上下文里给）、`codemode`（**不给模型，只能被脚本调用**）。第三个值是 Codemode 那一篇的主角，先记住。

## 2. 校验：先 coerce，再把错误交回模型

模型给你的参数，经常是"schema 上不完全对但意思对"的：数字给成字符串 `"42"`，数组给成单个对象。

Pi 的校验函数 `validateToolArguments`（`packages/ai/src/utils/validation.ts:54`）做了三步：

```ts
compile(schema, { formats, coerce: true, unresolvedRefs: "reject" })
parse(structuredClone(args))
// 失败：throw new Error(`Validation failed for tool "${name}":` + 逐条 "- path: message")
```

**coerce: true** 是宽容——`"42"` 会被转成 `42`。**structuredClone** 是先复制再校验，保证校验过程不改调用方手里的对象。**unresolvedRefs: "reject"** 是严格——schema 里有解析不了的 `$ref` 就直接拒绝，而不是放行一个半懂的校验。

编译结果按 schema 对象缓存在 WeakMap 里（`:6-18`）。用 WeakMap 而不是 Map，是因为 schema 对象可能来自动态生成，用强引用会泄漏。

失败之后去哪？不是抛给用户，而是**包成一条 `isError` 的工具结果回给模型**（`packages/agent/src/agent-loop.ts:780-786`）。这是 agent 设计里一个很重要的判断：**校验错误是模型的输入，不是程序的异常**。模型看到 `Validation failed for tool "edit": - edits.0.newText: expected string`，下一步就会自己改参数重试；而如果抛成异常终止循环，就只能人肉介入。

{% mermaid %}
sequenceDiagram
  participant M as 模型
  participant L as agent-loop
  participant V as validateToolArguments
  participant T as 工具.execute
  M->>L: toolCall(name, arguments)
  L->>L: prepareArguments（兼容层）
  L->>V: validate（coerce + 缓存）
  alt 校验失败
    V-->>L: Validation failed: path: message
    L->>M: toolResult{isError:true}
  else 校验通过
    V-->>L: 合法参数
    L->>T: execute(信号, onUpdate)
    T-->>L: AgentToolResult
    L->>M: toolResult{content}
  end
{% endmermaid %}

## 3. `prepareArguments`：一个只被用了一次的字段

这个字段在 schema 校验**之前**跑，注释说它是"schema 校验前兼容层"（`types.ts:617`）。全仓库只有一个工具用了它：`edit`。

为什么是它？因为 `edit` 的参数最复杂（一组编辑操作），而模型对它的输出最花样。源码注释（`tools/edit.ts:100-130`）：

> Some models (Opus 4.6, GLM-5.1) send edits as a JSON string instead of an array. Others send a single edit object instead of a one-element edits array.

于是 `prepareEditArguments` 把 JSON 字符串解析成数组、把单个对象包成单元素数组、把老版本的 `oldText/newText` 折成 `edits`。

这个字段的存在本身就是一个诚实的信号：**模型输出的不规范性不该由 schema 兜，而该由一层显式的、可命名的兼容逻辑兜**。兜不住的，就让它校验失败、回给模型——而不是在 schema 里写一堆 `oneOf` 把宽容度藏起来。

执行顺序是先 `prepare` 再 `validate`（`agent-loop.ts:704-716`、`:737`）。顺序反了就没意义了。

## 4. 并发：默认并行，但同文件串行

一批工具调用怎么执行？`agent-loop.ts:526-532` 的判断很干脆：

- 批内**任一**工具声明 `executionMode: "sequential"` → 整批串行
- 否则 → 并行（默认值 `?? "parallel"`，`packages/agent/src/agent.ts:261`）

注意是"任一即整批"，不是"逐个判断"。因为工具之间可能互相依赖，混着跑会让顺序不可预测；而既然有一个要求串行，那说明它可能依赖前面所有工具的结果。

{% mermaid %}
flowchart TD
  A["一批 toolCall"] --> B{"批内有工具声明<br/>executionMode: sequential?"}
  B -->|是| C["整批串行执行"]
  B -->|否| D["并行执行"]
  D --> E{"两个调用改同一个文件?"}
  E -->|是| F["withFileMutationQueue<br/>按文件排队"]
  E -->|否| G["真并行"]
{% endmermaid %}

但内置 8 个工具**一个都没有声明 sequential**。那 `write` 和 `edit` 同时改一个文件怎么办？靠另一层：**按文件的串行队列**（`tools/file-mutation-queue.ts:28-33`）：

> Operations for different files still run in parallel.

也就是并发控制在"文件"这个粒度上，而不是"整批"。两个 `write` 改不同文件可以真并行，改同一文件就排队。这比"整批串行"精细得多——`grep` 和 `write` 完全可以同时跑。

顺带一提，嵌套工具调用（工具里再调工具）复用同一判断（`core/nested-tool-calls.ts:203-205`），所以扩展写的工具也自动享受这套并发规则。

## 5. 停止：`terminate` 是"全票通过"

`AgentToolResult` 有个 `terminate?: boolean`（`packages/agent/src/types.ts:424-446`），注释（`:441-445`）：

> Hint that the agent should stop after the current tool batch
> ... every finalized tool result ... sets this to true

**必须批内每一个结果都置 true 才停**。为什么不是"任一即停"？因为一批里有三个工具，其中一个说"我完事了"，不代表另外两个的任务不需要继续。全票通过把"停止"变成一个协作决策，而不是某个工具的独断。

实现见 `agent-loop.ts:700-702`。

## 6. 结果：`structuredContent` 不进模型

`AgentToolResult` 的字段里有个容易被忽略的：

| 字段 | 去哪 |
| --- | --- |
| `content` | 给模型 |
| `details` | 给 UI 渲染 |
| `structuredContent` | 给程序（注释：`Not sent to the model`） |
| `usage` | 记账 |
| `isError` | 标记失败 |
| `terminate` | 请求停止 |

三个出口分开，是因为三者的需求完全不同。模型要的是**短、可读、够用**；UI 要的是**结构化的、能折叠和着色的**；程序要的是**类型化的**。混在一起，就只能三者都迁就最差的那个。

这也是为什么 `ToolDefinition` 里还有 `renderCall` / `renderResult` 两个函数——**工具自带渲染**。这看起来像是把 UI 耦合进了工具，但它解决一个真问题：只有工具自己知道"这个结果里哪部分是重点"。通用的 JSON 美化渲染永远做不到 `edit` 那种"红绿 diff"的效果。

代价是扩展作者要写两遍逻辑。Pi 的取舍是：给你 `details` 兜底（不写 render 就用默认渲染），写了就更好。

## 7. 注册：一行装进运行时

扩展里加工具就两步（`examples/extensions/hello.ts:8-27`）：

```ts
const helloTool = defineTool({
  name: "hello", label: "Hello",
  description: "Say hello",
  parameters: Type.Object({ name: Type.String() }),
  execute: async (_id, { name }) => ({ content: [{ type: "text", text: `Hello, ${name}!` }] }),
});
pi.registerTool(helloTool);
```

`registerTool` 的签名（`extensions/types.ts:1716-1718`）接受泛型的 `ToolDefinition`，然后由 `wrapToolDefinition`（`tools/tool-definition-wrapper.ts:27-49`）摊平成运行时需要的 `AgentTool`。

注意这里**没有 hooks 字段**——工具定义里不写"调用前/调用后做什么"。钩子是扩展级的 `pi.on("tool_call" / "tool_result" / ...)`（`types.ts:1705-1709`）。这个分离很干净：**工具只负责"做一件事"，横切逻辑（审计、权限、脱敏）统一挂在扩展的钩子上**。否则每个工具都要重复实现一遍"要不要记录日志"。

## 8. 小结

一个工具在 Pi 里是三层东西：

1. **声明**（给模型）：`description`、`parameters`（TypeBox，直出 JSON Schema）、`promptSnippet`、`exposure`
2. **执行**（给运行时）：`execute`、`executionMode`、`prepareArguments`、返回的 `AgentToolResult`
3. **呈现**（给人）：`details`、`renderCall`、`renderResult`

三层各自有独立的开关和失效条件，所以才能做到：同一个工具，在只读模式下不出现、在 Codemode 模式下不给模型、在并行批里按文件排队、校验失败时把错误当消息回给模型。

如果只记一句话：**工具不是"一个函数加一个 schema"，而是一张有明确出入口的卡片**——入口兼容模型的坏习惯，出口分离三种读者。

---

**相关阅读**

- [Pi 的一次请求：agent loop 里到底发生了什么](/2026/11/05/Pi-Loop/)
- [Pi 的上下文工程：每次请求，模型到底看到了什么](/2026/11/05/Pi-上下文/)
- [Pi 的会话树：一条对话为什么不是一条线](/2026/11/05/Pi-会话树/)
