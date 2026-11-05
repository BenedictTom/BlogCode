---
title: Codemode 与 MCP：先拒绝，为什么又加回来
date: 2026-11-05 20:00:00
categories:
  - Pi
tags:
  - Pi
  - MCP
  - Codemode
  - Agent
cover: /images/Pi-MCP与Codemode/cover.jpg
description: Pi 曾经在官网上写着“不支持 MCP”，作者还专门写过一篇《你根本不需要 MCP》。一年后，MCP 进了 Pi 的核心，而且默认藏进一个 JavaScript 沙箱里。这篇文章把两边的原文摊开，讲清楚他们当初拒绝的到底是什么，以及这次“加回来”改的是哪一层。
---

## 一、一条被删掉的官网声明

如果你在 2025 年打开 pi.dev，会看到一句很硬的话：**Pi 不支持 MCP**。作者 Mario Zechner 还写过一篇流传挺广的文章，标题直接叫《What if you don't need MCP at all?》——你根本不需要 MCP。

然后 2026 年 9 月 29 日，Earendil 官方博客发了一封"邮件"，标题是《"You Said No MCP!"》，第一段就把话挑明了：

> 如果你以前去过 pi.dev，你会看到一条骄傲的声明：Pi 不支持 MCP。……然而，只要你升级 Pi，就会发现 MCP 现在是一等功能。发生了什么？

这篇文章想回答的就是这个"发生了什么"。因为答案不是"真香"两个字能打发的——它牵扯到一个更普遍的问题：**当你的 agent 已经能跑 bash、能写代码，工具到底该以什么形式进上下文？**

## 二、先看清楚，当初拒绝的到底是什么

把 Mario 那篇文章读完，你会发现他骂的其实不是"MCP 这个协议"，而是"当时那批 MCP server 的形态"。

他的三个理由，一条比一条具体。

**第一，上下文成本。** 他拿两个最常被推荐的浏览器系 MCP server 做了量化：Playwright MCP 有 21 个工具，光工具定义就要吃掉 13.7k tokens，占 Claude 上下文的 6.8%；Chrome DevTools MCP 更狠，26 个工具、18.0k tokens、9.0%。这些 server 要"覆盖所有情况"，所以工具多、描述长，一次会话还没开始干活，上下文已经先被工具清单啃掉一成。

**第二，不可组合。** MCP server 返回的结果必须穿过 agent 的上下文，才能落盘、才能和别的结果拼接。也就是说，你想"先抓 500 条，再用脚本过滤，只把剩的 12 条给模型看"——做不到，中间那 500 条必须先变成 token 灌进对话。子 agent 能绕开一部分，但会引入子 agent 自己的一堆问题。

**第三，改不动。** 想给一个现成 MCP server 加个小功能，你得读懂它整个代码库——连同你的 agent 一起读。

于是他给了个替代方案：**别用 MCP server，让 agent 直接跑 CLI 脚本 + 写代码。**

他把自己常用的浏览器操作拆成四个 Node 脚本——`start.js`（起 Chrome，可带登录态）、`nav.js`（导航）、`eval.js`（在页面里执行 JS）、`screenshot.js`（截图），再加一个 README 说明怎么用。喂给 agent 的全部内容，就是这个 README：**225 tokens**。

对比一下那个 13.7k，差距是六十倍。而且这套东西还顺手解决了另外两个问题：输出可以重定向到文件不进上下文；几个调用可以用一条 bash 串起来。要加工具？再写一个脚本、README 补一行就行——他的"元素选择器"和"取 httpOnly cookie"两个工具就是这么加上去的，前后不到一分钟。

读到这儿你应该能感觉到：他真正想说的是，**模型本来就会 bash、会写 JS，这些能力是免费的；把工具重新描述成 JSON Schema 再塞回去，是在为模型已经会的事情重复付费。**

这套做法能成立，靠的是三件很朴素的事。

一是**知识已经在模型里了**。告诉一个模型"用 `document.querySelectorAll('a')` 数链接"，它不需要你解释 DOM API；但你写一份 schema 描述"search 工具接受 query 字符串、返回数组"，它反而要花力气去理解你的抽象。用 bash 和 JS 的好处是，你复用的是预训练里已经付过费的那部分。

