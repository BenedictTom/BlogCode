---
title: 定时任务_Quartz
main_color: "#bd128fff"
categories: 定时任务
tags:
  - 定时任务
cover: https://free.picui.cn/free/2026/03/28/69c74e01f0d1d.png
---


## Quartz

Quartz 是一个功能强大、开源的作业调度库，它可以集成到几乎任何 Java 应用中——无论是独立的应用程序、基于 Java EE 的 Web 应用还是大型分布式系统。Quartz 被设计用于在预定义的时间点或周期性地执行任务（被称为 Jobs），非常适合需要定时执行某些操作的场景。

### 主要特性

1. **灵活的调度模型**：支持复杂的调度需求，包括但不限于固定频率和时间间隔的触发、Cron 表达式定义的复杂调度模式。
2. **持久化作业存储**：可以通过 JDBC 将 Job 和 Trigger 信息保存到数据库中，实现集群环境下的高可用性和容错能力。
3. **集群支持**：允许多个 Quartz 实例组成集群共同处理作业，提高了系统的可伸缩性和可靠性。
4. **监听器和插件机制**：提供了一系列接口如 JobListener、TriggerListener 等，允许开发者自定义行为；同时支持插件扩展。
5. **事务管理**：可以与 JTA 事务集成，确保作业执行的一致性和完整性。
6. **轻量级且易于集成**：作为一个库存在，易于嵌入现有的应用程序中，并提供了 Spring 集成模块。

### 核心概念

- **Job**：代表一个具体的工作单元，实现了 `org.quartz.Job` 接口，并重写了 `execute(JobExecutionContext context)` 方法来定义具体的行为。
- **JobDetail**：封装了关于 Job 的详细信息，比如 Job 的名称、所属组别以及其它元数据。
- **Trigger**：定义了 Job 执行的时间规则。常见的类型有 SimpleTrigger（简单触发器）和 CronTrigger（基于 Cron 表达式的触发器）。
- **Scheduler**：是 Quartz 的核心组件，负责管理和协调 Job 和 Trigger 的生命周期，控制它们何时被触发以及如何执行。
- **JobStore**：决定了 Job 和 Trigger 数据的存储方式，可以选择内存中的 RAMJobStore 或者持久化的 JDBCJobStore。

### 基本使用流程

1. **创建 Job**：编写实现 `Job` 接口的类。
2. **定义 JobDetail**：创建 `JobDetail` 实例，指定 Job 类型及其它属性。
3. **配置 Trigger**：根据业务需求选择合适的触发器类型并设置相应的参数。
4. **获取 Scheduler**：通过 `StdSchedulerFactory.getDefaultScheduler()` 获取默认的 Scheduler 实例。
5. **安排 Job**：将 JobDetail 和 Trigger 注册到 Scheduler 中。
6. **启动 Scheduler**：调用 `scheduler.start()` 启动调度器，开始执行预定的任务。

### 示例代码

```java
import org.quartz.*;
import org.quartz.impl.StdSchedulerFactory;

public class QuartzExample {

    public static void main(String[] args) throws SchedulerException {
        // 创建 JobDetail
        JobDetail job = JobBuilder.newJob(HelloJob.class)
                .withIdentity("helloJob", "group1")
                .build();

        // 创建 Trigger
        Trigger trigger = TriggerBuilder.newTrigger()
                .withIdentity("helloTrigger", "group1")
                .startNow()
                .withSchedule(SimpleScheduleBuilder.simpleSchedule()
                        .withIntervalInSeconds(40)
                        .repeatForever())
                .build();

        // 获取 Scheduler 实例
        Scheduler scheduler = StdSchedulerFactory.getDefaultScheduler();

        // 安排 Job
        scheduler.scheduleJob(job, trigger);

        // 启动 Scheduler
        scheduler.start();
    }

    public static class HelloJob implements Job {
        @Override
        public void execute(JobExecutionContext context) throws JobExecutionException {
            System.out.println("Hello Quartz!");
        }
    }
}
```

## Scheduler

### Scheduler 简介

在 Quartz 中，`Scheduler` 是核心接口之一，它负责管理 Job（任务）和 Trigger（触发器），控制它们的生命周期，并根据触发器的时间规则调度执行相应的任务。`Scheduler` 可以认为是整个 Quartz 调度系统的大脑，它决定了何时以及如何执行作业。

### Scheduler 的主要职责

- **管理 Job 和 Trigger**：包括添加、删除、暂停、恢复等操作。
- **调度执行**：基于配置好的触发器时间规则，决定何时执行哪些作业。
- **状态管理**：可以启动、停止调度器，也可以查询当前调度器的状态。
- **监听器支持**：允许注册各种监听器（如 JobListener, TriggerListener, SchedulerListener），以便在特定事件发生时得到通知并作出响应。

