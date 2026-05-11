---
title: A2A 协议：让 AI Agent 学会"对话"的通信标准
date: 2026-05-11 14:00:00
tags: [Agent, A2A, Protocol, AI]
categories: [Agent]
cover: https://free.picui.cn/free/2026/04/25/69eccad3e8440.png
---

## 前言

当我们讨论 AI Agent 的能力边界时，一个常被忽略的问题是：**Agent 与 Agent 之间如何协作？**

单个 Agent 的能力终归有限。产品经理 Agent 擅长需求分析，开发工程师 Agent 精通技术架构，测试工程师 Agent 熟悉质量保障——但当一个复杂项目需要三者协同时，它们之间用什么语言"说话"？如何发现彼此的存在？又如何确保消息的可靠传递？

这就是 Google 在 2025 年提出 **A2A（Agent-to-Agent）协议**要解决的核心问题。A2A 定义了一套标准的、与框架无关的 Agent 间通信协议，让不同技术栈、不同厂商构建的 Agent 能够像微服务一样自由互联。

本文将从协议设计哲学出发，深入解析 A2A 的核心概念，并通过一个完整的多 Agent 协作系统的实现代码，展示协议如何从纸面规范落地为可运行的工程实践。

---

## 一、为什么需要 A2A

### 1.1 从"单兵作战"到"团队协作"

早期的 AI Agent 系统主要解决单 Agent 问题：给一个 Agent 足够的工具（搜索、代码执行、文件操作），它就能独立完成任务。但现实场景远比这复杂——

一个企业级 AI 工作流可能涉及：客服 Agent 接收用户诉求 → 分析 Agent 诊断问题 → 执行 Agent 实施修复 → 审核 Agent 验证结果。这些 Agent 可能由不同团队开发，部署在不同基础设施上，使用不同的 LLM 后端。如果没有统一的通信标准，每一对 Agent 之间都需要定制集成，复杂度会以 O(n²) 增长。

### 1.2 MCP 解决不了的问题

你可能会想：我们不是已经有了 MCP（Model Context Protocol）吗？的确，MCP 解决了 Agent 与外部工具/数据源之间的标准化接口问题。但 MCP 的定位是一个 **"万能工具带"**——它让单个 Agent 能够通过标准协议访问数据库、API、文件系统等资源。

A2A 解决的是另一个维度的问题：**Agent 与 Agent 之间的对等通信**。一个参与 A2A 通信的 Agent，可能内部使用 MCP 来调用自己的工具，但对外它通过 A2A 协议与其他 Agent 交互。两者是互补关系：MCP 扩展了单个 Agent 的"手"，A2A 连接了多个 Agent 的"脑"。

### 1.3 A2A 的五个设计原则

Google 在设计 A2A 时遵循了五个核心原则：

**原则一：拥抱 Agent 的"不透明性"（Opaque Execution）。** 不要求 Agent 暴露内部实现。一个 Agent 对另一个 Agent 来说就是黑盒——你只需要知道它能做什么（通过 AgentCard），不需要知道它怎么做。

**原则二：以现有 Web 标准为基础。** A2A 建立在 HTTP、JSON-RPC 2.0、SSE 等成熟的 Web 技术之上，不发明新的传输协议，最大化兼容性和可落地性。

**原则三：支持长时任务。** Agent 协作不是简单的"问一句答一句"。一个任务可能需要几分钟甚至几小时，A2A 通过 Task 生命周期管理和流式更新来支持这类场景。

**原则四：模态无关。** Agent 间交换的不仅是文本，还可能是文件、图片、结构化数据。A2A 的 Part 机制支持多种内容类型的传递。

**原则五：安全可信。** 支持企业级的认证和授权机制，确保 Agent 间通信的安全性。

---

## 二、A2A 协议的核心概念

A2A 协议围绕几个核心抽象构建，其中最重要的是：AgentCard、Task、Message、Part 和 Artifact。让我们拆解其中与工程实践最相关的部分。

### 2.1 AgentCard —— Agent 的"数字名片"

AgentCard 是整个 A2A 协议的起点。按照规范建议，每个 Agent 在 `/.well-known/agent.json` 路径发布一份 JSON 文档，声明自己是谁、能做什么、如何与之通信（也可通过目录服务等其他方式发布）。

