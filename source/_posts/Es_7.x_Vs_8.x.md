---
title: Es_7.x_Vs_8.x
main_color: "#229ab2ff"
categories: ElasticSearch
tags:
  - ElasticSearch
cover: https://free.picui.cn/free/2026/03/28/69c74d2a3cbb9.png
---

## 
Elasticsearch 7.x 跟 Elasticsearch 8.x 是如今最常使用的两个版本，在新项目上一般建议直接使用8.x，但是8.x需要jdk17以上支持、因此很多1.8的项目使用的多是7.x,在此对两个版本做一个详细的对比

# **Elasticsearch 7.x vs 8.x Java 客户端全面对比笔记**  
**—— `RestHighLevelClient` vs `elasticsearch-java`**

> **适用版本范围**：  
> - **ES 7.x**：7.0 ~ 7.17（`RestHighLevelClient` 已在 7.15+ 标记为 **deprecated**）  
> - **ES 8.x**：8.0+ 推荐使用新的 `elasticsearch-java` 客户端  
> - **当前时间**：2025年8月7日，建议新项目直接使用 8.x 客户端

---

## 📊 版本对比总览表

| 特性 | ES 7.x | ES 8.x | 影响程度 |
|------|--------|--------|----------|
| **Java 版本要求** | Java 8+ | **Java 17+** | 🔴 高 |
| **客户端状态** | ❌ 已废弃 | ✅ 官方推荐 | 🔴 高 |
| **API 风格** | 命令式 | 函数式 + Lambda | 🟡 中 |
| **类型安全** | 弱类型 | 强类型 + 泛型 | 🟢 低 |
| **POJO 映射** | 手动解析 | 自动映射 | 🟢 低 |
| **学习成本** | 低 | 中等 | 🟡 中 |
| **性能表现** | 良好 | 良好 | 🟢 低 |
| **社区支持** | 逐渐减少 | 活跃 | 🔴 高 |

---

## 🎯 实际使用场景分析

### 场景1：新项目启动
**推荐方案**：ES 8.x + `elasticsearch-java`
- ✅ 享受最新的功能和性能优化
- ✅ 长期维护支持
- ✅ 现代化的开发体验

### 场景2：现有 Java 8 项目
**推荐方案**：ES 7.x + `RestHighLevelClient`
- ⚠️ 无法升级 Java 版本时的临时方案
- ⚠️ 需要注意安全风险和功能限制

### 场景3：Spring Boot 项目
**推荐方案**：Spring Boot 3.x + ES 8.x
- ✅ 完美集成，开箱即用
- ✅ 自动配置和健康检查

---

## 一、核心背景

Elasticsearch 在 8.0 版本中**彻底重构了 Java 客户端**，推出了全新的官方 Java 客户端 `elasticsearch-java`，取代了 7.x 中使用的 `RestHighLevelClient`。

- `RestHighLevelClient` 被官方**弃用（deprecated）**，不再维护。
- 新客户端基于 **Java 17+**、**Jackson** 和 **gRPC-like 代码生成机制**，提供类型安全、DSL 友好的 API。
- 新客户端不再依赖 `transport` 或 `high-level-rest`，而是直接与 REST API 对齐。

### 🔄 迁移时间线
- **2021年10月**：ES 8.0 发布，引入新客户端
- **2022年**：Spring Data Elasticsearch 4.4+ 支持新客户端
- **2023年**：ES 7.x 进入维护模式
- **2024年**：ES 8.x 成为主流版本

---

## 二、依赖与模块对比

| 项目 | Elasticsearch 7.x (`RestHighLevelClient`) | Elasticsearch 8.x (`elasticsearch-java`) |
|------|-------------------------------------------|------------------------------------------|
| Maven 依赖 |  
```xml
<dependency>
    <groupId>org.elasticsearch.client</groupId>
    <artifactId>elasticsearch-rest-high-level-client</artifactId>
    <version>7.17.14</version>
</dependency>
```
|  
```xml
<dependency>
    <groupId>co.elastic.clients</groupId>
    <artifactId>elasticsearch-java</artifactId>
    <version>8.13.0</version>
</dependency>
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>2.15.2</version>
</dependency>
```
|
| 核心模块 | `elasticsearch` + `elasticsearch-rest-client` + `elasticsearch-rest-high-level-client` | `elasticsearch-java` + Jackson（必须显式引入） |
| 是否需要额外 HTTP 客户端 | 是（Apache `HttpClient`） | 是（通过 `RestClient` 底层） |
| Java 版本要求 | Java 8+ | **Java 17+**（最低要求） |

### 📦 完整的 Maven 依赖配置

#### ES 7.x 完整依赖
```xml
<dependencies>
    <!-- Elasticsearch 7.x 客户端 -->
    <dependency>
        <groupId>org.elasticsearch.client</groupId>
        <artifactId>elasticsearch-rest-high-level-client</artifactId>
        <version>7.17.14</version>
    </dependency>
    
    <!-- 底层 HTTP 客户端 -->
    <dependency>
        <groupId>org.apache.httpcomponents</groupId>
        <artifactId>httpclient</artifactId>
        <version>4.5.14</version>
    </dependency>
    
    <!-- JSON 处理 -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.15.2</version>
    </dependency>
    
    <!-- 日志框架 -->
    <dependency>
        <groupId>org.apache.logging.log4j</groupId>
        <artifactId>log4j-core</artifactId>
        <version>2.20.0</version>
    </dependency>
</dependencies>
```

#### ES 8.x 完整依赖
```xml
<dependencies>
    <!-- Elasticsearch 8.x 客户端 -->
    <dependency>
        <groupId>co.elastic.clients</groupId>
        <artifactId>elasticsearch-java</artifactId>
        <version>8.13.0</version>
    </dependency>
    
    <!-- 底层 REST 客户端 -->
    <dependency>
        <groupId>co.elastic.clients</groupId>
        <artifactId>elasticsearch-rest-client</artifactId>
        <version>8.13.0</version>
    </dependency>
    
    <!-- JSON 映射器（必须） -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.15.2</version>
    </dependency>
    
    <!-- 可选：Jackson 扩展 -->
    <dependency>
        <groupId>com.fasterxml.jackson.datatype</groupId>
        <artifactId>jackson-datatype-jsr310</artifactId>
        <version>2.15.2</version>
    </dependency>
    
    <!-- 日志框架 -->
    <dependency>
        <groupId>org.apache.logging.log4j</groupId>
        <artifactId>log4j-core</artifactId>
        <version>2.20.0</version>
    </dependency>
</dependencies>
```

### 🔧 Gradle 依赖配置

#### ES 7.x (Gradle)
```gradle
dependencies {
    implementation 'org.elasticsearch.client:elasticsearch-rest-high-level-client:7.17.14'
    implementation 'org.apache.httpcomponents:httpclient:4.5.14'
    implementation 'com.fasterxml.jackson.core:jackson-databind:2.15.2'
    implementation 'org.apache.logging.log4j:log4j-core:2.20.0'
}
```

#### ES 8.x (Gradle)
```gradle
dependencies {
    implementation 'co.elastic.clients:elasticsearch-java:8.13.0'
    implementation 'co.elastic.clients:elasticsearch-rest-client:8.13.0'
    implementation 'com.fasterxml.jackson.core:jackson-databind:2.15.2'
    implementation 'com.fasterxml.jackson.datatype:jackson-datatype-jsr310:2.15.2'
    implementation 'org.apache.logging.log4j:log4j-core:2.20.0'
}
```

### ⚠️ 版本兼容性注意事项

| ES 集群版本 | 7.x 客户端 | 8.x 客户端 | 推荐方案 |
|-------------|------------|------------|----------|
| ES 7.0-7.16 | ✅ 完全兼容 | ⚠️ 部分功能不可用 | 7.x 客户端 |
| ES 7.17+ | ✅ 完全兼容 | ✅ 基本兼容 | 8.x 客户端 |
| ES 8.0+ | ⚠️ 部分功能不可用 | ✅ 完全兼容 | 8.x 客户端 |

> ⚠️ 注意：8.x 客户端**最低要求 Java 17**，这是重大变化。

---

## 三、客户端创建方式对比

### 1. ES 7.x：`RestHighLevelClient`

#### 基础配置
```java
RestHighLevelClient client = new RestHighLevelClient(
    RestClient.builder(
        new HttpHost("localhost", 9200, "http")
    )
);
```

