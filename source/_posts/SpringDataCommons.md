---
title: Spring Data Commons 完整指南
main_color: "rgb(11, 32, 228)"
categories: Spring Data
tags:
  - Spring Data
cover: https://free.picui.cn/free/2026/03/28/69c74d6d1c35f.png
---

# Spring Data Commons 完整指南

## 概述

Spring Data Commons 是 Spring Data 项目的核心模块，为所有 Spring Data 子项目提供通用的基础设施和抽象。它定义了数据访问的核心概念、接口和工具类，使得不同的数据存储技术能够以统一的方式进行操作。

## 设计思想

### 1. 统一抽象层

Spring Data Commons 的核心设计思想是提供一个统一的数据访问抽象层，无论底层使用什么数据存储技术（关系型数据库、NoSQL、搜索引擎等），开发者都可以使用相同的编程模型。

**核心原则：**
- **Repository 模式**：提供统一的数据访问接口
- **领域驱动设计**：以实体对象为中心，而非数据表
- **声明式查询**：通过方法名或注解自动生成查询
- **类型安全**：利用泛型和反射提供编译时类型检查

### 2. 分层架构设计

```
┌─────────────────────────────────────┐
│          应用层 (Application)        │
├─────────────────────────────────────┤
│        服务层 (Service Layer)        │
├─────────────────────────────────────┤
│      Repository 接口层              │
├─────────────────────────────────────┤
│      Spring Data Commons            │
├─────────────────────────────────────┤
│      具体数据存储实现                │
│   (JPA, MongoDB, Redis, ES等)      │
└─────────────────────────────────────┘
```

### 3. 约定优于配置

Spring Data Commons 遵循"约定优于配置"的原则，通过合理的默认行为和命名约定，减少配置代码，提高开发效率。

## 核心模块详解

### 1. Repository 接口体系

#### 1.1 Repository 基础接口

```java
// 标记接口，用于标识数据访问对象
public interface Repository<T, ID> {
    // 不包含任何方法，仅作为标记
}
```

#### 1.2 CrudRepository 接口

提供基本的 CRUD 操作：

```java
public interface CrudRepository<T, ID> extends Repository<T, ID> {
    
    // 保存实体
    <S extends T> S save(S entity);
    
    // 批量保存
    <S extends T> Iterable<S> saveAll(Iterable<S> entities);
    
    // 根据ID查找
    Optional<T> findById(ID id);
    
    // 检查是否存在
    boolean existsById(ID id);
    
    // 查找所有
    Iterable<T> findAll();
    
    // 根据ID集合查找
    Iterable<T> findAllById(Iterable<ID> ids);
    
    // 统计总数
    long count();
    
    // 根据ID删除
    void deleteById(ID id);
    
    // 删除实体
    void delete(T entity);
    
    // 批量删除
    void deleteAllById(Iterable<? extends ID> ids);
    
    // 删除所有
    void deleteAll(Iterable<? extends T> entities);
    
    // 删除所有
    void deleteAll();
}
```

#### 1.3 PagingAndSortingRepository 接口

扩展分页和排序功能：

```java
public interface PagingAndSortingRepository<T, ID> extends CrudRepository<T, ID> {
    
    // 查找所有并排序
    Iterable<T> findAll(Sort sort);
    
    // 分页查找
    Page<T> findAll(Pageable pageable);
}
```

#### 1.4 JpaRepository 接口 (JPA专用)

```java
public interface JpaRepository<T, ID> extends PagingAndSortingRepository<T, ID>, QueryByExampleExecutor<T> {
    
    // 刷新实体
    void flush();
    
    // 保存并刷新
    <S extends T> S saveAndFlush(S entity);
    
    // 批量刷新
    void saveAllAndFlush(Iterable<S> entities);
    
    // 批量删除
    void deleteAllInBatch(Iterable<T> entities);
    
    // 删除所有
    void deleteAllInBatch();
    
    // 获取引用
    T getReferenceById(ID id);
    
    // 获取一个
    T getOne(ID id);
    
    // 获取引用
    T getById(ID id);
    
    // 查找所有
    List<T> findAll();
    
    // 根据ID查找
    List<T> findAllById(Iterable<ID> ids);
    
    // 保存所有
    <S extends T> List<S> saveAll(Iterable<S> entities);
    
    // 批量删除
    void deleteAllByIdInBatch(Iterable<ID> ids);
}
```

### 2. 分页和排序

#### 2.1 Pageable 接口

```java
public interface Pageable {
    
    // 获取页码（从0开始）
    int getPageNumber();
    
    // 获取页大小
    int getPageSize();
    
    // 获取偏移量
    long getOffset();
    
    // 获取排序
    Sort getSort();
    
    // 获取下一页
    Pageable next();
    
    // 获取上一页
    Pageable previousOrFirst();
    
    // 获取第一页
    Pageable first();
    
    // 是否有上一页
    boolean hasPrevious();
}
```

