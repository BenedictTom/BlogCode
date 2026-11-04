---
title: pi-ai：43 个供应商，10 种协议，一套流
date: 2026-11-05 02:10:00
categories:
  - Pi
tags:
  - Pi
  - pi-ai
  - LLM
  - Streaming
cover: /images/Pi-ai/cover.png
description: 拆 pi-ai 的包结构：43 个 provider 只落在 10 种 wire 协议上，11 个流式事件、两套认证路径、生成式模型目录，以及它为什么被设计成一个"无状态工具箱"。
---

前四篇讲的都是 `pi` 这个终端 agent。从这一篇起换个角度：**它底下那些包**。

先看最底层的 `@earendil-works/pi-ai`（1.5.0，HEAD `395f3e0`）。这个包的名字很朴素，问题也很朴素：**怎么用一套代码接 43 家模型供应商**。

答案不是写 43 套适配，而是——43 个供应商，其实只有 10 种协议。

## 0. 两个数字

```
providers/  → 43 个 provider 工厂
types.ts    → KnownApi 只有 10 种
```

`KnownApi`（`packages/ai/src/types.ts:64-75`）：

```ts
type KnownApi =
  | "openai-completions" | "mistral-conversations" | "openai-responses"
  | "azure-openai-responses" | "openai-codex-responses" | "anthropic-messages"
  | "bedrock-converse-stream" | "google-generative-ai" | "google-vertex" | "pi-messages";
```

而 `src/api/` 下正好 43 个文件、14,002 行，**一个文件对应一条 wire 协议**：`anthropic-messages.ts` 1,961 行、`openai-completions.ts` 1,739、`openai-codex-responses.ts` 1,723、`bedrock-converse-stream.ts` 1,461。

所以整个包的重心不是"43 个适配器"，而是**十套协议实现 + 一层很薄的供应商映射**。供应商之间的差异，绝大部分被压缩成了"元数据"（baseUrl、认证方式、模型清单、能力开关），而不是代码。

{% mermaid %}
flowchart TD
  A["43 个 provider 工厂<br/>providers/&lt;id&gt;.ts（各 ~10 行）"] --> B["createProvider<br/>id + auth + models + api"]
  B --> C["10 种 wire 协议实现<br/>api/*.ts"]
  C --> D["AssistantMessageEventStream<br/>11 种流式事件"]
  B --> E["认证<br/>ApiKeyAuth / OAuthAuth"]
  E --> D
  F["catalog/ 源目录<br/>models.dev 等"] -.生成.-> G["providers/&lt;id&gt;.models.ts"]
  G --> B
{% endmermaid %}

## 1. 三层与三个契约

`pi-ai` 的结构可以切得很干净：

| 层 | 位置 | 职责 |
| --- | --- | --- |
| 协议层 | `src/api/*.ts` | 把统一的 `Context` 变成某家 API 的请求、把响应流成统一事件 |
| 供应商层 | `src/providers/*.ts` | 说明"这家叫什么、怎么认证、有哪些模型、用哪个协议" |
| 目录层 | `catalog/` + `*.models.ts` | 模型清单、定价、上下文窗口、能力 |

有三个接口把这三层缝起来。

**契约一：`Provider`**（`src/models.ts:158`），必填 `id / name / auth / getModels / stream / streamSimple`，可选 `refreshModels / filterModels / generateImages / classify`。

**契约二：`ProviderStreams`**（`src/types.ts:327`），协议模块要提供：

```ts
stream(model, context, options?): AssistantMessageEventStream
streamSimple(...): AssistantMessageEventStream
```

**契约三：`createProvider`**（`src/models.ts:1080`）——把前两个拼起来的最小入口。缺实现会抛：

```
at least one of "api", "images", or "classifiers" is required
```

一个供应商工厂可以短到什么程度？`src/providers/deepseek.ts:6-15`，整个文件 10 行：

