---
title: 定时任务_XXL-JOB
main_color: "#0e9428ff"
categories: 定时任务
tags:
  - 定时任务
cover: https://ts3.tc.mm.bing.net/th/id/OIP-C.sYtwxiHeJ1yJoq_6NQkDZAHaDh?rs=1&pid=ImgDetMain&o=7&rm=3
---

## XXL-JOB 
一个分布式任务调度平台，它能够帮助开发者轻松实现任务的调度、监控和管理。该系统由许雪里（XXL）开源贡献，并且在 GitHub 上获得了广泛的关注和使用。以下是 XXL-JOB 的一些主要特点：

1. **简单易用**：提供WEB界面用于管理调度任务，无需编写额外代码即可快速上手。
2. **分布式部署**：支持集群模式部署，提升系统的高可用性和稳定性。
3. **弹性扩展**：可以方便地添加执行器节点来应对更多的任务需求。
4. **丰富的任务类型支持**：包括GLUE模式(Java)、BEAN模式(Spring bean)、POJO模式等，适应不同的开发场景。
5. **失败处理机制**：提供了重试机制、告警机制等功能，确保任务能够稳定运行。
6. **日志追踪**：对于每次任务执行的结果，都可以通过WEB界面查看详细日志，便于问题排查。
7. **依赖调度**：支持任务间的依赖调度，满足复杂的业务场景需求。

XXL-JOB适用于需要定时执行某些任务的场景，比如数据同步、报表生成、邮件发送等。它的出现大大简化了任务调度的复杂度，提升了开发效率.

## 核心组件

### 调度中心（Admin）

XXL-JOB 的 **调度中心（Admin）** 是整个 XXL-JOB 分布式任务调度平台的核心组件。它负责任务的统一管理、调度、监控和日志记录等核心功能，是整个系统的大脑。你可以把它理解为一个任务调度的“指挥中心”。

---

## 🧠 一、调度中心的核心功能

调度中心的主要职责包括以下几个方面：

| 功能 | 描述 |
|------|------|
| **任务管理** | 提供 Web 界面，支持任务的新增、修改、删除、暂停、启动等操作。 |
| **调度管理** | 按照设定的 Cron 表达式定时触发任务，并将任务分发给对应的执行器执行。 |
| **执行器管理** | 管理注册到调度中心的执行器（Executor），包括执行器的注册、心跳检测、下线管理等。 |
| **日志查看** | 可以查看每个任务的执行日志，便于问题排查和调试。 |
| **失败告警** | 支持配置失败告警机制（如邮件、钉钉等），任务失败后自动通知相关人员。 |
| **调度日志** | 记录每次调度的详细信息，包括调度时间、执行结果、执行耗时等。 |
| **分片广播** | 支持将一个任务分片到多个执行器上并行执行，提高执行效率。 |
| **路由策略** | 支持多种路由策略（如轮询、故障转移、一致性哈希等），决定任务由哪个执行器执行。 |
| **任务依赖** | 支持设置任务之间的依赖关系（如任务A执行完成后再执行任务B）。 |

---

## 🧩 二、调度中心的技术架构

XXL-JOB 调度中心是一个基于 **Spring Boot + MyBatis + MySQL + Quartz** 的 Web 应用。

### 1. 技术栈：
- **Spring Boot**：用于构建 Web 应用。
- **MyBatis**：用于数据库操作。
- **MySQL**：存储任务信息、执行器信息、调度日志等。
- **Quartz**：用于任务的定时调度（底层基于 Quartz 框架）。
- **HTML + Bootstrap + jQuery**：前端页面使用简单的 HTML 页面 + Bootstrap 框架构建，没有使用复杂的前端框架（如 Vue/React）。

### 2. 核心模块：
- `xxl-job-admin`：调度中心项目，包含 Web 页面和调度逻辑。
- `xxl-job-core`：公共核心模块，定义了调度中心与执行器之间的通信协议。

---

## 🛠️ 三、调度中心的工作流程

1. **执行器注册**：
   - 执行器启动后，会向调度中心发送注册请求。
   - 调度中心记录执行器的 IP、端口、AppName 等信息。

2. **任务调度**：
   - 调度中心根据 Cron 表达式触发任务。
   - 根据任务配置的执行器（AppName）和路由策略选择一个执行器节点。
   - 通过 HTTP 请求调用执行器的接口，触发任务执行。