### Scheduler 的架构与实现类

#### 架构概述

Quartz 的架构设计围绕着几个关键组件展开：

1. **Job & JobDetail**: 定义了要执行的任务及其详细信息。
2. **Trigger**: 决定了 Job 执行的时间点或频率。
3. **Scheduler**: 核心调度器，负责管理和协调 Job 与 Trigger。
4. **JobStore**: 存储 Job 和 Trigger 的数据，可以选择内存存储（RAMJobStore）或者持久化到数据库中（JDBCJobStore）。
5. **ThreadPool**: 提供线程池用于并发执行多个 Job 实例。

#### 主要实现类

- **StdSchedulerFactory**: 这是一个实现了 `SchedulerFactory` 接口的工厂类，默认情况下会创建 `StdScheduler` 实例。它是获取 `Scheduler` 实例最常用的方式。
  
- **DirectSchedulerFactory**: 允许直接构建 `Scheduler` 对象，提供了对调度器内部参数更细粒度的控制，但通常不推荐使用这种方式，除非有特殊需求。

- **StdScheduler**: 实现了 `Scheduler` 接口的主要类。它是通过 `StdSchedulerFactory` 创建出来的具体调度器实例，负责实际的调度工作。


### 示例代码

下面是一个简单的例子展示如何使用 `StdSchedulerFactory` 获取 `Scheduler` 并安排一个 Job：

```java
import org.quartz.*;
import org.quartz.impl.StdSchedulerFactory;

public class QuartzExample {

    public static void main(String[] args) throws SchedulerException {
        // 创建 JobDetail
        JobDetail job = JobBuilder.newJob(HelloJob.class)
                .withIdentity("helloJob", "group1")
                .build();

        // 创建 Trigger
        Trigger trigger = TriggerBuilder.newTrigger()
                .withIdentity("helloTrigger", "group1")
                .startNow()
                .withSchedule(SimpleScheduleBuilder.simpleSchedule()
                        .withIntervalInSeconds(40)
                        .repeatForever())
                .build();

        // 获取 Scheduler 实例
        Scheduler scheduler = StdSchedulerFactory.getDefaultScheduler();

        // 安排 Job
        scheduler.scheduleJob(job, trigger);

        // 启动 Scheduler
        scheduler.start();
    }

    public static class HelloJob implements Job {
        @Override
        public void execute(JobExecutionContext context) throws JobExecutionException {
            System.out.println("Hello Quartz!");
        }
    }
}
```

### 总结

- `Scheduler` 是 Quartz 框架的核心，负责管理和调度 Job 和 Trigger。
- `StdSchedulerFactory` 是获取 `Scheduler` 实例的标准途径，而 `StdScheduler` 则是最常见的 `Scheduler` 实

### StdScheduler
`StdScheduler` 是 Quartz 调度框架中的核心实现类之一，它实现了 `org.quartz.Scheduler` 接口。`StdScheduler` 提供了调度作业（Job）和触发器（Trigger）所需的所有功能，并且负责管理这些组件的生命周期以及根据触发器定义的时间规则来调度作业的执行。

### 主要职责

- **管理 Job 和 Trigger**：包括添加、删除、暂停、恢复等操作。
- **调度执行**：基于配置好的触发器时间规则，决定何时执行哪些作业。
- **状态管理**：可以启动、停止调度器，也可以查询当前调度器的状态。
- **监听器支持**：允许注册各种监听器（如 `JobListener`, `TriggerListener`, `SchedulerListener`），以便在特定事件发生时得到通知并作出响应。
- **持久化与非持久化存储**：通过不同的 `JobStore` 实现，可以选择将作业和触发器的信息保存在内存中或数据库中。

### 关键特性

1. **Job 与 Trigger 的管理**：
   - 可以动态地向调度器添加或移除 Job 和 Trigger。
   - 支持对单个 Job 或 Trigger 进行暂停、恢复等操作。

2. **调度机制**：
   - 根据不同的触发器类型（如 `SimpleTrigger`, `CronTrigger`），按照预定的时间表调度作业。
   - 支持并发执行多个作业实例。

3. **集群支持**：
   - 当使用 JDBCJobStore 时，`StdScheduler` 支持集群模式，允许多个调度器实例共享同一个数据库，从而实现高可用性和负载均衡。

4. **事务支持**：
   - 可以与 JTA 事务集成，确保作业执行的一致性和完整性。

5. **插件系统**：
   - 支持通过插件扩展调度器的功能，比如日志记录、邮件通知等。

### 构造与获取

通常情况下，不会直接实例化 `StdScheduler` 对象，而是通过 `StdSchedulerFactory` 来创建：

```java
Scheduler scheduler = StdSchedulerFactory.getDefaultScheduler();
```

