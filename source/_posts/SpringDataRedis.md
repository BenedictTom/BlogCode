---
title: Spring Data Redis 完整指南
main_color: "#1881a2ff"
categories: Redis
tags:
  - Spring Data
  - Redis
cover: https://free.picui.cn/free/2026/03/28/69c7fa7b7a8d1.png
---

# Spring Data Redis 完整指南

## 目录
- [概述](#概述)
- [核心概念](#核心概念)
- [环境准备](#环境准备)
- [基础配置](#基础配置)
- [核心功能](#核心功能)
- [高级特性](#高级特性)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)
- [性能优化](#性能优化)
- [实战示例](#实战示例)

## 概述

Spring Data Redis 是 Spring Data 项目的一部分，它为 Redis 键值存储提供了高级抽象和便捷的配置。它简化了 Redis 操作，提供了类型安全的 API，并集成了 Spring 的缓存抽象。

### 主要特性
- **类型安全**：提供泛型支持的类型安全操作
- **模板模式**：RedisTemplate 和 StringRedisTemplate
- **Repository 支持**：类似 JPA 的 Repository 接口
- **序列化支持**：多种序列化器选择
- **事务支持**：Redis 事务和 Spring 事务集成
- **集群支持**：Redis Cluster 和 Sentinel 支持

## 核心概念

### Redis 数据类型
Redis 支持以下数据类型，Spring Data Redis 为每种类型提供了专门的操作：

1. **String**：字符串类型
2. **Hash**：哈希表类型
3. **List**：列表类型
4. **Set**：集合类型
5. **Sorted Set**：有序集合类型
6. **Stream**：流类型（Redis 5.0+）

### Spring Data Redis 核心组件

#### RedisTemplate
通用的 Redis 操作模板，支持所有 Redis 数据类型。

#### StringRedisTemplate
专门用于字符串操作的模板，使用 String 序列化器。

#### RedisRepository
提供类似 JPA 的 Repository 接口，支持基本的 CRUD 操作。

## 环境准备

### 依赖配置

#### Maven 依赖
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>

<!-- 连接池支持 -->
<dependency>
    <groupId>org.apache.commons</groupId>
    <artifactId>commons-pool2</artifactId>
</dependency>

<!-- JSON 序列化支持 -->
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
</dependency>
```

#### Gradle 依赖
```gradle
implementation 'org.springframework.boot:spring-boot-starter-data-redis'
implementation 'org.apache.commons:commons-pool2'
implementation 'com.fasterxml.jackson.core:jackson-databind'
```

### Redis 服务器
确保你有可用的 Redis 服务器，可以通过以下方式获取：

1. **本地安装**：下载并安装 Redis
2. **Docker**：使用 Docker 容器运行 Redis
3. **云服务**：使用 Redis Cloud、AWS ElastiCache 等

## 基础配置

### 基本配置

#### application.yml 配置
```yaml
spring:
  redis:
    host: localhost
    port: 6379
    password: # 如果有密码，在这里配置
    database: 0
    timeout: 2000ms
    lettuce:
      pool:
        max-active: 8
        max-idle: 8
        min-idle: 0
        max-wait: -1ms
```

#### application.properties 配置
```properties
spring.redis.host=localhost
spring.redis.port=6379
spring.redis.password=
spring.redis.database=0
spring.redis.timeout=2000ms
spring.redis.lettuce.pool.max-active=8
spring.redis.lettuce.pool.max-idle=8
spring.redis.lettuce.pool.min-idle=0
spring.redis.lettuce.pool.max-wait=-1ms
```

### 高级配置

#### 自定义 RedisTemplate 配置
```java
@Configuration
public class RedisConfig {
    
    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory connectionFactory) {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory);
        
        // 设置 key 序列化器
        template.setKeySerializer(new StringRedisSerializer());
        template.setHashKeySerializer(new StringRedisSerializer());
        
        // 设置 value 序列化器
        Jackson2JsonRedisSerializer<Object> jackson2JsonRedisSerializer = 
            new Jackson2JsonRedisSerializer<>(Object.class);
        ObjectMapper om = new ObjectMapper();
        om.setVisibility(PropertyAccessor.ALL, JsonAutoDetect.Visibility.ANY);
        om.activateDefaultTyping(LaissezFaireSubTypeValidator.instance, 
            ObjectMapper.DefaultTyping.NON_FINAL, JsonTypeInfo.As.PROPERTY);
        jackson2JsonRedisSerializer.setObjectMapper(om);
        
        template.setValueSerializer(jackson2JsonRedisSerializer);
        template.setHashValueSerializer(jackson2JsonRedisSerializer);
        
        template.afterPropertiesSet();
        return template;
    }
    
    @Bean
    public StringRedisTemplate stringRedisTemplate(RedisConnectionFactory connectionFactory) {
        return new StringRedisTemplate(connectionFactory);
    }
}
```

#### 连接池配置
```java
@Configuration
public class RedisPoolConfig {
    
    @Bean
    public RedisConnectionFactory redisConnectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName("localhost");
        config.setPort(6379);
        config.setDatabase(0);
        
        LettuceConnectionFactory factory = new LettuceConnectionFactory(config);
        factory.setShareNativeConnection(false);
        return factory;
    }
    
    @Bean
    public GenericObjectPoolConfig<Object> poolConfig() {
        GenericObjectPoolConfig<Object> config = new GenericObjectPoolConfig<>();
        config.setMaxTotal(8);
        config.setMaxIdle(8);
        config.setMinIdle(0);
        config.setMaxWaitMillis(-1);
        return config;
    }
}
```

## 核心功能

### 基本操作

#### 字符串操作
```java
@Service
public class StringRedisService {
    
    @Autowired
    private StringRedisTemplate stringRedisTemplate;
    
    // 设置值
    public void setValue(String key, String value) {
        stringRedisTemplate.opsForValue().set(key, value);
    }
    
    // 设置值并设置过期时间
    public void setValueWithExpire(String key, String value, Duration timeout) {
        stringRedisTemplate.opsForValue().set(key, value, timeout);
    }
    
    // 获取值
    public String getValue(String key) {
        return stringRedisTemplate.opsForValue().get(key);
    }
    
    // 删除值
    public Boolean delete(String key) {
        return stringRedisTemplate.delete(key);
    }
    
    // 检查键是否存在
    public Boolean hasKey(String key) {
        return stringRedisTemplate.hasKey(key);
    }
    
    // 设置过期时间
    public Boolean expire(String key, Duration timeout) {
        return stringRedisTemplate.expire(key, timeout);
    }
    
    // 获取过期时间
    public Long getExpire(String key) {
        return stringRedisTemplate.getExpire(key);
    }
}
```

#### 哈希操作
```java
@Service
public class HashRedisService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    // 设置哈希字段
    public void setHashField(String key, String field, Object value) {
        redisTemplate.opsForHash().put(key, field, value);
    }
    
    // 获取哈希字段
    public Object getHashField(String key, String field) {
        return redisTemplate.opsForHash().get(key, field);
    }
    
    // 获取所有哈希字段
    public Map<Object, Object> getAllHashFields(String key) {
        return redisTemplate.opsForHash().entries(key);
    }
    
    // 删除哈希字段
    public Long deleteHashField(String key, Object... fields) {
        return redisTemplate.opsForHash().delete(key, fields);
    }
    
    // 检查哈希字段是否存在
    public Boolean hasHashField(String key, String field) {
        return redisTemplate.opsForHash().hasKey(key, field);
    }
    
    // 获取哈希字段数量
    public Long getHashSize(String key) {
        return redisTemplate.opsForHash().size(key);
    }
}
```

#### 列表操作
```java
@Service
public class ListRedisService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    // 从左侧推入元素
    public Long leftPush(String key, Object value) {
        return redisTemplate.opsForList().leftPush(key, value);
    }
    
    // 从右侧推入元素
    public Long rightPush(String key, Object value) {
        return redisTemplate.opsForList().rightPush(key, value);
    }
    
    // 从左侧弹出元素
    public Object leftPop(String key) {
        return redisTemplate.opsForList().leftPop(key);
    }
    
    // 从右侧弹出元素
    public Object rightPop(String key) {
        return redisTemplate.opsForList().rightPop(key);
    }
    
    // 获取列表范围
    public List<Object> getRange(String key, long start, long end) {
        return redisTemplate.opsForList().range(key, start, end);
    }
    
    // 获取列表长度
    public Long getSize(String key) {
        return redisTemplate.opsForList().size(key);
    }
    
    // 根据索引获取元素
    public Object getByIndex(String key, long index) {
        return redisTemplate.opsForList().index(key, index);
    }
}
```

#### 集合操作
```java
@Service
public class SetRedisService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    // 添加元素到集合
    public Long add(String key, Object... values) {
        return redisTemplate.opsForSet().add(key, values);
    }
    
    // 从集合中移除元素
    public Long remove(String key, Object... values) {
        return redisTemplate.opsForSet().remove(key, values);
    }
    
    // 获取集合中的所有元素
    public Set<Object> members(String key) {
        return redisTemplate.opsForSet().members(key);
    }
    
    // 检查元素是否在集合中
    public Boolean isMember(String key, Object value) {
        return redisTemplate.opsForSet().isMember(key, value);
    }
    
    // 获取集合大小
    public Long getSize(String key) {
        return redisTemplate.opsForSet().size(key);
    }
    
    // 集合运算
    public Set<Object> union(String key1, String key2) {
        return redisTemplate.opsForSet().union(key1, key2);
    }
    
    public Set<Object> intersection(String key1, String key2) {
        return redisTemplate.opsForSet().intersect(key1, key2);
    }
    
    public Set<Object> difference(String key1, String key2) {
        return redisTemplate.opsForSet().difference(key1, key2);
    }
}
```

#### 有序集合操作
```java
@Service
public class ZSetRedisService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    // 添加元素到有序集合
    public Boolean add(String key, Object value, double score) {
        return redisTemplate.opsForZSet().add(key, value, score);
    }
    
    // 批量添加元素
    public Long addBatch(String key, Set<ZSetOperations.TypedTuple<Object>> tuples) {
        return redisTemplate.opsForZSet().add(key, tuples);
    }
    
    // 获取元素分数
    public Double getScore(String key, Object value) {
        return redisTemplate.opsForZSet().score(key, value);
    }
    
    // 获取元素排名（升序）
    public Long getRank(String key, Object value) {
        return redisTemplate.opsForZSet().rank(key, value);
    }
    
    // 获取元素排名（降序）
    public Long getReverseRank(String key, Object value) {
        return redisTemplate.opsForZSet().reverseRank(key, value);
    }
    
    // 获取指定范围的元素（升序）
    public Set<Object> getRange(String key, long start, long end) {
        return redisTemplate.opsForZSet().range(key, start, end);
    }
    
    // 获取指定范围的元素（降序）
    public Set<Object> getReverseRange(String key, long start, long end) {
        return redisTemplate.opsForZSet().reverseRange(key, start, end);
    }
    
    // 获取指定分数范围的元素
    public Set<Object> getRangeByScore(String key, double min, double max) {
        return redisTemplate.opsForZSet().rangeByScore(key, min, max);
    }
}
```

### 事务操作

#### 基本事务
```java
@Service
public class TransactionRedisService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    // 执行事务
    public void executeTransaction() {
        redisTemplate.execute(new SessionCallback<Object>() {
            @Override
            public Object execute(RedisOperations operations) throws DataAccessException {
                operations.multi();
                
                operations.opsForValue().set("key1", "value1");
                operations.opsForValue().set("key2", "value2");
                operations.opsForValue().increment("counter");
                
                return operations.exec();
            }
        });
    }
    
    // 条件事务
    public void executeConditionalTransaction(String key, String expectedValue, String newValue) {
        redisTemplate.execute(new SessionCallback<Object>() {
            @Override
            public Object execute(RedisOperations operations) throws DataAccessException {
                while (true) {
                    operations.watch(key);
                    String currentValue = (String) operations.opsForValue().get(key);
                    
                    if (expectedValue.equals(currentValue)) {
                        operations.multi();
                        operations.opsForValue().set(key, newValue);
                        List<Object> results = operations.exec();
                        
                        if (results != null) {
                            // 事务成功执行
                            break;
                        }
                    } else {
                        operations.discard();
                        break;
                    }
                }
                return null;
            }
        });
    }
}
```

### 管道操作

#### 批量操作优化
```java
@Service
public class PipelineRedisService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    // 使用管道批量设置值
    public void batchSetWithPipeline(Map<String, Object> keyValueMap) {
        redisTemplate.executePipelined(new SessionCallback<Object>() {
            @Override
            public Object execute(RedisOperations operations) throws DataAccessException {
                keyValueMap.forEach((key, value) -> {
                    operations.opsForValue().set(key, value);
                });
                return null;
            }
        });
    }
    
    // 使用管道批量获取值
    public List<Object> batchGetWithPipeline(List<String> keys) {
        return redisTemplate.executePipelined(new SessionCallback<Object>() {
            @Override
            public Object execute(RedisOperations operations) throws DataAccessException {
                keys.forEach(key -> {
                    operations.opsForValue().get(key);
                });
                return null;
            }
        });
    }
    
    // 使用管道批量删除
    public void batchDeleteWithPipeline(List<String> keys) {
        redisTemplate.executePipelined(new SessionCallback<Object>() {
            @Override
            public Object execute(RedisOperations operations) throws DataAccessException {
                keys.forEach(key -> {
                    operations.delete(key);
                });
                return null;
            }
        });
    }
}
```

## 高级特性

### 缓存抽象集成

#### 启用缓存
```java
@SpringBootApplication
@EnableCaching
public class RedisApplication {
    public static void main(String[] args) {
        SpringApplication.run(RedisApplication.class, args);
    }
}
```

#### 缓存配置
```java
@Configuration
@EnableCaching
public class CacheConfig {
    
