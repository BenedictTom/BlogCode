---
title: Pi-Codemode：让模型写一段脚本去调工具
date: 2026-11-05 03:55:00
categories:
  - Pi
tags:
  - Pi
  - Codemode
  - MCP
  - Sandbox
cover: /images/Pi-Codemode/cover.png
description: Codemode 把"一个个工具调用"换成"一段脚本"：脚本在 QuickJS 沙箱里跑，中间结果不进上下文，MCP 工具默认只以 codemode 形式暴露。
---

工具调用有个隐形的成本：**每一次调用都是一次完整的上下文往返**。

想查 20 个文件的某一行，就是 20 次 `grep` 调用、20 段结果进上下文；想在 30 个 issue 里筛出含某个关键词的，就是 30 次调用加 30 段 HTML。上下文窗口就是这么被吃掉的——不是被"重要的东西"吃掉的，是被**中间结果**吃掉的。

Codemode 的答案很直接：**别让模型调用工具，让它写一段脚本来调工具。**

## 0. 一句话

`packages/codemode/README.md:3` 的原话：

> Runs model-written JavaScript in a QuickJS VM (compiled to WebAssembly) where the only capability is calling injected tools. Nested tool calls never enter the LLM context; only the script's output and return value do.

`packages/coding-agent/docs/codemode.md:3` 补了它和普通工具调用的差别：

> Only the script's output reaches the model, so a script can run calls in parallel and filter large results before the model sees them.

两个关键词：**只有输出进上下文**、**脚本里可以并行和过滤**。

{% mermaid %}
flowchart LR
  subgraph legacy["传统 tool call"]
    A1["模型"] -->|call 1| B1["工具"] -->|结果 1| A1
    A1 -->|call 2| B2["工具"] -->|结果 2| A1
    A1 -->|call 3| B3["工具"] -->|结果 3| A1
    A1 -.上下文被 3 份结果占满.-> A1
  end
  subgraph cm["Codemode"]
    C1["模型"] -->|写一段 JS| C2["QuickJS 沙箱"]
    C2 --> D1["工具 ×N"]
    D1 --> C2
    C2 -->|只回一个结果| C1
  end
{% endmermaid %}

## 1. 隔离：每次 execute 一个全新 VM

`README.md:11,362` 与 `runtime/host.ts:12-19`：在 Node/Bun 上，**每次 `execute` 起一个 worker thread + 一个全新的 QuickJS wasm 实例**。

"每次一个"这件事很重要。它不是"启动一次，复用很多次"的池子，而是**一次性隔离**：脚本跑完，整个 VM 连同它的堆一起丢掉。于是：

- 状态不会泄漏到下一次执行
- 不需要写"清理逻辑"（清理逻辑本身就是最容易出漏洞的地方）
- 超时/中断可以直接 `worker.terminate()`（`host.ts:12-19`）

代价是启动开销。QuickJS 编译到 wasm 之后实例化很快（毫秒级），所以这个代价可以接受。

Cloudflare 上是另一种形态：`RemoteCodemodeSandbox` 跑在独立 Worker 的 Durable Object 里（`README.md:133`）。同一套接口，不同的隔离边界。

VM 里的 import 只有两个：一个 WASI shim，一个 host-call 入口（`README.md:362`、`runtime/vm.ts:166-178`）。也就是说，**脚本连 `console` 都不是原生的**，而是宿主注入的。

## 2. 脚本能看见什么

`README.md:49-56` 列了全部能力：

```
tools   ALL_TOOLS   text   image   exit   store   load   globals
```

然后就断了：

> Nothing else: no timers, `fetch`, `process`, `require`, modules, or `WebAssembly`.

这张白名单值得逐条想：