这段代码会返回一个默认配置的 `StdScheduler` 实例。你也可以通过加载自定义的配置文件来获得一个特定配置的调度器实例。

### 基本使用流程

1. **创建 JobDetail**：定义要执行的任务及其详细信息。
2. **定义 Trigger**：设置任务执行的时间规则。
3. **获取 Scheduler 实例**：通常是通过 `StdSchedulerFactory` 获取。
4. **安排 Job**：将 JobDetail 和 Trigger 注册到 Scheduler 中。
5. **启动 Scheduler**：调用 `scheduler.start()` 启动调度器，开始执行预定的任务。

#### 示例代码

```java
import org.quartz.*;
import org.quartz.impl.StdSchedulerFactory;

public class QuartzExample {

    public static void main(String[] args) throws SchedulerException {
        // 创建 JobDetail
        JobDetail job = JobBuilder.newJob(HelloJob.class)
                .withIdentity("helloJob", "group1")
                .build();

        // 创建 Trigger
        Trigger trigger = TriggerBuilder.newTrigger()
                .withIdentity("helloTrigger", "group1")
                .startNow()
                .withSchedule(SimpleScheduleBuilder.simpleSchedule()
                        .withIntervalInSeconds(40)
                        .repeatForever())
                .build();

        // 获取 Scheduler 实例
        Scheduler scheduler = StdSchedulerFactory.getDefaultScheduler();

        // 安排 Job
        scheduler.scheduleJob(job, trigger);

        // 启动 Scheduler
        scheduler.start();
    }

    public static class HelloJob implements Job {
        @Override
        public void execute(JobExecutionContext context) throws JobExecutionException {
            System.out.println("Hello Quartz!");
        }
    }
}
```

在这个示例中，我们创建了一个简单的定时任务，每 40 秒打印一次 "Hello Quartz!"。这个过程展示了如何使用 `StdScheduler` 来安排和执行作业。

### 总结

`StdScheduler` 是 Quartz 框架的核心调度器实现，提供了强大的作业调度能力。它不仅能够满足基本的定时任务需求，还支持复杂的调度策略、集群部署及事务管理等功能。通过合理配置和利用其高级特性，可以有效地管理和调度大规模分布式系统的作业任务。


`StdScheduler` 实现了 `org.quartz.Scheduler` 接口，提供了丰富的 API 来管理作业（Job）和触发器（Trigger），以及控制调度器的行为。以下是 `Scheduler` 接口中定义的主要方法及其功能说明。请注意，由于篇幅限制，这里列出的是核心方法，并非所有可能的内部或扩展方法。

### `StdScheduler` 核心 API 表格

| 方法签名 | 描述 |
| --- | --- |
| `void start()` | 启动调度器，开始执行预定的任务。 |
| `void startDelayed(int seconds)` | 在指定秒数后启动调度器。 |
| `boolean isStarted()` | 判断调度器是否已经启动。 |
| `void standby()` | 将调度器置于待机状态，暂停任务执行但不关闭调度器。 |
| `boolean isInStandbyMode()` | 检查调度器是否处于待机模式。 |
| `void shutdown()` | 关闭调度器并等待所有正在执行的任务完成。 |
| `void shutdown(boolean waitForJobsToComplete)` | 关闭调度器，可选择是否等待当前正在执行的任务完成。 |
| `String getSchedulerName()` | 获取调度器名称。 |
| `SchedulerContext getContext()` | 获取调度器上下文。 |
| `JobDetail getJobDetail(JobKey jobKey)` | 根据 JobKey 获取 Job 的详细信息。 |
| `List<? extends Trigger> getTriggersOfJob(JobKey jobKey)` | 获取与特定作业关联的所有触发器。 |
| `TriggerState getTriggerState(TriggerKey triggerKey)` | 获取触发器的状态（如 NONE, NORMAL, PAUSED, COMPLETE, ERROR, BLOCKED）。 |
| `void scheduleJob(JobDetail jobDetail, Trigger trigger)` | 安排一个新的作业和触发器。 |
| `Date scheduleJob(Trigger trigger)` | 更新现有作业的触发器。 |
| `void addJob(JobDetail jobDetail, boolean replace)` | 添加一个作业到调度器中，replace 参数决定是否替换已存在的同名作业。 |
| `boolean deleteJob(JobKey jobKey)` | 删除指定的作业。 |
| `boolean unscheduleJob(TriggerKey triggerKey)` | 取消调度器中的指定触发器。 |
| `Date rescheduleJob(TriggerKey triggerKey, Trigger newTrigger)` | 重新安排触发器的时间规则。 |
| `void pauseJob(JobKey jobKey)` | 暂停指定作业。 |
| `void pauseJobs(GroupMatcher<JobKey> matcher)` | 暂停匹配给定条件的所有作业。 |
| `void pauseTrigger(TriggerKey triggerKey)` | 暂停指定触发器。 |
| `void pauseTriggers(GroupMatcher<TriggerKey> matcher)` | 暂停匹配给定条件的所有触发器。 |
| `void resumeJob(JobKey jobKey)` | 恢复指定作业。 |
| `void resumeJobs(GroupMatcher<JobKey> matcher)` | 恢复匹配给定条件的所有作业。 |
| `void resumeTrigger(TriggerKey triggerKey)` | 恢复指定触发器。 |
| `void resumeTriggers(GroupMatcher<TriggerKey> matcher)` | 恢复匹配给定条件的所有触发器。 |
| `List<JobExecutionContext> getCurrentlyExecutingJobs()` | 获取当前正在执行的所有作业的上下文。 |
| `<T extends SchedulerListener> void addSchedulerListener(T listener)` | 注册一个调度器监听器。 |
| `<T extends SchedulerListener> boolean removeSchedulerListener(T listener)` | 移除一个调度器监听器。 |
| `<T extends TriggerListener> void addGlobalTriggerListener(T listener)` | 注册一个全局触发器监听器。 |
| `<T extends JobListener> void addGlobalJobListener(T listener)` | 注册一个全局作业监听器。 |

