---
title: ElasticSearch基础
main_color: "#229ab2ff"
categories: ElasticSearch
tags:
  - ElasticSearch
cover: https://free.picui.cn/free/2026/03/28/69c74d2a3cbb9.png
---

# ElasticSearch基础学习指南

## 第一阶段：基础入门

### 1. 了解核心概念

#### 1.1 倒排索引（Inverted Index）
倒排索引是Elasticsearch的核心技术，也是其快速搜索的秘密武器。

**传统正向索引 vs 倒排索引：**
- **正向索引**：文档ID → 文档内容
- **倒排索引**：关键词 → 文档ID列表

**示例：**
```
文档1：Elasticsearch is a search engine
文档2：Elasticsearch is distributed
文档3：Search engine is powerful

倒排索引：
Elasticsearch → [文档1, 文档2]
search → [文档1, 文档3]
engine → [文档1, 文档3]
distributed → [文档2]
powerful → [文档3]
```

**优势：**
- 快速定位包含特定词汇的文档
- 支持复杂的全文搜索
- 高效的聚合操作

#### 1.2 文档（Document）
文档是Elasticsearch中的基本数据单元，类似于关系数据库中的一行记录。

**特点：**
- 以JSON格式存储
- 每个文档都有唯一的ID
- 包含多个字段（field）
- 支持嵌套结构

**示例：**
```json
{
  "_id": "1",
  "_index": "users",
  "_source": {
    "name": "张三",
    "age": 25,
    "email": "zhangsan@example.com",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### 1.3 索引（Index）
索引是存储同类文档的逻辑空间，类似于关系数据库中的表。

**特点：**
- 一个索引包含多个文档
- 每个索引有独立的映射（mapping）
- 支持分片和副本
- 可以设置不同的设置（settings）

**命名规范：**
- 小写字母
- 不能包含特殊字符（除了连字符和下划线）
- 不能以连字符、加号或点开头

#### 1.4 类型（Type）
在Elasticsearch 7.x版本后，类型概念已被废弃。在8.x版本中完全移除。

**历史背景：**
- 早期版本：索引 → 类型 → 文档
- 7.x版本：索引 → 文档（类型默认为_doc）
- 8.x版本：完全移除类型概念

#### 1.5 分片（Shard）与副本（Replica）

**分片（Shard）：**
- 索引被分割成多个分片
- 每个分片是一个独立的Lucene索引
- 支持水平扩展
- 提高并发处理能力

**副本（Replica）：**
- 分片的备份
- 提供高可用性
- 提高读取性能
- 支持负载均衡

**示例配置：**
```json
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  }
}
```

#### 1.6 集群（Cluster）与节点（Node）

**集群（Cluster）：**
- 一个或多个节点的集合
- 共享相同的集群名称
- 提供分布式搜索和分析能力

**节点（Node）：**
- 集群中的单个服务器
- 存储数据并参与索引和搜索
- 有不同的角色类型

**节点类型：**
- **主节点（Master Node）**：管理集群状态
- **数据节点（Data Node）**：存储和索引数据
- **协调节点（Coordinating Node）**：处理客户端请求
- **摄取节点（Ingest Node）**：预处理文档

### 2. 环境搭建与部署

#### 2.1 安装Elasticsearch

**系统要求：**
- Java 8或更高版本
- 至少2GB内存
- 足够的磁盘空间

**下载安装：**
```bash
# 下载Elasticsearch
wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-8.11.0-linux-x86_64.tar.gz

# 解压
tar -xzf elasticsearch-8.11.0-linux-x86_64.tar.gz
cd elasticsearch-8.11.0

# 启动
./bin/elasticsearch
```

**Docker安装（推荐）：**
```bash
# 拉取镜像
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.11.0

# 运行容器
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0
```

#### 2.2 安装Kibana

**下载安装：**
```bash
# 下载Kibana
wget https://artifacts.elastic.co/downloads/kibana/kibana-8.11.0-linux-x86_64.tar.gz

# 解压
tar -xzf kibana-8.11.0-linux-x86_64.tar.gz
cd kibana-8.11.0

# 启动
./bin/kibana
```

**Docker安装：**
```bash
# 拉取镜像
docker pull docker.elastic.co/kibana/kibana:8.11.0

# 运行容器
docker run -d \
  --name kibana \
  -p 5601:5601 \
  -e "ELASTICSEARCH_HOSTS=http://elasticsearch:9200" \
  docker.elastic.co/kibana/kibana:8.11.0
```

#### 2.3 Docker Compose快速搭建

创建`docker-compose.yml`文件：
```yaml
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - elastic

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - elastic

volumes:
  elasticsearch_data:

networks:
  elastic:
    driver: bridge
```

启动服务：
```bash
docker-compose up -d
```

#### 2.4 安全配置

**8.x版本默认安全配置：**
```yaml
# elasticsearch.yml
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: true
xpack.security.http.ssl.enabled: true
```

**创建用户：**
```bash
# 设置elastic用户密码
./bin/elasticsearch-setup-passwords interactive

