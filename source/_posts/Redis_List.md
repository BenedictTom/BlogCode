---
title: Redis_List
main_color: "#80a340ff"
categories: Redis
tags:
  - Redis
cover: https://www.zdnet.com/a/img/resize/de9071070cd7af7e4fa747cfefb167b9752580b6/2019/07/01/88f8ee84-6545-4d90-82c2-c068c9f8d5d6/redis1.jpg?auto=webp&fit=crop&height=675&width=1200
---

## List（列表）

### 什么是 List？

List（列表）是 Redis 中一种**有序且可重复**的数据结构，类似于编程语言中的数组或链表。它支持在列表的两端进行高效的插入和删除操作。

你可以把它想象成一个**双端队列**：
- 可以在头部和尾部快速添加或删除元素
- 元素有固定的顺序（按插入顺序）
- 允许重复元素存在
- 支持按索引访问

List 非常适合用于"消息队列"、"最新动态"、"任务列表"等场景。

---

### 通俗易懂的解释

想象你有一个**可以两头开口的管子**：

```
[头部] ←→ [元素1] ←→ [元素2] ←→ [元素3] ←→ [尾部]
```

你可以：
- 从头部或尾部**快速插入**新元素
- 从头部或尾部**快速取出**元素
- 查看任意位置的元素
- 按顺序遍历所有元素

这就是 Redis List 的核心思想：**双端操作 + 有序存储 + 支持重复**

---

### 核心特性

| 特性 | 说明 |
|------|------|
| **双端操作** | 支持在头部（LPUSH）和尾部（RPUSH）快速插入/删除 |
| **有序性** | 元素按插入顺序排列，支持按索引访问 |
| **可重复** | 同一个元素可以出现多次 |
| **高效操作** | 头部和尾部操作时间复杂度 O(1) |
| **支持阻塞操作** | 提供 BLPOP、BRPOP 等阻塞式命令 |

底层使用 **双向链表（Doubly Linked List）** 或 **压缩列表（Ziplist）** 实现，兼顾性能与内存。

---

### 常用命令

#### 1. `LPUSH key element [element ...]`
- **作用**：将一个或多个元素插入到列表的**头部**（左侧）。
- **示例**：
  ```bash
  LPUSH mylist "world" "hello"
  ```
  结果：`["hello", "world"]`（后插入的在前面）

---

#### 2. `RPUSH key element [element ...]`
- **作用**：将一个或多个元素插入到列表的**尾部**（右侧）。
- **示例**：
  ```bash
  RPUSH mylist "redis"
  ```
  结果：`["hello", "world", "redis"]`

---

#### 3. `LPOP key [count]`
- **作用**：移除并返回列表**头部**的一个或多个元素。
- **示例**：
  ```bash
  LPOP mylist  # 返回 "hello"，列表变为 ["world", "redis"]
  ```

#### `RPOP key [count]`
- **作用**：移除并返回列表**尾部**的一个或多个元素。
  ```bash
  RPOP mylist  # 返回 "redis"，列表变为 ["world"]
  ```

---

#### 4. `LLEN key`
- **作用**：返回列表的长度。
- **示例**：
  ```bash
  LLEN mylist  # 返回 1
  ```

---

#### 5. `LRANGE key start stop`
- **作用**：返回列表中指定范围内的元素。
- **示例**：
  ```bash
  LRANGE mylist 0 -1  # 返回所有元素
  LRANGE mylist 0 1   # 返回前两个元素
  ```
  - `0` 表示第一个元素，`-1` 表示最后一个元素

---

#### 6. `LINDEX key index`
- **作用**：通过索引获取列表中的元素。
- **示例**：
  ```bash
  LINDEX mylist 0  # 返回第一个元素
  ```

---

#### 7. `LINSERT key BEFORE|AFTER pivot element`
- **作用**：在列表的某个元素前或后插入新元素。
- **示例**：
  ```bash
  LINSERT mylist BEFORE "world" "new"
  ```

---

#### 8. `LREM key count element`
- **作用**：从列表中删除指定数量的指定元素。
- **示例**：
  ```bash
  LREM mylist 1 "hello"  # 删除一个 "hello"
  ```

