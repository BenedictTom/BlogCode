---
title: "MCP 全解：从 stdio 到无状态，再到网关与高并发"
date: 2026-11-04 18:30:00
categories: [Agent]
tags: [Agent, MCP, Protocol, AI]
cover: /images/MCP全解/cover.gif
description: 一次讲清 MCP 的两种传输、五个版本的有状态到无状态改造、网关该不该上、调用量大了怎么扛，最后手写一个能跑的最简 MCP Server。
---

## 0. 一句话概括

MCP 就是**给"模型调工具"这件事定的一份说明书**：用 JSON-RPC 2.0 说话，两种传输（本地走 stdio，远程走 Streamable HTTP），五个版本里把"连接是有状态的"这一点一路削成了"每条请求自带身份"。

而绝大多数人卡住的三个问题，其实是一个问题的三个面——**状态放哪**：

- 为什么远程服务老要开 SSE？→ 因为服务器有话说，得有条通道往回推。
- 为什么新版本把会话删了？→ 因为有状态让扩容变贵，而绝大部分工具根本不需要。
- 为什么上了网关？→ 因为一个会话就是一份内存，十个工具就是十份配置，得有人替你把它们收拢。

下面按你关心的顺序一个个说。先看图。

<figure>
<img src="/images/MCP全解/cover.gif" alt="MCP 示意图" width="460">
<figcaption>MCP 协议插图（本文封面同款）</figcaption>
</figure>

## 1. MCP 到底解决了什么

先说个老掉牙但确实准确的类比。

没有 MCP 的时候，每个 AI 应用要和 N 个外部能力对接，就得写 N 套胶水：搜索一套、数据库一套、工单系统一套。M 个应用就是 M × N 份代码，每份都要处理鉴权、超时、重试、参数格式、返回格式……

有了 MCP，应用只认协议，工具只实现协议，复杂度从 M × N 塌成 M + N。

{% mermaid %}
flowchart LR
  subgraph before["没有 MCP：M × N 条胶水"]
    direction TB
    a1[应用 A] --- s1[搜索]
    a1 --- s2[数据库]
    a2[应用 B] --- s1
    a2 --- s2
  end
  subgraph after["有 MCP：M + N"]
    direction TB
    b1[应用 A] --- p[("MCP")]
    b2[应用 B] --- p
    p --- t1[搜索 server]
    p --- t2[数据库 server]
  end
  before --> after
{% endmermaid %}

协议本身只规定**三种服务端原语**：

| 原语 | 一句话解释 | 典型例子 |
|---|---|---|
| Tools | 模型可以调用的函数 | 查天气、跑 SQL、发工单 |
| Resources | 模型可以读的上下文资源 | 文件、日志、表结构 |
| Prompts | 预置的提示词模板 | "帮我审这段代码" |

客户端那边还有几个反向能力（roots、sampling、elicitation）。这里有个大坑：**sampling 在 2026 年这条线上已经日落（sunset）**，看到老文章教你用 sampling 让服务器反过来"借"客户端的模型，先确认一下版本再说。

所有消息都是 JSON-RPC 2.0，所以"报文长什么样"这件事本身没什么可讲的——真正有意思的全在**传输**和**状态**上。

## 2. 两种传输：stdio 和 Streamable HTTP

社区里最常见的混乱是问"用 stdio 还是用 SSE"。这个问题本身是错的：**stdio 和 Streamable HTTP 是两种传输，SSE 是 HTTP 传输里的一种响应格式**，不是同一个维度的选项。

{% mermaid %}
flowchart LR
  subgraph local["stdio：把 server 当子进程"]
    c1[客户端] -->|"往 stdin 写 JSON-RPC"| srv[server 进程]
    srv -->|"从 stdout 回结果"| c1
  end
  subgraph remote["Streamable HTTP：server 是独立服务"]
    c2[客户端] -->|"POST /mcp"| http[server 服务]
    http -->|"JSON 或 SSE 流"| c2
  end
{% endmermaid %}

**stdio**：客户端把 server 当子进程拉起来，一行一条 JSON-RPC 消息，走进程的标准输入输出。没有端口、没有网络、没有鉴权，天然只服务一个客户端。桌面应用里的本地工具（读文件、跑命令、查本地库）基本都该用它。

**Streamable HTTP**：server 是独立部署的服务，客户端 POST 到单个端点（比如 `/mcp`），响应可以是普通 JSON，也可以是一条 SSE 流。这样才可能一边算一边回、多客户端共享。

