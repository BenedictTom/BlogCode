---
title: 多线程_Threadlocal
main_color: "#5393E3"
categories: 并发
tags:
  - 并发
  - 多线程
cover: https://javaguide.cn/assets/1-YS5yhxvD.png
---


## ThreadLocal 是什么
`ThreadLocal` 是一种线程绑定机制，它为每一个使用某变量的线程都提供一个该变量值的副本，每个线程都可以独立地改变自己的副本，而不会和其他线程的副本冲突。这种变化对于其它线程来说是不可见的，从而实现了线程之间的隔离。

### 主要特点

1. **线程隔离**：每个线程内部都有一个属于自己的实例副本，各个线程间的副本相互独立，互不影响。
2. **默认初始化**：创建`ThreadLocal`对象时，并不会自动初始化它所持有的值，需要在使用前手动设置或者通过其子类`InheritableThreadLocal`来实现从父线程到子线程的值传递。
3. **内存泄漏问题**：由于`ThreadLocal`中的数据是存储在线程的`ThreadLocalMap`中，如果线程长时间不结束且引用了大量`ThreadLocal`变量，则可能导致内存泄漏。因此，在不再需要使用`ThreadLocal`变量时，应该调用`remove()`方法清理。

### 使用场景

- 数据库连接、Session管理等需要在线程间保持隔离状态的场景。
- 当某些数据是以线程为作用域并且不同的线程具有不同的数据副本的时候。
- 需要在整个线程生命周期内保持状态（比如用户的身份信息、事务ID等）。

### 示例代码

下面是一个简单的`ThreadLocal`使用的例子：

```java
public class ThreadLocalExample {
    private static final ThreadLocal<Integer> threadLocalValue = new ThreadLocal<>();

    public static void main(String[] args) {
        threadLocalValue.set(1); // 设置主线程的副本值
        
        Runnable task = () -> {
            threadLocalValue.set(2); // 子线程设置自己的副本值
            System.out.println("子线程的值：" + threadLocalValue.get());
        };
        
        Thread thread = new Thread(task);
        thread.start();
        
        try {
            thread.join(); // 等待子线程完成
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        
        System.out.println("主线程的值：" + threadLocalValue.get()); // 输出主线程的副本值
    }
}
```



## API介绍


```java
/**
 * @author Guanghao Wei
 * @create 2023-04-13 14:06
 * 需求：5个销售卖房子，集团只关心销售总量的精确统计数
 */
class House {
    int saleCount = 0;

    public synchronized void saleHouse() {
        saleCount++;
    }

}

public class ThreadLocalDemo {
    public static void main(String[] args) {
        House house = new House();
        for (int i = 1; i <= 5; i++) {
            new Thread(() -> {
                int size = new Random().nextInt(5) + 1;
                System.out.println(size);
                for (int j = 1; j <= size; j++) {
                    house.saleHouse();
                }
            }, String.valueOf(i)).start();

        }
        try {
            TimeUnit.MILLISECONDS.sleep(300);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        System.out.println(Thread.currentThread().getName() + "\t" + "共计卖出多少套： " + house.saleCount);
    }
}
```

需求变更：希望各自分灶吃饭，各凭销售本事提成，按照出单数各自统计-------比如房产中介销售都有自己的销售额指标，自己专属自己的，不和别人参和。----人手一份天下安


