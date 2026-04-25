---
title: Spring AMQP 完整指南
main_color: "rgb(11, 32, 228)"
categories: 消息队列
tags:
  - AMQP
cover: https://free.picui.cn/free/2026/03/28/69c74d6c92bf8.png
---

> 一文吃透 AMQP 与 Spring AMQP（Spring for RabbitMQ）在生产中的用法：从快速上手、可靠投递、消费确认、重试与死信、延迟消息、幂等与顺序、批量消费、监控与测试，到常见问题排查，配齐可运行示例。

### 1. AMQP 与 RabbitMQ 基础
- **AMQP 是什么**: 一种消息协议，定义了消息、交换机、队列、路由键、绑定等概念。
- **RabbitMQ 关键概念**:
  - **Exchange（交换机）**: 接收消息并路由到队列。类型：`direct`（精确匹配）、`topic`（通配符）、`fanout`（广播）、`headers`（按头部匹配）。
  - **Queue（队列）**: 存放消息；可设置 TTL、最大长度、死信交换机等参数。
  - **Routing Key（路由键）**: 决定消息如何从交换机路由到队列。
  - **Binding（绑定）**: 交换机与队列之间的路由关系。
  - **Connection / Channel**: TCP 连接与轻量级信道；一个连接可复用多个通道。
  - **VHost**: 类似命名空间，用于隔离资源与权限。

### 2. 本地环境准备（RabbitMQ）
- **Docker 一键启动（含管理界面）**:
```bash
docker run -d --name rmq -p 5672:5672 -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=guest -e RABBITMQ_DEFAULT_PASS=guest \
  rabbitmq:3.13-management
```
- 浏览器打开 `http://localhost:15672`，用户名/密码：`guest/guest`。

### 3. Spring AMQP 选择
- Spring 的实现主要是 `spring-amqp` 与 `spring-rabbit`（通常统称 Spring for RabbitMQ）。
- Spring Boot 场景下直接使用 `spring-boot-starter-amqp` 即可。

#### 3.1 依赖
```xml
<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-amqp</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
  </dependency>
  <dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.retry</groupId>
    <artifactId>spring-retry</artifactId>
  </dependency>
</dependencies>
```

#### 3.2 配置
```yaml
spring:
  rabbitmq:
    host: localhost
    port: 5672
    username: guest
    password: guest
    virtual-host: /
    # 生产端可靠性
    publisher-confirm-type: correlated   # NONE|SIMPLE|CORRELATED
    publisher-returns: true
    template:
      mandatory: true
    # 消费端容器默认配置（可按需覆盖）
    listener:
      simple:
        acknowledge-mode: auto          # auto|manual|none
        concurrency: 2
        max-concurrency: 8
        prefetch: 50
        default-requeue-rejected: false # 业务异常不要反复回队
```

### 4. 基础拓扑与对象模型
在 Spring 中推荐用 `@Bean` 方式声明交换机、队列与绑定，应用启动即确保存在。

```java
@Configuration
public class RabbitTopologyConfig {

    public static final String EXCHANGE_ORDER = "ex.order";
    public static final String QUEUE_ORDER_CREATED = "q.order.created";
    public static final String ROUTING_ORDER_CREATED = "order.created";

    @Bean
    public TopicExchange orderExchange() {
        return ExchangeBuilder.topicExchange(EXCHANGE_ORDER)
                .durable(true)
                .build();
    }

    @Bean
    public Queue orderCreatedQueue() {
        return QueueBuilder.durable(QUEUE_ORDER_CREATED)
                .withArgument("x-dead-letter-exchange", "ex.dlx")
                .withArgument("x-dead-letter-routing-key", "dlx.order")
                .build();
    }

    @Bean
    public Binding bindOrderCreated() {
        return BindingBuilder.bind(orderCreatedQueue())
                .to(orderExchange())
                .with(ROUTING_ORDER_CREATED);
    }

    @Bean
    public DirectExchange deadLetterExchange() {
        return ExchangeBuilder.directExchange("ex.dlx").durable(true).build();
    }

    @Bean
    public Queue deadLetterQueue() {
        return QueueBuilder.durable("q.dlx.order").build();
    }

    @Bean
    public Binding bindDlx() {
        return BindingBuilder.bind(deadLetterQueue())
                .to(deadLetterExchange())
                .with("dlx.order");
    }
}
```

