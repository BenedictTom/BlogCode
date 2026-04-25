---
title: Memcached
main_color: "#229ab2ff"
categories: 缓存
tags:
  - 缓存
cover: https://free.picui.cn/free/2026/03/28/69c74f9f67bf4.png
---

# Memcached Java 集成指南

## 1. 概述

Memcached 是一个高性能、分布式的内存对象缓存系统，用于通过缓存数据库查询结果、页面片段、会话等来减轻后端存储压力、降低延迟、提高吞吐。

## 2. 安装与运行

### 2.1 macOS（Homebrew）

```bash
brew install memcached
memcached -m 256 -p 11211 -u nobody -l 0.0.0.0 -vv
```

### 2.2 Docker

```bash
docker run -d --name memcached \
  -p 11211:11211 \
  -m 512m \
  memcached:1.6-alpine \
  memcached -m 512 -c 2048 -o modern
```

## 3. Spring Boot 集成

### 3.1 依赖配置

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-cache</artifactId>
</dependency>
<dependency>
    <groupId>net.spy</groupId>
    <artifactId>spymemcached</artifactId>
    <version>2.12.3</version>
</dependency>
```

### 3.2 配置类

```java
@Configuration
@EnableCaching
public class MemcachedConfig {

    @Value("${memcached.servers:127.0.0.1:11211}")
    private String servers;

    @Value("${memcached.operationTimeout:3000}")
    private int operationTimeout;

    @Bean
    public MemcachedClient memcachedClient() throws IOException {
        ConnectionFactoryBuilder builder = new ConnectionFactoryBuilder()
                .setOpTimeout(operationTimeout)
                .setOpQueueMaxBlockTime(1000)
                .setMaxReconnectDelay(30)
                .setLocatorType(ConnectionPoolConfiguration.Locator.CONSISTENT)
                .setFailureMode(FailureMode.Redistribute);

        return new MemcachedClient(builder.build(), 
                AddrUtil.getAddresses(servers));
    }

    @Bean
    public CacheManager cacheManager(MemcachedClient memcachedClient) {
        return new MemcachedCacheManager(memcachedClient);
    }
}
```

### 3.3 自定义 CacheManager

```java
public class MemcachedCacheManager implements CacheManager {

    private final MemcachedClient memcachedClient;
    private final Map<String, Cache> caches = new ConcurrentHashMap<>();

    public MemcachedCacheManager(MemcachedClient memcachedClient) {
        this.memcachedClient = memcachedClient;
    }

    @Override
    public Cache getCache(String name) {
        return caches.computeIfAbsent(name, 
                k -> new MemcachedCache(k, memcachedClient));
    }

    @Override
    public Collection<String> getCacheNames() {
        return caches.keySet();
    }
}

public class MemcachedCache implements Cache {

    private final String name;
    private final MemcachedClient memcachedClient;

    public MemcachedCache(String name, MemcachedClient memcachedClient) {
        this.name = name;
        this.memcachedClient = memcachedClient;
    }

    @Override
    public String getName() {
        return name;
    }

    @Override
    public Object getNativeCache() {
        return memcachedClient;
    }

    @Override
    public ValueWrapper get(Object key) {
        try {
            Object value = memcachedClient.get(name + ":" + key);
            return value != null ? new SimpleValueWrapper(value) : null;
        } catch (Exception e) {
            throw new RuntimeException("Memcached get error", e);
        }
    }

    @Override
    public <T> T get(Object key, Class<T> type) {
        ValueWrapper wrapper = get(key);
        return wrapper != null ? (T) wrapper.get() : null;
    }

    @Override
    public void put(Object key, Object value) {
        try {
            memcachedClient.set(name + ":" + key, 300, value);
        } catch (Exception e) {
            throw new RuntimeException("Memcached put error", e);
        }
    }

    @Override
    public void evict(Object key) {
        try {
            memcachedClient.delete(name + ":" + key);
        } catch (Exception e) {
            throw new RuntimeException("Memcached evict error", e);
        }
    }

    @Override
    public void clear() {
        // Memcached 不支持按前缀删除，这里只是示例
        throw new UnsupportedOperationException("Clear not supported");
    }
}
```

### 3.4 应用配置

```yaml
# application.yml
memcached:
  servers: 127.0.0.1:11211
  operationTimeout: 3000
```

## 4. 使用示例

### 4.1 实体类

```java
@Data
@AllArgsConstructor
@NoArgsConstructor
public class User {
    private Long id;
    private String name;
    private String email;
    private LocalDateTime createTime;
}
```

### 4.2 Service 层

```java
@Service
@Slf4j
public class UserService {

    @Autowired
    private MemcachedClient memcachedClient;

