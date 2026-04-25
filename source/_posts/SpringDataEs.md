---
title: Es_SpringData
main_color: "#1881a2ff"
categories: ElasticSearch
tags:
  - Spring Data
cover: https://free.picui.cn/free/2026/03/28/69c74d6d1c35f.png
---

# SpringDataElasticSearch 详细笔记

## 目录
- [1. 简介](#1-简介)
- [2. Maven依赖配置](#2-maven依赖配置)
- [3. 基础配置](#3-基础配置)
- [4. 实体类映射](#4-实体类映射)
- [5. Repository接口](#5-repository接口)
- [6. 查询方法](#6-查询方法)
- [7. 自定义查询](#7-自定义查询)
- [8. 聚合查询](#8-聚合查询)
- [9. 批量操作](#9-批量操作)
- [10. 高级特性](#10-高级特性)
- [11. 完整示例](#11-完整示例)
- [12. 常见问题](#12-常见问题)

## 1. 简介

Spring Data Elasticsearch 是 Spring Data 项目的一部分，提供了对 Elasticsearch 的高级抽象。它简化了 Elasticsearch 的使用，提供了类似 JPA 的编程模型。

### 1.1 主要特性
- **Repository 支持**：提供类似 JPA 的 Repository 接口
- **查询方法**：支持方法名查询和 @Query 注解
- **实体映射**：自动映射 Java 对象到 Elasticsearch 文档
- **分页和排序**：内置分页和排序支持
- **聚合查询**：支持 Elasticsearch 的聚合功能

### 1.2 版本兼容性
| Spring Boot 版本 | Spring Data Elasticsearch 版本 | Elasticsearch 版本 |
|------------------|--------------------------------|-------------------|
| 2.7.x           | 4.4.x                          | 7.17.x            |
| 3.0.x           | 5.0.x                          | 8.x               |
| 3.1.x           | 5.1.x                          | 8.x               |
| 3.2.x           | 5.2.x                          | 8.x               |

## 2. Maven依赖配置

### 2.1 Spring Boot Starter
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-elasticsearch</artifactId>
</dependency>
```

### 2.2 完整依赖示例
```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>
    
    <groupId>com.example</groupId>
    <artifactId>elasticsearch-demo</artifactId>
    <version>1.0.0</version>
    
    <properties>
        <java.version>17</java.version>
    </properties>
    
    <dependencies>
        <!-- Spring Boot Starter -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        
        <!-- Spring Data Elasticsearch -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-elasticsearch</artifactId>
        </dependency>
        
        <!-- 测试依赖 -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        
        <!-- JSON处理 -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
        </dependency>
    </dependencies>
    
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

## 3. 基础配置

### 3.1 application.yml 配置
```yaml
spring:
  elasticsearch:
    uris: http://localhost:9200
    username: elastic
    password: your_password
    connection-timeout: 30s
    socket-timeout: 30s
    
# 或者使用旧版本配置
# spring:
#   data:
#     elasticsearch:
#       repositories:
#         enabled: true
#       cluster-name: elasticsearch
#       cluster-nodes: localhost:9300
```

### 3.2 配置类
```java
@Configuration
@EnableElasticsearchRepositories(basePackages = "com.example.repository")
public class ElasticsearchConfig {
    
    @Bean
    public ElasticsearchOperations elasticsearchTemplate(
            ElasticsearchClient elasticsearchClient) {
        return new ElasticsearchTemplate(elasticsearchClient);
    }
    
    @Bean
    public RestHighLevelClient elasticsearchClient() {
        RestHighLevelClient client = new RestHighLevelClient(
            RestClient.builder(
                new HttpHost("localhost", 9200, "http")
            )
        );
        return client;
    }
}
```

### 3.3 连接池配置
```java
@Configuration
public class ElasticsearchConfig {
    
    @Value("${spring.elasticsearch.uris}")
    private String uris;
    
    @Value("${spring.elasticsearch.username}")
    private String username;
    
    @Value("${spring.elasticsearch.password}")
    private String password;
    
    @Bean
    public ElasticsearchClient elasticsearchClient() {
        // 创建低级客户端
        RestClient restClient = RestClient.builder(
            HttpHost.create(uris)
        ).setHttpClientConfigCallback(httpClientBuilder -> {
            // 设置连接池
            httpClientBuilder.setMaxConnTotal(100);
            httpClientBuilder.setMaxConnPerRoute(20);
            
            // 设置认证
            if (username != null && password != null) {
                CredentialsProvider credentialsProvider = new BasicCredentialsProvider();
                credentialsProvider.setCredentials(AuthScope.ANY,
                    new UsernamePasswordCredentials(username, password));
                httpClientBuilder.setDefaultCredentialsProvider(credentialsProvider);
            }
            
            return httpClientBuilder;
        }).build();
        
        // 创建高级客户端
        return new RestHighLevelClient(restClient);
    }
}
```

## 4. 实体类映射

### 4.1 基础实体类
```java
import org.springframework.data.annotation.Id;
import org.springframework.data.elasticsearch.annotations.Document;
import org.springframework.data.elasticsearch.annotations.Field;
import org.springframework.data.elasticsearch.annotations.FieldType;
import org.springframework.data.elasticsearch.annotations.Setting;

import java.time.LocalDateTime;
import java.util.List;

@Document(indexName = "users")
@Setting(settingPath = "es-settings.json")
public class User {
    
    @Id
    private String id;
    
    @Field(type = FieldType.Text, analyzer = "ik_max_word")
    private String name;
    
    @Field(type = FieldType.Keyword)
    private String email;
    
    @Field(type = FieldType.Integer)
    private Integer age;
    
    @Field(type = FieldType.Date)
    private LocalDateTime createTime;
    
    @Field(type = FieldType.Nested)
    private List<Address> addresses;
    
    @Field(type = FieldType.Object)
    private Profile profile;
    
    // 构造函数
    public User() {}
    
    public User(String name, String email, Integer age) {
        this.name = name;
        this.email = email;
        this.age = age;
        this.createTime = LocalDateTime.now();
    }
    
    // Getter和Setter方法
    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    
    public Integer getAge() { return age; }
    public void setAge(Integer age) { this.age = age; }
    
    public LocalDateTime getCreateTime() { return createTime; }
    public void setCreateTime(LocalDateTime createTime) { this.createTime = createTime; }
    
    public List<Address> getAddresses() { return addresses; }
    public void setAddresses(List<Address> addresses) { this.addresses = addresses; }
    
    public Profile getProfile() { return profile; }
    public void setProfile(Profile profile) { this.profile = profile; }
}
```

### 4.2 嵌套对象
```java
@Document(indexName = "users")
public class Address {
    
    @Field(type = FieldType.Keyword)
    private String city;
    
    @Field(type = FieldType.Keyword)
    private String province;
    
    @Field(type = FieldType.Text)
    private String detail;
    
    // 构造函数和getter/setter
}

public class Profile {
    
    @Field(type = FieldType.Text)
    private String bio;
    
    @Field(type = FieldType.Keyword)
    private String avatar;
    
    @Field(type = FieldType.Object)
    private Map<String, Object> metadata;
    
    // 构造函数和getter/setter
}
```

### 4.3 索引设置文件 (es-settings.json)
```json
{
  "analysis": {
    "analyzer": {
      "ik_max_word": {
        "type": "ik_max_word"
      },
      "ik_smart": {
        "type": "ik_smart"
      }
    }
  },
  "number_of_shards": 1,
  "number_of_replicas": 0
}
```

## 5. Repository接口

### 5.1 基础Repository
```java
import org.springframework.data.elasticsearch.repository.ElasticsearchRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface UserRepository extends ElasticsearchRepository<User, String> {
    // 继承的基础方法：
    // save(), saveAll(), findById(), findAll(), delete(), deleteAll() 等
}
```

### 5.2 自定义Repository
```java
public interface CustomUserRepository {
    List<User> findByCustomQuery(String keyword);
    void updateUserAge(String id, Integer age);
}

@Repository
public class CustomUserRepositoryImpl implements CustomUserRepository {
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    @Override
    public List<User> findByCustomQuery(String keyword) {
        Criteria criteria = new Criteria("name").contains(keyword)
            .or("email").contains(keyword);
        Query query = new CriteriaQuery(criteria);
        return elasticsearchOperations.search(query, User.class)
            .getSearchHits().stream()
            .map(SearchHit::getContent)
            .collect(Collectors.toList());
    }
    
    @Override
    public void updateUserAge(String id, Integer age) {
        UpdateQuery updateQuery = UpdateQuery.builder(id)
            .withScript(new Script(ScriptType.INLINE, "painless",
                "ctx._source.age = params.age", Map.of("age", age)))
            .build();
        elasticsearchOperations.update(updateQuery, IndexCoordinates.of("users"));
    }
}
```

## 6. 查询方法

### 6.1 方法名查询
```java
@Repository
public interface UserRepository extends ElasticsearchRepository<User, String> {
    
    // 精确匹配
    List<User> findByName(String name);
    User findByEmail(String email);
    
    // 模糊查询
    List<User> findByNameContaining(String name);
    List<User> findByNameLike(String name);
    
    // 范围查询
    List<User> findByAgeBetween(Integer minAge, Integer maxAge);
    List<User> findByAgeGreaterThan(Integer age);
    List<User> findByAgeLessThan(Integer age);
    
    // 多条件查询
    List<User> findByNameAndAge(String name, Integer age);
    List<User> findByNameOrEmail(String name, String email);
    
    // 排序
    List<User> findByAgeOrderByNameAsc(Integer age);
    List<User> findByAgeOrderByCreateTimeDesc(Integer age);
    
    // 分页
    Page<User> findByAge(Integer age, Pageable pageable);
    
    // 限制结果数量
    List<User> findTop3ByAgeOrderByCreateTimeDesc(Integer age);
    
    // 存在性检查
    boolean existsByEmail(String email);
    long countByAge(Integer age);
    
    // 删除
    void deleteByEmail(String email);
    long deleteByAge(Integer age);
}
```

### 6.2 @Query注解查询
```java
@Repository
public interface UserRepository extends ElasticsearchRepository<User, String> {
    
    // 简单查询
    @Query("{\"match\": {\"name\": \"?0\"}}")
    List<User> findByNameMatch(String name);
    
    // 多字段查询
    @Query("{\"multi_match\": {\"query\": \"?0\", \"fields\": [\"name\", \"email\"]}}")
    List<User> findByNameOrEmail(String keyword);
    
    // 范围查询
    @Query("{\"range\": {\"age\": {\"gte\": ?0, \"lte\": ?1}}}")
    List<User> findByAgeRange(Integer minAge, Integer maxAge);
    
    // 复合查询
    @Query("{\"bool\": {\"must\": [{\"match\": {\"name\": \"?0\"}}, {\"range\": {\"age\": {\"gte\": ?1}}}]}}")
    List<User> findByNameAndAgeGreaterThan(String name, Integer age);
    
    // 聚合查询
    @Query("{\"aggs\": {\"age_stats\": {\"stats\": {\"field\": \"age\"}}}}")
    SearchHits<User> findWithAgeStats();
    
    // 嵌套查询
    @Query("{\"nested\": {\"path\": \"addresses\", \"query\": {\"bool\": {\"must\": [{\"match\": {\"addresses.city\": \"?0\"}}]}}}}")
    List<User> findByAddressCity(String city);
}
```

### 6.3 原生查询
```java
@Service
public class UserService {
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    public List<User> searchUsers(String keyword) {
        // 构建查询
        BoolQueryBuilder boolQuery = QueryBuilders.boolQuery()
            .should(QueryBuilders.matchQuery("name", keyword))
            .should(QueryBuilders.matchQuery("email", keyword))
            .minimumShouldMatch(1);
        
        // 创建查询对象
        NativeQuery query = NativeQuery.builder()
            .withQuery(boolQuery)
            .withSort(Sort.by(Sort.Direction.DESC, "createTime"))
            .withPageable(PageRequest.of(0, 10))
            .build();
        
        // 执行查询
        SearchHits<User> searchHits = elasticsearchOperations.search(query, User.class);
        
        return searchHits.getSearchHits().stream()
            .map(SearchHit::getContent)
            .collect(Collectors.toList());
    }
    
    public List<User> searchUsersWithHighlight(String keyword) {
        // 高亮查询
        NativeQuery query = NativeQuery.builder()
            .withQuery(QueryBuilders.matchQuery("name", keyword))
            .withHighlightQuery(new HighlightQuery(
                new HighlightBuilder().field("name").preTags("<em>").postTags("</em>"),
                User.class
            ))
            .build();
        
        return elasticsearchOperations.search(query, User.class)
            .getSearchHits().stream()
            .map(SearchHit::getContent)
            .collect(Collectors.toList());
    }
}
```

## 7. 自定义查询

### 7.1 Criteria查询
```java
@Service
public class UserService {
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    public List<User> findByCriteria(String name, Integer minAge, String city) {
        Criteria criteria = new Criteria();
        
        if (name != null) {
            criteria = criteria.and("name").contains(name);
        }
        
        if (minAge != null) {
            criteria = criteria.and("age").greaterThanEqual(minAge);
        }
        
        if (city != null) {
            criteria = criteria.and("addresses.city").is(city);
        }
        
        Query query = new CriteriaQuery(criteria);
        return elasticsearchOperations.search(query, User.class)
            .getSearchHits().stream()
            .map(SearchHit::getContent)
            .collect(Collectors.toList());
    }
    
    public List<User> findByComplexCriteria(String keyword, Integer age, String sortBy) {
        Criteria criteria = new Criteria("name").contains(keyword)
            .or("email").contains(keyword)
            .and("age").greaterThanEqual(age);
        
        CriteriaQuery query = new CriteriaQuery(criteria);
        
        if (sortBy != null) {
            query.addSort(Sort.by(Sort.Direction.DESC, sortBy));
        }
        
        return elasticsearchOperations.search(query, User.class)
            .getSearchHits().stream()
            .map(SearchHit::getContent)
            .collect(Collectors.toList());
    }
}
```

### 7.2 函数式查询
```java
@Service
public class UserService {
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    public List<User> findUsersWithFunction() {
        // 使用函数式查询
        Query query = new CriteriaQuery(
            new Criteria("age").between(18, 65)
                .and("name").contains("张")
                .and("createTime").greaterThan(LocalDateTime.now().minusDays(30))
        );
        
        return elasticsearchOperations.search(query, User.class)
            .getSearchHits().stream()
            .map(SearchHit::getContent)
            .collect(Collectors.toList());
    }
    
    public List<User> findUsersWithWildcard() {
        // 通配符查询
        Query query = new CriteriaQuery(
            new Criteria("name").matches("张*")
                .or("email").matches("*@gmail.com")
        );
        
        return elasticsearchOperations.search(query, User.class)
            .getSearchHits().stream()
            .map(SearchHit::getContent)
            .collect(Collectors.toList());
    }
}
```

## 8. 聚合查询

### 8.1 基础聚合
```java
@Service
public class UserService {
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    public Map<String, Object> getAgeStats() {
        // 统计聚合
        NativeQuery query = NativeQuery.builder()
            .withAggregation("age_stats", AggregationBuilders.stats("age_stats").field("age"))
            .withMaxResults(0) // 不返回文档，只返回聚合结果
            .build();
        
        SearchHits<User> searchHits = elasticsearchOperations.search(query, User.class);
        AggregationsContainer<?> aggregations = searchHits.getAggregations();
        
        Map<String, Object> result = new HashMap<>();
        if (aggregations != null) {
            StatsAggregation ageStats = aggregations.get("age_stats");
            result.put("count", ageStats.getCount());
            result.put("min", ageStats.getMin());
            result.put("max", ageStats.getMax());
            result.put("avg", ageStats.getAvg());
            result.put("sum", ageStats.getSum());
        }
        
        return result;
    }
    
    public List<Map<String, Object>> getAgeDistribution() {
        // 分组聚合
        NativeQuery query = NativeQuery.builder()
            .withAggregation("age_groups", 
                AggregationBuilders.terms("age_groups").field("age"))
            .withMaxResults(0)
            .build();
        
        SearchHits<User> searchHits = elasticsearchOperations.search(query, User.class);
        AggregationsContainer<?> aggregations = searchHits.getAggregations();
        
        List<Map<String, Object>> result = new ArrayList<>();
        if (aggregations != null) {
            TermsAggregation ageGroups = aggregations.get("age_groups");
            for (TermsAggregation.Entry entry : ageGroups.getTerms()) {
                Map<String, Object> group = new HashMap<>();
                group.put("age", entry.getKey());
                group.put("count", entry.getDocCount());
                result.add(group);
            }
        }
        
        return result;
    }
}
```

### 8.2 复杂聚合
```java
@Service
public class UserService {
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    public Map<String, Object> getComplexAggregations() {
        // 多级聚合
        NativeQuery query = NativeQuery.builder()
            .withAggregation("city_stats", 
                AggregationBuilders.terms("city_stats").field("addresses.city")
                    .subAggregation("avg_age", 
                        AggregationBuilders.avg("avg_age").field("age"))
                    .subAggregation("user_count", 
                        AggregationBuilders.count("user_count").field("id")))
            .withMaxResults(0)
            .build();
        
        SearchHits<User> searchHits = elasticsearchOperations.search(query, User.class);
        AggregationsContainer<?> aggregations = searchHits.getAggregations();
        
        Map<String, Object> result = new HashMap<>();
        if (aggregations != null) {
            TermsAggregation cityStats = aggregations.get("city_stats");
            List<Map<String, Object>> cityData = new ArrayList<>();
            
            for (TermsAggregation.Entry entry : cityStats.getTerms()) {
                Map<String, Object> city = new HashMap<>();
                city.put("city", entry.getKey());
                city.put("count", entry.getDocCount());
                
                // 获取子聚合
                AvgAggregation avgAge = entry.getAggregations().get("avg_age");
                ValueCountAggregation userCount = entry.getAggregations().get("user_count");
                
                city.put("avgAge", avgAge.getValue());
                city.put("userCount", userCount.getValue());
                cityData.add(city);
            }
            
            result.put("cities", cityData);
        }
        
        return result;
    }
    
    public List<Map<String, Object>> getDateHistogram() {
        // 时间直方图聚合
        NativeQuery query = NativeQuery.builder()
            .withAggregation("daily_users", 
                AggregationBuilders.dateHistogram("daily_users")
                    .field("createTime")
                    .calendarInterval(DateHistogramInterval.DAY))
            .withMaxResults(0)
            .build();
        
        SearchHits<User> searchHits = elasticsearchOperations.search(query, User.class);
        AggregationsContainer<?> aggregations = searchHits.getAggregations();
        
        List<Map<String, Object>> result = new ArrayList<>();
        if (aggregations != null) {
            DateHistogramAggregation dailyUsers = aggregations.get("daily_users");
            for (DateHistogramAggregation.Entry entry : dailyUsers.getBuckets()) {
                Map<String, Object> day = new HashMap<>();
                day.put("date", entry.getKeyAsString());
                day.put("count", entry.getDocCount());
                result.add(day);
            }
        }
        
        return result;
    }
}
```

## 9. 批量操作

### 9.1 批量保存
```java
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    public void saveUsersBatch(List<User> users) {
        // 使用Repository批量保存
        userRepository.saveAll(users);
    }
    
    public void saveUsersBatchWithOperations(List<User> users) {
        // 使用ElasticsearchOperations批量保存
        List<IndexQuery> queries = users.stream()
            .map(user -> new IndexQueryBuilder()
                .withId(user.getId())
                .withObject(user)
                .build())
            .collect(Collectors.toList());
        
        elasticsearchOperations.bulkIndex(queries, IndexCoordinates.of("users"));
    }
    
    public void saveUsersBatchWithBulkProcessor(List<User> users) {
        // 使用BulkProcessor批量保存
        BulkOperations bulkOperations = elasticsearchOperations.bulkOps(BulkOperations.BulkMode.INDEX, User.class);
        
        for (User user : users) {
            bulkOperations.insert(user);
        }
        
        BulkOperations.BulkResult result = bulkOperations.execute();
        System.out.println("批量保存完成，处理了 " + result.getTotalCount() + " 个文档");
    }
}
```

### 9.2 批量更新
```java
@Service
public class UserService {
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    public void updateUsersAgeBatch(Map<String, Integer> userIdToAge) {
        List<UpdateQuery> updateQueries = userIdToAge.entrySet().stream()
            .map(entry -> UpdateQuery.builder(entry.getKey())
                .withScript(new Script(ScriptType.INLINE, "painless",
                    "ctx._source.age = params.age", Map.of("age", entry.getValue())))
                .build())
            .collect(Collectors.toList());
        
        elasticsearchOperations.bulkUpdate(updateQueries, IndexCoordinates.of("users"));
    }
    
    public void updateUsersByQuery(String field, Object value, String script) {
        // 根据查询条件批量更新
        UpdateQuery updateQuery = UpdateQuery.builder()
            .withQuery(QueryBuilders.matchQuery(field, value))
            .withScript(new Script(ScriptType.INLINE, "painless", script))
            .build();
        
        elasticsearchOperations.update(updateQuery, IndexCoordinates.of("users"));
    }
}
```

### 9.3 批量删除
```java
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    public void deleteUsersBatch(List<String> userIds) {
        // 使用Repository批量删除
        userRepository.deleteAllById(userIds);
    }
    
    public void deleteUsersByQuery(String field, Object value) {
        // 根据查询条件批量删除
        Query query = new CriteriaQuery(new Criteria(field).is(value));
        elasticsearchOperations.delete(query, User.class);
    }
    
    public void deleteUsersByAgeRange(Integer minAge, Integer maxAge) {
        // 根据年龄范围批量删除
        Query query = new CriteriaQuery(
            new Criteria("age").between(minAge, maxAge)
        );
        elasticsearchOperations.delete(query, User.class);
    }
}
```

## 10. 高级特性

### 10.1 索引管理
```java
@Service
public class IndexService {
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    public void createIndex(String indexName) {
        // 创建索引
        IndexCoordinates indexCoordinates = IndexCoordinates.of(indexName);
        boolean exists = elasticsearchOperations.indexExists(indexCoordinates);
        
        if (!exists) {
            elasticsearchOperations.indexOps(indexCoordinates).create();
            System.out.println("索引 " + indexName + " 创建成功");
        } else {
            System.out.println("索引 " + indexName + " 已存在");
        }
    }
    
    public void deleteIndex(String indexName) {
        // 删除索引
        IndexCoordinates indexCoordinates = IndexCoordinates.of(indexName);
        boolean exists = elasticsearchOperations.indexExists(indexCoordinates);
        
        if (exists) {
            elasticsearchOperations.indexOps(indexCoordinates).delete();
            System.out.println("索引 " + indexName + " 删除成功");
        } else {
            System.out.println("索引 " + indexName + " 不存在");
        }
    }
    
    public void updateIndexMapping(String indexName) {
        // 更新索引映射
        IndexCoordinates indexCoordinates = IndexCoordinates.of(indexName);
        IndexOperations indexOps = elasticsearchOperations.indexOps(indexCoordinates);
        
        // 获取当前映射
        Document mapping = indexOps.getMapping();
        System.out.println("当前映射: " + mapping);
        
        // 更新映射（需要重新创建索引）
        // 注意：Elasticsearch不允许直接更新映射，需要重建索引
    }
}
```

### 10.2 别名管理
```java
@Service
public class AliasService {
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    public void createAlias(String indexName, String aliasName) {
        // 创建别名
        IndexCoordinates indexCoordinates = IndexCoordinates.of(indexName);
        IndexOperations indexOps = elasticsearchOperations.indexOps(indexCoordinates);
        
        AliasActions aliasActions = new AliasActions();
        aliasActions.add(new AliasAction.Add(AliasActionParameters.builder()
            .withIndices(indexName)
            .withAliases(aliasName)
            .build()));
        
        indexOps.alias(aliasActions);
        System.out.println("别名 " + aliasName + " 创建成功");
    }
    
    public void switchAlias(String oldIndex, String newIndex, String aliasName) {
        // 切换别名（零停机时间）
        IndexOperations oldIndexOps = elasticsearchOperations.indexOps(IndexCoordinates.of(oldIndex));
        IndexOperations newIndexOps = elasticsearchOperations.indexOps(IndexCoordinates.of(newIndex));
        
        AliasActions aliasActions = new AliasActions();
        aliasActions.add(new AliasAction.Remove(AliasActionParameters.builder()
            .withIndices(oldIndex)
            .withAliases(aliasName)
            .build()));
        aliasActions.add(new AliasAction.Add(AliasActionParameters.builder()
            .withIndices(newIndex)
            .withAliases(aliasName)
            .build()));
        
        oldIndexOps.alias(aliasActions);
        System.out.println("别名 " + aliasName + " 从 " + oldIndex + " 切换到 " + newIndex);
    }
}
```

### 10.3 模板管理
```java
@Service
public class TemplateService {
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    public void createIndexTemplate(String templateName, String indexPattern) {
        // 创建索引模板
        IndexTemplate indexTemplate = IndexTemplate.builder()
            .name(templateName)
            .indexPatterns(indexPattern)
            .settings(Map.of(
                "number_of_shards", 1,
                "number_of_replicas", 0
            ))
            .mappings(Map.of(
                "properties", Map.of(
                    "name", Map.of("type", "text", "analyzer", "ik_max_word"),
                    "age", Map.of("type", "integer"),
                    "createTime", Map.of("type", "date")
                )
            ))
            .build();
        
        elasticsearchOperations.indexOps(IndexCoordinates.of("_template"))
            .putTemplate(indexTemplate);
        
        System.out.println("索引模板 " + templateName + " 创建成功");
    }
}
```

## 11. 完整示例

### 11.1 完整的用户管理系统
```java
// 主应用类
@SpringBootApplication
@EnableElasticsearchRepositories(basePackages = "com.example.repository")
public class ElasticsearchApplication {
    public static void main(String[] args) {
        SpringApplication.run(ElasticsearchApplication.class, args);
    }
}

// 控制器
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @PostMapping
    public ResponseEntity<User> createUser(@RequestBody User user) {
        User savedUser = userService.saveUser(user);
        return ResponseEntity.ok(savedUser);
    }
    
    @GetMapping("/{id}")
    public ResponseEntity<User> getUser(@PathVariable String id) {
        Optional<User> user = userService.findById(id);
        return user.map(ResponseEntity::ok)
            .orElse(ResponseEntity.notFound().build());
    }
    
    @GetMapping
    public ResponseEntity<Page<User>> getUsers(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size,
            @RequestParam(required = false) String name,
            @RequestParam(required = false) Integer minAge) {
        
        Page<User> users = userService.findUsers(page, size, name, minAge);
        return ResponseEntity.ok(users);
    }
    
    @PutMapping("/{id}")
    public ResponseEntity<User> updateUser(@PathVariable String id, @RequestBody User user) {
        User updatedUser = userService.updateUser(id, user);
        return ResponseEntity.ok(updatedUser);
    }
    
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable String id) {
        userService.deleteUser(id);
        return ResponseEntity.ok().build();
    }
    
    @GetMapping("/search")
    public ResponseEntity<List<User>> searchUsers(@RequestParam String keyword) {
        List<User> users = userService.searchUsers(keyword);
        return ResponseEntity.ok(users);
    }
    
    @GetMapping("/stats")
    public ResponseEntity<Map<String, Object>> getUserStats() {
        Map<String, Object> stats = userService.getUserStats();
        return ResponseEntity.ok(stats);
    }
}

// 服务类
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    @Autowired
    private ElasticsearchOperations elasticsearchOperations;
    
    public User saveUser(User user) {
        if (user.getId() == null) {
            user.setId(UUID.randomUUID().toString());
        }
        user.setCreateTime(LocalDateTime.now());
        return userRepository.save(user);
    }
    
    public Optional<User> findById(String id) {
        return userRepository.findById(id);
    }
    
    public Page<User> findUsers(int page, int size, String name, Integer minAge) {
        Pageable pageable = PageRequest.of(page, size, Sort.by("createTime").descending());
        
        if (name != null || minAge != null) {
            Criteria criteria = new Criteria();
            if (name != null) {
                criteria = criteria.and("name").contains(name);
            }
            if (minAge != null) {
                criteria = criteria.and("age").greaterThanEqual(minAge);
            }
            
            Query query = new CriteriaQuery(criteria);
            query.setPageable(pageable);
            
            SearchHits<User> searchHits = elasticsearchOperations.search(query, User.class);
            List<User> users = searchHits.getSearchHits().stream()
                .map(SearchHit::getContent)
                .collect(Collectors.toList());
            
            return new PageImpl<>(users, pageable, searchHits.getTotalHits());
        } else {
            return userRepository.findAll(pageable);
        }
    }
    
    public User updateUser(String id, User user) {
        Optional<User> existingUser = userRepository.findById(id);
        if (existingUser.isPresent()) {
            User existing = existingUser.get();
            existing.setName(user.getName());
            existing.setEmail(user.getEmail());
            existing.setAge(user.getAge());
            existing.setAddresses(user.getAddresses());
            existing.setProfile(user.getProfile());
            return userRepository.save(existing);
        }
        throw new RuntimeException("User not found with id: " + id);
    }
    
    public void deleteUser(String id) {
        userRepository.deleteById(id);
    }
    
    public List<User> searchUsers(String keyword) {
        NativeQuery query = NativeQuery.builder()
            .withQuery(QueryBuilders.multiMatchQuery(keyword, "name", "email"))
            .withSort(Sort.by(Sort.Direction.DESC, "createTime"))
            .build();
        
        return elasticsearchOperations.search(query, User.class)
            .getSearchHits().stream()
            .map(SearchHit::getContent)
            .collect(Collectors.toList());
    }
    
    public Map<String, Object> getUserStats() {
        NativeQuery query = NativeQuery.builder()
            .withAggregation("age_stats", 
                AggregationBuilders.stats("age_stats").field("age"))
            .withAggregation("city_distribution", 
                AggregationBuilders.terms("city_distribution").field("addresses.city"))
            .withMaxResults(0)
            .build();
        
        SearchHits<User> searchHits = elasticsearchOperations.search(query, User.class);
        AggregationsContainer<?> aggregations = searchHits.getAggregations();
        
        Map<String, Object> stats = new HashMap<>();
        if (aggregations != null) {
            // 年龄统计
            StatsAggregation ageStats = aggregations.get("age_stats");
            Map<String, Object> ageData = new HashMap<>();
            ageData.put("count", ageStats.getCount());
            ageData.put("min", ageStats.getMin());
            ageData.put("max", ageStats.getMax());
            ageData.put("avg", ageStats.getAvg());
            stats.put("ageStats", ageData);
            
            // 城市分布
            TermsAggregation cityDistribution = aggregations.get("city_distribution");
            List<Map<String, Object>> cityData = new ArrayList<>();
            for (TermsAggregation.Entry entry : cityDistribution.getTerms()) {
                Map<String, Object> city = new HashMap<>();
                city.put("city", entry.getKey());
                city.put("count", entry.getDocCount());
                cityData.add(city);
            }
            stats.put("cityDistribution", cityData);
        }
        
        return stats;
    }
}
```

### 11.2 测试类
```java
@SpringBootTest
class UserServiceTest {
    
    @Autowired
    private UserService userService;
    
    @Autowired
    private UserRepository userRepository;
    
    @Test
    void testSaveAndFindUser() {
        // 创建用户
        User user = new User("张三", "zhangsan@example.com", 25);
        user.setAddresses(Arrays.asList(
            new Address("北京", "北京市", "朝阳区xxx街道")
        ));
        
        User savedUser = userService.saveUser(user);
        assertNotNull(savedUser.getId());
        assertEquals("张三", savedUser.getName());
        
        // 查找用户
        Optional<User> foundUser = userService.findById(savedUser.getId());
        assertTrue(foundUser.isPresent());
        assertEquals("张三", foundUser.get().getName());
    }
    
    @Test
    void testSearchUsers() {
        // 创建测试数据
        User user1 = new User("李四", "lisi@example.com", 30);
        User user2 = new User("王五", "wangwu@example.com", 35);
        userService.saveUser(user1);
        userService.saveUser(user2);
        
        // 搜索用户
        List<User> users = userService.searchUsers("李四");
        assertEquals(1, users.size());
        assertEquals("李四", users.get(0).getName());
    }
    
    @Test
    void testGetUserStats() {
        // 创建测试数据
        User user1 = new User("张三", "zhangsan@example.com", 25);
        User user2 = new User("李四", "lisi@example.com", 30);
        userService.saveUser(user1);
        userService.saveUser(user2);
        
        // 获取统计信息
        Map<String, Object> stats = userService.getUserStats();
        assertNotNull(stats);
        assertTrue(stats.containsKey("ageStats"));
    }
}
```

## 12. 常见问题

### 12.1 连接问题
```java
// 问题：连接超时
// 解决方案：调整连接配置
spring:
  elasticsearch:
    uris: http://localhost:9200
    connection-timeout: 60s
    socket-timeout: 60s
    max-in-memory-size: 100MB

// 问题：认证失败
// 解决方案：检查用户名密码
spring:
  elasticsearch:
    username: elastic
    password: your_password
```

### 12.2 映射问题
```java
// 问题：字段类型不匹配
// 解决方案：使用@Field注解指定类型
@Field(type = FieldType.Text, analyzer = "ik_max_word")
private String name;

@Field(type = FieldType.Keyword)
private String email;

// 问题：日期格式问题
// 解决方案：指定日期格式
@Field(type = FieldType.Date, format = DateFormat.basic_date_time)
private LocalDateTime createTime;
```

### 12.3 查询问题
```java
// 问题：中文分词不生效
// 解决方案：使用IK分词器
@Field(type = FieldType.Text, analyzer = "ik_max_word", searchAnalyzer = "ik_smart")
private String content;

// 问题：嵌套查询不工作
// 解决方案：使用正确的嵌套查询语法
@Query("{\"nested\": {\"path\": \"addresses\", \"query\": {\"bool\": {\"must\": [{\"match\": {\"addresses.city\": \"?0\"}}]}}}}")
List<User> findByAddressCity(String city);
```

### 12.4 性能优化
```java
// 1. 使用批量操作
public void batchSave(List<User> users) {
    userRepository.saveAll(users);
}

// 2. 使用滚动查询处理大量数据
public void processLargeDataset() {
    SearchScrollHits<User> scroll = elasticsearchOperations.searchScrollStart(
        0, SearchScrollHits.class, User.class, IndexCoordinates.of("users"));
    
    String scrollId = scroll.getScrollId();
    while (scroll.hasSearchHits()) {
        // 处理当前批次的数据
        for (SearchHit<User> searchHit : scroll.getSearchHits()) {
            User user = searchHit.getContent();
            // 处理用户数据
        }
        
        scroll = elasticsearchOperations.searchScrollContinue(
            scrollId, SearchScrollHits.class, User.class);
    }
    
    elasticsearchOperations.searchScrollClear(Arrays.asList(scrollId));
}

// 3. 使用索引别名实现零停机时间
public void reindexWithAlias(String oldIndex, String newIndex, String alias) {
    // 创建新索引
    createIndex(newIndex);
    
    // 重建索引数据
    reindexData(oldIndex, newIndex);
    
    // 切换别名
    switchAlias(oldIndex, newIndex, alias);
    
    // 删除旧索引
    deleteIndex(oldIndex);
}
```

### 12.5 监控和日志
```java
// 添加监控配置
@Configuration
public class ElasticsearchConfig {
    
    @Bean
    public ElasticsearchOperations elasticsearchTemplate(
            ElasticsearchClient elasticsearchClient) {
        
        // 添加请求监听器
        RestClient restClient = ((RestHighLevelClient) elasticsearchClient).getLowLevelClient();
        
        return new ElasticsearchTemplate(elasticsearchClient) {
            @Override
            public <T> SearchHits<T> search(Query query, Class<T> clazz) {
                long startTime = System.currentTimeMillis();
                try {
                    SearchHits<T> result = super.search(query, clazz);
                    long duration = System.currentTimeMillis() - startTime;
                    log.info("Elasticsearch query executed in {}ms", duration);
                    return result;
                } catch (Exception e) {
                    log.error("Elasticsearch query failed", e);
                    throw e;
                }
            }
        };
    }
}
```

## 总结

Spring Data Elasticsearch 提供了强大的 Elasticsearch 集成能力，通过本文档的学习，你应该能够：

1. **配置和连接**：正确配置 Spring Boot 与 Elasticsearch 的连接
2. **实体映射**：使用注解正确映射 Java 对象到 Elasticsearch 文档
3. **查询操作**：使用 Repository 接口和自定义查询进行数据检索
4. **聚合分析**：执行复杂的聚合查询和统计分析
5. **批量操作**：高效处理大量数据的增删改查
6. **高级特性**：管理索引、别名、模板等高级功能
7. **性能优化**：通过最佳实践提升查询和操作性能
8. **问题排查**：解决常见的连接、映射、查询等问题

Spring Data Elasticsearch 让 Elasticsearch 的使用变得更加简单和高效，特别适合在 Spring Boot 项目中进行全文搜索、日志分析、数据聚合等场景。
