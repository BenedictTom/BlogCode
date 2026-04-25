---
title: Claude Code Skill 开发指南
date: 2026-03-29 12:34:16
tags: [Agent]
categories: [Agent]
cover: https://picx.zhimg.com/70/v2-602aaee33c31e7fde8d335ede217493a_1440w.avis?source=172ae18b&biz_tag=Post
---

## 什么是 Claude Code Skill？

Claude Code Skill 是 Claude Code 中的一种可自定义的技能系统，它允许用户将复杂的工作流程封装成简单的命令。通过创建 skill，你可以让 Claude 自动执行重复性任务、遵循特定的工作流程，或者实现定制化的功能。

想象一下，如果你每天都有一个固定的工作流程：创建文件 → 编辑内容 → 运行测试 → 提交代码。如果每次都要手动告诉 Claude 每一步该怎么做，是不是很麻烦？有了 Skill 系统，你只需要说一句 `/my-skill`，Claude 就会自动按照你预设的流程执行所有步骤。

### Skill 的核心价值

<div align="center">

| 价值 | 说明 | 实际收益 |
|------|------|----------|
| **自动化重复任务** | 将日常固定流程封装成一键执行的命令 | 每天节省 30+ 分钟 |
| **标准化工作流程** | 确保每次执行任务时都遵循最佳实践 | 减少人为失误 |
| **知识沉淀** | 将个人经验和团队规范固化到技能中 | 新人快速上手 |
| **提升效率** | 减少重复说明，一次配置，多次复用 | 专注创造性工作 |

</div>

### 使用场景示例

以下是一些典型的使用场景：

1. **博客作者**：`/blog-deploy 文章标题` → 自动创建文章、提醒添加图片、部署到 GitHub
2. **开发人员**：`/code-review` → 对当前修改的代码进行全面审查
3. **数据分析师**：`/analyze-data` → 加载指定数据文件，生成可视化报告
4. **DevOps 工程师**：`/deploy-staging` → 执行完整的测试和部署流程

## Skill 的基本结构

一个 skill 由以下几个部分组成：

```
skill-name/
├── SKILL.md (必需)
│   ├── YAML frontmatter (name, description)
│   └── Markdown 指令
└── Bundled Resources (可选)
    ├── scripts/          - 可执行代码（Python/Shell 脚本等）
    ├── references/       - 参考文档（按领域组织的指南）
    └── assets/           - 模板、图标等资源文件
```

### 目录结构详解

```
.claude/skills/
├── blog-deploy/
│   └── SKILL.md              # 博客发布技能
├── code-reviewer/
│   ├── SKILL.md              # 代码审查技能
│   ├── scripts/
│   │   ├── lint.py           # 代码检查脚本
│   │   └── security_check.sh # 安全检查脚本
│   └── references/
│       ├── python_style.md   # Python 风格指南
│       └── security_rules.md # 安全规则
└── project-init/
    ├── SKILL.md
    └── assets/
        └── template.zip      # 项目模板
```

### YAML Frontmatter

每个 SKILL.md 文件都必须包含 YAML frontmatter，定义 skill 的基本信息：

```yaml
---
name: skill-name                    # 技能标识符，用于命令调用
description: 技能描述，这是触发技能的主要机制  # 触发机制和场景说明
---
```

**description 的重要性**：这是 Claude 决定是否使用该技能的关键。描述应该：
- ✅ 明确说明技能做什么
- ✅ 列出触发场景（何时使用）
- ✅ 稍微"pushy"一些，避免 Claude 不主动使用

#### 好的 description 示例

```yaml
# ❌ 不够好 - 太简单
description: 创建一个博客文章

# ✅ 好 - 包含触发场景
description: 一键完成 Hexo 博客发布流程：创建新文章 → 提醒添加图片 → 清理并部署到 GitHub。
当用户想要写博客、发布文章、部署博客时都要使用此技能。

# ✅ 更好 - 详细且 pushy
description: 代码审查助手。当用户提交代码、请求审查、提到"帮我看看这段代码"、"检查 bug"、
"性能优化"等场景时都要使用此技能。包括代码质量评估、安全漏洞检查、性能优化建议。
```

## 创建一个 Skill

### 第一步：明确需求

在开始之前，先问自己几个问题：

1. **这个技能要完成什么任务？** - 具体的输入和输出
2. **什么情况下应该触发这个技能？** - 用户会说什么话
3. **期望的工作流程是什么？** - 步骤 1、2、3...
4. **有哪些边界情况需要考虑？** - 错误处理、特殊场景

