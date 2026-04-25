---
title: MongoDB基础
main_color: "#229ab2ff"
categories: 数据库
tags:
  - MongoDB
cover: https://free.picui.cn/free/2026/03/28/69c74e3b20d4f.png  
---

# MongoDB 基础入门

## 阶段一：MongoDB 基础入门
**目标：掌握 MongoDB 的基本概念、安装与基础操作。**

## 1. 了解 NoSQL 与 MongoDB

### 什么是 NoSQL？
NoSQL（Not Only SQL）是一类非关系型数据库的统称，它们不使用传统的表格关系模型来存储数据。

**与关系型数据库（如 MySQL）的区别：**

| 特性 | 关系型数据库 | NoSQL数据库 |
|------|-------------|-------------|
| 数据模型 | 表格结构，预定义模式 | 灵活模式，多种数据模型 |
| 事务支持 | ACID事务 | 通常只支持BASE（基本可用、软状态、最终一致性） |
| 扩展性 | 垂直扩展（增加硬件） | 水平扩展（增加节点） |
| 查询语言 | SQL | 特定API或查询语言 |
| 一致性 | 强一致性 | 最终一致性 |

### MongoDB 的特点

#### 1. 文档模型
- **BSON格式**：Binary JSON，支持更多数据类型
- **嵌套文档**：可以存储复杂的层次结构数据
- **数组支持**：原生支持数组类型

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "name": "张三",
  "age": 25,
  "email": "zhangsan@example.com",
  "address": {
    "city": "北京",
    "street": "中关村大街",
    "postalCode": "100080"
  },
  "hobbies": ["读书", "游泳", "编程"],
  "createdAt": ISODate("2024-01-01T00:00:00Z")
}
```

#### 2. 高可用性
- **副本集（Replica Set）**：自动故障转移
- **分片集群（Sharding）**：水平扩展能力
- **自动备份**：支持增量备份和全量备份

#### 3. 水平扩展
- 通过分片将数据分布到多个服务器
- 支持读写分离
- 自动负载均衡

#### 4. 灵活模式
- 同一集合中的文档可以有不同的字段
- 支持动态添加字段
- 无需预定义表结构

### 适用场景
- **日志系统**：存储应用日志、系统日志
- **内容管理**：博客、CMS系统、文档存储
- **实时分析**：大数据分析、实时统计
- **IoT应用**：传感器数据、设备状态
- **游戏数据**：用户档案、游戏状态
- **电商平台**：商品目录、用户行为

## 2. 安装与环境搭建

### 本地安装 MongoDB Community Server

#### Windows 安装
1. 访问 [MongoDB 官网](https://www.mongodb.com/try/download/community)
2. 下载 Windows 版本的 MSI 安装包
3. 运行安装程序，选择"Complete"安装
4. 安装 MongoDB Compass（可选）
5. 配置环境变量

#### macOS 安装
```bash
# 使用 Homebrew 安装
brew tap mongodb/brew
brew install mongodb-community

# 启动 MongoDB 服务
brew services start mongodb/brew/mongodb-community

