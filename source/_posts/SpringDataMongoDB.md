---
title: Spring Data MongoDB 完整指南
main_color: "#1881a2ff"
categories: ORM
tags:
  - ORM
  - Spring Data
cover: https://free.picui.cn/free/2026/03/29/69c7fb2417b6d.webp
---

# Spring Data MongoDB 完整指南

## 概述

Spring Data MongoDB 是 Spring Data 项目的一部分，提供了基于 MongoDB 文档数据库的 Spring 数据访问技术。它简化了 MongoDB 的使用，提供了类似 JPA 的编程模型。

## 版本依赖

### Maven 依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-mongodb</artifactId>
</dependency>
```

### Gradle 依赖

```gradle
implementation 'org.springframework.boot:spring-boot-starter-data-mongodb'
```

### 版本兼容性

- Spring Boot 2.x: MongoDB 4.x, 5.x
- Spring Boot 3.x: MongoDB 5.x, 6.x, 7.x

## 集成 Spring Boot 项目

### 1. 配置文件 (application.yml)

```yaml
spring:
  data:
    mongodb:
      host: localhost
      port: 27017
      database: mydb
      username: admin
      password: password
      authentication-database: admin
      
      # 连接池配置
      max-connection-pool-size: 100
      min-connection-pool-size: 5
      max-connection-idle-time: 30000
      
      # 超时配置
      connect-timeout: 10000
      socket-timeout: 30000
      server-selection-timeout: 30000
```

### 2. 配置类

```java
@Configuration
@EnableMongoRepositories(basePackages = "com.example.repository")
public class MongoConfig extends AbstractMongoClientConfiguration {
    
    @Value("${spring.data.mongodb.database}")
    private String databaseName;
    
    @Value("${spring.data.mongodb.host}")
    private String host;
    
    @Value("${spring.data.mongodb.port}")
    private int port;
    
    @Override
    protected String getDatabaseName() {
        return databaseName;
    }
    
    @Override
    public MongoClient mongoClient() {
        return MongoClients.create(String.format("mongodb://%s:%d", host, port));
    }
}
```

## 实体映射

### @Document 注解映射 POJO

```java
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.index.CompoundIndex;

@Document(collection = "users")
@CompoundIndex(name = "username_email_idx", def = "{'username': 1, 'email': 1}")
public class User {
    
    @Id
    private String id;
    
    @Indexed(unique = true)
    private String username;
    
    @Field("user_email")
    @Indexed(unique = true)
    private String email;
    
    private String firstName;
    private String lastName;
    
    @Field("created_at")
    private LocalDateTime createdAt;
    
    @Field("updated_at")
    private LocalDateTime updatedAt;
    
    // 嵌套文档
    private Address address;
    
    // 数组字段
    private List<String> roles;
    
    // 构造函数、getter、setter
    // ...
}

@Document
public class Address {
    private String street;
    private String city;
    private String state;
    private String zipCode;
    private String country;
    
    // getter、setter
}
```

### 字段映射注解

- `@Id`: 标识主键字段
- `@Field`: 自定义字段名
- `@Indexed`: 创建索引
- `@CompoundIndex`: 复合索引
- `@TextIndexed`: 全文搜索索引
- `@GeoSpatialIndexed`: 地理空间索引

## Repository 接口

### 使用 MongoRepository 快速实现 DAO 层

```java
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.data.mongodb.repository.Update;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;

public interface UserRepository extends MongoRepository<User, String> {
    
    // 方法名查询
    User findByUsername(String username);
    User findByEmail(String email);
    List<User> findByFirstNameAndLastName(String firstName, String lastName);
    List<User> findByRolesContaining(String role);
    List<User> findByCreatedAtBetween(LocalDateTime start, LocalDateTime end);
    
    // 分页查询
    Page<User> findByRolesContaining(String role, Pageable pageable);
    
    // 排序查询
    List<User> findByFirstNameOrderByCreatedAtDesc(String firstName);
    
    // 限制结果数量
    List<User> findTop5ByOrderByCreatedAtDesc();
    
    // 存在性检查
    boolean existsByUsername(String username);
    long countByRolesContaining(String role);
    
    // 删除操作
    void deleteByUsername(String username);
    long deleteByRolesContaining(String role);
}
```

### 自定义查询方法

```java
public interface UserRepository extends MongoRepository<User, String> {
    
    // 使用 @Query 注解自定义查询
    @Query("{'username': ?0, 'active': true}")
    User findActiveUserByUsername(String username);
    
    @Query("{'$or': [{'firstName': ?0}, {'lastName': ?0}]}")
    List<User> findByFirstNameOrLastName(String name);
    
