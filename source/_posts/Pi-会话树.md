---
title: Pi 的会话树：一条对话为什么不是一条线
date: 2026-11-05 00:40:00
categories:
  - Pi
tags:
  - Pi
  - Agent
  - Session
  - JSONL
cover: /images/Pi-会话树/cover.png
description: 拆开 Pi 的会话存储：为什么一条对话被存成一棵 append-only 的树，leafId 是什么，压缩和回退怎么在树上"切一刀"而不删东西。
---

上一篇跟完了一次请求在 Pi 里的完整路径。这一篇往下一层：那些消息到底被存在哪儿、以什么形状存的。

如果你写过玩具 agent，答案大概是一个数组：`messages.push(...)`，存盘就是 `JSON.stringify(messages)`。Pi 不是。它把一条对话存成了**一棵树**，而且这个文件永远只追加、从不修改。

这不是为了炫技。九个功能里有六个是被"树"这个形状直接送出来的——回退、重试、分叉、压缩、切换模型、改一条旧消息。换成数组，每一个都要单独打补丁。

## 0. 先说结论

三句话：

1. 会话文件是一行一个 JSON 的 JSONL，每行是一个 **entry**，entry 自带 `id` 和 `parentId`。
2. 树的结构完全由 `parentId` 决定，另外只有一个叫 `leafId` 的指针表示"我现在站在这棵树的哪个节点上"。
3. 每次要发给模型之前，从 `leafId` 往上走到根，把这条路投影成消息数组——**路径就是上下文**。

就这三条。下面全部是它的推论。

## 1. 一条线的三个坏处

先把"为什么不能是数组"讲清楚，否则树看起来很无理。

**坏处一：回退只能截断。** 数组里你想退回到第 5 条消息，只能把这之后的全删掉。可用户往往只是"这条支线试错了，我想回到分叉点换个说法"——被删掉的那段其实有价值，删了就是真丢了。

**坏处二：重试要在原地改。** 模型答得不好，想让它重答。数组方案里你要么覆盖最后一条（那就丢了原答案），要么在中间插一条（那后面所有消息的位置都变了）。而磁盘上的文件是追加写的，改中间一行的代价是重写整个文件。

**坏处三：压缩没有位置感。** 上下文快满了，要压掉前 30 条。压完之后，那 30 条原始记录还要不要留？数组方案里它们只能被替换掉——于是"压缩"和"删历史"变成同一件事。

这三个坏处有同一个根源：**一条线只能表达"顺序"，表达不了"分叉"和"覆盖"**。而 agent 的日常操作恰恰全是分叉和覆盖。

## 2. 换一张数据结构

Pi 的选择是把"顺序"降级成"指针"：

```jsonl
{"type":"session","version":3,"id":"0199...","timestamp":"...","cwd":"/Users/me/proj"}
{"type":"message","id":"a1","parentId":null,"timestamp":"...","message":{...}}
{"type":"message","id":"a2","parentId":"a1","timestamp":"...","message":{...}}
{"type":"message","id":"a3","parentId":"a2","timestamp":"...","message":{...}}
```

第一行是文件头 `SessionHeader`（`session-manager.ts:35-43`），里面有 `cwd`、`version`、可选的 `parentSession`。之后每行是一个 `SessionEntry`，公共字段只有四个（`session-manager.ts:49-54`）：

- `type`：这一条是什么
- `id`：自己的 id
- `parentId`：上一条是谁（`null` 表示根）
- `timestamp`

**顺序信息在哪？** 在文件里的物理行序里，也在 `parentId` 链里。二者平时一致，一旦你回退，它们就不一致了——后面追加的 entry 的 `parentId` 会指向旧节点，物理上却排在文件末尾。这就是树能"长"出来的原因：**追加写 + 指回去**。

