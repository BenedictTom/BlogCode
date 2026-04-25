---
title: Spring IOC
main_color: "rgb(11, 32, 228)"
categories: Spring
tags:
  - Spring
cover: https://free.picui.cn/free/2026/03/29/69c7fc2ba4ee6.png
---


## 为什么需要 IoC

IoC（控制反转）通过容器负责对象的创建、装配与生命周期管理，业务代码只声明依赖。这样可以降低耦合、提升可测试性与扩展性。

---

## BeanFactory深入理解

### 核心接口族
- **BeanFactory**: 最基础的获取 Bean 能力，按名/类型获取、是否存在、是否单例等。
- **HierarchicalBeanFactory**: 父子容器层级结构，支持向父容器委派查找。
- **ListableBeanFactory**: 可列举容器中的 Bean 名称、类型，框架常用。
- **AutowireCapableBeanFactory**: 程序化创建/装配/初始化 Bean 的能力，包含自动装配与生命周期回调。
- **ConfigurableBeanFactory**: 运行期可配置（作用域、后置处理器、属性编辑器等）。
- **ConfigurableListableBeanFactory**: 上述能力的合集，`DefaultListableBeanFactory` 的核心接口。

### 关键实现
- **DefaultListableBeanFactory**: 通用 BeanFactory 实现，维护 `BeanDefinition` 注册表与单例缓存。
- **ApplicationContext**: 在 `BeanFactory` 之上，增加国际化、资源加载、事件发布、环境信息等；常见实现如 `AnnotationConfigApplicationContext`、`ClassPathXmlApplicationContext`、`WebApplicationContext`。

### BeanDefinition（Bean 元数据）
- 元信息包含：`beanClass`、`scope`（singleton/prototype/...）、`lazyInit`、`primary`、`dependsOn`、`autowireMode`、`initMethodName`、`destroyMethodName`、`propertyValues`、`constructorArgumentValues`、`qualifiers` 等。
- 注册来源：注解扫描（`@Component`、`@Bean`）、XML、编程式注册（`BeanDefinitionRegistry`）。

### FactoryBean 与获取语义
- **FactoryBean<T>**: 自定义工厂。容器中 `name` 默认代表 `getObject()` 产物，`&name` 才是工厂本身。

### Aware 接口与环境获取
- 常见：`BeanNameAware`、`BeanFactoryAware`、`ApplicationContextAware`、`EnvironmentAware`、`ResourceLoaderAware` 等，用于注入容器资源。

### 生命周期扩展点（按时序）
- 定义阶段：`BeanDefinitionRegistryPostProcessor` → 可动态注册/修改 `BeanDefinition`。
- 工厂级：`BeanFactoryPostProcessor`（如 `PropertySourcesPlaceholderConfigurer` 解析 `${...}`）。
- 实例化前：`InstantiationAwareBeanPostProcessor#postProcessBeforeInstantiation`（可返回代理，跳过后续创建）。
- 实例化与填充：`SmartInstantiationAwareBeanPostProcessor`、`InstantiationAwareBeanPostProcessor#postProcessProperties`（如 `AutowiredAnnotationBeanPostProcessor` 完成依赖注入）。
- 初始化前/后：`BeanPostProcessor#postProcessBeforeInitialization/AfterInitialization`（如 AOP 代理创建器）。
- 销毁阶段：`DestructionAwareBeanPostProcessor`。
- 元数据合并：`MergedBeanDefinitionPostProcessor`（如配置类增强）。

### 单例池与三级缓存（循环依赖）
- `singletonObjects`：完全初始化好的单例。
- `earlySingletonObjects`：提前暴露的早期单例（已实例化未初始化）。
- `singletonFactories`：`ObjectFactory`，用于创建早期引用（常用于 AOP 代理提前暴露）。
- 解决条件：仅支持单例、基于 setter/字段注入；构造器循环依赖默认不可解。引入代理时通过 `ObjectFactory` 暴露代理或早期引用。

---

## bean 容器的启动流程（高层概览）