#### 高级配置（SSL + 认证 + 连接池）
```java
import org.apache.http.auth.AuthScope;
import org.apache.http.auth.UsernamePasswordCredentials;
import org.apache.http.client.CredentialsProvider;
import org.apache.http.impl.client.BasicCredentialsProvider;
import org.apache.http.ssl.SSLContextBuilder;
import org.apache.http.ssl.SSLContexts;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestHighLevelClient;

// 1. 创建认证提供者
final CredentialsProvider credentialsProvider = new BasicCredentialsProvider();
credentialsProvider.setCredentials(AuthScope.ANY, 
    new UsernamePasswordCredentials("elastic", "password"));

// 2. 创建 SSL 上下文
SSLContextBuilder sslBuilder = SSLContexts.custom()
    .loadTrustMaterial(new File("path/to/ca.crt"), "password".toCharArray());

// 3. 创建 HTTP 客户端配置
HttpClientConfigCallback httpClientConfigCallback = httpClientBuilder -> {
    httpClientBuilder.setDefaultCredentialsProvider(credentialsProvider);
    httpClientBuilder.setSSLContext(sslBuilder.build());
    
    // 连接池配置
    httpClientBuilder.setMaxConnTotal(100);
    httpClientBuilder.setMaxConnPerRoute(20);
    
    // 超时配置
    httpClientBuilder.setConnectionTimeoutMillis(5000);
    httpClientBuilder.setSocketTimeoutMillis(60000);
    
    return httpClientBuilder;
};

// 4. 创建 REST 客户端
RestClient restClient = RestClient.builder(
    new HttpHost("localhost", 9200, "https")
)
.setHttpClientConfigCallback(httpClientConfigCallback)
.setRequestConfigCallback(requestConfigBuilder -> {
    requestConfigBuilder.setConnectTimeout(5000);
    requestConfigBuilder.setSocketTimeout(60000);
    requestConfigBuilder.setConnectionRequestTimeout(0);
    return requestConfigBuilder;
})
.build();

// 5. 创建高级客户端
RestHighLevelClient client = new RestHighLevelClient(restClient);
```

### 2. ES 8.x：`ElasticsearchClient`（新客户端）

#### 基础配置
```java
// 创建低层 REST 客户端
RestClient restClient = RestClient.builder(
    new HttpHost("localhost", 9200, "http")
).build();

// 创建 JSON 工厂（Jackson）
JacksonJsonpMapper jsonpMapper = new JacksonJsonpMapper();

// 创建传输层
RestClientTransport transport = new RestClientTransport(restClient, jsonpMapper);

// 创建类型安全的客户端
ElasticsearchClient client = new ElasticsearchClient(transport);
```

#### 高级配置（SSL + 认证 + 连接池）
```java
import co.elastic.clients.elasticsearch.ElasticsearchClient;
import co.elastic.clients.json.jackson.JacksonJsonpMapper;
import co.elastic.clients.transport.rest_client.RestClientTransport;
import org.apache.http.auth.AuthScope;
import org.apache.http.auth.UsernamePasswordCredentials;
import org.apache.http.client.CredentialsProvider;
import org.apache.http.impl.client.BasicCredentialsProvider;
import org.apache.http.ssl.SSLContextBuilder;
import org.elasticsearch.client.RestClient;
import org.elasticsearch.client.RestClientBuilder;

// 1. 创建认证提供者
final CredentialsProvider credentialsProvider = new BasicCredentialsProvider();
credentialsProvider.setCredentials(AuthScope.ANY, 
    new UsernamePasswordCredentials("elastic", "password"));

// 2. 创建 SSL 上下文
SSLContextBuilder sslBuilder = SSLContextBuilder.create()
    .loadTrustMaterial(new File("path/to/ca.crt"), "password".toCharArray());

// 3. 创建 REST 客户端构建器
RestClientBuilder builder = RestClient.builder(
    new HttpHost("localhost", 9200, "https")
);

// 4. 配置 HTTP 客户端
builder.setHttpClientConfigCallback(httpClientBuilder -> {
    httpClientBuilder.setDefaultCredentialsProvider(credentialsProvider);
    httpClientBuilder.setSSLContext(sslBuilder.build());
    
    // 连接池配置
    httpClientBuilder.setMaxConnTotal(100);
    httpClientBuilder.setMaxConnPerRoute(20);
    
    // 超时配置
    httpClientBuilder.setConnectionTimeoutMillis(5000);
    httpClientBuilder.setSocketTimeoutMillis(60000);
    
    return httpClientBuilder;
});

// 5. 配置请求参数
builder.setRequestConfigCallback(requestConfigBuilder -> {
    requestConfigBuilder.setConnectTimeout(5000);
    requestConfigBuilder.setSocketTimeout(60000);
    requestConfigBuilder.setConnectionRequestTimeout(0);
    return requestConfigBuilder;
});

// 6. 创建 REST 客户端
RestClient restClient = builder.build();

// 7. 创建 JSON 映射器（支持更多配置）
ObjectMapper mapper = new ObjectMapper();
mapper.registerModule(new JavaTimeModule());
mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

JacksonJsonpMapper jsonpMapper = new JacksonJsonpMapper(mapper);

// 8. 创建传输层
RestClientTransport transport = new RestClientTransport(restClient, jsonpMapper);

// 9. 创建类型安全的客户端
ElasticsearchClient client = new ElasticsearchClient(transport);
```

### 🔧 客户端配置工具类

#### ES 7.x 配置工具类
```java
public class Elasticsearch7Config {
    
    public static RestHighLevelClient createClient(String host, int port, 
                                                  String username, String password,
                                                  boolean useSSL) {
        try {
            // 认证配置
            final CredentialsProvider credentialsProvider = new BasicCredentialsProvider();
            if (username != null && password != null) {
                credentialsProvider.setCredentials(AuthScope.ANY, 
                    new UsernamePasswordCredentials(username, password));
            }
            
            // 协议选择
            String scheme = useSSL ? "https" : "http";
            
            // 创建客户端
            RestClient restClient = RestClient.builder(
                new HttpHost(host, port, scheme)
            )
            .setHttpClientConfigCallback(httpClientBuilder -> {
                httpClientBuilder.setDefaultCredentialsProvider(credentialsProvider);
                
                if (useSSL) {
                    // SSL 配置
                    SSLContextBuilder sslBuilder = SSLContextBuilder.create();
                    httpClientBuilder.setSSLContext(sslBuilder.build());
                }
                
                // 连接池配置
                httpClientBuilder.setMaxConnTotal(100);
                httpClientBuilder.setMaxConnPerRoute(20);
                
                return httpClientBuilder;
            })
            .build();
            
            return new RestHighLevelClient(restClient);
            
        } catch (Exception e) {
            throw new RuntimeException("Failed to create Elasticsearch client", e);
        }
    }
}
```

#### ES 8.x 配置工具类
```java
public class Elasticsearch8Config {
    
    public static ElasticsearchClient createClient(String host, int port, 
                                                  String username, String password,
                                                  boolean useSSL) {
        try {
            // 认证配置
            final CredentialsProvider credentialsProvider = new BasicCredentialsProvider();
            if (username != null && password != null) {
                credentialsProvider.setCredentials(AuthScope.ANY, 
                    new UsernamePasswordCredentials(username, password));
            }
            
            // 协议选择
            String scheme = useSSL ? "https" : "http";
            
            // 创建 REST 客户端
            RestClientBuilder builder = RestClient.builder(
                new HttpHost(host, port, scheme)
            );
            
            builder.setHttpClientConfigCallback(httpClientBuilder -> {
                httpClientBuilder.setDefaultCredentialsProvider(credentialsProvider);
                
                if (useSSL) {
                    SSLContextBuilder sslBuilder = SSLContextBuilder.create();
                    httpClientBuilder.setSSLContext(sslBuilder.build());
                }
                
                // 连接池配置
                httpClientBuilder.setMaxConnTotal(100);
                httpClientBuilder.setMaxConnPerRoute(20);
                
                return httpClientBuilder;
            });
            
            RestClient restClient = builder.build();
            
            // 创建 JSON 映射器
            ObjectMapper mapper = new ObjectMapper();
            mapper.registerModule(new JavaTimeModule());
            mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
            
            JacksonJsonpMapper jsonpMapper = new JacksonJsonpMapper(mapper);
            
            // 创建传输层和客户端
            RestClientTransport transport = new RestClientTransport(restClient, jsonpMapper);
            return new ElasticsearchClient(transport);
            
        } catch (Exception e) {
            throw new RuntimeException("Failed to create Elasticsearch client", e);
        }
    }
}
```

### 📊 配置对比总结

| 配置项 | ES 7.x | ES 8.x | 说明 |
|--------|--------|--------|------|
| **基础创建** | 简单，一步到位 | 分层创建，更灵活 | 8.x 提供更好的可插拔性 |
| **SSL 配置** | 通过 HttpClient | 通过 HttpClient | 配置方式相同 |
| **认证配置** | CredentialsProvider | CredentialsProvider | 配置方式相同 |
| **连接池** | HttpClient 配置 | HttpClient 配置 | 配置方式相同 |
| **JSON 映射** | 可选配置 | 必须配置 | 8.x 强制要求 |
| **超时配置** | RequestConfig | RequestConfig | 配置方式相同 |

> ✅ 优点：分层清晰，可插拔 JSON 映射器（如 Jackson、Gson）  
> ⚠️ 注意：必须手动创建 `JacksonJsonpMapper` 和 `RestClientTransport`

---

## 四、API 风格与代码可读性对比