### SSE 那段历史，为什么让人晕

- **2024-11-05**：规范里叫 "HTTP with SSE"。要两个端点——一个 POST 收请求，一个 GET 开 SSE 长连接收回复。两个端点意味着两套鉴权、两套路由、两套网关规则，还得处理"连接断了消息就丢了"。
- **2025-03-26**：换成 "Streamable HTTP"。**单端点**，POST 进去，普通请求直接回 JSON，需要流式就回一条 SSE。双端点方案从此列为 Deprecated。
- **2026-07-28**：连"流能不能续传"这件事都砍了——`Last-Event-ID`、事件 id、断点重投全部移除，断了就当这条请求丢了，客户端换个新 id 重发。

所以判断一份资料是不是过期，有个特别快的办法：**看它有没有教你配两个 URL**。有，就是 2024 年的东西。

## 3. 有状态 → 无状态：这三年到底改了什么

这是本文最想讲清楚的一段，因为它解释了今天所有"MCP 怎么扩容"的答案。

{% mermaid %}
flowchart LR
  v1["2024-11<br/>HTTP + SSE 双端点"] --> v2["2025-03<br/>Streamable HTTP"]
  v2 --> v3["2025-06<br/>协议版本头"]
  v3 --> v4["2025-11<br/>会话头改名"]
  v4 --> v5["2026-07<br/>删掉会话与握手"]
{% endmermaid %}

### 3.1 曾经的"有状态"长什么样

2025 年的设计里，一次连接是这样开的：

{% mermaid %}
flowchart TB
  subgraph old["2025：先握手，再一直带着会话号"]
    o1["initialize 握手"] --> o2["响应头发 Mcp-Session-Id"]
    o2 --> o3["之后每个请求都带这个头"]
    o3 --> o4["server 进程内存里存着这一轮的状态"]
  end
  subgraph new["2026-07：每条请求自带身份"]
    n1["tools/call"] --> n2["_meta 里带版本 / 能力 / 客户端信息"]
    n2 --> n3["server 现场处理，处理完就忘"]
  end
  old -.->|规范演进| new
{% endmermaid %}

规范原文写得很克制：服务器**可以**（MAY）在 initialize 的响应里给一个 `Mcp-Session-Id`，客户端**必须**（MUST）在后续请求里带上；服务器想结束会话就随便结束，之后对这个 id 回 404，客户端收到 404 **必须**重新握手。

问题就埋在"服务器**可以**"这三个字里。因为协议允许，所以生态里长出了大量"有会话"的实现：会话里存鉴权上下文、存用户偏好、存"上次查到第几页"、存 SSE 连接对象。这些东西一旦进内存，你就得到了一个有状态服务，它的所有麻烦随之而来。

### 3.2 为什么非删不可

一句话：**有状态的服务，扩容要付利息。**

- 负载均衡不能随便轮询了，得做会话粘滞，或者把会话搬进 Redis；
- 一个节点重启，落在那台机器上的会话全断，客户端得重新握手；
- 一台机器能扛多少客户端，取决于能存多少会话，于是你得设计上限、空闲回收、超时踢人；
- 长连接本身也贵：每个客户端挂一条 GET SSE 流，就是一条一直开着的 HTTP 连接。

而现实是：**绝大多数工具调用根本不需要状态。** 查天气不需要知道上次查了谁，跑一次 SQL 不需要记住上一条 SQL。为了少数场景让所有部署变复杂，显然不划算。

2026-07-28 这一版的处理非常干净利落：

- **删掉 `initialize` 握手**。连接不再有"建立"这一步，上来就是请求。
- **删掉 `Mcp-Session-Id`**。没有会话号可带，也就没有会话可以丢。
- **每条请求自带身份**：`_meta` 里放 `io.modelcontextprotocol/protocolVersion`、`.../clientCapabilities`，客户端建议再带 `clientInfo`；服务器在结果里回 `serverInfo`，版本对不上就回 `UnsupportedProtocolVersionError`。
- **新增 `server/discover`**：想一次性知道"这台服务器支持什么版本、有什么能力、是谁"，就问它，服务器必须实现。
- **列表不再随连接变化**：`tools/list` 的结果跟连接无关了，可以缓存、可以 CDN、可以预先算好。

### 3.3 那状态去哪了？

不是不许有状态，是**状态不能藏在连接里，得变成明面上的东西**。规范给了三条路：