# 或者手动启动
mongod --config /usr/local/etc/mongod.conf
```

#### Linux 安装
```bash
# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# 启动服务
sudo systemctl start mongod
sudo systemctl enable mongod
```

### 使用 MongoDB Atlas（云服务）
1. 访问 [MongoDB Atlas](https://www.mongodb.com/atlas)
2. 创建免费账户
3. 创建新集群（选择免费层 M0）
4. 配置网络访问（IP白名单）
5. 创建数据库用户
6. 获取连接字符串

**连接字符串示例：**
```
mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/database?retryWrites=true&w=majority
```

### 安装 MongoDB Compass（可视化工具）
1. 从官网下载对应平台的安装包
2. 安装完成后启动
3. 连接到本地或远程 MongoDB 实例
4. 提供图形化界面进行数据操作

## 3. 基础操作


### 数据类型

MongoDB支持多种数据类型，这些数据类型能够满足不同的应用场景需求。以下是MongoDB中常见的数据类型：

1. **Double**: 用于存储浮点数值。
2. **String**: 存储UTF-8编码的字符串，确保在不同语言环境下的兼容性。
3. **Object**: 表示嵌入式文档，允许在一个文档内部包含另一个文档或对象。
4. **Array**: 支持存储数组或列表，可以包含不同类型的值（包括其他文档）。
5. **Binary Data**: 用于存储二进制数据，如图像、文件等。
6. **ObjectId**: 是一种特殊的十六进制数，通常用作“_id”字段的默认值，保证每个文档的唯一性。
7. **Boolean**: 存储true和false值。
8. **Date**: 使用UTC时间格式表示日期和时间，可用于记录事件发生的时间戳。
9. **Null**: 表示空值或不存在的字段。
10. **Regular Expression**: 存储正则表达式，常用于复杂的字符串匹配操作。
11. **JavaScript**: 可以存储并执行JavaScript代码片段，尽管这不是最常见的用途。
12. **Symbol**: 主要用于与其他编程语言交互时保留特定语言的符号信息，在大多数情况下与字符串相似。
13. **Code with Scope**: 用来存储带有局部变量范围的JavaScript代码。
14. **32-bit Integer & 64-bit Integer**: 分别用于存储32位和64位整数。
15. **Decimal128**: 提供高精度的十进制数存储，适用于金融计算等需要精确小数处理的场景。
16. **Min/Max Keys**: 特殊的数据类型，分别比所有其他可能的键值小或大，通常用于特殊比较或排序逻辑。

每种数据类型都有其适用的场景，选择合适的数据类型有助于提高查询效率、减少存储空间以及简化应用程序逻辑。例如，使用`ObjectId`作为主键可以自动为每个文档生成唯一的标识符；而使用嵌入式文档（Object类型）可以构建复杂的数据结构，减少数据库查询次数，提高性能。理解这些数据类型是有效利用MongoDB的关键。


### 数据库、集合、文档的概念

#### 数据库（Database）
- MongoDB 中的顶级容器
- 包含多个集合
- 每个数据库有独立的权限和配置

```javascript
// 创建/切换到数据库
use myDatabase

// 查看所有数据库
show dbs

// 查看当前数据库
db
```

#### 集合（Collection）
- 类似于关系型数据库中的表
- 存储文档的容器
- 无需预定义结构

```javascript
// 创建集合（隐式创建）
db.users.insertOne({name: "张三", age: 25})

// 显式创建集合
db.createCollection("products")

// 查看所有集合
show collections
```

#### 文档（Document）
- 集合中的单个记录
- BSON 格式存储
- 支持嵌套结构和数组

```javascript
// 文档示例
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "name": "张三",
  "age": 25,
  "email": "zhangsan@example.com"
}
```

### CRUD 操作

#### 创建（Create）
```javascript
// 插入单个文档
db.users.insertOne({
  name: "李四",
  age: 30,
  email: "lisi@example.com",
  createdAt: new Date()
})

// 插入多个文档
db.users.insertMany([
  {name: "王五", age: 28, email: "wangwu@example.com"},
  {name: "赵六", age: 32, email: "zhaoliu@example.com"}
])

// 插入文档并指定 _id
db.users.insertOne({
  _id: "user001",
  name: "自定义ID用户",
  age: 25
})
```

#### 读取（Read）
```javascript
// 查询所有文档
db.users.find()

// 查询特定条件的文档
db.users.find({age: {$gt: 25}})

// 查询单个文档
db.users.findOne({name: "张三"})

// 限制返回数量
db.users.find().limit(5)

// 跳过文档数量
db.users.find().skip(5).limit(5)

// 排序
db.users.find().sort({age: 1})  // 1升序，-1降序

// 投影（只返回指定字段）
db.users.find({}, {name: 1, email: 1, _id: 0})
```

#### 更新（Update）
```javascript
// 更新单个文档
db.users.updateOne(
  {name: "张三"},
  {$set: {age: 26, updatedAt: new Date()}}
)

// 更新多个文档
db.users.updateMany(
  {age: {$lt: 30}},
  {$set: {status: "young"}}
)

// 替换整个文档
db.users.replaceOne(
  {name: "张三"},
  {name: "张三", age: 26, email: "zhangsan@example.com", status: "active"}
)

// 使用 upsert（不存在则插入）
db.users.updateOne(
  {email: "newuser@example.com"},
  {$set: {name: "新用户", age: 25}},
  {upsert: true}
)
```

#### 删除（Delete）
```javascript
// 删除单个文档
db.users.deleteOne({name: "张三"})

// 删除多个文档
db.users.deleteMany({age: {$lt: 18}})

// 删除集合中的所有文档
db.users.deleteMany({})

