---
title: Kafka
main_color: "#E2EAF4"
categories: 消息队列
tags:
  - 消息队列
cover: https://free.picui.cn/free/2026/03/28/69c74e1ec5a2e.webp
---


## Kafka全面指南

### 一、核心概念速览
- **Broker**: Kafka 服务器实例，集群由多个 Broker 组成。
- **Topic**: 主题，消息按主题分类存储。
- **Partition**: 分区，Topic 的并行度与吞吐单位；同一分区内消息按偏移量有序。
- **Replica/ISR**: 副本与同步副本集合，用于高可用；`min.insync.replicas` 决定写成功的最少副本数。
- **Producer**: 生产者，负责写入消息；`acks`、`retries`、`idempotence` 决定投递可靠性。
- **Consumer/Group**: 消费者与消费组；同组内分区只会被一个实例消费，实现水平扩展。
- **Offset**: 消费位点；默认存储在 Kafka 内部主题 `__consumer_offsets`。
- **Log Compaction/Deletion**: 日志压缩或过期删除策略，影响存储与回溯能力。

---

### 二、常用安装与 CLI（示例）
> 实际路径以本机 Kafka 安装为准

```bash
# 创建 Topic（3 副本、6 分区）
kafka-topics.sh --create --topic demo.orders --partitions 6 --replication-factor 3 --bootstrap-server localhost:9092

# 查看 Topic 详情
kafka-topics.sh --describe --topic demo.orders --bootstrap-server localhost:9092 | cat

# 查看消费组状态与滞后
kafka-consumer-groups.sh --bootstrap-server localhost:9092 --group order-consumer --describe | cat

# 快速写入/读取（测试）
kafka-console-producer.sh --broker-list localhost:9092 --topic demo.orders
kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic demo.orders --from-beginning | cat
```

---

### 三、Spring Boot 项目准备

#### 1. 依赖（Maven）
```xml
<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.kafka</groupId>
    <artifactId>spring-kafka</artifactId>
  </dependency>
  <dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
  </dependency>
</dependencies>
```

#### 2. 配置（application.yml）
```yaml
spring:
  kafka:
    bootstrap-servers: localhost:9092
    producer:
      acks: all
      retries: 3
      batch-size: 32768           # 32KB 批量
      linger-ms: 10               # 最多等待 10ms 以凑批
      compression-type: lz4
      enable-idempotence: true    # 幂等
      max-in-flight-requests-per-connection: 5
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
      properties:
        spring.json.add.type.headers: false     # 与多语言/非 Spring 兼容
    consumer:
      group-id: order-consumer
      auto-offset-reset: latest
      enable-auto-commit: false                 # 业务可控提交
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.springframework.kafka.support.serializer.JsonDeserializer
      properties:
        spring.json.trusted.packages: "*"
    listener:
      type: single
      ack-mode: manual
    # 开启事务（Exactly-Once 写入）
    producer.transaction-id-prefix: tx-order-
```

#### 3. DTO 与 Topic 自动创建
```java
// OrderCreatedEvent.java
public class OrderCreatedEvent {
    private String orderId;
    private String userId;
    private long   amount;
    private long   createdAt;

    // getters/setters/constructors/toString 省略
}
```

```java
// KafkaTopicConfig.java
import org.apache.kafka.clients.admin.NewTopic;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class KafkaTopicConfig {
    @Bean
    public NewTopic ordersTopic() {
        // 生产环境按容量与并发调优分区与副本
        return new NewTopic("demo.orders", 6, (short) 3);
    }

    @Bean
    public NewTopic ordersDltTopic() {
        return new NewTopic("demo.orders.DLT", 6, (short) 3);
    }
}
```

---

### 四、生产者示例

#### 1) 基础发送（键控有序 + 回调）
```java
// OrderProducer.java
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class OrderProducer {
    private final KafkaTemplate<String, OrderCreatedEvent> kafkaTemplate;

    public OrderProducer(KafkaTemplate<String, OrderCreatedEvent> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void sendOrder(OrderCreatedEvent event) {
        String key = event.getUserId(); // 以 userId 保证同一用户事件落到同一分区内的顺序
        kafkaTemplate.send("demo.orders", key, event)
                .whenComplete((result, ex) -> {
                    if (ex == null) {
                        // 成功
                        var meta = result.getRecordMetadata();
                        System.out.printf("sent ok topic=%s partition=%d offset=%d\n",
                                meta.topic(), meta.partition(), meta.offset());
                    } else {
                        // 失败（可接入告警/重试）
                        ex.printStackTrace();
                    }
                });
    }

    // 同步发送（需要强一致确认场景）
    public void sendSync(OrderCreatedEvent event) throws Exception {
        kafkaTemplate.send("demo.orders", event.getUserId(), event).get();
    }
}
```