二是**按需读取**。README 只在需要浏览器的时候读一次，不读就不占上下文。这跟后来 Anthropic 的 skills 是同一个思路——渐进式披露：先给一行描述，需要时再展开全文。他自己也承认，skills 把这件事做得更正式，并且能覆盖到非技术用户。

三是**输出可以不过脑子**。脚本的 stdout 可以重定向进文件，模型只在需要的时候 `head` 一下。这一步在只有工具调用的 harness 里做不到，因为工具结果必须回灌对话。

代价同样清楚：工具要自己维护，没有统一的发现机制，换一个 agent 就要重新接一遍（他给自己的解法是 `~/agent-tools` 加 PATH 别名）。这也埋下了后面转向的伏笔——当 MCP 生态足够大，你不可能要求每个人都维护一套自己的脚本。

## 三、那为什么后来又要加回来

官方的解释分两层，第一层很朴素，第二层才是关键。

第一层是"世界不是静止的"。这一年 MCP 自己变了：2025-06-18 那版把服务器明确成 OAuth Resource Server、加了结构化工具输出；2026-07-28 那版更是把协议级会话、`initialize` 握手、GET 流全部删掉，改成"每个请求自带元数据"的无状态形态。当年被吐槽的那些毛病，有一部分确实是协议在替 server 背锅。

但官方紧接着说了一句很诚实的话：**光是"MCP 变了"不足以让它进 core**。MCP 完全可以只是一个扩展——事实上社区就写过 `pi-mcp-adapter`。进核心的真正理由，是"它要求的改动本身普遍有用"：

> Pi 最终需要的东西，和 MCP 需要的东西非常像：一个可以玩的沙箱，形态就是一个解释器。

这句话是整篇文章的钥匙。Pi 在 1.0 里同时推了 Codemode——一个跑在 harness 侧、用 QuickJS（编译成 WebAssembly）执行的 JavaScript 沙箱。MCP 要解决"工具怎么被发现、怎么被组合"，Codemode 要解决"工具怎么被编排"——在 Pi 看来这是同一件事的两面。

第二层理由更具体，也更能解释代码长什么样：**工具装载的元数据不够用。**

1.0 之前 Pi 已经支持了几件新东西：deferred tool loading（工具可以延迟加载）、会话中途插入 system message、运行中调整 reasoning level。但工具装载机制没跟上。在 Codemode 的世界里，你必须能回答一个问题：**这个工具，是给模型看的，还是只给脚本看的？** 一个普通的 MCP 扩展拿不到 Pi 工具装载的元数据，就没法把这件事件做对。所以他们把 exposure 做进了 core。

还有第三层，语气最像"人"的一层：MCP 现在的位置比以前好，但 server 的写法还有很大改进空间，"我们想参与塑造它，而不是站旁边看"。

要理解这个判断，得把 1.0 同期的几项改动放在一起看。除了 Codemode，那版还加了 virtual models（把分类器、嵌入之类的小模型当成一种可调用的模型类型）、deferred tool loading、cache warming、会话中途插入 system message、新的 TUI 主题和默认全屏。

这几项看着零散，其实指向同一个方向：**模型看到的东西应该是动态的、按需的、可被结构性调整的**，而不是启动时拼好的一大块静态提示词。工具也一样——什么时候出现在列表里、以什么形式出现，都应该是可变的。MCP 如果还按"把所有工具一次性声明给模型"来用，就跟这个方向正好相反。

## 四、落地的那一刀：四种 exposure

"加回来"最容易被误解成"把 MCP 工具塞回模型的工具列表"。恰恰相反——Pi 默认**不**把 MCP 工具声明给模型。

每个 server 的工具注册成 `mcp__<server>__<tool>`（非字母数字下划线一律替换成 `_`），然后由 server 的 `exposure` 决定它怎么被够到：

