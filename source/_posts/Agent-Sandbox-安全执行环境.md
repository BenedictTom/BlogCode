---
title: Agent Sandbox：为什么 AI Agent 需要一个安全的执行环境
date: 2026-04-28 12:00:00
tags: [Agent, Sandbox, AI]
categories: [Agent]
cover: https://free.picui.cn/free/2026/04/25/69eccad3e8440.png
---

## 前言

当我们谈论 AI Agent 时，很容易把注意力集中在模型的推理能力上——它能不能理解需求、能不能生成正确的代码、能不能规划合理的步骤。但有一个更基础的问题常常被忽略：**Agent 生成的代码和命令，在哪里执行？**

想象一个场景：你让 AI Agent 帮你分析一份 CSV 数据。Agent 决定写一段 Python 脚本来处理，然后调用 `subprocess.run()` 执行它。问题来了——如果这段脚本有 bug，不小心执行了 `rm -rf /`，后果不堪设想。又或者，Agent 需要 `pip install` 一个库，但你不希望它污染你的本地环境。

这就是 **Sandbox**（沙箱）要解决的问题。它为 Agent 提供一个**隔离的、受控的、可销毁的执行环境**，让 Agent 可以自由地执行代码、运行命令、操作文件，而不会影响宿主机的安全和稳定。

---

## 一、为什么 Agent 需要 Sandbox

### 1.1 Agent 不只是"聊天"，它要"动手"

传统的 LLM 应用（比如 ChatGPT 的对话模式）只需要生成文本，不需要真正执行任何操作。但 Agent 不同——它的核心能力在于**行动**：执行代码、调用 API、操作文件系统、控制浏览器。这意味着 Agent 的输出不再是无害的文字，而是**有副作用的操作**。

这就引出了一个根本性的信任问题：**你敢让一个概率模型直接在你的生产环境里执行任意代码吗？**

答案显然是不敢。LLM 的输出天然具有不确定性——它可能生成正确的代码，也可能生成有 bug 的代码，甚至可能被 prompt injection 诱导执行恶意操作。在没有隔离的情况下，任何一次错误执行都可能导致数据丢失、环境损坏或安全泄露。

### 1.2 四个核心需求

Agent 对执行环境的需求可以归纳为四个维度：

**安全隔离** —— Agent 的操作不能影响宿主机。文件系统、网络、进程都需要隔离。即使 Agent 执行了破坏性命令，损失也限定在沙箱内部。

**环境一致性** —— Agent 需要一个预配置好的、可预测的运行环境。比如特定版本的 Python、预装的库、特定的系统工具。这样 Agent 的行为才具有可复现性。

**快速创建与销毁** —— 每个任务可能需要一个全新的沙箱，用完即弃。创建和销毁的速度直接影响 Agent 的响应体验。理想情况下，沙箱应该能在毫秒到秒级启动。

**可编程接口** —— Agent 不是通过终端手动操作沙箱，而是通过 API 调用。沙箱需要提供结构化的接口，让 Agent（或编排层）能够以编程方式执行命令、读写文件、获取运行结果。

### 1.3 为什么 Docker 不够？

有人可能会问：直接用 Docker 不就行了？Docker 确实提供了基本的隔离能力，但它并不是为 Agent 场景设计的：

首先是**启动速度**——Docker 容器的启动通常在秒级，对于需要频繁创建销毁的 Agent 任务来说偏慢。其次是**API 抽象层级**——Docker 提供的是底层容器操作接口，缺少"执行一段代码并返回结果"这样面向 Agent 的高层抽象。最后是**隔离强度**——Docker 基于 Linux namespace 和 cgroup 实现进程级隔离，所有容器共享宿主内核，恶意代码仍有可能通过内核漏洞逃逸。

专门为 Agent 设计的 Sandbox 方案在 Docker 的基础上做了大量增强：更快的启动、更高层的 API、更强的隔离（如 MicroVM）、以及针对 Agent 工作流的原生支持。

---

## 二、Sandbox 的使用模式

在 Agent 系统中，Sandbox 并不是一个独立存在的组件，而是以多种方式融入整个执行流程。

### 2.1 作为 Tool 调用

最常见的模式是将 Sandbox 封装为 Agent 的一个 **Tool**（工具）。Agent 在推理过程中决定需要执行代码时，调用 Sandbox Tool，将代码发送到沙箱执行，然后拿回结果继续推理。

以 AIO Sandbox 与 OpenAI Function Calling 的集成为例：