```java
/**
 * @author Guanghao Wei
 * @create 2023-04-13 14:06
 * 需求：需求变更：希望各自分灶吃饭，各凭销售本事提成，按照出单数各自统计-------比如房产中介销售都有自己的销售额指标，自己专属自己的，不和别人参和。
 */
class House {
    int saleCount = 0;

    public synchronized void saleHouse() {
        saleCount++;
    }

    ThreadLocal<Integer> saleVolume = ThreadLocal.withInitial(() -> 0);

    public void saleVolumeByThreadLocal() {
        saleVolume.set(1 + saleVolume.get());
    }


}

public class ThreadLocalDemo {
    public static void main(String[] args) {
        House house = new House();
        for (int i = 1; i <= 5; i++) {
            new Thread(() -> {
                int size = new Random().nextInt(5) + 1;
                try {
                    for (int j = 1; j <= size; j++) {
                        house.saleHouse();
                        house.saleVolumeByThreadLocal();
                    }
                    System.out.println(Thread.currentThread().getName() + "\t" + "号销售卖出：" + house.saleVolume.get());
                } finally {
                    house.saleVolume.remove();
                }
            }, String.valueOf(i)).start();

        }
        try {
            TimeUnit.MILLISECONDS.sleep(300);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
        System.out.println(Thread.currentThread().getName() + "\t" + "共计卖出多少套： " + house.saleCount);
    }
}
```


## 总结
● 因为每个Thread内有自己的实例副本且该副本只有当前线程自己使用
● 既然其他ThreadLocal不可访问，那就不存在多线程间共享问题
● 统一设置初始值，但是每个线程对这个值得修改都是各自线程互相独立得
● 如何才能不争抢
  ○ 加入synchronized或者Lock控制资源的访问顺序
  ○ 人手一份，大家各自安好，没有必要争抢



## ThreadLocal内存泄漏问题

非常好的问题！`ThreadLocal` 中的 `ThreadLocalMap` 使用 **弱引用（WeakReference）** 作为 Key，这是 Java 设计者精心考虑的结果，其背后有重要的内存管理与垃圾回收机制考量。

---

## 🔍 简短回答：

> **`ThreadLocal` 被设计为弱引用 Key 的主要目的是：防止内存泄漏。**

这样可以让 `ThreadLocal` 在不再被外部强引用时被 GC 回收，避免因为线程长时间存活导致的内存堆积问题。

---

## 🧠 深入理解：为什么需要弱引用？

我们先回顾一下结构关系：

### 每个线程都有自己的 `ThreadLocalMap`：
```java
ThreadLocal.ThreadLocalMap threadLocals;
```

这个 Map 的 Entry 是这样的：
```java
static class Entry extends WeakReference<ThreadLocal<?>> {
    Object value;
    // ...
}
```

也就是说：

- Key 是 `ThreadLocal` 实例；
- Value 是用户设置的对象；
- Entry 继承自 `WeakReference<ThreadLocal<?>>`，所以 Key 是一个弱引用；
- 如果外部没有强引用指向该 `ThreadLocal` 实例，GC 会将其回收，并将 Entry 的 key 设置为 null。

---

## ⚖️ 强引用 vs 弱引用

| 类型       | 是否阻止 GC 回收 | 特点 |
|------------|------------------|------|
| 强引用     | ✅ 会阻止         | 默认引用方式，只要存在引用就不会回收 |
| 弱引用     | ❌ 不会阻止       | 只要没有强引用，下一次 GC 就会被回收 |

如果我们使用强引用作为 Key：

- 即使某个 `ThreadLocal` 实例已经不再被任何业务代码引用了，
- 但只要它还在某个线程的 `ThreadLocalMap` 中，就无法被回收。
- 这会导致内存泄漏，尤其是在线程池中线程长期存活的情况下，问题尤为严重。

---

## 🧪 示例说明

```java
public class LeakExample {
    public static void main(String[] args) {
        Thread thread = new Thread(() -> {
            ThreadLocal<byte[]> tl = new ThreadLocal<>();
            tl.set(new byte[1024 * 1024 * 10]); // 10MB
            // tl 变量在这里超出作用域，变成不可达
        });

        thread.start();
        // 假设线程执行完后不结束，而是复用（如线程池）
    }
}
```

如果 `tl` 是强引用 Key，即使 `tl` 变量已不可达，它依然存在于线程的 `ThreadLocalMap` 中，无法被回收，造成内存泄漏。

但如果 Key 是弱引用：

