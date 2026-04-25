---
title: 定时任务_SpringTask
main_color: "#128fd3ff"
categories: 定时任务
tags:
  - 定时任务
cover: https://ae01.alicdn.com/kf/H09d4e16cb3ef40bab7c0b8bc76e3a688w.png
---


## SpringTask

`Spring Task` 是 Spring 框架提供的一个轻量级的任务调度工具，它使得在 Spring 应用中进行任务调度变得简单。通过使用 `@Scheduled` 注解，你可以在任何 Spring 管理的 Bean 中定义需要定时执行的方法。

### 主要特点

- **简单易用**：不需要额外的配置或复杂的设置，只需几个注解即可完成任务调度。
- **灵活性**：支持基于固定速率(`fixedRate`)、固定延迟(`fixedDelay`)以及 Cron 表达式(`cron`)的任务调度方式。
- **集成性**：作为 Spring 框架的一部分，能够很好地与其他 Spring 组件协作，如事务管理等。

### 使用方法

1. **启用调度功能**：首先，在你的 Spring Boot 应用的主类或者配置类上添加 `@EnableScheduling` 注解来启用调度功能。

2. **创建调度任务**：然后，在任何被 Spring 容器管理的 Bean 内部定义想要调度的方法，并使用 `@Scheduled` 注解来指定调度策略。

例如：

```java
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class MyTask {

    @Scheduled(fixedRate = 5000)
    public void reportCurrentTime() {
        System.out.println("当前时间：" + System.currentTimeMillis());
    }
}
```

在这个例子中，`reportCurrentTime` 方法将会每5秒执行一次。

3. **调度配置**：可以通过修改 `application.properties` 或者 `application.yml` 文件中的相关属性来调整调度器的行为，比如线程池大小等。



## 

以下是 **Spring Task** 中常用的注解和 API 的完整表格总结，适用于 Spring Framework 5.x 和 Spring Boot 2.x/3.x 环境。

---

## ✅ 一、Spring Task 注解

| 注解名称 | 所在包 | 说明 | 示例 |
|----------|--------|------|------|
| `@EnableScheduling` | `org.springframework.scheduling.annotation` | 启用定时任务功能，通常标注在配置类或启动类上。 | `@EnableScheduling` |
| `@Scheduled` | `org.springframework.scheduling.annotation` | 标注在方法上，表示该方法是定时任务方法。支持多种调度策略。 | `@Scheduled(cron = "0 * * * * ?")` |

### `@Scheduled` 注解支持的参数（调度策略）

| 参数名 | 类型 | 说明 | 示例 |
|--------|------|------|------|
| `cron` | `String` | 使用 Cron 表达式定义调度规则（支持 6 位或 7 位） | `cron = "0 0 12 * * ?"` |
| `zone` | `String` | 指定时区，默认为服务器本地时区 | `zone = "GMT+8"` |
| `fixedDelay` | `long` | 上一次任务执行完后，间隔固定时间再次执行（单位：毫秒） | `fixedDelay = 5000` |
| `fixedDelayString` | `String` | 同 `fixedDelay`，但值为字符串形式，支持占位符 | `fixedDelayString = "${task.delay}"` |
| `fixedRate` | `long` | 按照固定频率执行（不管上一次是否执行完） | `fixedRate = 5000` |
| `fixedRateString` | `String` | 同 `fixedRate`，但值为字符串形式 | `fixedRateString = "10000"` |
| `initialDelay` | `long` | 初始延迟时间（任务第一次执行前等待时间） | `initialDelay = 10000` |
| `initialDelayString` | `String` | 同 `initialDelay`，支持占位符 | `initialDelayString = "${task.initial}"` |

---

## ✅ 二、Spring Task 相关 API

| 类/接口 | 包路径 | 作用说明 |
|---------|--------|----------|
| `TaskScheduler` | `org.springframework.scheduling.TaskScheduler` | 提供调度器接口，用于注册定时任务。 |
| `ScheduledTaskRegistrar` | `org.springframework.scheduling.annotation` | 配置类中用于自定义任务调度器，实现 `SchedulingConfigurer` 接口后使用。 |
| `SchedulingConfigurer` | `org.springframework.scheduling.annotation` | 自定义调度配置接口，用于编程式配置任务调度器。 |
| `TaskExecutionProperties` | `org.springframework.boot.autoconfigure.task` | Spring Boot 中用于配置线程池等任务执行属性。 |
| `ThreadPoolTaskScheduler` | `org.springframework.scheduling.concurrent` | 基于线程池的调度器实现类，常用于自定义调度器。 |
| `@Async` | `org.springframework.scheduling.annotation` | 异步执行注解，需配合 `@EnableAsync` 使用。 |

---

## ✅ 三、Spring Boot 配置示例（application.yml）

```yaml
spring:
  task:
    scheduling:
      pool:
        size: 5  # 调度线程池大小，默认为1
      thread-name-prefix: task-scheduler-  # 线程名前缀
```

## ✅ 四、Cron 表达式格式（6位）