    @Bean
    public CacheManager cacheManager(RedisConnectionFactory connectionFactory) {
        RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(30))
            .serializeKeysWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new GenericJackson2JsonRedisSerializer()))
            .disableCachingNullValues();
        
        return RedisCacheManager.builder(connectionFactory)
            .cacheDefaults(config)
            .build();
    }
}
```

#### 使用缓存注解
```java
@Service
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    @Cacheable(value = "users", key = "#id")
    public User getUserById(Long id) {
        return userRepository.findById(id).orElse(null);
    }
    
    @CachePut(value = "users", key = "#user.id")
    public User saveUser(User user) {
        return userRepository.save(user);
    }
    
    @CacheEvict(value = "users", key = "#id")
    public void deleteUser(Long id) {
        userRepository.deleteById(id);
    }
    
    @CacheEvict(value = "users", allEntries = true)
    public void clearAllUsers() {
        // 清除所有用户缓存
    }
}
```

### 分布式锁

#### 实现分布式锁
```java
@Service
public class DistributedLockService {
    
    @Autowired
    private StringRedisTemplate stringRedisTemplate;
    
    private static final String LOCK_PREFIX = "lock:";
    private static final long DEFAULT_EXPIRE_TIME = 30000; // 30秒
    
    /**
     * 获取分布式锁
     */
    public boolean acquireLock(String lockKey, String requestId, long expireTime) {
        String key = LOCK_PREFIX + lockKey;
        String script = "if redis.call('set', KEYS[1], ARGV[1], 'NX', 'PX', ARGV[2]) then return 1 else return 0 end";
        
        Long result = stringRedisTemplate.execute(
            new DefaultRedisScript<>(script, Long.class),
            Collections.singletonList(key),
            requestId,
            String.valueOf(expireTime)
        );
        
        return result != null && result == 1;
    }
    