### 5. 消息模型与序列化
- 建议使用 JSON 序列化并携带类型信息，便于演进。
```java
@Data
@AllArgsConstructor
@NoArgsConstructor
public class OrderCreatedEvent {
    private String orderId;
    private String userId;
    private BigDecimal amount;
    private Instant createdAt;
}
```

```java
@Configuration
public class RabbitMessageConfig {

    @Bean
    public MessageConverter jacksonMessageConverter() {
        Jackson2JsonMessageConverter converter = new Jackson2JsonMessageConverter();
        converter.setCreateMessageIds(true);
        return converter;
    }

    @Bean
    public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory,
                                         MessageConverter messageConverter) {
        RabbitTemplate template = new RabbitTemplate(connectionFactory);
        template.setMessageConverter(messageConverter);
        // Returns（不可路由）回调
        template.setReturnsCallback(returned -> {
            // 记录不可达消息
            System.out.printf("Returned msg: %s, replyCode=%d, replyText=%s, exchange=%s, routingKey=%s%n",
                    new String(returned.getMessage().getBody(), StandardCharsets.UTF_8),
                    returned.getReplyCode(), returned.getReplyText(),
                    returned.getExchange(), returned.getRoutingKey());
        });
        // Confirm（到达交换机）回调
        template.setConfirmCallback((correlationData, ack, cause) -> {
            if (!ack) {
                System.out.printf("Publish not ack, correlation=%s, cause=%s%n",
                        correlationData, cause);
            }
        });
        return template;
    }
}
```

### 6. 生产者发送消息
```java
@Service
@RequiredArgsConstructor
public class OrderProducer {

    private final RabbitTemplate rabbitTemplate;

    public void publishOrderCreated(OrderCreatedEvent event) {
        CorrelationData correlationData = new CorrelationData(UUID.randomUUID().toString());
        rabbitTemplate.convertAndSend(
                RabbitTopologyConfig.EXCHANGE_ORDER,
                RabbitTopologyConfig.ROUTING_ORDER_CREATED,
                event,
                message -> {
                    // 业务相关头部，可用于幂等等
                    message.getMessageProperties().setHeader("x-dedup-key", event.getOrderId());
                    message.getMessageProperties().setDeliveryMode(MessageDeliveryMode.PERSISTENT);
                    return message;
                },
                correlationData
        );
    }
}
```

### 7. 消费者与 ACK 策略
- `AUTO`：默认，异常时会根据异常类型决定是否 requeue。
- `MANUAL`：手动确认，适合需要精细控制的场景。

#### 7.1 基本消费（AUTO）
```java
@Component
public class OrderCreatedListener {

    @RabbitListener(queues = RabbitTopologyConfig.QUEUE_ORDER_CREATED)
    public void onMessage(OrderCreatedEvent event) {
        // 业务处理
        System.out.println("Consumed order: " + event.getOrderId());
        // 抛出运行时异常时，根据配置可能进入 DLQ（default-requeue-rejected=false）
    }
}
```

#### 7.2 手动 ACK（MANUAL）
```java
@Configuration
public class ManualAckContainerConfig {

    @Bean
    public SimpleRabbitListenerContainerFactory manualAckContainerFactory(
            SimpleRabbitListenerContainerFactoryConfigurer configurer,
            ConnectionFactory connectionFactory,
            MessageConverter messageConverter) {
        SimpleRabbitListenerContainerFactory factory = new SimpleRabbitListenerContainerFactory();
        configurer.configure(factory, connectionFactory);
        factory.setAcknowledgeMode(AcknowledgeMode.MANUAL);
        factory.setMessageConverter(messageConverter);
        factory.setPrefetchCount(10);
        return factory;
    }
}
```

```java
@Component
public class ManualAckListener {

    @RabbitListener(queues = RabbitTopologyConfig.QUEUE_ORDER_CREATED,
                    containerFactory = "manualAckContainerFactory")
    public void onMessage(Message message, Channel channel) throws IOException {
        try {
            // 反序列化
            String body = new String(message.getBody(), StandardCharsets.UTF_8);
            System.out.println("Raw message: " + body);
            // 业务处理...

            channel.basicAck(message.getMessageProperties().getDeliveryTag(), false);
        } catch (Exception ex) {
            // 是否重回队列由业务决定
            boolean requeue = false;
            channel.basicNack(message.getMessageProperties().getDeliveryTag(), false, requeue);
        }
    }
}
```