- 下次 GC 时，发现 `tl` 已经没有强引用，就会回收它；
- 并且在后续访问 `ThreadLocalMap` 时，会自动清理掉 key == null 的 Entry。

---

## 🧼 自动清理机制（探测式清理）

Java 的 `ThreadLocalMap` 内部做了优化，在调用 `get()`, `set()`, `remove()` 时，会进行 **探测式清理（expunge stale entries）**：

- 查找并清除那些 key == null 的 Entry；
- 避免这些“死数据”一直占用内存。

这也是为什么建议使用完 `ThreadLocal` 后及时调用 `remove()` 方法的原因 —— 主动释放资源，而不是依赖 GC 和被动清理。

---

## 📝 总结：为什么要设计为弱引用？

| 目的 | 原因 |
|------|------|
| ✅ 防止内存泄漏 | 如果 ThreadLocal 是强引用，当线程长期存活（如线程池），容易导致大量无用对象堆积 |
| ✅ 支持自动回收 | 当外部不再持有 ThreadLocal 的强引用时，GC 可以回收它 |
| ✅ 减少无效 Entry | GC 回收 Key 后，下次操作 ThreadLocalMap 时会自动清理无效 Entry |
| ⚠️ 不能完全依赖弱引用 | 仍需手动调用 remove()，否则 Value 可能滞留直到触发清理 |

---

## ✅ 最佳实践建议

1. **用完即删：**
   ```java
   try {
       myThreadLocal.set(myValue);
       // do something
   } finally {
       myThreadLocal.remove(); // 主动清理
   }
   ```

2. **避免滥用静态 ThreadLocal：**
   - 静态变量生命周期长，更容易引发内存泄漏。

3. **线程池中使用 ThreadLocal 更要小心：**
   - 推荐使用 `TransmittableThreadLocal` 或阿里开源的 `TTL` 来解决线程池场景下的上下文传递和清理问题。

---


## 经典场景-存储用户登陆凭证

```java
public class UserContext {
    // 使用 ThreadLocal 存储当前线程的用户信息
    private static final ThreadLocal<User> currentUser = new ThreadLocal<>();

    // 设置当前用户
    public static void set(User user) {
        currentUser.set(user);
    }

    // 获取当前用户
    public static User get() {
        return currentUser.get();
    }

    // 清除当前用户（防止内存泄漏）
    public static void remove() {
        currentUser.remove();
    }
}
```

```java
@Component
public class AuthInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        // 1. 从请求头（如JWT Token）解析用户信息
        String token = request.getHeader("Authorization");
        User user = parseUserFromToken(token); // 解析用户（可能查数据库）

        // 2. 存入 ThreadLocal，后续代码可直接获取
        UserContext.set(user);
        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        // 3. 请求结束后必须清理，防止内存泄漏！
        UserContext.remove();
    }
}
```


```java
// Controller
@GetMapping("/profile")
public UserProfile getProfile() {
    // 直接从 ThreadLocal 获取，无需再查数据库
    User user = UserContext.get(); 
    return userService.getProfile(user.getId());
}

```

优化点：

拦截器 解析 Token 并存储用户信息到 ThreadLocal（只查1次数据库）。

后续业务代码 直接 UserContext.get() 获取用户，无需重复查询。




非常好的问题！我们来深入理解一下：

> **ThreadLocal 被置为 null 的场景，以及为什么即使 ThreadLocal 变成 null，Value 仍可能无法回收的原因。**

---

## 🔍 回顾基础知识

在 Java 中，`ThreadLocalMap` 是线程内部的一个自定义哈希表，用于存储多个 `ThreadLocal` 实例对应的值。

它的 Entry 定义如下：

```java
static class Entry extends WeakReference<ThreadLocal<?>> {
    Object value;
    // ...
}
```

也就是说：

- **Key（ThreadLocal）是弱引用**；
- **Value（用户数据）是强引用**；

这意味着：