| 特性 | ES 7.x | ES 8.x |
|------|--------|--------|
| **API 风格** | 命令式（Imperative） | 函数式 + 构建器（Fluent Lambda） |
| **DSL 构建方式** | 使用 `SearchSourceBuilder`、`QueryBuilders` 等静态方法 | 使用 Lambda 表达式，链式调用 |
| **类型安全** | ❌ 弱类型，返回 `Map<String, Object>` | ✅ 强类型，支持泛型和 POJO 映射 |
| **代码可读性** | 一般，嵌套多 | 高，接近自然语言 |

### 📝 详细代码示例对比

#### 1. 索引操作对比

##### ES 7.x 创建索引
```java
// 创建索引请求
CreateIndexRequest request = new CreateIndexRequest("products");
request.settings(Settings.builder()
    .put("index.number_of_shards", 3)
    .put("index.number_of_replicas", 1)
);

// 设置映射
Map<String, Object> properties = new HashMap<>();
properties.put("name", Map.of("type", "text"));
properties.put("price", Map.of("type", "double"));
properties.put("category", Map.of("type", "keyword"));
properties.put("created_at", Map.of("type", "date"));

Map<String, Object> mapping = Map.of("properties", properties);
request.mapping(mapping);

// 执行创建
CreateIndexResponse response = client.indices().create(request, RequestOptions.DEFAULT);
boolean acknowledged = response.isAcknowledged();
```

##### ES 8.x 创建索引
```java
// 创建索引（简洁版本）
client.indices().create(c -> c
    .index("products")
    .settings(s -> s
        .numberOfShards("3")
        .numberOfReplicas("1")
    )
    .mappings(m -> m
        .properties("name", p -> p.text(t -> t))
        .properties("price", p -> p.double_(d -> d))
        .properties("category", p -> p.keyword(k -> k))
        .properties("created_at", p -> p.date(d -> d))
    )
);
```

#### 2. 文档操作对比

##### ES 7.x 文档操作
```java
// 索引文档
IndexRequest indexRequest = new IndexRequest("products")
    .id("1")
    .source(Map.of(
        "name", "iPhone 15",
        "price", 999.99,
        "category", "electronics",
        "created_at", new Date()
    ));

IndexResponse response = client.index(indexRequest, RequestOptions.DEFAULT);
String documentId = response.getId();

// 获取文档
GetRequest getRequest = new GetRequest("products", "1");
GetResponse getResponse = client.get(getRequest, RequestOptions.DEFAULT);
Map<String, Object> source = getResponse.getSourceAsMap();

// 更新文档
UpdateRequest updateRequest = new UpdateRequest("products", "1")
    .doc(Map.of("price", 899.99));
UpdateResponse updateResponse = client.update(updateRequest, RequestOptions.DEFAULT);

// 删除文档
DeleteRequest deleteRequest = new DeleteRequest("products", "1");
DeleteResponse deleteResponse = client.delete(deleteRequest, RequestOptions.DEFAULT);
```

##### ES 8.x 文档操作
```java
// 索引文档
Product product = new Product("iPhone 15", 999.99, "electronics", new Date());
client.index(i -> i
    .index("products")
    .id("1")
    .document(product)
);

// 获取文档
GetResponse<Product> getResponse = client.get(g -> g
    .index("products")
    .id("1"),
    Product.class
);
Product retrievedProduct = getResponse.source();

// 更新文档
client.update(u -> u
    .index("products")
    .id("1")
    .doc(Map.of("price", 899.99)),
    Product.class
);

// 删除文档
client.delete(d -> d
    .index("products")
    .id("1")
);
```

#### 3. 复杂查询对比

##### ES 7.x 复杂查询
```java
SearchRequest request = new SearchRequest("products");
SearchSourceBuilder source = new SearchSourceBuilder();

// 构建查询
BoolQueryBuilder boolQuery = QueryBuilders.boolQuery();

// 匹配查询
boolQuery.must(QueryBuilders.matchQuery("name", "phone"));

// 范围查询
boolQuery.filter(QueryBuilders.rangeQuery("price")
    .gte(100)
    .lte(1000));

// 分类过滤
boolQuery.filter(QueryBuilders.termsQuery("category", "electronics", "phones"));

// 排序
source.sort("price", SortOrder.ASC);
source.sort("created_at", SortOrder.DESC);

// 分页
source.from(0);
source.size(10);

// 聚合
source.aggregation(AggregationBuilders
    .terms("category_agg")
    .field("category")
    .size(10));

source.aggregation(AggregationBuilders
    .avg("avg_price")
    .field("price"));

source.aggregation(AggregationBuilders
    .histogram("price_histogram")
    .field("price")
    .interval(100.0));

source.query(boolQuery);
request.source(source);

// 执行查询
SearchResponse response = client.search(request, RequestOptions.DEFAULT);

// 解析结果
SearchHits hits = response.getHits();
for (SearchHit hit : hits.getHits()) {
    Map<String, Object> sourceAsMap = hit.getSourceAsMap();
    // 处理文档...
}

// 解析聚合
Aggregations aggregations = response.getAggregations();
Terms categoryAgg = aggregations.get("category_agg");
for (Terms.Bucket bucket : categoryAgg.getBuckets()) {
    String category = bucket.getKeyAsString();
    long count = bucket.getDocCount();
    // 处理聚合结果...
}
```

##### ES 8.x 复杂查询
```java
SearchResponse<Product> response = client.search(s -> s
    .index("products")
    .query(q -> q
        .bool(b -> b
            .must(m -> m.match(t -> t.field("name").query("phone")))
            .filter(f -> f.range(r -> r
                .field("price")
                .gte(JsonData.of(100))
                .lte(JsonData.of(1000))
            ))
            .filter(f -> f.terms(t -> t
                .field("category")
                .terms(v -> v.value(Arrays.asList("electronics", "phones")))
            ))
        )
    )
    .sort(sort -> sort
        .field(f -> f.field("price").order(SortOrder.Asc))
        .field(f -> f.field("created_at").order(SortOrder.Desc))
    )
    .from(0)
    .size(10)
    .aggregations("category_agg", a -> a
        .terms(t -> t.field("category").size(10))
    )
    .aggregations("avg_price", a -> a
        .avg(avg -> avg.field("price"))
    )
    .aggregations("price_histogram", a -> a
        .histogram(h -> h.field("price").interval(100.0))
    ),
    Product.class
);

// 处理结果
List<Product> products = response.hits().hits().stream()
    .map(hit -> hit.source())
    .collect(Collectors.toList());

// 处理聚合
Map<String, Aggregate> aggregations = response.aggregations();
TermsAggregate categoryAgg = aggregations.get("category_agg").sterms();
for (StringTermsBucket bucket : categoryAgg.buckets().array()) {
    String category = bucket.key().stringValue();
    long count = bucket.docCount();
    // 处理聚合结果...
}
```

#### 4. 批量操作对比

##### ES 7.x 批量操作
```java
BulkRequest bulkRequest = new BulkRequest();

// 添加索引操作
bulkRequest.add(new IndexRequest("products")
    .id("1")
    .source(Map.of("name", "iPhone 15", "price", 999.99)));

// 添加更新操作
bulkRequest.add(new UpdateRequest("products", "2")
    .doc(Map.of("price", 899.99)));

// 添加删除操作
bulkRequest.add(new DeleteRequest("products", "3"));

// 执行批量操作
BulkResponse bulkResponse = client.bulk(bulkRequest, RequestOptions.DEFAULT);

// 检查结果
if (bulkResponse.hasFailures()) {
    for (BulkItemResponse item : bulkResponse.getItems()) {
        if (item.isFailed()) {
            System.err.println("Failed: " + item.getFailureMessage());
        }
    }
}
```

##### ES 8.x 批量操作
```java
client.bulk(b -> b
    .operations(op -> op
        .index(i -> i
            .index("products")
            .id("1")
            .document(new Product("iPhone 15", 999.99, "electronics", new Date()))
        )
    )
    .operations(op -> op
        .update(u -> u
            .index("products")
            .id("2")
            .action(a -> a.doc(Map.of("price", 899.99)))
        )
    )
    .operations(op -> op
        .delete(d -> d
            .index("products")
            .id("3")
        )
    )
);
```

### 📊 API 使用对比总结

| 操作类型 | ES 7.x 复杂度 | ES 8.x 复杂度 | 可读性提升 |
|----------|---------------|---------------|------------|
| **基础 CRUD** | 中等 | 低 | 🟢 显著提升 |
| **复杂查询** | 高 | 中等 | 🟢 显著提升 |
| **聚合查询** | 高 | 中等 | 🟢 显著提升 |
| **批量操作** | 中等 | 低 | 🟢 显著提升 |
| **索引管理** | 高 | 低 | 🟢 显著提升 |

> ✅ 8.x 写法更简洁、类型安全、易于维护。

---

## 五、实体类映射（POJO 支持）对比

| 项目 | ES 7.x | ES 8.x |
|------|--------|--------|
| 是否支持自动映射到 POJO | ❌ 不直接支持，需手动解析 `SearchHit.getSourceAsString()` | ✅ 支持，`search(..., Product.class)` |
| 是否支持注解驱动映射 | 依赖 Spring Data Elasticsearch 等框架 | ✅ 原生支持 `@JsonpProperty` 等注解 |
| 反序列化方式 | 手动使用 `ObjectMapper` | 自动通过 `JacksonJsonpMapper` |