## Job
在 Quartz 调度框架中，`Job` 是一个核心概念，它代表了你希望调度器执行的具体任务。每个 `Job` 实例都实现了 `org.quartz.Job` 接口，并且必须实现其中的 `execute(JobExecutionContext context)` 方法，该方法定义了当触发器触发时要执行的操作。

### Job 的基本概念

- **Job**: 一个具体的任务或工作单元，实现了 `Job` 接口。
- **JobDetail**: 包含了关于 `Job` 的详细信息，如名称、组别、描述以及一些配置参数等。它是 `Job` 的具体实例化表示，用于向调度器注册 `Job`。
- **Trigger**: 定义了 `Job` 应该何时被执行的时间规则。常见的触发器类型包括 `SimpleTrigger` 和 `CronTrigger`。

### 主要特点

1. **可序列化**：为了支持持久化存储（例如将作业保存到数据库中），`Job` 类通常需要实现 `Serializable` 接口。
2. **状态管理**：Quartz 提供了两种注解来控制 `Job` 的并发行为：
   - `@DisallowConcurrentExecution`: 标记此注解后，同一 `JobDetail` 的多个实例不会同时运行。
   - `@PersistJobDataAfterExecution`: 标记此注解后，`Job` 执行完毕后会自动保存其 `JobDataMap` 状态，以便下次执行时可以访问上次执行后的状态。
3. **JobDataMap**: 允许传递任意数量的键值对给 `Job`，这些数据可以通过 `JobExecutionContext` 获取。

### 创建和使用 Job

#### 1. 实现 Job 接口

```java
import org.quartz.*;

public class ExampleJob implements Job {
    @Override
    public void execute(JobExecutionContext context) throws JobExecutionException {
        // 在这里编写你要执行的任务逻辑
        System.out.println("Executing job at: " + new java.util.Date());
        
        // 可以通过 JobExecutionContext 访问 JobDataMap
        JobKey key = context.getJobDetail().getKey();
        JobDataMap dataMap = context.getJobDetail().getJobDataMap();
        String user = dataMap.getString("user");
        System.out.println("Hello, " + user);
    }
}
```

#### 2. 创建 JobDetail 并注册 Job

```java
import org.quartz.*;
import org.quartz.impl.StdSchedulerFactory;

public class QuartzExample {

    public static void main(String[] args) throws SchedulerException {
        // 创建 Scheduler 实例
        Scheduler scheduler = StdSchedulerFactory.getDefaultScheduler();

        // 创建 JobDetail
        JobDetail job = JobBuilder.newJob(ExampleJob.class)
                .withIdentity("exampleJob", "group1")
                .usingJobData("user", "World") // 添加自定义数据
                .build();

        // 创建 Trigger
        Trigger trigger = TriggerBuilder.newTrigger()
                .withIdentity("exampleTrigger", "group1")
                .startNow()
                .withSchedule(SimpleScheduleBuilder.simpleSchedule()
                        .withIntervalInSeconds(10)
                        .repeatForever())
                .build();

        // 注册 Job 到 Scheduler 中
        scheduler.scheduleJob(job, trigger);

        // 启动 Scheduler
        scheduler.start();
    }
}
```

### Job 的生命周期

1. **创建**：通过 `JobBuilder` 创建 `JobDetail` 对象。
2. **注册**：使用 `Scheduler.scheduleJob()` 方法将 `JobDetail` 和相应的 `Trigger` 注册到 `Scheduler`。
3. **执行**：当 `Trigger` 触发时，`Scheduler` 会调用 `Job` 的 `execute()` 方法。
4. **销毁**：如果不再需要某个 `Job`，可以通过 `Scheduler.deleteJob()` 方法从调度器中删除它。