```python
from openai import OpenAI
from agent_sandbox import Sandbox

client = OpenAI(api_key="your_api_key")
sandbox = Sandbox(base_url="http://localhost:8080")

def run_code(code, lang="python"):
    """在沙箱中执行代码——这就是 Agent 的 Tool"""
    if lang == "python":
        result = sandbox.shell.exec_command(command=f"python3 -c '{code}'")
        return result.data.output
    result = sandbox.shell.exec_command(command=f"node -e '{code}'")
    return result.data.output

# Agent 通过 Function Calling 调用这个 Tool
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "计算斐波那契数列前20项"}],
    tools=[{
        "type": "function",
        "function": {
            "name": "run_code",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "lang": {"type": "string"},
                },
            },
        },
    }],
)
```

这种模式的优势在于**对 Agent 透明**——Agent 不需要知道代码在哪里执行，它只需要调用 `run_code` 工具，就能安全地执行任意代码。

同样的思路也适用于 LangChain 等框架。把 Sandbox 封装为 `BaseTool`，就可以无缝接入 LangChain 的 Agent 链：

```python
from langchain.tools import BaseTool
from agent_sandbox import Sandbox

class SandboxTool(BaseTool):
    name = "sandbox_execute"
    description = "在隔离沙箱中执行命令"

    def _run(self, command: str) -> str:
        client = Sandbox(base_url="http://localhost:8080")
        result = client.shell.exec_command(command=command)
        return result.data.output
```

### 2.2 作为 MCP Server

另一种越来越流行的模式是将 Sandbox 暴露为 **MCP（Model Context Protocol）Server**。MCP 是一个标准化的工具协议，Agent 可以通过 MCP 协议发现和调用沙箱提供的各种能力——执行命令、读写文件、操控浏览器等等。

相比直接封装为 Tool，MCP 模式的优势在于**标准化和可组合性**。一个 MCP 兼容的 Sandbox 可以被任何支持 MCP 的 Agent 框架直接使用，不需要为每个框架写适配代码。而且 MCP 天然支持能力发现——Agent 可以在运行时查询 Sandbox 提供了哪些工具，动态选择使用。

比如 AIO Sandbox 就内置了 MCP Server，启动后可以直接通过 `http://localhost:8080/mcp` 访问，提供浏览器操控、Shell 执行、文件管理等多种 MCP 工具。

### 2.3 作为 Code Interpreter

**Code Interpreter**（代码解释器）是 Sandbox 最经典的应用场景。Agent 生成一段代码，发送到 Sandbox 中的 Jupyter Kernel 或 Node.js 运行时执行，拿回标准输出、错误信息、甚至图表等富媒体结果。

这种模式的关键在于**状态保持**——同一个 Sandbox 实例中，前后多次代码执行共享上下文。Agent 可以先执行 `import pandas as pd`，然后在下一轮执行 `df = pd.read_csv("data.csv")`，最后执行 `df.describe()`。整个过程就像在一个持久化的 Jupyter Notebook 中工作。

OpenSandbox 和 CubeSandbox 都提供了专门的 Code Interpreter SDK，让这种模式的集成变得非常简单。

### 2.4 作为完整的开发环境

更高阶的用法是将 Sandbox 打造为 Agent 的**完整工作空间**——不只是执行代码，还包括浏览器、IDE、终端、文件管理器等全套开发工具。

AIO Sandbox 就是这种思路的典型代表。它在一个 Docker 容器中集成了 VNC 浏览器、VSCode Server、Jupyter Notebook、Shell 终端和文件系统，所有组件共享同一个文件系统。Agent 可以在浏览器中下载一个文件，然后在 Shell 中处理它，再在 VSCode 中编辑——一切无缝衔接。

这种 All-in-One 的设计解决了传统方案中多个单功能沙箱之间**文件共享和状态同步**的痛点。

---

## 三、Sandbox 的隔离技术

不同的 Sandbox 方案采用了不同层次的隔离技术，各有取舍。

### 3.1 容器级隔离

基于 Docker / OCI 容器的隔离是最基础的方案。它利用 Linux 的 namespace（隔离文件系统、网络、PID 等）和 cgroup（限制 CPU、内存等资源）来实现进程级别的隔离。

优点是成熟稳定、启动较快、生态丰富。缺点是所有容器共享同一个内核，如果内核存在漏洞，恶意代码可能逃逸到宿主机。对于大多数非对抗性场景（比如执行 Agent 自己生成的代码），容器级隔离已经足够。

### 3.2 安全容器

安全容器（如 gVisor、Kata Containers）在容器的基础上增加了一层额外的隔离。gVisor 通过在用户态实现一个 Linux 内核的子集来拦截系统调用，避免容器直接接触宿主内核。Kata Containers 则为每个容器创建一个轻量级虚拟机，通过硬件虚拟化实现真正的内核隔离。