3. **任务执行**：
   - 执行器接收到请求后，执行本地任务逻辑。
   - 执行完成后，将执行结果（成功/失败）返回给调度中心。

4. **日志记录与监控**：
   - 调度中心记录每次调度的详细信息。
   - 用户可以通过 Web 界面查看调度日志、执行日志、失败告警等信息。

---

## 📦 四、调度中心的部署方式

调度中心是一个独立的 Java Web 应用，可以部署为：

### 1. **传统部署（Tomcat/Jetty）**
- 将 `xxl-job-admin` 编译成 WAR 包，部署到 Tomcat 或其他 Web 容器中。

### 2. **Spring Boot 启动**
- 直接运行 `XxlJobAdminApplication.java`，启动调度中心。

### 3. **Docker 部署**
- 可以使用社区提供的 Docker 镜像或自定义 Dockerfile 构建镜像。
- 示例命令：
  ```bash
  docker run -e PARAMS="--server.port=8080 --xxl.job.admin.addresses=http://127.0.0.1:8080/xxl-job-admin" -p 8080:8080 -d xxl-job-admin
  ```

---

## 🗃️ 五、调度中心的数据结构（MySQL 表结构）

调度中心依赖 MySQL 存储以下核心信息：

| 表名 | 说明 |
|------|------|
| `xxl_job_info` | 存储任务的基本信息（任务描述、调度时间、执行器、路由策略等） |
| `xxl_job_log` | 存储每次任务调度的执行日志 |
| `xxl_job_registry` | 存储执行器的注册信息（AppName、IP、端口等） |
| `xxl_job_group` | 存储执行器分组信息（执行器所在的机器组） |
| `xxl_job_qz_*` | Quartz 调度框架的系统表（用于任务调度） |

---

## 🌐 六、调度中心的通信机制

调度中心与执行器之间通过 **HTTP + JSON** 协议进行通信：

| 通信方向 | 说明 |
|----------|------|
| 调度中心 → 执行器 | 发送任务调度请求（POST 请求） |
| 执行器 → 调度中心 | 注册执行器信息、上报执行结果 |

---

## 🧪 七、调度中心的可视化界面

调度中心提供了一个简洁的 Web 管理界面，用户可以通过浏览器访问：

```
http://调度中心IP:8080/xxl-job-admin
默认账号：admin / 123456
```

界面功能包括：

- 任务管理（新增、编辑、删除）
- 执行器管理（注册、查看状态）
- 日志查看（调度日志、执行日志）
- 调度日志统计
- 失败告警配置
- 分片广播设置
- 路由策略选择

---

## ✅ 八、调度中心的高可用部署

调度中心本身是一个单点服务，为了提升可用性，可以结合以下方式实现高可用：

1. **数据库共享**：多个调度中心实例共享同一个 MySQL 数据库。
2. **Nginx 负载均衡**：通过 Nginx 做负载均衡，对外提供统一入口。
3. **Keepalived + VIP**：在物理机部署中，使用 Keepalived 实现虚拟 IP，实现故障切换。

> ⚠️ 注意：调度中心本身不支持集群部署（因为 Quartz 是本地调度），如果需要高可用，建议使用外部调度系统或使用其他调度平台（如 Elastic-Job、Quartz 集群模式）。

---

## 📚 九、总结

| 项目 | 说明 |
|------|------|
| 名称 | XXL-JOB 调度中心（Admin） |
| 作用 | 统一管理任务、调度、执行器注册、日志监控 |
| 技术栈 | Spring Boot + MyBatis + MySQL + Quartz |
| 部署方式 | WAR / Spring Boot / Docker |
| 数据存储 | MySQL |
| 通信方式 | HTTP + JSON |
| 可视化 | Web 界面（支持任务管理、日志查看等） |
| 高可用 | 单节点部署，可通过 Nginx 做负载均衡 |

---


### 执行器（Executor）

当然可以！XXL-JOB 的 **执行器（Executor）** 是任务的实际执行者，是整个调度系统中非常重要的一环。你可以把它理解为任务的“执行机器”，它接收来自调度中心（Admin）的任务指令，执行本地定义的任务逻辑，并将执行结果反馈给调度中心。

---

## 🧠 一、执行器的作用

执行器的主要职责包括：