### 注意事项

- **线程安全**：默认情况下，Quartz 会为每个触发的 `Job` 实例创建一个新的实例并执行 `execute()` 方法。因此，在大多数情况下，不需要担心线程安全问题。
- **持久化与非持久化**：根据所使用的 `JobStore`（如内存中的 `RAMJobStore` 或数据库中的 `JDBCJobStore`），`Job` 的状态可能会被持久化。如果使用持久化存储，则需要确保 `Job` 类是可序列化的。

### JobDetail

### JobDetail 介绍

在 Quartz 调度框架中，`JobDetail` 是用来描述和封装 `Job` 的详细信息的对象。它不仅包含了 `Job` 实例的定义，还携带了关于这个 `Job` 的元数据，如名称、组别、描述等，以及可以通过 `JobDataMap` 传递给 `Job` 的参数。简而言之，`JobDetail` 是你向调度器注册一个 `Job` 时使用的对象。

### 主要功能

1. **定义 Job 的身份**：每个 `JobDetail` 都有一个唯一的标识符（由名称和组构成），这使得你可以轻松地在调度器中查找、暂停或删除特定的任务。
2. **携带任务数据**：通过 `JobDataMap`，可以将任意数量的键值对传递给 `Job` 实例，这对于动态配置作业的行为非常有用。
3. **持久化与非持久化存储**：根据所使用的 `JobStore` 类型（内存中的 `RAMJobStore` 或数据库中的 `JDBCJobStore`），`JobDetail` 可以被临时保存或永久保存到存储介质中。
4. **支持并发控制**：通过注解（如 `@DisallowConcurrentExecution` 和 `@PersistJobDataAfterExecution`），可以控制 `Job` 实例的并发执行行为及其状态管理。

### 核心属性

- **Key (JobKey)**: 包含 `Job` 的名称和组别，用于唯一标识一个 `Job`。
- **Description**: 对 `Job` 的描述信息，便于理解和维护。
- **JobClass**: 指定要执行的 `Job` 类。
- **JobDataMap**: 一个方便的容器，允许你为 `Job` 实例添加任意数量的键值对数据。
- **Durability**: 如果设置为 true，则即使没有活跃的触发器关联此 `Job`，它也不会被自动删除。
- **RequestsRecovery**: 如果设置为 true，则当执行失败且调度器尝试恢复时，该 `Job` 将被标记为可恢复的。

### 创建和使用 JobDetail

#### 使用 JobBuilder 创建 JobDetail

Quartz 提供了 `JobBuilder` 来帮助创建 `JobDetail` 实例：

```java
import org.quartz.*;
import org.quartz.impl.StdSchedulerFactory;

public class QuartzExample {

    public static void main(String[] args) throws SchedulerException {
        // 创建 Scheduler 实例
        Scheduler scheduler = StdSchedulerFactory.getDefaultScheduler();

        // 创建 JobDetail
        JobDetail job = JobBuilder.newJob(HelloJob.class)
                .withIdentity("helloJob", "group1") // 定义 Job 的名称和组别
                .usingJobData("message", "Hello, Quartz!") // 添加自定义数据
                .build();

        // 创建 Trigger
        Trigger trigger = TriggerBuilder.newTrigger()
                .withIdentity("helloTrigger", "group1")
                .startNow()
                .withSchedule(SimpleScheduleBuilder.simpleSchedule()
                        .withIntervalInSeconds(10)
                        .repeatForever())
                .build();

        // 注册 Job 到 Scheduler 中
        scheduler.scheduleJob(job, trigger);

        // 启动 Scheduler
        scheduler.start();
    }

    public static class HelloJob implements Job {
        @Override
        public void execute(JobExecutionContext context) throws JobExecutionException {
            String message = context.getJobDetail().getJobDataMap().getString("message");
            System.out.println(message);
        }
    }
}
```

### JobDataMap

`JobDataMap` 是 `JobDetail` 中的一个重要组件，它允许你传递任意数量的键值对给 `Job` 实例。这些数据可以在 `Job` 执行期间访问，非常适合用于配置或参数传递。

```java
JobDetail job = JobBuilder.newJob(HelloJob.class)
        .withIdentity("helloJob", "group1")
        .usingJobData("user", "World") // 添加自定义数据
        .build();
```

然后在 `Job` 的 `execute()` 方法中，可以通过 `JobExecutionContext` 访问这些数据：

```java
String user = context.getJobDetail().getJobDataMap().getString("user");
System.out.println("Hello, " + user);
```

### QuartzJobBean