# 或自动生成
./bin/elasticsearch-setup-passwords auto
```

### 3. RESTful API操作

#### 3.1 基本CRUD操作

**创建索引：**
```bash
# 创建索引
PUT /users
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  }
}

# 创建索引并指定映射
PUT /products
{
  "settings": {
    "number_of_shards": 3,
    "number_of_replicas": 1
  },
  "mappings": {
    "properties": {
      "name": {
        "type": "text"
      },
      "price": {
        "type": "float"
      },
      "created_at": {
        "type": "date"
      }
    }
  }
}
```

**索引文档：**
```bash
# 自动生成ID
POST /users/_doc
{
  "name": "张三",
  "age": 25,
  "email": "zhangsan@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}

# 指定ID
PUT /users/_doc/1
{
  "name": "李四",
  "age": 30,
  "email": "lisi@example.com",
  "created_at": "2024-01-02T00:00:00Z"
}
```

**获取文档：**
```bash
# 获取单个文档
GET /users/_doc/1

# 获取多个文档
GET /users/_mget
{
  "ids": ["1", "2", "3"]
}

# 检查文档是否存在
HEAD /users/_doc/1
```

**更新文档：**
```bash
# 完整更新
PUT /users/_doc/1
{
  "name": "李四",
  "age": 31,
  "email": "lisi@example.com",
  "created_at": "2024-01-02T00:00:00Z"
}

# 部分更新
POST /users/_update/1
{
  "doc": {
    "age": 31
  }
}

# 脚本更新
POST /users/_update/1
{
  "script": {
    "source": "ctx._source.age += 1"
  }
}
```

**删除文档：**
```bash
# 删除单个文档
DELETE /users/_doc/1

# 删除索引
DELETE /users
```

#### 3.2 批量操作（Bulk API）

**批量索引：**
```bash
POST /_bulk
{"index": {"_index": "users", "_id": "1"}}
{"name": "张三", "age": 25, "email": "zhangsan@example.com"}
{"index": {"_index": "users", "_id": "2"}}
{"name": "李四", "age": 30, "email": "lisi@example.com"}
{"index": {"_index": "users", "_id": "3"}}
{"name": "王五", "age": 28, "email": "wangwu@example.com"}
```

**批量更新：**
```bash
POST /_bulk
{"update": {"_index": "users", "_id": "1"}}
{"doc": {"age": 26}}
{"update": {"_index": "users", "_id": "2"}}
{"doc": {"age": 31}}
```

**批量删除：**
```bash
POST /_bulk
{"delete": {"_index": "users", "_id": "1"}}
{"delete": {"_index": "users", "_id": "2"}}
```

#### 3.3 索引管理

**查看索引信息：**
```bash
# 查看所有索引
GET /_cat/indices?v

# 查看特定索引
GET /users

# 查看索引设置
GET /users/_settings

# 查看索引映射
GET /users/_mapping
```

**更新索引设置：**
```bash
# 更新副本数
PUT /users/_settings
{
  "index": {
    "number_of_replicas": 2
  }
}
```

**索引别名：**
```bash
# 创建别名
POST /_aliases
{
  "actions": [
    {
      "add": {
        "index": "users",
        "alias": "user_alias"
      }
    }
  ]
}

# 使用别名查询
GET /user_alias/_search
```

#### 3.4 映射（Mapping）

**字段类型：**

**文本类型：**
- `text`：全文搜索字段，会被分析器处理
- `keyword`：精确匹配字段，不会被分析

**数值类型：**
- `long`：64位整数
- `integer`：32位整数
- `short`：16位整数
- `byte`：8位整数
- `double`：64位浮点数
- `float`：32位浮点数
- `half_float`：16位浮点数
- `scaled_float`：缩放浮点数

**日期类型：**
- `date`：日期时间

**其他类型：**
- `boolean`：布尔值
- `binary`：二进制数据
- `geo_point`：地理位置
- `geo_shape`：地理形状
- `ip`：IP地址

**映射示例：**
```json
PUT /products
{
  "mappings": {
    "properties": {
      "name": {
        "type": "text",
        "analyzer": "standard",
        "search_analyzer": "standard"
      },
      "category": {
        "type": "keyword"
      },
      "price": {
        "type": "float"
      },
      "description": {
        "type": "text",
        "analyzer": "ik_max_word"
      },
      "tags": {
        "type": "keyword"
      },
      "created_at": {
        "type": "date",
        "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
      },
      "location": {
        "type": "geo_point"
      }
    }
  }
}
```

#### 3.5 Dynamic Mapping vs Explicit Mapping

**Dynamic Mapping：**
- Elasticsearch自动推断字段类型
- 适合快速原型开发
- 可能导致性能问题

**Explicit Mapping：**
- 手动定义字段类型
- 更好的性能和可控性
- 生产环境推荐使用

**Dynamic Mapping规则：**
```json
{
  "mappings": {
    "dynamic": "strict",  // strict, true, false
    "properties": {
      // 字段定义
    }
  }
}
```

**Dynamic设置：**
- `true`：新字段自动添加到映射
- `false`：新字段被忽略
- `strict`：新字段抛出异常