| 功能 | 说明 |
|------|------|
| **接收任务调度请求** | 调度中心通过 HTTP 请求通知执行器执行某个任务 |
| **执行任务逻辑** | 执行器根据任务类型（BEAN/GLUE/POJO）调用本地方法或脚本 |
| **返回执行结果** | 执行完成后，将执行状态（成功/失败）和日志返回给调度中心 |
| **注册自身信息** | 启动时向调度中心注册自己的 IP、端口、AppName 等信息 |
| **心跳检测** | 定期向调度中心发送心跳，保持注册状态 |
| **日志记录** | 本地记录任务执行日志，供调度中心查看 |
| **支持多种任务模式** | 支持 BEAN 模式、GLUE 模式（动态脚本）、POJO 模式等 |

---

## 🧩 二、执行器的结构与技术栈

执行器本质上是一个 **Spring Boot 应用程序**，可以独立部署，也可以集成到已有的 Java 服务中。

### 1. 技术栈：
- **Spring Boot**：用于构建执行器应用
- **Netty / HTTP**：用于接收调度中心的请求
- **xxl-job-core**：核心通信模块，封装了与调度中心交互的逻辑
- **Java 反射机制**：用于动态调用任务方法
- **Groovy / Shell / Python 等**：支持 GLUE 模式，执行动态脚本

### 2. 核心模块：
- `xxl-job-executor`：执行器主模块
- `xxl-job-core`：公共核心模块，定义通信协议、任务接口等

---

## 🛠️ 三、执行器的启动与注册流程

执行器启动时会做以下几件事：

1. **加载配置**：
   - 包括调度中心地址、执行器名称（AppName）、端口、日志路径等
   - 示例配置（`application.properties`）：
     ```properties
     xxl.job.admin.addresses=http://127.0.0.1:8080/xxl-job-admin
     xxl.job.executor.appname=order-service-executor
     xxl.job.executor.port=9999
     xxl.job.executor.logpath=/data/applogs/xxl-job/jobhandler
     xxl.job.executor.logretentiondays=30
     ```

2. **注册到调度中心**：
   - 执行器启动后，会向调度中心发送注册请求，包含：
     - AppName（执行器名称）
     - IP 地址
     - 端口号
   - 调度中心将执行器信息存储在 `xxl_job_registry` 表中

3. **启动 Netty 或 HTTP 服务**：
   - 监听来自调度中心的请求（默认端口 9999）

4. **定时发送心跳**：
   - 每隔一段时间（默认30秒）向调度中心发送心跳，保持注册状态

---

## 🧪 四、执行器如何执行任务

当调度中心触发一个任务时，执行器会经历以下流程：

1. **接收 HTTP 请求**：
   - 调度中心通过 HTTP 请求调用执行器的 `/api/trigger` 接口
   - 请求中包含任务 ID、参数、执行器信息等

2. **解析任务信息**：
   - 根据任务 ID 从本地获取任务处理器（JobHandler）

3. **执行任务逻辑**：
   - 支持三种任务模式：
     - **BEAN 模式**：Spring Bean 注解方式，适合集成到 Spring Boot 项目中
     - **GLUE 模式**：动态脚本（Groovy、Shell、Python 等）
     - **POJO 模式**：普通 Java 类 + 注解方式定义任务

4. **返回执行结果**：
   - 将执行结果（成功/失败）通过 HTTP 返回给调度中心
   - 若任务执行失败，可配置重试机制

---

## 📦 五、执行器的部署方式

执行器可以灵活部署，支持以下方式：

| 部署方式 | 说明 |
|----------|------|
| **独立部署** | 单独作为一个 Spring Boot 项目部署，适合专门执行任务的场景 |
| **集成到业务系统** | 将执行器集成到已有的 Java 服务中，如订单系统、支付系统等 |
| **集群部署** | 多个执行器节点部署，提高并发能力和可用性 |
| **Docker 部署** | 使用 Docker 容器化部署执行器，便于管理与扩展 |

---

## 🧩 六、执行器支持的任务模式详解

### 1. **BEAN 模式（推荐）**
- 通过 `@Component` 注解将任务类注册为 Spring Bean
- 使用 `@XxlJob("jobHandlerName")` 注解定义任务方法
- 示例代码：
  ```java
  @Component
  public class DemoJobHandler {
  
      @XxlJob("demoJobHandler")
      public void demoJobHandler() throws Exception {
          System.out.println("执行任务逻辑...");
      }
  }
  ```