```json
{
  "name": "产品经理",
  "description": "资深产品经理，负责产品需求分析和规划",
  "version": "1.0.0",
  "supportedInterfaces": [
    {
      "url": "http://localhost:9001/",
      "protocolBinding": "JSONRPC",
      "protocolVersion": "1.0.0"
    }
  ],
  "capabilities": { "streaming": true },
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["text/plain"],
  "skills": [
    {
      "id": "product_planning",
      "name": "产品需求规划",
      "description": "分析需求、输出PRD、定义功能优先级",
      "tags": ["collaboration"]
    }
  ]
}
```

AgentCard 的设计哲学非常清晰：它是 Agent 对外发布的**唯一自描述文档**，包含了发现和使用这个 Agent 所需的全部信息。其中最重要的字段是 `skills`——它让调用方知道这个 Agent 具体能做什么，而无需了解其内部如何实现。

### 2.2 Task —— 工作的生命周期

Task 是 A2A 协议中的核心工作单元。当一个 Agent 向另一个 Agent 发送请求时，就会创建一个 Task，它经历以下状态流转：

```
submitted → working → completed
                   → input-required（需要更多信息）
                   → canceled
                   → failed
```

Task 的生命周期设计使得 A2A 天然支持长时任务。一个 Task 可以在 `working` 状态持续任意时间，期间通过 SSE 流式推送进度更新。如果执行过程中需要额外信息，Agent 可以将 Task 状态切换为 `input-required`，等待调用方补充输入后继续执行。

### 2.3 Message —— 通信的基本单位

Message 是 Agent 间传递信息的载体，包含两个关键属性：

- **role**: `user`（请求方）或 `agent`（响应方）
- **parts**: 消息的内容片段列表

一条 Message 可以包含多个 Part，比如一段文字说明 + 一个附件 + 一块结构化数据，这种设计使得 Agent 间的信息交换足够灵活。

### 2.4 Part —— 最小内容单元

Part 是 A2A 中最小的内容承载单元，支持多种类型：

- **TextPart**: 纯文本内容
- **FilePart**: 文件数据（包含 MIME 类型，可以是 base64 编码的内联数据或外部 URL）
- **DataPart**: 结构化数据（JSON 对象）

这三种 Part 类型覆盖了 Agent 协作中的绝大多数数据交换场景。

### 2.5 Artifact —— 任务的输出产物

Artifact 是 Task 执行过程中产生的具体输出结果。与 Message 作为通信载体不同，Artifact 代表的是有明确结构的**成果物**——比如一份生成的文档、一段代码、一张图片。Artifact 内部同样由 Parts 组成，但它额外携带元数据（如名称、MIME 类型），使得接收方可以直接使用这些产出物。简单来说：Message 是"对话"，Artifact 是"交付物"。

### 2.6 通信传输 —— JSON-RPC + SSE

A2A 选择了 JSON-RPC 2.0 作为通信协议，核心方法包括（以早期版本规范为例，后续版本方法名格式可能有变化）：

| 方法 | 用途 |
|------|------|
| `message/send` | 发送消息并等待完整响应 |
| `message/stream` | 发送消息并通过 SSE 流式接收响应 |
| `tasks/get` | 查询 Task 当前状态 |
| `tasks/cancel` | 取消正在执行的 Task |

流式通信（Streaming）通过 Server-Sent Events 实现，这使得长时间运行的任务可以实时推送中间结果，而不需要调用方反复轮询。

---

## 三、从规范到实现：一个完整的多 Agent 协作系统

理论讲完了，下面我们通过一个真实的实现案例来看 A2A 如何从协议规范变成可运行的代码。这个系统模拟了一个软件开发团队：产品经理、开发工程师、测试工程师三个 Agent，它们之间可以自由协作。

### 3.1 系统架构