| 位置 | 值域 | 说明 |
|------|------|------|
| 1 | 0-59 | 秒 |
| 2 | 0-59 | 分 |
| 3 | 0-23 | 小时 |
| 4 | 1-31 | 日期 |
| 5 | 1-12 / JAN-DEC | 月份 |
| 6 | 0-7 / SUN-SAT | 星期几（0和7都是周日） |

> 示例：`"0 0 12 * * ?"` 表示每天中午12点执行。

---

## ✅ 五、示例代码（完整）

```java
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Component
public class ScheduledTasks {

    @Scheduled(fixedRate = 5000)
    public void runEvery5Seconds() {
        System.out.println("Fixed rate task - " + System.currentTimeMillis());
    }

    @Scheduled(fixedDelay = 5000)
    public void runAfter5Seconds() {
        System.out.println("Fixed delay task - " + System.currentTimeMillis());
    }

    @Scheduled(cron = "0 0 12 * * ?")
    public void runAtNoon() {
        System.out.println("执行每日中午12点任务 - " + System.currentTimeMillis());
    }
}
```

---

## ✅ 六、自定义调度器示例（使用 `SchedulingConfigurer`）

```java
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.SchedulingConfigurer;
import org.springframework.scheduling.config.ScheduledTaskRegistrar;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;

@Configuration
@EnableScheduling
public class SchedulerConfig implements SchedulingConfigurer {

    @Override
    public void configureTasks(ScheduledTaskRegistrar taskRegistrar) {
        ThreadPoolTaskScheduler taskScheduler = new ThreadPoolTaskScheduler();
        taskScheduler.setPoolSize(5);
        taskScheduler.initialize();

        taskRegistrar.setTaskScheduler(taskScheduler);
    }
}
```

---

## ✅ 七、注意事项

- `@Scheduled` 注解方法必须是无参、无返回值。
- `@EnableScheduling` 是必须的，否则定时任务不会生效。
- Spring Task 默认使用单线程调度器，若需并发建议配置线程池。
- 在分布式环境中，Spring Task 不具备任务协调能力，建议使用 Quartz、XXL-JOB、Spring Cloud Task 等。



### Spring Task 优缺点

#### **优点**

1. **简单易用**：Spring Task 是 Spring 框架的一部分，使用起来非常简便。只需要添加 `@EnableScheduling` 注解并使用 `@Scheduled` 标记需要定时执行的方法即可。
2. **轻量级**：无需额外的库或服务，适合小型应用或者对任务调度需求不复杂的场景。
3. **集成性好**：与 Spring 生态系统无缝集成，能够很好地利用 Spring 的依赖注入、事务管理等功能。
4. **配置灵活**：支持通过注解和配置文件两种方式来配置调度策略，包括基于 cron 表达式的调度、固定速率、固定延迟等。

#### **缺点**

1. **缺乏分布式支持**：Spring Task 不具备分布式环境下的任务协调能力。如果在多个节点上部署了同样的应用实例，每个实例都会独立执行预定的任务，这可能导致重复执行的问题。
2. **任务持久化问题**：没有内置的任务持久化机制，一旦任务失败或服务器重启，未完成的任务不会自动恢复。
3. **任务监控和管理功能有限**：相较于 Quartz 等专业任务调度框架，Spring Task 提供的任务监控和管理功能较为基础，不利于大规模生产环境下的运维管理。
4. **扩展性有限**：虽然可以通过自定义线程池等方式进行一定程度上的扩展，但对于更复杂的需求（如集群环境下任务的唯一执行），可能需要额外的工作量。

### 具体应用场景示例

- **单机应用中的定时任务**：对于不需要考虑分布式部署的应用来说，Spring Task 提供了一个非常便捷的方式来实现定时任务，例如每天凌晨生成前一天的日志报告，可以轻松地通过 `@Scheduled(cron = "0 0 0 * * ?")` 来设置。
  
- **后台数据处理**：在某些情况下，可能需要定期从数据库中拉取数据进行处理，比如每小时检查一次订单状态并更新库存信息。这种情况下，使用 Spring Task 可以减少外部依赖，简化开发流程。

- **不适合的场景**：如果你的应用部署在一个分布式的环境中，并且需要确保同一时间只有一个实例在执行某个定时任务，则 Spring Task 并不是一个好的选择。在这种情况下，你可能需要考虑使用像 Quartz 这样的工具，它提供了集群支持，能保证任务在同一时刻只被一个节点执行；或者使用消息队列来触发任务，以避免重复执行的问题。


非常好的问题！

你问的是：

> **“我的意思是这两种不都是并行的执行定时任务吗？”**

我们来详细分析一下：

---

## 🧠 **背景回顾**

你提到的两种方式：

1. **在 `@Scheduled` 定时任务中使用 `@Async`**
2. **直接配置定时任务的线程池（通过 `application.yml` 或 `SchedulingConfigurer`）**

你可能认为：**两者都能让定时任务并发执行，所以看起来差不多。**

但其实，它们的**并发机制和底层原理完全不同**。

---

## ✅ 一、直接配置定时任务线程池（推荐）

### 示例：

