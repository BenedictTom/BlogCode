---
title: 多线程_CompletableFuture
main_color: "#5393E3"
categories: 并发
tags:
  - 并发
  - 多线程
cover: https://free.picui.cn/free/2026/03/28/69c74dea76ddb.png
---

---

#### 一、引言
`CompletableFuture` 是 Java 8 引入的一个类，用于简化异步编程模型，提供了比传统的 `Future` 更强大的功能，如链式调用、组合多个异步任务的能力。


#### 二、Future 理论知识
- **定义与用途**：`Future` 是一个接口，代表异步计算的结果。可以通过它检查计算是否完成、等待其完成，并获取计算结果。
- **基本操作**：
  - `isDone()` 检查任务是否完成。
  - `get()` 获取计算结果（阻塞直到任务完成）。
  - `cancel(boolean mayInterruptIfRunning)` 尝试取消任务。



#### 三、Future实现类FutureTask
- **结构与功能**：`FutureTask` 实现了 `RunnableFuture` 接口，该接口扩展了 `Runnable` 和 `Future`。这使得它可以被线程执行并返回计算结果。
- **适用场景**：适用于那些希望在执行过程中获取中间状态或结果的任务。



#### 四、Future改进-CompletableFuture
- **引入背景**：传统 `Future` 缺乏对异步任务链式处理的支持，`CompletableFuture` 解决了这些问题。
- **主要特点**：
  - **链式调用**：通过 `.thenApply()`, `.thenAccept()` 等方法可以方便地进行后续处理。
  - **异常处理**：`.exceptionally(Function<Throwable, ? extends T> fn)` 提供了异常处理机制。
  - **组合任务**：`.thenCombine(CompletionStage<? extends U> other, BiFunction<? super T,? super U,? extends V> fn)` 可以用来合并两个独立的异步任务。



#### 五、案例讲解--电商比价
- **场景描述**：假设有一个电商平台，需要从多个供应商处获取商品价格并比较。
- **解决方案**：使用 `CompletableFuture.supplyAsync()` 来并发请求各供应商的价格，然后使用 `.thenCombine()` 或 `.thenCompose()` 来汇总这些信息。

```java
// 示例代码片段
List<Supplier<Double>> suppliers = Arrays.asList(supplierA, supplierB, supplierC);
List<CompletableFuture<Double>> futures = suppliers.stream()
        .map(supplier -> CompletableFuture.supplyAsync(() -> supplier.getPrice()))
        .collect(Collectors.toList());

CompletableFuture<Void> allOf = CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]));
allOf.thenRun(() -> {
    List<Double> prices = futures.stream().map(CompletableFuture::join).collect(Collectors.toList());
    // 进行价格比较逻辑
});
```


```java
/**
 * @author Guanghao Wei
 * @create 2023-04-10 12:53
 * 这里面需要注意一下Stream流方法的使用
 * 这种异步查询的方法大大节省了时间消耗，可以融入简历项目中，和面试官有所探讨
 */
public class CompletableFutureMallDemo {
    static List<NetMall> list = Arrays.asList(new NetMall("jd"), new NetMall("taobao"), new NetMall("dangdang"));

    /**
     * step by step
     * @param list
     * @param productName
     * @return
     */
    public static List<String> getPrice(List<NetMall> list, String productName) {
        //《Mysql》 in jd price is 88.05
        return list
                .stream()
                .map(netMall ->
                        String.format("《" + productName + "》" + "in %s price is %.2f",
                                netMall.getNetMallName(),
                                netMall.calcPrice(productName)))
                .collect(Collectors.toList());
    }

    /**
     * all in
     * 把list里面的内容映射给CompletableFuture()
     * @param list
     * @param productName
     * @return
     */
    public static List<String> getPriceByCompletableFuture(List<NetMall> list, String productName) {
        return list.stream().map(netMall ->
                        CompletableFuture.supplyAsync(() ->
                                String.format("《" + productName + "》" + "in %s price is %.2f",
                                        netMall.getNetMallName(),
                                        netMall.calcPrice(productName)))) //Stream<CompletableFuture<String>>
                .collect(Collectors.toList()) //List<CompletableFuture<String>>
                .stream()//Stream<String>
                .map(s -> s.join()).collect(Collectors.toList()); //List<String>
    }

    public static void main(String[] args) {
        /**
         * 采用step by setp方式查询
         * 《masql》in jd price is 110.11
         * 《masql》in taobao price is 109.32
         * 《masql》in dangdang price is 109.24
         * ------costTime: 3094 毫秒
         */
        long StartTime = System.currentTimeMillis();
        List<String> list1 = getPrice(list, "masql");
        for (String element : list1) {
            System.out.println(element);
        }
        long endTime = System.currentTimeMillis();
        System.out.println("------costTime: " + (endTime - StartTime) + " 毫秒");

        /**
         * 采用 all in三个异步线程方式查询
         * 《mysql》in jd price is 109.71
         * 《mysql》in taobao price is 110.69
         * 《mysql》in dangdang price is 109.28
         * ------costTime1009 毫秒
         */
        long StartTime2 = System.currentTimeMillis();
        List<String> list2 = getPriceByCompletableFuture(list, "mysql");
        for (String element : list2) {
            System.out.println(element);
        }
        long endTime2 = System.currentTimeMillis();
        System.out.println("------costTime" + (endTime2 - StartTime2) + " 毫秒");

    }
}

@AllArgsConstructor
@NoArgsConstructor
@Data
class NetMall {
    private String netMallName;

    public double calcPrice(String productName) {
        try {
            TimeUnit.SECONDS.sleep(1);
        } catch (InterruptedException e) {
            e.printStackTrace();
        }

        return ThreadLocalRandom.current().nextDouble() * 2 + productName.charAt(0);
    }
}

```