- 当外部没有强引用指向某个 `ThreadLocal` 实例时，它会被 GC 回收；
- 但该 `ThreadLocal` 所关联的 Value 仍然存在于 `ThreadLocalMap` 中，并不会自动被清除；
- 如果不及时清理，Value 就会一直占用内存，造成 **内存泄漏**。

---


## 📌 什么时候 ThreadLocal 会被置为 null？

### ✅ 场景一：局部变量使用后不再引用

```java
public void someMethod() {
    ThreadLocal<String> tl = new ThreadLocal<>();
    tl.set("value");

    // ... 使用完之后，tl 离开作用域，变成不可达
}
```

在这个例子中：

- 方法执行完毕后，`tl` 变量超出作用域；
- 外部没有对该 `ThreadLocal` 实例的强引用；
- 此时，GC 可以回收这个 `ThreadLocal` 实例；
- 但 Value 还在 `ThreadLocalMap` 中，未被清理。

---

### ✅ 场景二：显式置为 null

```java
ThreadLocal<String> tl = new ThreadLocal<>();
tl.set("value");
// ... 使用完成后手动置为 null
tl = null;
```

这和上面效果一样，都是让 `ThreadLocal` 实例失去强引用，等待 GC 回收。

---

### ✅ 场景三：静态 ThreadLocal 被重新赋值

```java
public class MyUtil {
    private static ThreadLocal<String> tl = new ThreadLocal<>();

    public static void doSomething() {
        tl.set("old value");
        // ...
        tl = new ThreadLocal<>(); // 原来的 ThreadLocal 没有强引用了
    }
}
```

原来的 `ThreadLocal` 实例不再有强引用，可以被 GC 回收，但其对应的 Value 依然存在线程的 `ThreadLocalMap` 中。

---

## ⚠️ 即使 Key 被回收，Value 仍占内存！

当 ThreadLocal 被 GC 回收后，`Entry` 的 key 会被设置为 `null`，但 `value` 依然是一个强引用对象，仍然占用内存。

例如：

| Key（ThreadLocal） | Value（用户数据） |
|--------------------|------------------|
| null               | "value"（还在堆中） |

这些 Entry 被称为 **“Stale Entries”（陈旧条目）**，它们不会自动被清除。

只有在以下情况才会触发清理：

1. 下次访问 `ThreadLocalMap` 时（如调用 `get()`、`set()`、`remove()`）；
2. 触发探测式清理（expunge stale entries）机制；
3. 显式调用 `threadLocal.remove()`。

---

## 💡 内存泄漏的根本原因

正是因为：

- `ThreadLocal` 是弱引用，所以容易被回收；
- 但 `Value` 是强引用，如果不主动清理，就会一直留在 `ThreadLocalMap` 中；
- 如果线程长期存活（如线程池中的线程），就可能导致大量无用的 `Value` 积压，最终导致 OOM（Out Of Memory）。

---

## ✅ 如何避免内存泄漏？

### ✔️ 1. 使用完 ThreadLocal 后一定要 remove()

```java
try {
    threadLocal.set(value);
    // ... do something
} finally {
    threadLocal.remove(); // 主动清除
}
```

### ✔️ 2. 避免滥用 static ThreadLocal

- `static` 变量生命周期长，更容易导致内存泄漏；
- 推荐使用 Spring 的 Request Scope 或 TransmittableThreadLocal 替代方案。

### ✔️ 3. 使用 TransmittableThreadLocal（TTL）