### 8. 重试、死信与失败处理
- 推荐：消费端使用 Spring Retry 做有限次重试 + 最终进入 DLQ；生产端依赖 Confirm/Return 与日志补偿。

#### 8.1 消费端重试配置
```java
@Configuration
@EnableRetry
public class ListenerRetryConfig {

    @Bean
    public SimpleRabbitListenerContainerFactory retryableContainerFactory(
            SimpleRabbitListenerContainerFactoryConfigurer configurer,
            ConnectionFactory connectionFactory,
            MessageConverter messageConverter) {
        SimpleRabbitListenerContainerFactory factory = new SimpleRabbitListenerContainerFactory();
        configurer.configure(factory, connectionFactory);
        factory.setMessageConverter(messageConverter);
        factory.setAdviceChain(RetryInterceptorBuilder.stateless()
                .maxAttempts(3)
                .backOffOptions(1000, 2.0, 5000) // 初始1s, 乘数2, 最大5s
                .recoverer((message, cause) -> {
                    // 超过重试次数，丢给 DLX（取决于容器的 requeue 策略）或记录日志告警
                    System.out.println("Retry exhausted: " + cause.getMessage());
                })
                .build());
        return factory;
    }
}
```

```java
@Component
public class RetryableListener {

    @RabbitListener(queues = RabbitTopologyConfig.QUEUE_ORDER_CREATED,
                    containerFactory = "retryableContainerFactory")
    public void onMessage(OrderCreatedEvent event) {
        // 模拟可能失败的业务
        if (new Random().nextBoolean()) {
            throw new IllegalStateException("random failure");
        }
        System.out.println("Processed: " + event.getOrderId());
    }
}
```

#### 8.2 死信队列与消息 TTL
- 队列参数：
  - `x-dead-letter-exchange` / `x-dead-letter-routing-key`
  - `x-message-ttl`（队列级 TTL）或消息级 `expiration`
- 上文 `RabbitTopologyConfig` 已配置 DLX 示例。

### 9. 延迟消息（两种方案）
- **TTL + DLX**：到期后路由到真正消费队列。
```java
@Bean
public Queue delayQueue() {
    return QueueBuilder.durable("q.delay.5s")
            .withArgument("x-dead-letter-exchange", RabbitTopologyConfig.EXCHANGE_ORDER)
            .withArgument("x-dead-letter-routing-key", RabbitTopologyConfig.ROUTING_ORDER_CREATED)
            .withArgument("x-message-ttl", 5000)
            .build();
}
```
- **延迟插件 `rabbitmq_delayed_message_exchange`**：更灵活（需要服务器装插件）。
```java
@Bean
public CustomExchange delayedExchange() {
    Map<String, Object> args = new HashMap<>();
    args.put("x-delayed-type", "topic");
    return new CustomExchange("ex.delay", "x-delayed-message", true, false, args);
}

@Bean
public Binding bindDelay() {
    return BindingBuilder.bind(orderCreatedQueue()).to(delayedExchange()).with("order.created").noargs();
}

// 发送时设置 x-delay
rabbitTemplate.convertAndSend("ex.delay", "order.created", event, m -> {
    m.getMessageProperties().setHeader("x-delay", 5000);
    return m;
});
```

### 10. 幂等、顺序与限流
- **幂等**：
  - 生产端为每条消息设置唯一业务键（如 `orderId`），消费端用 Redis `SETNX`/`INCR` 做去重；
  - 或使用数据库唯一键约束。
- **顺序**：
  - 单队列 + 单消费者 + `prefetch=1`；
  - 或者按分片键（如用户 ID）路由到不同队列以获得「分区内有序」。
- **限流**：
  - 设置 `prefetch` 与并发度；
  - 高峰期配合熔断与降级策略。

### 11. 批量发送与批量消费
- 发送端可以打包业务逻辑批量发送（注意消息大小限制，建议小于 128 KB）。
- 消费端容器支持批量：
```java
@Configuration
public class BatchContainerConfig {

    @Bean
    public SimpleRabbitListenerContainerFactory batchContainerFactory(
            SimpleRabbitListenerContainerFactoryConfigurer configurer,
            ConnectionFactory connectionFactory,
            MessageConverter messageConverter) {
        SimpleRabbitListenerContainerFactory factory = new SimpleRabbitListenerContainerFactory();
        configurer.configure(factory, connectionFactory);
        factory.setMessageConverter(messageConverter);
        factory.setBatchListener(true);
        factory.setConsumerBatchEnabled(true);
        factory.setBatchSize(20);
        factory.setPrefetchCount(40);
        return factory;
    }
}
```