`QuartzJobBean` 是 Spring 框架提供的一个类，用于将 Quartz 的任务调度功能与 Spring 的 IoC（控制反转）容器集成。它允许你在 Quartz 作业中使用 Spring 管理的 Bean 和依赖注入，从而使得在 Quartz Job 中可以访问 Spring 上下文中的服务或其他组件。

### `QuartzJobBean` 与普通 Quartz `Job` 的主要区别

1. **Spring 集成**：
   - **`QuartzJobBean`**：专门设计用于与 Spring 框架集成。通过继承 `QuartzJobBean`，你可以利用 Spring 的 IoC 功能，例如依赖注入。
   - **普通 `Job`**：不直接支持 Spring 的 IoC 容器。你需要手动管理依赖关系或通过其他方式（如应用上下文查找）获取所需的资源和服务。

2. **执行方法**：
   - **`QuartzJobBean`**：需要实现 `executeInternal(JobExecutionContext context)` 方法，而不是标准的 `Job` 接口的 `execute(JobExecutionContext context)` 方法。`executeInternal` 方法提供了一个更细粒度的控制，同时也能保持与 Spring 的良好集成。
   - **普通 `Job`**：只需实现 `execute(JobExecutionContext context)` 方法即可。

3. **依赖注入**：
   - **`QuartzJobBean`**：由于其设计初衷是为了与 Spring 集成，因此可以直接在类中定义依赖，并让 Spring 自动注入这些依赖。
   - **普通 `Job`**：通常不会自动获得依赖注入的支持，除非你自己编写代码来从 Spring 应用上下文中获取相应的 Bean。

4. **配置和调度**：
   - **`QuartzJobBean`**：可以通过 Spring 的配置文件或注解进行配置，并且可以利用 Spring 的 AOP、事务管理等功能。
   - **普通 `Job`**：通常需要通过 Quartz 的原生 API 进行配置和调度，可能涉及到更多的编码工作来设置调度规则、触发器等。

### 示例

下面是一个简单的示例，展示了如何使用 `QuartzJobBean`：

```java
import org.springframework.scheduling.quartz.QuartzJobBean;
import org.springframework.beans.factory.annotation.Autowired;

public class MyQuartzJob extends QuartzJobBean {

    @Autowired
    private MyService myService;

    @Override
    protected void executeInternal(JobExecutionContext context) {
        // 使用注入的服务
        myService.performTask();
    }
}
```

在这个例子中，`MyQuartzJob` 继承自 `QuartzJobBean` 并且通过 `@Autowired` 注入了 `MyService`，这样就可以在 `executeInternal` 方法中调用该服务的方法。

相比之下，如果你直接使用 Quartz 的 `Job` 接口，则无法直接享受到这种便捷的依赖注入机制，而必须自己处理依赖的获取。

总之，`QuartzJobBean` 提供了一种更加简便的方式，使得 Quartz Jobs 可以充分利用 Spring 的强大功能，特别是在大型项目或者需要高度模块化的应用中非常有用。然而，对于那些不需要 Spring 特性的简单场景，直接使用 Quartz 的 `Job` 接口可能会更加简洁明了。

## Triggers

在 Quartz 调度框架中，触发器（Triggers）是用于定义作业（Job）何时及如何执行的关键组件。每个触发器都实现了 `org.quartz.Trigger` 接口，并且负责指定一个或多个 Job 的执行计划。Quartz 提供了几种不同类型的触发器，以适应不同的调度需求。

### 触发器的主要类型

1. **SimpleTrigger**
   - 适用于需要简单重复执行的任务，例如每隔一定时间间隔执行一次任务。
   - 可以设置开始时间、结束时间、重复次数和重复间隔等参数。
   - 常见用法：每5分钟执行一次任务，或者从现在起延迟一段时间后只执行一次任务。

2. **CronTrigger**
   - 提供了更灵活的调度方案，基于 Unix cron 表达式来定义复杂的调度规则。
   - 非常适合于周期性任务，如每天早上9点执行，或者每月的第一个周一执行。
   - 使用标准的 cron 表达式格式："秒 分 时 日 月 星期 年(可选)"。

3. **CalendarIntervalTrigger**
   - 类似于 `SimpleTrigger`，但它允许根据日历单位（如天、周、月等）来安排重复任务。
   - 对于那些希望按照日历时间进行调度的任务特别有用，比如每周一执行一次任务。

4. **DailyTimeIntervalTrigger**
   - 允许你在一天中的特定时间段内按固定间隔重复执行任务。
   - 比如，在工作日的工作时间内（上午9点到下午5点），每小时执行一次任务。

5. **NthIncludedDayTrigger** (较少使用)
   - 这个触发器可以让你在一个给定的日历范围内选择第 n 天来执行任务。

### 创建触发器

Quartz 提供了 `TriggerBuilder` 来帮助创建各种类型的触发器实例。以下是一些示例：

#### SimpleTrigger 示例

