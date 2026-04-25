---
title: ElasticSearch查询
main_color: "#229ab2ff"
categories: ElasticSearch
tags:
  - ElasticSearch
cover: https://free.picui.cn/free/2026/03/28/69c74d2a3cbb9.png
---

# ElasticSearch查询详解

## 第二阶段：核心功能与查询

### 1. 搜索基础

#### 1.1 Query DSL
Query DSL（Domain Specific Language）是ElasticSearch的查询语言，使用JSON格式构建查询。

**基本结构：**
```json
{
  "query": {
    "查询类型": {
      "字段名": "查询值"
    }
  }
}
```

**查询上下文 vs 过滤上下文：**
- **查询上下文**：计算相关性得分，影响排序
- **过滤上下文**：只判断是否匹配，不计算得分，性能更好

### 2. 全文搜索

#### 2.1 match 查询（标准全文检索）
最基本的全文搜索查询，会对查询文本进行分词处理。

```json
{
  "query": {
    "match": {
      "title": "elasticsearch 教程"
    }
  }
}
```

**特点：**
- 自动分词处理
- 支持模糊匹配
- 计算相关性得分
- 支持operator参数（and/or）

```json
{
  "query": {
    "match": {
      "title": {
        "query": "elasticsearch 教程",
        "operator": "and"
      }
    }
  }
}
```

#### 2.2 match_phrase（短语匹配）
精确匹配短语，要求词条按顺序出现且位置相邻。

```json
{
  "query": {
    "match_phrase": {
      "title": "elasticsearch 教程"
    }
  }
}
```

**slop参数：** 允许词条之间的间隔
```json
{
  "query": {
    "match_phrase": {
      "title": {
        "query": "elasticsearch 教程",
        "slop": 2
      }
    }
  }
}
```

#### 2.3 multi_match（多字段搜索）
在多个字段中搜索相同的查询文本。

```json
{
  "query": {
    "multi_match": {
      "query": "elasticsearch",
      "fields": ["title", "content", "description"]
    }
  }
}
```

**类型选项：**
- `best_fields`：最佳字段匹配（默认）
- `most_fields`：最多字段匹配
- `cross_fields`：跨字段匹配
- `phrase`：短语匹配
- `phrase_prefix`：短语前缀匹配

```json
{
  "query": {
    "multi_match": {
      "query": "elasticsearch",
      "fields": ["title^2", "content"],
      "type": "best_fields",
      "tie_breaker": 0.3
    }
  }
}
```

### 3. 精确查询

#### 3.1 term 查询（关键词精确匹配）
精确匹配字段值，不进行分词处理。

```json
{
  "query": {
    "term": {
      "status": "active"
    }
  }
}
```

**注意：** term查询不会对查询值进行分词，适用于keyword类型字段。

#### 3.2 terms 查询（多值精确匹配）
匹配多个精确值中的任意一个。

```json
{
  "query": {
    "terms": {
      "category": ["技术", "编程", "数据库"]
    }
  }
}
```

#### 3.3 range 查询（范围查询）
查询字段值在指定范围内的文档。

```json
{
  "query": {
    "range": {
      "price": {
        "gte": 10,
        "lte": 100
      }
    }
  }
}
```

**范围操作符：**
- `gt`：大于
- `gte`：大于等于
- `lt`：小于
- `lte`：小于等于

**日期范围查询：**
```json
{
  "query": {
    "range": {
      "created_at": {
        "gte": "2024-01-01",
        "lte": "2024-12-31",
        "format": "yyyy-MM-dd"
      }
    }
  }
}
```

### 4. 复合查询

