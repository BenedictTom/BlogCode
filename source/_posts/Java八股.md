---
title: Java常见八股
main_color: "#707DE2"
categories: 面试者
tags:
  - Java
  - 八股
cover: https://img02.anheyu.com/adminuploads/1/2022/09/05/6315e1487d0f0.webp
---

# Java 八股面试题及答案

## 一、Java 基础 & 面向对象

### 1. final 关键字的作用有哪些？能修饰哪些元素？
**答案要点：**
- final 可修饰类、方法、变量。
- 修饰类：不可被继承。
- 修饰方法：不可被重写。
- 修饰变量：值不可变（常量），引用类型指向不可变但内容可变。

### 2. 接口和抽象类的区别是什么？在实际项目中如何选择？
**答案要点：**
- 接口只声明方法（Java 8+ 可有默认方法），抽象类可有成员变量、构造方法、已实现方法。
- Java 单继承多实现，接口用于规范，抽象类用于代码复用。
- 实际选择：无共性实现选接口，有部分实现选抽象类。

### 3. String、StringBuilder 和 StringBuffer 的区别是什么？线程安全体现在哪？
**答案要点：**
- String 不可变，线程安全。
- StringBuilder 可变，非线程安全，性能高。
- StringBuffer 可变，线程安全（方法加 synchronized），性能略低。

### 4. Java 中的异常体系结构是怎样的？checked exception 和 unchecked exception 有什么区别？
**答案要点：**
- Throwable → Error/Exception。
- Checked：编译期检查，必须捕获或声明（如 IOException）。
- Unchecked：运行时异常（RuntimeException 及其子类），可不处理（如 NullPointerException）。

### 5. 谈谈你对面向对象设计原则的理解（如开闭原则、里氏替换原则等）？
**答案要点：**
- 开闭原则：对扩展开放，对修改关闭。
- 里氏替换：子类可替换父类。
- 依赖倒置、单一职责、接口隔离、迪米特法则等。
- 实际开发中通过接口、抽象、组合等实现。

## 二、Java 并发编程

### 1. 线程有几种状态？状态之间如何转换？
**答案要点：**
- 新建（NEW）、就绪（RUNNABLE）、运行（RUNNING）、阻塞（BLOCKED）、等待（WAITING）、超时等待（TIMED_WAITING）、终止（TERMINATED）。
- 状态转换：start()、wait()/notify()、sleep()、join()、I/O 等。

### 2. synchronized 的实现原理是什么？锁优化有哪些策略（偏向锁、轻量级锁等）？
**答案要点：**
- synchronized 依赖对象头的 Mark Word，JVM 实现。
- 锁优化：偏向锁（无竞争）、轻量级锁（CAS）、重量级锁（操作系统互斥量）。
- 锁升级/降级机制。

### 3. volatile 的作用是什么？它能保证原子性吗？为什么？
**答案要点：**
- 保证可见性和有序性，不保证原子性。
- 适合状态标志、单例双检锁等场景。

### 4. CAS 是什么？它的缺点有哪些（ABA问题、自旋开销等）？
**答案要点：**
- Compare-And-Swap，无锁原子操作。
- 缺点：ABA 问题（可用版本号解决）、自旋消耗 CPU、只能保证一个变量原子性。

### 5. AQS 是什么？它是如何支持 ReentrantLock、CountDownLatch 等并发组件的？
**答案要点：**
- AbstractQueuedSynchronizer，队列同步器。
- 通过 FIFO 队列管理线程，模板方法设计。
- 支持独占/共享模式，底层实现 ReentrantLock、Semaphore、CountDownLatch 等。

### 6. 线程池的核心参数有哪些？拒绝策略有哪些？线程池如何复用线程？
**答案要点：**
- 核心参数：corePoolSize、maximumPoolSize、keepAliveTime、workQueue、threadFactory、handler。
- 拒绝策略：AbortPolicy、CallerRunsPolicy、DiscardPolicy、DiscardOldestPolicy。
- 线程复用：线程池维护线程队列，任务执行完不会销毁线程。

### 7. ThreadLocal 的原理是什么？使用时需要注意什么问题（如内存泄漏）？
**答案要点：**
- 每个线程有独立的 ThreadLocalMap，线程隔离。
- 注意内存泄漏（线程池复用时需 remove()），避免脏数据。

## 三、JVM 相关

### 1. JVM 内存模型分为哪几个区域？每个区域的作用是什么？
**答案要点：**
- 方法区（元空间）、堆、虚拟机栈、本地方法栈、程序计数器。
- 堆存对象，方法区存类元数据，栈存局部变量和方法调用。