1. **显式句柄**：需要跨调用记住什么，就让服务器造一个 handle 当普通参数传回来。想记分页位置？返回一个 `cursor`；想记购物车？返回一个 `cart_id`。这样状态存在你的数据库里，服务器本身还是无状态的。
2. **MRTR（Multi Round-Trip Requests）**：服务器处理到一半发现"我需要用户确认一下"，就回一个 `resultType: "input_required"` 的结果，里面带 `inputRequests`；客户端拿着答案，**带着 `inputResponses` 把原请求重发一遍**。注意——是客户端重发，不是服务器挂在内存里等。
3. **`subscriptions/listen`**：要收变更通知？开一条长寿命的 POST 响应流，声明你关心哪几类事件（工具列表变了、资源列表变了……），服务器通过这条流推给你。

### 3.4 我拿真机跑了一遍，差别是这样的

光看规范容易将信将疑，所以我在本机用官方 v2 SDK（`@modelcontextprotocol/server@2.4.0`，2026-07-28 这条线）写了个最小服务器，把两种"时代"的请求各发了一遍。

**第一条：老办法，先握手。**

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"old-client","version":"1.0"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
```

服务器依次回：

```json
{"result":{"protocolVersion":"2025-06-18","capabilities":{"tools":{"listChanged":true}},"serverInfo":{"name":"weather","version":"1.0.0"}}}
```

**第二条：新办法，不握手，每条请求自带 `_meta`。**

```json
{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{},"io.modelcontextprotocol/clientInfo":{"name":"probe","version":"0.0.1"}}}}
```

回的列表里带着几个新字段，信息量很大：

```json
{"result":{"tools":[{ "name":"get-forecast", "description":"获取某城市的天气预报",
  "inputSchema":{ "$schema":"https://json-schema.org/draft/2020-12/schema", "type":"object",
                  "properties":{"city":{"type":"string"}}, "required":["city"] }}],
  "resultType":"complete", "ttlMs":0, "cacheScope":"private",
  "_meta":{"io.modelcontextprotocol/serverInfo":{"name":"weather","version":"1.0.0"}}}}
