---
title: ClickHouse 入门：一个分析型数据库为什么长这样
date: 2026-11-20 20:00:00
categories: [数据库]
tags: [数据库, ClickHouse, OLAP, 列式存储]
cover: /images/ClickHouse入门/cover.jpg
description: 从“分析查询长什么样”出发，把 ClickHouse 的三个核心设计、MergeTree 的数据组织、分布式形态、建模四步和常见坑串成一条线，附本机实测数字。
---

如果你只用过 MySQL 或 PostgreSQL，第一次看到 ClickHouse 会有种错位感：建表要指定排序键，改一行数据要重写整个 part，按主键查一条居然比全表 `count()` 还慢，而 `select *` 几乎是原罪。

这些都不是怪癖，是同一个取舍在不同地方的投影。这篇文章不罗列功能，只讲一条因果链：**分析型查询的物理现实 → ClickHouse 用三个决定回应它 → 这些决定带来了什么用法和什么坑**。读完之后，你应该能自己判断一个场景该不该用它。

文中所有数字都在本机实测（macOS / OrbStack / ClickHouse 26.8.41.14 LTS，单机容器，10 亿字节级的小数据集），不是从别人的 benchmark 里抄的，条件也一并写在括号里。

## 一、先说它是什么，不是什么

ClickHouse 是一个**列式存储 + 向量化执行**的 OLAP 数据库，面向“扫一大片数据、只取少数几列、算聚合”的查询。

它擅长的事和它不擅长的事，其实是同一套设计的正反面：

| 它擅长 | 它不擅长 | 原因（后文展开） |
| --- | --- | --- |
| 亿级行的聚合、分组、去重 | 单行点查、主键查一条 | 稀疏索引只定位到 granule |
| 批量导入（每秒几十万到上百万行） | 高频小事务写入 | 每次写入产生一个 part，靠后台合并消化 |
| 大宽表的列裁剪扫描 | 大量 `JOIN`、复杂子查询 | 没有全局查询计划，join 靠自己扛内存 |
| 保留原始明细，随时换维度重算 | 行级更新、删除、事务 | 更新等于重写 part |

它不是“更快的 MySQL”，也不是“带 SQL 的 KV”，更不是搜索引擎。把它当 OLTP 用，会死得很难看；把它当“能存明细的报表引擎”用，会很舒服。

## 二、三个现场

**现场一：埋点表。** 产品的行为埋点一天几亿条，字段固定、只追加、不修改。业务要问的永远是“过去 30 天，各渠道各版本的转化率是多少”。这类查询会扫过几千万到几十亿行，但只用到 `channel`、`version`、`event`、`ts` 四列，而表里可能有四十列。

**现场二：报表跑不动。** 同样的查询放到 MySQL 上，二十列里读四列也要把整行读出来，IO 放大五倍以上；再加 `group by` 要在内存里维护几十万个分组，很快就碰内存墙。

**现场三：口径天天变。** 分析师今天要看漏斗，明天要看留存，后天要按新埋点重算。**这意味着原始明细必须留着**，不能提前聚合死——这一点决定了列存 + 便宜存储是刚需，而不是"顺便优化"。

三个现场的共同点是：**读得多、写得少、从不改，而且要的列远少于存的列**。记住这句话，后面所有设计都是它的推论。

## 三、物理现实：为什么行存在这里吃亏

数据库读盘的最小单位是一个块（block/page），不是一行。行存把同一行的所有列放在一起，于是"读四列"实际读的是"二十列拼成的整行"。

{% mermaid %}
graph LR
    subgraph 行存["行存：一行连续存放"]
        R1["id|ts|channel|version|event|...共20列|"] 
        R2["id|ts|channel|version|event|...共20列"]
        R3["id|ts|channel|version|event|...共20列"]
    end
    subgraph 列存["列存：一列连续存放"]
        C1["ts: 全部行的 ts"]
        C2["channel: 全部行的 channel"]
        C3["event: 全部行的 event"]
        C4["其余17列: 本次查询根本不读"]
    end
    行存 -->|"读4列 = 读20列"| IO1["IO 放大 5 倍"]
    列存 -->|"读4列 = 读4列"| IO2["IO 精确"]
{% endmermaid %}
<img src="/images/ClickHouse%E5%85%A5%E9%97%A8/scan.gif" alt="行存扫全列 vs 列存只扫需要的列" style="display:block;margin:18px auto;max-width:100%;border-radius:8px;">