以 `ApplicationContext#refresh()` 为主线，典型步骤：
1) 读取配置并注册 `BeanDefinition`（扫描/解析）
2) `prepareRefresh()`：初始化环境、占位符、事件基础设施
3) `obtainFreshBeanFactory()`：创建/刷新 `BeanFactory`，载入 `BeanDefinition`
4) `prepareBeanFactory()`：设置类加载器、表达式解析器、忽略/可解析依赖等
5) `postProcessBeanFactory()`：子类扩展（如 `AbstractApplicationContext` 的钩子）
6) 调用 `BeanFactoryPostProcessor` / `BeanDefinitionRegistryPostProcessor`
7) 注册 `BeanPostProcessor`
8) 本地化消息源、事件多播器初始化
9) `onRefresh()`：子类特殊 Bean 初始化（如 Web 相关组件）
10) 注册监听器
11) `finishBeanFactoryInitialization()`：实例化非懒加载单例（含依赖注入、AOP 代理）
12) `finishRefresh()`：发布 `ContextRefreshedEvent`，就绪

---

## bean 的实例化阶段（createBean 生命周期）

整体流程：
1) `resolveBeforeInstantiation`：若有 `InstantiationAwareBeanPostProcessor` 返回代理，则短路
2) `createBeanInstance`：选择构造器并实例化（反射或 CGLIB 用于方法注入）
3) `populateBean`：属性填充，处理 `@Autowired` / `@Value` / `@Resource`
4) `initializeBean`：
   - 调用 Aware 接口
   - `BeanPostProcessor#postProcessBeforeInitialization`
   - `@PostConstruct` → `InitializingBean#afterPropertiesSet` → 自定义 `init-method`
   - `BeanPostProcessor#postProcessAfterInitialization`（AOP 代理创建常在此）
5) 注册销毁回调（若单例且定义了销毁逻辑）

构造器选择规则：
- `@Autowired` 标注构造器优先；无注解时根据参数可解析度与 `@Primary`/`@Qualifier` 选择。

依赖注入顺序与来源：
- 构造器参数 → 字段/Setter 注入；来源包括容器 Bean、`Environment`、`PropertySources`、`Value` 表达式等。

AOP 代理时机：
- 典型通过 `AbstractAutoProxyCreator` 在 `postProcessBeforeInstantiation` 或 `postProcessAfterInitialization` 创建代理。

循环依赖可解/不可解：
- 可解：单例 + Setter/字段注入（通过三级缓存提前暴露）。
- 不可解：prototype、构造器循环依赖、某些需要最终代理对象才能注入的场景（需重构或引入 `@Lazy`）。

---

## refresh() 方法关键步骤详解（精简）

- `prepareRefresh()`：校验必要属性、初始化占位符、早期事件集合
- `obtainFreshBeanFactory()`：刷新/创建 `DefaultListableBeanFactory` 并载入 `BeanDefinition`
- `prepareBeanFactory(beanFactory)`：设置 `ClassLoader`、`SpEL` 解析器、`Environment`，注册可解析依赖（`BeanFactory`、`ResourceLoader` 等）
- `postProcessBeanFactory(beanFactory)`：子类自定义扩展点
- `invokeBeanFactoryPostProcessors(beanFactory)`：先 `BeanDefinitionRegistryPostProcessor`，再 `BeanFactoryPostProcessor`
- `registerBeanPostProcessors(beanFactory)`：排序并注册所有 `BeanPostProcessor`
- `initMessageSource()`、`initApplicationEventMulticaster()`：国际化与事件
- `onRefresh()`：模板方法，子上下文实现（如 Web 容器）
- `registerListeners()`：注册 `ApplicationListener`
- `finishBeanFactoryInitialization(beanFactory)`：转换服务、非懒加载单例创建
- `finishRefresh()`：发布刷新完成事件，清理资源

---

## 代码示例

### 基础配置与 Bean 定义
```java
@Configuration
public class AppConfig {
    @Bean
    public UserService userService(OrderService orderService) {
        return new UserService(orderService);
    }

    @Bean
    public OrderService orderService() {
        return new OrderService();
    }
}
```

### BeanPostProcessor 简化示例
```java
public class LogInitBeanPostProcessor implements BeanPostProcessor {
    @Override
    public Object postProcessBeforeInitialization(Object bean, String beanName) {
        if (bean instanceof InitializingBean) {
            System.out.println("Before init: " + beanName);
        }
        return bean;
    }

    @Override
    public Object postProcessAfterInitialization(Object bean, String beanName) {
        return bean;
    }
}
```

### FactoryBean 示例
```java
public class ClientFactoryBean implements FactoryBean<Client> {
    @Override
    public Client getObject() {
        return new Client("prod-endpoint");
    }

    @Override
    public Class<?> getObjectType() {
        return Client.class;
    }
}
// 获取产品：context.getBean("clientFactoryBean")
// 获取工厂：context.getBean("&clientFactoryBean")
```