```ts
export const deepseek = createProvider({
  id: "deepseek",
  auth: { apiKey: envApiKeyAuth("DeepSeek API key", ["DEEPSEEK_API_KEY"]) },
  api: openAICompletionsApi(),
});
```

10 行里没有一行是"适配代码"——`openAICompletionsApi()` 说明它走 OpenAI 兼容协议，剩下的全在模型目录里。

一个前提要纠正：**`src/providers/` 下没有子目录**（只有一个 `providers/images/`）。43 个 provider 都是扁平的 `<id>.ts`，每个还配一个 14 行的 `<id>.models.ts`。目录结构本身就在告诉你：这不是 43 个模块，是 43 个**声明**。

## 2. 流：11 个事件和一个"活对象"

协议层吐出的东西是 `AssistantMessageEvent`（`src/types.ts:831`），11 个变体：

```
start
text_start / text_delta / text_end
thinking_start / thinking_delta / thinking_end
toolcall_start / toolcall_delta / toolcall_end
done / error
```

三个块（文本、思考、工具调用）各有"开始/增量/结束"三拍，所以是 3×3 + start + done + error。

终止只有两个（`src/types.ts:844-847`）：

```ts
{ type: "done";  reason: Extract<StopReason, "stop"|"length"|"toolUse"|"deferred">; message }
{ type: "error"; reason: Extract<StopReason, "aborted"|"error">; error }
```

`StopReason` 有 7 个值（`:497`）：`pending / stop / length / toolUse / error / aborted / deferred`。其中 `pending` 是"还在生成"，所以只能出现在中间态；`deferred` 是"模型选择延后回答"（跟 pi 的 deferred tool loading 配套）。

{% mermaid %}
flowchart LR
  S["start<br/>partial 为空壳"] --> T1["text_start"] --> T2["text_delta ×N"] --> T3["text_end"]
  S --> K1["toolcall_start"] --> K2["toolcall_delta ×N"] --> K3["toolcall_end"]
  T3 --> D{"done 或 error"}
  K3 --> D
  D -->|done| R1["reason: stop / length / toolUse / deferred<br/>带最终 message"]
  D -->|error| R2["reason: aborted / error<br/>带 error 对象"]
{% endmermaid %}

这里有个注释非常值得抄下来（`src/types.ts:820`）：

> `partial` 是"共享的 live 响应对象"，不是快照。

意思是 `*_start` 事件里那个 `partial` 对象是**空的但会被后续 delta 持续填充**的。它的身份是"正在构建的那条消息"，不是"当时的快照"。所以：

- `*_start` 时不要读内容
- `*_delta` 时读增量
- `*_end` 之后才可信

这个设计省掉大量对象拷贝（一次长回复几百个 delta，每个都拷一份 partial 是不可能的），代价是**调用方必须理解它是有状态的**。事件流的实现 `AssistantMessageEventStream`（`src/utils/event-stream.ts:97`）继承自通用的 `EventStream<Event, Result>`，完成判定就是 `done` 或 `error`，并在结束前回填 `durationMs`。

## 3. 消息与用量：字段设计里的判断

`AssistantMessage`（`src/types.ts:593`）里有个细节值得单独说：

```ts
content: (TextContent | ThinkingContent | ToolCall)[]
api, provider, model, responseModel?, usage, stopReason,
errorMessage?, rawStopReason?, timestamp, durationMs?
```

- **`model` 和 `responseModel` 分开**：你请求 `gpt-x`，服务端可能路由到 `gpt-x-0613`。两个字段都留着，账单和复现才对得上。
- **`rawStopReason` 和 `stopReason` 分开**：统一后的 `stopReason` 给逻辑用，原始的给排查用。
- **`ThinkingContent.redacted`**：这是 Anthropic 系的"思考已被加密"标记。不设这个字段，你就没法区分"没有思考"和"有思考但看不到"。

`Usage`（`:467`）也有一处明确的注释：`reasoning` 是 `output` 的**子集**，不是额外项。这个区分很关键——很多工具会把 reasoning token 重复计入总量，导致成本算翻倍。