{% mermaid %}
flowchart LR
  subgraph lin["线性（数组）"]
    L1["msg1"] --> L2["msg2"] --> L3["msg3"] --> L4["msg4"]
    L3 -. 回退只能截断 .-> L2
  end
  subgraph tree["树（append-only）"]
    T1["msg1"] --> T2["msg2"]
    T2 --> T3a["msg3（旧）"]
    T2 --> T3b["msg3（重试）"]
    T3a --> T4a["msg4a"]
    T3b --> T4b["msg4b"]
    T3a -. 回退时挂一页摘要 .-> S["branch_summary"]
  end
{% endmermaid %}

这个设计有个立刻能感受到的好处：**所有操作都退化成"追加一行"**。回退是追加、压缩是追加、改一条旧消息也是追加。文件永远只往长了长，不存在"写坏一半"的问题，崩溃时最多丢掉最后半行（读取时坏行会被跳过，`session-manager.ts:675` 的注释写得很直白：`Blank and malformed lines are skipped`）。

## 3. entry 不只是消息

第二个反直觉的地方：会话文件里存的不只是"消息"。

`SessionEntry` 是个联合类型，一共 11 种（`session-manager.ts` 的 `SessionEntry` 定义）：

| type | 它表示什么 |
| --- | --- |
| `message` | 一条真正的消息（user / assistant / toolResult） |
| `thinking_level_change` | 思考档位被改成了 `high` |
| `model_change` | 换了一个模型 |
| `usage` | 一次请求的用量与花费 |
| `compaction` | 一次上下文压缩的结果 |
| `branch_summary` | 一段被放弃支线的摘要 |
| `custom` | 扩展存的自定义状态（只是状态，不进上下文） |
| `custom_message` | 扩展注入的一条消息（进上下文） |
| `context_edit` | 对某条旧消息的"改写声明" |
| `label` | 给某个节点起个名字 |
| `session_info` | 会话级别的元信息（比如标题） |

为什么要这么细？因为**在 Pi 里，"发生了什么"和"模型看到了什么"是两件事**。

举个例子：你中途把模型从 `claude` 换到 `deepseek`。数组方案里这条信息无处安放，只能写进某条消息的文本里（很多 agent 真的这么干过，于是模型会看到"用户说：请从现在起用另一个模型"这种假消息）。Pi 里它是一条 `model_change` 节点，落在树上，投影的时候被"读"成当前状态：

```ts
function getSessionContextSettings(path: SessionEntry[]) {
  let thinkingLevel = "off";
  let model = null;
  for (const entry of path) {
    if (entry.type === "thinking_level_change") thinkingLevel = entry.thinkingLevel;
    else if (entry.type === "model_change") model = { provider: entry.provider, modelId: entry.modelId };
    else if (entry.type === "message" && entry.message.role === "assistant") {
      model = { provider: entry.message.provider, modelId: entry.message.model };
    }
  }
  return { thinkingLevel, model };
}
```

上面这段是从 `session-manager.ts:419-436` 摘的（我省掉了类型标注）。注意它是**遍历路径、后来者覆盖**——所以"当前用什么模型"不是一个字段，而是这条路径上最后一次声明的结果。这就是树给的第二个红利：**状态是推导出来的，不是维护出来的**。任何回退都会自动把模型、思考档位一起退回去，不需要额外代码去"恢复状态"。

## 4. 一个指针：leafId

树有了，但还需要知道"我现在在哪"。答案是一个指针 `leafId`，指向当前叶子节点。

有意思的是：**这个指针不存**。它不在文件里，`SessionManager` 在内存里维护（`getLeafId()`，`session-manager.ts:1415`），默认就是文件里最后一条 entry：

```ts
let leaf = leafId ? index.get(leafId) : undefined;
leaf ??= entries[entries.length - 1];
```

（`session-manager.ts:400-405`，我省了 `index` 的构建。）

所以"当前在哪"这件事，默认等于"最后写了什么"，回退时被显式改指。这带来一个很干净的性质：**文件本身是完整的历史，指针只是视角**。同一份文件，换个 `leafId` 就是另一段对话——后面讲的 fork 和压缩，全靠这一点。

## 5. 投影：从叶子往上走，在压缩处切一刀

真正发给模型的东西，不是文件，是**投影**。分两步。

**第一步：把路径取出来。** 从 `leafId` 出发，沿 `parentId` 一路向上到根，然后反转（`buildSessionPath`，`session-manager.ts:390-417`）：