列存还顺带解决了三件事：

1. **压缩率**。同一列的数据类型相同、分布相似、相邻行常常重复，压缩算法才有东西可压。
2. **向量化**。一列在内存里是连续数组，CPU 可以对一批值做同样的运算，上 SIMD，而不是一行一行解释。
3. **只读需要的列**。查询优化器在扫描前就知道"这次只碰 4 列"，其余 16 列一个字节都不用读。

最后这条不是理论。我在本机建了张 6 列、1000 万行的表（`events`，磁盘上 146.47 MiB），跑了几种查询，读数取自 `system.query_log`（`read_bytes` 是未压缩逻辑字节，耗时是热缓存下三次取最小值）：

| 查询 | 读取字节 | 扫描行数 | 耗时 |
| --- | --- | --- | --- |
| `SELECT count() FROM events` | **16 B** | 0（只读 part 元数据） | 1 ms |
| `SELECT sum(duration_ms) FROM events` | 38.15 MiB | 1000 万 | 18 ms |
| `SELECT sum(duration_ms), sum(amount), count(DISTINCT page)` | 198.18 MiB | 1000 万 | 67 ms |
| `... WHERE event_type='purchase'`（排序键前缀） | 128.02 KiB | 13.1 万 | 5 ms |
| `... WHERE user_id=42`（非排序键） | 38.15 MiB（扫 `user_id` 整列） | 1000 万 | 11 ms |

`count()` 只花 16 字节，是因为每个 part 的元数据里已经记了行数——它连一个数据块都不用碰。而 `sum(duration_ms)` 只读 38 MB，是那张表磁盘尺寸的四分之一。**同一个表，查询读多少，完全由你碰了哪些列、命中了哪些索引决定**，这和行存"读一行就是读一行"的直觉完全不同。

## 四、三个核心决定

### 决定一：列存 + 按列压缩

列存本身不难，难的是让压缩真的有效。ClickHouse 给每一列独立选择编码和压缩算法，并且提供 `LowCardinality` 这个类型——把低基数字符串（比如只有 4 种取值的事件类型）换成字典编码的整数。

我实测了这张表各列的压缩比（`system.parts_columns` 口径，压缩前/后）：

| 列 | 类型 | 压缩前 | 压缩后 | 压缩比 |
| --- | --- | --- | --- | --- |
| `event_type` | `LowCardinality(String)` | 9.56 MiB | **48.99 KiB** | **199.7×** |
| `page` | `String` | 131.42 MiB | 23.59 MiB | 5.6× |
| `ts` | `DateTime` | 38.15 MiB | 20.03 MiB | 1.9× |
| `duration_ms` | `UInt32` | 38.15 MiB | 25.68 MiB | 1.5× |
| `user_id` | `UInt32` | 38.15 MiB | 35.58 MiB | 1.1× |
| `amount` | `Float64` | 76.29 MiB | 41.42 MiB | 1.8× |

注意最后两列：`user_id` 和 `amount` 我用 `rand()` 随机生成，是纯随机数，压缩比只有 1.1–1.8 倍。**压缩吃的从来不是"列存"这个形式，而是"列内数据的规律"**——真实业务数据里，用户 ID 会反复出现、金额会有大量重复、时间戳单调递增，压缩比通常远好于随机数据。低基数字符串列则是另一个量级：少了两个数量级的 IO，报表能快十倍不奇怪。

### 决定二：向量化执行

列存让"读得少"成立，向量化让"算得快"成立。传统执行器一次处理一行（tuple-at-a-time），每行都要判断类型、做虚函数调用；ClickHouse 一次处理一整列（通常是 8192 行的块），循环体是紧凑的数组运算，编译器能自动向量化，CPU 的 SIMD 通道才用得上。

官方架构文档里写得很直白：*"Data is stored by columns, and processed in arrays (vectors or chunks of columns) during query execution. Whenever possible, operations are dispatched on arrays, rather than on individual values."* 它也承认向量化不是银弹——临时向量要写回缓存，超出 L2 会退化，所以现实中的好系统会混合向量化与运行时代码生成。

### 决定三：稀疏主键索引

这是 ClickHouse 最容易被误解的一点：**它没有 B+ 树那样的稠密索引，而是"每 8192 行记一个标记"的稀疏索引**。