### 2. 对象是如何创建、分配和回收的？GC Roots 包括哪些类型？
**答案要点：**
- new 创建对象，分配在堆上。
- 回收：可达性分析，GC Roots 包括栈变量、静态变量、本地方法栈引用等。

### 3. 常见的垃圾回收算法有哪些？G1、CMS、ZGC 的特点分别是什么？
**答案要点：**
- 标记-清除、标记-整理、复制算法、分代收集。
- G1：分区、低延迟、可预测停顿。
- CMS：并发标记清除，低停顿。
- ZGC：低延迟、并发、支持大堆。

### 4. 类加载机制的过程是怎样的？双亲委派模型的作用是什么？
**答案要点：**
- 加载、验证、准备、解析、初始化。
- 双亲委派：优先父加载器，防止类重复加载和安全问题。

### 5. 如何判断一个对象是否可以被回收？什么是可达性分析？
**答案要点：**
- 可达性分析：从 GC Roots 出发不可达即可回收。
- finalize()、引用类型（强/软/弱/虚引用）影响回收。

### 6. JVM 中有哪些常见的 OOM 异常？如何排查？
**答案要点：**
- Java heap space、GC overhead limit exceeded、Metaspace、Direct buffer memory。
- 排查：内存分析工具（jmap、MAT）、堆转储、代码优化。

## 四、Spring 框架相关

### 1. Spring IOC 容器的工作原理是什么？Bean 的生命周期是怎样的？
**答案要点：**
- IOC：依赖注入，BeanFactory/ApplicationContext 管理对象。
- 生命周期：实例化、属性注入、Aware、初始化、销毁。

### 2. Spring AOP 的底层实现原理是什么？使用了哪种动态代理方式？
**答案要点：**
- JDK 动态代理（接口）、CGLIB（类）。
- 通过代理对象织入切面逻辑。

### 3. Spring Boot 自动装配的原理是什么？@ConditionalOnClass 等条件注解的作用？
**答案要点：**
- @EnableAutoConfiguration + spring.factories。
- 条件注解根据类/Bean/配置等条件决定是否装配。

### 4. Spring Boot 中 starter 的作用是什么？如何自定义一个 starter？
**答案要点：**
- starter 封装依赖和自动配置，简化集成。
- 自定义 starter：新建模块，编写自动配置类和 spring.factories。

### 5. Spring Cloud 中常见的组件有哪些？它们各自解决什么问题？
**答案要点：**
- Eureka（注册中心）、Ribbon（负载均衡）、Feign（声明式调用）、Hystrix（熔断）、Config（配置中心）、Gateway（网关）。

### 6. Spring Boot 中的 Profile 是怎么使用的？如何实现多环境配置管理？
**答案要点：**
- @Profile 注解，application-{profile}.yml。
- 启动参数 --spring.profiles.active=dev。

## 五、MySQL 数据库

### 1. MySQL 的事务四大特性是什么？隔离级别有哪些？各自解决了哪些问题？
**答案要点：**
- 四大特性：原子性、一致性、隔离性、持久性（ACID）。
- 隔离级别：读未提交、读已提交、可重复读、串行化。
- 解决脏读、不可重复读、幻读等问题。

### 2. InnoDB 和 MyISAM 存储引擎的区别是什么？
**答案要点：**
- InnoDB 支持事务、行级锁、外键，崩溃可恢复。
- MyISAM 不支持事务、表级锁，速度快，适合读多写少。

### 3. 什么是索引？B+树的结构是怎样的？为什么使用 B+树而不是 B树？
**答案要点：**
- 索引加速查询，B+树所有数据在叶子节点，非叶节点只存 key。
- B+树适合范围查询，磁盘 I/O 少。

### 4. 覆盖索引、联合索引、最左匹配原则分别是什么？
**答案要点：**
- 覆盖索引：查询只用到索引，不访问表。
- 联合索引：多个字段组成的索引。
- 最左匹配：索引从最左字段开始连续匹配。

### 5. SQL 查询慢的原因可能有哪些？如何进行性能调优？
**答案要点：**
- 无索引、索引失效、数据量大、SQL 设计不合理、硬件瓶颈。
- 优化：加索引、分库分表、SQL 优化、缓存、硬件升级。