### 第二步：编写 SKILL.md

下面是一个完整的示例，展示了一个博客发布 skill 的编写：

```markdown
---
name: blog-deploy
description: 一键完成 Hexo 博客发布流程：创建新文章 → 提醒添加图片 → 清理并部署到 GitHub。
当用户想要写博客、发布文章、部署博客时都要使用此技能。
---

# Hexo 博客发布流程

## 使用方法

**语法：** `/blog-deploy <文章标题>`

**示例：**
- `/blog-deploy 今天的学习笔记`
- `/blog-deploy Spring Boot 实战教程`

## 流程说明

### 步骤 1: 创建新文章
执行命令创建新文章：
```bash
hexo new post "<文章标题>"
```
告知用户文章已创建，路径为 `source/_posts/<文章标题>.md`

### 步骤 2: 提醒添加图片
提醒用户：
- 从网上找合适的图片并添加到文章中
- 完善文章内容和格式
- 可以添加 tags、categories 等 front-matter 信息

### 步骤 3: 等待用户编辑
**重要**：必须得到用户明确确认后才能继续下一步。
询问："你是否已完成文章编辑？确认后我将执行部署。"

### 步骤 4: 清理并部署
用户确认完成后，执行：
```bash
hexo clean && hexo deploy
```

### 步骤 5: 完成
告知用户部署已完成，博客已推送到 GitHub Pages。

## 注意事项
- 确保在博客项目根目录下执行
- 确保已配置好 GitHub SSH key
- 确保已在 `_config.yml` 中配置好 deploy 信息
```

### 编写技巧

1. **使用祈使句**：清晰直接地表达指令
   - ✅ "执行 `hexo new post` 创建文章"
   - ❌ "你可以考虑执行..."

2. **解释原因**：不仅告诉 Claude 做什么，还要说明为什么
   - ✅ "必须得到用户确认，因为用户可能需要时间编辑内容"
   - ❌ "必须得到用户确认"

3. **避免过度约束**：用"为什么"代替大量的"必须/禁止"
   - ✅ "用户可能需要尝试不同的命令，保持灵活性"
   - ❌ "NEVER 执行其他命令"

4. **保持简洁**：SKILL.md 最好控制在 500 行以内，复杂内容放到 reference 文件

## Skill 开发工作流

创建一个成熟的 skill 通常需要多次迭代：

```
┌─────────────┐
│ 明确需求    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 编写初稿    │
└──────┬──────┘
       │
       ▼
┌─────────────┐     测试不通过
│ 测试运行    │────────────┐
└──────┬──────┘            │
       │                   │
       │ 测试通过          │
       ▼                   │
┌─────────────┐            │
│ 收集反馈    │            │
└──────┬──────┘            │
       │                   │
       ▼                   │
┌─────────────┐            │
│ 改进优化    │────────────┘
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 完成发布    │
└─────────────┘
```

### 测试你的 Skill

编写完成后，创建 2-3 个真实的测试用例：

```json
{
  "skill_name": "blog-deploy",
  "evals": [
    {
      "id": 1,
      "prompt": "/blog-deploy 今天的学习笔记",
      "expected_output": "创建文章并引导用户完成部署流程"
    },
    {
      "id": 2,
      "prompt": "/blog-deploy React Hooks 详解",
      "expected_output": "正确创建技术类文章，包含 tags 建议"
    },
    {
      "id": 3,
      "prompt": "帮我发布一篇博客，题目是'机器学习入门'",
      "expected_output": "即使没有使用/命令，也能触发技能并正确执行"
    }
  ]
}
```

## 实用案例

### 案例 1：博客发布自动化

这是我们刚才创建的 skill，它将每天写博客的固定流程封装起来：

```yaml
# .claude/skills/blog-deploy/SKILL.md
---
name: blog-deploy
description: 一键完成 Hexo 博客发布流程：创建新文章 → 提醒添加图片 → 清理并部署到 GitHub。
当用户想要写博客、发布文章、部署博客时都要使用此技能。
---
```

**使用效果：**
```
用户：/blog-deploy 今天的学习笔记

AI: ✅ 文章已创建：source/_posts/今天的学习笔记.md

💡 提醒：
- 从网上找合适的图片添加到文章中
- 完善文章内容和格式

完成后请告诉我，我会执行部署操作。

[用户编辑完成后]

用户：已完成

AI: 正在执行 hexo clean && hexo deploy...

✅ 部署完成！博客已推送到 GitHub Pages
```