```ts
const path: SessionEntry[] = [];
let current = leaf;
while (current) {
  path.push(current);
  current = current.parentId ? index.get(current.parentId) : undefined;
}
path.reverse();
```

一个 while 循环，没有递归，没有遍历整棵树。这是树形存储的关键性能性质：**读一条路径的代价是路径长度，不是文件大小**。

**第二步：在这条路径上切出"有效区间"。** 这一步是 `buildContextEntries`（`session-manager.ts:476-543`），也是整个设计里最巧的地方。

它先在这条路径上找**最新的一次压缩**，然后把结果拼成三段：

1. 压缩节点本身（它是一条 `compaction` entry，里面装着摘要和 `firstKeptEntryId`）
2. 从 `firstKeptEntryId` 到压缩节点之间、且不是 system 消息的那些 entry
3. 压缩节点之后的全部 entry

{% mermaid %}
flowchart TD
  L["leafId（当前叶子）"] --> E5["entry 5"]
  E5 --> CP["compaction<br/>摘要 + firstKeptEntryId"]
  CP --> E3["entry 3"]
  E3 --> E2["entry 2"]
  E2 --> E1["entry 1"]
  CPD["上下文 = 摘要 + 从 firstKeptEntryId 起的原文 + 之后的全部"]
  CP -.-> CPD
{% endmermaid %}

用人话说：**压缩不是"把前 30 条删掉换成一段摘要"，而是"宣布从第 31 条开始重新看"**。第 1 到 30 条仍然躺在文件里，随时可以回去读；只是在构造上下文时，它们被那个摘要节点替代了。

这就解释了为什么 Pi 允许你压缩完继续聊、聊崩了还能回到压缩之前——因为压缩这个动作本身没有破坏任何数据，它只是在树上挂了一个"新的起点"。

顺带一提，`firstKeptEntryId` 的存在说明压缩是**有损但可控**的：摘要之外，还硬保留一段原始消息（最近的若干条），避免模型丢失最近几轮的细节。

## 6. 回退：不是删除，是挂一页摘要

现在讲最常用也最容易做错的功能：`/tree`。

在 Pi 里输入 `/tree` 会弹出一个树形选择器（`TreeSelectorComponent`，`interactive-mode.ts:5693` 的 `showTreeSelector`），你选中任意一个节点，回车。接下来的动作在 `agent-session.ts` 的 `navigateTree()`（`:4093`）里：

1. 算出"从当前叶子到目标节点"这一段被放弃的 entry（`collectEntriesForBranchSummary`，`:4124`）
2. 问你要不要给这段支线生成一页摘要
3. 要的话，生成一条 `branch_summary` entry 挂在目标节点下面
4. 把 `leafId` 改指目标节点

注意第 2、3 步：**被放弃的那段，不是消失了，是被总结成了一页，重新挂回树上**。

{% mermaid %}
sequenceDiagram
  participant U as 用户
  participant S as AgentSession
  participant M as SessionManager
  U->>S: /tree → 选中旧节点
  S->>M: collectEntriesForBranchSummary(旧leaf, target)
  M-->>S: 被放弃的 entry 列表
  S->>S: （可选）生成摘要
  S->>M: appendBranchSummary(target, 摘要)
  S->>M: setLeafId(target)
  Note over M: 文件只追加<br/>旧分支一条都没删
{% endmermaid %}

为什么值得这么做？因为"我回到分叉点换个说法"通常意味着"那条死路我已经想明白了"。如果摘要里写的是"试过用 A 方案，失败原因是 B"，那么新分支一开头就带着这个结论——**回退不但没丢信息，还把信息提升了密度**。

这是一个很典型的取舍：与其让用户（或模型）在新分支里重新踩一遍坑，不如花一次摘要的成本，把旧的上下文压缩后继承过来。Pi 把这做成一个可选的开关，默认关——因为有时候你回到分叉点就是想彻底甩掉之前的思路。