    /**
     * 释放分布式锁
     */
    public boolean releaseLock(String lockKey, String requestId) {
        String key = LOCK_PREFIX + lockKey;
        String script = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end";
        
        Long result = stringRedisTemplate.execute(
            new DefaultRedisScript<>(script, Long.class),
            Collections.singletonList(key),
            requestId
        );
        
        return result != null && result == 1;
    }
    
    /**
     * 尝试获取锁，带重试机制
     */
    public boolean tryLock(String lockKey, String requestId, long expireTime, long retryTime, long retryInterval) {
        long startTime = System.currentTimeMillis();
        
        while (System.currentTimeMillis() - startTime < retryTime) {
            if (acquireLock(lockKey, requestId, expireTime)) {
                return true;
            }
            
            try {
                Thread.sleep(retryInterval);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return false;
            }
        }
        
        return false;
    }
}
```

#### 使用分布式锁
```java
@Service
public class BusinessService {
    
    @Autowired
    private DistributedLockService lockService;
    
    public void processWithLock(String businessKey) {
        String lockKey = "business:" + businessKey;
        String requestId = UUID.randomUUID().toString();
        
        try {
            // 尝试获取锁
            if (lockService.acquireLock(lockKey, requestId, 30000)) {
                try {
                    // 执行业务逻辑
                    doBusinessLogic(businessKey);
                } finally {
                    // 释放锁
                    lockService.releaseLock(lockKey, requestId);
                }
            } else {
                throw new RuntimeException("获取锁失败");
            }
        } catch (Exception e) {
            // 处理异常
            log.error("业务处理失败", e);
            throw e;
        }
    }
    