```
┌─────────────────────────────────────────────────────┐
│  CLI 客户端                                          │
│  用户: @产品 去问一下开发现在是什么进度                  │
│       │                                             │
│       ▼ A2A message/send (SSE)                      │
│  ┌─────────────────────────────────────────────┐    │
│  │  产品经理 Agent :9001                        │    │
│  │  1. LLM 分析 → 判断需要调用其他 Agent         │    │
│  │  2. 作为 A2A 客户端 → 调用开发工程师          │    │
│  │  3. 综合结果回复用户                          │    │
│  └─────────────────────────────────────────────┘    │
│       │ A2A (Agent → Agent)                         │
│       ▼                                             │
│  ┌─────────────────────────────────────────────┐    │
│  │  开发工程师 Agent :9002                      │    │
│  └─────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────┐    │
│  │  测试工程师 Agent :9003                      │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

关键设计：**每个 Agent 既是 A2A Server（接收请求），也是 A2A Client（发起请求）。** 这种双重角色使得 Agent 间的通信是真正对等的，任何 Agent 都可以主动发起对另一个 Agent 的调用。

### 3.2 Agent 发现：从硬编码到动态自发现

在标准 A2A 中，Agent 的发现不依赖中心化注册表，而是通过拉取 AgentCard 实现。实现代码中的 `agent_discovery.py` 展示了这一机制：

```python
# 种子地址列表：只记录"去哪里找 Agent"
SEED_AGENT_URLS = [
    "http://localhost:9001",
    "http://localhost:9002",
    "http://localhost:9003",
]

async def fetch_agent_card(base_url: str) -> dict | None:
    """从 Agent 的标准端点动态获取 AgentCard（简化展示，实际含异常处理）。"""
    url = f"{base_url.rstrip('/')}/.well-known/agent.json"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            card = resp.json()
            card["_base_url"] = base_url
            return card
    except Exception:
        return None  # 连接失败时静默跳过
```

这里体现了 A2A 的一个重要设计决策：系统只需维护一份种子 URL 列表（类似 DNS 的根服务器），Agent 的能力描述、通信方式等所有细节都从 AgentCard 动态获取。新增 Agent 只需在种子列表中加一条 URL，无需修改任何其他代码。

与之对比的是项目中已被标记为弃用的硬编码注册表方式（`agent_registry.py`）：

```python
# [已弃用] 硬编码注册表 — 存在多个问题
AGENT_REGISTRY = {
    "产品经理": {
        "url": "http://localhost:9001",
        "description": "负责产品需求分析和规划",
    },
    ...
}
```

硬编码方式有三个致命缺陷：新增 Agent 需手动修改注册表、能力描述可能与实际 AgentCard 不一致、不支持 Agent 的动态上下线。标准 A2A 的 AgentCard 自发现机制优雅地解决了这些问题。

### 3.3 Agent 执行器：双重角色的实现

`base_agent.py` 中的 `BaseAgentExecutor` 是整个系统的核心。它封装了一个 Agent 同时作为服务端和客户端的完整逻辑：

```python
class BaseAgentExecutor(AgentExecutor):
    AGENT_NAME: str = ""
    SYSTEM_PROMPT: str = ""

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        # 1. 获取用户输入
        user_input = context.get_user_input()

        # 2. 调用 LLM（带 function calling）
        result = await call_llm_with_tools(
            system_prompt=self.SYSTEM_PROMPT,
            user_input=user_input,
            self_name=self.AGENT_NAME,
            a2a_caller=self._call_other_agent,  # 注入 A2A 调用能力
        )

        # 3. 将结果发布到事件队列
        response_message = new_text_message(text=result, role=Role.ROLE_AGENT)
        await event_queue.enqueue_event(response_message)

    async def _call_other_agent(self, url: str, message: str) -> str:
        """作为 A2A 客户端调用其他 Agent（SSE 流式）。"""
        config = ClientConfig(streaming=True)
        async with httpx.AsyncClient(timeout=120.0) as http_client:
            config.httpx_client = http_client
            factory = ClientFactory(config)
            client = await factory.create_from_url(url)

            request = SendMessageRequest(
                message=Message(
                    role=Role.ROLE_USER,
                    parts=[Part(text=message)],
                    message_id=str(uuid.uuid4()),
                )
            )

            result_texts = []
            async for response in await client.send_message(request):
                text = get_stream_response_text(response)
                if text:
                    result_texts.append(text)
            await client.close()
            return "\n".join(result_texts) if result_texts else "(无回复)"