## 4. 认证：把"刷新"和"转表头"拆开

`ProviderAuth`（`src/auth/types.ts:256`）有两种：

```ts
{ apiKey?: ApiKeyAuth; oauth?: OAuthAuth }
```

注释要求"至少有一个"，哪怕是本地无 key 的服务也要提供 `apiKey` 语义。为什么？因为**统一路径比特例便宜**：代码里只有一条"取凭据"的路，而不是"有 key 走 A、无 key 走 B"。

`ApiKeyAuth.resolve()` 的语义是**逐字段合并**：`credential.key ?? env("...")`，返回 `undefined` 表示未配置。这解释了 Pi 的一个行为：你在配置文件里存了 key，环境变量里的会被忽略；配置文件里没有，才回退环境变量。

OAuth 那边的拆分更值得看（`:225`）：

```ts
OAuthAuth { login, refresh, toAuth }
```

`refresh` 是**网络调用**，`toAuth` 必须是**无副作用的转换**。拆成两半的原因写在类型注释里：让 `Models` 能在存储锁内刷新。

这是个很实际的并发问题：token 快过期时，多个请求可能同时发现要刷新。如果 `toAuth` 里藏着刷新逻辑，锁的粒度就只能包住整个请求构造；拆开之后，锁只包住"刷新 + 写回"，`toAuth` 在外面随便跑。

9 个 OAuth flow（`src/auth/oauth/load.ts:14-23`）：anthropic / openaiCodex / openaiChatGPT / githubCopilot / openrouter / kimiCoding / meta / xai / radius。全部用**变量 specifier 动态 import**，避免打包器把 Node-only 的代码跟进浏览器构建。

注入点在 `src/models.ts:878`：

```ts
const apiKey = options?.apiKey ?? auth.apiKey;
```

然后覆盖 `baseUrl`、合并 `headers`、拼 `requestOptions`，最后 `provider.stream(...)`。协议层只消费 `options.apiKey`，缺了就抛 `No API key for provider: ${provider}`（`src/api/anthropic-messages.ts:851-853`）。

还有一个环境变量的坑值得记一笔：`src/env-api-keys.ts:1` 的第一行是

```ts
// NEVER convert to top-level imports - breaks browser/Vite builds
```

用 `node:` 拼接 + 动态 import，就是为了让这个包在浏览器里也能跑。

## 5. 模型目录：为什么是生成的

`src/models.generated.ts:1` 第一行就是：`// This file is auto-generated by catalog/generate.ts`。

真源在 `packages/ai/catalog/`：`providers/` 44 个文件、`families/` 5 个（anthropic / deepseek / google / kimi / openai）、`sources/`（models.dev、OpenRouter、Vercel、NVIDIA）、`define.ts`、`build.ts`、`generate.ts`。

构建四步（`catalog/define.ts:36-42`）：`models()` → 打上 `compat` 默认与 family 规则 → `finalize()` → `finalizeAll()`。

上游数据源是 `catalog/sources/models-dev.ts:6`：

```ts
const MODELS_DEV_URL = "https://models.dev/experimental/v2.0/api.json";
```

为什么要把模型清单做成"构建期生成"而不是"运行时拉取"？三个理由：

1. **离线可用**。agent 装在没网的环境里，也得知道模型的上下文窗口。
2. **可复现**。同一份代码，模型清单不会因为上游改了就悄悄变。
3. **能加人工规则**。`families/` 里那 5 个文件就是人工维护的"这家模型的特殊行为"，比如怎么算 thinking 档位、怎么算缓存价格。这些上游数据源不会告诉你。

代价是：**清单会过期**。所以 `Provider` 接口留了 `refreshModels?:` 这个可选项，让某些供应商（比如 OpenAI 兼容的自建服务）能在运行时刷新。

