---
title: 限流_Ratelimit
main_color: "#21bdbdff"  
categories: 流量控制
tags:
  - 并发    
cover: https://free.picui.cn/free/2026/03/28/69c74e1f15517.png
---


GUava RateLimiter 详解

### 一、为什么需要限流
- **保护服务稳定性**: 在突发流量或下游变慢时，限制进入系统的并发/请求速率，避免雪崩。
- **隔离关键资源**: 例如数据库、第三方接口，限定单位时间内的调用量。
- **平滑突发**: 将突发请求摊平到更长时间窗口内，提升整体吞吐的可预期性。

### 二、RateLimiter 底层原理（从源码与算法角度）
RateLimiter 是基于“令牌桶”思想的平滑限流器，核心实现类为 `SmoothRateLimiter` 及其两个子类：
- **SmoothBursty**: 允许一定的突发（burst），多余令牌会“存起来”，默认最多存储 `maxPermits = 1.0` 秒产出的令牌数。
- **SmoothWarmingUp**: 具有预热（warm-up）阶段，刚启动时“冷”，会逐步放宽速率直到稳定速率。

核心成员与概念（简化）：
- **storedPermits**: 当前桶内已累计的可用令牌数（可用于突发）。
- **maxPermits**: 桶能存的令牌上限（由速率与模式决定）。
- **stableIntervalMicros**: 稳定速率下的每个令牌对应的时间间隔（微秒），`= 1_000_000 / permitsPerSecond`。
- **nextFreeTicketMicros**: 下一个令牌可被“预约”的最早时间点（时间轴思想）。
- **resync(now)**: 懒更新，基于当前时间 `now` 补发令牌，更新 `storedPermits` 与 `nextFreeTicketMicros`。

工作流程（获取 n 个令牌时）：
1) `resync(now)`：根据 `now - nextFreeTicketMicros` 计算新增令牌数，累积到 `storedPermits`，并将 `nextFreeTicketMicros` 至少推进到 `now`。
2) 优先消耗 `storedPermits`（免费/较低等待成本），不足部分需要“预约未来令牌”，将 `nextFreeTicketMicros` 前移 `requiredPermits * stableIntervalMicros`。
3) 返回需要等待的时间 `waitMicros = max(0, nextFreeTicketMicros - now)`（`acquire()` 会真实睡眠，`tryAcquire()`可选择不等待）。

SmoothBursty 与 SmoothWarmingUp 区别：
- Bursty：简单，支持瞬时突发，空闲期会积累 `storedPermits`。
- WarmingUp：在一段预热时间内，令牌“更贵”，同样的请求会分配更长等待时间，使系统逐步达稳态，避免冷启动流量尖峰。

与常见算法对比：
- **令牌桶**：按速率产出令牌，允许突发（取决于桶容量）。RateLimiter 属此类。
- **漏桶**：固定速率出水，输出更平滑，但对突发吸收能力较弱。

线程安全与公平性：
- 内部通过 `synchronized` 保证线程安全；
- 非严格公平（先到不一定先得），但在高并发下表现稳定可控。

### 三、关键 API 说明
- `RateLimiter.create(double permitsPerSecond)`：创建突发型限流（SmoothBursty）。
- `RateLimiter.create(double permitsPerSecond, long warmup, TimeUnit unit)`：创建预热型限流（SmoothWarmingUp）。
- `double acquire()` / `double acquire(int permits)`：阻塞等待获取令牌，返回实际等待的秒数。
- `boolean tryAcquire()` / `tryAcquire(int permits, timeout, unit)`：在不超过超时时间内尝试获取，超时立即返回 false。
- `void setRate(double permitsPerSecond)`：动态调整速率，内部会重新计算参数并平滑过渡。

使用建议：
- 将 `RateLimiter` 作为单例复用（是重量级含状态对象）。
- 通过 `tryAcquire(timeout)` 优雅丢弃或降级，避免线程长时间阻塞。
- 根据场景选择 `Bursty` 或 `WarmingUp`。对冷启动敏感、下游“热机”需要时间的链路优先选用预热型。

### 四、常见坑位
- 单节点生效：Guava 仅在单 JVM 实例内限流，分布式需结合网关/Redis/Envoy 等集中式限流。
- 单位与精度：`acquire` 返回的是秒（double），注意度量与日志打印单位。
- 大粒度与小粒度：全局限流简单，但可能“误伤”。细粒度（接口、IP、用户、租户、方法级）更精准但更复杂。
- 令牌消耗粒度：一个请求可能消耗多个令牌（例如重量级操作），别一刀切全是 1。