```

这段代码的精妙之处在于：`_call_other_agent` 方法被作为回调注入到 LLM 工具调用链中。LLM 通过 function calling 自主决定是否需要与其他 Agent 协作——这不是硬编码的编排逻辑，而是 **Agent 基于上下文的自主决策**。

### 3.4 LLM 作为路由器：Function Calling 驱动的协作

Agent 间的协作不靠预设的工作流，而是 LLM 动态决定的。`llm_utils.py` 展示了这一机制的核心实现：

```python
async def build_call_agent_tool(self_name: str):
    """动态构建 function calling 工具定义。"""
    # 通过 AgentCard 动态发现其他 Agent
    cards = await discover_all_agents(exclude_name=self_name)
    name_to_url = {card["name"]: extract_rpc_url(card) for card in cards}

    # 从 AgentCard.skills 构建能力描述
    agent_list = "\n".join(
        f"- {card['name']}: {extract_skills_description(card)}"
        for card in cards
    )

    tools = [{
        "type": "function",
        "function": {
            "name": "call_agent",
            "description": f"调用团队中的其他智能体进行协作。\n"
                          f"以下智能体通过 AgentCard 动态发现：\n{agent_list}",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "enum": list(name_to_url.keys()),
                    },
                    "message": {"type": "string"},
                },
                "required": ["agent_name", "message"],
            },
        },
    }]
    return tools, name_to_url