    @Cacheable(value = "users", key = "#id")
    public User getUserById(Long id) {
        log.info("从数据库查询用户: {}", id);
        // 模拟数据库查询
        return new User(id, "用户" + id, "user" + id + "@example.com", 
                LocalDateTime.now());
    }

    @CacheEvict(value = "users", key = "#user.id")
    public void updateUser(User user) {
        log.info("更新用户: {}", user.getId());
        // 模拟数据库更新
    }

    @CacheEvict(value = "users", key = "#id")
    public void deleteUser(Long id) {
        log.info("删除用户: {}", id);
        // 模拟数据库删除
    }

    // 手动缓存操作
    public void manualCacheExample() {
        try {
            // 设置缓存
            Future<Boolean> future = memcachedClient.set("manual:key", 60, "value");
            boolean success = future.get(1, TimeUnit.SECONDS);
            log.info("设置缓存结果: {}", success);

            // 获取缓存
            Object value = memcachedClient.get("manual:key");
            log.info("获取缓存值: {}", value);

            // CAS 操作
            CASValue<Object> casValue = memcachedClient.gets("manual:key");
            if (casValue != null) {
                CASResponse response = memcachedClient.cas("manual:key", 
                        casValue.getCas(), 60, "new value");
                log.info("CAS 操作结果: {}", response);
            }

            // 计数器操作
            memcachedClient.set("counter", 0, "0");
            long incr = memcachedClient.incr("counter", 5);
            log.info("计数器增加后: {}", incr);

        } catch (Exception e) {
            log.error("缓存操作失败", e);
        }
    }
}
```

### 4.3 Controller 层

```java
@RestController
@RequestMapping("/api/users")
@Slf4j
public class UserController {

    @Autowired
    private UserService userService;

    @GetMapping("/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        User user = userService.getUserById(id);
        return ResponseEntity.ok(user);
    }

    @PutMapping("/{id}")
    public ResponseEntity<Void> updateUser(@PathVariable Long id, 
                                         @RequestBody User user) {
        user.setId(id);
        userService.updateUser(user);
        return ResponseEntity.ok().build();
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        userService.deleteUser(id);
        return ResponseEntity.ok().build();
    }

    @PostMapping("/cache-test")
    public ResponseEntity<String> testCache() {
        userService.manualCacheExample();
        return ResponseEntity.ok("缓存测试完成");
    }
}
```

## 5. 高级特性

### 5.1 缓存注解

```java
@Service
public class AdvancedCacheService {

    @Cacheable(value = "users", key = "#id", unless = "#result == null")
    public User getUser(Long id) {
        return findUserById(id);
    }

    @CachePut(value = "users", key = "#user.id")
    public User saveUser(User user) {
        return saveUserToDb(user);
    }

    @CacheEvict(value = "users", allEntries = true)
    public void clearAllUsers() {
        // 清除所有用户缓存
    }

    @Caching(evict = {
        @CacheEvict(value = "users", key = "#user.id"),
        @CacheEvict(value = "userList", allEntries = true)
    })
    public void updateUserAndClearList(User user) {
        // 更新用户并清除列表缓存
    }
}
```

### 5.2 条件缓存

```java
@Service
public class ConditionalCacheService {

    @Cacheable(value = "users", key = "#id", 
               condition = "#id != null and #id > 0",
               unless = "#result == null")
    public User getUser(Long id) {
        return findUserById(id);
    }

    @CachePut(value = "users", key = "#user.id", 
              condition = "#user != null and #user.id != null")
    public User saveUser(User user) {
        return saveUserToDb(user);
    }
}
```

### 5.3 自定义 Key 生成器

```java
@Component
public class CustomKeyGenerator implements KeyGenerator {
    
    @Override
    public Object generate(Object target, Method method, Object... params) {
        StringBuilder sb = new StringBuilder();
        sb.append(target.getClass().getSimpleName());
        sb.append(".");
        sb.append(method.getName());
        for (Object param : params) {
            sb.append(".");
            sb.append(param);
        }
        return sb.toString();
    }
}

@Configuration
public class CacheConfig {
    
    @Bean
    public KeyGenerator customKeyGenerator() {
        return new CustomKeyGenerator();
    }
}
```

## 6. 监控与健康检查

### 6.1 健康检查

```java
@Component
public class MemcachedHealthIndicator implements HealthIndicator {

    @Autowired
    private MemcachedClient memcachedClient;

    @Override
    public Health health() {
        try {
            // 简单的 ping 测试
            memcachedClient.set("health_check", 10, "ok");
            Object result = memcachedClient.get("health_check");
            
            if ("ok".equals(result)) {
                return Health.up()
                        .withDetail("status", "Memcached is running")
                        .build();
            } else {
                return Health.down()
                        .withDetail("status", "Memcached health check failed")
                        .build();
            }
        } catch (Exception e) {
            return Health.down()
                    .withDetail("status", "Memcached connection failed")
                    .withDetail("error", e.getMessage())
                    .build();
        }
    }
}
```

### 6.2 统计信息

```java
@Component
public class MemcachedStatsService {