{% mermaid %}
graph TD
    A["一个 part 的数据，按排序键排好序"] --> B["切成 granule，每 8192 行一个（index_granularity）"]
    B --> C["每个 granule 的第一行排序键值，写进 primary.idx"]
    C --> D["查询 WHERE 排序键 = x"]
    D --> E["二分找到可能包含 x 的 granule"]
    E --> F["只读这些 granule 的列文件"]
    F --> G["最多多读 index_granularity × 2 行的额外数据"]
{% endmermaid %}

稀疏索引的妙处在于**它小到可以常驻内存**，所以哪怕表有几百亿行，索引也不会撑爆 RAM。代价是：只能定位到"可能包含"的 8192 行区间，剩下的靠扫描。所以它适合"范围扫描 + 聚合"，不适合"主键查一条"。

本机验证：我用 `event_type` + `ts` 做排序键，查"最近 600 秒的采购事件"，返回 559 行：

```
读取 140.50 KiB，扫了 32,768 行，6 ms
```

32,768 正好是 4 个 granule。也就是说，数据库读了 4 个 8192 行的块，从里面筛出 559 行。**这就是稀疏索引的真实粒度感**：它不给你"精确到一行"，它给你"少读几个块"。

### 代价：三个决定放弃了什么

| 放弃的东西 | 具体表现 | 什么时候会咬你 |
| --- | --- | --- |
| 行级更新 | `ALTER UPDATE` 会重写整个 part（10M 行实测 0.45 s，因为只碰 11 个 part） | 高频改状态、改库存 |
| 事务 | 不支持跨表事务，写入是"批"语义 | 需要强一致的账务 |
| 稠密索引 | 主键查一条也要读一个 granule | 会话表、字典表 |
| 成熟 JOIN | 没有全局查询计划，右表要装进内存 | 多表关联的大查询 |

## 五、MergeTree：它的灵魂

ClickHouse 有几十种表引擎，但日常只用 `MergeTree` 家族。理解它要抓住四个概念：**part、partition、排序键、主键**。

- **part**：每次写入生成一个不可变的目录，内部按排序键排好序。
- **partition**：按 `PARTITION BY` 表达式（常见是月份或天）把数据分开，**不同分区的 part 永远不会合并**。分区主要用于数据生命周期管理（删旧数据直接 drop 分区），不是为了查询加速。
- **排序键 / 主键**：决定 part 内部的物理顺序，也决定稀疏索引能跳过什么。**主键可以只是排序键的前缀，甚至可以没有主键**（`ORDER BY tuple()`）。

### 一次写入发生了什么

{% mermaid %}
graph LR
    W["INSERT 一批数据"] --> P["生成一个新 part（按排序键排好序，写列文件 + 标记文件）"]
    P --> M["后台合并线程挑选若干小 part"]
    M --> B["合并成更大的 part（同样是排好序的）"]
    B --> M
    M -.->|"不同分区的 part 不合并"| X["分区边界"]
{% endmermaid %}
<img src="/images/ClickHouse%E5%85%A5%E9%97%A8/merge.gif" alt="后台合并：小 part 合并成大 part" style="display:block;margin:18px auto;max-width:100%;border-radius:8px;">


关键点是**写入只追加、从不原地修改**，合并是后台异步做的。这让读写可以并发（多版本：查询看到的是"查询开始时的那组 part"，不需要加锁），也让写入吞吐非常高——我 1000 万行一次性导入，实测 2.6 秒，生成 8 个 part。

### 坑一：小批量写入会产生海量 part

part 不是免费的：每个 part 都有元数据、索引文件、标记文件，查询时要打开所有 part。如果每秒写一次、每次写一行，part 数会指数级增长，直到触发保护。

我在本机做了个可控实验：先 `SYSTEM STOP MERGES` 停掉后台合并，然后灌 100 次单行插入——**part 数从 8 涨到 109**。恢复合并（`SYSTEM START MERGES`）后等 5 秒，回到 11 个。

这就是为什么 ClickHouse 有这两个阈值（26.8.41 的默认值，用 `system.merge_tree_settings` 查的）：

| 设置 | 默认值 | 含义 |
| --- | --- | --- |
| `parts_to_delay_insert` | 1000 | 活跃 part 超过这个数，INSERT 开始主动变慢 |
| `parts_to_throw_insert` | 3000 | 超过这个数直接拒绝写入 |