### 2. **GLUE 模式（动态脚本）**
- 支持 Groovy、Shell、Python、PHP、NodeJS 等脚本语言
- 适用于任务逻辑经常变动的场景
- 示例（Shell 脚本）：
  ```bash
  #!/bin/bash
  echo "执行Shell任务"
  ```

### 3. **POJO 模式**
- 不依赖 Spring，通过普通 Java 类 + 注解实现任务
- 适合非 Spring 项目使用

---

## 📊 七、执行器的监控与日志

执行器会将任务执行日志写入本地文件系统，路径由 `xxl.job.executor.logpath` 配置指定。调度中心可以通过 HTTP 接口读取这些日志并展示在 Web 界面中。

日志结构示例：

```
/data/applogs/xxl-job/jobhandler/2025-07-23/123456.log
```

日志内容包括：

- 任务开始时间
- 任务执行日志
- 任务结束时间
- 执行状态（成功/失败）
- 异常堆栈信息（如有）

---

## ✅ 八、执行器的高可用与负载均衡

执行器可以部署多个节点，形成一个执行器集群。调度中心在调度任务时，会根据配置的 **路由策略**（如轮询、故障转移、一致性哈希等）选择一个执行器节点来执行任务。

常见的路由策略：

| 策略 | 说明 |
|------|------|
| 故障转移 | 优先选择在线节点，失败后自动切换 |
| 轮询 | 按顺序轮流选择执行器节点 |
| 一致性哈希 | 同一个任务总是分发到同一个执行器 |
| 最近最久未使用 | 选择最近最少使用的节点 |
| 首次失败后重试 | 首次失败后自动重试另一个节点 |

---

## 📚 九、总结

| 项目 | 说明 |
|------|------|
| 名称 | XXL-JOB 执行器（Executor） |
| 作用 | 接收调度中心的任务请求，执行本地任务逻辑 |
| 技术栈 | Spring Boot + xxl-job-core |
| 部署方式 | 独立部署、集成部署、Docker、集群部署 |
| 通信方式 | HTTP + JSON |
| 任务模式 | BEAN 模式、GLUE 模式、POJO 模式 |
| 注册机制 | 启动时注册到调度中心，定期发送心跳 |
| 日志记录 | 本地日志文件，供调度中心查看 |
| 负载均衡 | 支持多种路由策略，执行器可集群部署 |

---

## 分片机制

XXL-JOB 的**分片机制**是一种强大的功能，特别适用于需要在多个执行器节点上并行处理大数据量或耗时任务的场景。通过分片广播，可以将一个大任务拆分成多个小任务，并分配给不同的执行器节点并行处理，从而提高任务执行效率。

### 分片机制概述

分片机制的核心思想是将一个任务分割成多个“分片”，每个分片对应一部分数据或逻辑，然后将这些分片分配给不同的执行器节点来并行处理。这样不仅可以加速任务执行，还可以避免单个节点成为性能瓶颈。

---

## 🧠 分片机制的工作原理

1. **任务定义**：在调度中心定义一个支持分片的任务，并指定总的分片数（`shardCount`）。
   
2. **分片参数传递**：
   - 调度中心会为每个分片生成唯一的 `shardIndex` 和 `shardTotal` 参数。
   - `shardIndex`: 当前分片索引（从0开始）
   - `shardTotal`: 总分片数

3. **分片分配**：当调度中心触发任务时，它会根据以下规则分配分片给可用的执行器节点：
   - 如果有多个执行器节点注册到调度中心，调度中心会按照一定的策略（如轮询、故障转移等）将分片分配给不同的执行器。
   - 每个执行器只处理分配给它的那部分分片。

4. **任务执行**：执行器接收到分片任务后，根据传入的 `shardIndex` 和 `shardTotal` 参数执行相应的逻辑。例如，如果任务是处理一批数据，可以根据这两个参数来确定当前执行器应该处理的数据范围。

5. **结果汇总**：各个执行器节点完成任务后，将执行结果返回给调度中心。你可以选择是否需要进一步汇总这些结果。

---

## 📝 分片任务的配置与实现

### 1. **任务配置**

在调度中心定义一个分片任务时，你需要设置以下关键参数：

- **Cron 表达式**：任务的调度时间
- **JobHandler**：任务处理器名称
- **Shard Count**：总分片数
- **Shard Param**：分片参数（可选）

### 2. **任务处理器代码示例**

下面是一个简单的 Java 示例，展示了如何编写一个支持分片的任务处理器：