    @Autowired
    private MemcachedClient memcachedClient;

    public Map<String, Object> getStats() {
        try {
            Map<String, String> stats = memcachedClient.getStats().get("127.0.0.1:11211");
            Map<String, Object> result = new HashMap<>();
            
            // 关键指标
            result.put("curr_items", stats.get("curr_items"));
            result.put("total_items", stats.get("total_items"));
            result.put("bytes", stats.get("bytes"));
            result.put("curr_connections", stats.get("curr_connections"));
            result.put("total_connections", stats.get("total_connections"));
            result.put("get_hits", stats.get("get_hits"));
            result.put("get_misses", stats.get("get_misses"));
            result.put("evictions", stats.get("evictions"));
            
            // 计算命中率
            long hits = Long.parseLong(stats.getOrDefault("get_hits", "0"));
            long misses = Long.parseLong(stats.getOrDefault("get_misses", "0"));
            double hitRate = (hits + misses) > 0 ? (double) hits / (hits + misses) : 0;
            result.put("hit_rate", String.format("%.2f%%", hitRate * 100));
            
            return result;
        } catch (Exception e) {
            throw new RuntimeException("获取 Memcached 统计信息失败", e);
        }
    }
}
```

## 7. 最佳实践

### 7.1 缓存策略

```java
@Service
public class CacheStrategyService {

    @Autowired
    private MemcachedClient memcachedClient;

    // 防止缓存穿透
    public User getUserWithNullCache(Long id) {
        String key = "user:" + id;
        Object cached = memcachedClient.get(key);
        
        if (cached != null) {
            if (cached instanceof NullValue) {
                return null; // 缓存了空值
            }
            return (User) cached;
        }
        
        User user = findUserFromDb(id);
        if (user != null) {
            memcachedClient.set(key, 300, user);
        } else {
            // 缓存空值，防止穿透
            memcachedClient.set(key, 60, new NullValue());
        }
        
        return user;
    }

    // 防止缓存击穿
    public User getUserWithLock(Long id) {
        String key = "user:" + id;
        String lockKey = "lock:user:" + id;
        
        Object cached = memcachedClient.get(key);
        if (cached != null) {
            return (User) cached;
        }
        
        // 尝试获取锁
        boolean locked = memcachedClient.add(lockKey, 10, "locked");
        if (locked) {
            try {
                // 双重检查
                cached = memcachedClient.get(key);
                if (cached != null) {
                    return (User) cached;
                }
                
                User user = findUserFromDb(id);
                if (user != null) {
                    memcachedClient.set(key, 300, user);
                }
                return user;
            } finally {
                memcachedClient.delete(lockKey);
            }
        } else {
            // 等待其他线程加载
            try {
                Thread.sleep(100);
                return getUserWithLock(id);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return null;
            }
        }
    }
}

// 空值标记
class NullValue {
    // 用于标记缓存中的空值
}
```

### 7.2 序列化配置

```java
@Configuration
public class SerializationConfig {

    @Bean
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        return mapper;
    }
}

@Component
public class JsonSerializer {
    
    @Autowired
    private ObjectMapper objectMapper;
    
    public String serialize(Object obj) throws JsonProcessingException {
        return objectMapper.writeValueAsString(obj);
    }
    
    public <T> T deserialize(String json, Class<T> clazz) throws JsonProcessingException {
        return objectMapper.readValue(json, clazz);
    }
}
```

## 8. 常见问题与解决方案

### 8.1 连接池配置

```java
@Configuration
public class MemcachedPoolConfig {

    @Bean
    public MemcachedClient memcachedClient() throws IOException {
        ConnectionFactoryBuilder builder = new ConnectionFactoryBuilder()
                .setOpTimeout(3000)
                .setOpQueueMaxBlockTime(1000)
                .setMaxReconnectDelay(30)
                .setLocatorType(ConnectionPoolConfiguration.Locator.CONSISTENT)
                .setFailureMode(FailureMode.Redistribute)
                .setDaemon(true)
                .setShouldOptimize(true)
                .setMaxConnPerNode(10)
                .setMinConnPerNode(2);

        return new MemcachedClient(builder.build(), 
                AddrUtil.getAddresses("127.0.0.1:11211"));
    }
}
```

### 8.2 异常处理

```java
@ControllerAdvice
public class MemcachedExceptionHandler {

    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<String> handleMemcachedException(RuntimeException e) {
        if (e.getMessage().contains("Memcached")) {
            log.error("Memcached 操作失败", e);
            return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body("缓存服务暂时不可用");
        }
        throw e;
    }
}
```