    @Query("{'createdAt': {$gte: ?0, $lte: ?1}}")
    List<User> findByCreatedAtRange(LocalDateTime start, LocalDateTime end);
    
    // 复杂查询
    @Query("{'$and': [{'roles': ?0}, {'createdAt': {$gte: ?1}}, {'active': true}]}")
    List<User> findActiveUsersByRoleAndDate(String role, LocalDateTime date);
    
    // 使用正则表达式
    @Query("{'username': {$regex: ?0, $options: 'i'}}")
    List<User> findByUsernameLike(String username);
    
    // 聚合查询
    @Query(value = "{}", fields = "{'username': 1, 'email': 1, '_id': 0}")
    List<User> findUsernameAndEmailOnly();
}
```

### 更新操作

```java
public interface UserRepository extends MongoRepository<User, String> {
    
    @Query("{'username': ?0}")
    @Update("{$set: {'lastLoginAt': ?1, 'loginCount': {$inc: 1}}}")
    void updateLastLogin(String username, LocalDateTime lastLoginAt);
    
    @Query("{'username': ?0}")
    @Update("{$push: {'roles': ?1}}")
    void addRole(String username, String role);
    
    @Query("{'username': ?0}")
    @Update("{$pull: {'roles': ?1}}")
    void removeRole(String username, String role);
}
```

## 高级查询功能

### 1. 分页和排序

```java
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    public Page<User> getUsersWithPagination(int page, int size, String sortBy) {
        Pageable pageable = PageRequest.of(page, size, Sort.by(sortBy).ascending());
        return userRepository.findAll(pageable);
    }
    
    public Page<User> getUsersByRoleWithPagination(String role, int page, int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by("createdAt").descending());
        return userRepository.findByRolesContaining(role, pageable);
    }
}
```

### 2. 投影操作

投影是MongoDB中控制查询返回字段的重要功能，可以显著提升查询性能，减少网络传输。

#### 2.1 使用@Query注解进行投影

```java
public interface UserRepository extends MongoRepository<User, String> {
    
    // 只返回用户名和邮箱，排除_id字段
    @Query(value = "{}", fields = "{'username': 1, 'email': 1, '_id': 0}")
    List<User> findUsernameAndEmailOnly();
    
    // 返回用户名、邮箱和创建时间，排除其他字段
    @Query(value = "{}", fields = "{'username': 1, 'email': 1, 'createdAt': 1, '_id': 0}")
    List<User> findUsernameEmailAndCreatedAt();
    
    // 条件查询 + 投影
    @Query(value = "{'roles': ?0}", fields = "{'username': 1, 'firstName': 1, 'lastName': 1, '_id': 0}")
    List<User> findUsersByRoleWithProjection(String role);
    
    // 复杂投影：包含嵌套字段
    @Query(value = "{}", fields = "{'username': 1, 'address.city': 1, 'address.country': 1, '_id': 0}")
    List<User> findUsernameAndAddressInfo();
    
    // 数组字段投影
    @Query(value = "{}", fields = "{'username': 1, 'roles': 1, '_id': 0}")
    List<User> findUsernameAndRoles();
}
```

#### 2.2 使用MongoTemplate进行动态投影

```java
@Service
public class UserProjectionService {
    
    @Autowired
    private MongoTemplate mongoTemplate;
    
    // 动态投影：根据传入的字段列表进行投影
    public List<User> findUsersWithDynamicProjection(List<String> fields) {
        Query query = new Query();
        
        // 构建投影
        for (String field : fields) {
            query.fields().include(field);
        }
        // 始终排除_id字段
        query.fields().exclude("_id");
        
        return mongoTemplate.find(query, User.class);
    }
    
    // 条件查询 + 投影
    public List<User> findActiveUsersWithProjection() {
        Query query = Query.query(Criteria.where("active").is(true));
        query.fields().include("username", "email", "lastLoginAt").exclude("_id");
        
        return mongoTemplate.find(query, User.class);
    }
    
    // 分页 + 投影
    public Page<User> findUsersWithPaginationAndProjection(int page, int size) {
        Query query = new Query();
        query.fields().include("username", "email", "createdAt").exclude("_id");
        
        // 分页
        query.with(PageRequest.of(page, size, Sort.by("createdAt").descending()));
        
        // 计算总数
        long total = mongoTemplate.count(Query.query(Criteria.where("active").is(true)), User.class);
        
        List<User> users = mongoTemplate.find(query, User.class);
        
        return new PageImpl<>(users, PageRequest.of(page, size), total);
    }
}
```

#### 2.3 投影DTO类

```java
// 投影DTO类
public class UserSummary {
    private String username;
    private String email;
    private LocalDateTime createdAt;
    private List<String> roles;
    
