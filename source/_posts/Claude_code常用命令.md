---
title: Claude Code 常用命令
date: 2026-03-29 12:34:16
tags: [Claude Code, AI, 效率工具]
categories: [VibeCoding]
cover: https://picx.zhimg.com/70/v2-602aaee33c31e7fde8d335ede217493a_1440w.avis?source=172ae18b&biz_tag=Post
---

## 一、基础命令（最常用）

### 1. 项目初始化

```bash
/init
```
初始化项目，让 Claude 分析当前代码库结构，建立对项目的整体认知。适合刚进入一个新项目时使用。

### 2. 文件操作

| 命令 | 说明 |
|------|------|
| `/init` | 初始化项目，分析代码结构 |
| `/read <file>` | 读取文件内容 |
| `/edit <file>` | 编辑文件 |
| `/write <file>` | 创建新文件 |
| `/glob <pattern>` | 按模式搜索文件 |
| `/grep <pattern>` | 搜索文件内容 |

### 3. 代码审查

```bash
/review
```
对代码变更进行审查，检查代码质量、潜在问题和改进建议。

```bash
/simplify
```
审查代码是否存在重复、冗余，优化代码质量和结构。

---

## 二、上下文与记忆命令

### 1. 上下文管理

```bash
/context
```
管理会话上下文，查看当前对话中保留的上下文信息。

```bash
/btw
```
添加背景信息或补充说明，帮助 Claude 更好理解你的需求和上下文。

### 2. Memory 系统

```bash
/memory
```
持久化存储重要信息，分为四种类型：

- **user**：用户的角色、偏好、知识背景
- **feedback**：用户对工作方式的评价和反馈
- **project**：项目目标、进展、决策记录
- **reference**：外部资源的引用位置

**示例：**
```
/memory save user "我是一名数据科学家，偏好 Python 和 Jupyter"
/memory save feedback "测试要用真实数据库，不要用 mock"
/memory save project "Q2 目标：完成用户模块重构"
/memory save reference "bug 追踪：Linear 项目'INGEST'"
```

---

## 三、任务管理命令

### 1. Todo 列表

```bash
/todo
```
创建和管理任务列表，跟踪多步骤任务的进度。

**常用操作：**
```bash
/todo add "修复登录 bug"
/todo list          # 查看所有任务
/todo complete 1    # 完成任务 ID 为 1 的任务
```

### 2. 计划模式

```bash
/plan
```
进入计划模式，用于设计复杂功能的实现方案。在开始写代码前，先输出实现步骤、文件结构和架构考虑。

---

## 四、分支与版本控制

### 1. Branch 管理

```bash
/branch
```
管理 Git 分支，支持创建、切换、合并分支等操作。

**常用操作：**
```bash
/branch create feature/new-auth
/branch switch main
/branch list
```

### 2. 提交与推送

```bash
/commit
```
创建 git 提交，自动分析变更内容生成提交信息。

**带参数提交：**
```bash
/commit -m "fix: 修复用户登录时的空指针异常"
```

### 3. Pull Request

```bash
/pr
```
创建和管理 GitHub Pull Request。

**常用操作：**
```bash
/pr create          # 创建新 PR
/pr list            # 查看 PR 列表
/pr view <number>   # 查看指定 PR
```

---

## 五、Agent 命令（高级）

### 1. 启动子代理

```bash
/agent <description>
```
启动一个专门的子代理来处理复杂任务。支持多种子代理类型：

| 子代理类型 | 用途 |
|-----------|------|
| `general-purpose` | 通用代理，处理复杂多步骤任务 |
| `Explore` | 探索代码库，搜索文件和代码 |
| `Plan` | 软件架构师，设计实现方案 |
| `code-reviewer` | 代码审查专家 |

**示例：**
```bash
/agent "搜索所有 API 端点并整理文档"
/agent type:Explore "找出所有使用 React Query 的地方"
/agent type:Plan "设计用户认证系统的重构方案"
```

### 2. 后台任务

```bash
/agent --background <description>
```
在后台运行代理任务，不阻塞当前对话。

---

## 六、分析与洞察命令

### 1. Insights 分析

```bash
/insights
```
生成项目洞察报告，分析代码质量、架构问题、技术债务等。

### 2. 测试与验证

```bash
/test
```
运行测试套件，验证代码变更。

```bash
/lint
```
运行代码检查工具，发现代码风格和问题。

---

## 七、技能（Skills）命令

### 1. 技能调用

```bash
/<skill-name>
```
调用已安装的技能来执行特定任务。