```java
@Configuration
@EnableScheduling
public class SchedulerConfig implements SchedulingConfigurer {
    @Override
    public void configureTasks(ScheduledTaskRegistrar taskRegistrar) {
        ThreadPoolTaskScheduler taskScheduler = new ThreadPoolTaskScheduler();
        taskScheduler.setPoolSize(5);
        taskScheduler.initialize();
        taskRegistrar.setTaskScheduler(taskScheduler);
    }
}
```

或配置 `application.yml`：

```yaml
spring:
  task:
    scheduling:
      pool:
        size: 5
```

### 📌 原理：

- Spring Task 默认使用的是**单线程**调度器。
- 配置了线程池后，Spring 会使用多个线程来**并行执行不同的定时任务方法**。
- 每个 `@Scheduled` 方法由不同的线程执行，**天然支持并行**。

### ✅ 优点：

- 多个定时任务可以**真正并行执行**。
- 不需要额外注解，**配置即生效**。
- 更适合定时任务本身是**计算密集型或耗时任务**。

---

## ✅ 二、在 `@Scheduled` 方法上加 `@Async`

### 示例：

```java
@Component
public class MyTask {

    @Scheduled(fixedRate = 5000)
    @Async
    public void doSomething() {
        // 耗时操作
    }
}
```

### 📌 原理：

- `@Scheduled` 本身是由一个线程调度的（比如默认线程池中的某个线程）。
- 加上 `@Async` 后，Spring 会把这个方法**交给异步线程池去执行**。
- 即：定时任务触发后，**立即把任务交给异步线程池**，主线程释放。

### ✅ 优点：

- 可以将耗时操作从定时任务线程中剥离出来，避免阻塞定时任务线程。
- 适合：**定时任务只是触发器，实际执行是异步操作**的场景。

---

## 🧩 两者并发执行的差异总结

| 特性 | 直接配置定时任务线程池 | 定时任务方法加 `@Async` |
|------|-------------------------|--------------------------|
| 并发机制 | 多个定时任务方法**并行执行** | 同一个定时任务方法**异步执行** |
| 线程池类型 | `TaskScheduler`（定时线程池） | `TaskExecutor`（通用异步线程池） |
| 是否能并行执行多个定时任务 | ✅ 是 | ❌ 否（除非多个定时任务都加 `@Async`） |
| 是否适合耗时任务 | ✅ 是 | ✅ 是（但需额外配置异步线程池） |
| 是否阻塞调度线程 | ❌ 否（多线程） | ✅ 是（除非加 `@Async`） |
| 是否需要额外配置异步线程池 | ❌ 否 | ✅ 是（需配置 `@EnableAsync` 和线程池） |
| 适合场景 | 多个定时任务并行执行 | 单个定时任务内部异步处理，不阻塞调度 |

---

## 🧪 举个例子对比

### 场景：你有两个定时任务 A 和 B，分别每 5 秒执行一次，每个任务执行 3 秒。

#### 1. **默认单线程调度器（无配置）**

- A 和 B **串行执行**（A 执行完，B 才能执行）。
- 总耗时：6 秒以上。

#### 2. **配置线程池大小为 2**

- A 和 B **并行执行**，互不干扰。
- 总耗时：3 秒左右。

#### 3. **A 方法加 `@Async`，调度线程池为 1，异步线程池为 2**

- A 的调度线程触发后立即返回，任务交给异步线程池执行。
- B 仍串行执行。
- A 的异步执行不影响调度线程。

---

## ✅ 推荐用法总结

| 场景 | 推荐做法 |
|------|----------|
| 多个定时任务并行执行 | ✅ 配置定时任务线程池（推荐） |
| 单个定时任务内部执行耗时操作 | ✅ 使用 `@Async` |
| 既要并行多个任务，又要异步执行某些任务 | ✅ 两者结合使用（配置定时线程池 + 配置异步线程池 + `@Async`） |

---

## 🧱 示例：两者结合使用（最佳实践）

```java
@Configuration
@EnableScheduling
@EnableAsync
public class SchedulerConfig implements SchedulingConfigurer, AsyncConfigurerSupport {

    // 定时任务线程池
    @Override
    public void configureTasks(ScheduledTaskRegistrar taskRegistrar) {
        ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(5);
        scheduler.initialize();
        taskRegistrar.setTaskScheduler(scheduler);
    }

    // 异步任务线程池
    @Bean(name = "taskExecutor")
    public Executor taskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(10);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("async-task-");
        executor.initialize();
        return executor;
    }

    @Override
    public Executor getAsyncExecutor() {
        return taskExecutor();
    }
}
```

然后：

```java
@Component
public class MyTask {

    @Scheduled(fixedRate = 5000)
    @Async("taskExecutor")
    public void taskA() {
        // 耗时操作
    }

    @Scheduled(fixedRate = 5000)
    public void taskB() {
        // 快速执行任务
    }
}
```

---

## ✅ 总结一句话：

> **直接配置定时任务线程池是让多个定时任务并行执行，而 `@Async` 是让某个定时任务的方法异步执行，两者解决的问题不同，但可以结合使用。**