    // 构造函数、getter、setter
    public UserSummary() {}
    
    public UserSummary(String username, String email, LocalDateTime createdAt, List<String> roles) {
        this.username = username;
        this.email = email;
        this.createdAt = createdAt;
        this.roles = roles;
    }
    
    // getter和setter方法
    // ...
}

// 在Repository中使用投影DTO
public interface UserRepository extends MongoRepository<User, String> {
    
    // 使用投影DTO返回特定字段
    @Query(value = "{}", fields = "{'username': 1, 'email': 1, 'createdAt': 1, 'roles': 1, '_id': 0}")
    List<UserSummary> findUserSummaries();
    
    // 条件查询 + 投影DTO
    @Query(value = "{'roles': ?0}", fields = "{'username': 1, 'email': 1, 'roles': 1, '_id': 0}")
    List<UserSummary> findUserSummariesByRole(String role);
}
```

#### 2.4 聚合管道中的投影

```java
@Service
public class UserAggregationService {
    
    @Autowired
    private MongoTemplate mongoTemplate;
    
    // 聚合查询中使用投影
    public List<UserStats> getUserStatsWithProjection() {
        Aggregation aggregation = Aggregation.newAggregation(
            // 匹配条件
            Aggregation.match(Criteria.where("active").is(true)),
            
            // 投影阶段：选择需要的字段
            Aggregation.project()
                .and("username").as("username")
                .and("roles").as("roles")
                .and("createdAt").as("createdAt")
                .and(DateOperators.year("createdAt")).as("year")
                .and(DateOperators.month("createdAt")).as("month")
                .andExclude("_id"),
            
            // 分组统计
            Aggregation.group("year", "month")
                .count().as("userCount")
                .addToSet("username").as("usernames"),
            
            // 排序
            Aggregation.sort(Sort.by("year", "month"))
        );
        
        AggregationResults<UserStats> results = mongoTemplate.aggregate(
            aggregation, "users", UserStats.class);
        
        return results.getMappedResults();
    }
    
    // 复杂投影：计算字段和条件投影
    public List<UserAnalytics> getUserAnalyticsWithComputedFields() {
        Aggregation aggregation = Aggregation.newAggregation(
            Aggregation.project()
                .and("username").as("username")
                .and("roles").as("roles")
                .and("createdAt").as("createdAt")
                .and("lastLoginAt").as("lastLoginAt")
                .and(DateOperators.dateDiff("createdAt", "lastLoginAt").unit(DateUnit.DAY)).as("daysSinceLastLogin")
                .and(ConditionalOperators
                    .when(Criteria.where("lastLoginAt").exists(true))
                    .then("active")
                    .otherwise("inactive")).as("status")
                .andExclude("_id"),
            
            Aggregation.match(Criteria.where("status").is("active")),
            
            Aggregation.sort(Sort.by("daysSinceLastLogin").ascending())
        );
        
        AggregationResults<UserAnalytics> results = mongoTemplate.aggregate(
            aggregation, "users", UserAnalytics.class);
        
        return results.getMappedResults();
    }
}

// 聚合结果DTO
public class UserStats {
    private Integer year;
    private Integer month;
    private Long userCount;
    private List<String> usernames;
    
    // getter、setter
}

public class UserAnalytics {
    private String username;
    private List<String> roles;
    private LocalDateTime createdAt;
    private LocalDateTime lastLoginAt;
    private Long daysSinceLastLogin;
    private String status;
    
    // getter、setter
}
```

#### 2.5 投影的最佳实践

```java
@Service
public class UserProjectionBestPractices {
    
    @Autowired
    private MongoTemplate mongoTemplate;
    
    // 1. 始终排除_id字段（除非特别需要）
    public List<User> findUsersExcludingId() {
        Query query = new Query();
        query.fields().exclude("_id");
        return mongoTemplate.find(query, User.class);
    }
    
    // 2. 使用include而不是exclude（更明确）
    public List<User> findUsersWithInclude() {
        Query query = new Query();
        query.fields().include("username", "email", "active");
        // 不需要显式排除_id，include会自动排除其他字段
        return mongoTemplate.find(query, User.class);
    }
    
    // 3. 避免投影嵌套文档的整个对象
    public List<User> findUsersWithSelectiveNestedFields() {
        Query query = new Query();
        // 只选择嵌套文档中的特定字段
        query.fields().include("username", "address.city", "address.country");
        return mongoTemplate.find(query, User.class);
    }
    