```java
import com.xxl.job.core.biz.model.ReturnT;
import com.xxl.job.core.handler.IJobHandler;
import com.xxl.job.core.handler.annotation.XxlJob;
import org.springframework.stereotype.Component;

@Component
public class ShardingJobHandler extends IJobHandler {

    @XxlJob("shardingJobHandler")
    public ReturnT<String> execute(String param) throws Exception {
        // 获取分片参数
        int shardIndex = this.getShardIndex(); // 当前分片索引
        int shardTotal = this.getShardTotal(); // 总分片数
        
        // 根据分片参数执行任务逻辑
        System.out.println("分片总数: " + shardTotal + ", 当前分片: " + shardIndex);
        
        // 示例：假设我们要处理一批用户数据，可以根据分片索引来确定要处理的数据范围
        // 处理逻辑...
        
        return SUCCESS;
    }
}
```

在这个例子中，`getShardIndex()` 和 `getShardTotal()` 方法分别用于获取当前执行器的分片索引和总分片数。

### 3. **路由策略**

调度中心提供了多种路由策略，用于决定如何将分片分配给不同的执行器节点：

- **轮询模式**：按顺序轮流分配分片给不同的执行器节点。
- **故障转移模式**：优先选择在线节点，若失败则自动切换至其他节点。
- **一致性哈希模式**：同一个分片总是分配给同一个执行器节点，保证任务的连续性。
- **最近最久未使用模式**：选择最近最少使用的执行器节点。
- **首台可用模式**：选择第一个可用的执行器节点。

你可以根据实际需求选择合适的路由策略。

---

## 🛠️ 分片机制的应用场景

分片机制非常适合以下几种场景：

1. **大数据处理**：如批量导入大量数据、数据清洗、数据迁移等任务。
2. **分布式计算**：如 MapReduce 类型的任务，需要将任务拆分为多个子任务并行处理。
3. **定时任务**：某些定时任务需要快速处理大量数据或复杂逻辑，可以通过分片机制加快处理速度。

### 示例：批量更新用户状态

假设你有一个包含百万条记录的用户表，现在需要定期检查并更新所有用户的某种状态（比如会员到期）。为了加快处理速度，可以将这个任务拆分为多个分片，每个分片处理一部分用户数据。

- **总分片数**：10
- **每个分片处理的数据范围**：可以根据用户 ID 或其他字段进行划分
- **执行器节点数**：5

在这种情况下，调度中心会将10个分片分配给5个执行器节点，并行处理数据更新任务，大大提高了处理效率。

---

## 路由策略
XXL-JOB 的 **路由策略（Routing Strategy）** 是调度中心在分发任务时，**选择执行器节点** 的一种规则。它是实现任务调度灵活性和高可用性的关键机制之一。

---

## 🧠 一、什么是路由策略？

在 XXL-JOB 中，一个任务可以绑定一个或多个执行器节点（Executor）。当任务被触发时，调度中心需要决定将任务分发给哪一个执行器节点去执行。这个过程就叫做“路由”，而决定路由方式的规则就是 **路由策略**。

路由策略决定了任务的执行节点，影响着系统的负载均衡、容错能力、任务执行效率等。

---

## 📌 二、支持的路由策略（官方内置）

XXL-JOB 提供了多种路由策略，你可以在调度中心的任务配置页面中选择：

| 路由策略 | 中文名称 | 说明 |
|----------|----------|------|
| `FIRST` | 首个 | 选择第一个可用的执行器节点 |
| `LAST` | 最后一个 | 选择最后一个可用的执行器节点 |
| `ROUND` | 轮询 | 按顺序轮流选择执行器节点 |
| `RANDOM` | 随机 | 随机选择一个可用的执行器节点 |
| `CONSISTENT_HASH` | 一致性哈希 | 相同任务总是分配到同一个执行器节点 |
| `LEAST_FREQUENTLY_USED` | 最不经常使用 | 优先选择执行次数最少的执行器节点 |
| `LEAST_RECENTLY_USED` | 最近最久未使用 | 优先选择最近最少使用的执行器节点 |
| `FAILOVER` | 故障转移 | 首次失败后自动切换其他节点执行 |
| `BUSYOVER` | 忙碌转移 | 如果目标执行器忙碌（正在执行任务），则自动切换其他节点 |
| `SHARDING_BROADCAST` | 分片广播 | 所有执行器节点都执行该任务（用于分片任务） |

