---
title: Redisson全面指南
main_color: "#1785e6ff"
categories: Redis
tags:
  - Redis
  - Redisson
  - 分布式锁
  - 缓存
cover: https://free.picui.cn/free/2026/03/29/69c899e433fa4.png
---

# Redisson全面指南

## 1. 什么是Redisson

Redisson是一个在Redis基础上实现的Java驻内存数据网格（In-Memory Data Grid），它不仅提供了Redis的基础功能，还提供了许多高级特性，如分布式锁、分布式集合、分布式服务等。

### 1.1 主要特性
- **分布式锁**：支持可重入锁、公平锁、读写锁等
- **分布式集合**：Map、Set、List、Queue等
- **分布式服务**：限流器、布隆过滤器、地理空间等
- **集群支持**：支持Redis集群、哨兵模式
- **连接池管理**：自动连接池管理，支持连接复用

### 1.2 与Jedis的区别
- **Jedis**：轻量级Redis客户端，功能相对简单
- **Redisson**：功能丰富的Redis客户端，提供更多高级特性

## 2. 环境搭建

### 2.1 Maven依赖

```xml
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson</artifactId>
    <version>3.24.3</version>
</dependency>
```

### 2.2 基础配置

```java
import org.redisson.Redisson;
import org.redisson.api.RedissonClient;
import org.redisson.config.Config;

public class RedissonConfig {
    
    public static RedissonClient createClient() {
        Config config = new Config();
        config.useSingleServer()
                .setAddress("redis://localhost:6379")
                .setPassword("password")
                .setDatabase(0)
                .setConnectionPoolSize(64)
                .setConnectionMinimumIdleSize(10);
        
        return Redisson.create(config);
    }
    
    // 集群配置
    public static RedissonClient createClusterClient() {
        Config config = new Config();
        config.useClusterServers()
                .addNodeAddress("redis://192.168.1.10:7000")
                .addNodeAddress("redis://192.168.1.11:7000")
                .addNodeAddress("redis://192.168.1.12:7000")
                .setScanInterval(2000);
        
        return Redisson.create(config);
    }
    
    // 哨兵配置
    public static RedissonClient createSentinelClient() {
        Config config = new Config();
        config.useSentinelServers()
                .setMasterName("mymaster")
                .addSentinelAddress("redis://192.168.1.10:26379")
                .addSentinelAddress("redis://192.168.1.11:26379");
        
        return Redisson.create(config);
    }
}
```

## 3. 分布式锁

### 3.1 可重入锁（RLock）

```java
import org.redisson.api.RLock;
import java.util.concurrent.TimeUnit;

public class DistributedLockExample {
    
    private final RedissonClient redissonClient;
    
    public DistributedLockExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void executeWithLock(String lockKey, Runnable task) {
        RLock lock = redissonClient.getLock(lockKey);
        
        try {
            // 尝试获取锁，最多等待10秒，锁过期时间30秒
            if (lock.tryLock(10, 30, TimeUnit.SECONDS)) {
                try {
                    task.run();
                } finally {
                    lock.unlock();
                }
            } else {
                throw new RuntimeException("获取锁失败");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("锁操作被中断", e);
        }
    }
    
    // 业务方法示例
    public void processOrder(String orderId) {
        String lockKey = "order:lock:" + orderId;
        executeWithLock(lockKey, () -> {
            // 处理订单逻辑
            System.out.println("处理订单: " + orderId);
            // 模拟业务处理时间
            try {
                Thread.sleep(1000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });
    }
}
```

### 3.2 公平锁

```java
public class FairLockExample {
    
    private final RedissonClient redissonClient;
    
    public FairLockExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void executeWithFairLock(String lockKey, Runnable task) {
        RLock fairLock = redissonClient.getFairLock(lockKey);
        
        try {
            if (fairLock.tryLock(10, 30, TimeUnit.SECONDS)) {
                try {
                    task.run();
                } finally {
                    fairLock.unlock();
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

### 3.3 读写锁

```java
public class ReadWriteLockExample {
    
    private final RedissonClient redissonClient;
    