---

#### 9. `LSET key index element`
- **作用**：通过索引设置列表元素的值。
- **示例**：
  ```bash
  LSET mylist 0 "updated"
  ```

---

#### 10. `阻塞操作命令`

- `BLPOP key [key ...] timeout`：阻塞式左弹出
  ```bash
  BLPOP mylist 10  # 等待 10 秒，如果列表为空则阻塞
  ```

- `BRPOP key [key ...] timeout`：阻塞式右弹出
  ```bash
  BRPOP mylist 5   # 等待 5 秒
  ```

- `BRPOPLPUSH source destination timeout`：阻塞式右弹出并左推入
  ```bash
  BRPOPLPUSH queue processing 10  # 从 queue 右弹出，推入 processing
  ```

---

### 🌰 实际应用场景举例：消息队列系统

#### 场景 1：简单的消息队列
```bash
# 生产者发送消息
LPUSH message_queue "任务1: 处理用户注册"
LPUSH message_queue "任务2: 发送邮件通知"
LPUSH message_queue "任务3: 更新用户统计"

# 消费者处理消息
RPOP message_queue  # 返回 "任务1: 处理用户注册"
```

#### 场景 2：最新动态列表
```bash
# 用户发布动态
LPUSH user:1001:activities "发布了新文章"
LPUSH user:1001:activities "点赞了某篇文章"
LPUSH user:1001:activities "关注了新用户"

# 获取最新 10 条动态
LRANGE user:1001:activities 0 9
```

#### 场景 3：任务调度系统
```bash
# 添加待处理任务
LPUSH pending_tasks "扫描文件系统"
LPUSH pending_tasks "备份数据库"
LPUSH pending_tasks "清理临时文件"

# 工作进程获取任务（阻塞式）
BLPOP pending_tasks 30  # 等待 30 秒获取任务
```

#### 场景 4：实现栈和队列
```bash
# 栈（后进先出）：LPUSH + LPOP
LPUSH stack "item1" "item2" "item3"
LPOP stack  # 返回 "item3"

# 队列（先进先出）：LPUSH + RPOP 或 RPUSH + LPOP
LPUSH queue "task1" "task2" "task3"
RPOP queue  # 返回 "task1"
```

---

### ✅ List 的经典使用场景

| 场景 | 说明 |
|------|------|
| **消息队列** | 生产者 LPUSH，消费者 RPOP，实现 FIFO 队列 |
| **最新动态** | 用户活动流、系统日志、时间线 |
| **任务调度** | 待处理任务列表，支持阻塞式获取 |
| **栈和队列** | 通过不同组合实现各种数据结构 |
| **排行榜** | 结合 ZSET 实现复杂的排序需求 |
| **分页查询** | LRANGE 实现高效的分页 |
| **阻塞队列** | BLPOP/BRPOP 实现生产者-消费者模式 |

---

### 🔔 注意事项

- **内存使用**：List 会占用较多内存，特别是长列表
- **性能考虑**：中间位置的操作（如 LINSERT）时间复杂度是 O(N)
- **阻塞操作**：BLPOP/BRPOP 会阻塞连接，注意超时设置
- **数据一致性**：多客户端操作时注意并发问题
- **大列表优化**：考虑使用 LTRIM 定期清理或拆分大列表

---

### ✅ 总结：List 适合什么场景？

| 特点 | 是否适合 List |
|------|----------------|
| 需要保持插入顺序 | ✅ 天然支持 |
| 双端快速操作 | ✅ 核心优势 |
| 支持重复元素 | ✅ 允许重复 |
| 消息队列需求 | ✅ 经典应用 |
| 最新动态展示 | ✅ 时间线场景 |
| 阻塞式消费 | ✅ BLPOP/BRPOP |
| 中间位置频繁操作 | ❌ 性能较差 |

---

✅ **一句话总结**：  
**如果你需要一个可以两头操作、保持顺序、支持重复的数据结构，特别是消息队列、时间线、任务列表等场景，Redis List 就是你的最佳选择！**
