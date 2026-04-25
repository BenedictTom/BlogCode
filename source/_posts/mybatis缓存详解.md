---
title: Mybatis缓存详解
main_color: "#1180c0ff"
categories: ORM
tags:
  - ORM
cover: https://free.picui.cn/free/2026/03/28/69c74e3ab3516.jpg
---



对的，你没记错，**MyBatis（包括 MyBatis-Plus）默认是开启一级缓存的**。  
 但是很多人会觉得“怎么每次都查数据库”，这是因为 **一级缓存有一些触发清空 / 失效的机制**，一不小心就用不上了。

我帮你梳理下：

------

## 🔹 1. 一级缓存的本质

- **一级缓存作用域：`SqlSession` 级别**
  - 在 **同一个 `SqlSession`** 中，相同的查询（SQL + 参数完全一致），第二次就不会再发 SQL，而是从缓存返回。
  - 但一旦 `SqlSession` 关闭（比如 Spring 管理事务时每次方法执行结束就关闭了），缓存也就没了。

👉 所以你在 Spring + MyBatis-Plus 里，**大部分情况下一个请求 = 一个 SqlSession**，请求结束缓存就失效。

------

## 🔹 2. 为什么你感觉没走缓存？

可能有以下几种情况：

### ✅ 情况一：不是同一个 `SqlSession`

- Spring 默认用 **事务范围** 管理 SqlSession。
- 如果你没显式开事务（`@Transactional`），那每次 Mapper 方法调用时，SqlSession 都会重新打开再关闭。
- 所以就算 SQL 一样，也不会命中缓存。

👉 **解决办法**：在 Service 方法上加上 `@Transactional`，确保多次查询在同一个 SqlSession 中。

------

### ✅ 情况二：执行了写操作

- 如果你在同一个 `SqlSession` 中执行了 **`insert/update/delete`**，MyBatis 会清空一级缓存，保证数据一致性。
- 所以写操作之后，再查就不会命中缓存。

------

### ✅ 情况三：查询参数或环境不一致

- 一级缓存的 Key = **SQL + 参数 + 环境**。
- 如果你查询的参数稍有不同（哪怕空格不一样），就算逻辑一样，也会被当成不同查询。

例如：

```java
userMapper.selectById(1);
userMapper.selectById(1L); // key 不一样，也可能不命中
```

------

### ✅ 情况四：Mapper 方法上用了 `@Options(flushCache=true)`

- 有些查询方法配置了 **每次都刷新缓存**，自然不会命中。

------

## 🔹 3. 验证缓存是否生效

举个简单例子：

```java
@Service
public class UserService {
    @Resource
    private UserMapper userMapper;

    @Transactional  // 保证同一个 SqlSession
    public void testCache() {
        System.out.println("第一次查询：");
        System.out.println(userMapper.selectById(1));

        System.out.println("第二次查询（应该走缓存，不发 SQL）：");
        System.out.println(userMapper.selectById(1));
    }
}
```

✅ 如果你加了 `@Transactional`，你会发现第二次不会发 SQL。
 如果不加事务，那每次调用 `selectById` 都会重新开 SqlSession，自然每次都打到数据库。

------

## 🔹 4. 二级缓存

- MP 默认 **关闭二级缓存**。
- 二级缓存是基于 Mapper namespace 的，需要在 `mapper.xml` 里加 `<cache/>` 才会启用。
- 并且要在全局配置里开启：`mybatis.configuration.cache-enabled=true`。

------

### ✅ 总结

1. **一级缓存默认开启**，但作用域是 **SqlSession**。
2. Spring 下，如果没开事务，每次调用都会新建 SqlSession，看起来就像没缓存。
3. 写操作、参数不同、flushCache 配置等都会导致缓存失效。

------





这个点非常关键 👍，我详细给你拆开解释一下：

------

## 🔹 Spring Boot + MyBatis-Plus 下的 SqlSession 生命周期

1. **MyBatis 原生**
   - MyBatis 的一级缓存作用域是 **SqlSession**。
   - 一个 SqlSession 就像一个数据库会话，它在**打开到关闭**之间，能记住查询结果。
2. **Spring 整合 MyBatis 之后**
   - Spring 不会让你自己去手动创建/关闭 SqlSession。
   - 它用 `SqlSessionTemplate` 来管理 SqlSession 的生命周期。
   - 默认策略是：
     - **有事务时**：整个事务范围内共用一个 SqlSession。
     - **没有事务时**：每次调用 Mapper 方法时，都会创建一个新的 SqlSession，执行完立刻关闭。

👉 这就是我说的「Spring 默认用事务范围管理 SqlSession」的意思。

------

## 🔹 举个例子