```java
@Component
public class BatchListener {

    @RabbitListener(queues = RabbitTopologyConfig.QUEUE_ORDER_CREATED,
                    containerFactory = "batchContainerFactory")
    public void onBatch(List<OrderCreatedEvent> events) {
        events.forEach(e -> System.out.println("Batch: " + e.getOrderId()));
    }
}
```

### 12. 监控与运维建议
- 使用管理界面查看 `Connections/Channels/Exchanges/Queues/Bindings`。
- 指标：已就绪消息数、未确认消息数、入站速率、出站速率、拒绝率。
- Spring Boot 集成 Micrometer，导出到 Prometheus + Grafana 观察消费者滞后。
- 配置建议：
  - 生产环境使用 `Quorum Queues`（3.10+ 默认推荐）提升高可用；
  - 合理设置队列最大长度与 TTL，避免无限堆积；
  - 使用独立 `vhost` 与专用账号，最小权限原则。

### 13. 事务 vs Confirm/Return
- RabbitMQ 事务（`txSelect/txCommit`）会严重降低吞吐，不推荐。
- 推荐使用 `publisher confirm + return` 与业务补偿日志；必要时配合本地事务表/Outbox Pattern。

### 14. 集成测试（Testcontainers）
```java
@Testcontainers
@SpringBootTest
public class RabbitIntegrationTest {

    @Container
    static RabbitMQContainer rabbit = new RabbitMQContainer("rabbitmq:3.13-management");

    @DynamicPropertySource
    static void props(DynamicPropertyRegistry registry) {
        registry.add("spring.rabbitmq.host", rabbit::getHost);
        registry.add("spring.rabbitmq.port", rabbit::getAmqpPort);
        registry.add("spring.rabbitmq.username", () -> "guest");
        registry.add("spring.rabbitmq.password", () -> "guest");
    }

    @Autowired
    private OrderProducer producer;

    @Test
    void publish_and_consume() throws Exception {
        producer.publishOrderCreated(new OrderCreatedEvent("o-1", "u-1", new BigDecimal("9.99"), Instant.now()));
        // 断言逻辑可以依赖受控队列或同步屏障（如 CountDownLatch）
    }
}
```

### 15. 常见问题速查
- **消息重复消费**：消费者幂等设计（Redis/数据库唯一键），禁用无意义的 requeue。
- **消息丢失**：
  - 生产端启用 Confirm/Return，磁盘持久化（队列与消息 `durable/persistent`）；
  - 消费端 MANUAL ack，业务完成后再 ack。
- **消息堆积**：扩容消费者并发/副本数，提高 `prefetch` 与消费者处理效率；对堆积消息做离线归档/快消处理。
- **序列化兼容**：使用 JSON 并添加版本字段或类型头部，避免类变更导致反序列化失败。
- **连接耗尽**：连接池/复用 Channel，避免为每条消息新建连接；设置心跳与合理的连接上限。

### 16. 参考资料
- Spring AMQP 文档：`https://docs.spring.io/spring-amqp/reference/`
- Spring for RabbitMQ 文档：`https://docs.spring.io/spring-amqp/reference/html/`
- RabbitMQ 官方：`https://www.rabbitmq.com/`
- Testcontainers RabbitMQ：`https://www.testcontainers.org/modules/rabbitmq/`

### 17. 最小可运行示例清单
- 依赖：`spring-boot-starter-amqp`、`spring-retry`、`jackson`
- 关键类：
  - `RabbitTopologyConfig`：交换机/队列/绑定
  - `RabbitMessageConfig`：`RabbitTemplate` 与 `MessageConverter`
  - `OrderProducer`：生产者
  - `OrderCreatedListener` 或 `ManualAckListener`：消费者
- 运行步骤：
  - 启动 Docker 中的 RabbitMQ
  - 启动 Spring Boot 应用
  - 通过接口或命令行调用 `OrderProducer.publishOrderCreated(...)`
  - 观察消费者日志与 RabbitMQ 管理台的队列情况