---

## 🧩 三、路由策略详解

### 1. `FIRST`（首个）
- 总是选择第一个注册的执行器节点。
- 适用于执行器节点只有一个的情况。
- **优点**：简单、快速。
- **缺点**：无法负载均衡。

### 2. `LAST`（最后一个）
- 总是选择最后一个注册的执行器节点。
- 与 `FIRST` 类似，只是方向相反。

### 3. `ROUND`（轮询）
- 按顺序依次选择执行器节点。
- **优点**：负载均衡效果较好。
- **缺点**：不能保证每个节点负载完全一致。

### 4. `RANDOM`（随机）
- 随机选择一个可用的执行器节点。
- **优点**：实现简单，负载较均衡。
- **缺点**：随机性可能导致某些节点负载偏高。

### 5. `CONSISTENT_HASH`（一致性哈希）
- 根据任务 ID（JobId）或参数进行哈希计算，将任务固定分配到某一个执行器节点。
- **优点**：保证相同任务总是分配到同一个节点，适合需要“状态一致性”的任务。
- **缺点**：新增或删除节点会影响部分任务的分配。

### 6. `LEAST_FREQUENTLY_USED`（最不经常使用）
- 优先选择执行次数最少的执行器节点。
- **优点**：更智能地实现负载均衡。
- **缺点**：需要维护执行次数统计。

### 7. `LEAST_RECENTLY_USED`（最近最久未使用）
- 优先选择最近最少使用的执行器节点。
- **优点**：避免某些节点长时间被使用，提升整体响应速度。
- **缺点**：逻辑略复杂。

### 8. `FAILOVER`（故障转移）
- 如果首次执行失败，会自动尝试切换到另一个执行器节点。
- **优点**：提高任务执行的可靠性。
- **缺点**：可能增加执行时间。

### 9. `BUSYOVER`（忙碌转移）
- 如果目标执行器正在执行任务，则自动切换到其他节点。
- **优点**：防止任务堆积。
- **缺点**：需要判断执行器是否空闲。

### 10. `SHARDING_BROADCAST`（分片广播）
- 所有执行器节点都执行该任务。
- 通常用于 **分片任务**，任务逻辑中根据 `shardIndex` 和 `shardTotal` 来区分数据处理范围。
- **优点**：充分利用所有执行器资源。
- **缺点**：如果任务不是分片任务，会导致重复执行。

---

## 🛠️ 四、如何选择合适的路由策略？

| 场景 | 推荐策略 |
|------|----------|
| 单执行器节点 | `FIRST` 或 `LAST` |
| 需要负载均衡 | `ROUND` 或 `RANDOM` |
| 需要一致性 | `CONSISTENT_HASH` |
| 任务失败重试 | `FAILOVER` |
| 分片任务 | `SHARDING_BROADCAST` |
| 任务对执行器有状态依赖 | `CONSISTENT_HASH` |
| 想避免执行器过载 | `BUSYOVER` |

---

## 📦 五、源码实现简析（可选）

在 XXL-JOB 的源码中，路由策略的实现位于：

```
com.xxl.job.admin.core.route.strategy.*
```

每个路由策略都是一个类，实现了 `ExecutorRouter` 接口：

```java
public interface ExecutorRouter {
    public ReturnT<String> route(TriggerParam triggerParam, List<String> addressList);
}
```

- `triggerParam`：任务触发参数，包含 JobId、分片信息等
- `addressList`：可用执行器地址列表
- 返回值：选中的执行器地址

例如 `ExecutorRouteRound` 类就是轮询策略的实现类。

---

## ✅ 六、总结

| 路由策略 | 适用场景 | 优点 | 缺点 |
|----------|----------|------|------|
| `FIRST` / `LAST` | 单节点 | 简单 | 无负载均衡 |
| `ROUND` | 多节点 | 负载均衡 | 分布不均 |
| `RANDOM` | 多节点 | 实现简单 | 随机性 |
| `CONSISTENT_HASH` | 状态一致性 | 一致性好 | 节点变化影响大 |
| `LEAST_FREQUENTLY_USED` | 负载均衡 | 更智能 | 需要统计 |
| `LEAST_RECENTLY_USED` | 均衡使用 | 避免过载 | 逻辑复杂 |
| `FAILOVER` | 容错 | 提高可靠性 | 增加时间 |
| `BUSYOVER` | 避免阻塞 | 防止堆积 | 判断逻辑 |
| `SHARDING_BROADCAST` | 分片任务 | 并行处理 | 重复执行风险 |