（这两个默认值在旧版本里是 150 / 300，升级到 26.x 后放宽了。你查自己机器的值最靠谱。）

**正确做法**：批量写。每批几万行到几十万行，或者用 `async_insert` 让服务端攒批，或者用 Kafka 引擎 / 物化视图做缓冲。

### 坑二：`OPTIMIZE ... FINAL` 不是日常操作

它会强制把所有 part 合并成一个大 part，非常耗 IO。日常不需要它——后台合并会自动收敛。只有"刚导入完等不及"或"要保证 `ReplacingMergeTree` 去重结果立刻可见"时才用。

### 引擎家族：同一个骨架，不同的合并逻辑

| 引擎 | 合并时做什么 | 典型场景 |
| --- | --- | --- |
| `MergeTree` | 只合并，不去重不聚合 | 明细表 |
| `ReplacingMergeTree` | 同排序键保留最后一条（版本号大的） | 订单状态、CDC 同步 |
| `SummingMergeTree` | 同排序键的数值列求和 | 预聚合指标 |
| `AggregatingMergeTree` | 同排序键执行 `AggregateFunction` 的合并 | 去重计数、分位数 |
| `CollapsingMergeTree` | 靠 `sign` 列抵消 +/- 行 | 可撤销的流式更新 |
| `ReplicatedMergeTree` | 在上述基础上走副本复制 | 生产集群 |

**一个常被误解的点**：`ReplacingMergeTree` 的去重是"合并时"发生的，不是写入时。所以在两次合并之间，同一条订单可能查出两行——想立刻拿到唯一结果，要么查的时候加 `FINAL`（慢），要么用 `argMax` 聚合，要么接受最终一致。

### 物化视图：把"每次重算"变成"写入时增量算"

```sql
CREATE MATERIALIZED VIEW demo.events_by_hour
ENGINE = SummingMergeTree
ORDER BY (event_type, hour)
AS SELECT
    event_type,
    toStartOfHour(ts) AS hour,
    count() AS cnt,
    sum(amount) AS amt
FROM demo.events
GROUP BY event_type, hour;
```

物化视图本质是"**INSERT 触发器 + 目标表**"：原始表来了数据，立即算一遍增量写进目标表。查询改成查目标表，就变成了几百行的点查。代价是它只对**新写入**的数据生效，历史数据要手动补，而且插入过程的失败会影响原始写入（所以生产上常配 `async` 物化视图或消息队列解耦）。

`Projection` 是另一条路：在表内定义"按另一种顺序物化的副本"，查询时优化器自动选。比物化视图更省心（自动维护一致性），但也更吃存储。

## 六、分布式：一张表怎么变成集群

单机 ClickHouse 已经能扛很多场景（它单机性能极其强悍），但真正上生产总归要分片。

{% mermaid %}
graph LR
    C["客户端"] --> D["Distributed 表（不存数据，只是路由视图）"]
    D --> S1["分片 1：本地 MergeTree 表"]
    D --> S2["分片 2：本地 MergeTree 表"]
    S1 --> R1["副本 1a"]
    S1 --> R2["副本 1b"]
    S2 --> R3["副本 2a"]
    S2 --> R4["副本 2b"]
    K["ClickHouse Keeper / ZooKeeper"] -.->|"复制日志、元数据、分布式 DDL"| S1
    K -.-> S2
{% endmermaid %}

几个要点：

1. **本地表 + Distributed 表**是标准形态。本地表（`ReplicatedMergeTree`）负责存数据，`Distributed` 表只负责路由查询。写数据要写本地表（或者配好分片键写 Distributed 表）。
2. **副本是异步多主复制**。写入任意一个副本，通过 Keeper 里的复制日志同步给其他副本；默认没有写仲裁，所以刚写完的节点挂掉可能丢数据——需要强一致就开 `insert_quorum`。
3. **查询是"下发 + 合并"**。`Distributed` 表把查询改写成发给各分片的子查询，各分片算完中间结果，最后汇总。它没有全局查询计划，所以跨分片的 `JOIN`、高基数 `GROUP BY` 会很吃力——这类查询往往需要先 `reshuffle`，或者干脆改成"宽表预聚合"。
4. **Keeper 是新的单点风险**。生产上至少三个节点。ClickHouse 从 21.x 起内置了 Keeper（用 Raft 实现），可以不依赖 ZooKeeper 了。

