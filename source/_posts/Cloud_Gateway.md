---
title: Gateway
main_color: "#80a340ff"
categories: 微服务
tags:
  - Spring Cloud
cover: https://free.picui.cn/free/2026/03/28/69c74d6ccd001.png
---

# Spring Cloud Gateway 微服务网关详解

## 1. 什么是API网关？

API网关是微服务架构中的一个重要组件，它作为所有客户端请求的统一入口点，负责路由、过滤、负载均衡、安全控制等功能。Spring Cloud Gateway是Spring Cloud生态中推荐的网关解决方案。

### 1.1 网关的主要功能

- **路由转发**：将请求路由到相应的微服务
- **负载均衡**：在多个服务实例间分发请求
- **安全控制**：认证、授权、限流等
- **监控统计**：请求日志、性能指标等
- **协议转换**：支持HTTP、WebSocket等协议

## 2. Spring Cloud Gateway架构

```
Client → Gateway → Route → Filter → Microservice
```

### 2.1 核心组件

- **Route（路由）**：网关的基本构建块，包含ID、目标URI、断言和过滤器
- **Predicate（断言）**：匹配HTTP请求的条件
- **Filter（过滤器）**：处理请求和响应的逻辑

## 3. 项目依赖配置

### 3.1 Maven依赖

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-gateway</artifactId>
</dependency>

<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-netflix-eureka-client</artifactId>
</dependency>

<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

### 3.2 Gradle依赖

```gradle
implementation 'org.springframework.cloud:spring-cloud-starter-gateway'
implementation 'org.springframework.cloud:spring-cloud-starter-netflix-eureka-client'
implementation 'org.springframework.boot:spring-boot-starter-actuator'
```

## 4. 基础配置示例

### 4.1 application.yml配置

```yaml
server:
  port: 8080

spring:
  application:
    name: gateway-service
  cloud:
    gateway:
      discovery:
        locator:
          enabled: true
          lower-case-service-id: true
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/users/**
          filters:
            - StripPrefix=1
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 10
                redis-rate-limiter.burstCapacity: 20
        - id: order-service
          uri: lb://order-service
          predicates:
            - Path=/api/orders/**
          filters:
            - StripPrefix=1
        - id: product-service
          uri: lb://product-service
          predicates:
            - Path=/api/products/**
          filters:
            - StripPrefix=1

eureka:
  client:
    service-url:
      defaultZone: http://localhost:8761/eureka/
  instance:
    prefer-ip-address: true

management:
  endpoints:
    web:
      exposure:
        include: "*"
  endpoint:
    health:
      show-details: always
```

### 4.2 主启动类

```java
@SpringBootApplication
@EnableDiscoveryClient
public class GatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }
}
```

## 5. 路由配置详解