```java
@Service
public class UserService {
    @Resource
    private UserMapper userMapper;

    public void test() {
        // 第一次查询
        userMapper.selectById(1);
        // 第二次查询
        userMapper.selectById(1);
    }
}
```

- 如果 **没有加事务**：

  - 第一次 `selectById` 打开一个 SqlSession，用完关闭。
  - 第二次 `selectById` 又新建一个 SqlSession。
  - 一级缓存是 **SqlSession 级别的**，所以第二次查不到缓存，又去数据库。

- 如果 **加了 @Transactional**：

  ```java
  @Transactional
  public void test() {
      userMapper.selectById(1);
      userMapper.selectById(1);
  }
  ```

  - Spring 会在整个 `test()` 方法执行期间，用一个 SqlSession。
  - 第一次查询后结果会缓存到这个 SqlSession 里。
  - 第二次查询就能直接命中缓存，不会再打数据库。

------

## 🔹 那么，读操作要不要加事务？

- **是否加事务**，和“要不要缓存”是两回事。
- 一般我们加事务是为了 **保证数据一致性**，而不是为了缓存。
- 读操作如果是单次查询，通常没必要加事务。
- 但是如果你在一个方法里有多次查询，并且希望利用一级缓存避免重复 SQL，那么 **可以加上 `@Transactional(readOnly = true)`**。

例子：

```java
@Transactional(readOnly = true)
public void getUserTwice() {
    userMapper.selectById(1); // 第一次查
    userMapper.selectById(1); // 第二次走缓存
}
```

------

## 🔹 推荐实践

1. **业务逻辑方法**
   - 该加事务还是要加（尤其是写操作）。
   - 如果只是单条读操作，不需要为了缓存去加事务。
2. **性能优化场景**
   - 如果你在一个 Service 方法里会多次查询同一个数据，可以加上 `@Transactional(readOnly = true)`，利用一级缓存避免重复 SQL。
3. **更好的缓存方案**
   - 如果是频繁的读操作，依赖 MyBatis 一级缓存并不是最佳选择，因为它只在 SqlSession 有效期内。
   - 推荐结合 Redis / Caffeine 做真正的跨请求缓存。

------

✅ 总结一句：

- **Spring 管理下，没开事务 = 每次调用 Mapper 方法都会新建 SqlSession → 一级缓存失效。**
- **读操作可以加 `@Transactional(readOnly = true)` 来维持 SqlSession 生命周期，但通常更推荐用二级缓存或外部缓存。**

------





好问题 👌，你已经把「MyBatis 一级缓存」和「分布式缓存」的区别问出来了。为什么 MyBatis 没设计成多个请求之间也能命中缓存呢？我给你拆开讲：

------

## 🔹 1. MyBatis 一级缓存的定位

- **作用域**：`SqlSession` 级别
- **生命周期**：随 SqlSession 创建和关闭而存在
- **目的**：减少**同一个会话**中的重复 SQL 查询，提高一次业务方法里的性能。

👉 它本质上是一个 **“会话级别的查询缓存”**，而不是通用缓存。

------

## 🔹 2. 为什么不设计成跨请求共享缓存？

如果要做到「多个请求都能命中缓存」，那就是 **二级缓存** 或者 **外部缓存（Redis/Caffeine）」** 的功能了。
 MyBatis 没把一级缓存设计成这样，主要有几个原因：

### ✅ 2.1 一致性难保证

- 如果多个请求都命中缓存，必须有机制保证在执行 `update/insert/delete` 后，缓存里的数据被正确清理。
- 但 MyBatis 是一个 **ORM 框架**，它本身不知道数据是否被别的应用 / SQL 修改了。
- 这意味着缓存极容易 **脏读**。

### ✅ 2.2 性能与复杂度

- 要支持跨请求缓存，意味着要在全局范围维护一个缓存（内存/分布式），这会大大增加复杂度。
- MyBatis 的定位是轻量 ORM，不是分布式缓存框架。
- 如果在 MyBatis 内置这种全局缓存，反而可能拖慢查询（缓存一致性检查的代价 > 查询本身）。

### ✅ 2.3 分布式环境不适合

- 现代应用大多是分布式部署（多实例）。
- 如果 MyBatis 直接做成「所有请求共享缓存」，那在分布式情况下，多个节点之间还得搞同步，这就完全变成了 Redis 这种缓存中间件的活了。

------

## 🔹 3. MyBatis 的选择：一级缓存 + 二级缓存

MyBatis 的设计是分层的：

1. **一级缓存**（默认开启）
   - 作用域：SqlSession
   - 优点：简单，局部性能优化
   - 缺点：不能跨请求
2. **二级缓存**（可选，需要 `<cache/>` 开启）
   - 作用域：Mapper namespace
   - 多个 SqlSession 可以共享同一个 Mapper 的缓存
   - 但依旧只在单 JVM 内有效，分布式环境下意义不大