| exposure | 行为 | 什么时候用 |
| --- | --- | --- |
| `codemode`（默认） | 只能从 codemode 脚本里调用；既不声明给模型，也不出现在 codemode 的描述里，脚本靠 `searchTools()` / `describeTool()` / `ALL_TOOLS` 现找 | 绝大多数 MCP server，尤其是希望脚本去组合、过滤调用的 |
| `deferred` | 不声明，直到 `tool_search` 为下一次模型调用加载到匹配项 | 工具很多、但发现之后应该直接调用的 server |
| `direct` | 像内置工具一样声明给模型，同时也能从 codemode 调 | 少量、高频、必须让模型一眼看见的工具 |
| `hidden` | 注册但不可达 | 临时关掉，或配合 `toolExposure` 只放行个别工具 |

`toolExposure` 还能按工具名或通配符逐个覆盖——比如整个 server 设成 `hidden`，只把 `search*` 那几个放出来。

这张表背后有个细节特别能说明设计取向：**当 server 用的是 `codemode` 或 `deferred` 时，模型在系统提示里只会看到一小节 `mcp_servers`**，内容是"这个 server 叫什么、它的工具怎么够到、一句话说明它提供什么"。这一节有硬上限：每个 server 的描述最多 250 字符，整节最多 4096 字符；装不下就把后面的 server 省略，末尾补一行"- … 还有 N 个 server，用 `searchTools()` 找它们的工具"。

也就是说，接十个 MCP server，模型的上下文里可能只多了几百个字符，而不是十份工具清单。

这一节实际长这样（示意）：

```text
MCP servers whose tools are not declared to you. Call the tools of `codemode`
servers from codemode scripts.
- linear (codemode): 团队 issue 跟踪，支持列表、评论、状态查询
- sentry (codemode): 错误事件与堆栈查询
- … 3 more servers; find their tools with searchTools()
```

注意最后一个细节：**codemode 自己的工具描述里也不列 MCP 工具**。文档解释得很直白——这样当 server 在会话中途连上或断开时，codemode 的描述不需要跟着变，也就不会造成缓存失效或提示词抖动。工具是被脚本用 `searchTools()` 现找的，描述里只需要告诉模型"有这么个入口"。

这一点比省 token 更微妙：它在暗示一种分工——**模型负责决定"要干什么"，脚本负责决定"用哪个工具、怎么调"。** 工具清单是执行细节，不是决策输入。

{% mermaid %}
flowchart TD
    A["一个 MCP 工具"] --> B{"声明给模型吗"}
    B -- "要，且立刻" --> C["direct<br/>进工具列表"]
    B -- "要，但先发现" --> D["deferred<br/>tool_search 加载后声明"]
    B -- "不要，只给脚本" --> E["codemode<br/>脚本里 searchTools 找"]
    B -- "谁都不给" --> F["hidden<br/>注册即不可达"]
    C --> G["系统提示：完整 schema"]
    D --> G
    E --> H["系统提示：mcp_servers 一节<br/>每 server ≤250 字符，整节 ≤4096"]
    F --> I["无任何痕迹"]
{% endmermaid %}

## 五、Codemode 到底是什么

前面反复出现这个词，得解释清楚。官方给的定义很短：Codemode 是**跑在 harness 侧**的沙箱，用来编排和协调工具调用，它的状态存在会话记录里，而不是文件系统里。

这句话值得拆开看。

一个 harness 执行工具，通常有两侧：跑 bash 的那一侧，和跑 agent loop 的那一侧。两侧的信任级别完全不同——loop 往往跑在可信环境里，而它执行的东西跑在不太可信的沙箱里。Codemode 特殊在它跑在 loop 那一侧，所以它能拿到工具句柄、能拿到模型、能拿到会话里的中间状态，但又被关在一个只有几十兆内存的 VM 里。

Pi 的实现里，这些约束是硬的：Node/Bun 下每次执行都起一个 worker thread、加载一个全新的 QuickJS wasm 实例；脚本能摸到的东西只有 `tools`、`ALL_TOOLS`、`text`/`image`、`exit`、`store`/`load`、`globals`——**没有 timer、没有 fetch、没有 process、没有 require、没有模块、没有 WebAssembly**。超时在 SDK 层有个 300 秒的默认值，到了 coding-agent 里改成由脚本首行的 `// @options: timeout_ms` 决定，不写就不设上限——因为一次 codemode 调用可能就是个把小时的批处理。内存在 coding-agent 里固定 256 MiB。脚本要跨调用记住东西，就用 `store()`/`load()`，而这份存储跟着会话记录走。