### 循环依赖（可解的 Setter 注入）
```java
@Component
class A {
    @Autowired
    private B b;
}

@Component
class B {
    @Autowired
    private A a;
}
// 单例 + 字段/Setter 注入：Spring 通过三级缓存可解。
```

---

## 常见问题与最佳实践
- **prototype 循环依赖**：不支持，需重构或引入 Provider（如 `ObjectFactory<T>`、`Provider<T>`）。
- **构造器循环依赖**：默认不可解；可通过拆分构造器依赖或引入 `@Lazy`/Setter。
- **`@Configuration` 与 `proxyBeanMethods`**：`true` 保证 `@Bean` 方法被代理（单例/依赖一致性），`false` 提升性能但需确保幂等。
- **优先级与排序**：`PriorityOrdered` > `Ordered` > 默认；涉及后置处理器与监听器注册顺序。
- **关闭容器**：确保销毁回调执行（`DisposableBean`、`@PreDestroy`、`destroy-method`）。

---

## 参考阅读（类名/方法名）
- `DefaultListableBeanFactory`、`AbstractAutowireCapableBeanFactory#createBean`
- `AbstractApplicationContext#refresh`
- `AutowiredAnnotationBeanPostProcessor`
- `AbstractAutoProxyCreator`



好的，我们来深入、系统地探讨 Spring 框架中 **Bean 的生命周期**。理解 Bean 的生命周期对于掌握 Spring 容器的工作原理、进行调试、实现自定义逻辑（如 AOP、资源管理）至关重要。

Bean 的生命周期指的是一个 Bean 从被 Spring 容器创建、初始化、使用，到最终被销毁的完整过程。这个过程由 Spring 容器（`BeanFactory` 或 `ApplicationContext`）精确地控制和管理。

---

### Bean 生命周期的核心阶段

一个典型的单例（Singleton）Bean 的生命周期可以分为以下几个关键阶段：

1.  **实例化 (Instantiation)**
    *   **描述**：Spring 容器根据 `BeanDefinition`（包含 Bean 的类名、作用域、构造函数参数等元数据）的信息，使用反射（或 CGLIB）创建 Bean 类的实例。
    *   **关键点**：此时 Bean 对象已经存在，但其属性尚未被赋值，依赖也未注入。这相当于 `new YourBean()` 这一步。

2.  **属性赋值 (Populate Properties / Dependency Injection)**
    *   **描述**：Spring 容器根据 `BeanDefinition` 中定义的属性和依赖关系，将值注入到刚刚创建的 Bean 实例中。
    *   **方式**：
        *   **基于 Setter 方法注入** (setter injection)
        *   **基于构造函数注入** (constructor injection)
        *   **基于字段注入** (field injection, 通常通过 `@Autowired` 等注解)
    *   **关键点**：在这个阶段，Bean 所依赖的其他 Bean（如果尚未创建，会递归执行其生命周期）会被解析并注入进来。

3.  **Aware 接口回调 (Aware Interfaces Callbacks)**
    *   **描述**：如果 Bean 实现了特定的 `Aware` 接口，Spring 容器会将相应的资源或信息注入给该 Bean。
    *   **常见 Aware 接口**：
        *   `BeanNameAware`：注入 Bean 在容器中的 ID/名称。`setBeanName(String name)`
        *   `BeanFactoryAware`：注入创建该 Bean 的 `BeanFactory` 实例。`setBeanFactory(BeanFactory beanFactory)`
        *   `ApplicationContextAware`：注入创建该 Bean 的 `ApplicationContext` 实例。`setApplicationContext(ApplicationContext applicationContext)`
        *   `EnvironmentAware`：注入 `Environment` 对象。
        *   `ResourceLoaderAware`：注入 `ResourceLoader` 对象。
        *   `MessageSourceAware`：注入 `MessageSource` 对象。
        *   `ApplicationEventPublisherAware`：注入 `ApplicationEventPublisher` 对象。
    *   **关键点**：这些回调允许 Bean 主动获取 Spring 容器的基础设施，实现更复杂的逻辑，但通常建议优先使用依赖注入而不是 Aware 接口，以保持解耦。