## 七、怎么用：一条最小路径

### 第一步：跑起来

```bash
docker run -d --name clickhouse \
  -p 8123:8123 -p 9000:9000 \
  clickhouse/clickhouse-server:26.8

# 命令行客户端
docker exec -it clickhouse clickhouse-client

# HTTP 接口（8123）：可以直接用 curl 查
curl 'http://localhost:8123/?query=SELECT%20version()'
```

两个端口的分工：**9000 是原生 TCP 协议**（客户端、驱动用），**8123 是 HTTP 接口**（`curl`、JDBC、各种语言 SDK 用）。做数据探索时 HTTP 接口很方便，因为查询就是一条 URL。

### 第二步：建模四步

这是整篇文章最实用的部分。拿到一个业务需求，按这个顺序想：

**① 先问：哪些列会出现在 `WHERE` 和 `GROUP BY` 里？**
排序键就选这些列，顺序按"过滤频率 × 选择性"排。`ORDER BY (event_type, ts)` 意味着"先按事件类型分块，块内按时间排"，所以"某类型 + 时间范围"的查询能跳过大量数据；反过来只按 `ts` 过滤就跳不动。

**② 再问：数据要不要按时间淘汰？**
要，就 `PARTITION BY toYYYYMM(ts)`（月度）或 `toYYYYMMDD(ts)`（日度）。**分区粒度千万别太细**：按 `user_id` 分区是反模式，会产生几十万个分区，每个分区又有一堆 part，元数据就压垮了。官方建议是"大多数情况按月，可观测性场景按天，永远不要按客户端标识分区"。

**③ 选引擎**：明细用 `MergeTree`，要按主键去重最新值用 `ReplacingMergeTree`，要预聚合用 `SummingMergeTree` / `AggregatingMergeTree`。

**④ 选编码**：低基数字符串用 `LowCardinality(String)`；时间戳用 `DateTime`（必要时 `DateTime64`）；金额别用 `Float64`（精确计算用 `Decimal`）；能用整数就别用字符串。

一个完整的 DDL：

```sql
CREATE TABLE analytics.events (
    ts           DateTime,
    user_id      UInt64,
    event_type   LowCardinality(String),   -- 4 种取值，字典编码
    channel      LowCardinality(String),
    page         String,
    duration_ms  UInt32,
    amount       Decimal(18, 2)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (event_type, ts)          -- 过滤 + 时间范围
TTL ts + INTERVAL 180 DAY;         -- 半年后自动删，靠合并触发
```

### 第三步：写入

- **批量写**，每批几万行以上。一次 `INSERT` 一行是自找麻烦。
- 流式数据用 `Kafka` 引擎表 + 物化视图，或者先落到消息队列再批量灌。
- 服务端攒批可以开 `async_insert=1, wait_for_async_insert=1`，让 ClickHouse 帮你把小批合并成大块再落盘。
- 导入大文件用 `clickhouse-client --query "INSERT INTO ... FORMAT CSV" < data.csv`，或者直接 `SELECT * FROM file(...)` 读本地文件。

### 第四步：查询习惯

| 习惯 | 原因 |
| --- | --- |
| 只 `SELECT` 需要的列 | 列存下少读一列就少一次 IO，别写 `SELECT *` |
| 用 `PREWHERE` 提前过滤 | 让过滤在读取其他列之前发生，减少解压量 |
| 避免在主键列上套函数 | `WHERE toDate(ts) = '2026-11-20'` 用不上索引，改成范围条件 |
| 大表 `JOIN` 前先想清楚右表多大 | 右表默认要装进内存，超了会报错 |
| 用 `LIMIT` 时注意 `ORDER BY` | 没有排序的 `LIMIT` 很快，但结果没意义 |
| 聚合前先缩小范围 | 能靠分区和索引砍掉的数据，别留到 `GROUP BY` 里 |

### 第五步：运维要看什么

- `system.parts`：part 数量、大小、分区分布。part 数失控是头号故障。
- `system.query_log`：每次查询读了多少字节、扫了多少行、耗时多少。调优的第一手证据。
- `system.merges`：正在进行的合并。
- `system.mutations`：`ALTER UPDATE/DELETE` 的进度，卡住的 mutation 会一直堆积。
- `system.replicas`：副本延迟、复制队列。