顺带说一个实现细节：`navigateTree` 也被 print 模式用（`print-mode.ts:93`），也就是 `pi -p` 里同样可以回退。这说明"树"不是 TUI 的装饰，它是会话模型的一部分，任何前端都能用。

## 7. 想改一条旧消息怎么办

还剩一个最难的情况：**我不回退，我就想改第 5 条消息里的一个错别字**。

追加写的文件改不了中间那行。删了重写？那所有 id 都得重编，指纹全变。Pi 的做法是 `context_edit`（`session-manager.ts:1371` 的 `appendContextEdit`）：追加一条 entry，内容是"第 5 条消息，替换成这样"或"第 5 条消息，省略掉"。

投影的时候，这条 `context_edit` 会把目标 entry 的投影结果换掉。文件里第 5 条还是原样，但模型看到的是改后的版本。

代码里能看到这个机制的两个真实用途：

- `agent-session.ts:983`：用户主动编辑某条消息
- `agent-session.ts:1291`：工具执行失败、上下文已经脏了的时候，把坏掉的那条消息**从投影里省略**（`replacement: null`），保证后续对话还能继续

第二个用途很有意思——它是"错误恢复"而不是"用户编辑"。当一条消息的投影结果无法持久化（代码里抛 `Cannot persist recovery omission because a projected message has no source entry`），系统宁可退化成抛错，也不肯悄悄改历史。**这个较真是对的**：一旦允许静默改写，树的可信度就没了。

## 8. fork 与标签

树的最后两个红利，各一句话：

**fork。** 从一个会话分叉出一个新会话（`forkFrom`），新文件复制到分叉点为止的所有 entry，文件头里写上 `parentSession`。于是"同一份历史、两条不同走向"成为可能，而且血缘关系明确。多智能体协作里，这就是"每个子任务拿一份自己的分支"。

**label。** `label` entry 给某个节点起个名字。因为节点有 id、有名字，你就可以用"回到那个叫 xxx 的节点"来代替"回退到第 37 条"——**引用的是节点，不是位置**。位置会变，节点不会。

## 9. 代价

一个诚实的设计总要付账。树形会话付的账是：

**每次启动都要重建投影。** 文件可能有几百条 entry，`buildSessionProjection`（`session-manager.ts:544`）要全读一遍。Pi 的缓解手段是：读文件时按行流式解析（`loadEntriesFromFile`，`:628`）、坏行跳过、头部扫描上限 1 MB（`MAX_SESSION_HEADER_SCAN_BYTES`，`:608`）。但本质上它仍然是 O(文件大小) 的重建，不是索引查询。

**文件只增不减。** 长期使用的会话会一直变长。这是 append-only 的必然代价，换来的是"任何时刻都能回到过去，且过去的东西不会被覆盖"。

**心智负担。** 第一次看到 `/tree` 的树形选择器，多数人是要愣一下的。线性对话是所有人都熟悉的隐喻，树不是。

## 10. 小结

回到开头那三个坏处：

| 坏处 | 数组方案 | 树方案 |
| --- | --- | --- |
| 回退 | 截断，丢历史 | 移动指针，全保留，还能挂摘要 |
| 重试 | 覆盖或中间插入 | 追加一个分叉节点 |
| 压缩 | 替换掉原文 | 挂一个压缩节点，原文留着 |

三条推论再抄一遍：

1. **一条对话 = 一棵 append-only 的树**，节点靠 `parentId` 相连，文件只追加。
2. **上下文 = 从 `leafId` 到根的一条路径**，压缩节点在这条路径上切出有效区间。
3. **状态是推导的，不是维护的**：模型、思考档位、压缩边界、消息改写，全都是"沿路径读出来"的结果。

这套设计最值得抄的地方，不是 JSONL，也不是 `parentId`——而是那个判断：**把"顺序"从数据结构里拿出来，变成一个指针**。顺序一旦可变，分叉、回退、覆盖就都免费了。

---

**相关阅读**

- [Pi 入门：一个把"极简"当真了的 agent](/2026/11/05/Pi-入门/)
- [Pi 的一次请求：agent loop 里到底发生了什么](/2026/11/05/Pi-Loop/)