    private void doBusinessLogic(String businessKey) {
        // 具体的业务逻辑
        log.info("执行业务逻辑: {}", businessKey);
    }
}
```

### 消息发布订阅

#### 消息发布者
```java
@Service
public class MessagePublisher {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    /**
     * 发布消息到指定频道
     */
    public void publish(String channel, Object message) {
        redisTemplate.convertAndSend(channel, message);
    }
    
    /**
     * 发布消息到多个频道
     */
    public void publishToChannels(List<String> channels, Object message) {
        channels.forEach(channel -> publish(channel, message));
    }
}
```

#### 消息订阅者
```java
@Component
public class MessageSubscriber {
    
    private static final Logger log = LoggerFactory.getLogger(MessageSubscriber.class);
    
    /**
     * 订阅指定频道的消息
     */
    @EventListener
    public void handleMessage(RedisMessageReceivedEvent event) {
        String channel = event.getChannel();
        Object message = event.getMessage();
        
        log.info("收到来自频道 {} 的消息: {}", channel, message);
        
        // 根据频道类型处理不同的消息
        switch (channel) {
            case "user:created":
                handleUserCreated(message);
                break;
            case "order:updated":
                handleOrderUpdated(message);
                break;
            default:
                log.warn("未知频道: {}", channel);
        }
    }
    
    private void handleUserCreated(Object message) {
        log.info("处理用户创建消息: {}", message);
        // 处理用户创建逻辑
    }
    
    private void handleOrderUpdated(Object message) {
        log.info("处理订单更新消息: {}", message);
        // 处理订单更新逻辑
    }
}
```

#### 消息监听器配置
```java
@Configuration
public class RedisMessageConfig {
    
    @Bean
    public RedisMessageListenerContainer redisMessageListenerContainer(
            RedisConnectionFactory connectionFactory) {
        
        RedisMessageListenerContainer container = new RedisMessageListenerContainer();
        container.setConnectionFactory(connectionFactory);
        
        // 配置消息监听器
        MessageListenerAdapter listenerAdapter = new MessageListenerAdapter(
            new MessageSubscriber(), "handleMessage");
        
        container.addMessageListener(listenerAdapter, 
            new ChannelTopic("user:created"));
        container.addMessageListener(listenerAdapter, 
            new ChannelTopic("order:updated"));
        
        return container;
    }
}
```

### 集群和哨兵支持

#### Redis Cluster 配置
```java
@Configuration
public class RedisClusterConfig {
    
    @Bean
    public RedisConnectionFactory redisConnectionFactory() {
        RedisClusterConfiguration clusterConfig = new RedisClusterConfiguration();
        clusterConfig.clusterNode("127.0.0.1", 7001);
        clusterConfig.clusterNode("127.0.0.1", 7002);
        clusterConfig.clusterNode("127.0.0.1", 7003);
        clusterConfig.clusterNode("127.0.0.1", 7004);
        clusterConfig.clusterNode("127.0.0.1", 7005);
        clusterConfig.clusterNode("127.0.0.1", 7006);
        
        return new LettuceConnectionFactory(clusterConfig);
    }
}
```

#### Redis Sentinel 配置
```java
@Configuration
public class RedisSentinelConfig {
    