4.  **BeanPostProcessor 前置处理 (BeanPostProcessor - postProcessBeforeInitialization)**
    *   **描述**：如果容器中注册了 `BeanPostProcessor` 实例，它们的 `postProcessBeforeInitialization` 方法会被调用。
    *   **时机**：在 **任何初始化回调方法（如 `InitializingBean` 的 `afterPropertiesSet` 或自定义 `init-method`）之前**。
    *   **功能**：可以对 Bean 实例进行修改或包装（例如，创建代理对象，这是 Spring AOP 的核心实现机制之一）。
    *   **方法签名**：`Object postProcessBeforeInitialization(Object bean, String beanName)`

5.  **初始化 (Initialization)**
    *   **描述**：这是 Bean 变得“可用”前的最后准备阶段。
    *   **执行顺序**：
        1.  **`@PostConstruct` 注解的方法**：如果 Bean 中有方法标注了 `@PostConstruct`，该方法会被调用。这是 JSR-250 规范定义的。
        2.  **`InitializingBean` 接口的 `afterPropertiesSet()` 方法**：如果 Bean 实现了 `InitializingBean` 接口，则调用其 `afterPropertiesSet()` 方法。
        3.  **自定义 `init-method`**：如果在配置（XML 或 `@Bean(initMethod = "...")`）中指定了 `init-method`，则调用该方法。
    *   **关键点**：这个阶段通常用于执行一些需要在所有依赖都注入完成后才能进行的初始化操作，比如打开数据库连接、加载缓存等。

6.  **BeanPostProcessor 后置处理 (BeanPostProcessor - postProcessAfterInitialization)**
    *   **描述**：如果容器中注册了 `BeanPostProcessor` 实例，它们的 `postProcessAfterInitialization` 方法会被调用。
    *   **时机**：在 **所有初始化回调方法（`@PostConstruct`, `afterPropertiesSet`, `init-method`）之后**。
    *   **功能**：同样可以对 Bean 实例进行修改或包装。Spring AOP 的代理对象通常在这里生成。
    *   **方法签名**：`Object postProcessAfterInitialization(Object bean, String beanName)`
    *   **重要性**：`BeanPostProcessor` 的这两个方法是 Spring 框架实现 AOP、事务管理等高级功能的核心扩展点。

7.  **Bean 就绪 (Bean Ready for Use)**
    *   **描述**：经过以上所有步骤，Bean 已经完全初始化，所有依赖都已注入，初始化逻辑也已执行完毕。此时，该 Bean 实例可以被应用程序安全地使用了。

8.  **销毁 (Destruction)**
    *   **描述**：当 Spring 容器关闭时（例如，调用 `ConfigurableApplicationContext.close()`），容器会负责销毁单例 Bean 以释放资源。
    *   **执行顺序**：
        1.  **`@PreDestroy` 注解的方法**：如果 Bean 中有方法标注了 `@PreDestroy`，该方法会被调用。这是 JSR-250 规范定义的。
        2.  **`DisposableBean` 接口的 `destroy()` 方法**：如果 Bean 实现了 `DisposableBean` 接口，则调用其 `destroy()` 方法。
        3.  **自定义 `destroy-method`**：如果在配置（XML 或 `@Bean(destroyMethod = "...")`）中指定了 `destroy-method`，则调用该方法。
    *   **关键点**：这个阶段通常用于执行资源清理工作，比如关闭文件句柄、数据库连接、网络连接等。
    *   **注意**：**原型（Prototype）作用域的 Bean 不会由容器管理其销毁**。一旦创建并返回给客户端，容器就不再跟踪它，其销毁由客户端代码负责。

---

### 作用域（Scope）对生命周期的影响

*   **Singleton (单例)**：
    *   默认作用域。
    *   容器中只有一个共享的实例。
    *   生命周期由容器完整管理：**创建一次，销毁一次**（在容器关闭时）。
    *   上述所有阶段都会完整执行。

*   **Prototype (原型)**：
    *   每次请求（调用 `getBean()`）都会创建一个新的实例。
    *   **容器只负责实例化、属性赋值、Aware 回调、BeanPostProcessor 处理和初始化**。
    *   **容器不管理其销毁**。`@PreDestroy`、`DisposableBean.destroy()`、`destroy-method` **不会被调用**。资源清理必须由使用该 Bean 的代码负责。
    *   生命周期：**每次 `getBean()` 都会完整执行从实例化到初始化的流程**。