#### 2.2 Page 接口

```java
public interface Page<T> extends Slice<T> {
    
    // 获取总页数
    int getTotalPages();
    
    // 获取总元素数
    long getTotalElements();
    
    // 转换为Pageable
    Pageable nextPageable();
    
    // 转换为Pageable
    Pageable previousPageable();
}
```

#### 2.3 Sort 类

```java
public class Sort implements Streamable<Order> {
    
    // 创建排序
    public static Sort by(String... properties);
    
    // 创建排序
    public static Sort by(Direction direction, String... properties);
    
    // 创建排序
    public static Sort by(List<Order> orders);
    
    // 添加排序
    public Sort and(Sort sort);
    
    // 添加排序
    public Sort and(Direction direction, String... properties);
}
```

#### 2.4 使用示例

```java
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    // 分页查询
    public Page<User> findUsers(int page, int size) {
        Pageable pageable = PageRequest.of(page, size, Sort.by("createTime").descending());
        return userRepository.findAll(pageable);
    }
    
    // 复杂排序
    public List<User> findUsersWithSort() {
        Sort sort = Sort.by("age").ascending()
                       .and(Sort.by("name").ascending());
        return userRepository.findAll(sort);
    }
}
```

### 3. 查询方法

#### 3.1 方法名查询

Spring Data Commons 支持通过方法名自动生成查询：

```java
public interface UserRepository extends JpaRepository<User, Long> {
    
    // 根据姓名查找
    User findByName(String name);
    
    // 根据年龄查找
    List<User> findByAge(int age);
    
    // 根据姓名和年龄查找
    List<User> findByNameAndAge(String name, int age);
    
    // 根据年龄范围查找
    List<User> findByAgeBetween(int minAge, int maxAge);
    
    // 根据姓名模糊查找
    List<User> findByNameLike(String name);
    
    // 根据姓名开头查找
    List<User> findByNameStartingWith(String prefix);
    
    // 根据姓名结尾查找
    List<User> findByNameEndingWith(String suffix);
    
    // 根据姓名包含查找
    List<User> findByNameContaining(String name);
    
    // 根据年龄大于查找
    List<User> findByAgeGreaterThan(int age);
    
    // 根据年龄小于查找
    List<User> findByAgeLessThan(int age);
    
    // 根据年龄大于等于查找
    List<User> findByAgeGreaterThanEqual(int age);
    
    // 根据年龄小于等于查找
    List<User> findByAgeLessThanEqual(int age);
    
    // 根据姓名不为空查找
    List<User> findByNameIsNotNull();
    
    // 根据姓名为空查找
    List<User> findByNameIsNull();
    
    // 根据姓名不为空查找
    List<User> findByNameIsNot(String name);
    
    // 根据姓名查找并排序
    List<User> findByNameOrderByAgeDesc(String name);
    
    // 根据姓名查找并分页
    Page<User> findByName(String name, Pageable pageable);
}
```

#### 3.2 查询关键字

| 关键字 | 示例 | 生成的查询片段 |
|--------|------|----------------|
| And | findByLastnameAndFirstname | where x.lastname = ?1 and x.firstname = ?2 |
| Or | findByLastnameOrFirstname | where x.lastname = ?1 or x.firstname = ?2 |
| Is,Equals | findByFirstname,findByFirstnameIs,findByFirstnameEquals | where x.firstname = ?1 |
| Between | findByStartDateBetween | where x.startDate between ?1 and ?2 |
| LessThan | findByAgeLessThan | where x.age < ?1 |
| LessThanEqual | findByAgeLessThanEqual | where x.age <= ?1 |
| GreaterThan | findByAgeGreaterThan | where x.age > ?1 |
| GreaterThanEqual | findByAgeGreaterThanEqual | where x.age >= ?1 |
| After | findByStartDateAfter | where x.startDate > ?1 |
| Before | findByStartDateBefore | where x.startDate < ?1 |
| IsNull | findByAgeIsNull | where x.age is null |
| IsNotNull,NotNull | findByAge(Is)NotNull | where x.age is not null |
| Like | findByFirstnameLike | where x.firstname like ?1 |
| NotLike | findByFirstnameNotLike | where x.firstname not like ?1 |
| StartingWith | findByFirstnameStartingWith | where x.firstname like ?1 (parameter bound with appended %) |
| EndingWith | findByFirstnameEndingWith | where x.firstname like ?1 (parameter bound with prepended %) |
| Containing | findByFirstnameContaining | where x.firstname like ?1 (parameter bound wrapped in %) |
| OrderBy | findByAgeOrderByLastnameDesc | where x.age = ?1 order by x.lastname desc |
| Not | findByLastnameNot | where x.lastname <> ?1 |
| In | findByAgeIn(Collection ages) | where x.age in ?1 |
| NotIn | findByAgeNotIn(Collection ages) | where x.age not in ?1 |
| True | findByActiveTrue() | where x.active = true |
| False | findByActiveFalse() | where x.active = false |
| IgnoreCase | findByFirstnameIgnoreCase | where UPPER(x.firstname) = UPPER(?1) |