### 5.1 基于路径的路由

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: path_route
          uri: http://localhost:8081
          predicates:
            - Path=/api/**
```

### 5.2 基于时间的路由

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: time_route
          uri: http://localhost:8081
          predicates:
            - After=2024-01-01T00:00:00+08:00[Asia/Shanghai]
            - Before=2024-12-31T23:59:59+08:00[Asia/Shanghai]
```

### 5.3 基于请求头的路由

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: header_route
          uri: http://localhost:8081
          predicates:
            - Header=X-Request-Id, \d+
```

### 5.4 基于查询参数的路由

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: query_route
          uri: http://localhost:8081
          predicates:
            - Query=name, test
```

## 6. 过滤器配置

### 6.1 内置过滤器

#### 6.1.1 请求过滤器

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: filter_route
          uri: http://localhost:8081
          predicates:
            - Path=/api/**
          filters:
            - AddRequestHeader=X-Request-Id, 12345
            - AddRequestParameter=param, value
            - StripPrefix=1
            - SetPath=/api/{segment}
```

#### 6.1.2 响应过滤器

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: response_filter_route
          uri: http://localhost:8081
          predicates:
            - Path=/api/**
          filters:
            - AddResponseHeader=X-Response-Id, 67890
            - SetStatus=200
```

### 6.2 自定义过滤器

#### 6.2.1 全局过滤器

```java
@Component
public class GlobalAuthFilter implements GlobalFilter, Ordered {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String token = request.getHeaders().getFirst("Authorization");
        
        if (token == null || !token.startsWith("Bearer ")) {
            exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
            return exchange.getResponse().setComplete();
        }
        
        // 验证token逻辑
        if (!isValidToken(token)) {
            exchange.getResponse().setStatusCode(HttpStatus.FORBIDDEN);
            return exchange.getResponse().setComplete();
        }
        
        return chain.filter(exchange);
    }
    
    @Override
    public int getOrder() {
        return -100; // 高优先级
    }
    
    private boolean isValidToken(String token) {
        // 实现token验证逻辑
        return true;
    }
}
```

#### 6.2.2 自定义过滤器工厂

```java
@Component
public class CustomFilterFactory extends AbstractGatewayFilterFactory<CustomFilterFactory.Config> {
    
    public CustomFilterFactory() {
        super(Config.class);
    }
    
    @Override
    public GatewayFilter apply(Config config) {
        return (exchange, chain) -> {
            // 前置处理
            if (config.isPreFilter()) {
                log.info("Pre-filter processing");
            }
            
            return chain.filter(exchange)
                .then(Mono.fromRunnable(() -> {
                    // 后置处理
                    if (config.isPostFilter()) {
                        log.info("Post-filter processing");
                    }
                }));
        };
    }
    
    @Data
    public static class Config {
        private boolean preFilter = true;
        private boolean postFilter = true;
    }
}
```

## 7. 限流配置

### 7.1 Redis限流器

```yaml
spring:
  redis:
    host: localhost
    port: 6379
  cloud:
    gateway:
      routes:
        - id: rate_limit_route
          uri: http://localhost:8081
          predicates:
            - Path=/api/**
          filters:
            - name: RequestRateLimiter
              args:
                redis-rate-limiter.replenishRate: 10
                redis-rate-limiter.burstCapacity: 20
                key-resolver: "#{@userKeyResolver}"
```

### 7.2 自定义限流键解析器

```java
@Configuration
public class RateLimiterConfig {
    
    @Bean
    public KeyResolver userKeyResolver() {
        return exchange -> {
            String user = exchange.getRequest().getHeaders().getFirst("X-User-Id");
            if (user == null) {
                user = "anonymous";
            }
            return Mono.just(user);
        };
    }
}
```

## 8. 熔断器配置

### 8.1 添加Hystrix依赖

```xml
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-starter-netflix-hystrix</artifactId>
</dependency>
```

### 8.2 配置熔断器

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: hystrix_route
          uri: http://localhost:8081
          predicates:
            - Path=/api/**
          filters:
            - name: Hystrix
              args:
                name: fallbackcmd
                fallbackUri: forward:/fallback
```

### 8.3 熔断器回调接口

```java
@RestController
public class FallbackController {
    
    @GetMapping("/fallback")
    public ResponseEntity<String> fallback() {
        return ResponseEntity.ok("Service is temporarily unavailable. Please try again later.");
    }
}
```

## 9. 安全配置

### 9.1 JWT认证过滤器

```java
@Component
public class JwtAuthenticationFilter implements GlobalFilter, Ordered {
    
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String token = request.getHeaders().getFirst("Authorization");
        
        if (token != null && token.startsWith("Bearer ")) {
            try {
                String jwt = token.substring(7);
                Claims claims = Jwts.parser()
                    .setSigningKey("secret")
                    .parseClaimsJws(jwt)
                    .getBody();
                
                // 将用户信息添加到请求头
                ServerHttpRequest modifiedRequest = request.mutate()
                    .header("X-User-Id", claims.getSubject())
                    .header("X-User-Role", claims.get("role", String.class))
                    .build();
                
                return chain.filter(exchange.mutate().request(modifiedRequest).build());
            } catch (Exception e) {
                exchange.getResponse().setStatusCode(HttpStatus.UNAUTHORIZED);
                return exchange.getResponse().setComplete();
            }
        }
        
        return chain.filter(exchange);
    }
    
    @Override
    public int getOrder() {
        return -200;
    }
}
```

## 10. 监控和日志

### 10.1 添加Micrometer依赖

```xml
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

### 10.2 配置指标收集

```yaml
management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus
  metrics:
    export:
      prometheus:
        enabled: true
```

### 10.3 自定义指标

```java
@Component
public class GatewayMetrics {
    
    private final Counter requestCounter;
    private final Timer requestTimer;
    
    public GatewayMetrics(MeterRegistry meterRegistry) {
        this.requestCounter = Counter.builder("gateway.requests.total")
            .description("Total number of gateway requests")
            .register(meterRegistry);
        
        this.requestTimer = Timer.builder("gateway.request.duration")
            .description("Gateway request duration")
            .register(meterRegistry);
    }
    
    public void incrementRequestCount() {
        requestCounter.increment();
    }
    
    public Timer.Sample startTimer() {
        return Timer.start();
    }
}
```

## 11. 实际开发中的最佳实践

### 11.1 网关部署方式

在实际开发中，网关的部署方式主要有以下几种：

#### 11.1.1 独立微服务部署（推荐）

**优点：**
- 职责单一，便于维护和扩展
- 可以独立进行版本升级和配置修改
- 便于监控和故障排查
- 支持水平扩展

**适用场景：**
- 中大型微服务架构
- 需要复杂路由和过滤逻辑
- 对性能和可用性要求较高

**项目结构示例：**

```
gateway-service/
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   └── com/example/gateway/
│   │   │       ├── config/
│   │   │       ├── filter/
│   │   │       ├── handler/
│   │   │       └── GatewayApplication.java
│   │   └── resources/
│   │       ├── application.yml
│   │       └── application-prod.yml
│   └── test/
├── Dockerfile
├── docker-compose.yml
└── pom.xml
```

#### 11.1.2 集成到现有服务中

**适用场景：**
- 小型项目或原型开发
- 路由逻辑相对简单
- 团队规模较小

**缺点：**
- 职责不够清晰
- 难以独立扩展和维护
- 可能影响主服务的性能

### 11.2 配置管理策略

#### 11.2.1 环境分离

```yaml
# application-dev.yml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: http://localhost:8081
          predicates:
            - Path=/api/users/**

# application-prod.yml
spring:
  cloud:
    gateway:
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/users/**
```

#### 11.2.2 配置中心集成

```yaml
spring:
  cloud:
    config:
      uri: http://config-server:8888
      name: gateway-service
      profile: ${spring.profiles.active}
```

### 11.3 高可用部署

#### 11.3.1 多实例部署

```yaml
# docker-compose.yml
version: '3.8'
services:
  gateway-1:
    image: gateway-service:latest
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=prod
    networks:
      - gateway-network
  
  gateway-2:
    image: gateway-service:latest
    ports:
      - "8081:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=prod
    networks:
      - gateway-network

networks:
  gateway-network:
    driver: bridge
```

#### 11.3.2 负载均衡配置

```yaml
spring:
  cloud:
    gateway:
      discovery:
        locator:
          enabled: true
          lower-case-service-id: true
      routes:
        - id: user-service
          uri: lb://user-service
          predicates:
            - Path=/api/users/**
```

### 11.4 性能优化

#### 11.4.1 连接池配置

```yaml
spring:
  cloud:
    gateway:
      httpclient:
        connect-timeout: 1000
        response-timeout: 5s
        pool:
          max-connections: 200
          max-idle-time: 15s
```

#### 11.4.2 缓存配置

```java
@Configuration
@EnableCaching
public class CacheConfig {
    
    @Bean
    public CacheManager cacheManager() {
        RedisCacheManager cacheManager = RedisCacheManager.builder(redisConnectionFactory())
            .cacheDefaults(defaultConfig())
            .build();
        return cacheManager;
    }
    
    private RedisCacheConfiguration defaultConfig() {
        return RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(10))
            .serializeKeysWith(RedisSerializationContext.SerializationPair.fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(RedisSerializationContext.SerializationPair.fromSerializer(new GenericJackson2JsonRedisSerializer()));
    }
}
```

## 12. 常见问题和解决方案

### 12.1 跨域问题

```java
@Configuration
public class CorsConfig {
    
    @Bean
    public CorsWebFilter corsFilter() {
        CorsConfiguration config = new CorsConfiguration();
        config.addAllowedOrigin("*");
        config.addAllowedHeader("*");
        config.addAllowedMethod("*");
        
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        
        return new CorsWebFilter(source);
    }
}
```

### 12.2 超时处理

```yaml
spring:
  cloud:
    gateway:
      httpclient:
        response-timeout: 10s
        pool:
          max-idle-time: 30s
```

### 12.3 重试机制

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: retry_route
          uri: lb://user-service
          predicates:
            - Path=/api/users/**
          filters:
            - name: Retry
              args:
                retries: 3
                statuses: BAD_GATEWAY,SERVICE_UNAVAILABLE
                methods: GET,POST
```

## 13. 总结

Spring Cloud Gateway作为微服务架构中的API网关，提供了强大的路由、过滤、限流、熔断等功能。在实际开发中，建议将网关作为独立的微服务进行部署，这样可以更好地实现职责分离、便于维护和扩展。

### 13.1 关键要点

1. **路由配置**：灵活的路由规则，支持多种断言条件
2. **过滤器链**：强大的过滤器机制，支持全局和局部过滤
3. **服务发现**：与Eureka、Consul等服务注册中心集成
4. **监控运维**：丰富的监控指标和健康检查
5. **高可用**：支持多实例部署和负载均衡

### 13.2 最佳实践

1. 将网关作为独立微服务部署
2. 合理配置路由规则和过滤器
3. 实现适当的限流和熔断机制
4. 配置完善的监控和日志
5. 考虑高可用和性能优化

通过合理使用Spring Cloud Gateway，可以构建一个稳定、高效、可扩展的微服务网关系统。