### 案例 2：代码审查助手

```markdown
---
name: code-reviewer
description: 对提交的代码进行全面审查，包括代码质量、性能优化、安全漏洞检查。
当用户提交代码、请求审查、提到"帮我看看这段代码"、"检查 bug"、"性能优化"等场景时都要使用此技能。
---

# 代码审查清单

## 审查维度

### 1. 代码质量
- [ ] 命名是否清晰、一致
- [ ] 函数是否单一职责
- [ ] 代码重复是否可以消除
- [ ] 注释是否恰当（解释为什么，而不是做什么）

### 2. 性能优化
- [ ] 是否存在 N+1 查询问题
- [ ] 循环中是否有不必要的计算
- [ ] 数据结构选择是否合理
- [ ] 内存使用是否高效

### 3. 安全漏洞
- [ ] SQL 注入风险
- [ ] XSS 攻击风险
- [ ] 输入验证是否完善
- [ ] 敏感信息是否泄露

### 4. 错误处理
- [ ] 异常是否被正确捕获
- [ ] 错误信息是否清晰
- [ ] 是否有合适的回滚机制

## 输出格式

审查完成后，按以下格式输出：

```
## 审查结果

### ✅ 做得好的地方
1. ...

### ⚠️ 需要改进的地方
1. ...

### 🚨 严重问题
1. ...

### 建议修改
```diff
- 原代码
+ 修改后
```
```
```

### 案例 3：项目初始化助手

```markdown
---
name: project-init
description: 帮助快速初始化新项目，包括配置依赖、创建目录结构、设置 CI/CD。
当用户提到"新建项目"、"初始化项目"、"创建脚手架"、"setup project"时都要使用此技能。
---

# 项目初始化流程

## 支持的框架

| 框架 | 命令 | 配置说明 |
|------|------|----------|
| Spring Boot | `spring init` | JDK 17+, Maven |
| React | `create-react-app` | TypeScript, Tailwind |
| Vue | `npm create vue@latest` | TypeScript, Pinia |
| Next.js | `npx create-next-app` | TypeScript, Tailwind |
| Express | `express-generator` | TypeScript, ESLint |

## 初始化步骤

### 1. 确认项目信息
询问用户：
- 项目名称
- 框架选择
- 是否需要 CI/CD 配置

### 2. 执行初始化命令
根据框架执行对应的初始化命令

### 3. 配置开发环境
- 安装依赖
- 配置 ESLint/Prettier
- 设置 Git hooks

### 4. 创建基础文件
- README.md
- .env.example
- docker-compose.yml (可选)
```

## 最佳实践

### 1. 渐进式披露

利用 skill 的三级加载系统，让 skill 保持简洁：

| 层级 | 内容 | 大小限制 | 何时加载 |
|------|------|----------|----------|
| Metadata | name + description | ~100 词 | 始终在上下文 |
| SKILL.md 主体 | 核心指令 | <500 行 | 技能触发时 |
| Bundled resources | 详细文档、脚本 | 无限制 | 按需加载 |

**示例：**
```markdown
# 主 SKILL.md（简洁）
## 代码审查
按照以下维度审查代码：
1. 代码质量 - 见 references/code_quality.md
2. 性能优化 - 见 references/performance.md
3. 安全检查 - 见 references/security.md

# references/security.md（详细）
## 安全检查清单
### SQL 注入
- 检查所有数据库查询是否使用参数化
- 检查 ORM 使用是否正确
...
```

### 2. 领域组织

当 skill 支持多个框架时，按领域组织参考文件：

```
cloud-deploy/
├── SKILL.md              # 工作流程 + 框架选择指南
└── references/
    ├── selection.md      # 如何选择合适的云服务
    ├── aws.md            # AWS 部署指南
    ├── gcp.md            # GCP 部署指南
    └── azure.md          # Azure 部署指南
```

**SKILL.md 中的引用方式：**
```markdown
## 选择云服务
- AWS: 功能最全，适合大型企业 - 详见 references/aws.md
- GCP: AI/ML 能力强 - 详见 references/gcp.md
- Azure: 与微软生态集成好 - 详见 references/azure.md
```

### 3. 测试与迭代

有效的测试策略：

- ✅ 编写初稿后立即测试
- ✅ 使用真实的用户语言（不是"测试用例"式的语言）
- ✅ 收集用户反馈
- ✅ 关注失败案例
- ✅ 持续优化描述和流程