#### 3.3 限制查询结果

```java
public interface UserRepository extends JpaRepository<User, Long> {
    
    // 限制返回数量
    User findFirstByOrderByAgeDesc();
    
    // 限制返回数量
    User findTopByOrderByAgeDesc();
    
    // 限制返回数量
    List<User> findTop3ByOrderByAgeDesc();
    
    // 限制返回数量
    List<User> findFirst10ByOrderByAgeDesc();
}
```

### 4. 投影查询

#### 4.1 接口投影

```java
// 定义投影接口
public interface UserSummary {
    String getName();
    int getAge();
    String getEmail();
}

// 在Repository中使用
public interface UserRepository extends JpaRepository<User, Long> {
    List<UserSummary> findByAgeGreaterThan(int age);
}
```

#### 4.2 类投影

```java
// 定义投影类
public class UserDto {
    private String name;
    private int age;
    
    // 构造函数
    public UserDto(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    // getter方法
    public String getName() { return name; }
    public int getAge() { return age; }
}

// 在Repository中使用
public interface UserRepository extends JpaRepository<User, Long> {
    List<UserDto> findByAgeGreaterThan(int age);
}
```

#### 4.3 动态投影

```java
public interface UserRepository extends JpaRepository<User, Long> {
    <T> T findByEmail(String email, Class<T> type);
}

// 使用示例
User user = userRepository.findByEmail("test@example.com", User.class);
UserSummary summary = userRepository.findByEmail("test@example.com", UserSummary.class);
```

### 5. 查询示例 (Query by Example)

#### 5.1 基本使用

```java
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    public List<User> findUsersByExample(String name, Integer age) {
        // 创建示例实体
        User user = new User();
        user.setName(name);
        user.setAge(age);
        
        // 创建匹配器
        ExampleMatcher matcher = ExampleMatcher.matching()
            .withStringMatcher(ExampleMatcher.StringMatcher.CONTAINING)
            .withIgnoreCase();
        
        // 创建示例
        Example<User> example = Example.of(user, matcher);
        
        // 执行查询
        return userRepository.findAll(example);
    }
}
```

#### 5.2 高级匹配器

```java
ExampleMatcher matcher = ExampleMatcher.matching()
    .withStringMatcher(ExampleMatcher.StringMatcher.CONTAINING)  // 字符串包含匹配
    .withIgnoreCase()                                            // 忽略大小写
    .withIgnorePaths("id", "createTime")                         // 忽略某些字段
    .withIncludeNullValues()                                     // 包含null值
    .withMatcher("age", ExampleMatcher.GenericPropertyMatchers.range()); // 范围匹配
```

### 6. 审计功能

#### 6.1 审计注解

```java
@Entity
@EntityListeners(AuditingEntityListener.class)
public class User {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    private String name;
    
    @CreatedDate
    @Column(updatable = false)
    private LocalDateTime createTime;
    
    @LastModifiedDate
    private LocalDateTime updateTime;
    
    @CreatedBy
    @Column(updatable = false)
    private String createBy;
    
    @LastModifiedBy
    private String updateBy;
    
    @Version
    private Long version;
    
    // getter和setter方法
}
```

#### 6.2 启用审计

```java
@Configuration
@EnableJpaAuditing(auditorAwareRef = "auditorProvider")
public class JpaConfig {
    
    @Bean
    public AuditorAware<String> auditorProvider() {
        return () -> Optional.ofNullable(SecurityContextHolder.getContext())
            .map(SecurityContext::getAuthentication)
            .map(Authentication::getName);
    }
}
```

### 7. 事件系统

#### 7.1 实体事件

```java
@Component
public class UserEventListener {
    
    @EventListener
    public void handleUserCreated(UserCreatedEvent event) {
        User user = event.getUser();
        System.out.println("User created: " + user.getName());
    }
    
    @EventListener
    public void handleUserUpdated(UserUpdatedEvent event) {
        User user = event.getUser();
        System.out.println("User updated: " + user.getName());
    }
    
    @EventListener
    public void handleUserDeleted(UserDeletedEvent event) {
        User user = event.getUser();
        System.out.println("User deleted: " + user.getName());
    }
}
```

#### 7.2 自定义事件

