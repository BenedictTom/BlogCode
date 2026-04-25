---
title: Sentinel
main_color: "#2bb2b6ff"
categories: 微服务
tags:
  - Spring Cloud
cover: https://free.picui.cn/free/2026/03/28/69c74fc120952.webp
---

# Sentinel全面指南

## 1. 什么是Sentinel

Sentinel是阿里巴巴开源的面向分布式服务架构的流量控制组件，以流量为切入点，从流量控制、熔断降级、系统负载保护等多个维度来保护服务的稳定性。

### 1.1 主要特性
- **丰富的应用场景**：秒杀、双11大促、集群限流、实时熔断等
- **完备的实时监控**：提供实时的监控功能，可以看到接入应用的单台机器秒级数据
- **广泛的开源生态**：支持Spring Cloud、Dubbo、gRPC等框架
- **完善的SPI扩展点**：提供简单易用、完善的SPI扩展接口

### 1.2 核心概念
- **资源（Resource）**：可以是Java应用程序中的任何内容，例如，由应用程序提供的服务，或由应用程序调用的其它服务
- **规则（Rule）**：围绕资源的实时状态设定的规则，可以包括流量控制规则、熔断降级规则、系统保护规则
- **指标（Metric）**：Sentinel内部提供了一些监控指标的统计信息

## 2. 快速开始

### 2.1 Maven依赖

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-sentinel</artifactId>
    <version>2021.0.5.0</version>
</dependency>
```

### 2.2 配置文件

```yaml
spring:
  cloud:
    sentinel:
      transport:
        dashboard: localhost:8080
        port: 8719
      datasource:
        ds:
          nacos:
            server-addr: localhost:8848
            dataId: sentinel-rules
            groupId: DEFAULT_GROUP
            rule-type: flow
```

### 2.3 启动类配置

```java
@SpringBootApplication
@EnableDiscoveryClient
public class SentinelApplication {
    public static void main(String[] args) {
        SpringApplication.run(SentinelApplication.class, args);
    }
}
```

## 3. 流量控制

### 3.1 基于QPS的限流

```java
@RestController
@RequestMapping("/api")
public class FlowController {
    
    @GetMapping("/test")
    @SentinelResource(value = "test", blockHandler = "blockHandlerForTest")
    public String test() {
        return "Hello Sentinel!";
    }
    
    // 限流处理函数
    public String blockHandlerForTest(BlockException ex) {
        return "服务繁忙，请稍后重试";
    }
}
```

### 3.2 基于线程数的限流

```java
@RestController
@RequestMapping("/api")
public class ThreadController {
    
    @GetMapping("/thread")
    @SentinelResource(value = "thread", 
                     blockHandler = "blockHandlerForThread",
                     fallback = "fallbackForThread")
    public String thread() {    
        // 模拟耗时操作
        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return "Thread operation completed";
    }
    
    public String blockHandlerForThread(BlockException ex) {
        return "线程池已满，请稍后重试";
    }
    
    public String fallbackForThread(Throwable e) {
        return "服务异常，降级处理";
    }
}
```

### 3.3 自定义限流规则

```java
@Component
public class SentinelRuleConfig {
    
    @PostConstruct
    public void initFlowRules() {
        List<FlowRule> rules = new ArrayList<>();
        
        // 创建流量控制规则
        FlowRule rule = new FlowRule();
        rule.setResource("test");
        rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        rule.setCount(10); // 每秒允许10个请求
        
        // 设置限流策略
        rule.setControlBehavior(RuleConstant.CONTROL_BEHAVIOR_WARM_UP);
        rule.setWarmUpPeriodSec(10); // 预热时间10秒
        
        rules.add(rule);
        FlowRuleManager.loadRules(rules);
    }
}
```

## 4. 熔断降级

### 4.1 异常比例熔断

```java
@RestController
@RequestMapping("/api")
public class CircuitBreakerController {
    
    @GetMapping("/circuit")
    @SentinelResource(value = "circuit", 
                     fallback = "fallbackForCircuit",
                     blockHandler = "blockHandlerForCircuit")
    public String circuit(@RequestParam(defaultValue = "0") int error) {
        if (error == 1) {
            throw new RuntimeException("模拟异常");
        }
        return "Circuit breaker test success";
    }
    
    public String fallbackForCircuit(int error, Throwable e) {
        return "服务降级，异常信息：" + e.getMessage();
    }
    
    public String blockHandlerForCircuit(int error, BlockException ex) {
        return "服务熔断，请稍后重试";
    }
}
```

### 4.2 自定义熔断规则

```java
@Component
public class CircuitBreakerRuleConfig {
    