```java
import org.quartz.*;
import org.quartz.impl.StdSchedulerFactory;

public class SimpleTriggerExample {
    public static void main(String[] args) throws SchedulerException {
        // 创建调度器
        Scheduler scheduler = StdSchedulerFactory.getDefaultScheduler();

        // 定义 JobDetail
        JobDetail job = JobBuilder.newJob(SimpleJob.class)
                .withIdentity("simpleJob", "group1")
                .build();

        // 创建 SimpleTrigger
        Trigger trigger = TriggerBuilder.newTrigger()
                .withIdentity("simpleTrigger", "group1")
                .startNow()
                .withSchedule(SimpleScheduleBuilder.simpleSchedule()
                        .withIntervalInSeconds(10)
                        .repeatForever())
                .build();

        // 将 Job 和 Trigger 注册到调度器中
        scheduler.scheduleJob(job, trigger);

        // 启动调度器
        scheduler.start();
    }

    public static class SimpleJob implements Job {
        @Override
        public void execute(JobExecutionContext context) throws JobExecutionException {
            System.out.println("Executing SimpleJob at: " + new java.util.Date());
        }
    }
}
```

#### CronTrigger 示例

```java
import org.quartz.*;
import org.quartz.impl.StdSchedulerFactory;

public class CronTriggerExample {
    public static void main(String[] args) throws SchedulerException {
        // 创建调度器
        Scheduler scheduler = StdSchedulerFactory.getDefaultScheduler();

        // 定义 JobDetail
        JobDetail job = JobBuilder.newJob(CronJob.class)
                .withIdentity("cronJob", "group1")
                .build();

        // 创建 CronTrigger
        Trigger trigger = TriggerBuilder.newTrigger()
                .withIdentity("cronTrigger", "group1")
                .withSchedule(CronScheduleBuilder.dailyAtHourAndMinute(10, 0)) // 每天上午10点执行
                .build();

        // 将 Job 和 Trigger 注册到调度器中
        scheduler.scheduleJob(job, trigger);

        // 启动调度器
        scheduler.start();
    }

    public static class CronJob implements Job {
        @Override
        public void execute(JobExecutionContext context) throws JobExecutionException {
            System.out.println("Executing CronJob at: " + new java.util.Date());
        }
    }
}
```

### 触发器的状态管理

- **暂停/恢复触发器**：可以通过 `scheduler.pauseTrigger(triggerKey)` 和 `scheduler.resumeTrigger(triggerKey)` 方法来控制触发器的状态。
- **删除触发器**：如果不再需要某个触发器，可以使用 `scheduler.unscheduleJob(triggerKey)` 方法将其从调度器中移除。


## JobStore

`JobStore` 在 Quartz 调度框架中扮演着核心角色，它负责持久化存储和管理调度器的所有数据，包括 Job、Trigger、Calendar 等。根据应用的需求和环境的不同，Quartz 提供了多种 `JobStore` 实现，每种实现都有其特定的使用场景。

### 主要功能

- **持久化**：决定如何保存调度器的状态信息（如 Job 和 Trigger 的定义及其执行状态）。
- **事务管理**：在某些情况下，需要确保调度操作的原子性，这通常涉及到数据库事务。
- **集群支持**：部分 `JobStore` 实现支持 Quartz 在集群环境中运行，以提供高可用性和负载均衡。

### 常见的 JobStore 实现

1. **RAMJobStore**
   - 默认实现，所有数据都存储在内存中。
   - 优点：简单、快速，无需额外配置。
   - 缺点：一旦应用程序停止或崩溃，所有的调度信息都会丢失。
   - 使用场景：适用于不需要持久化的简单应用或者开发测试环境。

2. **JDBCJobStore**
   - 将所有调度相关的数据存储到关系型数据库中。
   - 支持两种模式：
     - **JobStoreTX**：直接由 Quartz 管理事务。
     - **JobStoreCMT**：利用容器管理事务（CMT），适合与 JTA 一起使用。
   - 优点：提供了持久化能力，支持集群部署。
   - 缺点：相比 RAMJobStore，性能有所下降，因为涉及到了数据库操作。
   - 使用场景：适用于生产环境中的关键任务，特别是那些需要在系统重启后依然保持调度状态的应用。

3. **JobStoreSupport**
   - 这是一个抽象类，`JDBCJobStore` 是基于它的实现之一。
   - 它提供了对不同数据库的支持，并允许用户通过自定义 SQL 来优化性能。

4. **Clustered Mode with JDBCJobStore**
   - 当多个 Quartz 实例共享同一个数据库时，可以启用集群模式。
   - 在这种模式下，只有其中一个实例会实际触发 Job 执行，其他实例则作为备用，提高了系统的可靠性和可扩展性。
   - 注意事项：需要确保数据库表结构正确，且所有 Quartz 实例使用相同的配置。