### 📝 实体类定义对比

#### ES 7.x 实体类（需要手动映射）
```java
public class Product {
    private String id;
    private String name;
    private Double price;
    private String category;
    private Date createdAt;
    
    // 构造函数
    public Product() {}
    
    public Product(String name, Double price, String category, Date createdAt) {
        this.name = name;
        this.price = price;
        this.category = category;
        this.createdAt = createdAt;
    }
    
    // Getter 和 Setter
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public Double getPrice() { return price; }
    public void setPrice(Double price) { this.price = price; }
    
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
    
    public Date getCreatedAt() { return createdAt; }
    public void setCreatedAt(Date createdAt) { this.createdAt = createdAt; }
    
    // 手动映射方法
    public static Product fromMap(Map<String, Object> map) {
        Product product = new Product();
        product.setId((String) map.get("id"));
        product.setName((String) map.get("name"));
        product.setPrice((Double) map.get("price"));
        product.setCategory((String) map.get("category"));
        
        Object createdAtObj = map.get("created_at");
        if (createdAtObj instanceof String) {
            // 处理日期字符串
            try {
                SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSSZ");
                product.setCreatedAt(sdf.parse((String) createdAtObj));
            } catch (ParseException e) {
                // 处理异常
            }
        } else if (createdAtObj instanceof Date) {
            product.setCreatedAt((Date) createdAtObj);
        }
        
        return product;
    }
    
    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("id", id);
        map.put("name", name);
        map.put("price", price);
        map.put("category", category);
        map.put("created_at", createdAt);
        return map;
    }
}
```

#### ES 8.x 实体类（支持注解）
```java
import co.elastic.clients.json.JsonpDeserializer;
import co.elastic.clients.json.JsonpMapper;
import co.elastic.clients.json.JsonpSerializable;
import co.elastic.clients.json.ObjectBuilderDeserializer;
import co.elastic.clients.json.ObjectDeserializer;
import co.elastic.clients.util.ObjectBuilder;
import jakarta.json.JsonObject;
import jakarta.json.stream.JsonGenerator;

import java.time.LocalDateTime;
import java.util.function.Function;

public class Product implements JsonpSerializable {
    private String id;
    private String name;
    private Double price;
    private String category;
    private LocalDateTime createdAt;
    
    // 构造函数
    public Product() {}
    
    public Product(String name, Double price, String category, LocalDateTime createdAt) {
        this.name = name;
        this.price = price;
        this.category = category;
        this.createdAt = createdAt;
    }
    
    // Getter 和 Setter
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public Double getPrice() { return price; }
    public void setPrice(Double price) { this.price = price; }
    
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    // JSON 序列化
    @Override
    public void serialize(JsonGenerator generator, JsonpMapper mapper) {
        generator.writeStartObject();
        if (this.id != null) {
            generator.writeKey("id");
            generator.write(this.id);
        }
        if (this.name != null) {
            generator.writeKey("name");
            generator.write(this.name);
        }
        if (this.price != null) {
            generator.writeKey("price");
            generator.write(this.price);
        }
        if (this.category != null) {
            generator.writeKey("category");
            generator.write(this.category);
        }
        if (this.createdAt != null) {
            generator.writeKey("created_at");
            generator.write(this.createdAt.toString());
        }
        generator.writeEnd();
    }
    
    // JSON 反序列化
    public static final JsonpDeserializer<Product> _DESERIALIZER = ObjectBuilderDeserializer.lazy(
        Product::new, Product::setupProductDeserializer, Product::new);
    
    protected static void setupProductDeserializer(ObjectDeserializer<Product.Builder> op) {
        op.add(Builder::id, JsonpDeserializer.stringDeserializer(), "id");
        op.add(Builder::name, JsonpDeserializer.stringDeserializer(), "name");
        op.add(Builder::price, JsonpDeserializer.doubleDeserializer(), "price");
        op.add(Builder::category, JsonpDeserializer.stringDeserializer(), "category");
        op.add(Builder::createdAt, JsonpDeserializer.localDateTimeDeserializer(), "created_at");
    }
    
    // Builder 类
    public static class Builder implements ObjectBuilder<Product> {
        private String id;
        private String name;
        private Double price;
        private String category;
        private LocalDateTime createdAt;
        
        public Builder id(String value) {
            this.id = value;
            return this;
        }
        
        public Builder name(String value) {
            this.name = value;
            return this;
        }
        
        public Builder price(Double value) {
            this.price = value;
            return this;
        }
        
        public Builder category(String value) {
            this.category = value;
            return this;
        }
        
        public Builder createdAt(LocalDateTime value) {
            this.createdAt = value;
            return this;
        }
        
        @Override
        public Product build() {
            Product product = new Product();
            product.id = this.id;
            product.name = this.name;
            product.price = this.price;
            product.category = this.category;
            product.createdAt = this.createdAt;
            return product;
        }
    }
}
```

### 🔧 使用 Jackson 注解的简化版本

#### ES 8.x 简化实体类（推荐）
```java
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.annotation.JsonDeserialize;
import com.fasterxml.jackson.databind.annotation.JsonSerialize;
import com.fasterxml.jackson.datatype.jsr310.deser.LocalDateTimeDeserializer;
import com.fasterxml.jackson.datatype.jsr310.ser.LocalDateTimeSerializer;

import java.time.LocalDateTime;

public class Product {
    private String id;
    
    @JsonProperty("name")
    private String name;
    
    @JsonProperty("price")
    private Double price;
    
    @JsonProperty("category")
    private String category;
    
    @JsonProperty("created_at")
    @JsonSerialize(using = LocalDateTimeSerializer.class)
    @JsonDeserialize(using = LocalDateTimeDeserializer.class)
    private LocalDateTime createdAt;
    
    // 构造函数
    public Product() {}
    
    public Product(String name, Double price, String category, LocalDateTime createdAt) {
        this.name = name;
        this.price = price;
        this.category = category;
        this.createdAt = createdAt;
    }
    
    // Getter 和 Setter
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public Double getPrice() { return price; }
    public void setPrice(Double price) { this.price = price; }
    
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    @Override
    public String toString() {
        return "Product{" +
                "id='" + id + '\'' +
                ", name='" + name + '\'' +
                ", price=" + price +
                ", category='" + category + '\'' +
                ", createdAt=" + createdAt +
                '}';
    }
}
```

### 📊 映射方式对比

#### ES 7.x 手动映射示例
```java
// 查询并手动映射
SearchResponse response = client.search(request, RequestOptions.DEFAULT);
SearchHit[] hits = response.getHits().getHits();

List<Product> products = Arrays.stream(hits)
    .map(hit -> {
        try {
            // 手动解析 JSON
            String sourceAsString = hit.getSourceAsString();
            ObjectMapper mapper = new ObjectMapper();
            mapper.registerModule(new JavaTimeModule());
            mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
            
            return mapper.readValue(sourceAsString, Product.class);
        } catch (Exception e) {
            throw new RuntimeException("Failed to parse product", e);
        }
    })
    .collect(Collectors.toList());
```

#### ES 8.x 自动映射示例
```java
// 查询并自动映射
SearchResponse<Product> response = client.search(s -> s
    .index("products")
    .query(q -> q.matchAll(m -> m)),
    Product.class
);

List<Product> products = response.hits().hits().stream()
    .map(hit -> hit.source())
    .collect(Collectors.toList());
```

### 🌱 Spring Data Elasticsearch 集成

#### ES 7.x + Spring Data
```java
// 配置类
@Configuration
@EnableElasticsearchRepositories(basePackages = "com.example.repository")
public class ElasticsearchConfig extends AbstractElasticsearchConfiguration {
    
    @Override
    @Bean
    public RestHighLevelClient elasticsearchClient() {
        ClientConfiguration clientConfiguration = ClientConfiguration.builder()
            .connectedTo("localhost:9200")
            .build();
        return RestClients.create(clientConfiguration).rest();
    }
}

// 实体类
@Document(indexName = "products")
public class Product {
    @Id
    private String id;
    
    @Field(type = FieldType.Text)
    private String name;
    
    @Field(type = FieldType.Double)
    private Double price;
    
    @Field(type = FieldType.Keyword)
    private String category;
    
    @Field(type = FieldType.Date)
    private LocalDateTime createdAt;
    
    // getter/setter...
}

// Repository
@Repository
public interface ProductRepository extends ElasticsearchRepository<Product, String> {
    List<Product> findByCategory(String category);
    List<Product> findByPriceBetween(Double minPrice, Double maxPrice);
}
```

