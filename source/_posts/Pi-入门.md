---
title: "Pi 入门：从一条命令，到一个会改代码的 agent"
date: 2026-11-05 01:10:00
categories: [Pi]
tags: [Pi, Agent, 源码解析]
cover: /images/Pi-入门/cover.png
description: 把 Pi 拆开看：一条 `pi` 命令进来之后，参数怎么解析、会话从哪来、十一个包各自管什么，以及为什么它要把一个 agent 拆得这么碎。
---

## 0. 一句话概括

Pi 是一个跑在终端里的编程 agent：你在某个目录下敲 `pi`，它读文件、跑命令、改代码。

但源码层面它更值得看的地方不是"能改代码"——这是所有同类工具的基本盘——而是**它把这件事拆成了十一个包**，并且每个包都能单独拿出来用：

- 想把 agent 嵌进自己的服务？用 `pi-agent-core` 的 loop，两三百行就能起一个。
- 想自己接一家模型供应商？只改 `pi-ai`，别的包一行不用动。
- 想把 agent 变成一个扛崩溃、多客户端、能长时间跑的服务？换 `pi-durable`，它和终端版共用同一个模型层。
- 想让模型别背一百个工具说明书，而是写段脚本去编排它们？那是 `codemode`。

这篇是系列的第一篇，只做一件事：**把地图铺开**。一条命令从敲下到模型开口，中间经过哪些模块；十一个包谁依赖谁；后面八篇分别往哪儿钻。

> 本文所有结论基于 `earendil-works/pi` 仓库提交 `395f3e0`、`packages/coding-agent` 版本 `1.5.0`（2026-11-04 拉取）。行号会随版本漂移，对不上时以同名的函数为目标去搜。

## 1. 先跑起来

安装有两条路，官方推荐第一条：

```bash
curl -fsSL https://pi.dev/install.sh | sh
```

它把依赖版本都钉死，之后用 `pi update` 升级。第二条是 npm：

```bash
npm install -g --ignore-scripts @earendil-works/pi-coding-agent
```

需要 Node.js 22.19 或更高——这不是随手写的门槛，下面会看到原因：它用到了一些比较新的 Node 能力，而且包本身是纯 ESM、靠 Node 的 type stripping 直接跑 TypeScript。

装完在一个项目目录里起：

```bash
cd ~/my-project
pi
```

第一次会让你选模型：有订阅（比如 Claude、ChatGPT）的走登录，没订阅的填 API key，本地跑 llama.cpp 的也能接。选完就开始对话了。

界面是三段式：上面是对话记录，中间是输入框，底下是状态栏（当前目录、模型、会话状态）。官方文档里的截图长这样：

<figure>
<img src="/images/Pi-入门/interactive-mode.png" alt="Pi 的终端界面：对话、编辑器与状态栏">
<figcaption>Pi 的交互模式（截图来自 Pi 官方文档 <code>packages/coding-agent/docs/images/interactive-mode.png</code>）</figcaption>
</figure>

到这里为止，它和别的终端 agent 没什么两样。差别在敲下回车之后。

## 2. 一条命令的旅程

`pi` 这个可执行文件指向 `dist/bundle/cli.js`，真正的入口是 `src/main.ts`（1,011 行）。它做的事情可以按顺序切成四段：**解析参数 → 决定跟哪个会话打交道 → 建一个会话对象 → 选一种跑法**。

{% mermaid %}
flowchart TD
  a["敲下 pi"] --> b["main.ts 解析参数<br/>cwd / model / session"]
  b --> c{"要不要接着旧会话"}
  c -->|"新会话"| d["SessionManager.create"]
  c -->|"continue"| e["SessionManager.continueRecent"]
  c -->|"open / fork"| f["SessionManager.open / forkFrom"]
  d --> g["createAgentSession<br/>core/sdk.ts:191"]
  e --> g
  f --> g
  g --> h{"选跑法"}
  h -->|"终端交互"| i["InteractiveMode"]
  h -->|"一次性"| j["runPrintMode"]
  h -->|"被别的程序驱动"| k["runRpcMode"]
{% endmermaid %}

四个跑法里三个值得说一句：

- **InteractiveMode** 是人用的：TUI、快捷键、`/` 命令、树形会话浏览都在这一层。
- **runPrintMode** 是 `pi -p "..."` 用的：跑一次，把结果打到 stdout 就退出，适合塞进脚本或 CI。
- **runRpcMode** 是给别的程序用的：JSON-RPC over stdio，外面套一层 GUI 或者 IDE 插件就能驱动它。

也就是说，**同一个 agent 内核，三种外壳**。后面写扩展、写 MCP、写网关时，"外壳"和"内核"的边界会反复出现，先记住这条线。

