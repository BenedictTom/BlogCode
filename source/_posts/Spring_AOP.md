---
title: Spring AOP
main_color: "rgb(11, 32, 228)"
categories: Spring
tags:
  - Spring
cover: https://free.picui.cn/free/2026/03/28/69c74d6ce005d.jpeg
---


### 什么是 AOP（面向切面编程）

- **核心目的**: 将横切关注点（日志、鉴权、事务、监控、限流、审计等）从业务代码中解耦，集中在切面里统一管理。
- **关键术语**:
  - **JoinPoint**: 连接点，程序执行的某个点（方法调用、异常抛出等）。
  - **Pointcut**: 切点，匹配一组 JoinPoint 的表达式（如某包下所有方法）。
  - **Advice**: 通知，切入的动作（Before/Around/After...）。
  - **Aspect**: 切面，Pointcut + Advice 的集合。
  - **Weaving**: 织入，将切面应用到目标对象生成代理。
  - **Proxy**: 代理对象。Spring AOP 通过代理实现（JDK/CGLIB）。

### Spring AOP 与 AspectJ

- **Spring AOP**: 运行时代理（JDK 动态代理或 CGLIB）。覆盖方法级别切面，常用于业务应用。
- **AspectJ**: 编译时/加载时织入，功能更强，语法更丰富。Spring 也支持 AspectJ 注解风格，但仍由 Spring AOP 运行时代理执行。

提示：默认 `@EnableAspectJAutoProxy` 已由 Spring Boot 自动配置；在非 Boot 项目可手动开启。

```java
// 非 Spring Boot 项目可显式开启
@Configuration
@EnableAspectJAutoProxy(exposeProxy = true) // 需要自调用走代理时可开启 exposeProxy
public class AopConfig {}
```

### 快速上手：从简单到复杂

#### 1. 最简单：方法入参/返回日志

```java
@Aspect
@Component
public class LoggingAspect {

  // 切点：匹配 service 包及子包下的所有 public 方法
  @Pointcut("execution(public * com.example.service..*(..))")
  public void serviceMethods() {}

  @Before("serviceMethods()")
  public void beforeInvoke(JoinPoint joinPoint) {
    String method = joinPoint.getSignature().toShortString();
    Object[] args = joinPoint.getArgs();
    System.out.println("[AOP] Before: " + method + ", args=" + Arrays.toString(args));
  }

  @AfterReturning(pointcut = "serviceMethods()", returning = "result")
  public void afterReturn(JoinPoint joinPoint, Object result) {
    String method = joinPoint.getSignature().toShortString();
    System.out.println("[AOP] Return: " + method + ", result=" + result);
  }

  @AfterThrowing(pointcut = "serviceMethods()", throwing = "ex")
  public void afterThrow(JoinPoint joinPoint, Throwable ex) {
    String method = joinPoint.getSignature().toShortString();
    System.err.println("[AOP] Throw: " + method + ", ex=" + ex.getMessage());
  }
}
```

要点：
- `@Before` 不可改变返回值；`@AfterReturning` 可拿到返回值；`@AfterThrowing` 捕获异常；`@After` 无论成功/失败都会执行。

#### 2. 进阶：环绕通知统计耗时与统一异常转换

```java
@Aspect
@Component
public class ProfilingAspect {

  @Around("execution(* com.example..controller..*(..))")
  public Object around(ProceedingJoinPoint pjp) throws Throwable {
    long start = System.nanoTime();
    String method = pjp.getSignature().toShortString();
    try {
      Object ret = pjp.proceed();
      long costMs = (System.nanoTime() - start) / 1_000_000;
      System.out.println("[AOP] " + method + " cost=" + costMs + "ms");
      return ret;
    } catch (IllegalArgumentException e) {
      // 将异常统一转换为业务异常
      throw new BizException("参数错误: " + e.getMessage());
    }
  }
}
```

要点：
- `@Around` 独占执行链，必须调用 `pjp.proceed()` 才会继续到目标方法。
- 可测量性能、包装返回值、统一异常。

#### 3. 复杂：自定义注解 + 参数解析 + 权限控制（含 SpEL）

目标：基于 `@RequirePermission` 注解定义权限点，支持从方法参数解析用户、资源 ID，甚至支持 SpEL 表达式解析动态权限键，失败则抛出 `AccessDeniedException`。

1) 定义注解

```java
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.METHOD})
public @interface RequirePermission {
  // 静态权限，例如 "post:edit"
  String value() default "";

  // 支持 SpEL，例如 "post:edit:#{#postId}"
  String spel() default "";

  // 需要的角色（任一命中即可放行）
  String[] roles() default {};
}
```

2) 定义权限检查服务（示例）