- **没有 `fetch`**：脚本不能自己上网，所有网络能力必须由某个工具提供。这既是安全，也是"可审计"——你永远知道流量从哪个工具出去的。
- **没有 `setTimeout`**：延迟只能由宿主控制（超时由 `timeoutMs` 管），脚本自己不能挂起。
- **没有 `require` / modules**：不能加载任何代码。
- **没有 `WebAssembly`**：不能把沙箱当跳板再开一层。
- **`store` / `load`**：脚本内的持久化，但有配额（见下）。

有一处设计细节特别"抠"：`MAX_OUTPUT_CHARS = 16 Mi`、`MAX_OUTPUT_ITEMS = 100_000`（`runtime/prelude-source.ts:42-43`），而 `store` 单值是 **256 KiB**、总量 1 Mi（`:34-35`）。

**输出的上限比存储的上限大得多。** 意思是：脚本可以往 `store` 里放点东西攒着，但只能放小东西；输出可以很大（16 MiB），但那是"一次性交出去"的。用这两个数字划出了"临时工作区"和"最终交付物"的区别。

## 3. 和 MCP 的关系：默认不给模型看

这是 Codemode 最有意思的一处设计，也是我读之前完全没想到的。

MCP 工具在 Pi 里注册成 `mcp__<server>__<tool>`（`extensions/mcp/index.ts:9`），默认的 `exposure` 是 **`"codemode"`**（`core/mcp-servers.ts:177`）：

```
"exposure": "codemode"
```

回想上一篇讲工具时的三个 exposure：`model`（能看见能调用）、`model-only`、`codemode`（**不给模型，只能被脚本调用**）。

**所以默认情况下，模型根本不知道那些 MCP 工具存在。** 它只知道"有个沙箱，里面能调工具"。要调某个 MCP 工具，它得先 `searchTools()` 去找（`mcp-servers.ts:53-61`）：

```js
const found = searchTools("radius");   // 找带 radius 的工具
const r = await tools.mcp__dev_radius__search({ query: "..." });
```

{% mermaid %}
flowchart LR
  subgraph defm["默认暴露（model）"]
    A1["工具声明"] --> A2["system prompt<br/>每轮都带"]
  end
  subgraph cexp["codemode 暴露"]
    B1["工具注册进沙箱"] --> B2["模型看不到声明"]
    B2 --> B3["脚本里 searchTools() 现查"]
    B3 --> B4["tools.mcp__server__tool()"]
  end
  A2 -.工具一多就爆.-> B1
{% endmermaid %}

为什么要这么绕？因为 MCP 服务器一多，工具声明本身就吃掉大量上下文。一个接了 5 个 server 的配置，可能就是上百个工具声明——几万 token 的 system prompt，还没开始聊。

`codemode` 曝光把这块成本挪进了沙箱：**工具声明不再发给模型，工具名在脚本里现查**。

名字还得转义：非标识符字符转下划线，`mcp__dev-radius__search` → `tools.mcp__dev_radius__search`（`docs/codemode.md:31`）。因为 `-` 不是合法的 JS 标识符字符——这就是"把工具名当变量名用"的代价。

顺便遥相呼应第一篇 MCP 文里的那句话：**MCP Gateway 解决的是"服务太多太散"**。Codemode 解决的是同一个问题的另一半——不只是接入要收敛，**声明也要收敛**。

## 4. 限额：一张数字表

| 限额 | 值 | 位置 |
| --- | --- | --- |
| 默认超时 | `300_000` ms | `runtime/execution.ts:49` |
| 脚本自定超时 | 首行 `// @options: timeout_ms`，缺省 Infinity | `extensions/codemode/execute.ts:555` |
| coding-agent 内存 | 256 MiB | `execute.ts:56,593` |
| Cloudflare 内存 | 32 MiB/VM，isolate 共享 128 MB | `src/cloudflare.ts:32` |
| 中断预算 | `DEFAULT_INTERRUPT_BUDGET = 100_000` | `runtime/inline.ts:39` |
| inline 栈 | 256 KiB | `runtime/inline.ts:42` |
| 输出上限 | 16 Mi chars / 100k items | `prelude-source.ts:42-43` |
| store 上限 | 256 KiB/值，1 Mi 总量 | `prelude-source.ts:34-35` |