3. **更大范围的缓存 → 外部中间件**
   - 推荐用 Redis、Caffeine 这种专门的缓存框架，才能做到真正的跨请求、跨节点缓存

------

## 🔹 4. 举个类比

- **一级缓存** = 你自己手里的小笔记本，只在这次开会（一次 SqlSession）中好用，会后就丢掉。
- **二级缓存** = 公司会议室里的白板（某个 Mapper 的范围），大家在同一办公室能看到，但跨公司（分布式）就看不到了。
- **Redis 等外部缓存** = 专业的档案室，大家（多个请求、多台机器）都能查阅，并且有人专门负责更新。

------

## 🔹 5. 总结

MyBatis 没设计成「多个请求共享一级缓存」的原因是：

1. 容易产生数据不一致（脏数据问题）。
2. 超出了 ORM 框架的职责，会让 MyBatis 变得臃肿。
3. 分布式环境下更适合用 Redis/Caffeine 来做。

👉 因此 MyBatis 的缓存层次是：

- **一级缓存**：会话级别，保证事务内效率。
- **二级缓存**：Mapper 级别，可选，但仅 JVM 内有效。
- **真正跨请求/分布式缓存**：交给外部缓存中间件。

------





这个点很多人都会搞混 👌，我给你拆解一下 **MyBatis 的二级缓存**：

------

## 🔹 一级缓存 vs 二级缓存 回顾

- **一级缓存**：`SqlSession` 级别
  - 默认开启
  - 生命周期：随 SqlSession 存活
  - 用完 `SqlSession` 关闭就没了
  - 👉 所以通常只在「一次请求（事务）」内有效
- **二级缓存**：`Mapper namespace` 级别
  - **默认关闭**，需要在 `mapper.xml` 里 `<cache/>` 开启
  - 多个 SqlSession 共享同一个 Mapper 的缓存
  - 生命周期：整个应用运行期（除非手动清空、执行写操作、或 JVM 重启）
  - 👉 不是只限于一次请求，而是可以跨多个请求、多次 SqlSession

------

## 🔹 举个例子

### `UserMapper.xml`

```xml
<mapper namespace="com.example.mapper.UserMapper">
    <!-- 开启二级缓存 -->
    <cache/>

    <select id="selectById" resultType="com.example.entity.User">
        SELECT * FROM user WHERE id = #{id}
    </select>
</mapper>
```

### 使用场景

```java
// 第一次请求
userMapper.selectById(1);  // 发 SQL，结果写入二级缓存

// 第二次请求（不在同一个事务，不是同一个 SqlSession）
userMapper.selectById(1);  // 不发 SQL，直接从二级缓存拿结果
```

👉 只要是 **同一个 Mapper 的查询方法**，参数一致，就可以命中二级缓存。
 即便跨请求、跨事务，甚至不同的 SqlSession 也能共享。

------

## 🔹 二级缓存失效的情况

1. 执行了 **增删改操作**（`insert/update/delete`），会清空该 Mapper 下的二级缓存。
2. Mapper 配置了 `flushCache="true"`（默认 update/insert/delete 会刷新，select 默认 false）。
3. 手动清除缓存。

------

## 🔹 二级缓存的局限

1. **只在当前 JVM 内有效**
   - 如果是分布式部署（多台应用服务器），每个节点都有自己的二级缓存，数据不一致风险很大。
   - 所以生产环境通常不会直接用 MyBatis 自带的二级缓存，而是用 Redis 之类的外部缓存。
2. **基于 Mapper namespace 隔离**
   - 不同 Mapper 的缓存不会共享。
   - `UserMapper` 缓存的内容，`OrderMapper` 无法命中。

------

## ✅ 总结

- **一级缓存**：SqlSession 范围 → 一次请求/事务有效
- **二级缓存**：Mapper namespace 范围 → 可以跨请求、跨事务、跨 SqlSession，有效期是应用运行期间
- **限制**：二级缓存不适合分布式，跨节点时要用 Redis 等中间件

------



你抓得很准 👌，我们可以分两层来看：

------

## 🔹 1. 单 JVM / 单机场景

在这种情况下，**MyBatis 自带的二级缓存确实能保证一定程度的一致性**：

- MyBatis 在执行 `insert/update/delete` 的时候，会 **自动清空对应 Mapper namespace 的缓存**。
- 所以只要 **所有数据库操作都通过 MyBatis**，缓存和数据库的数据是一致的。

👉 换句话说：

- 如果你就是单机应用，所有 SQL 都是通过 MyBatis 发的，那二级缓存不会出大问题。
- 这时候二级缓存能提升性能（跨请求命中缓存）。

------

## 🔹 2. 脏读的根源