这套约束换来两个好处，都跟"状态存在会话记录里"有关。

其一，**可重放**。脚本和它的输出都作为会话条目落盘，所以一段 codemode 执行在会话树里是一个可回溯的节点，而不是一段散落在日志里的副作用。这一点在 Pi 的会话模型里很自然——所有东西都是条目。

其二，**可续跑**。`store()` 里的东西跟着会话走，下一个 turn 的脚本可以 `load()` 出来接着算。于是"分三批处理 5000 条数据"变成一个自然的写法：每批一个脚本，中间结果落在 store，模型只在最后看汇总。

这解释了官方那句话为什么成立：**它要的就是"一个解释器形态的沙箱"**。MCP 那边需要的是"工具能被发现、能被组合"，Codemode 这边提供的是"组合发生在一个有边界、可重放的地方"。

{% mermaid %}
sequenceDiagram
    autonumber
    participant M as 模型
    participant L as Agent Loop
    participant Q as Codemode (QuickJS)
    participant S as MCP Server

    M->>L: 调用 codemode，传入一段 JS
    L->>Q: 起 worker thread + 新 wasm 实例
    Q->>Q: searchTools("issue") 找到工具
    Q->>S: tools.mcp__linear__list_issues(...)
    S-->>Q: 结构化结果
    Q->>Q: 循环处理 167 条，只留 11 条
    Q-->>L: 返回 {total, counts, flagged}
    L-->>M: 只有这段摘要进上下文
{% endmermaid %}

注意这条链上最重要的一件事：**中间那 167 条 issue 从来没有进过模型上下文**。传统 MCP 路径里，它们会作为工具结果一条条回到对话里；Codemode 路径里，它们只在脚本的局部变量里活过一次。

## 六、把两条路摆在一起看

回到第三节那个对比。同样是"用浏览器抓点东西"，两种形态的差别是这样的：

| | 经典 MCP 路径 | Pi 的默认路径 |
| --- | --- | --- |
| 模型看到什么 | 21–26 个工具的完整 schema（13.7k–18.0k tokens） | 一个 `codemode` 工具 + 一节 `mcp_servers`（几百字符） |
| 怎么发现工具 | 一开始就全在列表里 | 脚本里 `searchTools()` 现找 |
| 怎么组合 | 结果进上下文再拼 | 脚本里 `await`、循环、`Promise.all` |
| 中间结果去哪 | 对话历史 | 脚本局部变量 / `store()` |
| 加一个工具 | 改 server、重启、schema 重新进上下文 | 写个脚本或加个 server 条目 |
| 出问题怎么查 | 看对话里的工具调用 | 看脚本、看 `store()` 里的落点 |

这个表其实回答了"为什么加回来却看起来更像当年那篇文章"：**MCP 回来了，但"MCP 工具占据上下文"这件事没回来。**

顺便给一个选 `direct` 的判据，因为默认值不是永远对的：**如果模型必须"看一眼就知道有这个能力"，而且这个能力一天要被调几十次，就该 `direct`。** 典型例子是"读文档"这种 server——模型不该先写一段脚本去发现"有没有读文档的工具"，它应该直接看见。反过来，"分析 167 个 issue 的情绪"这种一次性重活，`codemode` 才是对的：工具叫什么名字根本不重要，重要的是别让 167 条结果进上下文。

## 七、他们没解决的问题，也没藏着

官方文章里有一句话，我觉得比"我们支持 MCP 了"更重要：

> MCP 最大的问题一直是它很难组合。就算有了 Codemode——那只是个小沙箱，让工具调用能组合起来——MCP 也没完全交付这一点。

也就是说，Codemode 缓解了症状，没治好病。病根在哪？官方给了个判断：**问题更多出在 server 和各家 harness 的做法上，不是协议本身。**

他们期望 MCP 变成什么样，说得也很直白：**"MCP 应该更像 OpenAPI 加上智能工具发现"**——工具返回结构化数据，工具的发现靠文档和描述，而不是靠把所有 schema 提前灌进上下文。

还有一层关系容易被忽略：**MCP 自己在 2026-07-28 那版的无状态化，恰好让"用脚本调它"变得更自然。**