OpenSandbox 支持 gVisor、Kata Containers 和 Firecracker MicroVM 等多种安全容器运行时，用户可以根据安全需求选择合适的隔离级别。

### 3.3 MicroVM

MicroVM（微虚拟机）是目前 Agent Sandbox 领域最强的隔离方案。它为每个沙箱创建一个独立的虚拟机，拥有独立的内核、独立的内存空间、独立的虚拟设备。即使沙箱内部被完全攻破，攻击者也无法接触到宿主机的内核。

CubeSandbox 就采用了基于 KVM 的 MicroVM 方案（CubeHypervisor）。它的亮点在于**启动速度**——通过预构建模板和快照技术，MicroVM 可以在极短时间内启动，同时保持完整的虚拟化隔离。

### 3.4 网络隔离

除了计算隔离，网络隔离也至关重要。Agent 执行的代码可能尝试访问外部网络——下载恶意软件、泄露敏感数据、或者攻击内网服务。

CubeSandbox 通过 CubeVS（基于 eBPF 的虚拟交换机）实现内核级的网络隔离和安全策略执行。OpenSandbox 则提供了 Ingress Gateway 和 per-sandbox Egress Controls，可以为每个沙箱单独配置网络出入规则。这种精细化的网络策略让管理员能够在"Agent 需要联网"和"不能让 Agent 随意访问"之间找到平衡。

---

## 四、开源 Sandbox 方案对比

目前，Agent Sandbox 领域涌现了多个有影响力的开源项目。以下重点介绍三个代表性方案。

### 4.1 AIO Sandbox（agent-infra/sandbox）

**定位：All-in-One 应用层沙箱**

AIO Sandbox 的核心理念是"一个容器搞定一切"。它将浏览器（VNC + CDP）、Shell 终端、文件系统、VSCode Server、Jupyter Notebook 和 MCP Server 集成在一个 Docker 容器中，所有组件共享同一个文件系统。

```bash
# 30秒启动一个完整的 Agent 执行环境
docker run --security-opt seccomp=unconfined \
  --rm -it -p 8080:8080 \
  ghcr.io/agent-infra/sandbox:latest
```

启动后可以直接访问多个端点：API 文档（`/v1/docs`）、VNC 浏览器（`/vnc/`）、VSCode Server（`/code-server/`）、MCP 服务（`/mcp`）。

AIO Sandbox 提供了 Python、TypeScript 和 Golang 三种语言的 SDK，并且内置了 LangChain 和 OpenAI Assistant 的集成示例。对于快速搭建 Agent 原型来说，它是上手最快的选择。

**适合场景**：快速原型验证、需要浏览器自动化的 Agent、All-in-One 开发环境。

**技术栈**：Python 55%、TypeScript 38%，Apache 2.0 协议，4.5k stars。

### 4.2 OpenSandbox（alibaba/OpenSandbox）

**定位：通用沙箱平台**

OpenSandbox 是阿里巴巴开源的通用 AI 沙箱平台，已被纳入 CNCF Landscape。相比 AIO Sandbox 的"开箱即用"，OpenSandbox 更强调**平台化和可扩展性**。

它的核心设计哲学是**协议先行**——定义了一套 Sandbox Protocol（OpenAPI 规范），包括沙箱生命周期管理 API 和沙箱执行 API。任何人都可以基于这套协议实现自己的沙箱运行时。

OpenSandbox 提供了所有主流语言的 SDK：Python、Java/Kotlin、JavaScript/TypeScript、C#/.NET、Go，覆盖面非常广。它支持 Docker 和 Kubernetes 两种运行时，特别是其高性能 Kubernetes 运行时，适合大规模分布式调度场景。

在安全方面，OpenSandbox 的能力最为全面：统一的 Ingress Gateway 支持多种路由策略，per-sandbox 的 Egress Controls 可以精细化管控每个沙箱的网络出入，还支持 gVisor、Kata Containers 和 Firecracker 等安全容器运行时。

它还引入了 OSEP（OpenSandbox Enhancement Proposals）机制来管理协议演进，体现了其面向生态的开放治理理念。

**适合场景**：企业级部署、多语言团队、大规模分布式 Agent 调度、需要严格安全隔离的场景。

**技术栈**：Python 42%、Go 33%、Kotlin/Java/C#/TypeScript 多语言，Apache 2.0 协议，10.3k stars。

### 4.3 CubeSandbox（TencentCloud/CubeSandbox）

**定位：高性能 MicroVM 沙箱**

