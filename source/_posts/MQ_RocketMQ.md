---
title: RocketMQ
main_color: "#E2EAF4"
categories: 消息队列
tags:
  - 消息队列
cover: https://free.picui.cn/free/2026/03/28/69c74f9f92765.png
---

# RocketMQ全面指南

## 目录
- [简介](#简介)
- [核心概念](#核心概念)
- [架构设计](#架构设计)
- [安装部署](#安装部署)
- [SpringBoot集成](#springboot集成)
- [生产者示例](#生产者示例)
- [消费者示例](#消费者示例)
- [事务消息](#事务消息)
- [顺序消息](#顺序消息)
- [延迟消息](#延迟消息)
- [批量消息](#批量消息)
- [死信队列](#死信队列)
- [消息持久化](#消息持久化)
- [负载均衡](#负载均衡)
- [消息过滤](#消息过滤)
- [最佳实践](#最佳实践)

## 简介

RocketMQ是阿里巴巴开源的一个分布式消息和流数据平台，具有低延迟、高并发、高可用、高可靠等特性。它广泛应用于电商、金融、物流、游戏等行业的异步通信、应用解耦、流量削峰等场景。

### 主要特性
- **高吞吐量**：单机支持10万级消息吞吐
- **低延迟**：毫秒级消息投递
- **高可用**：支持主从架构，故障自动切换
- **分布式事务**：支持分布式事务消息
- **顺序消息**：支持全局顺序和分区顺序
- **延迟消息**：支持定时投递
- **消息回溯**：支持按时间或位点回溯消息

## 核心概念

### 1. 消息模型
- **Producer**：消息生产者，负责产生消息
- **Consumer**：消息消费者，负责消费消息
- **Broker**：消息存储服务器，负责存储和转发消息
- **NameServer**：路由注册中心，负责路由发现

### 2. 消息类型
- **普通消息**：异步发送，不保证顺序
- **顺序消息**：保证消息按顺序消费
- **事务消息**：支持分布式事务
- **延迟消息**：支持定时投递
- **批量消息**：支持批量发送和消费

### 3. 消息模式
- **集群消费**：同组消费者平均分配消息
- **广播消费**：同组消费者都收到所有消息

## 架构设计

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Producer  │    │  Producer  │    │  Producer  │
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │
      └──────────────────┼──────────────────┘
                         │
              ┌──────────┴──────────┐
              │     NameServer      │
              │   (路由注册中心)     │
              └──────────┬──────────┘
                         │
      ┌──────────────────┼──────────────────┐
      │                  │                  │
┌─────▼───────┐    ┌─────▼───────┐    ┌─────▼───────┐
│   Broker    │    │   Broker    │    │   Broker    │
│  (Master)   │    │  (Master)   │    │  (Master)   │
└─────┬───────┘    └─────┬───────┘    └─────┬───────┘
      │                  │                  │
┌─────▼───────┐    ┌─────▼───────┐    ┌─────▼───────┐
│   Broker    │    │   Broker    │    │   Broker    │
│  (Slave)    │    │  (Slave)    │    │  (Slave)    │
└─────────────┘    └─────────────┘    └─────────────┘
      │                  │                  │
      └──────────────────┼──────────────────┘
                         │
      ┌──────────────────┼──────────────────┐
      │                  │                  │
┌─────▼───────┐    ┌─────▼───────┐    ┌─────▼───────┐
│  Consumer   │    │  Consumer   │    │  Consumer   │
│   Group1    │    │   Group2    │    │   Group3    │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 安装部署

### 1. 环境要求
- JDK 1.8+
- Maven 3.6+
- 4GB+ 内存

### 2. 下载安装
```bash
# 下载RocketMQ
wget https://archive.apache.org/dist/rocketmq/4.9.7/rocketmq-all-4.9.7-bin-release.zip

# 解压
unzip rocketmq-all-4.9.7-bin-release.zip
cd rocketmq-4.9.7

# 启动NameServer
nohup sh bin/mqnamesrv &

# 启动Broker
nohup sh bin/mqbroker -n localhost:9876 &
```

### 3. 验证安装
```bash
# 查看进程
ps -ef | grep rocketmq

# 查看日志
tail -f ~/logs/rocketmqlogs/namesrv.log
tail -f ~/logs/rocketmqlogs/broker.log
```

## SpringBoot集成

### 1. Maven依赖
```xml
<dependency>
    <groupId>org.apache.rocketmq</groupId>
    <artifactId>rocketmq-spring-boot-starter</artifactId>
    <version>2.2.3</version>
</dependency>

<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
```

### 2. 配置文件
```yaml
# application.yml
rocketmq:
  name-server: localhost:9876
  producer:
    group: my-producer-group
    send-message-timeout: 3000
    retry-times-when-send-failed: 2
    retry-times-when-send-async-failed: 2
  consumer:
    group: my-consumer-group
    pull-batch-size: 10
    consume-timeout: 15
    max-reconsume-times: 3

spring:
  application:
    name: rocketmq-demo
```

## 生产者示例

### 1. 基础生产者
```java
package com.example.rocketmq.producer;

import org.apache.rocketmq.spring.core.RocketMQTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Component;

@Component
public class MessageProducer {
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    /**
     * 发送同步消息
     */
    public void sendSyncMessage(String topic, String message) {
        rocketMQTemplate.syncSend(topic, message);
    }
    
    /**
     * 发送异步消息
     */
    public void sendAsyncMessage(String topic, String message) {
        rocketMQTemplate.asyncSend(topic, message, (sendResult, throwable) -> {
            if (throwable != null) {
                System.err.println("消息发送失败: " + throwable.getMessage());
            } else {
                System.out.println("消息发送成功: " + sendResult.getMsgId());
            }
        });
    }
    
    /**
     * 发送单向消息
     */
    public void sendOneWayMessage(String topic, String message) {
        rocketMQTemplate.sendOneWay(topic, message);
    }
}
```

### 2. 消息对象生产者
```java
package com.example.rocketmq.producer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.core.RocketMQTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
public class OrderMessageProducer {
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    /**
     * 发送订单消息
     */
    public void sendOrderMessage(OrderMessage orderMessage) {
        rocketMQTemplate.syncSend("order-topic", orderMessage);
    }
    
    /**
     * 发送延迟消息
     */
    public void sendDelayMessage(OrderMessage orderMessage, int delayLevel) {
        rocketMQTemplate.syncSend("order-delay-topic", 
            MessageBuilder.withPayload(orderMessage)
                .setHeader("DELAY_LEVEL", delayLevel)
                .build());
    }
}
```

### 3. 消息模型
```java
package com.example.rocketmq.model;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

public class OrderMessage implements Serializable {
    
    private static final long serialVersionUID = 1L;
    
    private String orderId;
    private String userId;
    private String productId;
    private BigDecimal amount;
    private LocalDateTime createTime;
    private String status;
    
    // 构造函数
    public OrderMessage() {}
    
    public OrderMessage(String orderId, String userId, String productId, BigDecimal amount) {
        this.orderId = orderId;
        this.userId = userId;
        this.productId = productId;
        this.amount = amount;
        this.createTime = LocalDateTime.now();
        this.status = "PENDING";
    }
    
    // Getter和Setter方法
    public String getOrderId() { return orderId; }
    public void setOrderId(String orderId) { this.orderId = orderId; }
    
    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }
    
    public String getProductId() { return productId; }
    public void setProductId(String productId) { this.productId = productId; }
    
    public BigDecimal getAmount() { return amount; }
    public void setAmount(BigDecimal amount) { this.amount = amount; }
    
    public LocalDateTime getCreateTime() { return createTime; }
    public void setCreateTime(LocalDateTime createTime) { this.createTime = createTime; }
    
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    
    @Override
    public String toString() {
        return "OrderMessage{" +
                "orderId='" + orderId + '\'' +
                ", userId='" + userId + '\'' +
                ", productId='" + productId + '\'' +
                ", amount=" + amount +
                ", createTime=" + createTime +
                ", status='" + status + '\'' +
                '}';
    }
}
```

## 消费者示例

### 1. 基础消费者
```java
package com.example.rocketmq.consumer;

import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
import org.apache.rocketmq.spring.core.RocketMQListener;
import org.springframework.stereotype.Component;

@Component
@RocketMQMessageListener(
    topic = "order-topic",
    consumerGroup = "order-consumer-group"
)
public class OrderMessageConsumer implements RocketMQListener<String> {
    
    @Override
    public void onMessage(String message) {
        System.out.println("收到订单消息: " + message);
        // 处理订单逻辑
        processOrder(message);
    }
    
    private void processOrder(String message) {
        // 模拟订单处理
        try {
            Thread.sleep(100);
            System.out.println("订单处理完成: " + message);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

### 2. 对象消息消费者
```java
package com.example.rocketmq.consumer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
import org.apache.rocketmq.spring.core.RocketMQListener;
import org.springframework.stereotype.Component;

@Component
@RocketMQMessageListener(
    topic = "order-topic",
    consumerGroup = "order-object-consumer-group"
)
public class OrderObjectConsumer implements RocketMQListener<OrderMessage> {
    
    @Override
    public void onMessage(OrderMessage orderMessage) {
        System.out.println("收到订单对象消息: " + orderMessage);
        
        // 根据订单状态处理
        switch (orderMessage.getStatus()) {
            case "PENDING":
                processPendingOrder(orderMessage);
                break;
            case "PAID":
                processPaidOrder(orderMessage);
                break;
            case "SHIPPED":
                processShippedOrder(orderMessage);
                break;
            default:
                System.out.println("未知订单状态: " + orderMessage.getStatus());
        }
    }
    
    private void processPendingOrder(OrderMessage order) {
        System.out.println("处理待支付订单: " + order.getOrderId());
        // 发送支付提醒等逻辑
    }
    
    private void processPaidOrder(OrderMessage order) {
        System.out.println("处理已支付订单: " + order.getOrderId());
        // 发货等逻辑
    }
    
    private void processShippedOrder(OrderMessage order) {
        System.out.println("处理已发货订单: " + order.getOrderId());
        // 物流跟踪等逻辑
    }
}
```

### 3. 批量消息消费者
```java
package com.example.rocketmq.consumer;

import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
import org.apache.rocketmq.spring.core.RocketMQListener;
import org.springframework.stereotype.Component;
import java.util.List;

@Component
@RocketMQMessageListener(
    topic = "batch-topic",
    consumerGroup = "batch-consumer-group"
)
public class BatchMessageConsumer implements RocketMQListener<List<String>> {
    
    @Override
    public void onMessage(List<String> messages) {
        System.out.println("收到批量消息，数量: " + messages.size());
        
        for (String message : messages) {
            System.out.println("处理消息: " + message);
            processMessage(message);
        }
    }
    
    private void processMessage(String message) {
        // 批量处理逻辑
        try {
            Thread.sleep(50);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
```

## 事务消息

### 1. 事务消息生产者
```java
package com.example.rocketmq.producer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.core.RocketMQTemplate;
import org.apache.rocketmq.spring.support.RocketMQHeaders;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Component;

@Component
public class TransactionMessageProducer {
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    /**
     * 发送事务消息
     */
    public void sendTransactionMessage(OrderMessage orderMessage) {
        Message<OrderMessage> message = MessageBuilder
            .withPayload(orderMessage)
            .setHeader(RocketMQHeaders.TRANSACTION_ID, orderMessage.getOrderId())
            .build();
            
        rocketMQTemplate.sendMessageInTransaction("transaction-topic", message, orderMessage);
    }
}
```

### 2. 事务消息监听器
```java
package com.example.rocketmq.listener;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.annotation.RocketMQTransactionListener;
import org.apache.rocketmq.spring.core.RocketMQLocalTransactionListener;
import org.apache.rocketmq.spring.core.RocketMQLocalTransactionState;
import org.springframework.messaging.Message;
import org.springframework.stereotype.Component;

@Component
@RocketMQTransactionListener
public class TransactionListenerImpl implements RocketMQLocalTransactionListener {
    
    @Override
    public RocketMQLocalTransactionState executeLocalTransaction(Message msg, Object arg) {
        try {
            OrderMessage orderMessage = (OrderMessage) arg;
            System.out.println("执行本地事务: " + orderMessage.getOrderId());
            
            // 模拟本地事务执行
            boolean success = executeLocalBusiness(orderMessage);
            
            if (success) {
                return RocketMQLocalTransactionState.COMMIT;
            } else {
                return RocketMQLocalTransactionState.ROLLBACK;
            }
        } catch (Exception e) {
            System.err.println("本地事务执行异常: " + e.getMessage());
            return RocketMQLocalTransactionState.ROLLBACK;
        }
    }
    
    @Override
    public RocketMQLocalTransactionState checkLocalTransaction(MessageExt msg) {
        try {
            String orderId = msg.getTransactionId();
            System.out.println("检查本地事务状态: " + orderId);
            
            // 检查本地事务状态
            boolean exists = checkLocalTransactionStatus(orderId);
            
            if (exists) {
                return RocketMQLocalTransactionState.COMMIT;
            } else {
                return RocketMQLocalTransactionState.ROLLBACK;
            }
        } catch (Exception e) {
            System.err.println("检查本地事务异常: " + e.getMessage());
            return RocketMQLocalTransactionState.UNKNOWN;
        }
    }
    
    private boolean executeLocalBusiness(OrderMessage orderMessage) {
        // 模拟业务逻辑执行
        return Math.random() > 0.3; // 70%成功率
    }
    
    private boolean checkLocalTransactionStatus(String orderId) {
        // 模拟检查本地事务状态
        return Math.random() > 0.5;
    }
}
```

## 顺序消息

### 1. 顺序消息生产者
```java
package com.example.rocketmq.producer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.core.RocketMQTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import java.util.List;

@Component
public class OrderSequenceProducer {
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    /**
     * 发送顺序消息
     */
    public void sendOrderSequenceMessage(OrderMessage orderMessage) {
        // 使用订单ID作为消息队列选择器，确保同一订单的消息进入同一队列
        rocketMQTemplate.syncSendOrderly(
            "order-sequence-topic", 
            orderMessage, 
            orderMessage.getOrderId()
        );
    }
    
    /**
     * 发送批量顺序消息
     */
    public void sendBatchOrderSequenceMessage(List<OrderMessage> orderMessages) {
        for (OrderMessage orderMessage : orderMessages) {
            sendOrderSequenceMessage(orderMessage);
        }
    }
}
```

### 2. 顺序消息消费者
```java
package com.example.rocketmq.consumer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
import org.apache.rocketmq.spring.core.RocketMQListener;
import org.springframework.stereotype.Component;

@Component
@RocketMQMessageListener(
    topic = "order-sequence-topic",
    consumerGroup = "order-sequence-consumer-group",
    consumeMode = ConsumeMode.ORDERLY // 顺序消费模式
)
public class OrderSequenceConsumer implements RocketMQListener<OrderMessage> {
    
    @Override
    public void onMessage(OrderMessage orderMessage) {
        System.out.println("顺序消费订单消息: " + orderMessage.getOrderId());
        
        // 按顺序处理订单状态变更
        processOrderSequence(orderMessage);
    }
    
    private void processOrderSequence(OrderMessage order) {
        switch (order.getStatus()) {
            case "PENDING":
                System.out.println("步骤1: 订单创建 - " + order.getOrderId());
                break;
            case "PAID":
                System.out.println("步骤2: 订单支付 - " + order.getOrderId());
                break;
            case "SHIPPED":
                System.out.println("步骤3: 订单发货 - " + order.getOrderId());
                break;
            case "DELIVERED":
                System.out.println("步骤4: 订单送达 - " + order.getOrderId());
                break;
        }
    }
}
```

## 延迟消息

### 1. 延迟消息生产者
```java
package com.example.rocketmq.producer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.core.RocketMQTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
public class DelayMessageProducer {
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    /**
     * 发送延迟消息
     * 延迟级别: 1s 5s 10s 30s 1m 2m 3m 4m 5m 6m 7m 8m 9m 10m 20m 30m 1h 2h
     */
    public void sendDelayMessage(OrderMessage orderMessage, int delayLevel) {
        rocketMQTemplate.syncSend(
            "order-delay-topic", 
            orderMessage, 
            3000, // 超时时间
            delayLevel
        );
    }
    
    /**
     * 发送订单超时提醒
     */
    public void sendOrderTimeoutReminder(OrderMessage orderMessage) {
        // 15分钟后提醒
        sendDelayMessage(orderMessage, 9); // 对应10分钟
    }
    
    /**
     * 发送订单自动取消
     */
    public void sendOrderAutoCancel(OrderMessage orderMessage) {
        // 30分钟后自动取消
        sendDelayMessage(orderMessage, 16); // 对应30分钟
    }
}
```

### 2. 延迟消息消费者
```java
package com.example.rocketmq.consumer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
import org.apache.rocketmq.spring.core.RocketMQListener;
import org.springframework.stereotype.Component;

@Component
@RocketMQMessageListener(
    topic = "order-delay-topic",
    consumerGroup = "order-delay-consumer-group"
)
public class DelayMessageConsumer implements RocketMQListener<OrderMessage> {
    
    @Override
    public void onMessage(OrderMessage orderMessage) {
        System.out.println("收到延迟消息: " + orderMessage.getOrderId());
        
        // 处理延迟消息逻辑
        processDelayMessage(orderMessage);
    }
    
    private void processDelayMessage(OrderMessage order) {
        // 根据业务逻辑处理延迟消息
        if (order.getStatus().equals("PENDING")) {
            System.out.println("订单超时提醒: " + order.getOrderId());
            sendTimeoutNotification(order);
        }
    }
    
    private void sendTimeoutNotification(OrderMessage order) {
        // 发送超时通知
        System.out.println("发送订单超时通知给用户: " + order.getUserId());
    }
}
```

## 批量消息

### 1. 批量消息生产者
```java
package com.example.rocketmq.producer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.core.RocketMQTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import java.util.List;

@Component
public class BatchMessageProducer {
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    /**
     * 发送批量消息
     */
    public void sendBatchMessage(List<OrderMessage> orderMessages) {
        if (orderMessages.size() > 32) {
            // RocketMQ限制单次批量消息不超过32条
            throw new IllegalArgumentException("批量消息数量不能超过32条");
        }
        
        rocketMQTemplate.syncSend("batch-topic", orderMessages);
    }
    
    /**
     * 分批发送大量消息
     */
    public void sendLargeBatchMessage(List<OrderMessage> orderMessages) {
        int batchSize = 32;
        for (int i = 0; i < orderMessages.size(); i += batchSize) {
            int endIndex = Math.min(i + batchSize, orderMessages.size());
            List<OrderMessage> batch = orderMessages.subList(i, endIndex);
            sendBatchMessage(batch);
        }
    }
}
```

## 死信队列

### 1. 死信队列概念
死信队列（Dead Letter Queue，DLQ）用于存储无法被正常消费的消息。当消息消费失败次数超过最大重试次数时，消息会被发送到死信队列。

### 2. 死信队列配置
```yaml
# application.yml
rocketmq:
  consumer:
    group: order-consumer-group
    max-reconsume-times: 3  # 最大重试次数
    # 死信队列主题，格式：%DLQ%消费者组名
    # 例如：%DLQ%order-consumer-group
```

### 3. 死信队列消费者
```java
package com.example.rocketmq.consumer;

import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
import org.apache.rocketmq.spring.core.RocketMQListener;
import org.springframework.stereotype.Component;

@Component
@RocketMQMessageListener(
    topic = "%DLQ%order-consumer-group",  // 死信队列主题
    consumerGroup = "dlq-consumer-group"
)
public class DeadLetterQueueConsumer implements RocketMQListener<String> {
    
    @Override
    public void onMessage(String message) {
        System.out.println("收到死信消息: " + message);
        
        // 处理死信消息
        processDeadLetterMessage(message);
    }
    
    private void processDeadLetterMessage(String message) {
        // 记录死信消息日志
        logDeadLetterMessage(message);
        
        // 发送告警通知
        sendAlertNotification(message);
        
        // 尝试手动处理或人工介入
        manualProcessMessage(message);
    }
    
    private void logDeadLetterMessage(String message) {
        System.err.println("死信消息记录: " + message);
        // 可以写入数据库或日志文件
    }
    
    private void sendAlertNotification(String message) {
        System.out.println("发送死信消息告警通知");
        // 发送邮件、短信或钉钉通知
    }
    
    private void manualProcessMessage(String message) {
        System.out.println("尝试手动处理死信消息");
        // 实现手动处理逻辑
    }
}
```

### 4. 死信消息重试机制
```java
package com.example.rocketmq.consumer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
import org.apache.rocketmq.spring.core.RocketMQListener;
import org.springframework.stereotype.Component;

@Component
@RocketMQMessageListener(
    topic = "order-topic",
    consumerGroup = "order-retry-consumer-group",
    maxReconsumeTimes = 3  // 最大重试3次
)
public class RetryMessageConsumer implements RocketMQListener<OrderMessage> {
    
    @Override
    public void onMessage(OrderMessage orderMessage) {
        try {
            System.out.println("处理订单消息: " + orderMessage.getOrderId());
            processOrderWithRetry(orderMessage);
        } catch (Exception e) {
            System.err.println("消息处理异常，将进行重试: " + e.getMessage());
            // 抛出异常会触发重试机制
            throw e;
        }
    }
    
    private void processOrderWithRetry(OrderMessage order) {
        // 模拟可能失败的业务逻辑
        if (Math.random() < 0.3) {
            throw new RuntimeException("模拟业务处理失败");
        }
        
        System.out.println("订单处理成功: " + order.getOrderId());
    }
}
```

## 消息持久化

### 1. 消息持久化机制
RocketMQ支持两种消息持久化方式：
- **同步刷盘**：消息写入内存后立即刷盘到磁盘，保证消息不丢失
- **异步刷盘**：消息写入内存后异步刷盘，性能更好但可能丢失少量消息

### 2. Broker配置
```properties
# broker.conf
# 刷盘方式：SYNC_FLUSH(同步刷盘) / ASYNC_FLUSH(异步刷盘)
flushDiskType=SYNC_FLUSH

# 刷盘间隔(毫秒)
flushIntervalCommitLog=500

# 刷盘间隔(毫秒)
flushIntervalConsumeQueue=1000

# 刷盘间隔(毫秒)
flushIntervalFlushMap=1000
```

### 3. 生产者持久化配置
```java
package com.example.rocketmq.producer;

import org.apache.rocketmq.spring.core.RocketMQTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Component
public class PersistentMessageProducer {
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    /**
     * 发送持久化消息
     */
    public void sendPersistentMessage(String topic, String message) {
        // 默认情况下，RocketMQ所有消息都是持久化的
        rocketMQTemplate.syncSend(topic, message);
    }
    
    /**
     * 发送高可靠性消息（同步刷盘）
     */
    public void sendHighReliabilityMessage(String topic, String message) {
        // 通过消息属性设置
        rocketMQTemplate.syncSend(topic, 
            MessageBuilder.withPayload(message)
                .setHeader("FLUSH_DISK_TYPE", "SYNC_FLUSH")
                .build());
    }
}
```

### 4. 消费者持久化配置
```java
package com.example.rocketmq.consumer;

import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
import org.apache.rocketmq.spring.core.RocketMQListener;
import org.springframework.stereotype.Component;

@Component
@RocketMQMessageListener(
    topic = "persistent-topic",
    consumerGroup = "persistent-consumer-group",
    consumeMode = ConsumeMode.CONCURRENTLY,  // 并发消费
    messageModel = MessageModel.CLUSTERING   // 集群模式
)
public class PersistentMessageConsumer implements RocketMQListener<String> {
    
    @Override
    public void onMessage(String message) {
        System.out.println("消费持久化消息: " + message);
        
        // 处理消息
        processMessage(message);
        
        // 手动确认消费完成
        acknowledgeMessage(message);
    }
    
    private void processMessage(String message) {
        try {
            // 模拟消息处理
            Thread.sleep(100);
            System.out.println("消息处理完成: " + message);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
    
    private void acknowledgeMessage(String message) {
        // 记录消费确认日志
        System.out.println("消息消费确认: " + message);
    }
}
```

## 负载均衡

### 1. 生产者负载均衡
RocketMQ生产者支持多种负载均衡策略：

```java
package com.example.rocketmq.producer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.core.RocketMQTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import java.util.List;

@Component
public class LoadBalancedProducer {
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    /**
     * 轮询负载均衡（默认）
     */
    public void sendMessageWithRoundRobin(String topic, OrderMessage message) {
        // 默认使用轮询策略，消息会均匀分布到各个队列
        rocketMQTemplate.syncSend(topic, message);
    }
    
    /**
     * 哈希负载均衡
     */
    public void sendMessageWithHash(String topic, OrderMessage message) {
        // 使用订单ID作为哈希键，相同订单的消息会进入同一队列
        rocketMQTemplate.syncSendOrderly(topic, message, message.getOrderId());
    }
    
    /**
     * 随机负载均衡
     */
    public void sendMessageWithRandom(String topic, OrderMessage message) {
        // 随机选择队列发送
        rocketMQTemplate.syncSend(topic, message);
    }
    
    /**
     * 批量消息负载均衡
     */
    public void sendBatchMessageWithLoadBalance(String topic, List<OrderMessage> messages) {
        // 批量消息会自动进行负载均衡
        rocketMQTemplate.syncSend(topic, messages);
    }
}
```

### 2. 消费者负载均衡
消费者支持集群消费和广播消费两种模式：

```java
package com.example.rocketmq.consumer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
import org.apache.rocketmq.spring.core.RocketMQListener;
import org.springframework.stereotype.Component;

@Component
@RocketMQMessageListener(
    topic = "load-balance-topic",
    consumerGroup = "load-balance-consumer-group",
    consumeMode = ConsumeMode.CONCURRENTLY,  // 并发消费
    messageModel = MessageModel.CLUSTERING    // 集群模式，消息在消费者间负载均衡
)
public class LoadBalancedConsumer implements RocketMQListener<OrderMessage> {
    
    @Override
    public void onMessage(OrderMessage message) {
        System.out.println("消费者[" + getConsumerId() + "] 收到消息: " + message.getOrderId());
        processMessage(message);
    }
    
    private void processMessage(OrderMessage message) {
        try {
            // 模拟消息处理
            Thread.sleep(200);
            System.out.println("消息处理完成: " + message.getOrderId());
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
    
    private String getConsumerId() {
        return Thread.currentThread().getName();
    }
}

/**
 * 广播消费模式 - 所有消费者都会收到所有消息
 */
@Component
@RocketMQMessageListener(
    topic = "broadcast-topic",
    consumerGroup = "broadcast-consumer-group",
    consumeMode = ConsumeMode.CONCURRENTLY,
    messageModel = MessageModel.BROADCASTING  // 广播模式
)
public class BroadcastConsumer implements RocketMQListener<OrderMessage> {
    
    @Override
    public void onMessage(OrderMessage message) {
        System.out.println("广播消费者[" + getConsumerId() + "] 收到消息: " + message.getOrderId());
        processBroadcastMessage(message);
    }
    
    private void processBroadcastMessage(OrderMessage message) {
        // 处理广播消息
        System.out.println("处理广播消息: " + message.getOrderId());
    }
    
    private String getConsumerId() {
        return Thread.currentThread().getName();
    }
}
```

### 3. 队列选择策略
```java
package com.example.rocketmq.strategy;

import org.springframework.stereotype.Component;
import java.util.List;

@Component
public class QueueSelectionStrategy {
    
    /**
     * 轮询选择策略
     */
    public int selectQueueByRoundRobin(int currentIndex, int queueCount) {
        return (currentIndex + 1) % queueCount;
    }
    
    /**
     * 哈希选择策略
     */
    public int selectQueueByHash(String key, int queueCount) {
        int hashCode = key.hashCode();
        return Math.abs(hashCode) % queueCount;
    }
    
    /**
     * 随机选择策略
     */
    public int selectQueueByRandom(int queueCount) {
        return (int) (Math.random() * queueCount);
    }
    
    /**
     * 权重选择策略
     */
    public int selectQueueByWeight(List<Double> weights) {
        double totalWeight = weights.stream().mapToDouble(Double::doubleValue).sum();
        double random = Math.random() * totalWeight;
        
        double currentWeight = 0;
        for (int i = 0; i < weights.size(); i++) {
            currentWeight += weights.get(i);
            if (random <= currentWeight) {
                return i;
            }
        }
        return weights.size() - 1;
    }
}
```

### 4. 负载均衡监控
```java
package com.example.rocketmq.monitor;

import org.springframework.stereotype.Component;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Component
public class LoadBalanceMonitor {
    
    private final ConcurrentHashMap<String, AtomicLong> queueMessageCount = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, AtomicLong> consumerMessageCount = new ConcurrentHashMap<>();
    
    /**
     * 记录队列消息数量
     */
    public void recordQueueMessage(String queueName) {
        queueMessageCount.computeIfAbsent(queueName, k -> new AtomicLong(0)).incrementAndGet();
    }
    
    /**
     * 记录消费者消息数量
     */
    public void recordConsumerMessage(String consumerName) {
        consumerMessageCount.computeIfAbsent(consumerName, k -> new AtomicLong(0)).incrementAndGet();
    }
    
    /**
     * 获取负载均衡统计
     */
    public void printLoadBalanceStats() {
        System.out.println("=== 负载均衡统计 ===");
        
        System.out.println("队列消息分布:");
        queueMessageCount.forEach((queue, count) -> 
            System.out.println("  " + queue + ": " + count.get() + " 条消息"));
        
        System.out.println("消费者消息分布:");
        consumerMessageCount.forEach((consumer, count) -> 
            System.out.println("  " + consumer + ": " + count.get() + " 条消息"));
        
        // 计算负载均衡度
        calculateLoadBalanceDegree();
    }
    
    private void calculateLoadBalanceDegree() {
        if (queueMessageCount.isEmpty()) return;
        
        long totalMessages = queueMessageCount.values().stream()
            .mapToLong(AtomicLong::get).sum();
        long avgMessages = totalMessages / queueMessageCount.size();
        
        double variance = queueMessageCount.values().stream()
            .mapToDouble(count -> Math.pow(count.get() - avgMessages, 2))
            .average().orElse(0.0);
        
        double standardDeviation = Math.sqrt(variance);
        double coefficientOfVariation = standardDeviation / avgMessages;
        
        System.out.println("负载均衡度: " + String.format("%.2f%%", (1 - coefficientOfVariation) * 100));
    }
}
```

## 消息过滤

### 1. SQL表达式过滤
```java
package com.example.rocketmq.consumer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
import org.apache.rocketmq.spring.core.RocketMQListener;
import org.springframework.stereotype.Component;

@Component
@RocketMQMessageListener(
    topic = "filter-topic",
    consumerGroup = "filter-consumer-group",
    sql = "amount > 100 AND status = 'PENDING'"  // SQL表达式过滤
)
public class SQLFilterConsumer implements RocketMQListener<OrderMessage> {
    
    @Override
    public void onMessage(OrderMessage message) {
        System.out.println("收到过滤后的消息: " + message);
        processFilteredMessage(message);
    }
    
    private void processFilteredMessage(OrderMessage message) {
        // 处理过滤后的消息
        System.out.println("处理高价值待支付订单: " + message.getOrderId());
    }
}
```

### 2. Tag过滤
```java
package com.example.rocketmq.producer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.core.RocketMQTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.stereotype.Component;

@Component
public class TagFilterProducer {
    
    @Autowired
    private RocketMQTemplate rocketMQTemplate;
    
    /**
     * 发送带Tag的消息
     */
    public void sendMessageWithTag(OrderMessage message, String tag) {
        rocketMQTemplate.syncSend(
            "tag-topic:" + tag,  // 使用冒号分隔Topic和Tag
            message
        );
    }
    
    /**
     * 发送不同状态的消息
     */
    public void sendOrderStatusMessage(OrderMessage message) {
        String tag = message.getStatus().toLowerCase();
        sendMessageWithTag(message, tag);
    }
}
```

## 最佳实践

### 1. 消息幂等性
```java
package com.example.rocketmq.util;

import org.springframework.stereotype.Component;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class MessageIdempotentChecker {
    
    private final ConcurrentHashMap<String, Boolean> processedMessages = new ConcurrentHashMap<>();
    
    /**
     * 检查消息是否已处理
     */
    public boolean isProcessed(String messageId) {
        return processedMessages.containsKey(messageId);
    }
    
    /**
     * 标记消息已处理
     */
    public void markProcessed(String messageId) {
        processedMessages.put(messageId, true);
    }
    
    /**
     * 清理过期消息ID（建议定期清理）
     */
    public void cleanExpiredMessages() {
        // 实现清理逻辑，避免内存泄漏
        if (processedMessages.size() > 10000) {
            processedMessages.clear();
        }
    }
}
```

### 2. 消息重试机制
```java
package com.example.rocketmq.consumer;

import com.example.rocketmq.model.OrderMessage;
import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
import org.apache.rocketmq.spring.core.RocketMQListener;
import org.springframework.stereotype.Component;

@Component
@RocketMQMessageListener(
    topic = "order-topic",
    consumerGroup = "order-retry-consumer-group",
    maxReconsumeTimes = 3 // 最大重试次数
)
public class RetryMessageConsumer implements RocketMQListener<OrderMessage> {
    
    @Override
    public void onMessage(OrderMessage orderMessage) {
        try {
            System.out.println("处理订单消息: " + orderMessage.getOrderId());
            processOrderWithRetry(orderMessage);
        } catch (Exception e) {
            System.err.println("消息处理异常: " + e.getMessage());
            // 抛出异常会触发重试机制
            throw e;
        }
    }
    
    private void processOrderWithRetry(OrderMessage order) {
        // 模拟可能失败的业务逻辑
        if (Math.random() < 0.3) {
            throw new RuntimeException("模拟业务处理失败");
        }
        
        System.out.println("订单处理成功: " + order.getOrderId());
    }
}
```

### 3. 消息监控
```java
package com.example.rocketmq.monitor;

import org.springframework.stereotype.Component;
import java.util.concurrent.atomic.AtomicLong;

@Component
public class MessageMonitor {
    
    private final AtomicLong totalMessages = new AtomicLong(0);
    private final AtomicLong successMessages = new AtomicLong(0);
    private final AtomicLong failedMessages = new AtomicLong(0);
    
    public void recordMessage() {
        totalMessages.incrementAndGet();
    }
    
    public void recordSuccess() {
        successMessages.incrementAndGet();
    }
    
    public void recordFailure() {
        failedMessages.incrementAndGet();
    }
    
    public void printStatistics() {
        System.out.println("=== 消息统计 ===");
        System.out.println("总消息数: " + totalMessages.get());
        System.out.println("成功消息数: " + successMessages.get());
        System.out.println("失败消息数: " + failedMessages.get());
        System.out.println("成功率: " + 
            String.format("%.2f%%", 
                (double) successMessages.get() / totalMessages.get() * 100));
    }
}
```

## 总结

RocketMQ是一个功能强大、性能优异的分布式消息队列系统。通过SpringBoot集成，我们可以轻松实现各种消息场景：

1. **基础消息**：异步通信、应用解耦
2. **事务消息**：分布式事务一致性
3. **顺序消息**：保证消息顺序消费
4. **延迟消息**：定时任务、超时处理
5. **批量消息**：提高消息处理效率

在实际使用中，需要注意：
- 消息幂等性处理
- 异常重试机制
- 消息监控和告警
- 性能调优和容量规划

通过合理使用这些特性，可以构建高可用、高性能的分布式系统。