    // 4. 使用投影提升查询性能
    public List<User> findUsersForListDisplay() {
        Query query = Query.query(Criteria.where("active").is(true));
        // 只返回列表显示需要的字段
        query.fields().include("username", "email", "lastLoginAt", "roles");
        query.with(Sort.by("username").ascending());
        
        return mongoTemplate.find(query, User.class);
    }
}
```

#### 2.6 投影性能优化示例

```java
@Service
public class UserPerformanceService {
    
    @Autowired
    private MongoTemplate mongoTemplate;
    
    // 性能对比：使用投影 vs 不使用投影
    public void performanceComparison() {
        long startTime = System.currentTimeMillis();
        
        // 不使用投影：返回所有字段
        Query fullQuery = new Query();
        List<User> fullUsers = mongoTemplate.find(fullQuery, User.class);
        
        long fullQueryTime = System.currentTimeMillis() - startTime;
        
        // 使用投影：只返回必要字段
        startTime = System.currentTimeMillis();
        Query projectedQuery = new Query();
        projectedQuery.fields().include("username", "email");
        List<User> projectedUsers = mongoTemplate.find(projectedQuery, User.class);
        
        long projectedQueryTime = System.currentTimeMillis() - startTime;
        
        System.out.println("完整查询时间: " + fullQueryTime + "ms");
        System.out.println("投影查询时间: " + projectedQueryTime + "ms");
        System.out.println("性能提升: " + ((double)(fullQueryTime - projectedQueryTime) / fullQueryTime * 100) + "%");
    }
}
```

### 3. 聚合操作

```java
@Service
public class UserAnalyticsService {
    
    @Autowired
    private MongoTemplate mongoTemplate;
    
    public List<UserStats> getUserStatsByRole() {
        Aggregation aggregation = Aggregation.newAggregation(
            Aggregation.group("roles")
                .count().as("userCount")
                .avg("loginCount").as("avgLoginCount")
                .max("createdAt").as("latestUser")
        );
        
        AggregationResults<UserStats> results = mongoTemplate.aggregate(
            aggregation, "users", UserStats.class);
        
        return results.getMappedResults();
    }
    
    public List<UserActivity> getUserActivityByMonth() {
        Aggregation aggregation = Aggregation.newAggregation(
            Aggregation.project()
                .and(DateOperators.month("createdAt")).as("month")
                .and(DateOperators.year("createdAt")).as("year"),
            Aggregation.group("month", "year")
                .count().as("userCount"),
            Aggregation.sort(Sort.by("year", "month"))
        );
        
        AggregationResults<UserActivity> results = mongoTemplate.aggregate(
            aggregation, "users", UserActivity.class);
        
        return results.getMappedResults();
    }
}
```

### 3. 地理空间查询

```java
@Document
public class Location {
    @Id
    private String id;
    
    @GeoSpatialIndexed(type = GeoSpatialIndexType.GEO_2DSPHERE)
    private Point location;
    
    private String name;
    private String description;
    
    // getter、setter
}

public interface LocationRepository extends MongoRepository<Location, String> {
    
    // 查找指定点附近的文档
    List<Location> findByLocationNear(Point point, Distance distance);
    
    // 查找指定区域内的文档
    List<Location> findByLocationWithin(Box box);
    
    // 查找指定多边形区域内的文档
    List<Location> findByLocationWithin(Polygon polygon);
}
```

## 事务支持

### 配置事务

```java
@Configuration
@EnableMongoRepositories
@EnableTransactionManagement
public class MongoConfig extends AbstractMongoClientConfiguration {
    
    @Bean
    MongoTransactionManager transactionManager(MongoDatabaseFactory dbFactory) {
        return new MongoTransactionManager(dbFactory);
    }
    
    // ... 其他配置
}
```

### 使用事务

```java
@Service
@Transactional
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    @Autowired
    private RoleRepository roleRepository;
    
    public void createUserWithRoles(User user, List<String> roleNames) {
        // 保存用户
        User savedUser = userRepository.save(user);
        
        // 创建角色
        for (String roleName : roleNames) {
            Role role = new Role();
            role.setName(roleName);
            role.setUserId(savedUser.getId());
            roleRepository.save(role);
        }
        
        // 如果任何操作失败，整个事务将回滚
    }
}
```

## 性能优化

### 1. 索引策略

```java
@Document(collection = "users")
@CompoundIndex(name = "username_email_idx", def = "{'username': 1, 'email': 1}")
@CompoundIndex(name = "role_created_idx", def = "{'roles': 1, 'createdAt': -1}")
@TextIndexed(weight = 2)
public class User {
    // ... 字段定义
}
```

### 2. 批量操作

```java
@Service
public class UserBatchService {
    