#### 2) 事务发送（Exactly-Once 写入）
```java
// Transactional send
import org.springframework.stereotype.Service;

@Service
public class OrderTxService {
    private final KafkaTemplate<String, OrderCreatedEvent> kafkaTemplate;

    public OrderTxService(KafkaTemplate<String, OrderCreatedEvent> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void createOrderTransactionally(OrderCreatedEvent event) {
        kafkaTemplate.executeInTransaction(tpl -> {
            tpl.send("demo.orders", event.getUserId(), event);
            // 可在同一事务内发送多条消息/多个主题
            return true;
        });
    }
}
```

---

### 五、消费者示例

#### 1) 容器工厂与错误处理（DLT）
```java
// KafkaConsumerConfig.java
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.kafka.listener.DeadLetterPublishingRecoverer;
import org.springframework.util.backoff.FixedBackOff;

@Configuration
public class KafkaConsumerConfig {
    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, OrderCreatedEvent> recordFactory(
            org.springframework.kafka.core.ConsumerFactory<String, OrderCreatedEvent> consumerFactory,
            KafkaTemplate<String, OrderCreatedEvent> kafkaTemplate
    ) {
        var factory = new ConcurrentKafkaListenerContainerFactory<String, OrderCreatedEvent>();
        factory.setConsumerFactory(consumerFactory);
        factory.setConcurrency(3); // 并发线程，受分区数限制
        factory.getContainerProperties().setAckMode(org.springframework.kafka.listener.ContainerProperties.AckMode.MANUAL);

        var recoverer = new DeadLetterPublishingRecoverer(kafkaTemplate,
                (record, ex) -> new org.apache.kafka.common.TopicPartition(record.topic() + ".DLT", record.partition()));
        var errorHandler = new DefaultErrorHandler(recoverer, new FixedBackOff(1000L, 3)); // 固定回退 3 次
        factory.setCommonErrorHandler(errorHandler);
        return factory;
    }

    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, OrderCreatedEvent> batchFactory(
            org.springframework.kafka.core.ConsumerFactory<String, OrderCreatedEvent> consumerFactory
    ) {
        var factory = new ConcurrentKafkaListenerContainerFactory<String, OrderCreatedEvent>();
        factory.setConsumerFactory(consumerFactory);
        factory.setBatchListener(true);
        factory.getContainerProperties().setAckMode(org.springframework.kafka.listener.ContainerProperties.AckMode.MANUAL);
        return factory;
    }
}
```

#### 2) 单条消费（手动提交偏移量）
```java
// OrderConsumer.java
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

@Component
public class OrderConsumer {
    @KafkaListener(topics = "demo.orders", containerFactory = "recordFactory")
    public void onMessage(ConsumerRecord<String, OrderCreatedEvent> record, Acknowledgment ack) {
        try {
            OrderCreatedEvent event = record.value();
            // 处理业务（注意幂等）
            System.out.println("consume: " + event);
            ack.acknowledge(); // 明确提交偏移量
        } catch (Exception e) {
            // 抛出异常交给容器的错误处理（重试/进入 DLT）
            throw e;
        }
    }
}
```

#### 3) 批量消费
```java
// BatchOrderConsumer.java
import java.util.List;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Component;

@Component
public class BatchOrderConsumer {
    @KafkaListener(topics = "demo.orders", containerFactory = "batchFactory")
    public void onBatch(List<ConsumerRecord<String, OrderCreatedEvent>> records, Acknowledgment ack) {
        // 批处理提高吞吐
        records.forEach(r -> System.out.println("batch consume: " + r.value()));
        ack.acknowledge();
    }
}
```

---

### 六、端到端 Exactly-Once（读-处理-写）

场景：从 `demo.orders` 消费，处理后写入 `demo.orders.processed`，要求端到端“恰好一次”。要点：
- 生产端启用事务（`producer.transaction-id-prefix`）。
- 监听容器绑定 `KafkaTransactionManager`，使用 `AckMode.RECORD` 或手动 ack。
- 处理逻辑在同一 Kafka 事务中完成消费位点提交与新消息发送。