真正把东西拼起来的是 `createAgentSession()`（`core/sdk.ts:191`）。它接受一个选项对象，把会话管理器、模型运行时、工具、扩展、系统提示词一样样装进去，最后 `new AgentSession(...)`（`core/sdk.ts:455`）。这个 `AgentSession` 就是后面八篇的主角——它是"议程"的中心：上面接着 TUI 或 RPC，下面接着 agent loop 和模型。

### 会话存在哪

Pi 的会话不是数据库，是一个个 JSONL 文件，按工作目录分桶：

```
~/.pi/agent/sessions/--Users-smzdm-chw-my-project--/2026-11-04T17-43-52-8f3a.jsonl
```

这个目录名是拿 cwd 编码来的：去掉开头的斜杠，把 `/` 和 `:` 换成 `-`，两边各包两个短横线（`core/session-manager.ts` 的 `getDefaultSessionDirPath`）。所以同一个项目下的会话自动聚在一起，换个目录就是另一堆。

JSONL 的好处是**追加只写一行**，不用回读整个文件；坏处是查询得自己扫。Pi 的取舍很明确：宁可扫，也不引入数据库。原因在第三篇会讲——因为它的会话是**树**，每行都带 `id` 和 `parentId`，追加写恰好是最自然的树存储方式。

全局配置也在这个目录：`~/.pi/agent/` 下面是 `auth.json`（凭据）、`models.json`（自定义模型）、`settings.json`（偏好）。项目级的约定则放在仓库里的 `AGENTS.md`，这个第四篇细说。

## 3. 十一个包怎么分工

仓库是 npm workspaces 的 monorepo，`packages/` 下十一个包。按"离模型多远"排一下：

| 包 | 代码量（非测试 .ts） | 管什么 |
| --- | --- | --- |
| `coding-agent` | 77,357 行 | 终端 harness：会话、工具、扩展、命令、TUI 接线 |
| `chord` | 52,502 行 | 上下文与取消传播的底层设施 |
| `durable` | 33,669 行 | 把 agent 变成可恢复的服务（实验性） |
| `ai` | 28,806 行 | 模型层：供应商、流式解析、模型目录、鉴权 |
| `tui` | 19,973 行 | 终端 UI 组件与渲染 |
| `schema` | 4,573 行 | 参数/配置校验 |
| `mcp` | 4,742 行 | MCP 客户端集成 |
| `codemode` | 3,037 行 | 让模型写脚本调工具 |
| `agent` | 2,555 行 | 最小 agent 循环（`pi-agent-core`） |
| `env` | 少量 | 环境探测 |
| `evals` | 少量 | 评测 |

两个地方值得停一下。

**第一，最小的那个包才是心脏。** `agent` 只有 2,555 行，核心循环 `agent-loop.ts` 959 行。77,000 行的 `coding-agent` 全都建在它上面。这个比例本身就是一种态度：循环要小到能一眼看完，复杂的东西都推到外围。

**第二，`ai` 是独立可复用的。** `coding-agent` 的依赖列表里能看到 `@earendil-works/pi-agent-core`、`pi-ai`、`pi-codemode`、`pi-mcp`、`pi-tui`，但它没有依赖 `durable`。反过来，`durable` 和 `coding-agent` 是**平级**的——两者都站在 `agent` 和 `ai` 上，一个面向"一个人、一个终端"，一个面向"多客户端、扛崩溃"。

{% mermaid %}
flowchart BT
  subgraph apps["两种形态"]
    ca["coding-agent<br/>终端 harness"]
    du["durable<br/>可恢复的服务"]
  end
  subgraph core["共用内核"]
    ag["agent<br/>agent loop"]
    ai["ai<br/>供应商与流"]
  end
  subgraph base["底座"]
    ch["chord<br/>上下文/取消"]
    sc["schema<br/>校验"]
    tu["tui<br/>终端渲染"]
    cm["codemode<br/>脚本化工具"]
    mc["mcp<br/>MCP 客户端"]
  end
  ca --> ag
  ca --> ai
  ca --> tu
  ca --> cm
  ca --> mc
  du --> ag
  du --> ai
  du --> ch
  ag --> ai
  ag --> ch
  ai --> sc
  cm --> sc
{% endmermaid %}

这张图是后面所有文章的路线图。⑨ 讲 `ai`，⑩⑪ 讲 `durable`，⑫ 讲 `codemode`，②③④⑤ 讲 `coding-agent` 里的 loop、会话、上下文和工具。

## 4. 三个反直觉的设计

读源码之前先接受三件事，后面会顺很多。

### 4.1 它没有"模式切换"的魔法，只有一层很薄的包装

很多人对 agent 的想像是：有个调度器，判断该聊天还是该干活，然后切模式。Pi 里没有这个东西。

有的只是一个循环：**把消息拼成请求 → 流式拿回响应 → 如果响应里有工具调用就执行 → 把结果塞回消息 → 再来一轮**，直到模型不再要工具为止。所谓"干活"，就是这个循环转了很多圈；所谓"聊天"，就是转了一圈就停。