// 删除整个集合
db.users.drop()

// 删除整个数据库
db.dropDatabase()
```

### 查询操作符

#### 比较操作符
```javascript
// 等于
db.users.find({age: 25})

// 不等于
db.users.find({age: {$ne: 25}})

// 大于
db.users.find({age: {$gt: 25}})

// 大于等于
db.users.find({age: {$gte: 25}})

// 小于
db.users.find({age: {$lt: 25}})

// 小于等于
db.users.find({age: {$lte: 25}})

// 在指定范围内
db.users.find({age: {$in: [25, 30, 35]}})

// 不在指定范围内
db.users.find({age: {$nin: [25, 30, 35]}})
```

#### 逻辑操作符
```javascript
// AND 操作（默认）
db.users.find({age: {$gt: 25}, city: "北京"})

// OR 操作
db.users.find({$or: [{age: {$lt: 25}}, {city: "上海"}]})

// AND 和 OR 组合
db.users.find({
  $and: [
    {age: {$gte: 18}},
    {$or: [{city: "北京"}, {city: "上海"}]}
  ]
})

// NOT 操作
db.users.find({age: {$not: {$lt: 25}}})
```

#### 元素操作符
```javascript
// 字段存在
db.users.find({email: {$exists: true}})

// 字段类型检查
db.users.find({age: {$type: "number"}})
```

#### 数组操作符
```javascript
// 包含所有元素
db.users.find({hobbies: {$all: ["读书", "游泳"]}})

// 包含任意元素
db.users.find({hobbies: {$in: ["读书"]}})

// 数组大小
db.users.find({hobbies: {$size: 3}})

// 数组元素匹配
db.users.find({"hobbies.0": "读书"})
```

## 4. 索引基础

### 索引的重要性
- **提高查询性能**：避免全集合扫描
- **支持排序操作**：避免内存排序
- **唯一性约束**：确保数据唯一性
- **文本搜索**：支持全文检索

### 创建单字段索引
```javascript
// 创建升序索引
db.users.createIndex({age: 1})

// 创建降序索引
db.users.createIndex({createdAt: -1})

// 创建唯一索引
db.users.createIndex({email: 1}, {unique: true})

// 创建稀疏索引（只索引存在该字段的文档）
db.users.createIndex({phone: 1}, {sparse: true})

// 查看集合的索引
db.users.getIndexes()

// 删除索引
db.users.dropIndex({age: 1})
```

### 创建复合索引
```javascript
// 创建复合索引
db.users.createIndex({age: 1, city: 1})

// 创建复合唯一索引
db.users.createIndex({username: 1, email: 1}, {unique: true})

// 复合索引的顺序很重要
// 查询 {age: 25, city: "北京"} 可以使用索引
// 查询 {city: "北京"} 不能有效使用索引
```

### 索引类型


在MongoDB中，索引可以是升序（ascending）或降序（descending），这主要影响的是索引中数据的排序方式。尽管升序和降序索引在查询性能上对于单字段索引来说几乎没有差别，它们的区别主要体现在多字段索引以及排序操作中。

### 单字段索引

- **升序索引**：当你创建一个升序索引时，MongoDB会根据该字段的值从小到大对文档进行排序。
- **降序索引**：相反，如果你创建的是降序索引，那么MongoDB将按照该字段的值从大到小来对文档排序。

对于单字段索引而言，升序和降序索引的实际查询效率几乎相同，因为MongoDB能够高效地遍历索引树，无论其顺序如何。

### 多字段索引

当涉及到包含多个字段的复合索引时，升序和降序索引的选择变得更为重要，尤其是在执行需要对结果集进行排序的查询时：

- 如果你的查询经常需要基于某些字段以特定顺序返回结果，那么正确设置每个字段的索引顺序（升序或降序）可以使MongoDB直接使用索引来满足排序需求，而无需执行额外的排序步骤。例如，如果一个查询通常要求按字段A降序然后按字段B升序排列结果，那么为字段A创建降序索引且为字段B创建升序索引可能会提高性能。
  
- 在某些情况下，特别是当查询条件与排序顺序相匹配时，正确的索引顺序可以帮助MongoDB更有效地执行查询，因为它可以直接“行走”索引来获取已排序的结果，而不是先获取所有符合条件的文档再进行排序。

总之，在大多数情况下，对于单个字段的索引，选择升序还是降序并不会显著影响查询性能。然而，在设计复合索引时，考虑到查询中常用的排序模式，合理安排各个字段的索引顺序可以优化查询性能。

#### 1. 单字段索引
```javascript
// 最常见的索引类型
db.users.createIndex({name: 1})
```

#### 2. 复合索引
```javascript
// 支持多字段查询
db.users.createIndex({lastName: 1, firstName: 1})
```

#### 3. 多键索引（数组字段）
```javascript
// 自动为数组字段创建
db.users.createIndex({tags: 1})
```

#### 4. 地理空间索引
```javascript
// 2dsphere 索引用于地理空间查询
db.places.createIndex({location: "2dsphere"})
```

#### 5. 文本索引
```javascript
// 支持全文搜索
db.articles.createIndex({content: "text"})
```

#### 6. 哈希索引
```javascript
// 用于分片集群
db.users.createIndex({_id: "hashed"})
```

### 索引管理
```javascript
// 查看索引使用情况
db.users.aggregate([
  {$indexStats: {}}
])