    public ReadWriteLockExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void readData(String key) {
        RReadWriteLock rwLock = redissonClient.getReadWriteLock(key);
        RLock readLock = rwLock.readLock();
        
        try {
            if (readLock.tryLock(10, 30, TimeUnit.SECONDS)) {
                try {
                    // 读取数据
                    System.out.println("读取数据: " + key);
                } finally {
                    readLock.unlock();
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
    
    public void writeData(String key, String value) {
        RReadWriteLock rwLock = redissonClient.getReadWriteLock(key);
        RLock writeLock = rwLock.writeLock();
        
        try {
            if (writeLock.tryLock(10, 30, TimeUnit.SECONDS)) {
                try {
                    // 写入数据
                    System.out.println("写入数据: " + key + " = " + value);
                } finally {
                    writeLock.unlock();
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

### 3.4 多重锁

```java
public class MultiLockExample {
    
    private final RedissonClient redissonClient;
    
    public MultiLockExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void executeWithMultiLock(List<String> lockKeys, Runnable task) {
        RLock[] locks = lockKeys.stream()
                .map(redissonClient::getLock)
                .toArray(RLock[]::new);
        
        RLock multiLock = redissonClient.getMultiLock(locks);
        
        try {
            if (multiLock.tryLock(10, 30, TimeUnit.SECONDS)) {
                try {
                    task.run();
                } finally {
                    multiLock.unlock();
                }
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

## 4. 分布式集合

### 4.1 分布式Map

```java
import org.redisson.api.RMap;
import java.util.concurrent.TimeUnit;

public class DistributedMapExample {
    
    private final RedissonClient redissonClient;
    
    public DistributedMapExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void mapOperations() {
        RMap<String, String> map = redissonClient.getMap("myMap");
        
        // 基本操作
        map.put("key1", "value1");
        map.put("key2", "value2");
        
        // 批量操作
        map.putAll(Map.of("key3", "value3", "key4", "value4"));
        
        // 原子操作
        map.putIfAbsent("key1", "newValue");
        
        // 过期时间
        map.expire(1, TimeUnit.HOURS);
        
        // 监听器
        map.addListener(new EntryListener<String, String>() {
            @Override
            public void onPut(EntryEvent<String, String> event) {
                System.out.println("Put: " + event.getKey() + " = " + event.getValue());
            }
            
            @Override
            public void onRemove(EntryEvent<String, String> event) {
                System.out.println("Remove: " + event.getKey());
            }
            
            // 其他方法实现...
        });
    }
}
```

### 4.2 分布式Set

```java
import org.redisson.api.RSet;

public class DistributedSetExample {
    
    private final RedissonClient redissonClient;
    
    public DistributedSetExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void setOperations() {
        RSet<String> set = redissonClient.getSet("mySet");
        
        // 基本操作
        set.add("item1");
        set.add("item2");
        set.addAll(Arrays.asList("item3", "item4"));
        
        // 集合运算
        RSet<String> set2 = redissonClient.getSet("mySet2");
        set2.add("item2");
        set2.add("item5");
        
        // 交集
        RSet<String> intersection = set.intersection(set2);
        
        // 并集
        RSet<String> union = set.union(set2);
        
        // 差集
        RSet<String> difference = set.difference(set2);
    }
}
```

### 4.3 分布式List

```java
import org.redisson.api.RList;

public class DistributedListExample {
    
    private final RedissonClient redissonClient;
    
    public DistributedListExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void listOperations() {
        RList<String> list = redissonClient.getList("myList");
        
        // 基本操作
        list.add("item1");
        list.add("item2");
        list.add(0, "item0");
        
        // 批量操作
        list.addAll(Arrays.asList("item3", "item4"));
        
        // 获取元素
        String first = list.get(0);
        String last = list.get(list.size() - 1);
        
        // 删除操作
        list.remove("item1");
        list.remove(0);
    }
}
```

### 4.4 分布式Queue

```java
import org.redisson.api.RQueue;
import org.redisson.api.RBlockingQueue;

public class DistributedQueueExample {
    
    private final RedissonClient redissonClient;
    
    public DistributedQueueExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void queueOperations() {
        RQueue<String> queue = redissonClient.getQueue("myQueue");
        
        // 基本操作
        queue.offer("task1");
        queue.offer("task2");
        
        // 消费队列
        String task = queue.poll();
        
        // 阻塞队列
        RBlockingQueue<String> blockingQueue = redissonClient.getBlockingQueue("myBlockingQueue");
        
        try {
            // 阻塞等待元素
            String element = blockingQueue.take();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

### 4.5 Bucket（RBucket/RBuckets）

```java
import org.redisson.api.RBucket;
import org.redisson.api.RBuckets;

public class BucketExample {
    
    private final RedissonClient redissonClient;
    
    public BucketExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void singleValueOps() {
        RBucket<String> bucket = redissonClient.getBucket("config:site:title");
        
        // set / get
        bucket.set("我的博客");
        String title = bucket.get();
        
        // 带TTL的写入
        bucket.set("临时值", 10, TimeUnit.MINUTES);
        
        // CAS
        boolean updated = bucket.compareAndSet("临时值", "新值");
        
        // getAndSet
        String old = bucket.getAndSet("最终值");
        
        // 存在则不覆盖
        boolean created = bucket.trySet("仅当不存在时写入");
        
        // 删除
        bucket.delete();
    }
    
    public void multiValueOps() {
        RBuckets buckets = redissonClient.getBuckets();
        
        // 批量设置
        Map<String, Object> map = new HashMap<>();
        map.put("config:a", 1);
        map.put("config:b", 2);
        buckets.set(map);
        
        // 批量读取
        Map<String, Object> results = buckets.get("config:a", "config:b");
        results.forEach((k, v) -> System.out.println(k + " -> " + v));
    }
}
```

## 5. 分布式服务

### 5.1 限流器

```java
import org.redisson.api.RRateLimiter;

public class RateLimiterExample {
    
    private final RedissonClient redissonClient;
    
    public RateLimiterExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void rateLimitExample() {
        RRateLimiter rateLimiter = redissonClient.getRateLimiter("myRateLimiter");
        
        // 设置速率：每1秒产生2个令牌
        rateLimiter.trySetRate(RateType.OVERALL, 2, 1, RateIntervalUnit.SECONDS);
        
        // 尝试获取令牌
        if (rateLimiter.tryAcquire(1)) {
            System.out.println("获取令牌成功，执行业务逻辑");
        } else {
            System.out.println("获取令牌失败，请求被限流");
        }
    }
    
    // 业务方法限流
    public void processWithRateLimit(String userId) {
        RRateLimiter userLimiter = redissonClient.getRateLimiter("user:" + userId + ":limit");
        userLimiter.trySetRate(RateType.OVERALL, 10, 1, RateIntervalUnit.MINUTES);
        
        if (userLimiter.tryAcquire(1)) {
            // 执行业务逻辑
            System.out.println("用户 " + userId + " 请求被处理");
        } else {
            throw new RuntimeException("用户请求过于频繁，请稍后再试");
        }
    }
}
```

### 5.2 布隆过滤器

```java
import org.redisson.api.RBloomFilter;

public class BloomFilterExample {
    
    private final RedissonClient redissonClient;
    
    public BloomFilterExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void bloomFilterExample() {
        RBloomFilter<String> bloomFilter = redissonClient.getBloomFilter("myBloomFilter");
        
        // 初始化布隆过滤器：预期元素数量10000，误判率0.01
        bloomFilter.tryInit(10000L, 0.01);
        
        // 添加元素
        bloomFilter.add("user1@example.com");
        bloomFilter.add("user2@example.com");
        
        // 检查元素是否存在
        boolean exists = bloomFilter.contains("user1@example.com");
        boolean notExists = bloomFilter.contains("user3@example.com");
        
        System.out.println("user1 exists: " + exists);
        System.out.println("user3 exists: " + notExists);
    }
    
    // 邮件地址去重示例
    public boolean isEmailProcessed(String email) {
        RBloomFilter<String> emailFilter = redissonClient.getBloomFilter("processedEmails");
        emailFilter.tryInit(100000L, 0.001);
        
        if (emailFilter.contains(email)) {
            return true; // 可能已处理过
        }
        
        // 添加到过滤器
        emailFilter.add(email);
        return false; // 未处理过
    }
}
```

### 5.3 地理空间

```java
import org.redisson.api.RGeo;
import org.redisson.api.GeoUnit;

public class GeoExample {
    
    private final RedissonClient redissonClient;
    
    public GeoExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void geoOperations() {
        RGeo<String> geo = redissonClient.getGeo("myGeo");
        
        // 添加地理位置
        geo.add(116.397128, 39.916527, "北京");
        geo.add(121.473701, 31.230416, "上海");
        geo.add(113.264435, 23.129163, "广州");
        
        // 计算距离
        Double distance = geo.dist("北京", "上海", GeoUnit.KILOMETERS);
        System.out.println("北京到上海距离: " + distance + " km");
        
        // 查找附近的位置
        Map<String, Double> nearby = geo.searchWithDistance("北京", 1000, GeoUnit.KILOMETERS);
        nearby.forEach((city, dist) -> 
            System.out.println(city + ": " + dist + " km"));
    }
    
    // 附近商家查询示例
    public List<String> findNearbyStores(double longitude, double latitude, double radius) {
        RGeo<String> storeGeo = redissonClient.getGeo("stores");
        
        // 查找指定半径内的商家
        return storeGeo.search(radius, GeoUnit.KILOMETERS, longitude, latitude);
    }
}
```

### 5.4 信号量（RSemaphore/RPermitExpirableSemaphore）

```java
import org.redisson.api.RSemaphore;
import org.redisson.api.RPermitExpirableSemaphore;

public class SemaphoreExample {
    
    private final RedissonClient redissonClient;
    
    public SemaphoreExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    // 固定并发许可数量
    public void fixedPermits() {
        RSemaphore semaphore = redissonClient.getSemaphore("concurrency:processImage");
        // 初始化许可数（仅首次设置生效）
        semaphore.trySetPermits(5);
        
        try {
            // 获取许可（可阻塞/可超时）
            boolean ok = semaphore.tryAcquire(1, 3, TimeUnit.SECONDS);
            if (!ok) {
                System.out.println("当前并发已满，稍后重试");
                return;
            }
            try {
                // 执行业务
                System.out.println("处理图片中...");
            } finally {
                // 释放许可
                semaphore.release();
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
    
    // 带自动过期的许可（避免忘记释放导致永久占用）
    public void expirablePermits() {
        RPermitExpirableSemaphore expirable = redissonClient.getPermitExpirableSemaphore("concurrency:generateReport");
        expirable.trySetPermits(3);
        
        try {
            // 获取许可并设置自动过期时间（例如30秒）
            String permitId = expirable.acquire(30, TimeUnit.SECONDS);
            try {
                // 执行业务
                System.out.println("生成报表中...");
            } finally {
                // 正常释放（如果已过期，释放将返回false，可忽略）
                expirable.release(permitId);
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

## 6. 常用场景

### 6.1 库存扣减

```java
public class InventoryService {
    
    private final RedissonClient redissonClient;
    
    public InventoryService(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public boolean deductInventory(String productId, int quantity) {
        String lockKey = "inventory:lock:" + productId;
        RLock lock = redissonClient.getLock(lockKey);
        
        try {
            if (lock.tryLock(5, 10, TimeUnit.SECONDS)) {
                try {
                    RAtomicLong inventory = redissonClient.getAtomicLong("inventory:" + productId);
                    long currentStock = inventory.get();
                    
                    if (currentStock >= quantity) {
                        inventory.addAndGet(-quantity);
                        return true;
                    } else {
                        return false;
                    }
                } finally {
                    lock.unlock();
                }
            }
            return false;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        }
    }
}
```

### 6.2 分布式计数器

```java
public class CounterService {
    
    private final RedissonClient redissonClient;
    
    public CounterService(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public long increment(String key) {
        RAtomicLong counter = redissonClient.getAtomicLong(key);
        return counter.incrementAndGet();
    }
    
    public long getCount(String key) {
        RAtomicLong counter = redissonClient.getAtomicLong(key);
        return counter.get();
    }
    
    public void reset(String key) {
        RAtomicLong counter = redissonClient.getAtomicLong(key);
        counter.set(0);
    }
    
    // 带过期时间的计数器
    public long incrementWithExpire(String key, long expireSeconds) {
        RAtomicLong counter = redissonClient.getAtomicLong(key);
        long result = counter.incrementAndGet();
        counter.expire(expireSeconds, TimeUnit.SECONDS);
        return result;
    }
}
```

### 6.3 分布式任务调度

```java
public class TaskScheduler {
    
    private final RedissonClient redissonClient;
    
    public TaskScheduler(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void scheduleTask(String taskId, long delaySeconds, Runnable task) {
        RBlockingQueue<String> taskQueue = redissonClient.getBlockingQueue("delayedTasks");
        
        // 延迟执行
        redissonClient.getExecutorService("taskExecutor").schedule(() -> {
            taskQueue.offer(taskId);
            task.run();
        }, delaySeconds, TimeUnit.SECONDS);
    }
    
    public void processDelayedTasks() {
        RBlockingQueue<String> taskQueue = redissonClient.getBlockingQueue("delayedTasks");
        
        while (true) {
            try {
                String taskId = taskQueue.take();
                System.out.println("处理延迟任务: " + taskId);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }
}
```

### 6.4 接口并发限流（基于信号量）

```java
@Service
public class ConcurrencyGuardService {
    private final RedissonClient redissonClient;
    
    public ConcurrencyGuardService(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void handleRequest(String apiName, Runnable task) {
        String semKey = "api:concurrency:" + apiName;
        RSemaphore semaphore = redissonClient.getSemaphore(semKey);
        semaphore.trySetPermits(20); // 限制该接口最大并发20
        
        try {
            if (!semaphore.tryAcquire(1, 500, TimeUnit.MILLISECONDS)) {
                throw new RuntimeException("并发繁忙，请稍后重试");
            }
            try {
                task.run();
            } finally {
                semaphore.release();
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("请求被中断");
        }
    }
}
```

### 6.5 单值配置/热更新（基于Bucket）

```java
@Service
public class ConfigService {
    private final RedissonClient redissonClient;
    
    public ConfigService(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void updateSiteTitle(String title) {
        redissonClient.getBucket("config:site:title").set(title);
    }
    
    public String getSiteTitle() {
        return (String) redissonClient.getBucket("config:site:title").get();
    }
    
    public void cacheTempToken(String token, long seconds) {
        redissonClient.getBucket("token:" + token).set(Boolean.TRUE, seconds, TimeUnit.SECONDS);
    }
    
    public boolean checkAndConsumeToken(String token) {
        RBucket<Boolean> bucket = redissonClient.getBucket("token:" + token);
        Boolean existed = bucket.getAndSet(null); // 读出后清空
        bucket.delete();
        return Boolean.TRUE.equals(existed);
    }
}
```

## 7. 工具类封装

### 7.1 Redisson工具类

```java
import org.redisson.Redisson;
import org.redisson.api.RedissonClient;
import org.redisson.config.Config;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import javax.annotation.PreDestroy;
import java.util.concurrent.TimeUnit;

@Component
public class RedissonUtil {
    
    @Value("${redis.host:localhost}")
    private String host;
    
    @Value("${redis.port:6379}")
    private int port;
    
    @Value("${redis.password:}")
    private String password;
    
    @Value("${redis.database:0}")
    private int database;
    
    private RedissonClient redissonClient;
    
    @PostConstruct
    public void init() {
        Config config = new Config();
        config.useSingleServer()
                .setAddress("redis://" + host + ":" + port)
                .setPassword(password.isEmpty() ? null : password)
                .setDatabase(database)
                .setConnectionPoolSize(64)
                .setConnectionMinimumIdleSize(10)
                .setIdleConnectionTimeout(10000)
                .setConnectTimeout(10000)
                .setTimeout(3000);
        
        redissonClient = Redisson.create(config);
    }
    
    @PreDestroy
    public void destroy() {
        if (redissonClient != null) {
            redissonClient.shutdown();
        }
    }
    
    public RedissonClient getClient() {
        return redissonClient;
    }
    
    // 分布式锁工具方法
    public boolean executeWithLock(String lockKey, Runnable task, long waitTime, long leaseTime) {
        return executeWithLock(lockKey, task, waitTime, leaseTime, TimeUnit.SECONDS);
    }
    
    public boolean executeWithLock(String lockKey, Runnable task, long waitTime, long leaseTime, TimeUnit unit) {
        RLock lock = redissonClient.getLock(lockKey);
        
        try {
            if (lock.tryLock(waitTime, leaseTime, unit)) {
                try {
                    task.run();
                    return true;
                } finally {
                    lock.unlock();
                }
            }
            return false;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        }
    }
    
    // 带返回值的锁方法
    public <T> T executeWithLock(String lockKey, Supplier<T> task, long waitTime, long leaseTime) {
        return executeWithLock(lockKey, task, waitTime, leaseTime, TimeUnit.SECONDS);
    }
    
    public <T> T executeWithLock(String lockKey, Supplier<T> task, long waitTime, long leaseTime, TimeUnit unit) {
        RLock lock = redissonClient.getLock(lockKey);
        
        try {
            if (lock.tryLock(waitTime, leaseTime, unit)) {
                try {
                    return task.get();
                } finally {
                    lock.unlock();
                }
            }
            throw new RuntimeException("获取锁失败");
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new RuntimeException("锁操作被中断", e);
        }
    }
    
    // 限流器工具方法
    public boolean tryAcquire(String key, int permits, int rate, int rateInterval) {
        RRateLimiter rateLimiter = redissonClient.getRateLimiter(key);
        rateLimiter.trySetRate(RateType.OVERALL, rate, rateInterval, RateIntervalUnit.SECONDS);
        return rateLimiter.tryAcquire(permits);
    }
    
    // 布隆过滤器工具方法
    public boolean addToBloomFilter(String key, String value, long expectedInsertions, double falseProbability) {
        RBloomFilter<String> bloomFilter = redissonClient.getBloomFilter(key);
        bloomFilter.tryInit(expectedInsertions, falseProbability);
        return bloomFilter.add(value);
    }
    
    public boolean containsInBloomFilter(String key, String value) {
        RBloomFilter<String> bloomFilter = redissonClient.getBloomFilter(key);
        return bloomFilter.contains(value);
    }

    // Bucket工具方法
    public <T> void bucketSet(String key, T value) {
        RBucket<T> bucket = redissonClient.getBucket(key);
        bucket.set(value);
    }

    public <T> void bucketSet(String key, T value, long ttl, TimeUnit unit) {
        RBucket<T> bucket = redissonClient.getBucket(key);
        bucket.set(value, ttl, unit);
    }

    public <T> T bucketGet(String key) {
        RBucket<T> bucket = redissonClient.getBucket(key);
        return bucket.get();
    }

    public <T> boolean bucketCompareAndSet(String key, T expected, T update) {
        RBucket<T> bucket = redissonClient.getBucket(key);
        return bucket.compareAndSet(expected, update);
    }

    public <T> T bucketGetAndSet(String key, T update) {
        RBucket<T> bucket = redissonClient.getBucket(key);
        return bucket.getAndSet(update);
    }

    public Map<String, Object> bucketsGet(String... keys) {
        RBuckets buckets = redissonClient.getBuckets();
        return buckets.get(keys);
    }

    public void bucketsSet(Map<String, Object> keyValues) {
        RBuckets buckets = redissonClient.getBuckets();
        buckets.set(keyValues);
    }

    // 信号量工具方法
    public boolean semaphoreTryAcquire(String key, int permits, long timeout, TimeUnit unit) {
        RSemaphore semaphore = redissonClient.getSemaphore(key);
        try {
            return semaphore.tryAcquire(permits, timeout, unit);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return false;
        }
    }

    public void semaphoreRelease(String key, int permits) {
        RSemaphore semaphore = redissonClient.getSemaphore(key);
        semaphore.release(permits);
    }

    public String expirableSemaphoreAcquire(String key, long leaseTime, TimeUnit unit) {
        RPermitExpirableSemaphore expirable = redissonClient.getPermitExpirableSemaphore(key);
        try {
            return expirable.acquire(leaseTime, unit);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return null;
        }
    }

    public boolean expirableSemaphoreRelease(String key, String permitId) {
        if (permitId == null) return false;
        RPermitExpirableSemaphore expirable = redissonClient.getPermitExpirableSemaphore(key);
        return expirable.release(permitId);
    }
}
```

### 7.2 分布式锁注解

```java
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface DistributedLock {
    
    /**
     * 锁的key，支持SpEL表达式
     */
    String key();
    
    /**
     * 等待锁的时间，默认5秒
     */
    long waitTime() default 5;
    
    /**
     * 持有锁的时间，默认30秒
     */
    long leaseTime() default 30;
    
    /**
     * 时间单位，默认秒
     */
    TimeUnit timeUnit() default TimeUnit.SECONDS;
    
    /**
     * 锁失败时的异常信息
     */
    String message() default "获取分布式锁失败";
}
```

### 7.3 分布式锁AOP

```java
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.expression.EvaluationContext;
import org.springframework.expression.Expression;
import org.springframework.expression.ExpressionParser;
import org.springframework.expression.spel.standard.SpelExpressionParser;
import org.springframework.expression.spel.support.StandardEvaluationContext;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class DistributedLockAspect {
    
    @Autowired
    private RedissonUtil redissonUtil;
    
    private final ExpressionParser parser = new SpelExpressionParser();
    
    @Around("@annotation(distributedLock)")
    public Object around(ProceedingJoinPoint joinPoint, DistributedLock distributedLock) throws Throwable {
        String lockKey = parseKey(distributedLock.key(), joinPoint);
        
        return redissonUtil.executeWithLock(
            lockKey,
            () -> {
                try {
                    return joinPoint.proceed();
                } catch (Throwable e) {
                    throw new RuntimeException(e);
                }
            },
            distributedLock.waitTime(),
            distributedLock.leaseTime(),
            distributedLock.timeUnit()
        );
    }
    
    private String parseKey(String key, ProceedingJoinPoint joinPoint) {
        try {
            Expression expression = parser.parseExpression(key);
            EvaluationContext context = new StandardEvaluationContext();
            
            // 设置方法参数
            String[] paramNames = getParameterNames(joinPoint);
            Object[] args = joinPoint.getArgs();
            
            for (int i = 0; i < paramNames.length; i++) {
                context.setVariable(paramNames[i], args[i]);
            }
            
            return expression.getValue(context, String.class);
        } catch (Exception e) {
            return key;
        }
    }
    
    private String[] getParameterNames(ProceedingJoinPoint joinPoint) {
        // 这里简化处理，实际项目中可以使用反射或其他方式获取参数名
        return new String[joinPoint.getArgs().length];
    }
}
```

## 8. 最佳实践

### 8.1 锁的命名规范

```java
public class LockNamingConvention {
    
    // 业务锁：业务:操作:资源ID
    public static final String ORDER_LOCK = "order:process:{orderId}";
    public static final String USER_LOCK = "user:update:{userId}";
    public static final String INVENTORY_LOCK = "inventory:deduct:{productId}";
    
    // 系统锁：system:操作:资源
    public static final String SYSTEM_MAINTENANCE = "system:maintenance";
    public static final String CACHE_REFRESH = "cache:refresh:{cacheKey}";
    
    // 限流锁：rate:业务:用户ID
    public static final String RATE_LIMIT = "rate:api:{userId}";
}
```

### 8.2 异常处理

```java
public class LockExceptionHandler {
    
    public static <T> T executeWithExceptionHandling(String lockKey, Supplier<T> task) {
        try {
            return task.get();
        } catch (Exception e) {
            // 记录日志
            log.error("执行任务失败，lockKey: {}", lockKey, e);
            
            // 根据异常类型决定是否重试
            if (isRetryableException(e)) {
                return retry(lockKey, task);
            }
            
            throw new RuntimeException("任务执行失败", e);
        }
    }
    
    private static boolean isRetryableException(Exception e) {
        // 判断是否为可重试的异常
        return e instanceof TimeoutException || 
               e instanceof InterruptedException ||
               e instanceof RedisConnectionException;
    }
    
    private static <T> T retry(String lockKey, Supplier<T> task) {
        // 重试逻辑
        int maxRetries = 3;
        int retryCount = 0;
        
        while (retryCount < maxRetries) {
            try {
                Thread.sleep(1000 * (retryCount + 1)); // 指数退避
                return task.get();
            } catch (Exception e) {
                retryCount++;
                if (retryCount >= maxRetries) {
                    throw new RuntimeException("重试次数已达上限", e);
                }
            }
        }
        
        throw new RuntimeException("重试失败");
    }
}
```

### 8.3 监控和指标

```java
@Component
public class RedissonMetrics {
    
    private final MeterRegistry meterRegistry;
    private final RedissonClient redissonClient;
    
    public RedissonMetrics(MeterRegistry meterRegistry, RedissonClient redissonClient) {
        this.meterRegistry = meterRegistry;
        this.redissonClient = redissonClient;
    }
    
    @Scheduled(fixedRate = 60000) // 每分钟执行一次
    public void recordMetrics() {
        // 记录连接池指标
        Timer.Sample sample = Timer.start(meterRegistry);
        
        try {
            // 获取Redis信息
            // 这里可以添加更多指标收集逻辑
        } finally {
            sample.stop(Timer.builder("redisson.operation.duration")
                    .tag("operation", "metrics_collection")
                    .register(meterRegistry));
        }
    }
    
    public void recordLockOperation(String operation, long duration, boolean success) {
        Timer.builder("redisson.lock.operation")
                .tag("operation", operation)
                .tag("success", String.valueOf(success))
                .register(meterRegistry)
                .record(duration, TimeUnit.MILLISECONDS);
    }
}
```

## 9. 性能优化

### 9.1 连接池配置

```java
@Configuration
public class RedissonConfig {
    
    @Bean
    public RedissonClient redissonClient() {
        Config config = new Config();
        config.useSingleServer()
                .setAddress("redis://localhost:6379")
                .setConnectionPoolSize(64)           // 连接池大小
                .setConnectionMinimumIdleSize(10)    // 最小空闲连接数
                .setIdleConnectionTimeout(10000)     // 空闲连接超时时间
                .setConnectTimeout(10000)            // 连接超时时间
                .setTimeout(3000)                    // 命令超时时间
                .setRetryAttempts(3)                 // 重试次数
                .setRetryInterval(1500)              // 重试间隔
                .setKeepAlive(true)                  // 保持连接活跃
                .setTcpNoDelay(true);                // TCP_NODELAY
        
        return Redisson.create(config);
    }
}
```

### 9.2 批量操作优化

```java
public class BatchOperationExample {
    
    private final RedissonClient redissonClient;
    
    public BatchOperationExample(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void batchOperations() {
        // 使用管道批量操作
        RBatch batch = redissonClient.createBatch();
        
        for (int i = 0; i < 1000; i++) {
            batch.getAtomicLong("counter:" + i).incrementAndGet();
        }
        
        // 执行批量操作
        BatchResult<?> result = batch.execute();
        
        // 处理结果
        List<?> responses = result.getResponses();
        System.out.println("批量操作完成，处理数量: " + responses.size());
    }
    
    // 异步批量操作
    public void asyncBatchOperations() {
        RBatch batch = redissonClient.createBatch();
        
        for (int i = 0; i < 1000; i++) {
            batch.getAtomicLong("counter:" + i).incrementAndGetAsync();
        }
        
        // 异步执行
        batch.executeAsync().thenAccept(result -> {
            System.out.println("异步批量操作完成");
        });
    }
}
```

## 10. 故障排查

### 10.1 常见问题

1. **锁无法释放**
   - 检查锁的持有时间是否合理
   - 确保finally块中调用unlock()
   - 检查是否有死锁情况

2. **性能问题**
   - 检查连接池配置
   - 使用批量操作减少网络往返
   - 合理设置锁的等待时间和持有时间

3. **连接问题**
   - 检查网络连接
   - 验证Redis配置
   - 检查防火墙设置

### 10.2 调试工具

```java
@Component
public class RedissonDebugger {
    
    private final RedissonClient redissonClient;
    
    public RedissonDebugger(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }
    
    public void debugLock(String lockKey) {
        RLock lock = redissonClient.getLock(lockKey);
        
        System.out.println("锁名称: " + lock.getName());
        System.out.println("是否被锁定: " + lock.isLocked());
        System.out.println("是否被当前线程持有: " + lock.isHeldByCurrentThread());
        System.out.println("等待队列长度: " + lock.getQueueLength());
        System.out.println("持有锁的线程ID: " + lock.getHoldCount());
    }
    
    public void debugConnection() {
        // 检查连接状态
        try {
            redissonClient.getKeys().count();
            System.out.println("Redis连接正常");
        } catch (Exception e) {
            System.out.println("Redis连接异常: " + e.getMessage());
        }
    }
}
```

## 总结

Redisson是一个功能强大的Redis客户端，提供了丰富的分布式功能。通过合理使用分布式锁、集合、服务等特性，可以构建高性能、高可用的分布式应用。

关键要点：
1. **合理使用锁**：避免锁粒度过大或过小
2. **异常处理**：确保锁的正确释放和异常处理
3. **性能优化**：使用连接池、批量操作等提升性能
4. **监控告警**：建立完善的监控体系
5. **最佳实践**：遵循命名规范和设计原则

通过本文的学习，你应该能够熟练使用Redisson的各种功能，并在实际项目中合理应用。