#### ES 8.x + Spring Data
```java
// 配置类
@Configuration
@EnableElasticsearchRepositories(basePackages = "com.example.repository")
public class ElasticsearchConfig extends AbstractElasticsearchConfiguration {
    
    @Override
    @Bean
    public ElasticsearchClient elasticsearchClient() {
        RestClient restClient = RestClient.builder(
            new HttpHost("localhost", 9200, "http")
        ).build();
        
        JacksonJsonpMapper jsonpMapper = new JacksonJsonpMapper();
        RestClientTransport transport = new RestClientTransport(restClient, jsonpMapper);
        
        return new ElasticsearchClient(transport);
    }
}

// 实体类（使用 Spring Data 注解）
@Document(indexName = "products")
public class Product {
    @Id
    private String id;
    
    @Field(type = FieldType.Text)
    private String name;
    
    @Field(type = FieldType.Double)
    private Double price;
    
    @Field(type = FieldType.Keyword)
    private String category;
    
    @Field(type = FieldType.Date)
    private LocalDateTime createdAt;
    
    // getter/setter...
}

// Repository（支持更多查询方法）
@Repository
public interface ProductRepository extends ElasticsearchRepository<Product, String> {
    List<Product> findByCategory(String category);
    List<Product> findByPriceBetween(Double minPrice, Double maxPrice);
    
    // 支持 @Query 注解
    @Query("{\"bool\": {\"must\": [{\"match\": {\"name\": \"?0\"}}]}}")
    List<Product> findByNameContaining(String name);
}
```

### 📈 映射性能对比

| 操作 | ES 7.x 性能 | ES 8.x 性能 | 说明 |
|------|-------------|-------------|------|
| **单文档映射** | 中等 | 高 | 8.x 自动映射更快 |
| **批量文档映射** | 低 | 高 | 8.x 批量处理优化 |
| **复杂对象映射** | 低 | 高 | 8.x 类型安全映射 |
| **内存使用** | 中等 | 低 | 8.x 更高效的内存使用 |

> ✅ 8.x 原生支持 POJO 映射，代码更简洁，性能更好。

---

## 六、索引管理与 Mapping 映射

| 功能 | ES 7.x | ES 8.x |
|------|--------|--------|
| 创建索引 + Mapping | 手动拼接 JSON 或使用 `XContentBuilder` | 支持从 POJO 自动生成 Mapping（需配合注解） |
| 类型安全 | ❌ | ✅ 支持生成类型化 Mapping |
| 更新 Mapping | 7.x 支持动态更新部分字段 | 8.x 同样支持，但 API 更清晰 |

### ES 8.x 示例：从 POJO 生成 Mapping

```java
// 假设 Product 类有 @JsonpProperty 注解
IndexTemplate template = IndexTemplate.of(t -> t
    .mappings(m -> m
        .properties("name", p -> p.text(t2 -> t2))
        .properties("price", p -> p.double_(d -> d))
    )
);
```

---

## 七、身份验证与安全配置

| 项目 | ES 7.x | ES 8.x |
|------|--------|--------|
| Basic Auth | 使用 `CredentialsProvider` | 同样支持，配置方式一致 |
| API Key / Bearer Token | 支持，但需手动设置 Header | 支持，可通过 `RequestOptions` 设置 |
| SSL/TLS | 支持，需配置 `HttpClient` | 支持，配置方式类似 |

```java
// 8.x 中设置 Basic Auth
final CredentialsProvider credentialsProvider = new BasicCredentialsProvider();
credentialsProvider.setCredentials(AuthScope.ANY, new UsernamePasswordCredentials("user", "pass"));

RestClientBuilder builder = RestClient.builder(new HttpHost("localhost", 9200))
    .setHttpClientConfigCallback(hcb -> hcb.setDefaultCredentialsProvider(credentialsProvider));
```

---

## 八、错误处理与响应封装

| 项目 | ES 7.x | ES 8.x |
|------|--------|--------|
| 异常类型 | `ElasticsearchException`、`IOException` | 统一为 `ElasticsearchException` |
| 响应结构 | `SearchResponse` 包含 `Hits`, `Aggregations` 等 | `SearchResponse<T>` 泛型封装，结构更清晰 |
| 错误信息提取 | 需解析 `response.status()` 和异常 | 支持更细粒度的错误码和原因提取 |

### 🚨 异常处理对比

#### ES 7.x 异常处理
```java
try {
    SearchRequest request = new SearchRequest("products");
    SearchSourceBuilder source = new SearchSourceBuilder();
    source.query(QueryBuilders.matchQuery("name", "phone"));
    request.source(source);
    
    SearchResponse response = client.search(request, RequestOptions.DEFAULT);
    
    // 检查响应状态
    if (response.status() != RestStatus.OK) {
        throw new RuntimeException("Search failed with status: " + response.status());
    }
    
    // 处理结果
    SearchHits hits = response.getHits();
    for (SearchHit hit : hits.getHits()) {
        // 处理文档...
    }
    
} catch (ElasticsearchException e) {
    // 处理 Elasticsearch 异常
    if (e.status() == RestStatus.NOT_FOUND) {
        System.err.println("Index not found: " + e.getMessage());
    } else if (e.status() == RestStatus.BAD_REQUEST) {
        System.err.println("Bad request: " + e.getMessage());
    } else {
        System.err.println("Elasticsearch error: " + e.getMessage());
    }
    throw e;
} catch (IOException e) {
    // 处理 IO 异常
    System.err.println("IO error: " + e.getMessage());
    throw new RuntimeException("Failed to execute search", e);
}
```

#### ES 8.x 异常处理
```java
try {
    SearchResponse<Product> response = client.search(s -> s
        .index("products")
        .query(q -> q.match(t -> t.field("name").query("phone"))),
        Product.class
    );
    
    // 处理结果
    List<Product> products = response.hits().hits().stream()
        .map(hit -> hit.source())
        .collect(Collectors.toList());
        
} catch (ElasticsearchException e) {
    // 更详细的异常信息
    if (e instanceof ElasticsearchStatusException) {
        ElasticsearchStatusException statusEx = (ElasticsearchStatusException) e;
        System.err.println("Status: " + statusEx.status());
        System.err.println("Error type: " + statusEx.error().type());
        System.err.println("Error reason: " + statusEx.error().reason());
    }
    
    // 根据错误类型处理
    switch (e.status()) {
        case NOT_FOUND:
            System.err.println("Index not found: " + e.getMessage());
            break;
        case BAD_REQUEST:
            System.err.println("Bad request: " + e.getMessage());
            break;
        case UNAUTHORIZED:
            System.err.println("Unauthorized: " + e.getMessage());
            break;
        case FORBIDDEN:
            System.err.println("Forbidden: " + e.getMessage());
            break;
        default:
            System.err.println("Elasticsearch error: " + e.getMessage());
    }
    throw e;
}
```

### 🔧 自定义异常处理工具类

#### ES 7.x 异常处理工具
```java
public class Elasticsearch7ExceptionHandler {
    
    public static <T> T executeWithRetry(Supplier<T> operation, int maxRetries) {
        int retryCount = 0;
        while (retryCount < maxRetries) {
            try {
                return operation.get();
            } catch (ElasticsearchException e) {
                retryCount++;
                if (retryCount >= maxRetries) {
                    throw e;
                }
                
                // 根据异常类型决定是否重试
                if (isRetryableException(e)) {
                    try {
                        Thread.sleep(1000 * retryCount); // 指数退避
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException("Operation interrupted", ie);
                    }
                } else {
                    throw e; // 不可重试的异常直接抛出
                }
            } catch (IOException e) {
                retryCount++;
                if (retryCount >= maxRetries) {
                    throw new RuntimeException("IO error after " + maxRetries + " retries", e);
                }
                try {
                    Thread.sleep(1000 * retryCount);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw new RuntimeException("Operation interrupted", ie);
                }
            }
        }
        throw new RuntimeException("Unexpected error");
    }
    
    private static boolean isRetryableException(ElasticsearchException e) {
        return e.status() == RestStatus.SERVICE_UNAVAILABLE ||
               e.status() == RestStatus.GATEWAY_TIMEOUT ||
               e.status() == RestStatus.REQUEST_TIMEOUT ||
               e.status() == RestStatus.TOO_MANY_REQUESTS;
    }
    
    public static void logError(ElasticsearchException e) {
        System.err.println("=== Elasticsearch Error ===");
        System.err.println("Status: " + e.status());
        System.err.println("Message: " + e.getMessage());
        System.err.println("Error Type: " + e.getClass().getSimpleName());
        
        if (e.getCause() != null) {
            System.err.println("Cause: " + e.getCause().getMessage());
        }
        
        // 打印堆栈跟踪（可选）
        e.printStackTrace();
    }
}
```