CubeSandbox 是腾讯云开源的 Agent 沙箱方案。它与前两者最大的区别在于**隔离层级**——CubeSandbox 不依赖容器，而是基于 KVM MicroVM 虚拟化技术，为每个沙箱创建一个真正独立的虚拟机。

其架构由多个精心设计的组件构成：CubeAPI（Rust 实现的高并发 REST 网关）、CubeMaster（集群编排器）、Cubelet（节点级生命周期管理）、CubeProxy（反向代理）、CubeVS（基于 eBPF 的虚拟交换机）、CubeHypervisor & CubeShim（虚拟化层）。

CubeSandbox 的一个独特策略是**兼容 E2B SDK**。E2B 是目前 Agent Sandbox 领域使用最广泛的 SDK 之一，CubeSandbox 实现了与其 API 的兼容，用户只需要替换 URL 就能从 E2B 无缝迁移：

```python
import os
from e2b_code_interpreter import Sandbox  # 直接使用 E2B SDK

# CubeSandbox 透明拦截所有请求
with Sandbox.create(template=os.environ["CUBE_TEMPLATE_ID"]) as sandbox:
    result = sandbox.run_code("print('Hello from Cube Sandbox!')")
    print(result)
```

CubeSandbox 还引入了**模板机制**——用户可以从 Docker 镜像创建沙箱模板，后续所有沙箱实例都基于模板快照快速启动。这大幅缩短了启动时间，特别适合需要高并发创建大量沙箱的场景。

**适合场景**：对安全隔离要求极高的场景、高并发沙箱调度、从 E2B 迁移的用户、RL Training。

**技术栈**：Rust 52%、Go 26%、C 18%，Apache 2.0 协议，4.5k stars。

### 4.4 横向对比

| 维度 | AIO Sandbox | OpenSandbox | CubeSandbox |
|------|-------------|-------------|-------------|
| **隔离方式** | Docker 容器 | Docker / K8s + 安全容器 | KVM MicroVM |
| **定位** | All-in-One 应用层 | 通用平台 | 高性能基础设施 |
| **SDK 语言** | Python, TS, Go | Python, Java, TS, C#, Go | E2B 兼容 |
| **浏览器支持** | VNC + CDP + MCP | 示例提供 | 示例提供 |
| **MCP 支持** | 内置 | MCP SDK | - |
| **K8s 原生** | 否 | 是 | 自建编排（CubeMaster） |
| **网络策略** | 基础 | Ingress + Egress 精细控制 | eBPF 虚拟交换机 |
| **上手难度** | 低（一行 docker run） | 中等 | 较高（需裸机 / VM） |

三个项目各有侧重，并不构成直接的替代关系。如果你需要快速搭建一个 Agent demo，AIO Sandbox 的一行启动命令最为友好。如果你在规划企业级的 Agent 基础设施，OpenSandbox 的平台化设计和多语言 SDK 会更合适。如果你对安全隔离有极致要求，或者需要在高并发场景下运行大量沙箱实例，CubeSandbox 的 MicroVM 方案是最强选择。

---

## 五、Sandbox 与 Harness 的关系

回到更宏观的视角，Sandbox 在 Agent Harness 体系中扮演什么角色？

在之前讨论的六维框架（Prompt + Context + Skills + Orchestration + MCP/Tools + Data & Memory）中，Sandbox 横跨了 **Tools** 和 **Orchestration** 两个维度。从 Tools 的角度看，Sandbox 是 Agent 最核心的执行工具之一——它赋予了 Agent "动手"的能力。从 Orchestration 的角度看，Sandbox 是 Harness 实现"环境约束型"控制的关键基础设施——通过隔离执行环境，Harness 可以在不限制 Agent 能力的前提下，确保操作的安全性。

更深层地看，Sandbox 体现了 Harness Engineering 的一个核心原则：**与其相信 Agent 不会犯错，不如让犯错的代价可控**。沙箱不是为了防止 Agent 犯错（那是模型和 Prompt 的事），而是为了确保即使 Agent 犯了错，损失也被限定在一个可接受的范围内。

---

## 六、结语

Agent Sandbox 正在经历快速的生态分化。从 AIO Sandbox 的 All-in-One 便捷方案，到 OpenSandbox 的平台化标准体系，再到 CubeSandbox 的 MicroVM 极致隔离，不同的方案在便捷性、可扩展性和安全性之间各做了不同的取舍。

对于 Agent 开发者来说，选择合适的 Sandbox 方案，和选择合适的模型一样重要。因为 Agent 的可靠性，不仅取决于它的"大脑"有多聪明，更取决于它的"手脚"是否被妥善地约束和保护。
