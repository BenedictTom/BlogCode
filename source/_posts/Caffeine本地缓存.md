---
title: Caffeine本地缓存 
main_color: "#c0e0e0"  
categories: 缓存  
tags:
  - 缓存  
cover: https://free.picui.cn/free/2026/03/28/69c74d59dd2a6.webp
---

# Caffeine 本地缓存全方位详解

Caffeine 是 Java 生态下高性能、近乎无锁的本地缓存库，被广泛用于替代 Guava Cache。它在高并发、低延迟场景下表现优异，支持丰富的缓存淘汰策略和灵活的加载机制。

---

## 一、Caffeine 基础入门

### 1.1 Caffeine 简介
- Caffeine 是一个基于 Java 8 的本地缓存库，灵感来自 Guava Cache，但性能更优。
- 支持多种淘汰策略（基于容量、时间、引用等），并发性能极高。
- 适合热点数据、短生命周期数据的本地缓存场景。

### 1.2 依赖引入
```xml
<dependency>
    <groupId>com.github.ben-manes.caffeine</groupId>
    <artifactId>caffeine</artifactId>
    <version>3.1.8</version>
</dependency>
```

---

## 二、缓存构建方式

### 2.1 最基础用法
```java
// 创建一个最大容量为100的缓存
Cache<String, Object> cache = Caffeine.newBuilder()
    .maximumSize(100)
    .build();

// put/get
cache.put("key", "value");
Object value = cache.getIfPresent("key");
```

### 2.2 自动加载（LoadingCache）
```java
LoadingCache<String, Object> loadingCache = Caffeine.newBuilder()
    .maximumSize(100)
    .build(key -> loadFromDb(key));

Object value = loadingCache.get("key"); // 若不存在自动调用 loadFromDb
```

### 2.3 异步加载（AsyncLoadingCache）
```java
AsyncLoadingCache<String, Object> asyncCache = Caffeine.newBuilder()
    .maximumSize(100)
    .buildAsync(key -> loadFromDbAsync(key));

CompletableFuture<Object> future = asyncCache.get("key");
```

### 2.4 手动加载
```java
Cache<String, Object> cache = Caffeine.newBuilder()
    .maximumSize(100)
    .build();

Object value = cache.get("key", k -> loadFromDb(k));
```

---

## 三、常用淘汰策略

- **maximumSize**：基于缓存条目数量淘汰（LRU近似）
- **maximumWeight/Weigher**：基于权重淘汰（如按内存大小）
- **expireAfterWrite**：写入后多久过期
- **expireAfterAccess**：访问后多久过期
- **refreshAfterWrite**：写入后多久自动刷新（异步刷新）
- **弱/软引用**：`weakKeys()`, `weakValues()`, `softValues()`

```java
Caffeine.newBuilder()
    .maximumSize(1000)
    .expireAfterWrite(10, TimeUnit.MINUTES)
    .expireAfterAccess(5, TimeUnit.MINUTES)
    .refreshAfterWrite(1, TimeUnit.MINUTES)
    .build();
```

---

## 四、同步加载、异步加载、手动加载

### 4.1 同步加载（LoadingCache）
- 通过 `build(Function)` 方式，get 时自动加载。
- 适合数据源响应快、同步场景。

### 4.2 异步加载（AsyncLoadingCache）
- 通过 `buildAsync(Function)`，返回 `CompletableFuture`。
- 适合高并发、IO密集型场景。

### 4.3 手动加载（Cache.get(key, mappingFunction)）
- 只有在缓存未命中时才调用 mappingFunction。
- 适合自定义加载逻辑。

#### 加载方式区别与适用场景

| 加载方式         | 触发时机         | 返回类型                | 适用场景                   | 优点                  | 注意事项                |
|------------------|------------------|------------------------|----------------------------|-----------------------|------------------------|
| 同步加载         | get 时自动加载   | 直接返回 value         | 数据源快、同步业务         | 使用简单，代码直观     | 阻塞主线程，慢时影响性能 |
| 异步加载         | get 时自动加载   | CompletableFuture      | 高并发、IO密集、异步业务   | 不阻塞主线程，吞吐高   | 需处理异步回调         |
| 手动加载         | get(key, func)   | 直接返回 value         | 需自定义加载逻辑、灵活控制 | 灵活、可自定义         | 需手动管理缓存失效等    |