// 查看查询计划
db.users.find({age: 25}).explain("executionStats")

// 后台创建索引（生产环境推荐）
db.users.createIndex({age: 1}, {background: true})

// 部分索引（只索引满足条件的文档）
db.users.createIndex(
  {age: 1},
  {partialFilterExpression: {age: {$gte: 18}}}
)
```

### 索引最佳实践
1. **为查询条件创建索引**：WHERE 子句中的字段
2. **为排序字段创建索引**：ORDER BY 中的字段
3. **避免过多索引**：每个索引都会占用存储空间和影响写入性能
4. **使用复合索引**：减少索引数量，提高查询效率
5. **监控索引使用情况**：删除未使用的索引

## 5. 实践练习

### 练习1：用户管理系统
```javascript
// 创建用户集合
use userManagement

// 插入测试数据
db.users.insertMany([
  {
    name: "张三",
    age: 25,
    email: "zhangsan@example.com",
    city: "北京",
    hobbies: ["读书", "游泳"],
    createdAt: new Date()
  },
  {
    name: "李四",
    age: 30,
    email: "lisi@example.com",
    city: "上海",
    hobbies: ["编程", "游戏"],
    createdAt: new Date()
  },
  {
    name: "王五",
    age: 28,
    email: "wangwu@example.com",
    city: "广州",
    hobbies: ["旅游", "摄影"],
    createdAt: new Date()
  }
])

// 创建索引
db.users.createIndex({email: 1}, {unique: true})
db.users.createIndex({age: 1, city: 1})
db.users.createIndex({createdAt: -1})

// 查询练习
// 1. 查找年龄大于25岁的用户
db.users.find({age: {$gt: 25}})

// 2. 查找北京的年轻用户（年龄小于30）
db.users.find({city: "北京", age: {$lt: 30}})

// 3. 按年龄排序
db.users.find().sort({age: 1})

// 4. 统计各城市的用户数量
db.users.aggregate([
  {$group: {_id: "$city", count: {$sum: 1}}}
])
```

### 练习2：博客系统
```javascript
// 创建博客集合
use blogSystem

// 插入博客文章
db.posts.insertMany([
  {
    title: "MongoDB 入门指南",
    content: "MongoDB 是一个强大的 NoSQL 数据库...",
    author: "张三",
    tags: ["MongoDB", "数据库", "NoSQL"],
    publishedAt: new Date(),
    views: 150,
    likes: 25
  },
  {
    title: "Node.js 开发实践",
    content: "Node.js 是一个基于 Chrome V8 引擎的 JavaScript 运行时...",
    author: "李四",
    tags: ["Node.js", "JavaScript", "后端"],
    publishedAt: new Date(),
    views: 89,
    likes: 12
  }
])

// 创建索引
db.posts.createIndex({title: "text", content: "text"})
db.posts.createIndex({author: 1})
db.posts.createIndex({publishedAt: -1})
db.posts.createIndex({views: -1})

// 全文搜索
db.posts.find({$text: {$search: "MongoDB"}})

// 热门文章（按浏览量排序）
db.posts.find().sort({views: -1}).limit(5)
```



### 常用资源
- [MongoDB 官方文档](https://docs.mongodb.com/)
- [MongoDB 大学免费课程](https://university.mongodb.com/)
- [MongoDB 社区论坛](https://community.mongodb.com/)

---

