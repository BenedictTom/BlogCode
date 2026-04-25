---
title: Nacos
main_color: "#80a340ff"
categories: 微服务
tags:
  - Spring Cloud
cover: https://free.picui.cn/free/2026/03/28/69c74e5516073.png
---

## Nacos全面指南

Nacos是阿里巴巴开源的一个更易于构建云原生应用的动态服务发现、配置管理和服务管理平台。它提供了服务注册与发现、配置管理、动态DNS服务、服务元数据及流量管理等功能。

### 注册中心

#### 1. 什么是服务注册中心

服务注册中心是微服务架构中的核心组件，负责管理所有服务的注册、发现和健康检查。Nacos作为注册中心具有以下特点：

- **高可用性**：支持集群部署，保证服务的高可用
- **服务健康检查**：自动检测服务状态，及时剔除不健康的服务
- **负载均衡**：支持多种负载均衡策略
- **服务元数据管理**：支持服务版本、分组等元数据管理

#### 2. 快速开始

##### 2.1 启动Nacos服务器

```bash
# 下载Nacos
wget https://github.com/alibaba/nacos/releases/download/2.2.3/nacos-server-2.2.3.zip

# 解压并启动
unzip nacos-server-2.2.3.zip
cd nacos/bin
# Linux/Unix/Mac
sh startup.sh -m standalone
# Windows
startup.cmd -m standalone
```

##### 2.2 添加依赖

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
    <version>2021.0.5.0</version>
</dependency>
```

##### 2.3 配置application.yml

```yaml
spring:
  application:
    name: user-service
  cloud:
    nacos:
      discovery:
        server-addr: 127.0.0.1:8848
        namespace: public
        group: DEFAULT_GROUP
        cluster-name: DEFAULT
        username: nacos
        password: nacos
        # 是否启用服务注册
        register-enabled: true
        # 是否启用服务发现
        discovery-enabled: true
        # 心跳间隔
        heart-beat-interval: 5000
        # 心跳超时时间
        heart-beat-timeout: 15000
        # IP删除超时时间
        ip-delete-timeout: 30000
```

##### 2.4 启用服务发现

```java
@SpringBootApplication
@EnableDiscoveryClient
public class UserServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserServiceApplication.class, args);
    }
}
```

#### 3. 服务注册与发现

##### 3.1 服务注册

服务启动后会自动向Nacos注册中心注册，包含以下信息：
- 服务名称
- 服务IP地址
- 服务端口
- 服务健康状态
- 服务元数据

##### 3.2 服务发现

```java
@RestController
@RequestMapping("/user")
public class UserController {
    
    @Autowired
    private DiscoveryClient discoveryClient;
    
    @GetMapping("/instances")
    public List<ServiceInstance> getInstances() {
        // 获取指定服务的所有实例
        return discoveryClient.getInstances("user-service");
    }
    
    @GetMapping("/services")
    public List<String> getServices() {
        // 获取所有服务名称
        return discoveryClient.getServices();
    }
}
```

##### 3.3 负载均衡

```java
@RestController
public class TestController {
    
    @Autowired
    private RestTemplate restTemplate;
    
    @Bean
    @LoadBalanced
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
    
    @GetMapping("/test")
    public String test() {
        // 使用服务名调用，自动负载均衡
        return restTemplate.getForObject("http://user-service/user/info", String.class);
    }
}
```

#### 4. 高级特性

##### 4.1 服务分组

```yaml
spring:
  cloud:
    nacos:
      discovery:
        group: PROD_GROUP  # 生产环境分组
```

##### 4.2 命名空间

```yaml
spring:
  cloud:
    nacos:
      discovery:
        namespace: prod-namespace  # 生产环境命名空间
```

##### 4.3 集群配置

```yaml
spring:
  cloud:
    nacos:
      discovery:
        cluster-name: SHANGHAI  # 上海集群