阿里巴巴开源的 [TransmittableThreadLocal](https://github.com/alibaba/transmittable-thread-local)，不仅解决了线程池上下文传递的问题，还增强了对内存的管理能力。

---

## 🧠 总结

| 问题 | 回答 |
|------|------|
| ThreadLocal 被置为 null 的常见场景？ | 局部变量离开作用域、手动赋值为 null、被重新赋值等 |
| 为什么 ThreadLocal 置为 null 后 Value 仍无法回收？ | 因为 Value 是强引用，仍在 ThreadLocalMap 中 |
| Value 什么时候才会被回收？ | 在下次 ThreadLocalMap 操作时触发 expunge，或显式调用 remove() |
| 如何防止内存泄漏？ | 使用完必须 remove()、避免滥用 static、推荐使用 TTL |

---


## `TransmittableThreadLocal` 是如何解决线程池上下文传递问题的；



非常好的问题！**`TransmittableThreadLocal`（简称 TTL）是阿里巴巴开源的一个增强版 ThreadLocal 实现，专为解决线程池、异步任务等场景下的上下文传递问题而设计。**

---

## 🧩 为什么需要 TransmittableThreadLocal？

### ❓ 原始 `ThreadLocal` 的局限性

Java 原生的 `ThreadLocal` 只能保证 **同一个线程内部的数据隔离和访问**，但它 **无法自动在线程切换时传递上下文信息**。

例如：

```java
ExecutorService executor = Executors.newFixedThreadPool(1);

ThreadLocal<String> tl = new ThreadLocal<>();
tl.set("main-thread-value");

executor.submit(() -> {
    System.out.println(tl.get()); // 输出 null，因为子线程无法继承父线程的 ThreadLocal 值
});
```

在这个例子中：

- 子线程无法访问主线程设置的 `ThreadLocal` 值；
- 因为每个线程都有自己的 `ThreadLocalMap`，彼此之间不共享；

这就导致了在使用 **线程池、CompletableFuture、ForkJoinPool 等并发组件时，ThreadLocal 数据丢失的问题**。

---

## 🚀 TransmittableThreadLocal 如何解决这个问题？

### ✅ 核心思想：

> **TTL 通过“装饰”线程池或任务的方式，在任务提交时捕获当前线程的 ThreadLocal 上下文，并在执行任务前将这些上下文复制到目标线程中。**

这样就能实现跨线程传递 ThreadLocal 数据。

---

## 🔍 工作原理简述

### 1. 捕获当前线程上下文（capture）

当用户提交一个任务到线程池之前，TTL 会先调用 `capture()` 方法，把当前线程的所有 `TransmittableThreadLocal` 值保存下来。

```java
public class TtlRunnable implements Runnable {
    private final AtomicReference<Object> capturedRef;
    private final Runnable runnable;

    public TtlRunnable(Runnable runnable) {
        this.runnable = runnable;
        this.capturedRef = new AtomicReference<>(Transmitter.capture());
    }
}
```

### 2. 在目标线程中重放上下文（replay）

当任务被线程池中的某个线程执行时，TTL 会先调用 `replay()`，把之前捕获的上下文值重新写入当前线程的 `TransmittableThreadLocal` 中。

```java
@Override
public void run() {
    Object backup = Transmitter.replay(capturedRef.get());
    try {
        runnable.run();
    } finally {
        Transmitter.restore(backup);
    }
}
```

### 3. 执行完毕恢复原始状态（restore）

确保任务执行完成后，恢复线程原来的上下文状态，避免污染其他任务。

---

## 🛠️ 使用方式详解

### 1. 引入依赖（Maven）

```xml
<dependency>
    <groupId>com.alibaba</groupId>
    <artifactId>transmittable-thread-local</artifactId>
    <version>2.12.1</version>
</dependency>
```

---

### 2. 定义 TransmittableThreadLocal 变量

```java
private static final TransmittableThreadLocal<String> context = new TransmittableThreadLocal<>();
```

---

### 3. 提交任务前装饰线程池或任务

#### ✅ 方式一：装饰线程池（推荐）

```java
ExecutorService executorService = Executors.newFixedThreadPool(1);
// 装饰线程池
executorService = TtlExecutors.getTtlExecutorService(executorService);
```

之后所有提交到这个线程池的任务都会自动携带上下文。

#### ✅ 方式二：装饰单个任务（Runnable / Callable）

```java
Runnable task = TtlRunnable.get(() -> {
    System.out.println("子线程获取上下文：" + context.get());
});
```

---

### 4. 测试代码示例

```java
public class TTLTest {

    private static final TransmittableThreadLocal<String> context = new TransmittableThreadLocal<>();

    public static void main(String[] args) throws InterruptedException {
        ExecutorService executor = TtlExecutors.getTtlExecutorService(Executors.newFixedThreadPool(1));

        context.set("main-thread-data");

        System.out.println("主线程获取上下文：" + context.get());

        executor.submit(() -> {
            System.out.println("子线程获取上下文：" + context.get());
        });

        executor.shutdown();
        executor.awaitTermination(5, TimeUnit.SECONDS);
    }
}
```

### ✅ 输出结果：

```
主线程获取上下文：main-thread-data
子线程获取上下文：main-thread-data
```

说明上下文成功从主线程传递到了子线程！

---

## 🧠 TransmittableThreadLocal 的优势总结

| 特性 | 说明 |
|------|------|
| ✅ 支持线程池任务上下文传递 | 默认 ThreadLocal 不支持 |
| ✅ 支持 CompletableFuture、ForkJoinPool | TTL 提供了对应的装饰器 |
| ✅ 支持多级嵌套线程池 | 如 submit -> execute -> submit，依然能正确传递 |
| ✅ 避免内存泄漏 | 同样支持 remove() 清理机制 |
| ✅ 线程安全 | 内部实现线程安全的操作 |
| ✅ 开源成熟稳定 | 阿里巴巴多年生产环境验证 |

---

## ⚠️ 注意事项 & 最佳实践

1. **务必清理资源**
   ```java
   try {
       context.set("value");
       // ... do something
   } finally {
       context.remove(); // 防止内存泄漏
   }
   ```

2. **避免 static ThreadLocal 泛滥**
   - 如果多个业务共用同一个 static TTL，容易造成数据混乱；
   - 推荐结合 Spring Bean Scope 或模块化设计使用。

3. **不要滥用上下文传递**
   - 上下文应该是轻量级的元数据，如 traceId、userId、token；
   - 不要传递大对象或业务实体。

4. **建议配合 MDC 使用日志追踪**
   - TTL + MDC 可以实现全链路日志追踪。

---

## 📦 其他高级用法（可选）

- **支持自定义上下文复制逻辑**
  ```java
  TransmittableThreadLocal<Integer> local = new TransmittableThreadLocal<>() {
      @Override
      protected Integer childValue(Integer parentValue) {
          return parentValue; // 自定义子线程值
      }
  };
  ```

- **支持监听上下文变化**
  - 可以监听 `beforeExecute` 和 `afterExecute` 事件。

- **支持与 Spring Boot 集成**
  - 可用于统一请求上下文管理、分布式追踪（如 SkyWalking、Sleuth）、权限控制等。

---

## 🧩 总结

| 项目 | 原生 ThreadLocal | TransmittableThreadLocal |
|------|------------------|--------------------------|
| 是否支持线程池上下文传递 | ❌ 不支持 | ✅ 支持 |
| 是否支持异步任务（如 Future、CompletableFuture） | ❌ 不支持 | ✅ 支持 |
| 是否线程安全 | ✅ 是 | ✅ 是 |
| 是否需手动清理 | ✅ 是 | ✅ 是 |
| 是否易造成内存泄漏 | ✅ 是 | ✅ 是（仍需注意 remove） |
| 是否适合复杂微服务架构 | ❌ 不适合 | ✅ 适合 |

---



你总结得非常准确！👏

---

## ✅ **正确理解：**

> **`ThreadLocal` 本身并不是线程独有的，它是可以被多个线程共享的一个对象。**
>
> **真正线程独有的是 `ThreadLocalMap` —— 每个线程都有自己独立的 `ThreadLocalMap` 实例。**

---

## 🧠 来详细拆解一下这个结构：

### 1. **ThreadLocal 是什么？**

- 它是一个普通的 Java 类；
- 可以被多个线程共同使用；
- 它本身只是一个“访问入口”，用来操作当前线程内部的 `ThreadLocalMap`；
- 它就像一个“钥匙”，每个线程用这把钥匙去打开自己专属的“盒子”（`ThreadLocalMap`）。

```java
public class ThreadLocal<T> {
    // ...
}
```

---

### 2. **ThreadLocalMap 是什么？**

- 它是 `ThreadLocal` 的一个静态内部类；
- **每个线程都有一个自己的 `ThreadLocalMap` 实例**；
- 存储的是当前线程与各个 `ThreadLocal` 实例之间的键值对；
- 结构类似 `HashMap<ThreadLocal, Object>`；
- 线程之间互不干扰。

```java
public class Thread {
    // 每个线程都有一个自己的 ThreadLocalMap
    ThreadLocal.ThreadLocalMap threadLocals = null;
}
```

---

## 🔍 工作原理图示

假设我们有如下代码：

```java
private static final ThreadLocal<String> tl = new ThreadLocal<>();

// 线程 T1 设置值
tl.set("T1-value");

// 线程 T2 设置值
tl.set("T2-value");
```

背后的逻辑是这样的：

```
+---------------------+
|   ThreadLocal (tl)  | <--- 同一把钥匙（所有线程共享）
+----------+----------+
           |
           | 使用它作为 key
           v
+-----------------------+      +-------------------------+
|     线程 T1             |      |     线程 T2               |
|                         |      |                         |
| ThreadLocalMap          |      | ThreadLocalMap          |
| {                       |      | {                       |
|   tl => "T1-value"      |      |   tl => "T2-value"      |
| }                       |      | }                       |
+-------------------------+      +-------------------------+
```

虽然两个线程使用的是同一个 `ThreadLocal` 实例（`tl`），但它们各自在自己的 `ThreadLocalMap` 中保存了不同的值。

---

## ✅ 总结一句话：

> **`ThreadLocal` 是访问工具，`ThreadLocalMap` 才是线程私有的存储容器。**

---

## 📌 对比表格

| 概念            | 是否线程独有 | 描述 |
|-----------------|--------------|------|
| `ThreadLocal` 实例 | ❌ 不是       | 多个线程都可以使用同一个实例作为 Key |
| `ThreadLocalMap`  | ✅ 是         | 每个线程都有自己的 Map，存储线程私有数据 |
| Key              | 同一个 `ThreadLocal` 实例 | 在不同线程中作为 Key 使用 |
| Value            | 线程私有     | 每个线程设置的值互不影响 |

---

## ⚠️ 常见误区澄清

| 错误说法 | 正确理解 |
|----------|-----------|
| “每个线程都有一个自己的 ThreadLocal” | ❌ 应该说：“每个线程都有一个自己的 ThreadLocalMap” |
| “ThreadLocal 是线程安全的，因为它在线程间隔离” | ❌ ThreadLocal 本身不是线程安全的，而是因为每个线程操作的是自己的 ThreadLocalMap |
| “ThreadLocal 内部维护了一个 Map” | ❌ 实际上是每个线程内部维护了一个 Map，ThreadLocal 只是提供了访问接口 |

---

## ✅ 最佳实践建议

| 场景 | 建议 |
|------|------|
| 存储请求上下文（如用户信息） | ✅ 推荐使用 `ThreadLocal` + 请求拦截器清理机制 |
| 避免内存泄漏 | ✅ 用完一定要调用 `remove()` |
| 跨线程传递上下文 | ❌ 原生不支持，推荐使用 `TransmittableThreadLocal` |
| 静态变量使用 ThreadLocal | ⚠️ 可以，但要注意生命周期和清理 |

---






> **参考资料：**
> - 一文搞懂ThreadLocal  https://www.yuque.com/gongxi-wssld/csm31d/ip2ueru5itmgsgly