两个数字值得单独说：

**"脚本自定超时缺省 Infinity"** 看着危险，但要知道上下文：coding-agent 传下去的是 `timeoutMs: Math.max(1, Math.round(deadline - waitedMs))`（`execute.ts:592`）。也就是"剩余预算"——已经等掉的时间要扣掉。缺省 Infinity 意味着"不设自己的上限，听宿主的"，不是"无限跑"。

**中断预算 100,000** 和 **inline 栈 256 KiB** 是一对：中断检查要花钱（每次循环查一下 flag），给 10 万次预算，同时限制调用栈深度，防止递归把中断检查点淹没。

## 5. 最小可用

`README.md:18-45` 的骨架：

```ts
const sandbox = new CodemodeSandbox({ timeoutMs: 60_000, tools });
const result = await sandbox.execute(`
  const rows = await tools.fetchIssues({ limit: 100 });
  return rows.filter(r => r.title.includes("leak")).map(r => r.number);
`);
// result.output / result.value / result.ok
```

三个返回字段各有用处：`output` 是脚本打印的东西，`value` 是 `return` 的值，`ok` 是成败。

在 coding-agent 里，codemode 本身也是一个工具（`extensions/codemode/tool.ts:398`），而它的 exposure 是 **`"model-only"`**——**脚本不能再起脚本**。这条限制很必要：否则一层嵌套一层，超时、内存、中断的预算全部失效。

沙箱的组装在 `execute.ts:584-594`，那里才是把"当前会话的工具集"注入进去的地方。

## 6. 代价

Codemode 不是免费的。三个代价：

**调试变难。** 脚本在 VM 里跑，你不能 `console.log` 到处插（能，但输出要绕一圈）。错误栈也是 VM 的栈，不是你的源码行号。

**错误模型要重设计。** 工具调用失败在脚本里是异常还是返回值？如果是异常，一个失败就让整段脚本中断；如果是返回值，脚本得自己判断。这是每个 Codemode 使用者都要做的一次选择。

**模型要会写代码。** 这个门槛比"选个工具"高。所以 Pi 在文档里反复强调：脚本首行可以写注释配置，输出要自己裁剪——这些都是在教模型"怎么写好这段脚本"。

但换来的收益也很实在：**上下文占用从 O(调用次数) 变成 O(1)**。对于"批量查、批量筛"这种任务，差距是数量级的。

## 7. 小结

四句话：

1. **Codemode = 把工具调用变成一段脚本**，只有脚本输出进上下文。
2. **每次执行一个全新的 QuickJS VM**，能力白名单之外什么都没有（没有 fetch/timers/modules）。
3. **MCP 工具默认 `exposure: "codemode"`**——不给模型看声明，脚本里用 `searchTools()` 现查，省下大量 system prompt。
4. **限额分四层**：时间（剩余预算）、内存（256 MiB）、中断（10 万次）、输出（16 Mi + store 256 KiB）。

如果把它和前面几篇连起来看，会看到一个越来越清晰的倾向：Pi 这一套东西都在**把"上下文"当成稀缺资源来设计**——会话树用路径代替复制、上下文工程用索引代替全文、工具用 `exposure` 控制可见性、Codemode 把中间结果留在沙箱里。

一句话总结整个系列的暗线：**agent 的能力上限，不取决于它能调多少工具，而取决于它能在不污染上下文的前提下调多少工具。**

---

**相关阅读**

- [pi-ai：43 个供应商，10 种协议，一套流](/2026/11/05/Pi-ai/)
- [Pi 怎么定义一个工具：一张卡片上的十个字段](/2026/11/05/Pi-工具/)
- [Pi Durable（下）：谁在跑，谁在看](/2026/11/05/Pi-Durable-下/)