- **同步加载**：适合数据源快、对延迟敏感的场景，主线程会等待加载完成。
- **异步加载**：适合高并发、IO密集型（如远程API/数据库），不会阻塞主线程，提升吞吐。
- **手动加载**：适合需要自定义加载逻辑、批量加载、或特殊缓存失效策略的场景。

> 实际开发中可根据业务需求选择合适的加载方式，也可结合使用（如主用同步，部分场景用异步/手动）。

---

## 五、与 Spring Boot 整合

### 5.1 引入依赖
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-cache</artifactId>
</dependency>
<dependency>
    <groupId>com.github.ben-manes.caffeine</groupId>
    <artifactId>caffeine</artifactId>
</dependency>
```

### 5.2 配置 application.yml
```yaml
spring:
  cache:
    type: caffeine
    caffeine:
      spec: maximumSize=500,expireAfterWrite=10m,refreshAfterWrite=1m
```

### 5.3 使用 @Cacheable
```java
@Cacheable(cacheNames = "userCache", key = "#userId")
public User getUserById(Long userId) {
    // 查询数据库
}
```

---

## 六、多级缓存（Caffeine + Redis）

- 本地缓存（Caffeine）+ 分布式缓存（Redis）组合，兼顾速度和一致性。
- 典型方案：先查本地 -> 本地未命中查Redis -> Redis未命中查DB
- 可用 Spring Cache + 自定义 CacheManager 实现

**示例伪代码：**
```java
public Object get(String key) {
    Object value = caffeineCache.getIfPresent(key);
    if (value != null) return value;
    value = redisCache.get(key);
    if (value != null) {
        caffeineCache.put(key, value);
        return value;
    }
    value = dbQuery(key);
    redisCache.put(key, value);
    caffeineCache.put(key, value);
    return value;
}
```

---

## 七、性能优化建议

- 合理设置 maximumSize，防止 OOM
- 结合 expireAfterWrite/expireAfterAccess 控制数据新鲜度
- 使用异步加载减少主线程阻塞
- 对热点数据可用 refreshAfterWrite 异步刷新
- 监控 hit rate、load time、eviction count（Caffeine 提供 stats()）
- 避免 value 过大（如大对象、图片等）

---

## 八、Caffeine 底层原理简析

- 基于高效的并发数据结构（Striped64、ConcurrentLinkedQueue等）
- 淘汰策略采用 Window TinyLFU 算法，兼顾 LRU 和 LFU 优点
- 采用分段锁和无锁队列，极大提升并发性能
- 维护写队列、访问队列、频率计数器等多种结构
- 支持异步刷新、监听器、统计等高级特性

---

## 九、常见面试题

1. **Caffeine 和 Guava Cache 有什么区别？**
   - Caffeine 性能更高，支持 Window TinyLFU，淘汰策略更先进。
   - Guava Cache 已停止维护。
2. **Caffeine 支持哪些淘汰策略？**
   - 基于容量、权重、时间、引用类型（弱/软）、异步刷新等。
3. **Caffeine 如何实现高并发？**
   - 分段锁、无锁队列、CAS、Window TinyLFU 算法。
4. **如何实现多级缓存？**
   - 本地 + Redis，先查本地，未命中查分布式，最后查DB。
5. **Caffeine 如何监控缓存命中率？**
   - `cache.stats()` 获取命中率、加载时间、淘汰次数等。
6. **Caffeine 适合哪些场景？**
   - 热点数据、本地高并发、低延迟、短生命周期数据。
7. **Caffeine 不适合哪些场景？**
   - 分布式一致性要求高、缓存容量极大（建议用分布式缓存）。

---

## 十、参考资料
- [Caffeine 官方文档](https://github.com/ben-manes/caffeine)
- [Spring Boot Cache 官方文档](https://docs.spring.io/spring-boot/docs/current/reference/html/io.html#io.caching)
- [Caffeine Wiki](https://github.com/ben-manes/caffeine/wiki)
- [高性能本地缓存 Caffeine 原理与实战](https://juejin.cn/post/6844904101388621832)
- [性能利器Caffeine缓存全面指南](https://segmentfault.com/a/1190000044579389)。

---

> 本文涵盖了 Caffeine 缓存的基础、进阶、原理与面试，适合日常开发和面试复习。