    @PostConstruct
    public void initDegradeRules() {
        List<DegradeRule> rules = new ArrayList<>();
        
        // 创建熔断降级规则
        DegradeRule rule = new DegradeRule();
        rule.setResource("circuit");
        rule.setGrade(RuleConstant.DEGRADE_GRADE_EXCEPTION_RATIO);
        rule.setCount(0.5); // 异常比例阈值50%
        rule.setTimeWindow(10); // 熔断时间窗口10秒
        rule.setMinRequestAmount(5); // 最小请求数5个
        
        rules.add(rule);
        DegradeRuleManager.loadRules(rules);
    }
}
```

### 4.3 慢调用熔断

```java
@RestController
@RequestMapping("/api")
public class SlowCallController {
    
    @GetMapping("/slow")
    @SentinelResource(value = "slow", 
                     fallback = "fallbackForSlow",
                     blockHandler = "blockHandlerForSlow")
    public String slow(@RequestParam(defaultValue = "100") long delay) {
        try {
            Thread.sleep(delay);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return "Slow call completed in " + delay + "ms";
    }
    
    public String fallbackForSlow(long delay, Throwable e) {
        return "慢调用降级处理";
    }
    
    public String blockHandlerForSlow(long delay, BlockException ex) {
        return "慢调用熔断处理";
    }
}
```

## 5. 系统保护

### 5.1 系统规则配置

```java
@Component
public class SystemRuleConfig {
    
    @PostConstruct
    public void initSystemRules() {
        List<SystemRule> rules = new ArrayList<>();
        
        // 系统负载保护规则
        SystemRule rule = new SystemRule();
        rule.setHighestSystemLoad(0.8); // 系统负载阈值0.8
        rule.setAvgRt(1000); // 平均响应时间阈值1000ms
        rule.setQps(100); // 系统QPS阈值100
        rule.setMaxThread(50); // 最大线程数50
        
        rules.add(rule);
        SystemRuleManager.loadRules(rules);
    }
}
```

### 5.2 自适应系统保护

```java
@RestController
@RequestMapping("/api")
public class SystemProtectionController {
    
    @GetMapping("/system")
    @SentinelResource(value = "system", 
                     blockHandler = "blockHandlerForSystem")
    public String system() {
        // 模拟系统资源消耗
        for (int i = 0; i < 1000000; i++) {
            Math.sqrt(i);
        }
        return "System protection test completed";
    }
    
    public String blockHandlerForSystem(BlockException ex) {
        return "系统保护触发，请稍后重试";
    }
}
```

## 6. 热点参数限流

### 6.1 热点参数限流实现

```java
@RestController
@RequestMapping("/api")
public class HotParamController {
    
    @GetMapping("/hot")
    @SentinelResource(value = "hot", 
                     blockHandler = "blockHandlerForHot",
                     fallback = "fallbackForHot")
    public String hot(@RequestParam String userId, 
                     @RequestParam String itemId) {
        return "User: " + userId + " bought item: " + itemId;
    }
    
    public String blockHandlerForHot(String userId, String itemId, 
                                   BlockException ex) {
        return "热点参数限流，用户ID: " + userId + ", 商品ID: " + itemId;
    }
    
    public String fallbackForHot(String userId, String itemId, Throwable e) {
        return "热点参数降级处理";
    }
}
```

### 6.2 热点参数规则配置

```java
@Component
public class HotParamRuleConfig {
    
    @PostConstruct
    public void initParamFlowRules() {
        List<ParamFlowRule> rules = new ArrayList<>();
        
        // 创建热点参数限流规则
        ParamFlowRule rule = new ParamFlowRule("hot");
        rule.setParamIdx(0); // 第一个参数（userId）
        rule.setGrade(RuleConstant.FLOW_GRADE_QPS);
        rule.setCount(5); // 每个userId每秒最多5个请求
        
        // 设置特殊参数值
        Map<Object, Integer> paramCount = new HashMap<>();
        paramCount.put("VIP001", 10); // VIP用户每秒10个请求
        paramCount.put("VIP002", 15); // 超级VIP用户每秒15个请求
        rule.setParamFlowItemList(paramCount.entrySet().stream()
            .map(entry -> new ParamFlowItem(entry.getKey(), entry.getValue()))
            .collect(Collectors.toList()));
        
        rules.add(rule);
        ParamFlowRuleManager.loadRules(rules);
    }
}
```

## 7. 集群流控

### 7.1 集群限流配置

```yaml
spring:
  cloud:
    sentinel:
      transport:
        dashboard: localhost:8080
        port: 8719
      datasource:
        ds:
          nacos:
            server-addr: localhost:8848
            dataId: sentinel-cluster-rules
            groupId: DEFAULT_GROUP
            rule-type: cluster-flow
```

### 7.2 集群限流实现

```java
@RestController
@RequestMapping("/api")
public class ClusterFlowController {
    