#### 4.1 bool 查询（must, should, must_not, filter）
构建复杂查询的核心，组合多个查询条件。

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "title": "elasticsearch" } }
      ],
      "should": [
        { "match": { "content": "教程" } }
      ],
      "must_not": [
        { "term": { "status": "deleted" } }
      ],
      "filter": [
        { "range": { "price": { "gte": 10 } } }
      ]
    }
  }
}
```

**各子句说明：**
- **must**：必须匹配，贡献相关性得分
- **should**：应该匹配，贡献相关性得分
- **must_not**：必须不匹配，不贡献得分
- **filter**：必须匹配，不贡献得分，性能更好

**minimum_should_match：**
```json
{
  "query": {
    "bool": {
      "should": [
        { "match": { "title": "elasticsearch" } },
        { "match": { "content": "教程" } },
        { "match": { "tags": "搜索" } }
      ],
      "minimum_should_match": 2
    }
  }
}
```

### 5. 高亮（Highlighting）
为搜索结果中的匹配文本添加高亮标记。

```json
{
  "query": {
    "match": {
      "content": "elasticsearch"
    }
  },
  "highlight": {
    "fields": {
      "content": {
        "pre_tags": ["<em>"],
        "post_tags": ["</em>"],
        "fragment_size": 150,
        "number_of_fragments": 3
      }
    }
  }
}
```

**高亮参数：**
- `pre_tags/post_tags`：高亮标签
- `fragment_size`：片段大小
- `number_of_fragments`：片段数量
- `fragmenter`：片段分割方式

### 6. 分析器（Analyzer）

#### 6.1 分词过程
分析器由三个组件组成：
1. **Character Filter**：字符过滤器，处理原始文本
2. **Tokenizer**：分词器，将文本分割成词条
3. **Token Filter**：词条过滤器，处理词条

**处理流程：** `原始文本 → Character Filter → Tokenizer → Token Filter → 词条`

#### 6.2 常用内置分析器

**standard 分析器：**
- 按空格和标点符号分词
- 小写化处理
- 删除停用词

**whitespace 分析器：**
- 仅按空格分词
- 不进行小写化

**keyword 分析器：**
- 不进行分词
- 将整个文本作为一个词条

**simple 分析器：**
- 按非字母字符分词
- 小写化处理

#### 6.3 中文分词：IK Analyzer
专门为中文设计的分词器，支持智能分词和细粒度分词。

**安装配置：**
```bash
# 下载IK分词器
wget https://github.com/medcl/elasticsearch-analysis-ik/releases/download/v7.17.0/elasticsearch-analysis-ik-7.17.0.zip
# 解压到plugins目录
unzip elasticsearch-analysis-ik-7.17.0.zip -d /path/to/elasticsearch/plugins/
```

**使用示例：**
```json
{
  "analyzer": "ik_max_word",
  "text": "中华人民共和国"
}
```

**IK分析器类型：**
- `ik_smart`：智能分词
- `ik_max_word`：最细粒度分词

#### 6.4 自定义分析器
根据业务需求创建自定义分析器。

```json
{
  "settings": {
    "analysis": {
      "analyzer": {
        "my_analyzer": {
          "type": "custom",
          "char_filter": ["html_strip"],
          "tokenizer": "standard",
          "filter": ["lowercase", "stop"]
        }
      }
    }
  }
}
```

### 7. 聚合（Aggregation）

#### 7.1 Metrics Aggregation（指标聚合）
计算数值型字段的统计指标。

**avg（平均值）：**
```json
{
  "aggs": {
    "avg_price": {
      "avg": {
        "field": "price"
      }
    }
  }
}
```

**sum（求和）：**
```json
{
  "aggs": {
    "total_sales": {
      "sum": {
        "field": "sales_amount"
      }
    }
  }
}
```

**min/max（最小值/最大值）：**
```json
{
  "aggs": {
    "price_stats": {
      "stats": {
        "field": "price"
      }
    }
  }
}
```

**cardinality（基数统计）：**
```json
{
  "aggs": {
    "unique_users": {
      "cardinality": {
        "field": "user_id"
      }
    }
  }
}
```

#### 7.2 Bucket Aggregation（分桶聚合）
将文档分组到不同的桶中。

**terms（词条分桶）：**
```json
{
  "aggs": {
    "categories": {
      "terms": {
        "field": "category",
        "size": 10
      }
    }
  }
}
```

**date_histogram（日期直方图）：**
```json
{
  "aggs": {
    "sales_over_time": {
      "date_histogram": {
        "field": "created_at",
        "calendar_interval": "1d"
      }
    }
  }
}
```

**range（范围分桶）：**
```json
{
  "aggs": {
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [
          { "to": 50 },
          { "from": 50, "to": 100 },
          { "from": 100 }
        ]
      }
    }
  }
}
```

#### 7.3 Pipeline Aggregation（管道聚合）
对聚合结果进行二次计算。

**avg_bucket（桶平均值）：**
```json
{
  "aggs": {
    "sales_per_month": {
      "date_histogram": {
        "field": "created_at",
        "calendar_interval": "1M"
      },
      "aggs": {
        "total_sales": {
          "sum": {
            "field": "sales_amount"
          }
        }
      }
    },
    "avg_monthly_sales": {
      "avg_bucket": {
        "buckets_path": "sales_per_month>total_sales"
      }
    }
  }
}
```

#### 7.4 嵌套聚合
在桶聚合内部进行指标聚合。

```json
{
  "aggs": {
    "categories": {
      "terms": {
        "field": "category"
      },
      "aggs": {
        "avg_price": {
          "avg": {
            "field": "price"
          }
        },
        "total_sales": {
          "sum": {
            "field": "sales_amount"
          }
        }
      }
    }
  }
}
```

### 8. 实用查询技巧

#### 8.1 分页查询
```json
{
  "from": 0,
  "size": 10,
  "query": {
    "match_all": {}
  }
}
```

#### 8.2 排序
```json
{
  "query": {
    "match_all": {}
  },
  "sort": [
    { "price": { "order": "desc" } },
    { "_score": { "order": "desc" } }
  ]
}
```

#### 8.3 字段选择
```json
{
  "_source": ["title", "price", "category"],
  "query": {
    "match_all": {}
  }
}
```

#### 8.4 脚本查询
```json
{
  "query": {
    "script": {
      "script": {
        "source": "doc['price'].value * 1.1 > params.threshold",
        "params": {
          "threshold": 100
        }
      }
    }
  }
}
```

### 9. 性能优化建议

1. **合理使用filter上下文**：不需要计算得分的查询使用filter
2. **避免深度分页**：使用search_after代替from/size
3. **合理设置分片数**：避免过多分片影响性能
4. **使用索引别名**：便于索引管理和零停机切换
5. **合理设置refresh_interval**：平衡实时性和性能

### 10. 总结

ElasticSearch的查询功能非常强大，掌握这些核心概念和技巧对于构建高效的搜索系统至关重要：

- **Query DSL**是构建查询的基础
- **全文搜索**适用于文本内容检索
- **精确查询**适用于结构化数据
- **bool查询**是构建复杂查询的核心
- **分析器**决定了文本如何处理和索引
- **聚合**是数据分析的强大工具

聚合是数据分析的核心，务必熟练掌握。通过合理组合这些功能，可以构建出功能强大、性能优异的搜索和数据分析系统。