```java
public class UserCreatedEvent extends ApplicationEvent {
    
    private final User user;
    
    public UserCreatedEvent(Object source, User user) {
        super(source);
        this.user = user;
    }
    
    public User getUser() {
        return user;
    }
}

// 发布事件
@Autowired
private ApplicationEventPublisher eventPublisher;

public User createUser(User user) {
    User savedUser = userRepository.save(user);
    eventPublisher.publishEvent(new UserCreatedEvent(this, savedUser));
    return savedUser;
}
```

### 8. 数据绑定和转换

#### 8.1 自定义转换器

```java
@Component
public class StringToLocalDateConverter implements Converter<String, LocalDate> {
    
    @Override
    public LocalDate convert(String source) {
        if (source == null || source.isEmpty()) {
            return null;
        }
        return LocalDate.parse(source, DateTimeFormatter.ISO_LOCAL_DATE);
    }
}

@Component
public class LocalDateToStringConverter implements Converter<LocalDate, String> {
    
    @Override
    public String convert(LocalDate source) {
        if (source == null) {
            return null;
        }
        return source.format(DateTimeFormatter.ISO_LOCAL_DATE);
    }
}
```

#### 8.2 注册转换器

```java
@Configuration
public class ConversionConfig {
    
    @Bean
    public ConversionService conversionService() {
        ConversionServiceFactoryBean factory = new ConversionServiceFactoryBean();
        factory.setConverters(getConverters());
        factory.afterPropertiesSet();
        return factory.getObject();
    }
    
    private Set<Converter> getConverters() {
        Set<Converter> converters = new HashSet<>();
        converters.add(new StringToLocalDateConverter());
        converters.add(new LocalDateToStringConverter());
        return converters;
    }
}
```

### 9. 实用工具类

#### 9.1 DomainClassConverter

```java
@RestController
@RequestMapping("/users")
public class UserController {
    
    @Autowired
    private UserRepository userRepository;
    
    // 自动转换ID为实体
    @GetMapping("/{user}")
    public User getUser(@PathVariable("user") User user) {
        return user;
    }
}
```

#### 9.2 PageableHandlerMethodArgumentResolver

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    
    @Override
    public void addArgumentResolvers(List<HandlerMethodArgumentResolver> argumentResolvers) {
        argumentResolvers.add(new PageableHandlerMethodArgumentResolver());
    }
}

// 在Controller中使用
@GetMapping("/users")
public Page<User> getUsers(Pageable pageable) {
    return userRepository.findAll(pageable);
}

// URL: /users?page=0&size=10&sort=name,asc&sort=age,desc
```

### 10. 最佳实践

#### 10.1 Repository 设计原则

1. **单一职责**：每个Repository只负责一个聚合根
2. **接口隔离**：只继承需要的接口
3. **命名规范**：方法名要清晰表达查询意图
4. **避免过度抽象**：不要为了抽象而抽象

#### 10.2 性能优化

```java
public interface UserRepository extends JpaRepository<User, Long> {
    
    // 使用@Query优化复杂查询
    @Query("SELECT u FROM User u WHERE u.age > :age AND u.status = :status")
    List<User> findActiveUsersByAge(@Param("age") int age, @Param("status") String status);
    
    // 使用@QueryHints添加查询提示
    @QueryHints(value = {
        @QueryHint(name = HINT_FETCH_SIZE, value = "50"),
        @QueryHint(name = HINT_CACHEABLE, value = "true")
    })
    @Query("SELECT u FROM User u")
    List<User> findAllWithHints();
    
    // 使用@EntityGraph优化N+1问题
    @EntityGraph(attributePaths = {"orders", "profile"})
    List<User> findAll();
}
```

#### 10.3 异常处理

```java
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    public User findUserById(Long id) {
        try {
            return userRepository.findById(id)
                .orElseThrow(() -> new UserNotFoundException("User not found with id: " + id));
        } catch (DataAccessException e) {
            throw new ServiceException("Database error while finding user", e);
        }
    }
}

// 自定义异常
public class UserNotFoundException extends RuntimeException {
    public UserNotFoundException(String message) {
        super(message);
    }
}

public class ServiceException extends RuntimeException {
    public ServiceException(String message, Throwable cause) {
        super(message, cause);
    }
}
```

## 总结

Spring Data Commons 通过提供统一的数据访问抽象层，大大简化了数据访问代码的编写。其核心设计思想包括：

1. **统一抽象**：为不同数据存储技术提供一致的编程模型
2. **约定优于配置**：通过合理的默认行为和命名约定减少配置
3. **类型安全**：利用泛型和反射提供编译时类型检查
4. **声明式查询**：通过方法名或注解自动生成查询逻辑

主要模块包括：
- Repository 接口体系
- 分页和排序
- 查询方法生成
- 投影查询
- 查询示例
- 审计功能
- 事件系统
- 数据绑定和转换
- 实用工具类

通过合理使用这些功能，可以构建出高效、可维护的数据访问层，提高开发效率，减少重复代码。