一个诚实的说明：`catalog/README.md:5` 写了 `src/providers/data/<provider>.json` 是 gitignored 的生成物，我这次的 checkout 里这个目录不存在，所以**没统计到模型条目总数**。这个数字我不想猜。

## 6. StringEnum：一个 24 行的兼容补丁

`src/utils/string-enum.ts:3-5` 的注释把来龙去脉说清楚了：

> Creates a string enum schema compatible with Google's API and other providers that don't support anyOf/const patterns: `{ type: "string", enum: [...] }`

有些 API 不支持 JSON Schema 的 `anyOf` / `const` 写法。于是这个工具返回一个**裸对象**而不是 schema 构造器调用：

```ts
{ type: "string", enum: values, description?, default? }
```

关键在 `:12` 的注释：返回裸对象，是为了让 `Static<typeof Schema>` 仍然能推出字面量联合类型。也就是说，它在不破坏 TypeScript 类型推导的前提下，把 schema 降级成所有供应商都能吃的最简形式。

24 行代码，解决的是"跨供应商 schema 方言"问题。这类补丁是接很多家模型时必然会攒出来的——它不该被藏起来，而该有个名字、有注释、被导出（`src/index.ts:42`）。

## 7. 无状态工具箱：transcript 与 validation

`pi-ai` 里最被复用的不是 `Models` 门面，而是一堆纯函数：

| 函数 | 干什么 |
| --- | --- |
| `toToolDeclaration`（`transcript.ts:123`） | 工具定义 → 给模型的声明（白名单 + 剥 TypeBox 标记） |
| `declarationsEqual`（`:141`） | 两个声明是否等价（纯字符串比较，为缓存服务） |
| `validateToolArguments`（`validation.ts:54`） | 参数校验 + coerce |
| `normalizeContext`（`transcript.ts:30`） | 把 `Context` 折成带 brand 的 `TranscriptContext` |
| `collapseSystemMessages`（`:113`） | 按模型能力折叠中途 system 消息 |

这些函数**没有状态、没有 I/O、可单独测**。这一点在下一篇写 durable 时会看到价值：`packages/durable` 依赖 `pi-ai`，但**不依赖 `pi-agent-core`**——它直接 import 这些工具子路径（`utils/transcript`、`utils/validation`、`utils/estimate`、`utils/retry`），完全绕过 agent 层。

## 8. 依赖方向证明分层

看依赖图最省事：

```
ai            → pi-schema, pi-telemetry        （不 import 任何上层）
agent         → pi-ai
coding-agent  → pi-agent-core + pi-ai
durable       → pi-ai（不依赖 pi-agent-core）
```

`pi-ai` 从不 import 上层包。`AgentMessage` 和 `convertToLlm` 都在 `packages/agent`，`packages/ai` 里只有 `Message`——**"agent 的消息可以是自定义角色"这个应用层概念，没有渗进模型层**。

这条边界的意义：`pi-ai` 可以被任何东西当"模型 SDK"用，包括一个不需要 agent 的服务。durable 就是这么干的。

## 9. 小结

`pi-ai` 的核心判断只有一句：**供应商之间的差异，主要是数据差异，不是代码差异**。

所以它做成：

- 10 种协议实现（代码量都在这里）
- 43 个十行工厂（声明）
- 一套生成式目录（数据）
- 一堆无状态纯函数（可复用）

顺着这个思路再看那些"奇怪的"设计——`partial` 是活对象、`model` 与 `responseModel` 分开、OAuth 拆 `refresh`/`toAuth`、StringEnum 返回裸对象——都能归结成同一件事：**把状态留在最小的地方，把差异压进数据里**。

---

**相关阅读**

- [Pi 入门：一个把"极简"当真了的 agent](/2026/11/05/Pi-入门/)
- [Pi 怎么定义一个工具：一张卡片上的十个字段](/2026/11/05/Pi-工具/)
- [Pi 的上下文工程：每次请求，模型到底看到了什么](/2026/11/05/Pi-上下文/)