这个循环在 `packages/agent/src/agent-loop.ts` 的 `runLoop()`（172-330 行）里，一百多行。第二篇会一行行拆。

### 4.2 模型层不认识"工具循环"

`pi-ai` 里没有 turn、没有 tool loop、没有重试策略。它只做一件事：**给一个模型 + 一串消息 + 一组工具声明，吐出一个流式响应**。

反过来，`agent` 包不知道 HTTP、不知道 SSE、不知道哪家供应商。它只知道"调 `streamFn`，拿事件"。

这条界线的好处是：接第十家供应商不用碰循环，改循环不用碰十家供应商。代价是中间那层类型要设计得很仔细——`AgentMessage` 和 `Message` 是两个类型，只在发请求那一刻转换（`agent-loop.ts:404` 的 `config.convertToLlm(messages)`）。这个"只在边界转换"的规矩，是整份代码里贯彻得最彻底的。

### 4.3 一堆东西是"可选挂载"的

会话、工具、扩展、MCP、codemode、缓存预热、压缩——这些在别的实现里往往是核心的一部分，在 Pi 里全是**往会话对象上挂的**。

`createAgentSession()` 的选项对象有几十个字段，每一个都是"给就给，不给用默认"。所以你能看到同一份代码支撑三种形态：

- `pi` 终端：全挂上。
- `pi -p` 脚本：挂一部分，不要 TUI。
- 嵌入 SDK 或 RPC：只挂你要的。

这也是为什么本文标题是"从一条命令到一个会改代码的 agent"——那条命令本身很薄，重量都在它拼出来的那个对象上。

## 5. 这个系列怎么读

九篇分三组，建议按顺序，但每组内部可以跳。

**第一组：终端 agent 是怎么转的（①-⑤）**

- ① 本篇：地图。
- ② Agent Loop：一次请求转几圈，什么时候停，`terminate` 是什么，为什么"截断的工具调用一律不执行"。
- ③ 会话树：为什么对话是一棵树而不是一条线，`/tree` 回退时那半条分支去哪了，压缩怎么在树上切一刀。
- ④ 上下文工程：系统提示词不是一次性写死的，它是**分段**的，改一段只发改动的那段。
- ⑤ 工具系统：一个工具从 TypeBox schema 到模型手里的 JSON Schema，中间过了几道手。

**第二组：模型层（⑨）**

- ⑨ `pi-ai`：十几家供应商怎么收敛到一个接口，流式事件长什么样，鉴权两条路（API key 与 OAuth）怎么并存。

**第三组：把 agent 变成服务（⑩-⑫）**

- ⑩ Durable 上：崩溃了怎么接着干，checkpoint 的"一步"到底多长。
- ⑪ Durable 下：任务树、文档、多客户端同步、扩展热替换。
- ⑫ Codemode：为什么"让模型写代码调工具"可能比"给模型一百个工具"更省。

## 6. 读源码前的三个准备

如果你打算边读边跟，这三件事能省你不少时间。

**第一，先跑一次 `pi -p`。** 交互模式有 TUI 干扰，`pi -p "读一下 package.json 说说这个项目"` 更干净，你能看到工具调用是怎么一轮轮发生的。

**第二，知道会话文件在哪。** 跑完去 `~/.pi/agent/sessions/--<你的目录>--/` 找最新的 `.jsonl`，`cat` 一下。你会看到每一行是一个 JSON 对象，`type` 字段有 `session`、`message`、`model_change`、`compaction`……**这比任何文档都直观**，第三篇全靠它。

**第三，别从 `coding-agent` 开始读。** 它 77,000 行，而且大量代码是 TUI 渲染和命令解析。从 `packages/agent/src/agent-loop.ts` 开始，959 行，读完再往两边扩。

## 7. 小结

- Pi 是一条命令，但那条命令只做四件事：解析参数、挑会话、建会话对象、选外壳。
- 内核是 `agent`（2,555 行，循环 959 行），模型层是 `ai`，终端体验是 `coding-agent` + `tui`，服务形态是 `durable`。
- 没有模式切换，只有一个"请求-工具-再请求"的循环；没有魔法，只有一堆可选挂载。
- 会话是 `~/.pi/agent/sessions/` 下的 JSONL，按目录分桶，一行一个节点。

下一篇从那个循环开始：一次 `pi -p "..."` 到底转了几圈，每一圈里发生了什么，以及它凭什么知道"该停了"。

---

**相关阅读**

- [Pi 的一次请求：agent loop 里到底发生了什么](/2026/11/05/Pi-Loop/)
- [Pi 的会话树：一条对话为什么不是一条线](/2026/11/05/Pi-会话树/)
- [Pi 的上下文工程：每次请求，模型到底看到了什么](/2026/11/05/Pi-上下文/)