示例配置与代码（关键片段）：
```java
// TxKafkaConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.core.ProducerFactory;
import org.springframework.kafka.transaction.KafkaTransactionManager;

@Configuration
public class TxKafkaConfig {
    @Bean
    public KafkaTransactionManager<String, OrderCreatedEvent> kafkaTxManager(ProducerFactory<String, OrderCreatedEvent> pf) {
        return new KafkaTransactionManager<>(pf);
    }

    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, OrderCreatedEvent> txFactory(
            org.springframework.kafka.core.ConsumerFactory<String, OrderCreatedEvent> cf,
            KafkaTransactionManager<String, OrderCreatedEvent> tm
    ) {
        var factory = new ConcurrentKafkaListenerContainerFactory<String, OrderCreatedEvent>();
        factory.setConsumerFactory(cf);
        factory.getContainerProperties().setAckMode(org.springframework.kafka.listener.ContainerProperties.AckMode.MANUAL);
        factory.getContainerProperties().setTransactionManager(tm);
        return factory;
    }
}
```

```java
// ExactlyOnceProcessor.java
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.stereotype.Service;

@Service
public class ExactlyOnceProcessor {
    private final KafkaTemplate<String, OrderCreatedEvent> kafkaTemplate;

    public ExactlyOnceProcessor(KafkaTemplate<String, OrderCreatedEvent> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    @KafkaListener(topics = "demo.orders", containerFactory = "txFactory")
    public void process(OrderCreatedEvent event, Acknowledgment ack) {
        kafkaTemplate.executeInTransaction(tpl -> {
            // 1) 业务处理（幂等）
            // 2) 产出到下游主题
            tpl.send("demo.orders.processed", event.getUserId(), event);
            // 3) 提交本条消费位点
            ack.acknowledge();
            return true;
        });
    }
}
```

---

### 七、序列化与对象消息
- Spring Kafka 默认 Json 序列化即可跨服务传输对象。
- 与非 Java/非 Spring 交互时避免写入类型头（`spring.json.add.type.headers=false`）。
- 需要强 Schema 的场景可考虑 Avro/Protobuf + Schema Registry（额外组件，不在本示例覆盖）。

---

### 八、Topic 配置与存储策略（重要）
- **保留策略**：
  - 时间删除：`retention.ms`（如 7 天）；
  - 大小删除：`retention.bytes`；
  - 压缩：`cleanup.policy=compact`（按 Key 保留最新值，适合 KV/快照）；或 `compact,delete` 组合。
- **最小同步副本**：`min.insync.replicas` 与生产者 `acks=all` 配合，防止少数副本下数据丢失。
- **大消息**：调整 `message.max.bytes`、`fetch.max.bytes`，尽量避免超大单消息，推荐切片。

示例修改（按需）：
```bash
kafka-configs.sh --bootstrap-server localhost:9092 \
  --alter --topic demo.orders \
  --add-config retention.ms=604800000,cleanup.policy=delete
```

---

### 九、监控与关键指标
- **生产端**：`record-error-rate`、`record-retry-rate`、`request-latency-avg/p95`。
- **消费端**：`consumer_lag`、`records-lag-max`、反压情况（poll 间隔、处理耗时）。
- **集群端**：ISR 变动、Under Replicated Partitions、Leader 选举频率、磁盘使用与页缓存命中率。

---

### 十、常见问题与排查
- **重复消费**：使用幂等（业务层去重）+ 事务 + 以 Key 控制有序处理。
- **乱序**：同 Key 保证分区内顺序；跨 Key 无全局顺序保证。
- **位点提交不当**：处理成功后再提交；失败抛出由容器重试或 DLT。
- **批量延迟过高**：调小 `linger.ms` 或 `batch.size`；低延迟场景减少凑批。
- **分区不均衡**：做好 Key 设计或自定义分区器；监控热点分区。

---

### 十一、最佳实践清单
- **可靠性**：`acks=all` + 合理 `min.insync.replicas`，生产端开启 `enable.idempotence`。
- **吞吐**：合适的 `batch.size`、`linger.ms`、压缩（`lz4/zstd`）。
- **顺序**：按业务维度使用 Key，必要时单分区串行处理。
- **隔离**：生产、消费使用独立集群或独立 Topic 前缀；不同业务分组隔离。
- **资源**：分区数依据峰值吞吐、消费者并发、延迟目标综合评估。
- **重试/死信**：消费侧使用 `DefaultErrorHandler + DLT`，明确重试上限与告警闭环。
- **事务**：仅在确需端到端一致性时使用；否则使用幂等 + 业务去重。

---

以上示例可直接落地到 Spring Boot 项目中：
- 先引入依赖与 `application.yml` 配置；
- 定义 DTO、Topic、Producer、Consumer；
- 按业务选择单条/批量、手动 ack、是否开启事务与 DLT；
- 结合 CLI 与监控工具进行观测与调优。