#### 六、CompletableFuture常用API
`CompletableFuture` 是 Java 8 引入的一个强大的异步编程工具类，它实现了 `Future` 接口，并提供了丰富的 API 来处理异步任务。以下是 `CompletableFuture` 的主要 API 列表，按照功能分类整理：

你说得对，`CompletableFuture` 还有一些其他的静态方法和实例方法。以下是更全面的 `CompletableFuture` API 列表，包括你提到的 `allOf` 和 `anyOf` 方法以及其他一些重要的方法：

| 功能类别                | 方法名                                                                                                  | 描述                                                                                                                                                     |
|-------------------------|-----------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| **创建 CompletableFuture** | `supplyAsync(Supplier<U> supplier)`                                                                     | 提交一个返回结果的任务到默认的线程池执行并返回一个 `CompletableFuture` 实例。                                                                         |
|                         | `runAsync(Runnable runnable)`                                                                             | 提交一个不返回结果的任务到默认的线程池执行并返回一个 `CompletableFuture` 实例。                                                                       |
|                         | `supplyAsync(Supplier<U> supplier, Executor executor)`                                                  | 提交一个返回结果的任务到指定的线程池执行并返回一个 `CompletableFuture` 实例。                                                                          |
|                         | `runAsync(Runnable runnable, Executor executor)`                                                        | 提交一个不返回结果的任务到指定的线程池执行并返回一个 `CompletableFuture` 实例。                                                                        |
| **组合 Future**         | `thenApply(Function<? super T,? extends U> fn)`                                                         | 将当前 `CompletableFuture` 结果转换成另一个值。                                                                                                        |
|                         | `thenAccept(Consumer<? super T> action)`                                                                | 对当前 `CompletableFuture` 的结果进行消费操作。                                                                                                          |
|                         | `thenRun(Runnable action)`                                                                              | 在当前 `CompletableFuture` 完成后执行一个 Runnable 操作。                                                                                            |
|                         | `thenCombine(CompletionStage<? extends U> other, BiFunction<? super T,? super U,? extends V> fn)`        | 组合两个 `CompletableFuture` 的结果并生成一个新的 `CompletableFuture`。                                                                               |
|                         | `thenCompose(Function<? super T, ? extends CompletionStage<U>> fn)`                                     | 使用当前 `CompletableFuture` 的结果作为下一个 `CompletableFuture` 的输入。                                                                             |
|                         | `applyToEither(CompletionStage<? extends T> other, Function<? super T, U> fn)`                          | 当任意一个 `CompletableFuture` 完成时应用提供的函数。                                                                                                |
|                         | `acceptEither(CompletionStage<? extends T> other, Consumer<? super T> action)`                          | 当任意一个 `CompletableFuture` 完成时执行提供的动作。                                                                                                |
|                         | `runAfterEither(CompletionStage<?> other, Runnable action)`                                               | 当任意一个 `CompletableFuture` 完成时执行提供的 Runnable 操作。                                                                                        |
|                         | `thenAcceptBoth(CompletionStage<? extends U> other, BiConsumer<? super T, ? super U> action)`             | 当两个 `CompletableFuture` 都完成后执行提供的动作。                                                                                                    |
|                         | `runAfterBoth(CompletionStage<?> other, Runnable action)`                                                 | 当两个 `CompletableFuture` 都完成后执行提供的 Runnable 操作。                                                                                          |
| **异常处理**            | `exceptionally(Function<Throwable, ? extends T> fn)`                                                    | 处理异常情况，当 `CompletableFuture` 出现异常时提供一个默认值。                                                                                    |
|                         | `handle(BiFunction<? super T, Throwable, ? extends U> fn)`                                              | 处理正常完成或异常情况，允许对结果或异常进行自定义处理。                                                                                             |
| **回调**                | `whenComplete(BiConsumer<? super T, ? super Throwable> action)`                                           | 注册一个动作，在 `CompletableFuture` 完成（无论是成功还是失败）后执行。                                                                              |
|                         | `whenCompleteAsync(BiConsumer<? super T, ? super Throwable> action)`                                      | 注册一个动作，在 `CompletableFuture` 完成（无论是成功还是失败）后异步执行。                                                                          |
| **阻塞获取结果**        | `get()`                                                                                                 | 阻塞等待 `CompletableFuture` 的结果。如果任务尚未完成，则会一直等待直到任务完成。                                                                      |
|                         | `get(long timeout, TimeUnit unit)`                                                                      | 阻塞等待 `CompletableFuture` 的结果，最多等待指定的时间。如果在指定时间内任务未完成，则抛出超时异常。                                                   |
|                         | `join()`                                                                                                | 类似于 get()，但是用于 `CompletableFuture` 自身的方法调用，不会抛出受检异常。                                                                         |
| **取消和状态检查**      | `cancel(boolean mayInterruptIfRunning)`                                                                   | 尝试取消正在进行中的 `CompletableFuture` 任务。                                                                                                        |
|                         | `isDone()`                                                                                              | 检查 `CompletableFuture` 是否已经完成，包括正常完成、异常完成或被取消的情况。                                                                        |
|                         | `isCancelled()`                                                                                           | 检查 `CompletableFuture` 是否已经被取消。                                                                                                                |
| **静态方法**            | `completedFuture(T value)`                                                                              | 返回一个已完成的 `CompletableFuture`，其结果为给定的值。                                                                                               |
|                         | `failedFuture(Throwable ex)`                                                                              | 返回一个已完成且带有异常的 `CompletableFuture`。                                                                                                       |
|                         | `anyOf(CompletableFuture<?>... futures)`                                                                  | 返回一个新的 `CompletableFuture`，它会在任意一个给定的 `CompletableFuture` 完成时完成，并持有第一个完成的结果。                                         |
|                         | `allOf(CompletableFuture<?>... futures)`                                                                  | 返回一个新的 `CompletableFuture`，它会在所有给定的 `CompletableFuture` 完成时完成。                                                                      |
| **延迟执行**            | `delayedExecutor(long delay, TimeUnit unit)`                                                              | 创建一个延迟执行器，可以在指定时间后执行任务。                                                                                                         |
|                         | `delayedExecutor(long delay, TimeUnit unit, ScheduledExecutorService scheduler)`                        | 使用指定的调度器创建一个延迟执行器，可以在指定时间后执行任务。                                                                                         |
| **异步回调**            | `thenApplyAsync(Function<? super T,? extends U> fn)`                                                    | 异步地将当前 `CompletableFuture` 结果转换成另一个值。                                                                                                |
|                         | `thenApplyAsync(Function<? super T,? extends U> fn, Executor executor)`                                   | 使用指定的执行器异步地将当前 `CompletableFuture` 结果转换成另一个值。                                                                                  |
|                         | `thenAcceptAsync(Consumer<? super T> action)`                                                           | 异步地对当前 `CompletableFuture` 的结果进行消费操作。                                                                                                  |
|                         | `thenAcceptAsync(Consumer<? super T> action, Executor executor)`                                          | 使用指定的执行器异步地对当前 `CompletableFuture` 的结果进行消费操作。                                                                                  |
|                         | `thenRunAsync(Runnable action)`                                                                           | 异步地在当前 `CompletableFuture` 完成后执行一个 Runnable 操作。                                                                                      |
|                         | `thenRunAsync(Runnable action, Executor executor)`                                                      | 使用指定的执行器异步地在当前 `CompletableFuture` 完成后执行一个 Runnable 操作。                                                                      |
|                         | `thenCombineAsync(CompletionStage<? extends U> other, BiFunction<? super T,? super U,? extends V> fn)`   | 异步地组合两个 `CompletableFuture` 的结果并生成一个新的 `CompletableFuture`。                                                                          |
|                         | `thenCombineAsync(CompletionStage<? extends U> other, BiFunction<? super T,? super U,? extends V> fn, Executor executor)` | 使用指定的执行器异步地组合两个 `CompletableFuture` 的结果并生成一个新的 `CompletableFuture`。                                                          |
|                         | `thenComposeAsync(Function<? super T, ? extends CompletionStage<U>> fn)`                                | 异步地使用当前 `CompletableFuture` 的结果作为下一个 `CompletableFuture` 的输入。                                                                       |
|                         | `thenComposeAsync(Function<? super T, ? extends CompletionStage<U>> fn, Executor executor)`               | 使用指定的执行器异步地使用当前 `CompletableFuture` 的结果作为下一个 `CompletableFuture` 的输入。                                                       |
|                         | `applyToEitherAsync(CompletionStage<? extends T> other, Function<? super T, U> fn)`                       | 异步地当任意一个 `CompletableFuture` 完成时应用提供的函数。                                                                                          |
|                         | `applyToEitherAsync(CompletionStage<? extends T> other, Function<? super T, U> fn, Executor executor)`    | 使用指定的执行器异步地当任意一个 `CompletableFuture` 完成时应用提供的函数。                                                                          |
|                         | `acceptEitherAsync(CompletionStage<? extends T> other, Consumer<? super T> action)`                       | 异步地当任意一个 `CompletableFuture` 完成时执行提供的动作。                                                                                            |
|                         | `acceptEitherAsync(CompletionStage<? extends T> other, Consumer<? super T> action, Executor executor)`    | 使用指定的执行器异步地当任意一个 `CompletableFuture` 完成时执行提供的动作。                                                                        |
|                         | `runAfterEitherAsync(CompletionStage<?> other, Runnable action)`                                          | 异步地当任意一个 `CompletableFuture` 完成时执行提供的 Runnable 操作。                                                                                |
|                         | `runAfterEitherAsync(CompletionStage<?> other, Runnable action, Executor executor)`                     | 使用指定的执行器异步地当任意一个 `CompletableFuture` 完成时执行提供的 Runnable 操作。                                                            |
|                         | `thenAcceptBothAsync(CompletionStage<? extends U> other, BiConsumer<? super T, ? super U> action)`        | 异步地当两个 `CompletableFuture` 都完成后执行提供的动作。                                                                                              |
|                         | `thenAcceptBothAsync(CompletionStage<? extends U> other, BiConsumer<? super T, ? super U> action, Executor executor)` | 使用指定的执行器异步地当两个 `CompletableFuture` 都完成后执行提供的动作。                                                                          |
|                         | `runAfterBothAsync(CompletionStage<?> other, Runnable action)`                                            | 异步地当两个 `CompletableFuture` 都完成后执行提供的 Runnable 操作。                                                                                    |
|                         | `runAfterBothAsync(CompletionStage<?> other, Runnable action, Executor executor)`                       | 使用指定的执行器异步地当两个 `CompletableFuture` 都完成后执行提供的 Runnable 操作。                                                                |
| **其他**                | `toCompletableFuture()`                                                                                 | 如果 `this` 是 `CompletableFuture` 的子类，则返回 `this`；否则返回一个新的 `CompletableFuture`，它的行为与 `this` 相同。                                |


#### 七、总结
`CompletableFuture` 提供了更灵活的异步编程方式，使得编写非阻塞、高效的应用程序变得更加简单。理解其核心概念和常用API是掌握现代Java并发编程的关键。

---


> **参考资料：**
> -  https://www.yuque.com/gongxi-wssld/csm31d/ip2ueru5itmgsgly