    @Autowired
    private MongoTemplate mongoTemplate;
    
    public void batchInsertUsers(List<User> users) {
        mongoTemplate.insert(users, User.class);
    }
    
    public void batchUpdateUsers(List<BulkOperations> operations) {
        BulkOperations bulkOps = mongoTemplate.bulkOps(BulkOperations.BulkMode.UNORDERED, User.class);
        
        for (BulkOperations op : operations) {
            bulkOps.updateOne(op.getQuery(), op.getUpdate());
        }
        
        bulkOps.execute();
    }
}
```

### 3. 连接池优化

```yaml
spring:
  data:
    mongodb:
      max-connection-pool-size: 100
      min-connection-pool-size: 10
      max-connection-idle-time: 30000
      max-connection-life-time: 300000
      server-selection-timeout: 30000
      connect-timeout: 10000
      socket-timeout: 30000
```

## 错误处理和监控

### 1. 异常处理

```java
@ControllerAdvice
public class MongoExceptionHandler {
    
    @ExceptionHandler(DuplicateKeyException.class)
    public ResponseEntity<String> handleDuplicateKey(DuplicateKeyException e) {
        return ResponseEntity.badRequest().body("数据已存在");
    }
    
    @ExceptionHandler(DataIntegrityViolationException.class)
    public ResponseEntity<String> handleDataIntegrity(DataIntegrityViolationException e) {
        return ResponseEntity.badRequest().body("数据完整性违反");
    }
}
```

### 2. 健康检查

```java
@Component
public class MongoHealthIndicator implements HealthIndicator {
    
    @Autowired
    private MongoTemplate mongoTemplate;
    
    @Override
    public Health health() {
        try {
            mongoTemplate.executeCommand("{ping: 1}");
            return Health.up().withDetail("database", "MongoDB").build();
        } catch (Exception e) {
            return Health.down()
                .withDetail("database", "MongoDB")
                .withDetail("error", e.getMessage())
                .build();
        }
    }
}
```

## 测试

### 1. 单元测试

```java
@ExtendWith(MockitoExtension.class)
class UserServiceTest {
    
    @Mock
    private UserRepository userRepository;
    
    @InjectMocks
    private UserService userService;
    
    @Test
    void testFindByUsername() {
        // Given
        User user = new User();
        user.setUsername("testuser");
        when(userRepository.findByUsername("testuser")).thenReturn(user);
        
        // When
        User result = userService.findByUsername("testuser");
        
        // Then
        assertThat(result).isNotNull();
        assertThat(result.getUsername()).isEqualTo("testuser");
    }
}
```

### 2. 集成测试

```java
@SpringBootTest
@TestPropertySource(properties = {
    "spring.data.mongodb.database=testdb"
})
@DirtiesContext
class UserRepositoryIntegrationTest {
    
    @Autowired
    private UserRepository userRepository;
    
    @Test
    void testSaveAndFindUser() {
        // Given
        User user = new User();
        user.setUsername("testuser");
        user.setEmail("test@example.com");
        
        // When
        User savedUser = userRepository.save(user);
        User foundUser = userRepository.findByUsername("testuser");
        
        // Then
        assertThat(savedUser.getId()).isNotNull();
        assertThat(foundUser).isNotNull();
        assertThat(foundUser.getUsername()).isEqualTo("testuser");
    }
}
```

## 最佳实践

### 1. 实体设计

- 使用有意义的集合名称
- 合理设计文档结构，避免过深的嵌套
- 适当使用索引提升查询性能
- 考虑文档大小限制（16MB）

### 2. 查询优化

- 使用投影减少数据传输
- 合理使用分页避免大量数据查询
- 利用索引优化查询性能
- 避免使用 `$where` 操作符

### 3. 数据一致性

- 使用事务保证数据一致性
- 合理设计文档结构减少关联查询
- 使用乐观锁处理并发更新

### 4. 监控和维护

- 定期监控查询性能
- 分析慢查询日志
- 优化索引策略
- 监控连接池状态

## 总结

Spring Data MongoDB 提供了强大而灵活的 MongoDB 数据访问能力，通过合理的配置和使用，可以构建高性能、可维护的应用程序。关键点包括：

1. **配置管理**: 合理的连接配置和索引策略
2. **实体映射**: 使用注解进行灵活的文档映射
3. **查询优化**: 利用 Repository 接口和自定义查询
4. **性能调优**: 索引优化、批量操作、连接池管理
5. **事务支持**: 保证数据一致性
6. **监控测试**: 完善的测试和监控体系