### 6. Explain 执行计划中的 key_len、type、Extra 字段分别代表什么？
**答案要点：**
- key_len：索引长度。
- type：连接类型（ALL、index、range、ref、eq_ref、const、system、NULL）。
- Extra：额外信息（如 Using index、Using filesort）。

## 六、Redis 缓存相关

### 1. Redis 支持哪些数据类型？应用场景分别是什么？
**答案要点：**
- String、List、Set、Hash、ZSet（有序集合）、Bitmap、HyperLogLog、Geo。
- 应用：缓存、排行榜、计数器、消息队列、分布式锁等。

### 2. Redis 的持久化机制有哪几种？RDB 和 AOF 的区别是什么？
**答案要点：**
- RDB（快照）、AOF（追加日志）、混合持久化。
- RDB 适合全量备份，AOF 适合高可靠。

### 3. Redis 缓存穿透、击穿、雪崩的解决方案分别是什么？
**答案要点：**
- 穿透：布隆过滤器、缓存空对象。
- 击穿：加互斥锁、热点数据永不过期。
- 雪崩：加随机过期、限流降级。

### 4. Redis 的淘汰策略有哪些？默认使用的是哪种？
**答案要点：**
- noeviction、allkeys-lru、volatile-lru、allkeys-random、volatile-random、volatile-ttl。
- 默认 noeviction。

### 5. Redis 单线程为什么这么快？Redis 6.0 引入了多线程，是为了解决什么问题？
**答案要点：**
- 单线程避免上下文切换，I/O 多路复用。
- 6.0 多线程用于网络 I/O，提高并发处理能力。

### 6. Redis 分布式锁的实现方式有哪些？如何避免死锁？
**答案要点：**
- setnx+expire、RedLock。
- 避免死锁：设置超时时间、定期续约、幂等性操作。

## 七、RabbitMQ 消息队列

### 1. RabbitMQ 的核心组成部分有哪些？交换机的类型有哪些？
**答案要点：**
- 组成：生产者、消费者、队列、交换机、绑定、路由键。
- 交换机类型：direct、fanout、topic、headers。

### 2. 如何保证消息的顺序性？在哪些场景下会出现乱序？
**答案要点：**
- 保证顺序：同一队列、单一消费者。
- 乱序：多消费者、消息重试、网络延迟。

### 3. 如何确保消息不丢失？生产端确认机制和消费端 ACK 机制是怎么回事？
**答案要点：**
- 生产端 confirm，消费端手动 ack。
- 持久化队列、消息、事务。

### 4. 死信队列是什么？如何设置？适用于哪些业务场景？
**答案要点：**
- 死信队列：消息被拒绝、过期、队列满时转入。
- 设置：x-dead-letter-exchange、x-dead-letter-routing-key。
- 场景：延迟消息、异常处理、补偿机制。

### 5. RabbitMQ 和 Kafka 的主要区别是什么？分别适用于什么场景？
**答案要点：**
- RabbitMQ：低延迟、强一致性、适合事务、短消息。
- Kafka：高吞吐、分区、适合大数据、日志、流处理。

## 八、Python & Docker & Git & Linux

### 1. Python 中的 GIL 是什么？它对多线程程序的影响是什么？
**答案要点：**
- 全局解释器锁（Global Interpreter Lock）。
- 同一时刻只有一个线程执行字节码，多线程无法利用多核 CPU。

### 2. 列表推导式和生成器表达式的区别是什么？
**答案要点：**
- 列表推导式返回列表，立即计算。
- 生成器表达式返回生成器，惰性计算，节省内存。

### 3. Docker 和虚拟机的区别是什么？Docker 的三大核心概念是什么？
**答案要点：**
- Docker 基于容器，虚拟机基于硬件虚拟化。
- Docker 启动快、资源占用少。
- 三大核心：镜像（Image）、容器（Container）、仓库（Registry）。

### 4. Git 的常用命令有哪些？merge 和 rebase 的区别是什么？
**答案要点：**
- 常用命令：clone、pull、push、commit、branch、checkout、merge、rebase、log、status。
- merge：保留分支历史，产生新合并节点。
- rebase：线性历史，变基到目标分支。

### 5. Linux 中常用的查看日志、监控进程的命令有哪些？
**答案要点：**
- 查看日志：tail、less、cat、grep。
- 监控进程：ps、top、htop、pstree。

### 6. 如何查找并杀死某个端口的进程？比如占用 8080 端口的进程？
**答案要点：**
- 查找：`lsof -i:8080` 或 `netstat -anp | grep 8080`。
- 杀死：`kill -9 <pid>`。