### 五、与 Spring Boot 结合的常用模式

#### 5.1 依赖
Maven：
```xml
<dependency>
  <groupId>com.google.guava</groupId>
  <artifactId>guava</artifactId>
  <version>33.2.1-jre</version>
</dependency>
```

Gradle：
```groovy
implementation 'com.google.guava:guava:33.2.1-jre'
```

#### 5.2 全局 Filter 级限流（简单粗暴，全站 QPS）
```java
// GlobalRateLimitFilter.java
import com.google.common.util.concurrent.RateLimiter;
import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import java.io.IOException;

@Component
public class GlobalRateLimitFilter implements Filter {
  private final RateLimiter rateLimiter = RateLimiter.create(200.0); // 全站 200 QPS

  @Override
  public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
      throws IOException, ServletException {
    if (!rateLimiter.tryAcquire()) {
      HttpServletResponse resp = (HttpServletResponse) response;
      resp.setStatus(429);
      resp.setContentType("application/json;charset=UTF-8");
      resp.getWriter().write("{\"code\":429,\"msg\":\"Too Many Requests\"}");
      return;
    }
    chain.doFilter(request, response);
  }
}
```

适用：全站简单限流、临时保护；不适用：差异化策略。

#### 5.3 HandlerInterceptor 按接口限流（可配置每个路径的 QPS）
```java
// PathRateLimitInterceptor.java
import com.google.common.util.concurrent.RateLimiter;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class PathRateLimitInterceptor implements HandlerInterceptor {
  private final Map<String, RateLimiter> pathLimiter = new ConcurrentHashMap<>();

  public PathRateLimitInterceptor() {
    pathLimiter.put("/api/pay", RateLimiter.create(50));
    pathLimiter.put("/api/search", RateLimiter.create(300));
  }

  @Override
  public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
    String path = request.getRequestURI();
    RateLimiter limiter = pathLimiter.get(path);
    if (limiter == null) return true;
    if (!limiter.tryAcquire()) {
      response.setStatus(429);
      response.setContentType("application/json;charset=UTF-8");
      response.getWriter().write("{\"code\":429,\"msg\":\"Too Many Requests\"}");
      return false;
    }
    return true;
  }
}

// WebMvcConfig.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
  @Autowired private PathRateLimitInterceptor interceptor;
  @Override
  public void addInterceptors(InterceptorRegistry registry) {
    registry.addInterceptor(interceptor).addPathPatterns("/**");
  }
}
```

可扩展：将路径与速率放到配置文件或 Nacos，启动时加载、运行时热更新。

#### 5.4 注解 + AOP（方法级、可按维度限流）
定义注解：
```java
// RateLimit.java
import java.lang.annotation.*;

@Target({ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Documented
public @interface RateLimit {
  double permitsPerSecond();
  long timeout() default 0; // 超时时间，默认不等待
  java.util.concurrent.TimeUnit timeUnit() default java.util.concurrent.TimeUnit.MILLISECONDS;
  String key() default ""; // 维度键（SPEL 表达式或占位）
  boolean warmup() default false; // 是否预热
  long warmupPeriod() default 1_000; // 预热时长（ms）
}
```