#### ES 8.x 异常处理工具
```java
public class Elasticsearch8ExceptionHandler {
    
    public static <T> T executeWithRetry(Supplier<T> operation, int maxRetries) {
        int retryCount = 0;
        while (retryCount < maxRetries) {
            try {
                return operation.get();
            } catch (ElasticsearchException e) {
                retryCount++;
                if (retryCount >= maxRetries) {
                    throw e;
                }
                
                if (isRetryableException(e)) {
                    try {
                        Thread.sleep(1000 * retryCount);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException("Operation interrupted", ie);
                    }
                } else {
                    throw e;
                }
            }
        }
        throw new RuntimeException("Unexpected error");
    }
    
    private static boolean isRetryableException(ElasticsearchException e) {
        return e.status() == RestStatus.SERVICE_UNAVAILABLE ||
               e.status() == RestStatus.GATEWAY_TIMEOUT ||
               e.status() == RestStatus.REQUEST_TIMEOUT ||
               e.status() == RestStatus.TOO_MANY_REQUESTS;
    }
    
    public static void logError(ElasticsearchException e) {
        System.err.println("=== Elasticsearch Error ===");
        System.err.println("Status: " + e.status());
        System.err.println("Message: " + e.getMessage());
        System.err.println("Error Type: " + e.getClass().getSimpleName());
        
        // 8.x 提供更详细的错误信息
        if (e instanceof ElasticsearchStatusException) {
            ElasticsearchStatusException statusEx = (ElasticsearchStatusException) e;
            System.err.println("Error Type: " + statusEx.error().type());
            System.err.println("Error Reason: " + statusEx.error().reason());
            System.err.println("Error Root Cause: " + statusEx.error().rootCause());
        }
        
        if (e.getCause() != null) {
            System.err.println("Cause: " + e.getCause().getMessage());
        }
        
        e.printStackTrace();
    }
    
    // 8.x 特有的错误处理方法
    public static <T> Optional<T> safeExecute(Supplier<T> operation) {
        try {
            return Optional.of(operation.get());
        } catch (ElasticsearchException e) {
            logError(e);
            return Optional.empty();
        }
    }
    
    public static void safeExecute(Runnable operation) {
        try {
            operation.run();
        } catch (ElasticsearchException e) {
            logError(e);
        }
    }
}
```

### 📊 响应结构对比

#### ES 7.x 响应处理
```java
SearchResponse response = client.search(request, RequestOptions.DEFAULT);

// 检查响应状态
if (response.status() != RestStatus.OK) {
    throw new RuntimeException("Search failed");
}

// 获取分页信息
SearchHits hits = response.getHits();
long totalHits = hits.getTotalHits().value;
float maxScore = hits.getMaxScore();
SearchHit[] searchHits = hits.getHits();

// 获取聚合结果
Aggregations aggregations = response.getAggregations();
if (aggregations != null) {
    Terms categoryAgg = aggregations.get("category_agg");
    if (categoryAgg != null) {
        for (Terms.Bucket bucket : categoryAgg.getBuckets()) {
            String category = bucket.getKeyAsString();
            long count = bucket.getDocCount();
            // 处理聚合结果...
        }
    }
}

// 获取建议结果
Suggest suggest = response.getSuggest();
if (suggest != null) {
    // 处理建议结果...
}
```

#### ES 8.x 响应处理
```java
SearchResponse<Product> response = client.search(s -> s
    .index("products")
    .query(q -> q.matchAll(m -> m)),
    Product.class
);

// 获取分页信息
long totalHits = response.hits().total().value();
float maxScore = response.hits().maxScore();

// 获取文档列表
List<Product> products = response.hits().hits().stream()
    .map(hit -> hit.source())
    .collect(Collectors.toList());

// 获取聚合结果
Map<String, Aggregate> aggregations = response.aggregations();
if (aggregations != null) {
    TermsAggregate categoryAgg = aggregations.get("category_agg").sterms();
    for (StringTermsBucket bucket : categoryAgg.buckets().array()) {
        String category = bucket.key().stringValue();
        long count = bucket.docCount();
        // 处理聚合结果...
    }
}

// 获取建议结果
Map<String, List<Suggestion<Product>>> suggest = response.suggest();
if (suggest != null) {
    // 处理建议结果...
}
```

### 🛡️ 错误处理最佳实践

#### 1. 统一异常处理
```java
@ControllerAdvice
public class ElasticsearchExceptionHandler {
    
    @ExceptionHandler(ElasticsearchException.class)
    public ResponseEntity<ErrorResponse> handleElasticsearchException(ElasticsearchException e) {
        ErrorResponse error = new ErrorResponse();
        error.setStatus(e.status().getStatus());
        error.setMessage(e.getMessage());
        error.setTimestamp(LocalDateTime.now());
        
        return ResponseEntity.status(e.status().getStatus()).body(error);
    }
    
    @ExceptionHandler(IOException.class)
    public ResponseEntity<ErrorResponse> handleIOException(IOException e) {
        ErrorResponse error = new ErrorResponse();
        error.setStatus(500);
        error.setMessage("Internal server error: " + e.getMessage());
        error.setTimestamp(LocalDateTime.now());
        
        return ResponseEntity.status(500).body(error);
    }
}
```

#### 2. 重试机制
```java
@Component
public class ElasticsearchService {
    
    @Retryable(value = {ElasticsearchException.class}, 
               maxAttempts = 3, 
               backoff = @Backoff(delay = 1000, multiplier = 2))
    public SearchResponse<Product> searchProducts(String query) {
        return client.search(s -> s
            .index("products")
            .query(q -> q.match(t -> t.field("name").query(query))),
            Product.class
        );
    }
    
    @Recover
    public SearchResponse<Product> recoverSearch(ElasticsearchException e, String query) {
        // 降级处理：返回空结果或缓存结果
        log.error("Search failed after retries for query: " + query, e);
        return SearchResponse.of(s -> s.hits(h -> h.total(t -> t.value(0))));
    }
}
```

#### 3. 健康检查
```java
@Component
public class ElasticsearchHealthIndicator implements HealthIndicator {
    
    private final ElasticsearchClient client;
    
    public ElasticsearchHealthIndicator(ElasticsearchClient client) {
        this.client = client;
    }
    
    @Override
    public Health health() {
        try {
            // 执行简单的集群健康检查
            client.cluster().health(h -> h);
            return Health.up()
                .withDetail("status", "Elasticsearch is healthy")
                .build();
        } catch (ElasticsearchException e) {
            return Health.down()
                .withDetail("status", "Elasticsearch is down")
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}
```

### 📈 错误处理对比总结

| 特性 | ES 7.x | ES 8.x | 改进程度 |
|------|--------|--------|----------|
| **异常类型** | 多种异常类型 | 统一的 `ElasticsearchException` | 🟢 简化 |
| **错误信息** | 基础错误信息 | 详细的错误类型和原因 | 🟢 显著改进 |
| **重试机制** | 需手动实现 | 支持更智能的重试 | 🟢 显著改进 |
| **降级处理** | 复杂 | 简化 | 🟢 显著改进 |
| **监控集成** | 需额外配置 | 更好的监控支持 | 🟢 显著改进 |

---

## 九、性能与资源管理

| 项目 | ES 7.x | ES 8.x |
|------|--------|--------|
| 连接池管理 | 依赖 Apache HttpClient | 同样基于 `RestClient`，性能相近 |
| 内存开销 | 一般 | 略高（因生成类较多），但可接受 |
| 客户端关闭 | `client.close()` | 同样需要关闭 `RestClient` 和 `transport` |

---

## 十、兼容性与迁移建议

| 项目 | 说明 |
|------|------|
| **8.x 客户端能否连接 7.x 集群？** | ✅ 可以，但**建议集群版本 ≥ 7.17**，否则部分新 API 不可用 |
| **7.x 客户端能否连接 8.x 集群？** | ⚠️ 可以，但**不推荐**，因 8.x 已移除部分旧 API，且 `RestHighLevelClient` 已废弃 |
| **迁移成本** | 中等，需重写 API 调用，但逻辑不变 |
| **Spring 集成** | Spring Data Elasticsearch 4.4+ 支持 8.x 客户端 |

---

## 十一、总结：核心差异一览表

| 维度 | Elasticsearch 7.x (`RestHighLevelClient`) | Elasticsearch 8.x (`elasticsearch-java`) |
|------|-------------------------------------------|------------------------------------------|
| 官方状态 | ❌ 已废弃（deprecated） | ✅ 官方推荐，长期支持 |
| Java 版本 | 8+ | **17+** |
| API 风格 | 命令式，静态方法 | 函数式，Lambda 构建器 |
| 类型安全 | 弱 | 强（泛型 + POJO 映射） |
| POJO 支持 | 需手动解析 | 原生支持 |
| 代码可读性 | 一般 | 高 |
| 学习成本 | 低（传统风格） | 中（需适应 Lambda） |
| 性能 | 相当 | 相当 |
| 未来前景 | ❌ 停止更新 | ✅ 持续演进 |

---

## ✅ 最终建议

| 场景 | 推荐方案 |
|------|----------|
| **新项目** | ✅ 直接使用 **Elasticsearch 8.x + `elasticsearch-java` 客户端** |
| **老项目升级** | 🔁 逐步迁移，优先升级集群到 8.x，再替换客户端 |
| **无法升级 Java 版本** | ⚠️ 继续使用 7.x 客户端，但需注意安全风险 |
| **使用 Spring Boot** | 推荐 `spring-boot-starter-data-elasticsearch` 4.4+ 版本 |

---

## 十二、完整迁移指南

### 🚀 迁移步骤详解