```java
public interface PermissionService {
  boolean hasPermission(String userId, String permissionKey);
  boolean hasAnyRole(String userId, Collection<String> roles);
}

@Service
public class InMemoryPermissionService implements PermissionService {
  private final Map<String, Set<String>> userPerms = new ConcurrentHashMap<>();
  private final Map<String, Set<String>> userRoles = new ConcurrentHashMap<>();

  @PostConstruct
  public void init() {
    userPerms.put("u1", new HashSet<>(Arrays.asList("post:edit:1", "post:view")));
    userRoles.put("u1", new HashSet<>(Arrays.asList("ADMIN")));
  }

  public boolean hasPermission(String userId, String permissionKey) {
    return userPerms.getOrDefault(userId, Collections.emptySet()).contains(permissionKey);
  }

  public boolean hasAnyRole(String userId, Collection<String> roles) {
    Set<String> r = userRoles.getOrDefault(userId, Collections.emptySet());
    for (String role : roles) if (r.contains(role)) return true;
    return false;
  }
}
```

3) 获取当前用户的简单上下文

```java
public class SecurityContextHolderLite {
  private static final ThreadLocal<String> USER = new ThreadLocal<>();
  public static void setUserId(String userId) { USER.set(userId); }
  public static String getUserId() { return USER.get(); }
  public static void clear() { USER.remove(); }
}
```

4) 切面：解析注解、绑定参数名、解析 SpEL、执行校验

```java
@Aspect
@Component
public class PermissionAspect {

  private final PermissionService permissionService;
  private final ExpressionParser parser = new SpelExpressionParser();
  private final ParameterNameDiscoverer nameDiscoverer = new DefaultParameterNameDiscoverer();

  public PermissionAspect(PermissionService permissionService) {
    this.permissionService = permissionService;
  }

  @Around("@annotation(requirePermission)")
  public Object check(ProceedingJoinPoint pjp, RequirePermission requirePermission) throws Throwable {
    Method method = ((MethodSignature) pjp.getSignature()).getMethod();
    String userId = Optional.ofNullable(SecurityContextHolderLite.getUserId())
        .orElseThrow(() -> new AccessDeniedException("未登录"));

    // 1) 角色校验（可选）：任一命中则提前放行
    String[] roles = requirePermission.roles();
    if (roles.length > 0 && permissionService.hasAnyRole(userId, Arrays.asList(roles))) {
      return pjp.proceed();
    }

    // 2) 构造权限键
    String key = requirePermission.value();
    String spel = requirePermission.spel();
    if (!spel.isEmpty()) {
      // 通过 SpEL 从参数中计算动态部分
      EvaluationContext ctx = buildEvalContext(method, pjp.getArgs());
      String evaluated = parser.parseExpression(spel).getValue(ctx, String.class);
      key = key.isEmpty() ? evaluated : (key + ":" + evaluated);
    }
    if (key.isEmpty()) {
      throw new IllegalStateException("@RequirePermission 需要设置 value 或 spel");
    }

    // 3) 权限校验
    if (!permissionService.hasPermission(userId, key)) {
      throw new AccessDeniedException("权限不足: " + key);
    }
    return pjp.proceed();
  }

  private EvaluationContext buildEvalContext(Method method, Object[] args) {
    MethodBasedEvaluationContext ctx = new MethodBasedEvaluationContext(null, method, args, nameDiscoverer);
    // 便捷变量
    ctx.setVariable("args", args);
    return ctx;
  }
}
```

5) 使用方式

```java
@Service
public class PostService {

  // 需要角色 ADMIN 或 拥有权限键 post:edit:{postId}
  @RequirePermission(value = "post:edit", spel = "#{#postId}", roles = {"ADMIN"})
  public void editPost(Long postId, String content) {
    // ... 编辑逻辑
  }
}
```

当调用 `editPost(1L, "...")` 时，切面会拼出权限键 `post:edit:1`；若用户是 `ADMIN` 也可直接通过。

### 切点表达式速查（execution 为主）

- **按包/类/方法**
  - `execution(* com.example.service.*.*(..))`：匹配 `service` 包下所有类的所有方法
  - `execution(* com.example..*(..))`：匹配 `com.example` 及子包所有方法
  - `execution(public * *(..))`：匹配所有 `public` 方法
  - `within(com.example.controller..*)`：限定在该包（类）范围内
- **按类型关系**
  - `this(com.example.FooService)`：代理对象实现/继承该类型
  - `target(com.example.FooService)`：目标对象是该类型
- **按参数/注解**
  - `args(java.lang.String, ..)`：第一个参数是 `String`
  - `@annotation(com.example.Loggable)`：标注了注解的方法
  - `@within(org.springframework.stereotype.Service)`：类上带注解
  - `@target(...)`：目标类带注解