*   **Request / Session / Application (Web 作用域)**：
    *   在 Web 应用中使用。
    *   `Request`：每个 HTTP 请求创建一个新实例，请求结束时销毁。
    *   `Session`：每个 HTTP Session 创建一个实例，Session 失效时销毁。
    *   `Application`：每个 `ServletContext` 生命周期内创建一个实例，`ServletContext` 销毁时销毁。
    *   容器会管理其完整生命周期（包括销毁）。

---

### 生命周期流程图（简化版）

```
[Bean Definition]
       |
       v
[实例化 (new Instance)]
       |
       v
[属性赋值 (DI: Setters/Constructors)]
       |
       v
[Aware 接口回调 (e.g., BeanNameAware, BeanFactoryAware)]
       |
       v
[BeanPostProcessor.postProcessBeforeInitialization]
       |
       v
[初始化 (Initialization)]
       |--> @PostConstruct
       |--> InitializingBean.afterPropertiesSet()
       |--> init-method
       |
       v
[BeanPostProcessor.postProcessAfterInitialization]
       |
       v
===================> Bean Ready for Use <===================
       |
       | (Container Shutdown for Singleton/Scoped Beans)
       v
[销毁 (Destruction)]
       |--> @PreDestroy
       |--> DisposableBean.destroy()
       |--> destroy-method
       |
       v
[Bean Destroyed]
```

---

### 总结与最佳实践

1.  **理解顺序**：牢记生命周期各阶段的执行顺序，特别是 `BeanPostProcessor` 与 `InitializingBean`/`init-method` 的前后关系。
2.  **优先使用注解**：推荐使用 `@PostConstruct` 和 `@PreDestroy` 进行初始化和销毁，而不是实现 `InitializingBean` 和 `DisposableBean`，以减少对 Spring API 的直接依赖，提高代码的可移植性。
3.  **合理使用 Aware 接口**：除非必要，尽量避免使用 Aware 接口，优先通过依赖注入获取所需资源。
4.  **`BeanPostProcessor` 是关键扩展点**：它是 Spring 实现 AOP、事务、缓存等非功能性需求的核心机制。
5.  **注意作用域**：明确 Bean 的作用域，特别是 Prototype Bean 的销毁需要自行管理。
6.  **资源清理**：务必在销毁阶段（`@PreDestroy` 等）释放占用的资源（文件、连接等），防止内存泄漏。


这是一个非常好的问题！将 Spring Bean 默认设计为**单例（Singleton）**，是 Spring 框架设计中的一个核心决策，背后有着深刻的理由和权衡。这并非随意为之，而是基于性能、资源管理、设计模式以及典型应用场景的综合考量。

下面我们来深入探讨 **“为什么要将 Spring Bean 默认设计为单例？”**

---

### 1. **性能（Performance）**

这是最直接、最重要的原因。

*   **减少对象创建开销**：创建对象（实例化）是一个相对昂贵的操作，尤其是当类的构造函数复杂、依赖众多或涉及反射时。如果每次获取 Bean 都创建一个新实例（即原型模式），会带来巨大的性能损耗。
*   **减少垃圾回收（GC）压力**：频繁创建和丢弃对象会增加 JVM 堆内存的压力，导致更频繁的垃圾回收（GC），进而影响应用的整体性能和响应时间。
*   **单例的优势**：单例模式确保一个类只有一个实例，并提供一个全局访问点。Spring 容器在启动时创建一次该 Bean，之后所有请求都返回同一个实例，**避免了重复创建的开销**，极大地提升了性能。

### 2. **资源效率（Resource Efficiency）**

*   **共享昂贵资源**：很多 Bean 本身代表的是**无状态的服务**或**共享资源**。例如：
    *   **Service 层对象**：处理业务逻辑，通常不包含用户特定的状态。
    *   **DAO/Repository 对象**：用于数据库访问，其内部可能持有连接池（如 `DataSource`），连接池本身就是共享资源。
    *   **工具类**：如日期格式化工具、加密解密工具等。
*   **避免资源浪费**：如果这些无状态的服务被设计为原型，每次调用都创建一个新实例，虽然每个实例本身不占用太多状态，但成千上万的实例会浪费内存和 CPU。单例模式让它们可以被高效地共享。

### 3. **符合典型应用场景（Typical Use Cases）**

在绝大多数企业级应用中：