**测试用例语言对比：**
```
❌ 测试用例：执行博客发布流程
✅ 测试用例：我每天都要写博客然后找图再部署，能不能一键搞定

❌ 测试用例：审查代码
✅ 测试用例：刚写了个新功能，帮我看下有没有什么问题
```

### 4. 脚本化重复操作

如果在多个测试案例中都发现 Claude 独立编写相似的脚本，这应该被打包到 skill 中：

```
my-skill/
├── SKILL.md
└── scripts/
    ├── generate_report.py    # 生成报告脚本
    ├── format_data.sh        # 数据格式化脚本
    └── deploy.sh             # 部署脚本
```

**在 SKILL.md 中引用脚本：**
```markdown
## 生成报告
执行脚本生成报告：
```bash
python scripts/generate_report.py --input "$DATA_FILE" --output report.md
```

脚本会自动：
1. 读取输入数据
2. 生成可视化图表
3. 输出 Markdown 报告
```

## 高级功能

### 描述优化

skill 的触发机制依赖于 description 字段。可以使用官方提供的优化脚本来提升触发准确率：

**步骤 1：生成测试查询**
创建 20 个测试查询（包含应该触发和不应该触发的场景）：

```json
[
  {"query": "/blog-deploy 学习笔记", "should_trigger": true},
  {"query": "帮我发布博客", "should_trigger": true},
  {"query": "写一篇文章", "should_trigger": true},
  {"query": "hexo 怎么部署", "should_trigger": true},
  {"query": "读取这个文件", "should_trigger": false},
  {"query": "git commit 怎么写", "should_trigger": false}
]
```

**步骤 2：运行优化循环**
```bash
python -m scripts.run_loop \
  --eval-set eval_set.json \
  --skill-path path/to/skill \
  --model claude-sonnet-4-6 \
  --max-iterations 5
```

这个过程会：
1. 评估当前 description 的触发率
2. 分析失败案例
3. 生成改进的 description
4. 重新评估，迭代 5 次
5. 输出最优 description

### 打包分享

创建完成后，可以将 skill 打包成 `.skill` 文件分享给他人：

```bash
python -m scripts.package_skill path/to/skill-folder
```

打包后会生成一个 `.skill` 文件，可以：
- 通过邮件分享给同事
- 发布到内部知识库
- 上传到技能市场

**安装 .skill 文件：**
```bash
# 在 Claude Code 中
/import path/to/skill.skill
```

## 常见问题 FAQ

### Q: Skill 不触发怎么办？

**A:** 检查以下几点：
1. description 是否足够详细和具体
2. 用户的请求是否过于简单（简单请求可能不会触发技能）
3. 尝试在 description 中添加更多触发场景

### Q: Skill 执行流程不对怎么办？

**A:**
1. 检查 SKILL.md 中的指令是否清晰
2. 添加更多"为什么"的解释
3. 减少过度约束的"必须/禁止"

### Q: 如何调试 Skill？

**A:**
1. 使用 `/skill-debug` 命令（如果有）
2. 查看技能执行的日志
3. 添加测试用例并运行

### Q: 可以在技能中使用外部工具吗？

**A:** 可以！skill 可以：
- 执行 Shell 命令
- 运行 Python/Node.js 脚本
- 调用 MCP 服务器
- 使用 HTTP 请求

## 总结

Claude Code Skill 是一个强大的工具，可以帮助你将重复性工作自动化，建立标准化的工作流程。

### 关键要点回顾

1. **明确需求**：先想清楚技能要解决什么问题
2. **写好 description**：这是触发的关键，要详细且"pushy"
3. **解释为什么**：让 AI 理解意图，不只是执行命令
4. **持续迭代**：通过测试和反馈不断改进
5. **脚本化**：把重复的代码打包成脚本

### 开始你的第一个 Skill

从你最常做的重复性任务开始：
1. 记录你每天都要说的重复指令
2. 思考如何把它们封装成一个流程
3. 编写 SKILL.md
4. 测试、改进、完成！

---

## 参考资源

- [Claude Code 官方文档](https://claude.ai/code)
- [GitHub - anthropics/claude-code](https://github.com/anthropics/claude-code)
- [Skill Creator 源码](https://www.paicoding.com/article/detail/2608333775943683)
- [MCP 协议文档](https://modelcontextprotocol.io/)

---