```

### 配置中心

#### 1. 什么是配置中心

配置中心用于集中管理应用配置，支持配置的动态刷新、版本管理、灰度发布等功能。Nacos配置中心具有以下优势：

- **配置集中管理**：所有配置集中存储，便于管理
- **动态配置更新**：支持配置热更新，无需重启应用
- **配置版本管理**：支持配置的版本控制和回滚
- **配置加密**：支持敏感配置的加密存储

#### 2. 快速开始

##### 2.1 添加依赖

```xml
<dependency>
    <groupId>com.alibaba.cloud</groupId>
    <artifactId>spring-cloud-starter-alibaba-nacos-config</artifactId>
    <version>2021.0.5.0</version>
</dependency>
```

##### 2.2 配置bootstrap.yml

```yaml
spring:
  application:
    name: user-service
  profiles:
    active: dev
  cloud:
    nacos:
      config:
        server-addr: 127.0.0.1:8848
        namespace: public
        group: DEFAULT_GROUP
        # 配置文件格式
        file-extension: yaml
        # 共享配置
        shared-configs:
          - data-id: common-config.yaml
            group: DEFAULT_GROUP
            refresh: true
        # 扩展配置
        extension-configs:
          - data-id: extension-config.yaml
            group: DEFAULT_GROUP
            refresh: true
        # 配置加密
        encrypt-data-id: encrypt-config.yaml
        # 配置加密密钥
        encrypt-key: your-encrypt-key
```

##### 2.3 使用config.import方式（推荐）

Spring Boot 2.4+版本引入了新的配置导入机制，可以直接在`application.yml`中使用`spring.config.import`来导入Nacos配置：

```yaml
# application.yml
spring:
  application:
    name: user-service
  profiles:
    active: dev
  config:
    import:
      # 导入Nacos配置，支持多种格式
      - nacos:coupon.yaml
      - nacos:user-service-${spring.profiles.active}.yaml
      - nacos:common-config.yaml
      - nacos:database-config.yaml
      - nacos:redis-config.yaml
      # 支持指定命名空间和分组
      - nacos:prod-config.yaml?namespace=prod&group=PROD_GROUP
      - nacos:test-config.yaml?namespace=test&group=TEST_GROUP
      # 支持配置刷新
      - nacos:dynamic-config.yaml?refresh=true
      # 支持配置优先级
      - optional:nacos:optional-config.yaml
      # 支持条件导入
      - conditional:nacos:${spring.profiles.active}-config.yaml
```

**config.import方式的优势：**

1. **简化配置**：无需额外的bootstrap.yml文件
2. **灵活导入**：支持条件导入、可选导入
3. **优先级控制**：可以控制配置的加载顺序
4. **环境适配**：支持profile相关的配置导入
5. **统一管理**：所有配置导入都在一个地方管理

**配置参数说明：**

- `nacos:` - 指定配置源为Nacos
- `namespace` - 命名空间，默认为public
- `group` - 配置分组，默认为DEFAULT_GROUP
- `refresh` - 是否支持配置刷新，默认为true
- `optional:` - 可选配置，导入失败不会影响应用启动
- `conditional:` - 条件配置，根据条件决定是否导入

**实际应用示例：**

```yaml
# 生产环境配置
spring:
  config:
    import:
      - nacos:prod-common.yaml?namespace=prod&group=PROD_GROUP
      - nacos:prod-database.yaml?namespace=prod&group=PROD_GROUP
      - nacos:prod-redis.yaml?namespace=prod&group=PROD_GROUP
      - nacos:prod-security.yaml?namespace=prod&group=PROD_GROUP

# 开发环境配置
spring:
  config:
    import:
      - nacos:dev-common.yaml?namespace=dev&group=DEV_GROUP
      - nacos:dev-database.yaml?namespace=dev&group=DEV_GROUP
      - nacos:dev-redis.yaml?namespace=dev&group=DEV_GROUP