```

这段实现揭示了一个关键的架构模式：**Agent 的可调用列表不是静态配置的，而是每次调用前从 AgentCard 动态发现的。** 工具定义中的 `enum` 字段和 `description` 都来自运行时获取的 AgentCard 数据。这意味着即使在运行过程中新增或下线一个 Agent，系统也能自动适配。

LLM 调用流程是一个两阶段过程：

```python
async def call_llm_with_tools(system_prompt, user_input, self_name, a2a_caller):
    tools, name_to_url = await build_call_agent_tool(self_name)

    # 第一次调用：LLM 决定是否需要协作
    response = await client.chat.completions.create(
        model=model, messages=messages, tools=tools, tool_choice="auto"
    )

    # 如果 LLM 决定调用其他 Agent
    if assistant_message.tool_calls:
        for tool_call in assistant_message.tool_calls:
            agent_name = func_args["agent_name"]
            agent_url = name_to_url[agent_name]
            # 通过 A2A 协议发起调用
            result = await a2a_caller(agent_url, agent_message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

        # 第二次调用：综合协作结果生成最终回复
        final_response = await client.chat.completions.create(
            model=model, messages=messages
        )
```

这个"两次 LLM 调用"模式是 Agent 协作的经典范式：第一次调用让 LLM 分析用户意图并决定协作策略，第二次调用让 LLM 基于协作结果生成最终回复。

### 3.5 具体 Agent 的实现：极简的继承模式

有了 BaseAgentExecutor 的抽象，具体 Agent 的实现变得极其简洁：

```python
class ProductAgentExecutor(BaseAgentExecutor):
    AGENT_NAME = "产品经理"
    SYSTEM_PROMPT = """你是一个资深产品经理。你的职责包括：
    - 分析用户需求，输出清晰的产品需求文档(PRD)
    - 定义产品功能优先级
    - 与开发工程师和测试工程师协作沟通

    当用户要求你与其他团队成员沟通时，请使用 call_agent 工具来联系他们。"""
```

每个具体 Agent 只需定义两样东西：名称和系统提示词。所有的 A2A 通信、AgentCard 发布、Agent 发现、LLM 调用、function calling 处理都由基类封装。这种设计使得新增一个 Agent 的成本极低——写一个 prompt，起一个端口，系统就能自动发现并纳入协作网络。

### 3.6 运行效果

```
你> @产品 设计一个在线教育平台的核心功能
[产品经理 回复]: ...PRD 内容...

你> @产品 去问一下开发这个方案技术上可行吗
[发送至 产品经理]
[产品经理 回复]: 我刚和开发工程师沟通了，他认为...
  └── 内部自动调用了 开发工程师 Agent (A2A)

你> @测试 针对这个方案出一个测试计划
[测试工程师 回复]: ...测试计划...
```

注意第二条交互：用户只是告诉产品经理"去问一下开发"，产品经理 Agent 自主决定通过 A2A 协议调用开发工程师 Agent，获取回复后综合整理再反馈给用户。这就是 A2A 协议赋予 Agent 的核心能力——**自主协作**。

---

## 四、A2A 与 MCP 的关系：不是竞争，是互补

很多人第一次接触 A2A 时的疑问是：它和 MCP 有什么区别？让我们把这个问题说清楚。

| 维度 | MCP | A2A |
|------|-----|-----|
| 定位 | Agent ↔ 工具/数据源 | Agent ↔ Agent |
| 类比 | "万能工具带" | "Agent 间的对话协议" |
| 通信模式 | Client-Server（Agent 调用工具） | 双向 Client-Server（任意 Agent 可主动发起请求） |
| 核心解决的问题 | 扩展单个 Agent 的能力边界 | 连接多个 Agent 的协作网络 |
| 典型使用 | Agent 读数据库、调 API、操作文件 | Agent 请另一个 Agent 帮忙完成子任务 |

一个典型的企业系统中，两者完美互补：每个 Agent 内部通过 MCP 连接自己的工具集（数据库、搜索引擎、文件系统），对外通过 A2A 与其他 Agent 协作。就像一个团队里每个人都有自己的工具箱（MCP），但他们之间通过会议和邮件（A2A）进行协作。

---

## 五、A2A 在实际场景中的价值

### 5.1 企业跨部门 Agent 协作

想象一个客服场景：客服 Agent 收到用户投诉 → 通过 A2A 调用订单查询 Agent → 再调用退款处理 Agent → 最终综合结果回复用户。每个 Agent 由不同团队维护，通过标准协议互联。

### 5.2 多厂商 Agent 生态

一个旅行规划平台：酒店推荐 Agent（厂商A）+ 机票搜索 Agent（厂商B）+ 行程规划 Agent（厂商C）。A2A 让不同厂商的 Agent 能够无缝协作，就像微服务通过 REST/gRPC 互联一样。

### 5.3 分布式 Agent 系统

大规模 Agent 系统中，不同 Agent 可以部署在不同的机器、不同的网络区域，通过 A2A 协议跨网络通信。Agent 的水平扩展变得与传统微服务一样自然。

---

## 六、设计思考：A2A 做对了什么

### 6.1 最小化协议面

A2A 没有试图规定 Agent 内部应该如何运作，只定义了外部通信接口。这使得任何技术栈——无论是 LangChain、AutoGen、CrewAI 还是自研框架——都可以实现 A2A 兼容。协议的"薄度"恰恰是其最大优势。

### 6.2 渐进式复杂度

最简单的 A2A 实现只需要：一个 HTTP 端点返回 AgentCard + 一个 JSON-RPC 端点处理消息。不需要 streaming、不需要长时任务、不需要多模态。随着需求增长，再逐步开启这些能力。这种渐进式设计大大降低了入门门槛。

### 6.3 基于 Web 标准

HTTP + JSON-RPC + SSE，全部是成熟的 Web 技术。不需要安装特殊的 SDK 或运行时，任何能发 HTTP 请求的语言都能实现 A2A 客户端。这个决策让 A2A 的生态潜力远超那些依赖特定框架的方案。

### 6.4 Agent 自治与协作的平衡

A2A 的"不透明性"原则非常巧妙：Agent 之间互为黑盒，只通过声明的接口交互。这既保护了各 Agent 的实现细节（可能涉及商业机密），又确保了协作的标准化。一个 Agent 不需要知道另一个 Agent 是用 GPT-4 还是 Claude 驱动的，它只需要知道对方"能做什么"。

---

## 七、总结

A2A 协议回答的核心问题其实很简单：**如何让 AI Agent 像微服务一样互联互通？**

它的答案是三个层面的标准化：**发现**（AgentCard 声明能力）、**通信**（JSON-RPC + SSE 传递消息）、**协调**（Task 生命周期管理状态）。

从本文分析的实现代码中，我们可以看到 A2A 真正的工程价值：写一个新 Agent 只需定义 prompt 和端口，系统自动完成发现、通信、协作的全部连接。当 Agent 数量从 3 个增长到 30 个、300 个时，这种标准化的威力才会真正显现。

如果说 MCP 让每个 Agent 都拥有了强大的"个人工具箱"，那么 A2A 就是给整个 Agent 生态铺设的"高速公路网"。未来的 AI 系统，必然是无数专精 Agent 通过标准协议协作的分布式网络。A2A 正在为这个未来铺路。

---

## 参考

- [Google A2A Protocol 官方仓库](https://github.com/a2aproject/A2A)
- [A2A Protocol Specification](https://a2a-protocol.org/latest/specification/)（[GitHub 备用链接](https://github.com/a2aproject/A2A/blob/main/docs/specification.md)）
- [Announcing the Agent2Agent Protocol](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- 本文实现代码：基于 Google A2A Python SDK（`a2a` 包）构建的多 Agent 协作演示系统