切面实现（支持按 key 维度缓存多个限流器）：
```java
// RateLimitAspect.java
import com.google.common.util.concurrent.RateLimiter;
import jakarta.servlet.http.HttpServletRequest;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.lang.reflect.Method;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

@Aspect
@Component
public class RateLimitAspect {
  private final Map<String, RateLimiter> limiterCache = new ConcurrentHashMap<>();

  @Around("@annotation(RateLimit)")
  public Object around(ProceedingJoinPoint pjp) throws Throwable {
    Method method = ((MethodSignature) pjp.getSignature()).getMethod();
    RateLimit anno = method.getAnnotation(RateLimit.class);

    String baseKey = method.getDeclaringClass().getName() + ":" + method.getName();
    String dimensionKey = resolveKey(anno.key());
    String finalKey = dimensionKey.isEmpty() ? baseKey : baseKey + ":" + dimensionKey;

    RateLimiter limiter = limiterCache.computeIfAbsent(finalKey, k ->
        anno.warmup() ? RateLimiter.create(anno.permitsPerSecond(), anno.warmupPeriod(), TimeUnit.MILLISECONDS)
                      : RateLimiter.create(anno.permitsPerSecond())
    );

    boolean ok = anno.timeout() > 0
        ? limiter.tryAcquire(1, anno.timeout(), anno.timeUnit())
        : limiter.tryAcquire();

    if (!ok) {
      throw new TooManyRequestsException("Too Many Requests");
    }

    return pjp.proceed();
  }

  private String resolveKey(String keyExpr) {
    if (keyExpr == null || keyExpr.isEmpty()) return "";
    ServletRequestAttributes attrs = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
    if (attrs == null) return "";
    HttpServletRequest req = attrs.getRequest();
    switch (keyExpr) {
      case "ip":
        String ip = req.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) ip = req.getRemoteAddr();
        return ip == null ? "" : ip.split(",")[0];
      case "user":
        Object uid = req.getAttribute("uid"); // 示例：登录拦截器写入
        return uid == null ? "guest" : String.valueOf(uid);
      default:
        return keyExpr; // 也可以扩展为 SpEL 解析
    }
  }

  public static class TooManyRequestsException extends RuntimeException {
    public TooManyRequestsException(String msg) { super(msg); }
  }
}
```

在 Controller 中使用：
```java
// DemoController.java
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class DemoController {
  // 接口级 100 QPS，默认不等待
  @RateLimit(permitsPerSecond = 100)
  @GetMapping("/api/search")
  public String search() { return "ok"; }

  // 预热限流：冷启动时放缓至 20 QPS，1s 预热至稳定
  @RateLimit(permitsPerSecond = 20, warmup = true, warmupPeriod = 1000)
  @GetMapping("/api/cold")
  public String cold() { return "ok"; }

  // 按 IP 限流：每个 IP 5 QPS，最多等待 50ms
  @RateLimit(permitsPerSecond = 5, timeout = 50, timeUnit = java.util.concurrent.TimeUnit.MILLISECONDS, key = "ip")
  @GetMapping("/api/by-ip")
  public String byIp() { return "ok"; }

  // 按用户限流：每个用户 10 QPS
  @RateLimit(permitsPerSecond = 10, key = "user")
  @GetMapping("/api/by-user")
  public String byUser() { return "ok"; }
}
```

异常与统一返回处理：
```java
// GlobalExceptionHandler.java
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {
  @ExceptionHandler(RateLimitAspect.TooManyRequestsException.class)
  public Object tooMany(Exception e) {
    return java.util.Map.of("code", 429, "msg", e.getMessage());
  }
}
```

#### 5.5 按权重/令牌数限流（一个请求消耗多个令牌）
```java
RateLimiter limiter = RateLimiter.create(100); // 100 QPS
boolean ok = limiter.tryAcquire(5, 20, java.util.concurrent.TimeUnit.MILLISECONDS); // 需要 5 个令牌
```

适用：导出、批处理、复杂计算等重量级操作。

#### 5.6 异步任务/线程池前置限流
```java
RateLimiter limiter = RateLimiter.create(50);
executor.submit(() -> {
  if (!limiter.tryAcquire(1, 10, java.util.concurrent.TimeUnit.MILLISECONDS)) return; // 丢弃或入延迟队列
  // 执行业务
});
```

### 六、分布式与生产实践建议
- **分布式一致性**：Guava 仅本地生效；多实例需放到 API 网关、使用 Redis + Lua/滑动窗口、或使用支持全局限流的服务（Nginx/Envoy/Service Mesh）。
- **动态配置**：速率热更新可通过配置中心推送，监听后调用 `setRate` 或重建对应的 `RateLimiter`。
- **监控与告警**：暴露获取失败数、等待耗时分布、丢弃量，便于调参。
- **压测调参**：在预期峰值下进行压测，权衡 429 率与业务可接受性；关键链路考虑预热型。

### 七、小结
RateLimiter 通过时间轴“预约”和懒补发令牌，实现了高效、平滑的令牌桶限流，支持突发与预热两种模式。在 Spring Boot 中可灵活以 Filter、Interceptor、注解+AOP 等方式落地，并可扩展到按接口、IP、用户等多维度限流。生产上需结合分布式方案、动态调参与完善的监控体系。