5. **TerracottaJobStore (Deprecated)**
   - 曾经是 Quartz 分布式调度的一个解决方案，但现在已经被弃用。
   - 如果你需要分布式调度功能，应该考虑其他现代的分布式调度系统或服务。

### 配置示例

#### 使用 RAMJobStore（默认）

如果你不指定任何 `JobStore`，Quartz 将默认使用 `RAMJobStore`。你也可以显式地设置它：

```properties
org.quartz.jobStore.class = org.quartz.simpl.RAMJobStore
```

#### 使用 JDBCJobStore

要使用 `JDBCJobStore`，首先需要初始化数据库表结构（可以从 Quartz 发行包中找到相应的 SQL 文件）。然后，在配置文件中进行如下设置：

```properties
# 使用 JobStoreTX 管理事务
org.quartz.jobStore.class = org.quartz.impl.jdbcjobstore.JobStoreTX
org.quartz.jobStore.driverDelegateClass = org.quartz.impl.jdbcjobstore.StdJDBCDelegate
org.quartz.jobStore.dataSource = myDS
org.quartz.jobStore.tablePrefix = QRTZ_
org.quartz.jobStore.isClustered = true # 启用集群模式
```

这里 `driverDelegateClass` 应该根据所使用的数据库类型选择合适的实现（例如 MySQL 可能需要 `org.quartz.impl.jdbcjobstore.MySQLDelegate`）。


## Quartz配置参考

### 线程池配置

在 Quartz 中，线程池用于执行触发的 Job。通过配置合适的线程池大小，可以有效地控制并发执行的 Job 数量，并优化系统资源的使用。Quartz 提供了灵活的方式来自定义和配置线程池。

### 默认线程池

Quartz 默认使用 `org.quartz.simpl.SimpleThreadPool` 作为其线程池实现。这个线程池是基于 Java 的 `ThreadPoolExecutor` 构建的，支持固定数量的工作线程，并且可以在调度器启动时进行配置。

### 配置线程池

你可以通过 Quartz 的配置文件（如 `quartz.properties`）来配置线程池。以下是一些常用的配置项：

```properties
# 指定线程池的实现类，默认为 SimpleThreadPool
org.quartz.threadPool.class = org.quartz.simpl.SimpleThreadPool

# 线程池中线程的数量，默认值通常为10
org.quartz.threadPool.threadCount = 25

# 线程优先级，范围从1（最低）到10（最高），默认为5
org.quartz.threadPool.threadPriority = 5

# 是否使能线程池中的守护线程模式，默认为true
org.quartz.threadPool.makeThreadsDaemons = true

# 可选参数，设置线程池的线程名称前缀
org.quartz.threadPool.threadsInheritContextClassLoaderOfInitializingThread = true
```

### 自定义线程池

如果你需要更复杂的线程管理策略，或者想要集成第三方线程池库（如 Apache Commons Pool 或者 Spring TaskExecutor），可以通过实现 `org.quartz.spi.ThreadPool` 接口来创建自定义线程池。

下面是一个简单的示例，展示如何在 Spring Boot 应用程序中配置 Quartz 使用自定义的线程池：

```java
import org.quartz.spi.ThreadPool;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Configuration
public class QuartzConfig {

    @Bean
    public ThreadPool quartzThreadPool() {
        return new ThreadPool() {
            private final ExecutorService executorService = Executors.newFixedThreadPool(30);

            @Override
            public int blockForAvailableThreads() {
                // 这里简化处理，返回0表示总是有可用线程
                return 0;
            }

            @Override
            public void initialize() {
                // 初始化逻辑
            }

            @Override
            public boolean runInThread(Runnable runnable) {
                if (runnable != null) {
                    executorService.submit(runnable);
                    return true;
                }
                return false;
            }

            @Override
            public int getPoolSize() {
                return ((ThreadPoolExecutor)executorService).getPoolSize();
            }

            @Override
            public int getMaxPoolSize() {
                return ((ThreadPoolExecutor)executorService).getMaximumPoolSize();
            }

            @Override
            public void shutdown(boolean waitForJobsToComplete) {
                executorService.shutdown();
            }
        };
    }
}
```

### 注意事项

- **线程数的选择**：线程池大小应该根据你的应用需求以及服务器硬件资源来确定。如果线程数过少，可能导致任务排队等待；如果过多，则可能消耗过多系统资源。
- **线程优先级**：调整线程优先级可以帮助你控制任务的紧急程度，但应谨慎使用，避免引发不可预测的行为。
- **守护线程**：设置为守护线程意味着当所有非守护线程结束时，JVM 可以退出而无需等待这些线程完成。这对于后台服务可能是有用的，但在某些情况下可能会导致未完成的任务被中断。