    @GetMapping("/cluster")
    @SentinelResource(value = "cluster", 
                     blockHandler = "blockHandlerForCluster")
    public String cluster() {
        return "Cluster flow control test";
    }
    
    public String blockHandlerForCluster(BlockException ex) {
        return "集群限流触发";
    }
}
```

## 8. 实时监控

### 8.1 自定义监控指标

```java
@Component
public class CustomMetrics {
    
    private final Counter requestCounter;
    private final Timer responseTimer;
    
    public CustomMetrics(MeterRegistry meterRegistry) {
        this.requestCounter = Counter.builder("sentinel.requests")
            .description("Sentinel请求计数")
            .register(meterRegistry);
        
        this.responseTimer = Timer.builder("sentinel.response.time")
            .description("Sentinel响应时间")
            .register(meterRegistry);
    }
    
    public void incrementRequest() {
        requestCounter.increment();
    }
    
    public void recordResponseTime(long timeMs) {
        responseTimer.record(timeMs, TimeUnit.MILLISECONDS);
    }
}
```

### 8.2 监控集成

```java
@RestController
@RequestMapping("/api")
public class MonitorController {
    
    private final CustomMetrics metrics;
    
    public MonitorController(CustomMetrics metrics) {
        this.metrics = metrics;
    }
    
    @GetMapping("/monitor")
    @SentinelResource(value = "monitor", 
                     blockHandler = "blockHandlerForMonitor")
    public String monitor() {
        long startTime = System.currentTimeMillis();
        
        try {
            // 模拟业务逻辑
            Thread.sleep(100);
            metrics.incrementRequest();
            return "Monitor test completed";
        } finally {
            long responseTime = System.currentTimeMillis() - startTime;
            metrics.recordResponseTime(responseTime);
        }
    }
    
    public String blockHandlerForMonitor(BlockException ex) {
        return "监控接口限流";
    }
}
```

## 9. 最佳实践

### 9.1 资源定义规范

```java
public class SentinelResourceConstants {
    // 资源名称常量
    public static final String USER_SERVICE = "user-service";
    public static final String ORDER_SERVICE = "order-service";
    public static final String PAYMENT_SERVICE = "payment-service";
    
    // 业务场景常量
    public static final String LOGIN = "login";
    public static final String REGISTER = "register";
    public static final String PAY = "pay";
}
```

### 9.2 统一异常处理

```java
@ControllerAdvice
public class SentinelExceptionHandler {
    
    @ExceptionHandler(BlockException.class)
    @ResponseBody
    public ResponseEntity<String> handleBlockException(BlockException e) {
        String message = "服务限流：" + e.getRule().getResource();
        return ResponseEntity.status(HttpStatus.TOO_MANY_REQUESTS)
            .body(message);
    }
    
    @ExceptionHandler(Throwable.class)
    @ResponseBody
    public ResponseEntity<String> handleGenericException(Throwable e) {
        String message = "服务异常：" + e.getMessage();
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(message);
    }
}
```

### 9.3 配置管理

```java
@Configuration
@ConfigurationProperties(prefix = "sentinel")
@Data
public class SentinelProperties {
    
    private String dashboard;
    private int port;
    private String datasource;
    private Map<String, Object> rules = new HashMap<>();
    
    @PostConstruct
    public void init() {
        // 初始化配置
        System.setProperty("csp.sentinel.dashboard.server", dashboard);
        System.setProperty("csp.sentinel.api.port", String.valueOf(port));
    }
}
```

## 10. 常见问题与解决方案

### 10.1 限流不生效
- 检查资源名称是否正确
- 确认规则配置是否正确加载
- 验证限流阈值设置是否合理

### 10.2 熔断不触发
- 检查异常比例或异常数阈值设置
- 确认时间窗口配置
- 验证最小请求数设置

### 10.3 性能优化
- 合理设置限流阈值
- 使用异步处理提高吞吐量
- 配置合适的线程池大小

## 11. 总结

Sentinel作为阿里巴巴开源的流量控制组件，提供了完善的流量控制、熔断降级、系统保护等功能。通过合理配置和使用，可以有效保护微服务架构的稳定性，提高系统的可用性和可靠性。

### 11.1 核心优势
- **简单易用**：提供丰富的注解和配置方式
- **功能完善**：支持多种限流策略和熔断模式
- **实时监控**：提供详细的监控指标和可视化界面
- **扩展性强**：支持自定义规则和SPI扩展

### 11.2 适用场景
- 微服务架构的流量控制
- 高并发系统的保护
- 秒杀、大促等特殊场景
- 系统稳定性保障

通过本指南的学习，你应该能够熟练使用Sentinel来保护你的微服务应用，构建更加稳定可靠的分布式系统。