```

`resultType: "complete"` 是新版每个结果都必须带的；`ttlMs` 和 `cacheScope` 是**给客户端和网关的缓存指令**（我这里是 0 和 private，意思是别缓存）——这一点后面讲扩容时会再用到。

**顺手踩的一个坑**：如果你不带 `_meta` 直接发 `server/discover`，服务器会把它当成 2025 时代的"无声明开场"，回你一句：

```json
{"jsonrpc":"2.0","id":1,"error":{"code":-32601,"message":"Method not found"}}
```

不是服务器坏了，是它按旧规矩接待了你。

## 4. 那 SSE 现在还有什么用

回到聊天记录里没答完的那个问题：**什么样的工具需要推送？**

答案是"当服务器有话说，而这句话不在本次请求的返回值里"的时候。2026-07-28 之后，这句话的场景收敛成四类：

{% mermaid %}
sequenceDiagram
  participant C as 客户端
  participant S as MCP Server
  C->>S: tools/call 一个长任务
  S-->>C: 进度通知 progress
  S-->>C: resultType: input_required
  Note over C,S: 服务器要输入（MRTR），但不占内存
  C->>S: 带 inputResponses 重发原请求
  S-->>C: resultType: complete
{% endmermaid %}

1. **流式结果**：结果太大或太慢，一条 SSE 事件一条地吐，比攒完再发体验好得多。
2. **进度通知**：长任务报进度，让客户端别以为卡死了。
3. **变更订阅**：`subscriptions/listen`，工具或资源列表变了推给客户端。
4. **中途要输入**：MRTR 的 `input_required`。

**不需要推送的场景，就别用流。** 一次查询、一次写入、一次计算，普通 JSON 返回就行——多一条长连接，就多一份连接数、超时、网关和负载均衡的配置成本。

## 5. MCP Gateway：把"很多个 server"收成一个

这里要先把一个误解拆掉：**网关不是用来给单个 server 扩容的。** 单个 server 扛不住，你该做的是无状态化 + 加副本（下一节）。网关解决的是另一种痛：

- Agent 那边要配 10 个 server，每个都有自己的启动命令、环境变量、密钥；
- 10 个 server 的工具全塞进上下文，光工具描述就吃掉几千 token；
- 密钥散落在每个客户端的配置里，谁泄露了都不知道；
- 想审计"这个 Agent 今天调了哪些工具"，无从查起。

以 Docker 的 MCP Gateway 为例（`docker/mcp-gateway`，Docker Desktop 里 MCP Toolkit 的底座），它把这几件事一次性办了：每个 server 跑在独立容器里、**统一入口**、密钥由 Docker 侧管理而不进环境变量、内置 OAuth 流程、**动态发现**所有 server 的 tools/resources/prompts 并聚合、外加日志与调用追踪。

{% mermaid %}
flowchart LR
  c1[Claude Desktop] --> gw[("MCP Gateway")]
  c2[Cursor] --> gw
  c3[自研 Agent] --> gw
  gw -->|"鉴权 · 聚合 · 审计"| s1[搜索 server]
  gw --> s2[数据库 server]
  gw --> s3[工单 server]
{% endmermaid %}

所以判断"要不要上网关"，看的是这三条里中了几条：**工具多到管不过来 / 密钥多到不敢发 / 要审计**。只有一台 server、只有你自己用，加网关纯属给自己加一层故障点。

顺带一个容易被忽略的收益：网关可以让多个客户端共享同一份"发现结果"。SDK 给网关/worker 池专门留了 `prior` 参数——**探测一次 `server/discover`，把结果存起来，后面每个新客户端连接时直接采用，一个字节都不用发**。对"网关每秒要接几百个短连接"这种场景，这是实打实的省。

## 6. 调用量特别大，怎么办

把优化按"从便宜到贵"排个序，照这个顺序做基本不会错。

{% mermaid %}
flowchart TB
  l1["① 无状态化：请求之间不留内存"] --> l2["② 横向加副本：负载均衡随便挂"]
  l2 --> l3["③ 上缓存：ttlMs / cacheScope"]
  l3 --> l4["④ 事件跨节点：ServerEventBus 接 Redis"]
  l4 --> l5["⑤ 网关兜底：限流 / 熔断 / 连接池"]
{% endmermaid %}

**① 无状态化。** 在 2026-07-28 这条线上，这是默认行为：每个 HTTP 请求都从你的工厂函数现场造一个 server 实例，处理完就扔。没有会话就没有粘滞，没有粘滞就没有"某台机器挂了带走一批客户端"。

**② 横向加副本。** 无状态之后，横向扩容是"挂到任意负载均衡后面"这一句话的事——不需要会话亲和，不需要共享状态，不需要配置。这也是为什么规范宁肯删掉会话：**它把扩容从"架构设计"降级成了"运维动作"**。

如果你还停在 2025 的老线（有会话），那就只有两条路：把会话搬进共享存储（每个节点都指向同一个 event store，断流可从任意节点续），或者做消息路由（按 session 把流量固定到属主节点）。两条都比无状态贵。

**③ 缓存。** 结果里的 `ttlMs` 和 `cacheScope` 就是干这个的。`tools/list` 这类"与连接无关"的端点天生适合缓存；网关侧缓存一份，能挡掉大量重复发现请求。

**④ 事件总线。** 无状态部署里唯一还会跨节点的东西是 `subscriptions/listen`——默认的事件总线是进程内的，A 节点上的"工具变了"永远到不了 B 节点上挂着的订阅者。解法是把 `ServerEventBus` 实现到你的 Redis / MQ 上，每个节点都拿同一个总线。

**⑤ 网关兜底。** 限流、熔断、并发上限、连接池，放在网关层比放在每个 server 里靠谱，因为它是唯一能看到全局流量的地方。

还有一个必须提的成本项：**工具描述也是 token**。十个 server 一百个工具全暴露给模型，每次请求都要为这些描述付钱，还容易让模型选错。所以"先缩小暴露面，再谈扩容"——按需发现、按场景挂载、用完就摘，往往比加机器更有效。

## 7. 写一个最简单的 MCP

理论说完了，动手。下面这个服务器我本机跑通过，改动量几乎为零。

### 7.1 装依赖

```bash
npm install @modelcontextprotocol/server zod
```

注意是 `@modelcontextprotocol/server` 这个新包（v2），不是老的 `@modelcontextprotocol/sdk`。顺手记两个坑：v2 要求 **zod 4**（`zod ^4.2.0`），并且 TypeScript ≥ 6 不再自动带 `@types/*`，`tsconfig` 里要写 `"types": ["node"]`。

### 7.2 三十行写完

```javascript
import { McpServer } from '@modelcontextprotocol/server';
import { serveStdio } from '@modelcontextprotocol/server/stdio';
import * as z from 'zod/v4';

serveStdio(() => {
  const server = new McpServer({ name: 'weather', version: '1.0.0' });

  server.registerTool(
    'get-forecast',
    {
      description: '获取某城市的天气预报',
      inputSchema: z.object({ city: z.string() }),
    },
    async ({ city }) => ({
      content: [{ type: 'text', text: `${city} 未来一周晴天。` }],
    }),
  );

  return server;
});
```

几个点值得停一下：

- `serveStdio` 收的是一个**工厂函数**，不是实例。每次需要新实例时它自己调——这正是"无状态"在代码里的样子。
- `inputSchema` 直接写 zod，SDK 会转成 JSON Schema（我上面实测输出的是 draft 2020-12 那份）。
- 处理函数返回的是 `content` 数组，不是字符串——因为一条回复可以由多种内容拼成（文本、图片、资源引用）。

### 7.3 跑起来

stdio 服务器不会自己打印什么，你得喂给它 JSON-RPC。把下面几行按行写进去：

```bash
printf '%s\n' \
 '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{},"io.modelcontextprotocol/clientInfo":{"name":"probe","version":"0.0.1"}}}}' \
 '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get-forecast","arguments":{"city":"杭州"},"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{},"io.modelcontextprotocol/clientInfo":{"name":"probe","version":"0.0.1"}}}}' \
 | node weather.mjs
```

你会看到两行回包，第二行是：

```json
{"result":{"content":[{"type":"text","text":"杭州 未来一周晴天。"}],"resultType":"complete","_meta":{"io.modelcontextprotocol/serverInfo":{"name":"weather","version":"1.0.0"}}}}
```

**没有任何握手，上来就是调用**——这就是 2026-07-28 的样子。

### 7.4 接进真实客户端

本地工具用 stdio，配置里就是一条命令：

```json
{
  "mcpServers": {
    "weather": {
      "command": "node",
      "args": ["/绝对路径/weather.mjs"]
    }
  }
}
```

### 7.5 三个必踩的坑

**坑一：`console.log` 会把客户端搞挂。** stdio 传输里 stdout 是协议通道，你打一行调试日志，客户端就读到一条不合法的 JSON-RPC，直接断连。所有日志走 `console.error`。

**坑二：不带 `_meta` 会得到 `Method not found`。** 如上文实测，裸请求会被当成 2025 时代的老客户端。写测试脚本时务必带上。

**坑三：工具描述就是上下文成本。** 描述写得太细，每个会话都要为它付 token；写得太粗，模型选错工具。经验是**一句话说清"什么时候该用它"**，比罗列参数更有用（参数本来就在 schema 里）。

## 8. 一页速查

| 问题 | 答案 |
|---|---|
| 本地工具用什么传输 | stdio（子进程 + 标准输入输出） |
| 远程服务用什么传输 | Streamable HTTP（单端点，JSON 或 SSE） |
| 看到两个端点 / 两个 URL | 2024 年的老写法，已废弃 |
| 现在还有会话吗 | 2026-07-28 起没有了，连 `initialize` 都删了 |
| 那状态存哪 | 显式句柄当参数、MRTR、`subscriptions/listen` |
| 什么时候开流 | 流式结果、进度、变更订阅、中途要输入 |
| 会话粘滞还要不要 | 无状态部署不要；只有 2025 老线才需要 |
| 网关解决什么 | 工具多、密钥多、要审计；不是用来给单点扩容的 |
| 扩容第一步 | 无状态化，然后横向加副本 |
| 最省事的降本 | 减少暴露给模型的工具数量 |

## 相关阅读

- [FunctionCall、Agent、Mcp](/2026/04/25/AI_MCP/) —— 三者的入门概念与对比，本文是它在协议层面的展开
- [A2A 协议：让 AI Agent 学会"对话"的通信标准](/2026/05/11/A2A-Agent%E9%97%B4%E9%80%9A%E4%BF%A1%E5%8D%8F%E8%AE%AE/) —— MCP 管"Agent 到工具"，A2A 管"Agent 到 Agent"，互补而非竞争
- [DSH Agent 主循环：一次对话到底是怎么跑起来的](/2026/10/30/DSH-Agent%E4%B8%BB%E5%BE%AA%E7%8E%AF/) —— 工具调用在 Agent 内部长什么样
- [DSH 沙箱设计：一次 bash 调用，到底被关进了什么](/2026/11/02/DSH-%E6%B2%99%E7%AE%B1%E8%AE%BE%E8%AE%A1/) —— 工具真跑起来之后，边界在哪