    @Bean
    public RedisConnectionFactory redisConnectionFactory() {
        RedisSentinelConfiguration sentinelConfig = new RedisSentinelConfiguration()
            .master("mymaster")
            .sentinel("127.0.0.1", 26379)
            .sentinel("127.0.0.1", 26380)
            .sentinel("127.0.0.1", 26381);
        
        return new LettuceConnectionFactory(sentinelConfig);
    }
}
```

## 最佳实践

### 键命名规范

#### 命名约定
```java
public class RedisKeyUtils {
    
    // 用户相关键
    public static String getUserKey(Long userId) {
        return "user:" + userId;
    }
    
    public static String getUserProfileKey(Long userId) {
        return "user:profile:" + userId;
    }
    
    public static String getUserSessionKey(String sessionId) {
        return "user:session:" + sessionId;
    }
    
    // 订单相关键
    public static String getOrderKey(String orderId) {
        return "order:" + orderId;
    }
    
    public static String getOrderStatusKey(String orderId) {
        return "order:status:" + orderId;
    }
    
    // 缓存相关键
    public static String getCacheKey(String prefix, String... params) {
        return prefix + ":" + String.join(":", params);
    }
    
    // 锁相关键
    public static String getLockKey(String business, String id) {
        return "lock:" + business + ":" + id;
    }
}
```

### 序列化策略

#### 选择合适的序列化器
```java
@Configuration
public class SerializationConfig {
    
    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory connectionFactory) {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory);
        
        // 对于简单的字符串值，使用 StringRedisSerializer
        template.setKeySerializer(new StringRedisSerializer());
        template.setHashKeySerializer(new StringRedisSerializer());
        
        // 对于复杂对象，使用 JSON 序列化器
        Jackson2JsonRedisSerializer<Object> jsonSerializer = new Jackson2JsonRedisSerializer<>(Object.class);
        ObjectMapper objectMapper = new ObjectMapper();
        
        // 配置 ObjectMapper
        objectMapper.setVisibility(PropertyAccessor.ALL, JsonAutoDetect.Visibility.ANY);
        objectMapper.activateDefaultTyping(LaissezFaireSubTypeValidator.instance, 
            ObjectMapper.DefaultTyping.NON_FINAL, JsonTypeInfo.As.PROPERTY);
        objectMapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        
        jsonSerializer.setObjectMapper(objectMapper);
        
        template.setValueSerializer(jsonSerializer);
        template.setHashValueSerializer(jsonSerializer);
        
        template.afterPropertiesSet();
        return template;
    }
}
```

### 异常处理

#### 统一的异常处理
```java
@ControllerAdvice
public class RedisExceptionHandler {
    
    private static final Logger log = LoggerFactory.getLogger(RedisExceptionHandler.class);
    
    @ExceptionHandler(RedisConnectionFailureException.class)
    public ResponseEntity<String> handleRedisConnectionFailure(RedisConnectionFailureException e) {
        log.error("Redis 连接失败", e);
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
            .body("缓存服务暂时不可用");
    }
    
    @ExceptionHandler(RedisSystemException.class)
    public ResponseEntity<String> handleRedisSystemException(RedisSystemException e) {
        log.error("Redis 系统异常", e);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body("缓存服务内部错误");
    }
    
    @ExceptionHandler(SerializationException.class)
    public ResponseEntity<String> handleSerializationException(SerializationException e) {
        log.error("序列化异常", e);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
            .body("数据格式错误");
    }
}
```

### 监控和日志

#### Redis 操作监控
```java
@Component
public class RedisOperationMonitor {
    
    private static final Logger log = LoggerFactory.getLogger(RedisOperationMonitor.class);
    
    @EventListener
    public void handleRedisOperation(RedisOperationEvent event) {
        String operation = event.getOperation();
        String key = event.getKey();
        long duration = event.getDuration();
        
        log.info("Redis 操作: {} - 键: {} - 耗时: {}ms", operation, key, duration);
        
        // 记录慢查询
        if (duration > 100) {
            log.warn("慢查询检测: {} - 键: {} - 耗时: {}ms", operation, key, duration);
        }
    }
}
```

## 常见问题

### 连接问题

#### 连接超时
```java
@Configuration
public class RedisConnectionConfig {
    
    @Bean
    public RedisConnectionFactory redisConnectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName("localhost");
        config.setPort(6379);
        
        LettuceClientConfiguration clientConfig = LettuceClientConfiguration.builder()
            .commandTimeout(Duration.ofSeconds(5))
            .shutdownTimeout(Duration.ofSeconds(5))
            .build();
        
        return new LettuceConnectionFactory(config, clientConfig);
    }
}
```

#### 连接池配置
```java
@Configuration
public class RedisPoolConfig {
    
    @Bean
    public RedisConnectionFactory redisConnectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName("localhost");
        config.setPort(6379);
        
        GenericObjectPoolConfig<Object> poolConfig = new GenericObjectPoolConfig<>();
        poolConfig.setMaxTotal(20);
        poolConfig.setMaxIdle(10);
        poolConfig.setMinIdle(5);
        poolConfig.setMaxWaitMillis(3000);
        poolConfig.setTestOnBorrow(true);
        poolConfig.setTestOnReturn(true);
        poolConfig.setTestWhileIdle(true);
        