**可用技能示例：**
- `/blog-deploy <标题>` - Hexo 博客发布流程
- `/skill-creator` - 创建和优化技能
- `/loop` - 定时重复任务

### 2. 技能创建

```bash
/skill-creator
```
创建新技能或优化现有技能，包含完整的测试和评估流程。

---

## 八、循环与定时任务

### 1. Loop 循环

```bash
/loop <interval> <command>
```
按指定间隔重复执行命令。

**示例：**
```bash
/loop 5m "检查部署状态"
/loop 10m /test  # 每 10 分钟运行测试
```

### 2. Cron 定时任务

```bash
/cron
```
管理定时任务，支持标准 cron 表达式。

**示例：**
```bash
/cron create "0 9 * * *" "运行晨间检查"
/cron list
/cron delete <job-id>
```

---

## 九、工作区（Worktree）命令

```bash
/worktree
```
创建隔离的 Git 工作区，用于并行开发多个功能。

**常用操作：**
```bash
/worktree create feature-branch
/worktree enter <name>
/worktree exit --keep    # 退出并保留
/worktree exit --remove  # 退出并删除
```

---

## 十、其他实用命令

### 1. 帮助与设置

```bash
/help
```
获取帮助信息。

```bash
/settings
```
查看和修改 Claude Code 设置。

### 2. 对话管理

```bash
/clear
```
清除当前对话历史。

```bash
/restore
```
恢复之前的对话会话。

### 3. 唤醒调度

```bash
/schedule
```
安排在特定时间执行任务。

```bash
/schedule 300 "检查构建结果"  # 5 分钟后执行
```

---

## 十一、进阶命令

### 1. 代码执行

```bash
/bash <command>
```
执行 shell 命令。

```bash
/python <code>
```
直接执行 Python 代码片段。

### 2. 差异与补丁

```bash
/diff
```
查看代码变更差异。

```bash
/patch
```
应用代码补丁。

### 3. 询问与解释

```bash
/ask <question>
```
向 Claude 提问。

```bash
/explain
```
解释代码或概念。

### 4. 搜索与发现

```bash
/find <pattern>
```
查找文件或内容。

```bash
/tree
```
显示目录树结构。

### 5. 模式切换

```bash
/vibe
```
进入 Vibe 模式，更自由的对话风格。

```bash
/planmode
```
进入计划模式（同 `/plan`）。

### 6. MCP 服务

```bash
/mcp
```
管理 MCP（Model Context Protocol）服务，连接外部工具和 API。

### 7. 钩子（Hooks）

```bash
/hooks
```
管理钩子配置，设置自动化触发器。

### 8. 键盘快捷键

```bash
/keys
```
查看和配置键盘快捷键。

---

## 十二、快捷键速查

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+C` | 中断当前操作 |
| `Ctrl+D` | 退出 Claude Code |
| `Ctrl+L` | 清屏 |
| `Ctrl+R` | 重新运行上一个命令 |
| `Tab` | 自动补全命令 |
| `Shift+Tab` | 显示补全建议 |
| `Up/Down` | 浏览命令历史 |

---

## 快速参考表

| 类别 | 命令 | 使用频率 |
|------|------|----------|
| 基础 | `/init`, `/read`, `/edit`, `/bash` | ⭐⭐⭐⭐⭐ |
| 审查 | `/review`, `/simplify`, `/diff` | ⭐⭐⭐⭐ |
| 上下文 | `/context`, `/btw`, `/memory` | ⭐⭐⭐⭐ |
| 任务 | `/todo`, `/plan` | ⭐⭐⭐ |
| Git | `/branch`, `/commit`, `/pr` | ⭐⭐⭐⭐ |
| Agent | `/agent` | ⭐⭐⭐ |
| 技能 | `/<skill-name>` | ⭐⭐⭐ |
| 定时 | `/loop`, `/cron`, `/schedule` | ⭐⭐ |
| 查询 | `/ask`, `/explain`, `/grep`, `/find` | ⭐⭐⭐⭐ |
| 执行 | `/python`, `/bash` | ⭐⭐⭐ |
| 配置 | `/settings`, `/hooks`, `/mcp`, `/keys` | ⭐⭐ |

---

## 最佳实践

1. **项目开始**：先用 `/init` 让 Claude 了解项目结构
2. **复杂任务**：用 `/todo` 拆解任务，用 `/plan` 设计方案
3. **代码提交**：定期用 `/review` 和 `/simplify` 保证代码质量
4. **重要信息**：用 `/memory` 保存需要跨会话的信息
5. **并行工作**：用 `/worktree` 隔离不同功能的开发
6. **自动化**：用 `/loop` 和 `/cron` 设置定期检查


