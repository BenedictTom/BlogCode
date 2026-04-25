---
title: 多线程_AQS源码分析
main_color: "#5393E3"
categories: 并发
tags:
  - 并发
  - 多线程
cover: https://free.picui.cn/free/2026/03/28/69c74d88b7f09.jpg
---

# AQS源码深度分析

## 目录
- [1. ReentrantLock数据结构与继承关系](#1-reentrantlock数据结构与继承关系)
- [2. AQS核心机制](#2-aqs核心机制)
- [3. 加锁流程详解](#3-加锁流程详解)
- [4. 解锁流程详解](#4-解锁流程详解)
- [5. 公平锁vs非公平锁](#5-公平锁vs非公平锁)
- [6. 相关面试题](#6-相关面试题)

---

## 1. ReentrantLock数据结构与继承关系

### 1.1 整体架构

`ReentrantLock` 内部核心实现主要靠三个内部类来支撑：

```java
public class ReentrantLock implements Lock, java.io.Serializable {
    private final Sync sync;
    
    abstract static class Sync extends AbstractQueuedSynchronizer { ... }
    static final class NonfairSync extends Sync { ... }
    static final class FairSync extends Sync { ... }
}
```

**核心思想**：`ReentrantLock` 只是一个壳子，真正的加锁/解锁逻辑都委托给了 `Sync` 体系。

### 1.2 继承关系图

```
ReentrantLock
    └── Sync (abstract) extends AbstractQueuedSynchronizer
        ├── NonfairSync (非公平锁实现)
        └── FairSync (公平锁实现)
```

### 1.3 核心内部类详解

#### 1.3.1 Sync（抽象基类）

```java
abstract static class Sync extends AbstractQueuedSynchronizer {
    // 核心字段
    private volatile int state;        // 锁状态：0=空闲，>0=被占用
    private transient Thread exclusiveOwnerThread; // 持有锁的线程
    
    // 核心方法
    abstract void lock();
    final boolean nonfairTryAcquire(int acquires);
    protected final boolean tryRelease(int releases);
}
```

**关键特点**：
- 继承了 **AQS (AbstractQueuedSynchronizer)**
- **state** 表示锁的重入次数（0 = 没人持有，>0 = 被某个线程持有，值为重入次数）
- **exclusiveOwnerThread** 记录持有锁的线程
- 提供了 **acquire/release** 模板，具体由子类（公平/非公平）实现获取逻辑

#### 1.3.2 NonfairSync（非公平锁实现）

```java
static final class NonfairSync extends Sync {
    final void lock() {
        if (compareAndSetState(0, 1))   // 尝试直接抢锁
            setExclusiveOwnerThread(Thread.currentThread());
        else
            acquire(1);  // 没抢到，进入AQS队列排队
    }
    
    protected final boolean tryAcquire(int acquires) {
        return nonfairTryAcquire(acquires);
    }
}
```

**主要特点**：**插队机制**
- 线程调用 `lock()` 时，先尝试用 `compareAndSetState(0, 1)` 抢锁（CAS）
- 如果成功，直接获得锁 → 不管队列里是否有人在等
- 如果失败，才会走 AQS 的队列挂起逻辑

**优点**：吞吐量高，减少线程切换
**缺点**：可能导致**饥饿**（一直有新线程插队，队列里的老线程迟迟拿不到锁）

#### 1.3.3 FairSync（公平锁实现）

```java
static final class FairSync extends Sync {
    final void lock() {
        acquire(1); // 直接交给AQS的公平获取逻辑
    }
    
    protected final boolean tryAcquire(int acquires) {
        Thread current = Thread.currentThread();
        int c = getState();
        if (c == 0) {
            if (!hasQueuedPredecessors() && compareAndSetState(0, acquires)) {
                setExclusiveOwnerThread(current);
                return true;
            }
        }
        else if (current == getExclusiveOwnerThread()) {
            setState(c + acquires);
            return true;
        }
        return false;
    }
}
```

**主要特点**：**严格排队**
- 每次获取锁时，先判断队列里是否有前驱节点
- 如果有人在排队 → 必须排队，不能插队
- 只有队列前面没人或者自己在队首，才能尝试 `CAS` 抢锁
- `hasQueuedPredecessors()` 就是公平的关键 → 判断是否有线程在前面排队

**优点**：线程获取锁的顺序和请求顺序一致，**避免饥饿**
**缺点**：吞吐量比非公平锁低

---

## 2. AQS核心机制

### 2.1 AQS核心字段

```java
public abstract class AbstractQueuedSynchronizer extends AbstractOwnableSynchronizer {
    // 核心状态字段
    private volatile int state;        // 同步状态
    
    // CLH队列头尾指针
    private transient volatile Node head;
    private transient volatile Node tail;
    
    // 持有锁的线程（继承自AbstractOwnableSynchronizer）
    private transient Thread exclusiveOwnerThread;
}
```

**核心数据结构**：
- **state**（int）：表示同步状态（如锁是否被占用，重入次数，信号量数量等）
- **CLH 队列**：一个 FIFO 双向队列，用来挂起等待的线程（`head`、`tail` 节点）

### 2.2 AQS核心方法分类

#### 2.2.1 独占模式（Exclusive）

👉 用于 **互斥锁**（如 ReentrantLock）

| 方法 | 作用 | 实现方 |
|------|------|--------|
| `acquire(int arg)` | 独占模式入口方法 | AQS实现 |
| `tryAcquire(int arg)` | 真正尝试获取锁 | 子类实现 |
| `release(int arg)` | 独占模式释放方法 | AQS实现 |
| `tryRelease(int arg)` | 真正释放锁 | 子类实现 |

#### 2.2.2 共享模式（Shared）

👉 用于 **允许多个线程同时获取的资源**（如 Semaphore、CountDownLatch）

| 方法 | 作用 | 实现方 |
|------|------|--------|
| `acquireShared(int arg)` | 共享模式入口 | AQS实现 |
| `tryAcquireShared(int arg)` | 共享资源获取逻辑 | 子类实现 |
| `releaseShared(int arg)` | 释放共享资源 | AQS实现 |
| `tryReleaseShared(int arg)` | 释放共享资源逻辑 | 子类实现 |

#### 2.2.3 队列管理（核心机制）

| 方法 | 作用 |
|------|------|
| `addWaiter(Node mode)` | 把当前线程封装成节点，加入队列 |
| `acquireQueued(Node node, int arg)` | 自旋尝试获取锁，如果失败则阻塞 |
| `unparkSuccessor(Node node)` | 唤醒队列中的下一个等待线程 |
| `hasQueuedPredecessors()` | 判断当前线程是否有前驱节点（公平锁依赖） |

### 2.3 核心调用链总结

**独占模式（ReentrantLock 为例）**：
```
lock() 
  -> sync.lock()
    -> acquire(1) 
      -> tryAcquire(1) 失败 → addWaiter() 入队 → acquireQueued() 阻塞
unlock()
  -> sync.release(1) 
    -> tryRelease(1) → unparkSuccessor() 唤醒队列下一个
```

**共享模式（Semaphore 为例）**：
```
acquire()
  -> acquireShared(1)
    -> tryAcquireShared(1) 失败 → addWaiter(SHARED) 入队 → doAcquireShared() 阻塞
release()
  -> releaseShared(1)
    -> tryReleaseShared(1) → doReleaseShared() 唤醒下一个
```

---

## 3. 加锁流程详解

### 3.1 完整加锁流程

#### 3.1.1 最外层入口：`lock()`

```java
@ReservedStackAccess
final void lock() {
    if (!initialTryLock())
        acquire(1);
}
```

**逻辑**：
- **先快速尝试** `initialTryLock()`（CAS 抢一下）
- 如果失败，走 **完整的 AQS 队列排队获取** `acquire(1)`

#### 3.1.2 快速尝试：`initialTryLock()`

```java
final boolean initialTryLock() {
    Thread current = Thread.currentThread();
    int c = getState(); // state 表示锁的占用次数

    if (c == 0) { // 没人占锁
        if (!hasQueuedThreads() && compareAndSetState(0, 1)) {
            setExclusiveOwnerThread(current);
            return true;
        }
    } else if (getExclusiveOwnerThread() == current) { // 重入
        if (++c < 0) throw new Error("Maximum lock count exceeded");
        setState(c);
        return true;
    }
    return false;
}
```

**逻辑分析**：
- `state == 0` → 锁空闲 → 如果队列没人等 → CAS 把 `state` 改成 1 → 抢到锁
- `state > 0 且 owner 是自己` → 支持重入（`state++`）
- 否则返回 `false` → 抢锁失败

⚡ 这个方法对应 **乐观快速路径**，大部分时候锁竞争不激烈，它就直接成功了

#### 3.1.3 慢路径：`acquire(int arg)`

```java
public final void acquire(int arg) {
    if (!tryAcquire(arg))
        acquire(null, arg, false, false, false, 0L);
}
```

**逻辑**：
- `tryAcquire(arg)`：再尝试一次获取锁
- 如果还失败 → 进入 `acquire(...)`，即 **入队、自旋、挂起**

#### 3.1.4 核心获取流程：`acquire(...)`

这是 AQS 最复杂的地方，核心循环逻辑：

```java
final int acquire(Node node, int arg, boolean shared,
                  boolean interruptible, boolean timed, long time) {
    Thread current = Thread.currentThread();
    byte spins = 0, postSpins = 0;
    boolean interrupted = false, first = false;
    Node pred = null;

    for (;;) {
        // Step1: 判断是否在队列首
        if (!first && (pred = (node == null) ? null : node.prev) != null &&
            !(first = (head == pred))) {
            if (pred.status < 0) {
                cleanQueue();           // predecessor cancelled
                continue;
            } else if (pred.prev == null) {
                Thread.onSpinWait();    // ensure serialization
                continue;
            }
        }
        
        // Step2: 如果在首（或者未入队），再尝试获取锁
        if (first || pred == null) {
            boolean acquired;
            try {
                if (shared)
                    acquired = (tryAcquireShared(arg) >= 0);
                else
                    acquired = tryAcquire(arg);
            } catch (Throwable ex) {
                cancelAcquire(node, interrupted, false);
                throw ex;
            }
            if (acquired) {
                if (first) {
                    node.prev = null;
                    head = node;
                    pred.next = null;
                    node.waiter = null;
                    if (shared)
                        signalNextIfShared(node);
                    if (interrupted)
                        current.interrupt();
                }
                return 1;
            }
        }
        
        // Step3: 获取不到 → 入队（enq）
        if (node == null) {
            if (shared)
                node = new SharedNode();
            else
                node = new ExclusiveNode();
        } else if (pred == null) {
            node.waiter = current;
            Node t = tail;
            node.setPrevRelaxed(t);
            if (t == null)
                tryInitializeHead();
            else if (!casTail(t, node))
                node.setPrevRelaxed(null);
            else
                t.next = node;
        }
        
        // Step4: 入队后，如果还是拿不到锁 → 设置等待状态 / park
        else if (first && spins != 0) {
            --spins;
            Thread.onSpinWait();
        } else if (node.status == 0) {
            node.status = WAITING;
        } else {
            long nanos;
            spins = postSpins = (byte)((postSpins << 1) | 1);
            if (!timed)
                LockSupport.park(this);
            else if ((nanos = time - System.nanoTime()) > 0L)
                LockSupport.parkNanos(this, nanos);
            else
                break;
            node.clearStatus();
            if ((interrupted |= Thread.interrupted()) && interruptible)
                break;
        }
    }
    return cancelAcquire(node, interrupted, interruptible);
}
```

### 3.2 加锁流程图

```
lock()
  └─> initialTryLock() → 成功 → 返回
                      → 失败 → acquire(1)
                                   ├─ tryAcquire(1) → 成功 → 返回
                                   └─ acquire(...) 循环
                                            ├─ 判断是否队首
                                            ├─ 在队首 → tryAcquire → 成功 → head 指向自己
                                            ├─ 不在队首 → 入队
                                            ├─ 入队后 → 设置 WAITING → park 阻塞
                                            └─ 被 unpark 唤醒 → 回到 tryAcquire
```

---

## 4. 解锁流程详解

### 4.1 完整解锁流程

#### 4.1.1 ReentrantLock.unlock()

```java
public void unlock() {
    sync.release(1);
}
```

调用的是 AQS 的 `release(1)`，参数 `1` 代表「释放一个资源（一次重入）」

#### 4.1.2 AQS.release(int arg)

```java
public final boolean release(int arg) {
    if (tryRelease(arg)) {
        Node h = head;
        if (h != null && h.status != 0)
            unparkSuccessor(h);  // 唤醒队列中的下一个等待者
        return true;
    }
    return false;
}
```

**逻辑**：
- **`tryRelease(arg)`**：真正释放锁（子类实现）
- 如果完全释放成功（state 归零） → 尝试唤醒队列里的下一个线程
- 返回 `true` 表示锁已经空闲

#### 4.1.3 tryRelease(arg) （ReentrantLock 的实现）

```java
protected final boolean tryRelease(int releases) {
    int c = getState() - releases;
    if (Thread.currentThread() != getExclusiveOwnerThread())
        throw new IllegalMonitorStateException();
    boolean free = false;
    if (c == 0) {   // state 归零，锁彻底释放
        free = true;
        setExclusiveOwnerThread(null);
    }
    setState(c);
    return free;
}
```

**逻辑分析**：
- `state - releases`：减少重入计数
- 如果 `state == 0`：
  - 锁完全释放
  - 清空持有线程记录（exclusiveOwnerThread = null）
  - 返回 `true`
- 否则只是部分释放（比如重入 3 次，释放一次 → state 从 3 变 2），返回 `false`

#### 4.1.4 唤醒后继线程：unparkSuccessor(Node h)

```java
private void unparkSuccessor(Node node) {
    int ws = node.status;
    if (ws < 0)
        compareAndSetWaitStatus(node, ws, 0);

    Node s = node.next;
    if (s == null || s.status > 0) {
        s = null;
        for (Node t = tail; t != null && t != node; t = t.prev) {
            if (t.status <= 0)
                s = t;
        }
    }
    if (s != null)
        LockSupport.unpark(s.thread);
}
```

**逻辑**：
- 先把 **head 节点的状态** 清零
- 找到第一个有效的后继节点（等待状态的节点）
- 调用 `LockSupport.unpark(s.thread)` 唤醒它

### 4.2 解锁流程图

```
unlock()
  → release(1)
       → tryRelease(1)
            state -= 1
            if state == 0:
               清空 owner
               return true
            else:
               return false
       → if true (锁彻底释放)
            unparkSuccessor(head)
                找到 head 的下一个等待线程
                LockSupport.unpark() 唤醒它
```

---

## 5. 公平锁vs非公平锁

### 5.1 对比总结

| 特性 | 非公平锁（NonfairSync） | 公平锁（FairSync） |
|------|------------------------|-------------------|
| **获取策略** | 插队机制，直接CAS抢锁 | 严格FIFO排队 |
| **性能** | 吞吐量高 | 吞吐量较低 |
| **公平性** | 可能导致饥饿 | 保证公平性 |
| **实现复杂度** | 简单 | 复杂 |
| **默认选择** | 是 | 否 |

### 5.2 核心差异代码

**非公平锁**：
```java
final void lock() {
    if (compareAndSetState(0, 1))   // 直接抢锁
        setExclusiveOwnerThread(Thread.currentThread());
    else
        acquire(1);
}
```

**公平锁**：
```java
final void lock() {
    acquire(1); // 直接交给AQS的公平获取逻辑
}

protected final boolean tryAcquire(int acquires) {
    // 关键：hasQueuedPredecessors() 检查是否有前驱
    if (!hasQueuedPredecessors() && compareAndSetState(0, acquires)) {
        setExclusiveOwnerThread(Thread.currentThread());
        return true;
    }
    return false;
}
```

### 5.3 选择建议

- **高并发场景**：选择非公平锁，性能更好
- **需要严格顺序**：选择公平锁，避免饥饿
- **一般情况**：默认非公平锁即可

---

## 6. 相关面试题

### 6.1 AQS核心原理

**Q: AQS的核心原理是什么？**

**A:** AQS（AbstractQueuedSynchronizer）是Java并发包中的核心同步器，其核心原理包括：

1. **状态管理**：通过volatile int state字段管理同步状态
2. **队列机制**：使用CLH队列（FIFO双向链表）管理等待线程
3. **模板方法模式**：提供acquire/release模板，子类实现tryAcquire/tryRelease
4. **独占/共享模式**：支持独占锁（如ReentrantLock）和共享锁（如Semaphore）

**核心思想**：通过CAS操作管理state状态，通过队列管理等待线程，实现高效的线程同步。

### 6.2 ReentrantLock实现原理

**Q: ReentrantLock是如何实现可重入的？**

**A:** ReentrantLock通过以下机制实现可重入：

1. **state计数**：每次获取锁时state+1，释放时state-1
2. **owner记录**：exclusiveOwnerThread记录持有锁的线程
3. **重入判断**：在tryAcquire中检查当前线程是否为owner
4. **计数管理**：重入时state递增，完全释放时state归零

```java
// 重入逻辑
if (current == getExclusiveOwnerThread()) {
    setState(c + acquires);  // state递增
    return true;
}
```

### 6.3 公平锁vs非公平锁

**Q: 公平锁和非公平锁的区别是什么？**

**A:** 主要区别如下：

1. **获取策略**：
   - 非公平锁：直接CAS抢锁，可能插队
   - 公平锁：检查队列，严格FIFO

2. **性能差异**：
   - 非公平锁：吞吐量高，减少线程切换
   - 公平锁：吞吐量低，保证公平性

3. **饥饿问题**：
   - 非公平锁：可能导致饥饿
   - 公平锁：避免饥饿

4. **实现复杂度**：
   - 非公平锁：实现简单
   - 公平锁：需要hasQueuedPredecessors()检查

### 6.4 AQS队列机制

**Q: AQS的CLH队列是如何工作的？**

**A:** CLH队列工作机制：

1. **节点结构**：每个等待线程封装为Node节点
2. **入队操作**：通过CAS操作将节点添加到队尾
3. **出队操作**：获取锁的线程成为新的head节点
4. **唤醒机制**：释放锁时唤醒下一个等待节点
5. **状态管理**：通过Node.status管理节点状态

**核心流程**：
```
线程获取锁失败 → 创建Node节点 → CAS入队 → park阻塞 → 被唤醒 → 重新尝试获取锁
```

### 6.5 锁的性能优化

**Q: AQS在性能方面做了哪些优化？**

**A:** 主要优化包括：

1. **快速路径**：initialTryLock()直接CAS，避免入队开销
2. **自旋等待**：在park前进行短暂自旋，减少上下文切换
3. **CAS操作**：使用CAS保证原子性，避免重量级锁
4. **队列优化**：CLH队列减少锁竞争，提高并发性能
5. **状态压缩**：将多个状态信息压缩到state字段中

### 6.6 死锁预防

**Q: 如何避免使用ReentrantLock时的死锁？**

**A:** 避免死锁的策略：

1. **固定顺序**：按固定顺序获取多个锁
2. **超时机制**：使用tryLock(timeout)避免无限等待
3. **锁的粒度**：尽量减小锁的粒度，减少持有时间
4. **避免嵌套**：避免在持有锁时获取其他锁
5. **使用工具**：使用ReentrantReadWriteLock等更细粒度的锁

### 6.7 源码设计模式

**Q: AQS使用了哪些设计模式？**

**A:** 主要使用了以下设计模式：

1. **模板方法模式**：acquire/release提供模板，tryAcquire/tryRelease由子类实现
2. **策略模式**：通过不同的Sync实现类提供不同的锁策略
3. **状态模式**：通过state字段管理不同的同步状态
4. **观察者模式**：通过队列管理等待线程，实现线程间的通知机制

### 6.8 实际应用场景

**Q: 在实际项目中，什么时候选择ReentrantLock而不是synchronized？**

**A:** 选择ReentrantLock的场景：

1. **需要公平性**：需要保证线程获取锁的顺序
2. **需要超时**：使用tryLock(timeout)避免无限等待
3. **需要中断**：使用lockInterruptibly()响应中断
4. **需要多个条件变量**：使用Condition实现复杂的等待/通知
5. **需要可重入**：同一个线程需要多次获取锁
6. **性能要求高**：在高并发场景下性能更好

---

## 总结

AQS作为Java并发包的核心，通过巧妙的设计实现了高效的线程同步机制：

1. **状态管理**：通过volatile state字段管理同步状态
2. **队列机制**：使用CLH队列管理等待线程
3. **模板方法**：提供统一的同步框架
4. **性能优化**：快速路径、自旋等待等优化策略

ReentrantLock作为AQS的典型应用，展示了如何基于AQS构建可重入的独占锁，通过公平锁和非公平锁的不同实现，满足了不同场景的需求。

掌握AQS的核心原理，不仅有助于理解Java并发包的设计思想，也为解决实际并发问题提供了重要的理论基础。