那版把协议级会话、`initialize` 握手、GET 长连接全删了，改成每个请求在 `_meta` 里自带 `protocolVersion`、`clientCapabilities`，外加一个必须实现的 `server/discover`。结果就是——**一次工具调用变成一次纯函数调用**，不依赖之前发生过什么。

这对脚本化是决定性的。有会话的时候，脚本要在多个调用之间维持同一个会话，还要处理"会话被服务器踢了回 404 得重新握手"这种分支；没有会话之后，脚本里就是一行 `await`，并发 `Promise.all` 也不用担心串味。

所以两边其实是互相成全的：MCP 变得更像一组无状态函数，Codemode 才敢把它当成库来用；反过来，正因为有脚本兜着，MCP 才可以放心地把"组合"这件事从协议里拿掉。

这话反过来就是在批评现状：今天大量 MCP server 还是按"给会把工具全灌进上下文的 harness 用"来设计的，于是它们在自己的返回值上做 token 优化——返回一段精心排版的文本，而不是结构化数据。这在只有工具调用的 harness 里是合理的，但在有 Codemode 的 harness 里就是浪费：结构化数据让脚本去筛、去算，比让模型读散文便宜得多。

## 八、时间线：一年里到底变了什么

把三件事并排放在一条时间线上，转折就不神秘了。

{% mermaid %}
flowchart LR
    A["2025-11<br/>Mario 写《你根本不需要 MCP》<br/>官网：Pi 不支持 MCP"] --> B["2025-12<br/>社区扩展 pi-mcp-adapter<br/>证明可以做，但没进 core"]
    B --> C["2026-07<br/>MCP 规范无状态化<br/>去会话、去握手、去 GET 流"]
    C --> D["2026-09-29<br/>官方《You Said No MCP!》<br/>宣布进 core，默认藏进 codemode"]
    D --> E["2026-10<br/>Pi 1.0<br/>Codemode 自动随 MCP 启用"]
{% endmermaid %}

三件事分别是：**协议的形态变了**（会话从协议里拿掉，server 变成无状态函数）、**harness 的能力变了**（有了 deferred loading、会话中途 system message、reasoning level 切换）、**工具装载的元数据补上了**（exposure）。三件凑齐，"把 MCP 藏进脚本"才成为一个能落地的默认值，而不是一句口号。

补一个细节：Pi 明确不支持的，是**已经废弃的 legacy SSE 传输**。配置里 `type` 只能是 `stdio`、`http`、`streamable-http`，写 `sse` 会被拒绝，文档还贴心提醒你"很多宣称 SSE 端点的 server 同时提供 streamable HTTP，通常叫 `/mcp` 而不是 `/sse`"。这跟当年那篇文章的立场其实一脉相承——他们从来没有反对"远程工具"这件事，反对的是把工具的描述当成上下文的固定税。

## 九、这套折中给 harness 设计者的三条启示

写完这些，我觉得对做 agent 的人真正有复用价值的，是下面三条。

**第一，工具进入上下文的"时机"和"形式"要分开设计。** 大多数 harness 只有一个开关：工具声明或不声明。Pi 把它拆成了两维——什么时候进（立刻 / 发现后）、以什么形式进（schema / 脚本 / 不可达）。`deferred` 和 `codemode` 就是这两个维度的组合。这件事不需要 MCP 也能做，本地工具一样适用。

**第二，把"组合"放在上下文之外。** 一条经验判据：**只要两个工具调用的中间结果，模型不需要读，那它就不该进上下文。** 传统做法是子 agent；Codemode 的做法是同一段脚本里 `await`。后者更便宜，因为它连一次模型往返都省了。

**第三，别把 codemode 当成万能钥匙。** 它有两个真实的代价。一是调试变难：脚本失败时你拿到的是"这一段跑挂了"，而不是"第 3 个工具调用失败"，得靠 `store()` 留痕一点点排。二是失败更贵：脚本里第 20 个调用挂了，前面 19 个的结果默认也一起没了（除非你显式 store），而传统工具调用是逐个落地的。所以高频、需要中途观察、需要人工介入的流程，反而不该塞进一个脚本。