#### 第一步：环境准备
```bash
# 1. 升级 Java 版本到 17+
java -version

# 2. 更新 Maven/Gradle 配置
# 3. 备份现有代码
# 4. 创建新分支进行迁移
```

#### 第二步：依赖更新
```xml
<!-- 移除旧依赖 -->
<dependency>
    <groupId>org.elasticsearch.client</groupId>
    <artifactId>elasticsearch-rest-high-level-client</artifactId>
    <version>7.17.14</version>
</dependency>

<!-- 添加新依赖 -->
<dependency>
    <groupId>co.elastic.clients</groupId>
    <artifactId>elasticsearch-java</artifactId>
    <version>8.13.0</version>
</dependency>
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>2.15.2</version>
</dependency>
```

#### 第三步：客户端配置迁移
```java
// 旧代码
@Configuration
public class ElasticsearchConfig {
    @Bean
    public RestHighLevelClient elasticsearchClient() {
        return new RestHighLevelClient(
            RestClient.builder(new HttpHost("localhost", 9200, "http"))
        );
    }
}

// 新代码
@Configuration
public class ElasticsearchConfig {
    @Bean
    public ElasticsearchClient elasticsearchClient() {
        RestClient restClient = RestClient.builder(
            new HttpHost("localhost", 9200, "http")
        ).build();
        
        JacksonJsonpMapper jsonpMapper = new JacksonJsonpMapper();
        RestClientTransport transport = new RestClientTransport(restClient, jsonpMapper);
        
        return new ElasticsearchClient(transport);
    }
}
```

#### 第四步：API 调用迁移
```java
// 旧代码
SearchRequest request = new SearchRequest("products");
SearchSourceBuilder source = new SearchSourceBuilder();
source.query(QueryBuilders.matchQuery("name", "phone"));
request.source(source);
SearchResponse response = client.search(request, RequestOptions.DEFAULT);

// 新代码
SearchResponse<Product> response = client.search(s -> s
    .index("products")
    .query(q -> q.match(t -> t.field("name").query("phone"))),
    Product.class
);
```

### 📋 迁移检查清单

- [ ] Java 版本升级到 17+
- [ ] 更新 Maven/Gradle 依赖
- [ ] 迁移客户端配置
- [ ] 更新实体类注解
- [ ] 迁移 API 调用代码
- [ ] 更新异常处理逻辑
- [ ] 测试所有功能
- [ ] 性能测试
- [ ] 文档更新

---

## 十三、实际项目示例

### 🏪 电商搜索系统示例

#### 项目结构
```
src/main/java/com/example/eshop/
├── config/
│   ├── ElasticsearchConfig.java
│   └── ElasticsearchHealthConfig.java
├── model/
│   ├── Product.java
│   ├── Category.java
│   └── SearchRequest.java
├── repository/
│   ├── ProductRepository.java
│   └── CategoryRepository.java
├── service/
│   ├── ProductService.java
│   ├── SearchService.java
│   └── IndexService.java
└── controller/
    ├── ProductController.java
    └── SearchController.java
```

#### 核心代码示例

##### 1. 配置类
```java
@Configuration
@EnableElasticsearchRepositories(basePackages = "com.example.eshop.repository")
public class ElasticsearchConfig extends AbstractElasticsearchConfiguration {
    
    @Value("${elasticsearch.host:localhost}")
    private String host;
    
    @Value("${elasticsearch.port:9200}")
    private int port;
    
    @Value("${elasticsearch.username:}")
    private String username;
    
    @Value("${elasticsearch.password:}")
    private String password;
    
    @Override
    @Bean
    public ElasticsearchClient elasticsearchClient() {
        // 创建 REST 客户端
        RestClientBuilder builder = RestClient.builder(
            new HttpHost(host, port, "http")
        );
        
        // 配置认证
        if (StringUtils.hasText(username) && StringUtils.hasText(password)) {
            final CredentialsProvider credentialsProvider = new BasicCredentialsProvider();
            credentialsProvider.setCredentials(AuthScope.ANY, 
                new UsernamePasswordCredentials(username, password));
            
            builder.setHttpClientConfigCallback(httpClientBuilder -> {
                httpClientBuilder.setDefaultCredentialsProvider(credentialsProvider);
                return httpClientBuilder;
            });
        }
        
        RestClient restClient = builder.build();
        
        // 配置 JSON 映射器
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        
        JacksonJsonpMapper jsonpMapper = new JacksonJsonpMapper(mapper);
        RestClientTransport transport = new RestClientTransport(restClient, jsonpMapper);
        
        return new ElasticsearchClient(transport);
    }
}
```

##### 2. 实体类
```java
@Document(indexName = "products")
public class Product {
    @Id
    private String id;
    
    @Field(type = FieldType.Text, analyzer = "ik_max_word")
    private String name;
    
    @Field(type = FieldType.Text, analyzer = "ik_smart")
    private String description;
    
    @Field(type = FieldType.Double)
    private Double price;
    
    @Field(type = FieldType.Keyword)
    private String category;
    
    @Field(type = FieldType.Keyword)
    private String brand;
    
    @Field(type = FieldType.Integer)
    private Integer stock;
    
    @Field(type = FieldType.Date)
    private LocalDateTime createdAt;
    
    @Field(type = FieldType.Date)
    private LocalDateTime updatedAt;
    
    // 构造函数、getter/setter...
}
```

##### 3. 服务类
```java
@Service
@Slf4j
public class ProductService {
    
    private final ElasticsearchClient client;
    private final ProductRepository repository;
    
    public ProductService(ElasticsearchClient client, ProductRepository repository) {
        this.client = client;
        this.repository = repository;
    }
    
    public Product saveProduct(Product product) {
        product.setCreatedAt(LocalDateTime.now());
        product.setUpdatedAt(LocalDateTime.now());
        return repository.save(product);
    }
    
    public SearchResponse<Product> searchProducts(SearchRequest request) {
        try {
            return client.search(s -> s
                .index("products")
                .query(q -> buildQuery(q, request))
                .sort(sort -> buildSort(sort, request))
                .from(request.getFrom())
                .size(request.getSize())
                .aggregations("category_agg", a -> a
                    .terms(t -> t.field("category").size(10))
                )
                .aggregations("price_stats", a -> a
                    .stats(stats -> stats.field("price"))
                ),
                Product.class
            );
        } catch (ElasticsearchException e) {
            log.error("Search failed", e);
            throw new RuntimeException("Search operation failed", e);
        }
    }
    
    private Function<Query.Builder, ObjectBuilder<Query>> buildQuery(
            Query.Builder queryBuilder, SearchRequest request) {
        return q -> {
            BoolQuery.Builder boolQuery = new BoolQuery.Builder();
            
            // 文本搜索
            if (StringUtils.hasText(request.getKeyword())) {
                boolQuery.must(m -> m
                    .multiMatch(mm -> mm
                        .fields("name^2", "description")
                        .query(request.getKeyword())
                        .type(TextQueryType.BestFields)
                    )
                );
            }
            
            // 分类过滤
            if (StringUtils.hasText(request.getCategory())) {
                boolQuery.filter(f -> f
                    .term(t -> t.field("category").value(request.getCategory()))
                );
            }
            
            // 价格范围
            if (request.getMinPrice() != null || request.getMaxPrice() != null) {
                boolQuery.filter(f -> f
                    .range(r -> r
                        .field("price")
                        .gte(request.getMinPrice() != null ? 
                            JsonData.of(request.getMinPrice()) : null)
                        .lte(request.getMaxPrice() != null ? 
                            JsonData.of(request.getMaxPrice()) : null)
                    )
                );
            }
            
            // 库存过滤
            if (request.getInStock() != null && request.getInStock()) {
                boolQuery.filter(f -> f
                    .range(r -> r.field("stock").gt(JsonData.of(0)))
                );
            }
            
            return boolQuery;
        };
    }
    
    private Function<SortOptions.Builder, ObjectBuilder<SortOptions>> buildSort(
            SortOptions.Builder sortBuilder, SearchRequest request) {
        return s -> {
            if ("price".equals(request.getSortBy())) {
                s.field(f -> f
                    .field("price")
                    .order("asc".equals(request.getSortOrder()) ? 
                        SortOrder.Asc : SortOrder.Desc)
                );
            } else if ("created_at".equals(request.getSortBy())) {
                s.field(f -> f
                    .field("created_at")
                    .order("asc".equals(request.getSortOrder()) ? 
                        SortOrder.Asc : SortOrder.Desc)
                );
            } else {
                // 默认按相关性排序
                s.score(sc -> sc.order(SortOrder.Desc));
            }
            return s;
        };
    }
    
    public void createIndex() {
        try {
            client.indices().create(c -> c
                .index("products")
                .settings(s -> s
                    .numberOfShards("3")
                    .numberOfReplicas("1")
                    .analysis(a -> a
                        .analyzer("ik_max_word", analyzer -> analyzer
                            .type("ik_max_word")
                        )
                        .analyzer("ik_smart", analyzer -> analyzer
                            .type("ik_smart")
                        )
                    )
                )
                .mappings(m -> m
                    .properties("name", p -> p
                        .text(t -> t.analyzer("ik_max_word"))
                    )
                    .properties("description", p -> p
                        .text(t -> t.analyzer("ik_smart"))
                    )
                    .properties("price", p -> p
                        .double_(d -> d)
                    )
                    .properties("category", p -> p
                        .keyword(k -> k)
                    )
                    .properties("brand", p -> p
                        .keyword(k -> k)
                    )
                    .properties("stock", p -> p
                        .integer(i -> i)
                    )
                    .properties("created_at", p -> p
                        .date(d -> d)
                    )
                    .properties("updated_at", p -> p
                        .date(d -> d)
                    )
                )
            );
            log.info("Products index created successfully");
        } catch (ElasticsearchException e) {
            if (e.status() == RestStatus.BAD_REQUEST && 
                e.getMessage().contains("resource_already_exists_exception")) {
                log.info("Products index already exists");
            } else {
                throw e;
            }
        }
    }
}
```

