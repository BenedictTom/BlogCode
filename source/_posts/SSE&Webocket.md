---
title: Sse && Websocket
main_color: "#1881a2ff"
categories: http
tags:
  - http
cover: https://free.picui.cn/free/2026/03/28/69c74fc2598a0.png
---

# SSE 与 WebSocket 完整指南

## 目录
- [概述](#概述)
- [Server-Sent Events (SSE)](#server-sent-events-sse)
  - [底层原理](#sse-底层原理)
  - [Java 实现](#sse-java-实现)
- [WebSocket](#websocket)
  - [底层原理](#websocket-底层原理)
  - [Java 实现](#websocket-java-实现)
- [对比分析](#对比分析)
- [选择建议](#选择建议)

## 概述

在传统的 HTTP 协议中，客户端发起请求，服务器响应后连接即关闭。这种请求-响应模式无法满足实时双向通信的需求。为了解决这个问题，出现了两种主要的实时通信方案：

1. **Server-Sent Events (SSE)**：服务器向客户端推送数据
2. **WebSocket**：全双工通信协议

两者各有优势，适用于不同的场景。

---

## Server-Sent Events (SSE)

Server-Sent Events 是一种允许服务器向客户端推送数据的技术。它是基于 HTTP 的单向通信协议，服务器可以主动向客户端发送数据。

### SSE 底层原理

#### HTTP 协议基础

SSE 基于标准的 HTTP 协议，使用 HTTP 长连接机制。关键在于以下几点：

1. **Content-Type**: 必须设置为 `text/event-stream`
2. **Cache-Control**: 设置为 `no-cache`，防止缓存
3. **Connection**: 保持连接打开，使用 `keep-alive`
4. **数据传输格式**: 遵循 EventSource 规范

#### 数据传输格式

SSE 使用纯文本格式传输数据，每条消息格式如下：

```
event: messageType
id: 12345
data: {"key": "value"}

```

字段说明：
- `event`: 事件类型（可选）
- `id`: 消息ID（可选），用于断线重连
- `data`: 实际数据（必需），可以多行
- 空行：分隔不同消息

#### 连接建立过程

```
1. 客户端发送 HTTP GET 请求
   GET /events HTTP/1.1
   Accept: text/event-stream
   Cache-Control: no-cache

2. 服务器响应，保持连接打开
   HTTP/1.1 200 OK
   Content-Type: text/event-stream
   Cache-Control: no-cache
   Connection: keep-alive

3. 服务器持续发送数据
   data: message 1

   data: message 2

4. 客户端通过 EventSource API 接收
```

#### 心跳机制

为了保持连接活跃，服务器会定期发送注释行（以 `:` 开头的行）：

```
: keep-alive comment

```

#### 断线重连

客户端使用 `id` 字段实现断线重连：
1. 服务器发送消息时带上 `id`
2. 客户端记录最后接收的 `id`
3. 断线重连时，客户端通过 `Last-Event-ID` 请求头发送上次的 `id`
4. 服务器从该 `id` 之后继续发送

### SSE Java 实现

#### Spring Boot 实现

##### Maven 依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
```

##### 控制器实现

```java
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

@RestController
public class SseController {

    private final ScheduledExecutorService executor = Executors.newScheduledThreadPool(10);

    /**
     * SSE 端点
     * @return SseEmitter
     */
    @GetMapping(value = "/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamEvents() {
        SseEmitter emitter = new SseEmitter(Long.MAX_VALUE); // 永不超时
        
        // 启动任务，定期发送数据
        executor.scheduleAtFixedRate(() -> {
            try {
                // 发送数据
                SseEmitter.SseEventBuilder event = SseEmitter.event()
                    .name("message")  // 事件类型
                    .id(String.valueOf(System.currentTimeMillis()))  // 消息ID
                    .data("Hello from server - " + System.currentTimeMillis());  // 数据
                
                emitter.send(event);
            } catch (IOException e) {
                emitter.completeWithError(e);
            }
        }, 0, 1, TimeUnit.SECONDS);
        
        // 连接完成时的回调
        emitter.onCompletion(() -> {
            System.out.println("SSE connection completed");
        });
        
        emitter.onError((ex) -> {
            System.out.println("SSE error: " + ex.getMessage());
        });
        
        emitter.onTimeout(() -> {
            System.out.println("SSE timeout");
        });
        
        return emitter;
    }

    /**
     * 支持断线重连的 SSE
     */
    @GetMapping(value = "/events/reconnect", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter streamEventsWithReconnect(@RequestParam(required = false) String lastEventId) {
        SseEmitter emitter = new SseEmitter(Long.MAX_VALUE);
        
        // 如果有 lastEventId，从该位置继续
        long startId = lastEventId != null ? Long.parseLong(lastEventId) : 0;
        
        executor.scheduleAtFixedRate(() -> {
            try {
                long currentId = System.currentTimeMillis();
                
                if (currentId > startId) {
                    SseEmitter.SseEventBuilder event = SseEmitter.event()
                        .name("message")
                        .id(String.valueOf(currentId))
                        .data("Data: " + currentId);
                    
                    emitter.send(event);
                }
            } catch (IOException e) {
                emitter.completeWithError(e);
            }
        }, 0, 1, TimeUnit.SECONDS);
        
        return emitter;
    }
}
```

##### 使用 SseEventSink（Spring 6+）

```java
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.ResponseBodyEmitter;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.concurrent.CompletableFuture;

@RestController
public class SseEventSinkController {

    @GetMapping(value = "/events/v2", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public ResponseBodyEmitter streamEventsV2() {
        ResponseBodyEmitter emitter = new ResponseBodyEmitter(Long.MAX_VALUE);
        
        CompletableFuture.runAsync(() -> {
            try {
                for (int i = 0; i < 100; i++) {
                    emitter.send(SseEmitter.event()
                        .name("message")
                        .data("Message " + i));
                    
                    Thread.sleep(1000);
                }
                emitter.complete();
            } catch (Exception e) {
                emitter.completeWithError(e);
            }
        });
        
        return emitter;
    }
}
```

##### 客户端实现（JavaScript）

```javascript
// 创建 EventSource 连接
const eventSource = new EventSource('http://localhost:8080/events');

// 监听默认 message 事件
eventSource.onmessage = function(event) {
    console.log('Received:', event.data);
    console.log('Event ID:', event.lastEventId);
};

// 监听自定义事件
eventSource.addEventListener('message', function(event) {
    console.log('Custom event:', event.data);
});

// 错误处理
eventSource.onerror = function(event) {
    console.error('SSE error:', event);
    // 客户端会自动重连
};

// 手动关闭连接
// eventSource.close();
```

---

## WebSocket

WebSocket 是一种在单个 TCP 连接上进行全双工通信的协议。它允许服务器和客户端同时发送数据，实现了真正的双向通信。

### WebSocket 底层原理

#### 协议升级过程

WebSocket 连接通过 HTTP 握手建立，然后升级为 WebSocket 协议：

```
1. 客户端发送升级请求
   GET /ws HTTP/1.1
   Host: example.com
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
   Sec-WebSocket-Version: 13
   Origin: http://example.com

2. 服务器响应升级
   HTTP/1.1 101 Switching Protocols
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=

3. 连接升级完成，开始 WebSocket 数据传输
```

#### 数据帧格式

WebSocket 使用帧（Frame）格式传输数据，每帧包含以下部分：

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+-------------------------------+
```

字段说明：
- **FIN**: 是否为最后一帧
- **RSV**: 保留字段
- **Opcode**: 操作码（0x1=文本，0x2=二进制，0x8=关闭，0x9=Ping，0xA=Pong）
- **MASK**: 是否掩码（客户端必须设置，服务器不设置）
- **Payload len**: 负载长度
- **Masking-key**: 掩码密钥（如果 MASK=1）
- **Payload data**: 实际数据

#### 心跳机制（Ping/Pong）

WebSocket 使用 Ping/Pong 帧保持连接活跃：
- **Ping 帧**（opcode 0x9）：服务器或客户端发送
- **Pong 帧**（opcode 0xA）：收到 Ping 后必须回复 Pong

#### 连接关闭

正常关闭流程：
1. 一方发送关闭帧（opcode 0x8）
2. 另一方收到后也发送关闭帧
3. 关闭 TCP 连接

关闭帧可包含关闭状态码和原因。

### WebSocket Java 实现

#### Spring Boot 实现

##### Maven 依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-websocket</artifactId>
</dependency>
```

##### WebSocket 配置类

```java
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    /**
     * 配置消息代理
     */
    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        // 启用简单消息代理，用于向客户端推送消息
        // 客户端订阅的地址前缀
        config.enableSimpleBroker("/topic", "/queue");
        
        // 客户端向服务器发送消息的地址前缀
        config.setApplicationDestinationPrefixes("/app");
        
        // 用户目标前缀（点对点消息）
        config.setUserDestinationPrefix("/user");
    }

    /**
     * 注册 STOMP 端点
     */
    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // 允许跨域
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("*")
                .withSockJS();  // 支持 SockJS 降级
        
        // 不适用 SockJS 的端点
        registry.addEndpoint("/ws-native")
                .setAllowedOriginPatterns("*");
    }
}
```

##### 消息控制器

```java
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
public class WebSocketController {

    private final SimpMessagingTemplate messagingTemplate;

    public WebSocketController(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    /**
     * 接收客户端消息并广播
     */
    @MessageMapping("/chat")
    @SendTo("/topic/messages")
    public ChatMessage handleMessage(ChatMessage message) {
        System.out.println("Received: " + message.getContent());
        return message;
    }

    /**
     * 服务器主动推送消息
     */
    @GetMapping("/send")
    public void sendMessage(@RequestParam String content) {
        ChatMessage message = new ChatMessage("Server", content);
        // 广播到 /topic/messages
        messagingTemplate.convertAndSend("/topic/messages", message);
    }

    /**
     * 点对点消息
     */
    @MessageMapping("/private")
    public void sendPrivateMessage(PrivateMessage message) {
        // 发送给特定用户
        messagingTemplate.convertAndSendToUser(
            message.getToUser(),
            "/queue/messages",
            message
        );
    }
}
```

##### 原生 WebSocket 实现（不使用 STOMP）

```java
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.io.IOException;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class CustomWebSocketHandler extends TextWebSocketHandler {

    private final ConcurrentHashMap<String, WebSocketSession> sessions = new ConcurrentHashMap<>();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        sessions.put(session.getId(), session);
        System.out.println("WebSocket connection established: " + session.getId());
        
        // 发送欢迎消息
        try {
            session.sendMessage(new TextMessage("Welcome! Your ID: " + session.getId()));
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
        System.out.println("Received from " + session.getId() + ": " + payload);
        
        // 回显消息
        session.sendMessage(new TextMessage("Echo: " + payload));
        
        // 广播给所有连接的客户端
        broadcast("User " + session.getId() + " said: " + payload);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessions.remove(session.getId());
        System.out.println("WebSocket connection closed: " + session.getId());
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) {
        System.out.println("WebSocket error: " + exception.getMessage());
        sessions.remove(session.getId());
    }

    /**
     * 广播消息给所有连接的客户端
     */
    public void broadcast(String message) {
        sessions.values().forEach(session -> {
            try {
                session.sendMessage(new TextMessage(message));
            } catch (IOException e) {
                e.printStackTrace();
            }
        });
    }
}
```

##### WebSocket 端点配置

```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    @Autowired
    private CustomWebSocketHandler customWebSocketHandler;

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(customWebSocketHandler, "/ws-custom")
                .setAllowedOriginPatterns("*");
    }
}
```

##### 客户端实现（JavaScript）

```javascript
// 使用原生 WebSocket
const ws = new WebSocket('ws://localhost:8080/ws-custom');

ws.onopen = function(event) {
    console.log('WebSocket connection opened');
    ws.send('Hello Server!');
};

ws.onmessage = function(event) {
    console.log('Received:', event.data);
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};

ws.onclose = function(event) {
    console.log('WebSocket connection closed');
};

// 使用 STOMP（需要引入 stomp.js 库）
const socket = new SockJS('http://localhost:8080/ws');
const stompClient = Stomp.over(socket);

stompClient.connect({}, function(frame) {
    console.log('Connected: ' + frame);
    
    // 订阅广播消息
    stompClient.subscribe('/topic/messages', function(message) {
        console.log('Received:', JSON.parse(message.body));
    });
    
    // 发送消息
    stompClient.send("/app/chat", {}, JSON.stringify({
        from: 'User',
        content: 'Hello!'
    }));
});

function disconnect() {
    if (stompClient !== null) {
        stompClient.disconnect();
    }
}
```

---

## 对比分析

### 协议层面对比

| 特性 | SSE | WebSocket |
|------|-----|-----------|
| **协议基础** | HTTP | 独立协议（基于 TCP） |
| **通信方向** | 单向（服务器→客户端） | 双向 |
| **连接方式** | HTTP 长连接 | WebSocket 协议 |
| **数据格式** | 纯文本（EventSource 格式） | 二进制或文本（Frame 格式） |
| **浏览器支持** | 较好（现代浏览器） | 很好（IE10+） |
| **自动重连** | 原生支持 | 需要手动实现 |

### 技术实现对比

| 特性 | SSE | WebSocket |
|------|-----|-----------|
| **实现复杂度** | 简单 | 中等 |
| **服务器资源** | 每个连接占用一个 HTTP 连接 | 每个连接占用一个 TCP 连接 |
| **消息大小** | 理论上无限制，但受 HTTP 缓冲区影响 | 理论上无限制 |
| **心跳机制** | 注释行保持连接 | Ping/Pong 帧 |
| **错误处理** | 自动重连（带 lastEventId） | 需要手动处理 |

### 使用场景对比

#### SSE 适用场景

1. **服务器推送通知**
   - 实时新闻推送
   - 系统通知
   - 日志流输出

2. **单向数据流**
   - 股票价格更新
   - 进度条更新
   - 实时统计信息

3. **简单实现场景**
   - 不需要双向通信
   - 需要自动重连
   - 防火墙友好（HTTP）

#### WebSocket 适用场景

1. **双向实时通信**
   - 聊天应用
   - 在线游戏
   - 协作编辑

2. **低延迟需求**
   - 高频交易
   - 实时监控
   - 视频通话信令

3. **复杂交互**
   - 需要客户端频繁发送数据
   - 需要双向流式传输

### 性能对比

#### 连接开销

- **SSE**: 基于 HTTP，每个连接保持一个 HTTP 连接，开销相对较大
- **WebSocket**: 升级后是轻量级协议，帧头开销小（2-14 字节）

#### 消息大小

- **SSE**: 适合小到中等大小的消息
- **WebSocket**: 支持任意大小的消息，支持二进制

#### 并发连接

- **SSE**: 受限于 HTTP 连接数（浏览器通常限制 6-10 个同域连接）
- **WebSocket**: 不受 HTTP 连接数限制，但受服务器资源限制

### 代码复杂度对比

#### SSE 代码示例

```java
// 服务器端
@GetMapping(value = "/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public SseEmitter streamEvents() {
    SseEmitter emitter = new SseEmitter(Long.MAX_VALUE);
    executor.scheduleAtFixedRate(() -> {
        emitter.send(SseEmitter.event().data("Hello"));
    }, 0, 1, TimeUnit.SECONDS);
    return emitter;
}

// 客户端（JavaScript）
const eventSource = new EventSource('/events');
eventSource.onmessage = (e) => console.log(e.data);
```

#### WebSocket 代码示例

```java
// 服务器端（使用 STOMP）
@MessageMapping("/chat")
@SendTo("/topic/messages")
public Message handleMessage(Message msg) {
    return msg;
}

// 客户端（JavaScript）
const stompClient = Stomp.over(new SockJS('/ws'));
stompClient.connect({}, () => {
    stompClient.subscribe('/topic/messages', (msg) => {
        console.log(msg.body);
    });
    stompClient.send('/app/chat', {}, JSON.stringify({...}));
});
```

---

## 选择建议

### 选择 SSE 的情况

1. ✅ 只需要服务器向客户端推送数据
2. ✅ 需要简单的实现，不想处理复杂协议
3. ✅ 需要自动重连机制
4. ✅ 防火墙环境严格（只允许 HTTP）
5. ✅ 数据量不大，主要是文本数据
6. ✅ 需要利用现有的 HTTP 基础设施

### 选择 WebSocket 的情况

1. ✅ 需要双向实时通信
2. ✅ 需要低延迟和高性能
3. ✅ 需要传输二进制数据
4. ✅ 客户端需要频繁发送数据
5. ✅ 需要实现复杂的消息路由（使用 STOMP）
6. ✅ 需要点对点通信

### 混合使用

在实际项目中，可以同时使用两者：

- **SSE**: 用于服务器主动推送通知、日志流等
- **WebSocket**: 用于聊天、实时协作等需要双向通信的场景

### 总结

- **SSE** 更适合单向推送场景，实现简单，适合通知、日志、进度更新等
- **WebSocket** 更适合双向通信场景，性能更好，适合聊天、游戏、实时协作等

选择时主要考虑：
1. 通信方向（单向 vs 双向）
2. 实现复杂度要求
3. 性能要求
4. 浏览器兼容性
5. 防火墙限制

根据具体业务需求选择最合适的技术方案。