# 测试环境配置
spring:
  config:
    import:
      - nacos:test-common.yaml?namespace=test&group=TEST_GROUP
      - nacos:test-database.yaml?namespace=test&group=TEST_GROUP
```

**注意事项：**

1. 使用`config.import`方式时，需要确保Spring Boot版本在2.4+
2. 配置导入顺序很重要，后面的配置会覆盖前面的配置
3. 建议使用`optional:`前缀导入非关键配置
4. 生产环境建议明确指定namespace和group，避免配置冲突

##### 2.4 启用配置管理

```java
@SpringBootApplication
@EnableDiscoveryClient
public class UserServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserServiceApplication.class, args);
    }
}
```

#### 3. 配置管理

##### 3.1 配置文件命名规则

Nacos配置文件的命名规则为：`${spring.application.name}-${spring.profiles.active}.${spring.cloud.nacos.config.file-extension}`

例如：`user-service-dev.yaml`

##### 3.2 配置内容示例

在Nacos控制台创建配置文件：

```yaml
# user-service-dev.yaml
server:
  port: 8080

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/user_db
    username: root
    password: 123456
    driver-class-name: com.mysql.cj.jdbc.Driver

# 自定义配置
app:
  name: User Service
  version: 1.0.0
  features:
    - user-management
    - user-auth
```

##### 3.3 配置使用

```java
@RestController
@RequestMapping("/config")
@RefreshScope  // 支持配置热更新
public class ConfigController {
    
    @Value("${app.name}")
    private String appName;
    
    @Value("${app.version}")
    private String appVersion;
    
    @Autowired
    private ConfigurationProperties configProps;
    
    @GetMapping("/info")
    public Map<String, Object> getConfigInfo() {
        Map<String, Object> info = new HashMap<>();
        info.put("appName", appName);
        info.put("appVersion", appVersion);
        info.put("features", configProps.getFeatures());
        return info;
    }
}

@Component
@ConfigurationProperties(prefix = "app")
@Data
public class ConfigurationProperties {
    private String name;
    private String version;
    private List<String> features;
}
```

#### 4. 高级特性

##### 4.1 配置加密

```yaml
# 在Nacos中配置加密的敏感信息
spring:
  datasource:
    password: ENC(encrypted-password)
```

##### 4.2 配置回滚

Nacos支持配置的历史版本管理，可以快速回滚到之前的配置版本。

##### 4.3 灰度发布

支持配置的灰度发布，可以逐步将新配置推送给部分实例。

##### 4.4 配置监听

```java
@Component
public class ConfigChangeListener {
    
    @NacosConfigListener(dataId = "user-service-dev.yaml", groupId = "DEFAULT_GROUP")
    public void onConfigChange(String newConfig) {
        log.info("配置发生变化: {}", newConfig);
        // 处理配置变化逻辑
    }
}
```

### 最佳实践

#### 1. 高可用部署

- 部署Nacos集群，至少3个节点
- 使用外部数据库（MySQL）存储配置
- 配置负载均衡器

#### 2. 安全配置

- 启用Nacos的认证功能
- 配置适当的权限控制
- 敏感配置使用加密存储

#### 3. 监控告警

- 监控Nacos服务状态
- 配置服务健康检查告警
- 监控配置变更频率

#### 4. 性能优化

- 合理配置心跳间隔
- 适当设置配置缓存
- 监控服务注册发现性能

### 总结

Nacos作为Spring Cloud Alibaba生态的核心组件，提供了完整的服务注册发现和配置管理解决方案。通过合理使用Nacos，可以构建高可用、易维护的微服务架构。

在实际项目中，建议：

1. **合理规划命名空间和分组**：按环境、业务模块等维度进行划分
2. **配置管理规范化**：建立配置命名规范，便于管理和维护
3. **监控和告警**：建立完善的监控体系，及时发现问题
4. **备份和恢复**：定期备份配置数据，建立恢复机制