        return new LettuceConnectionFactory(config);
    }
}
```

### 序列化问题

#### 处理循环引用
```java
@Configuration
public class RedisSerializationConfig {
    
    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory connectionFactory) {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory);
        
        Jackson2JsonRedisSerializer<Object> jsonSerializer = new Jackson2JsonRedisSerializer<>(Object.class);
        ObjectMapper objectMapper = new ObjectMapper();
        
        // 处理循环引用
        objectMapper.configure(SerializationFeature.FAIL_ON_EMPTY_BEANS, false);
        objectMapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);
        
        // 忽略 transient 字段
        objectMapper.configure(MapperFeature.PROPAGATE_TRANSIENT_MARKER, true);
        
        jsonSerializer.setObjectMapper(objectMapper);
        
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(jsonSerializer);
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(jsonSerializer);
        
        template.afterPropertiesSet();
        return template;
    }
}
```

### 性能问题

#### 批量操作优化
```java
@Service
public class BatchOperationService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    // 批量设置值
    public void batchSet(Map<String, Object> keyValueMap) {
        if (keyValueMap.size() > 1000) {
            // 分批处理，避免单次操作过大
            List<Map<String, Object>> batches = splitMap(keyValueMap, 1000);
            batches.forEach(this::processBatch);
        } else {
            processBatch(keyValueMap);
        }
    }
    
    private void processBatch(Map<String, Object> batch) {
        redisTemplate.executePipelined(new SessionCallback<Object>() {
            @Override
            public Object execute(RedisOperations operations) throws DataAccessException {
                batch.forEach((key, value) -> {
                    operations.opsForValue().set(key, value);
                });
                return null;
            }
        });
    }
    
    private List<Map<String, Object>> splitMap(Map<String, Object> map, int batchSize) {
        List<Map<String, Object>> batches = new ArrayList<>();
        Iterator<Map.Entry<String, Object>> iterator = map.entrySet().iterator();
        
        while (iterator.hasNext()) {
            Map<String, Object> batch = new HashMap<>();
            for (int i = 0; i < batchSize && iterator.hasNext(); i++) {
                Map.Entry<String, Object> entry = iterator.next();
                batch.put(entry.getKey(), entry.getValue());
            }
            batches.add(batch);
        }
        
        return batches;
    }
}
```

## 性能优化

### 连接池优化

#### 连接池参数调优
```java
@Configuration
public class OptimizedRedisConfig {
    
    @Bean
    public RedisConnectionFactory redisConnectionFactory() {
        RedisStandaloneConfiguration config = new RedisStandaloneConfiguration();
        config.setHostName("localhost");
        config.setPort(6379);
        
        // 优化连接池配置
        GenericObjectPoolConfig<Object> poolConfig = new GenericObjectPoolConfig<>();
        
        // 根据并发量调整最大连接数
        poolConfig.setMaxTotal(50);
        poolConfig.setMaxIdle(20);
        poolConfig.setMinIdle(10);
        
        // 连接获取超时时间
        poolConfig.setMaxWaitMillis(2000);
        
        // 连接验证
        poolConfig.setTestOnBorrow(true);
        poolConfig.setTestOnReturn(false);
        poolConfig.setTestWhileIdle(true);
        
        // 空闲连接检测
        poolConfig.setTimeBetweenEvictionRunsMillis(30000);
        poolConfig.setMinEvictableIdleTimeMillis(1800000);
        
        return new LettuceConnectionFactory(config);
    }
}
```

### 序列化优化

#### 使用更高效的序列化器
```java
@Configuration
public class OptimizedSerializationConfig {
    
    @Bean
    public RedisTemplate<String, Object> redisTemplate(RedisConnectionFactory connectionFactory) {
        RedisTemplate<String, Object> template = new RedisTemplate<>();
        template.setConnectionFactory(connectionFactory);
        
        // 使用 Kryo 序列化器提高性能
        KryoRedisSerializer<Object> kryoSerializer = new KryoRedisSerializer<>();
        
        template.setKeySerializer(new StringRedisSerializer());
        template.setValueSerializer(kryoSerializer);
        template.setHashKeySerializer(new StringRedisSerializer());
        template.setHashValueSerializer(kryoSerializer);
        
        template.afterPropertiesSet();
        return template;
    }
}

// Kryo 序列化器实现
public class KryoRedisSerializer<T> implements RedisSerializer<T> {
    
    private final Kryo kryo;
    
    public KryoRedisSerializer() {
        this.kryo = new Kryo();
        this.kryo.setRegistrationRequired(false);
    }
    
    @Override
    public byte[] serialize(T t) throws SerializationException {
        if (t == null) {
            return new byte[0];
        }
        
        try (ByteArrayOutputStream baos = new ByteArrayOutputStream();
             Output output = new Output(baos)) {
            kryo.writeObject(output, t);
            output.flush();
            return baos.toByteArray();
        } catch (Exception e) {
            throw new SerializationException("序列化失败", e);
        }
    }
    