## 八、什么时候用，什么时候别用

| 场景 | 适不适合 | 说明 |
| --- | --- | --- |
| 日志、埋点、APM 明细 | 非常适合 | 只追加、按时间查、列裁剪收益巨大 |
| BI 报表、大宽表聚合 | 非常适合 | 典型 OLAP |
| 时序指标（配合 `AggregatingMergeTree`） | 适合 | 指标预聚合 |
| 用户行为分析、漏斗、留存 | 适合 | 明细保留，口径随便变 |
| 用 SQL 直接查 S3 / 文件 | 适合 | `s3()`、`file()` 表函数，不用导入 |
| 订单、账户等 OLTP | 不适合 | 需要事务和行级更新 |
| 高频点查（按 ID 查一条） | 不适合 | 稀疏索引帮不上，每次读一个 granule |
| 全文检索 / 模糊搜索 | 不适合 | 有 text index 但不专业，用 ES |
| 频繁 `UPDATE` / `DELETE` 单行 | 不适合 | 每次都是重写 part 的 mutation |
| 小数据量（几百万行以内） | 没必要 | SQLite / DuckDB / PostgreSQL 更省事 |

### 和其他分析引擎怎么选

| 系统 | 一句话定位 | 和 ClickHouse 的差别 |
| --- | --- | --- |
| **Doris / StarRocks** | MPP 架构的分析数据库 | 对 `JOIN` 和多表关联更友好，运维组件更多（FE/BE） |
| **DuckDB** | 嵌入式分析数据库 | 单机、零运维，适合本地分析文件；并发和集群不行 |
| **Elasticsearch** | 搜索引擎 | 全文检索强，聚合精度和成本不如列存 |
| **PostgreSQL** | 通用关系库 | 事务、点查、生态强；大宽表扫描性能差一个数量级 |
| **Spark / Flink** | 计算引擎 | 不是存储，通常和上面某个组合使用 |

选型判据其实就一句：**你的查询是"扫一大片、算聚合"还是"查几条、要事务"**。前者 ClickHouse，后者别用。

## 九、心智模型：一句话记住它

> ClickHouse 把数据按列切成不可变的 part，按排序键排好序，用稀疏索引跳着读，后台不断把小 part 合并成大 part；它用"放弃行级更新和事务"换来了极致的扫描与聚合速度。

如果你只能记住三件事：

1. **排序键决定一切**。查询能不能跳过数据，全看你把什么列放在 `ORDER BY` 的前面。
2. **写入要批量**。part 是合并出来的，不是写出来的；小批量写入会让后台合并追不上。
3. **它是"存明细的报表引擎"**，不是"能算的数据库"。原始明细留着，聚合随时重算，这才是它最舒服的用法。

## 附：本文实测环境

- ClickHouse `26.8.41.14`（LTS），单机容器，OrbStack，12.6 GB 内存分配
- 数据集：6 列 1000 万行，磁盘占用 146.47 MiB，8 个 part
- 耗时统一取 `system.query_log.query_duration_ms`（服务端执行时间），热缓存下三次取最小；冷读首次通常是热缓存的 5–10 倍
- 同机比较有意义，绝对值不要当 benchmark 用——尤其不要拿容器里的数字去对比裸机 MySQL
- 版本相关数字（`parts_to_delay_insert=1000`、`index_granularity=8192`）请以你机器上的 `system.merge_tree_settings` 为准

## 参考资料

- [ClickHouse 官方文档：MergeTree engine](https://clickhouse.com/docs/en/engines/table-engines/mergetree-family/mergetree)
- [ClickHouse 官方文档：Architecture Overview](https://clickhouse.com/docs/en/development/architecture)
- [ClickHouse 官方文档：Custom Partitioning Key](https://clickhouse.com/docs/en/engines/table-engines/mergetree-family/custom-partitioning-key)
- [ClickHouse 官方文档：Distributed table engine](https://clickhouse.com/docs/en/engines/table-engines/special/distributed)
- [ClickHouse GitHub 仓库](https://github.com/ClickHouse/ClickHouse)

## 相关阅读

- [如何设计一个数字员工](/2026/11/05/数字员工架构/)
- [Agent 的记忆怎么做：四份开源实现的拆解与取舍](/2026/11/11/Agent记忆/)
- [Context：从人与人到 Agent 与 Agent](/2026/11/18/Context-从人到Agent/)