- **按 Bean 名称**
  - `bean(postService)` 或 `bean(*Service)`
- **逻辑组合**
  - `and`、`or`、`not`

常见组合示例：
```text
execution(* com.example..*(..)) and @annotation(org.springframework.transaction.annotation.Transactional)
within(com.example.service..*) and not within(com.example.service.internal..*)
```

### 常用 API 与技巧

- **JoinPoint / ProceedingJoinPoint**
  - `getArgs()`：方法实参数组
  - `getSignature()`：`Signature`，强转为 `MethodSignature` 获取 `Method`
  - `proceed()`：环绕通知放行
- **Signature / MethodSignature**
  - `getDeclaringTypeName()`、`getName()`、`toShortString()`
  - `((MethodSignature) jp.getSignature()).getMethod()`
- **获取注解/方法/类**
  - `Method method = ((MethodSignature) jp.getSignature()).getMethod()`
  - `Annotation ann = method.getAnnotation(...)`
- **Web 上下文**
  - `ServletRequestAttributes attrs = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes()`
  - `HttpServletRequest request = attrs.getRequest()`
- **顺序控制**
  - `@Order(1)` 数值越小优先级越高
- **切点复用**
  - `@Pointcut("execution(..)") public void p() {}`，在多个通知上复用 `p()`

### 常见坑与最佳实践

- **自调用导致 AOP 失效**：同类方法互调不会经过代理。解决：
  - 将被切方法拆到另一个 Bean；或
  - 开启 `@EnableAspectJAutoProxy(exposeProxy = true)` 并用 `((FooService) AopContext.currentProxy()).bar()` 调用。
- **JDK 代理 vs CGLIB**：接口默认用 JDK。若只在实现类上加注解，且通过接口注入调用，可能匹配不到。可强制 CGLIB：
  - `spring.aop.proxy-target-class=true`（Boot）；或手动配置。
- **`final`/`private` 方法无法被代理**（CGLIB 对 private/final 也无能为力），尽量避免。
- **事务与切面顺序**：与 `@Transactional` 协同时注意 `@Order`，需要先鉴权再开启事务可设鉴权切面更小的顺序值。
- **参数名丢失**：SpEL 绑定参数名需编译参数名（-parameters）或使用 `DefaultParameterNameDiscoverer`。

### 更多示例：统一返回包装切面

```java
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.METHOD, ElementType.TYPE})
public @interface WrapResponse {}

@Data
@AllArgsConstructor
public class ApiResult<T> {
  private int code; private String message; private T data;
  public static <T> ApiResult<T> ok(T data) { return new ApiResult<>(0, "ok", data); }
}

@Aspect
@Component
@Order(10)
public class ResponseWrapAspect {
  @Around("@within(WrapResponse) || @annotation(WrapResponse)")
  public Object wrap(ProceedingJoinPoint pjp) throws Throwable {
    Object ret = pjp.proceed();
    if (ret instanceof ApiResult) return ret;
    return ApiResult.ok(ret);
  }
}
```

### 常用方法/类清单（速查）

- **注解**：`@Aspect`、`@Before`、`@Around`、`@After`、`@AfterReturning`、`@AfterThrowing`、`@Pointcut`、`@Order`
- **切点关键字**：`execution`、`within`、`this`、`target`、`args`、`@annotation`、`@within`、`@target`、`bean`
- **核心类型**：`JoinPoint`、`ProceedingJoinPoint`、`Signature`、`MethodSignature`
- **表达式解析**：`ExpressionParser`、`SpelExpressionParser`、`EvaluationContext`、`MethodBasedEvaluationContext`、`ParameterNameDiscoverer`
- **辅助**：`AopContext.currentProxy()`、`RequestContextHolder`、`AnnotationUtils`

### 最小可用 Demo 结构（参考）

```text
com.example
├─ config
│  └─ AopConfig.java
├─ aop
│  ├─ LoggingAspect.java
│  ├─ ProfilingAspect.java
│  ├─ PermissionAspect.java
│  └─ annotation
│     └─ RequirePermission.java
├─ security
│  ├─ PermissionService.java
│  ├─ InMemoryPermissionService.java
│  └─ SecurityContextHolderLite.java
└─ service
   └─ PostService.java
```

### FAQ

- **能否拦截构造函数或字段访问？** Spring AOP 只支持方法级别；需要更强支持请用 AspectJ LTW/CTW。
- **如何仅拦截某注解参数特定值？** 使用 SpEL + 注解属性；或在切面中读取注解并自定义判断。
- **如何在切面中修改入参？** 只能在 `@Around` 中构造新参数数组调用 `proceed(newArgs)`。