    @Override
    public T deserialize(byte[] bytes) throws SerializationException {
        if (bytes == null || bytes.length == 0) {
            return null;
        }
        
        try (ByteArrayInputStream bais = new ByteArrayInputStream(bytes);
             Input input = new Input(bais)) {
            return (T) kryo.readObject(input, Object.class);
        } catch (Exception e) {
            throw new SerializationException("反序列化失败", e);
        }
    }
}
```

### 缓存策略优化

#### 多级缓存
```java
@Service
public class MultiLevelCacheService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    @Autowired
    private CaffeineCacheManager localCacheManager;
    
    // 本地缓存 + Redis 缓存
    public Object getWithMultiLevelCache(String key) {
        // 第一级：本地缓存
        Object localValue = localCacheManager.getCache("local").get(key);
        if (localValue != null) {
            return localValue;
        }
        
        // 第二级：Redis 缓存
        Object redisValue = redisTemplate.opsForValue().get(key);
        if (redisValue != null) {
            // 回填本地缓存
            localCacheManager.getCache("local").put(key, redisValue);
        }
        
        return redisValue;
    }
    
    // 写入时同步更新两级缓存
    public void setWithMultiLevelCache(String key, Object value) {
        // 更新 Redis
        redisTemplate.opsForValue().set(key, value);
        
        // 更新本地缓存
        localCacheManager.getCache("local").put(key, value);
    }
}
```

## 实战示例

### 用户会话管理

#### 会话存储服务
```java
@Service
public class UserSessionService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    private static final String SESSION_PREFIX = "session:";
    private static final Duration SESSION_TIMEOUT = Duration.ofHours(2);
    
    /**
     * 创建用户会话
     */
    public String createSession(Long userId, UserSession session) {
        String sessionId = UUID.randomUUID().toString();
        String key = SESSION_PREFIX + sessionId;
        
        redisTemplate.opsForValue().set(key, session, SESSION_TIMEOUT);
        
        // 同时存储用户ID到会话ID的映射
        String userSessionKey = "user:session:" + userId;
        redisTemplate.opsForValue().set(userSessionKey, sessionId, SESSION_TIMEOUT);
        
        return sessionId;
    }
    
    /**
     * 获取用户会话
     */
    public UserSession getSession(String sessionId) {
        String key = SESSION_PREFIX + sessionId;
        return (UserSession) redisTemplate.opsForValue().get(key);
    }
    
    /**
     * 更新会话
     */
    public void updateSession(String sessionId, UserSession session) {
        String key = SESSION_PREFIX + sessionId;
        redisTemplate.opsForValue().set(key, session, SESSION_TIMEOUT);
    }
    
    /**
     * 删除会话
     */
    public void deleteSession(String sessionId) {
        String key = SESSION_PREFIX + sessionId;
        UserSession session = getSession(sessionId);
        
        if (session != null) {
            // 删除会话
            redisTemplate.delete(key);
            
            // 删除用户ID映射
            String userSessionKey = "user:session:" + session.getUserId();
            redisTemplate.delete(userSessionKey);
        }
    }
    
    /**
     * 获取用户的所有会话
     */
    public List<UserSession> getUserSessions(Long userId) {
        String userSessionKey = "user:session:" + userId;
        String sessionId = (String) redisTemplate.opsForValue().get(userSessionKey);
        
        if (sessionId != null) {
            UserSession session = getSession(sessionId);
            return session != null ? Collections.singletonList(session) : Collections.emptyList();
        }
        
        return Collections.emptyList();
    }
}
```

### 购物车实现

#### 购物车服务
```java
@Service
public class ShoppingCartService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    private static final String CART_PREFIX = "cart:";
    private static final Duration CART_TIMEOUT = Duration.ofDays(30);
    
    /**
     * 添加商品到购物车
     */
    public void addToCart(Long userId, Long productId, Integer quantity) {
        String cartKey = CART_PREFIX + userId;
        
        // 使用 Hash 存储购物车商品
        redisTemplate.opsForHash().put(cartKey, productId.toString(), quantity);
        
        // 设置过期时间
        redisTemplate.expire(cartKey, CART_TIMEOUT);
    }
    
    /**
     * 从购物车移除商品
     */
    public void removeFromCart(Long userId, Long productId) {
        String cartKey = CART_PREFIX + userId;
        redisTemplate.opsForHash().delete(cartKey, productId.toString());
    }
    
    /**
     * 更新购物车商品数量
     */
    public void updateCartItemQuantity(Long userId, Long productId, Integer quantity) {
        if (quantity <= 0) {
            removeFromCart(userId, productId);
        } else {
            String cartKey = CART_PREFIX + userId;
            redisTemplate.opsForHash().put(cartKey, productId.toString(), quantity);
            redisTemplate.expire(cartKey, CART_TIMEOUT);
        }
    }
    
    /**
     * 获取购物车内容
     */
    public Map<Long, Integer> getCart(Long userId) {
        String cartKey = CART_PREFIX + userId;
        Map<Object, Object> cartMap = redisTemplate.opsForHash().entries(cartKey);
        
        Map<Long, Integer> result = new HashMap<>();
        cartMap.forEach((key, value) -> {
            result.put(Long.valueOf(key.toString()), (Integer) value);
        });
        
        return result;
    }
    
    /**
     * 清空购物车
     */
    public void clearCart(Long userId) {
        String cartKey = CART_PREFIX + userId;
        redisTemplate.delete(cartKey);
    }
    
    /**
     * 获取购物车商品数量
     */
    public Long getCartItemCount(Long userId) {
        String cartKey = CART_PREFIX + userId;
        return redisTemplate.opsForHash().size(cartKey);
    }
}
```

### 排行榜系统

#### 排行榜服务
```java
@Service
public class LeaderboardService {
    
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;
    