**第四，沙箱的形态跟着宿主走。** Codemode 关在 QuickJS 里能成立，是因为它只需要调工具，不需要文件系统、不需要网络。如果换成"要跑数据库迁移"的任务，这个沙箱就不合适了——那属于 bash 侧的事。Pi 的选择是让两侧都留着：bash 侧有完整系统，harness 侧有一个只够编排的小 VM。

## 十、自己动手试一遍

在 Pi 里接一个 MCP server，三步：

```bash
# 1. 加一个本地 stdio server
pi mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem .

# 2. 看连接状态、工具数、当前的 exposure
pi mcp list

# 3. 进会话，用 /mcp 改 exposure、登录、重连
pi
```

默认情况下这些工具是 `codemode`。会话里你要让模型直接看见它们，就把 exposure 改成 `direct`；只放行几个，就用 `toolExposure` 按名字或通配符覆盖。

然后在会话里直接这么说话：

> 用 codemode 把 docs 目录下所有 md 文件的标题列出来，重复的合并，只把重复次数大于 1 的给我

模型会写一段脚本，`searchTools()` 找到文件工具，循环读、在脚本里做聚合，最后只把那一小段结果返回。你可以让它把中间结果 `store()` 起来，下一轮再用——这些都不占上下文。

大致长这样（结构照搬，工具名随你的 server 变）：

```js
// 在 codemode 沙箱里执行：只有 tools / store / text，没有 fetch 和 setTimeout
const found = await searchTools("markdown file list", { limit: 5 });
const list = tools[found[0].name];              // 按名字取到工具句柄

const files = await list({ dir: "docs", glob: "**/*.md" });
const counts = new Map();

for (const f of files) {
  const body = await tools.read_file({ path: f.path });  // 逐个读，结果不进上下文
  for (const line of body.split("\n")) {
    if (!line.startsWith("# ")) continue;
    const title = line.slice(2).trim();
    counts.set(title, (counts.get(title) ?? 0) + 1);
  }
}

store("dup-titles", [...counts].filter(([, n]) => n > 1));  // 落进会话，下轮可 load()
return [...counts].filter(([, n]) => n > 1);
```

这里有两个值得注意的写法。`searchTools()` 返回的是**排序后的候选**，不是全量清单，所以模型不用知道 server 里一共有多少个工具。`store()` 存的东西跟着会话走，下一次你让它"把上次那些重复标题按出现次数再排一下"，它 `load()` 出来就行，不用重新扫一遍目录。

{% mermaid %}
flowchart TD
    A["接一个 MCP server"] --> B{"工具该被模型看见吗"}
    B -- "高频、少量" --> C["exposure: direct"]
    B -- "多，但要直接调" --> D["exposure: deferred"]
    B -- "要组合、要过滤" --> E["exposure: codemode（默认）"]
    C --> F["上下文里多几份 schema"]
    D --> F
    E --> G["上下文里多一行 mcp_servers"]
    G --> H["脚本负责把中间结果消化掉"]
{% endmermaid %}

## 十一、最后一句

"先拒绝，又加回来"这个叙事很容易被读成打脸。但把两边的原文对着读，会发现他们拒绝的东西一直没变：**拒绝的是"MCP server 把一堆工具描述当成每轮会话的固定成本"这种形态**，而不是协议本身。

这次加回来，改的是消费端——用一个跑在 harness 侧的沙箱，把"工具怎么被发现、怎么被组合、什么时候进上下文"这三件事从模型手里拿走，交给脚本。

某种意义上，这是把那篇 2025 年的文章往前推了一步：当年他的答案是"别用 MCP，让 agent 写脚本调 CLI"；现在的答案是"用 MCP，但让 agent 写脚本调 MCP"。协议没变，写法变了，账就平了。

---

**相关阅读**

- [Pi 入门：从一条命令，到一个会改代码的 agent](/2026/11/05/Pi-入门/)
- [Pi-Codemode：让模型写一段脚本去调工具](/2026/11/05/Pi-Codemode/)
- [Pi 怎么定义一个工具：一张卡片上的十个字段](/2026/11/05/Pi-工具/)
- [MCP 全解：从 stdio 到无状态，再到网关与高并发](/2026/11/04/MCP全解/)
- [同一个 Agent 主循环，两种工程答案：Pi 与 DSH 对照解剖](/2026/11/05/Agent主循环对比-Pi与DSH/)