##### 4. 控制器
```java
@RestController
@RequestMapping("/api/products")
@Slf4j
public class ProductController {
    
    private final ProductService productService;
    
    public ProductController(ProductService productService) {
        this.productService = productService;
    }
    
    @PostMapping
    public ResponseEntity<Product> createProduct(@RequestBody Product product) {
        Product savedProduct = productService.saveProduct(product);
        return ResponseEntity.status(HttpStatus.CREATED).body(savedProduct);
    }
    
    @GetMapping("/search")
    public ResponseEntity<SearchResult<Product>> searchProducts(
            @ModelAttribute SearchRequest request) {
        try {
            SearchResponse<Product> response = productService.searchProducts(request);
            
            SearchResult<Product> result = new SearchResult<>();
            result.setProducts(response.hits().hits().stream()
                .map(hit -> hit.source())
                .collect(Collectors.toList()));
            result.setTotal(response.hits().total().value());
            result.setMaxScore(response.hits().maxScore());
            
            // 处理聚合结果
            Map<String, Aggregate> aggregations = response.aggregations();
            if (aggregations != null) {
                // 分类聚合
                TermsAggregate categoryAgg = aggregations.get("category_agg").sterms();
                Map<String, Long> categoryStats = categoryAgg.buckets().array().stream()
                    .collect(Collectors.toMap(
                        bucket -> bucket.key().stringValue(),
                        bucket -> bucket.docCount()
                    ));
                result.setCategoryStats(categoryStats);
                
                // 价格统计
                StatsAggregate priceStats = aggregations.get("price_stats").stats();
                result.setPriceStats(new PriceStats(
                    priceStats.min(),
                    priceStats.max(),
                    priceStats.avg(),
                    priceStats.sum()
                ));
            }
            
            return ResponseEntity.ok(result);
            
        } catch (Exception e) {
            log.error("Search failed", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(new SearchResult<>());
        }
    }
    
    @PostMapping("/index/create")
    public ResponseEntity<String> createIndex() {
        try {
            productService.createIndex();
            return ResponseEntity.ok("Index created successfully");
        } catch (Exception e) {
            log.error("Failed to create index", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body("Failed to create index: " + e.getMessage());
        }
    }
}
```

---

## 十四、性能优化建议

### 🚀 客户端优化

#### 1. 连接池配置
```java
RestClientBuilder builder = RestClient.builder(new HttpHost("localhost", 9200))
    .setHttpClientConfigCallback(httpClientBuilder -> {
        // 连接池配置
        httpClientBuilder.setMaxConnTotal(100);
        httpClientBuilder.setMaxConnPerRoute(20);
        
        // 超时配置
        httpClientBuilder.setConnectionTimeoutMillis(5000);
        httpClientBuilder.setSocketTimeoutMillis(60000);
        
        return httpClientBuilder;
    });
```

#### 2. 批量操作优化
```java
// 批量索引
List<Product> products = getProducts();
BulkRequest.Builder br = new BulkRequest.Builder();

for (Product product : products) {
    br.operations(op -> op
        .index(idx -> idx
            .index("products")
            .id(product.getId())
            .document(product)
        )
    );
}

BulkResponse result = client.bulk(br.build());
```

#### 3. 查询优化
```java
// 使用 source filtering 减少网络传输
SearchResponse<Product> response = client.search(s -> s
    .index("products")
    .query(q -> q.matchAll(m -> m))
    .source(src -> src.filter(f -> f
        .includes("id", "name", "price") // 只返回需要的字段
    )),
    Product.class
);
```

### 📊 监控和指标

#### 1. 健康检查
```java
@Component
public class ElasticsearchHealthIndicator implements HealthIndicator {
    
    private final ElasticsearchClient client;
    
    @Override
    public Health health() {
        try {
            ClusterHealthResponse health = client.cluster().health(h -> h);
            return Health.up()
                .withDetail("cluster_name", health.clusterName())
                .withDetail("status", health.status())
                .withDetail("number_of_nodes", health.numberOfNodes())
                .withDetail("active_shards", health.activeShards())
                .build();
        } catch (Exception e) {
            return Health.down()
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}
```

#### 2. 性能监控
```java
@Aspect
@Component
public class ElasticsearchPerformanceAspect {
    
    private final MeterRegistry meterRegistry;
    
    @Around("execution(* com.example.service.*Service.*(..))")
    public Object measurePerformance(ProceedingJoinPoint joinPoint) throws Throwable {
        Timer.Sample sample = Timer.start(meterRegistry);
        try {
            return joinPoint.proceed();
        } finally {
            sample.stop(Timer.builder("elasticsearch.operation.duration")
                .tag("method", joinPoint.getSignature().getName())
                .tag("class", joinPoint.getTarget().getClass().getSimpleName())
                .register(meterRegistry));
        }
    }
}
```

---

## 十五、常见问题与解决方案

### ❓ FAQ

#### Q1: 如何在不升级 Java 版本的情况下使用 ES 8.x？
**A**: 可以使用 ES 8.x 的 REST 客户端，但功能受限。建议升级到 Java 17+。

#### Q2: 迁移过程中如何保证数据一致性？
**A**: 
1. 使用滚动查询分批处理数据
2. 实现双写机制
3. 使用数据校验工具

#### Q3: 如何处理复杂的聚合查询？
**A**: ES 8.x 提供了更清晰的聚合 API：
```java
client.search(s -> s
    .index("products")
    .aggregations("category_price_stats", a -> a
        .terms(t -> t.field("category"))
        .aggregations("price_stats", sa -> sa
            .stats(stats -> stats.field("price"))
        )
    ),
    Product.class
);
```

#### Q4: 如何实现自定义分析器？
**A**: 在索引创建时配置：
```java
client.indices().create(c -> c
    .index("products")
    .settings(s -> s
        .analysis(a -> a
            .analyzer("custom_analyzer", analyzer -> analyzer
                .type("custom")
                .tokenizer("standard")
                .filter("lowercase", "stop")
            )
        )
    )
);
```

---

## 十六、总结与最佳实践

### 🎯 核心建议

1. **新项目**：直接使用 ES 8.x + `elasticsearch-java`
2. **老项目**：逐步迁移，优先升级集群版本
3. **性能优化**：合理配置连接池和批量操作
4. **监控**：实现完善的健康检查和性能监控
5. **测试**：充分的单元测试和集成测试

### 📚 学习资源

- [Elasticsearch 官方文档](https://www.elastic.co/guide/en/elasticsearch/client/java-api-client/current/index.html)
- [Spring Data Elasticsearch](https://docs.spring.io/spring-data/elasticsearch/docs/current/reference/html/)
- [Elasticsearch 最佳实践](https://www.elastic.co/guide/en/elasticsearch/guide/current/index.html)

### 🔮 未来展望

- ES 9.x 将进一步优化 Java 客户端
- 更多 AI/ML 功能集成
- 更好的云原生支持
- 性能持续优化

---

📌 **最终总结**：  
**Elasticsearch 8.x 的新 Java 客户端是一次重大升级，带来了类型安全、函数式 API 和更好的开发体验。虽然学习成本略高，但从长期维护和现代化开发角度看，强烈建议新项目直接使用 8.x 客户端。对于现有项目，建议制定合理的迁移计划，逐步升级。**

---

## 🔗 参考资料

- [Elastic 官方文档 - Java API Client](https://www.elastic.co/guide/en/elasticsearch/client/java-api-client/current/index.html)
- [Migrating from the High Level REST Client](https://www.elastic.co/guide/en/elasticsearch/client/java-api-client/current/migrate-hlrc.html)
- [Spring Data Elasticsearch](https://docs.spring.io/spring-data/elasticsearch/docs/current/reference/html/)
- [Elasticsearch 性能调优指南](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-indexing-speed.html)
- [Elasticsearch 集群管理](https://www.elastic.co/guide/en/elasticsearch/reference/current/cluster.html)

---

📌 **笔记总结**：  
**Elasticsearch 8.x 的新 Java 客户端是一次重大升级，带来了类型安全、函数式 API 和更好的开发体验。虽然学习成本略高，但从长期维护和现代化开发角度看，强烈建议新项目直接使用 8.x 客户端。**