    private static final String LEADERBOARD_PREFIX = "leaderboard:";
    
    /**
     * 更新用户分数
     */
    public void updateScore(String leaderboardName, Long userId, Double score) {
        String key = LEADERBOARD_PREFIX + leaderboardName;
        redisTemplate.opsForZSet().add(key, userId, score);
    }
    
    /**
     * 获取用户排名（升序）
     */
    public Long getUserRank(String leaderboardName, Long userId) {
        String key = LEADERBOARD_PREFIX + leaderboardName;
        return redisTemplate.opsForZSet().rank(key, userId);
    }
    
    /**
     * 获取用户排名（降序）
     */
    public Long getUserReverseRank(String leaderboardName, Long userId) {
        String key = LEADERBOARD_PREFIX + leaderboardName;
        return redisTemplate.opsForZSet().reverseRank(key, userId);
    }
    
    /**
     * 获取排行榜前N名
     */
    public List<LeaderboardEntry> getTopN(String leaderboardName, int n) {
        String key = LEADERBOARD_PREFIX + leaderboardName;
        Set<ZSetOperations.TypedTuple<Object>> topN = 
            redisTemplate.opsForZSet().reverseRangeWithScores(key, 0, n - 1);
        
        List<LeaderboardEntry> result = new ArrayList<>();
        if (topN != null) {
            for (ZSetOperations.TypedTuple<Object> tuple : topN) {
                result.add(new LeaderboardEntry(
                    (Long) tuple.getValue(),
                    tuple.getScore()
                ));
            }
        }
        
        return result;
    }
    
    /**
     * 获取用户分数
     */
    public Double getUserScore(String leaderboardName, Long userId) {
        String key = LEADERBOARD_PREFIX + leaderboardName;
        return redisTemplate.opsForZSet().score(key, userId);
    }
    
    /**
     * 获取排行榜总人数
     */
    public Long getLeaderboardSize(String leaderboardName) {
        String key = LEADERBOARD_PREFIX + leaderboardName;
        return redisTemplate.opsForZSet().size(key);
    }
    
    /**
     * 获取分数范围内的用户
     */
    public List<LeaderboardEntry> getUsersByScoreRange(String leaderboardName, 
                                                      Double minScore, Double maxScore) {
        String key = LEADERBOARD_PREFIX + leaderboardName;
        Set<ZSetOperations.TypedTuple<Object>> users = 
            redisTemplate.opsForZSet().rangeByScoreWithScores(key, minScore, maxScore);
        
        List<LeaderboardEntry> result = new ArrayList<>();
        if (users != null) {
            for (ZSetOperations.TypedTuple<Object> tuple : users) {
                result.add(new LeaderboardEntry(
                    (Long) tuple.getValue(),
                    tuple.getScore()
                ));
            }
        }
        
        return result;
    }
}

// 排行榜条目
public class LeaderboardEntry {
    private Long userId;
    private Double score;
    
    public LeaderboardEntry(Long userId, Double score) {
        this.userId = userId;
        this.score = score;
    }
    
    // getters and setters
    public Long getUserId() { return userId; }
    public void setUserId(Long userId) { this.userId = userId; }
    public Double getScore() { return score; }
    public void setScore(Double score) { this.score = score; }
}
```

## 总结

Spring Data Redis 提供了强大而灵活的 Redis 操作能力，通过本文档的学习，你应该能够：

1. **理解核心概念**：掌握 Redis 数据类型和 Spring Data Redis 的核心组件
2. **配置环境**：正确配置依赖和连接参数
3. **使用基础功能**：熟练使用各种数据类型的操作方法
4. **应用高级特性**：实现缓存、分布式锁、消息发布订阅等功能
5. **遵循最佳实践**：采用合适的命名规范、序列化策略和异常处理
6. **解决常见问题**：处理连接、序列化和性能相关问题
7. **优化性能**：通过连接池、序列化和缓存策略优化性能
8. **实战应用**：在实际项目中实现用户会话、购物车、排行榜等功能

### 学习建议

1. **循序渐进**：从基础操作开始，逐步学习高级特性
2. **实践为主**：多写代码，在实际项目中应用所学知识
3. **关注性能**：注意 Redis 操作的性能影响，合理使用批量操作和管道
4. **监控运维**：建立完善的监控和日志体系
5. **持续学习**：关注 Redis 新版本特性和 Spring Data Redis 的更新

### 扩展资源

- [Spring Data Redis 官方文档](https://docs.spring.io/spring-data/redis/docs/current/reference/html/)
- [Redis 官方文档](https://redis.io/documentation)
- [Spring Boot 参考指南](https://docs.spring.io/spring-boot/docs/current/reference/html/)
- [Redis 命令参考](https://redis.io/commands)

通过系统学习和实践，你将能够熟练使用 Spring Data Redis 构建高性能、可扩展的缓存和存储解决方案。