问题出在 **MyBatis 并不知道数据库还有别的写入来源**：

- 如果另一台程序、另一个服务，甚至 DBA 手工执行了 `update`，MyBatis 是察觉不到的。
- 这时缓存里还是旧值，查询就会命中缓存，导致**脏读**。

这就是我之前说的：**MyBatis 是 ORM，不是缓存框架**。它没有“数据库变更感知”能力。

------

## 🔹 3. 那么为什么单机下也不能完全掉以轻心？

即使单机单 JVM：

- 如果你绕过 MyBatis，比如直接用 `JdbcTemplate` 或者执行了原生 SQL，二级缓存依然不会被刷新。
- 如果同一个表被多个 Mapper 管理，不同 Mapper 的缓存 namespace 是隔离的，更新了 A 的缓存，B 还是旧的。

------

## 🔹 4. 对比一下三种缓存方案

| 缓存类型                   | 范围             | 一致性保证                                   | 适用场景                         |
| -------------------------- | ---------------- | -------------------------------------------- | -------------------------------- |
| 一级缓存                   | SqlSession       | 事务内一致                                   | 单次请求/事务，减少重复查询      |
| 二级缓存                   | Mapper namespace | MyBatis 写操作能清空缓存，但无法感知外部修改 | 单机应用，轻量级性能优化         |
| 外部缓存（Redis/Caffeine） | 全局 / 分布式    | 应用需要自己维护失效策略                     | 分布式环境，需要高并发高性能缓存 |

------

## ✅ 总结

- **单 JVM 单机**：MyBatis 二级缓存能保证一致性（前提：所有 SQL 都走 MyBatis）。
- **有外部写入 / 多服务 / 分布式**：二级缓存无法感知数据库变化，容易脏读。
- **生产环境最佳实践**：大多数团队会关闭 MyBatis 二级缓存，转而用 Redis/Caffeine 这种专业缓存。

------

要不要我帮你总结一份 👉「在 Spring Boot + MyBatis-Plus 项目中，何时适合用一级缓存 / 二级缓存 / Redis 缓存」的 **实战选型建议表**？



你说得没错，**一级缓存确实在很多 Spring Boot 场景下显得鸡肋**，因为每个请求通常就是一次 SqlSession，缓存很快就消失了。

但是一级缓存还是有它的**存在价值**，主要是在以下场景下有用：

------

## 🔹 1. **同一事务内，多次查询同一数据**

- **场景**：一个 Service 方法里需要对同一条记录多次查询。
- **示例**：

```java
@Transactional
public void updateUserName(Long id) {
    User user1 = userMapper.selectById(id); // 第一次查询
    User user2 = userMapper.selectById(id); // 第二次查询 -> 命中一级缓存
    user2.setName("Alice");
    userMapper.updateById(user2);
}
```

- **作用**：第二次查询不再打数据库，减少一次 SQL 调用。
- **适用业务**：同一事务内复杂业务逻辑，多次用到同一实体。

------

## 🔹 2. **延迟加载 / 关联对象查询**

- **场景**：存在对象关联（one-to-many / many-to-one），MyBatis 默认可以延迟加载。
- **示例**：

```java
Order order = orderMapper.selectById(1); 
User user = order.getUser(); // 延迟加载 User
User user2 = userMapper.selectById(1); // 一级缓存命中，不再查数据库
```

- **作用**：同一个 SqlSession 内，多次引用同一对象不会重复查询。

------

## 🔹 3. **批量操作前的重复读取**

- **场景**：Service 方法里循环处理列表数据，每次都要查询数据库进行判断。
- **示例**：

```java
@Transactional
public void processOrders(List<Long> orderIds) {
    for (Long id : orderIds) {
        Order order = orderMapper.selectById(id); // 同一次事务里可能重复查询
        // 处理逻辑
    }
}
```

- 一级缓存可以避免重复查询同一条记录，提高性能。

------

## 🔹 4. **测试 / 小型应用**

- 在一些小型项目、单事务的批处理场景，一级缓存几乎**开箱即用**，无需额外缓存配置，就能减少数据库压力。

------

## 🔹 5. ⚠️ 限制

- **只在同一个 SqlSession / 事务有效**
- **跨请求 / 跨事务无效**，所以在 Web 应用里很多单次查询确实“鸡肋”。
- **如果想跨请求缓存** → 需要二级缓存或 Redis/Caffeine。

------

### ✅ 总结

- 一级缓存适合**同一事务内、多次重复查询**的业务场景。
- 它的价值主要在**减少重复 SQL 查询**，尤其是**复杂事务逻辑或关联对象**的处理。
- 在普通 REST 请求场景下，一级缓存看起来鸡肋，但在**批量操作、事务内部重复访问**的情况下，还是有意义的。