*   **Controller, Service, Repository** 这些核心组件都是**无状态**的。它们的行为是固定的（如“计算订单总价”、“保存用户信息”），不依赖于某个特定用户的会话数据（会话数据通常放在 `HttpSession` 或方法参数中）。
*   **配置对象**：如数据源（`DataSource`）、事务管理器（`PlatformTransactionManager`）、消息队列连接工厂等，天然就是全局唯一的共享资源。
*   **工具和辅助类**：日志、缓存管理、邮件发送等服务，通常也是无状态的。

对于这些**无状态**的组件，单例模式是**最自然、最高效**的选择。Spring 默认单例的设计完美契合了这种主流场景。

### 4. **简化依赖管理（Simplified Dependency Management）**

*   **依赖图更清晰**：当大部分 Bean 都是单例时，整个应用的依赖关系图（Dependency Graph）在容器启动时就基本确定了。Spring 可以在启动时解析并建立好所有依赖关系。
*   **循环依赖处理**：虽然循环依赖是设计上的坏味道，但 Spring 通过三级缓存等机制对单例 Bean 的循环依赖提供了有限的支持（主要是针对 setter 注入）。如果都是原型 Bean，处理循环依赖会变得极其复杂甚至不可能。

### 5. **与设计模式的契合**

*   **工厂模式 + 单例模式**：Spring 本质上是一个高级的工厂（`BeanFactory`），它管理对象的创建。对于需要全局唯一实例的对象，工厂返回单例是自然而然的。
*   **享元模式（Flyweight）**：单例可以看作是享元模式的一种特例（共享一个实例）。对于大量重复使用的无状态对象，享元模式能极大节省内存。

---

### 6. **“无状态”是关键前提**

**核心思想**：单例模式之所以安全且高效，是因为 **Spring 管理的大多数 Bean 是无状态的（Stateless）**。

*   **无状态 Bean**：其行为不依赖于任何实例变量（成员变量）中存储的特定数据。它的方法执行只依赖于传入的参数。这样的 Bean 可以被多个线程安全地共享。
    ```java
    @Service
    public class OrderService {
        // 无状态：方法行为只依赖参数，不依赖实例变量
        public BigDecimal calculateTotal(Order order) {
            return order.getItems().stream()
                       .map(Item::getPrice)
                       .reduce(BigDecimal.ZERO, BigDecimal::add);
        }
    }
    ```
*   **有状态 Bean**：如果一个 Bean 的实例变量存储了特定用户或会话的数据，那么它就是有状态的。**有状态的 Bean 绝不能使用单例！**
    *   **解决方案**：对于有状态的场景（如 Web 应用中的用户会话数据），应该使用 `@Scope("session")` 或 `@Scope("request")` 等 Web 作用域，或者将状态数据存储在 `HttpSession` 中，而服务层 Bean 保持无状态和单例。

---

### 7. **灵活性：默认单例，但可选其他作用域**

Spring 的设计非常灵活：

*   **默认是单例**：满足 90%+ 的场景，保证了默认配置下的高性能。
*   **提供其他作用域**：当确实需要时，可以轻松地将 Bean 配置为其他作用域：
    *   `@Scope("prototype")`：每次请求都创建新实例。
    *   `@Scope("request")`：每个 HTTP 请求一个实例。
    *   `@Scope("session")`：每个 HTTP Session 一个实例。
    *   `@Scope("application")`：每个 `ServletContext` 一个实例。

```java
@Component
@Scope("prototype") // 明确指定为原型
public class UserSessionData {
    private String username;
    // ... getter/setter
}
```

---

### 总结

Spring 将 Bean 默认设计为单例，是一个**深思熟虑的、以性能和效率为导向的、符合主流应用场景的优秀设计决策**。其核心原因在于：

1.  **性能卓越**：避免重复创建对象，减少 GC 压力。
2.  **资源高效**：共享无状态的服务和昂贵的资源。
3.  **场景契合**：绝大多数业务组件（Service, DAO, Controller）本质上是无状态的，适合共享。
4.  **管理简化**：依赖关系清晰，启动时可预构建。

**关键前提**：这个设计依赖于一个重要的约定——**开发者应确保被管理为单例的 Bean 是无状态的**。Spring 通过提供 `prototype`、`request`、`session` 等作用域，为有状态的场景提供了完美的解决方案，从而在**性能**和**灵活性**之间取得了极佳的平衡。

简而言之：**“因为大多数东西可以且应该被共享，所以默认共享（单例）；如果不能共享，你可以明确告诉容器（使用其他作用域）。”** 这就是 Spring 单例设计的精髓。