---


## 容器部署

```bash
docker pull xuxueli/xxl-job-admin:2.4.0
```



```sql
CREATE database if NOT EXISTS `xxl_job` default character set utf8mb4 collate utf8mb4_unicode_ci;
use `xxl_job`;
 
SET NAMES utf8mb4;
 
CREATE TABLE `xxl_job_info` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `job_group` int(11) NOT NULL COMMENT '执行器主键ID',
  `job_desc` varchar(255) NOT NULL,
  `add_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  `author` varchar(64) DEFAULT NULL COMMENT '作者',
  `alarm_email` varchar(255) DEFAULT NULL COMMENT '报警邮件',
  `schedule_type` varchar(50) NOT NULL DEFAULT 'NONE' COMMENT '调度类型',
  `schedule_conf` varchar(128) DEFAULT NULL COMMENT '调度配置，值含义取决于调度类型',
  `misfire_strategy` varchar(50) NOT NULL DEFAULT 'DO_NOTHING' COMMENT '调度过期策略',
  `executor_route_strategy` varchar(50) DEFAULT NULL COMMENT '执行器路由策略',
  `executor_handler` varchar(255) DEFAULT NULL COMMENT '执行器任务handler',
  `executor_param` varchar(512) DEFAULT NULL COMMENT '执行器任务参数',
  `executor_block_strategy` varchar(50) DEFAULT NULL COMMENT '阻塞处理策略',
  `executor_timeout` int(11) NOT NULL DEFAULT '0' COMMENT '任务执行超时时间，单位秒',
  `executor_fail_retry_count` int(11) NOT NULL DEFAULT '0' COMMENT '失败重试次数',
  `glue_type` varchar(50) NOT NULL COMMENT 'GLUE类型',
  `glue_source` mediumtext COMMENT 'GLUE源代码',
  `glue_remark` varchar(128) DEFAULT NULL COMMENT 'GLUE备注',
  `glue_updatetime` datetime DEFAULT NULL COMMENT 'GLUE更新时间',
  `child_jobid` varchar(255) DEFAULT NULL COMMENT '子任务ID，多个逗号分隔',
  `trigger_status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '调度状态：0-停止，1-运行',
  `trigger_last_time` bigint(13) NOT NULL DEFAULT '0' COMMENT '上次调度时间',
  `trigger_next_time` bigint(13) NOT NULL DEFAULT '0' COMMENT '下次调度时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
 
CREATE TABLE `xxl_job_log` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `job_group` int(11) NOT NULL COMMENT '执行器主键ID',
  `job_id` int(11) NOT NULL COMMENT '任务，主键ID',
  `executor_address` varchar(255) DEFAULT NULL COMMENT '执行器地址，本次执行的地址',
  `executor_handler` varchar(255) DEFAULT NULL COMMENT '执行器任务handler',
  `executor_param` varchar(512) DEFAULT NULL COMMENT '执行器任务参数',
  `executor_sharding_param` varchar(20) DEFAULT NULL COMMENT '执行器任务分片参数，格式如 1/2',
  `executor_fail_retry_count` int(11) NOT NULL DEFAULT '0' COMMENT '失败重试次数',
  `trigger_time` datetime DEFAULT NULL COMMENT '调度-时间',
  `trigger_code` int(11) NOT NULL COMMENT '调度-结果',
  `trigger_msg` text COMMENT '调度-日志',
  `handle_time` datetime DEFAULT NULL COMMENT '执行-时间',
  `handle_code` int(11) NOT NULL COMMENT '执行-状态',
  `handle_msg` text COMMENT '执行-日志',
  `alarm_status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '告警状态：0-默认、1-无需告警、2-告警成功、3-告警失败',
  PRIMARY KEY (`id`),
  KEY `I_trigger_time` (`trigger_time`),
  KEY `I_handle_code` (`handle_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
 
CREATE TABLE `xxl_job_log_report` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `trigger_day` datetime DEFAULT NULL COMMENT '调度-时间',
  `running_count` int(11) NOT NULL DEFAULT '0' COMMENT '运行中-日志数量',
  `suc_count` int(11) NOT NULL DEFAULT '0' COMMENT '执行成功-日志数量',
  `fail_count` int(11) NOT NULL DEFAULT '0' COMMENT '执行失败-日志数量',
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `i_trigger_day` (`trigger_day`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
 
CREATE TABLE `xxl_job_logglue` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `job_id` int(11) NOT NULL COMMENT '任务，主键ID',
  `glue_type` varchar(50) DEFAULT NULL COMMENT 'GLUE类型',
  `glue_source` mediumtext COMMENT 'GLUE源代码',
  `glue_remark` varchar(128) NOT NULL COMMENT 'GLUE备注',
  `add_time` datetime DEFAULT NULL,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
 
CREATE TABLE `xxl_job_registry` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `registry_group` varchar(50) NOT NULL,
  `registry_key` varchar(255) NOT NULL,
  `registry_value` varchar(255) NOT NULL,
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `i_g_k_v` (`registry_group`,`registry_key`,`registry_value`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
 
CREATE TABLE `xxl_job_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_name` varchar(64) NOT NULL COMMENT '执行器AppName',
  `title` varchar(12) NOT NULL COMMENT '执行器名称',
  `address_type` tinyint(4) NOT NULL DEFAULT '0' COMMENT '执行器地址类型：0=自动注册、1=手动录入',
  `address_list` text COMMENT '执行器地址列表，多地址逗号分隔',
  `update_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
 
CREATE TABLE `xxl_job_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL COMMENT '账号',
  `password` varchar(50) NOT NULL COMMENT '密码',
  `role` tinyint(4) NOT NULL COMMENT '角色：0-普通用户、1-管理员',
  `permission` varchar(255) DEFAULT NULL COMMENT '权限：执行器ID列表，多个逗号分割',
  PRIMARY KEY (`id`),
  UNIQUE KEY `i_username` (`username`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
 
CREATE TABLE `xxl_job_lock` (
  `lock_name` varchar(50) NOT NULL COMMENT '锁名称',
  PRIMARY KEY (`lock_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
 
INSERT INTO `xxl_job_group`(`id`, `app_name`, `title`, `address_type`, `address_list`, `update_time`) VALUES (1, 'xxl-job-executor-sample', '示例执行器', 0, NULL, '2018-11-03 22:21:31' );
INSERT INTO `xxl_job_info`(`id`, `job_group`, `job_desc`, `add_time`, `update_time`, `author`, `alarm_email`, `schedule_type`, `schedule_conf`, `misfire_strategy`, `executor_route_strategy`, `executor_handler`, `executor_param`, `executor_block_strategy`, `executor_timeout`, `executor_fail_retry_count`, `glue_type`, `glue_source`, `glue_remark`, `glue_updatetime`, `child_jobid`) VALUES (1, 1, '测试任务1', '2018-11-03 22:21:31', '2018-11-03 22:21:31', 'XXL', '', 'CRON', '0 0 0 * * ? *', 'DO_NOTHING', 'FIRST', 'demoJobHandler', '', 'SERIAL_EXECUTION', 0, 0, 'BEAN', '', 'GLUE代码初始化', '2018-11-03 22:21:31', '');
INSERT INTO `xxl_job_user`(`id`, `username`, `password`, `role`, `permission`) VALUES (1, 'admin', 'e10adc3949ba59abbe56e057f20f883e', 1, NULL);
INSERT INTO `xxl_job_lock` ( `lock_name`) VALUES ( 'schedule_lock');
 
commit;
```


```bash
docker run -di -e PARAMS="--spring.datasource.url=jdbc:mysql://192.168.1.29:3306/xxl_job?Unicode=true&characterEncoding=UTF-8 --spring.datasource.username=root --spring.datasource.password=pzy123 --xxl.job.accessToken=pingzhuyan.test" \
-p 9001:8080 \
-v /usr/local/src/docker/xxl-job:/data/applogs \
--name xxl-job \
--privileged=true \
xuxueli/xxl-job-admin:2.4.0
```

--privileged=true 给予容器Root权限
-v 目录挂载   ：左边为宿主机目录，右边为容器内目录
以下几个配置非常重要，请根据自己情况修改
–xxl.job.accessToken=pingzhuyan.test  这行配置指定accessToken，当你在程序中引入xxl-job时，需要用到accessToken
--spring.datasource.username=root xxl-job 数据库登录账户
--spring.datasource.password=pzy123 数据库登录密码
--spring.datasource.url Sql数据库的url


http://192.168.1.29:9001/xxl-job-admin



