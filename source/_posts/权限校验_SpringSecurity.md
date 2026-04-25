---
title: 权限校验_SpringSecurity
main_color: "#c21b1bff"
categories: 权限校验
tags:
  - 权限校验
cover: https://free.picui.cn/free/2026/03/28/69c74e1f08f27.jpeg
---


## springsecurity

Spring Security 是一个功能强大且高度可定制的认证和授权框架，它致力于为基于Spring的应用程序提供安全性。它是Spring项目家族的一部分，旨在与Spring MVC等框架无缝集成。

### 主要特性

1. **认证**：验证用户的身份，确保用户是他们声称的那个人。Spring Security 支持多种形式的认证，包括HTTP BASIC和HTTP Digest认证、基于表单的登录、OpenID、OAuth2、SAML等。
   
2. **授权**：控制访问应用的不同资源，确保用户只能访问他们被允许访问的资源。这涉及到角色和权限的概念，可以非常细粒度地控制到方法级别或者URL级别的访问权限。
   
3. **保护针对常见攻击的措施**：如会话固定攻击、点击劫持、跨站请求伪造（CSRF）等。Spring Security 提供了内置的机制来防御这些攻击。
   
4. **Servlet API 集成**：提供了对Java EE Servlet API的良好支持，比如它可以很容易地与标准的Java EE安全模型集成，同时又不局限于该模型。
   
5. **可扩展性**：由于其模块化设计，开发者可以根据自己的需求选择合适的组件进行使用，并且可以方便地添加自定义的安全逻辑。

### 核心概念

- **Authentication（认证）**：代表当前用户的认证信息，包括用户名、密码、权限等。
- **Authorization（授权）**：决定一个已认证的用户是否具有执行某个操作或访问某个资源的权限。
- **UserDetailsService**：这是一个接口，通常用于从持久存储中加载用户特定的数据。实现此接口可以帮助你根据用户名获取用户的详细信息，包括密码、权限等。
- **SecurityContext（安全上下文）**：保存当前认证信息的对象，可以在整个请求生命周期内访问。

### 使用场景

Spring Security 可以被用来保护几乎任何类型的应用程序，但特别适用于需要精细控制用户访问权限的Web应用程序。无论是构建内部企业级应用还是面向公众的网站，Spring Security都能提供必要的工具来满足复杂的安全需求。通过配置不同的过滤器和提供者，可以轻松适应各种安全策略和要求。



## 认证流程

好的，我们来深入探讨一下Spring Security认证流程的底层原理，尽量做到通俗易懂，同时揭示其背后的核心机制。

### Spring Security 认证流程底层原理详解

我们可以把整个流程想象成一个高度组织化、流程化的“身份验证工厂”。核心在于**责任分离**和**委托模式**。

#### 1. 请求拦截：`FilterChainProxy` 与 `SecurityFilterChain`

*   **原理**：Spring Security 的核心是基于 **Servlet Filter**。它通过 `FilterChainProxy` 这个特殊的过滤器，将一组安全相关的过滤器（`SecurityFilterChain`）注入到标准的 Servlet 过滤器链中。
*   **底层操作**：当一个HTTP请求到达时，`FilterChainProxy` 会根据请求的URL等信息，决定使用哪一条 `SecurityFilterChain` 来处理。这个 `SecurityFilterChain` 包含了一系列按特定顺序排列的 `Filter`。
*   **关键点**：这些 `Filter` 是**有顺序**的，每个 `Filter` 负责一个特定的安全任务。例如：
    *   `WebAsyncManagerIntegrationFilter`: 处理异步请求的安全上下文传递。
    *   `SecurityContextPersistenceFilter`: **极其重要**！它负责在请求开始时，从 `SecurityContextRepository`（通常是 `HttpSessionSecurityContextRepository`，即从Session中）加载 `SecurityContext`，并放入 `SecurityContextHolder`。在请求结束时，它会将更新后的 `SecurityContext` 再保存回 `SecurityContextRepository`。这保证了“一次登录，整个会话有效”。
    *   后续的过滤器（如 `UsernamePasswordAuthenticationFilter`）就可以从 `SecurityContextHolder` 中获取当前的 `SecurityContext` 和 `Authentication` 信息。

#### 2. 触发认证：特定的 `AuthenticationFilter` (如 `UsernamePasswordAuthenticationFilter`)

*   **原理**：当请求需要认证时（比如提交了登录表单），特定的过滤器会被触发。
*   **底层操作**：以表单登录为例，`UsernamePasswordAuthenticationFilter` 会：
    1.  检查请求是否是登录请求（通常是POST到 `/login`）。
    2.  从请求中提取用户名（`username`）和密码（`password`）。
    3.  将这些信息封装成一个 **`UsernamePasswordAuthenticationToken`** 对象。这个对象是一个 `Authentication` 接口的实现，此时它处于 **`unauthenticated`** 状态（`getAuthenticated()` 返回 `false`），因为它只包含了用户提供的凭据，还没有经过验证。
    4.  调用 `AuthenticationManager` 的 `authenticate()` 方法，并将这个未认证的 `Authentication` 对象作为参数传入。

#### 3. 协调认证：`AuthenticationManager` (`ProviderManager`)

*   **原理**：`AuthenticationManager` 是一个接口，其标准实现是 `ProviderManager`。它本身不执行认证逻辑，而是扮演“**协调者**”的角色。
*   **底层操作**：
    1.  `ProviderManager` 持有一个 `List<AuthenticationProvider>`。
    2.  当它收到 `authenticate()` 调用时，它会遍历这个列表中的每一个 `AuthenticationProvider`。
    3.  对于列表中的每个 `AuthenticationProvider`，它会先调用 `supports(Class<?> authentication)` 方法，询问：“你支持处理这种类型的 `Authentication` 对象吗？”（比如，`DaoAuthenticationProvider` 支持 `UsernamePasswordAuthenticationToken`）。
    4.  如果某个 `AuthenticationProvider` 返回 `true`，`ProviderManager` 就会调用该 `AuthenticationProvider` 的 `authenticate(Authentication authentication)` 方法，并将未认证的 `Authentication` 对象传递给它。

#### 4. 执行认证：`AuthenticationProvider` (如 `DaoAuthenticationProvider`)

*   **原理**：`AuthenticationProvider` 是真正执行认证逻辑的地方。不同的 `Provider` 实现不同的认证机制（数据库、LDAP、OAuth2等）。
*   **底层操作**（以 `DaoAuthenticationProvider` 为例）：
    1.  它接收到 `ProviderManager` 传来的未认证的 `Authentication` 对象（包含用户名和密码）。
    2.  它调用配置好的 `UserDetailsService` 的 `loadUserByUsername(String username)` 方法，根据用户名去加载用户信息。
    3.  `UserDetailsService` 从数据库、内存或其他数据源中查询用户，返回一个 `UserDetails` 对象。这个对象包含了用户的正确密码（加密后的）、权限（`GrantedAuthority`）、账户状态（是否启用、是否过期）等信息。
    4.  `DaoAuthenticationProvider` 将用户提交的密码（明文）与 `UserDetails` 中存储的密码（加密后的）进行比对。这个比对工作由 `PasswordEncoder` 完成。
    5.  如果密码匹配，并且账户状态有效，`DaoAuthenticationProvider` 会创建一个新的 `UsernamePasswordAuthenticationToken` 对象。**关键区别**：这个新的 `Authentication` 对象是 **`authenticated`** 状态（`setAuthenticated(true)`），并且它的 `principal` 属性是完整的 `UserDetails` 对象（而不仅仅是用户名），`credentials` 通常会被清空（出于安全考虑），`authorities` 属性则来自 `UserDetails`。
    6.  将这个已认证的 `Authentication` 对象返回给 `ProviderManager`。
    7.  如果认证失败（密码不匹配、用户不存在、账户禁用等），`AuthenticationProvider` 会抛出相应的 `AuthenticationException`（如 `BadCredentialsException`, `UsernameNotFoundException`）。

#### 5. 返回结果：`ProviderManager` -> `AuthenticationFilter`

*   **原理**：`ProviderManager` 收到 `AuthenticationProvider` 返回的结果。
*   **底层操作**：
    *   如果成功，`ProviderManager` 将已认证的 `Authentication` 对象返回给调用它的 `AuthenticationFilter`。
    *   如果失败，它会将捕获到的 `AuthenticationException` 继续向上抛出。

#### 6. 处理结果：`AuthenticationFilter`

*   **原理**：`AuthenticationFilter` 收到结果后，进行后续处理。
*   **底层操作**：
    *   **成功**：调用 `onSuccessfulAuthentication()` 方法。
        1.  调用 `SecurityContextHolder.getContext().setAuthentication(authenticatedAuthentication)`。这会将已认证的 `Authentication` 对象放入当前线程的 `SecurityContext` 中。
        2.  触发 `AuthenticationSuccessHandler`（如 `SavedRequestAwareAuthenticationSuccessHandler`），通常会进行重定向（比如跳转到登录前的页面或首页）。
    *   **失败**：调用 `onUnsuccessfulAuthentication()` 方法。
        1.  触发 `AuthenticationFailureHandler`（如 `SimpleUrlAuthenticationFailureHandler`），通常会重定向回登录页并显示错误信息。

#### 7. 持久化上下文：`SecurityContextPersistenceFilter` (请求结束时)

*   **原理**：在请求的最后阶段，`SecurityContextPersistenceFilter` 再次发挥作用。
*   **底层操作**：
    1.  它从 `SecurityContextHolder` 中获取当前线程的 `SecurityContext`。
    2.  调用 `SecurityContextRepository`（默认是 `HttpSessionSecurityContextRepository`）的 `saveContext()` 方法。
    3.  这个 `Repository` 会将 `SecurityContext`（包含了已认证的 `Authentication` 对象）**序列化并存储到 HTTP Session 中**。
    4.  这样，当下一个请求到来时，`SecurityContextPersistenceFilter` 在请求开始时就能从Session中重新加载这个 `SecurityContext`，从而实现“一次登录，会话内有效”。

### 总结：底层核心机制

1.  **过滤器链驱动**：一切始于 `FilterChainProxy` 和 `SecurityFilterChain`，通过一系列有序的 `Filter` 拦截和处理请求。
2.  **安全上下文 (`SecurityContext`) 的生命周期管理**：`SecurityContextPersistenceFilter` 负责在请求开始时从存储（如Session）加载上下文，在请求结束时将更新后的上下文存回存储。`SecurityContextHolder` 是访问当前线程 `SecurityContext` 的静态工具。
3.  **认证流程的委托与协作**：
    *   `AuthenticationFilter` 捕获登录请求，创建未认证的 `Authentication`。
    *   `AuthenticationManager` (`ProviderManager`) 遍历 `AuthenticationProvider` 列表，寻找合适的 `Provider`。
    *   `AuthenticationProvider` 调用 `UserDetailsService` 获取用户数据，并使用 `PasswordEncoder` 验证密码，生成已认证的 `Authentication`。
4.  **数据源抽象**：`UserDetailsService` 抽象了用户信息的来源，`PasswordEncoder` 抽象了密码的加密和验证方式，`SecurityContextRepository` 抽象了 `SecurityContext` 的存储方式。这使得框架非常灵活，易于扩展和定制。

简单来说，Spring Security 通过**过滤器链**拦截请求，利用**安全上下文**在请求间保持用户状态，通过**`AuthenticationManager`** 协调，由具体的 **`AuthenticationProvider`** 调用 **`UserDetailsService`** 获取用户信息并验证凭证，最终将认证结果存入上下文并持久化到Session中，从而完成整个认证流程。


## 过滤器

好的，我们来深入、系统地讲解 Spring Security 的过滤器体系，从设计思想到实战应用。

### Spring Security 过滤器：从原理到实践

Spring Security 的核心安全机制建立在 **Servlet Filter** 之上。理解其过滤器链是掌握 Spring Security 的关键。

---

#### 一、 设计思想：责任链模式 (Chain of Responsibility Pattern)

*   **核心理念**：将一个复杂的请求处理过程分解为一系列**独立的、职责单一的处理单元（过滤器）**，这些单元按特定顺序连接成一条“链”。
*   **工作流程**：
    1.  **拦截**：HTTP 请求到达应用时，首先被过滤器链的**第一个过滤器**拦截。
    2.  **处理/委托**：每个过滤器执行其特定的安全任务（如认证、授权、CSRF检查等）。
    3.  **传递**：如果当前过滤器的逻辑允许请求继续（例如，认证成功或无需处理），它会调用 `FilterChain.doFilter(request, response)` 方法，将请求和响应对象传递给链中的**下一个过滤器**。
    4.  **终止**：如果某个过滤器的逻辑阻止了请求（例如，认证失败、权限不足），它会**直接向客户端返回响应**（如401 Unauthorized, 403 Forbidden），并**不再调用 `doFilter`**，从而中断整个链条。后续的过滤器和最终的业务逻辑（Servlet）都不会被执行。
    5.  **返回**：当请求最终到达业务逻辑并处理完毕后，响应会沿着过滤器链**反向**传递回来，每个过滤器有机会在响应返回客户端前进行后处理（如清理资源）。

*   **优势**：
    *   **模块化**：每个过滤器只关心一个特定的安全功能，代码清晰，易于维护和测试。
    *   **可扩展性**：可以轻松地添加、移除或重新排序过滤器，以定制安全策略。
    *   **灵活性**：不同的应用可以配置不同的过滤器链。
    *   **解耦**：业务逻辑与安全逻辑完全分离。

---

#### 二、 基础架构：核心组件

1.  **`FilterChainProxy`**:
    *   **角色**：这是 Spring Security 过滤器链的“**总代理**”或“**门面**”。它本身是一个标准的 `javax.servlet.Filter`。
    *   **职责**：
        *   作为 Spring Security 在 Servlet 容器过滤器链中的**唯一入口点**。
        *   持有并管理一个或多个 `SecurityFilterChain` 实例。
        *   根据请求的 URL 和其他条件，决定使用哪一个 `SecurityFilterChain` 来处理当前请求。
        *   将请求委托给选中的 `SecurityFilterChain` 执行。

2.  **`SecurityFilterChain`**:
    *   **角色**：一个**过滤器链的配置**，定义了在特定条件下（如特定URL模式）需要应用哪些安全过滤器以及它们的顺序。
    *   **组成**：本质上是一个 `List<Filter>`。在 Spring Boot 中，通常通过 `HttpSecurity` 对象的 DSL（领域特定语言）来配置。
    *   **特点**：一个应用可以有多个 `SecurityFilterChain`，实现对不同路径（如 `/api/**`, `/admin/**`, `/static/**`）应用不同的安全策略。

3.  **`SecurityContextHolder`**:
    *   **角色**：一个**静态工具类**，用于存储当前线程的安全上下文（`SecurityContext`）。
    *   **`SecurityContext`**: 包含当前用户的认证信息（`Authentication` 对象）。
    *   **`Authentication`**: 代表当前用户的身份和权限，包含 `Principal`（通常是用户名或 `UserDetails`）、`Credentials`（通常是密码，认证后通常设为null）、`Authorities`（权限列表）等。
    *   **重要性**：整个过滤器链和业务代码都通过 `SecurityContextHolder` 来获取当前用户的认证状态。**它是贯穿整个请求处理过程的“安全信息载体”**。

---

#### 三、 常用核心 Filter (按典型执行顺序)

Spring Security 内置了数十个过滤器。以下是关键过滤器及其作用：

1.  **`WebAsyncManagerIntegrationFilter`**:
    *   **作用**：确保在使用 Spring 的 `Callable` 或 `WebAsyncTask` 进行异步请求处理时，`SecurityContext` 能够在不同的线程间正确传递。

2.  **`SecurityContextPersistenceFilter`**:
    *   **作用**：**极其重要！**
        *   **请求开始时**：从 `SecurityContextRepository`（默认是 `HttpSessionSecurityContextRepository`）中加载 `SecurityContext`（通常从 HTTP Session 中反序列化），并放入 `SecurityContextHolder`。如果 Session 中没有，创建一个空的 `SecurityContext`。
        *   **请求结束时**：将 `SecurityContextHolder` 中当前的 `SecurityContext` 保存回 `SecurityContextRepository`（默认存回 Session）。**这是实现“一次登录，会话有效”的关键**。

3.  **`HeaderWriterFilter`**:
    *   **作用**：向响应头中添加安全相关的头部，如 `X-Content-Type-Options: nosniff`, `X-XSS-Protection`, `X-Frame-Options` (防御点击劫持) 等。

4.  **`CsrfFilter`**:
    *   **作用**：防御跨站请求伪造（CSRF）攻击。检查 POST/PUT/DELETE 等非安全请求是否包含有效的 CSRF Token。通常与表单或 `@CsrfToken` 注解配合使用。

5.  **`LogoutFilter`**:
    *   **作用**：处理登出请求（默认 `/logout`）。验证登出请求，清除 `SecurityContext`，使 Session 无效（可选），并重定向到登录页或指定页面。

6.  **`UsernamePasswordAuthenticationFilter`**:
    *   **作用**：处理基于表单的登录请求（默认 POST `/login`）。
        *   从请求中提取 `username` 和 `password` 参数。
        *   封装成 `UsernamePasswordAuthenticationToken`。
        *   调用 `AuthenticationManager` 进行认证。
        *   认证成功：调用 `AuthenticationSuccessHandler`（如重定向）。
        *   认证失败：调用 `AuthenticationFailureHandler`（如重定向回登录页）。

7.  **`DefaultLoginPageGeneratingFilter` / `DefaultLogoutPageGeneratingFilter`**:
    *   **作用**：当没有配置自定义登录/登出页，且启用了默认生成时，自动提供一个简单的登录/登出表单页面。

8.  **`BearerTokenAuthenticationFilter`**:
    *   **作用**：在 OAuth2 或 JWT 场景下，从请求头（`Authorization: Bearer <token>`）中提取 JWT 或 OAuth2 访问令牌，并尝试进行认证。

9.  **`RequestCacheAwareFilter`**:
    *   **作用**：在用户认证成功后，如果之前访问了一个需要认证的资源，它会从 `RequestCache` 中恢复原始的请求，并重定向用户到那个资源，而不是直接跳转到首页。

10. **`SecurityContextHolderAwareRequestFilter`**:
    *   **作用**：包装原始的 `HttpServletRequest`，使其能够通过 `isUserInRole()`, `getRemoteUser()` 等方法与 `SecurityContext` 交互，方便在业务代码中进行简单的安全检查。

11. **`AnonymousAuthenticationFilter`**:
    *   **作用**：如果 `SecurityContextHolder` 中没有 `Authentication` 对象（即用户未登录），此过滤器会创建一个 `AnonymousAuthenticationToken` 并放入 `SecurityContext`。这使得“匿名用户”也有一个身份，方便后续的授权决策（例如，`permitAll()` 或 `hasRole('ANONYMOUS')`）。

12. **`SessionManagementFilter`**:
    *   **作用**：处理与 Session 相关的安全功能，如：
        *   检测 Session Fixation 攻击并创建新 Session。
        *   应用 `SessionAuthenticationStrategy`。
        *   检查并发 Session 控制（如限制一个用户只能有一个登录会话）。

13. **`ExceptionTranslationFilter`**:
    *   **作用**：**极其重要！**
        *   它位于过滤器链的靠后位置（通常在授权过滤器之前）。
        *   它不主动执行安全检查，而是**捕获**在其之后执行的过滤器（主要是 `FilterSecurityInterceptor`）抛出的两种异常：
            *   `AuthenticationException`：认证失败（如未登录、凭证错误）-> 调用 `AuthenticationEntryPoint`（如重定向到登录页或返回 401）。
            *   `AccessDeniedException`：授权失败（如权限不足）-> 调用 `AccessDeniedHandler`（如返回 403）。
        *   **它将底层的安全异常转换为对客户端有意义的 HTTP 响应**。

14. **`FilterSecurityInterceptor`**:
    *   **作用**：这是**授权决策**的核心过滤器。
        *   它基于 `HttpSecurity` 中配置的 `authorizeHttpRequests()` 规则（如 `.antMatchers("/admin/**").hasRole("ADMIN")`）。
        *   调用 `AccessDecisionManager` 来决定当前 `Authentication` 是否有权访问当前请求的资源。
        *   如果有权限，放行；如果没有权限，抛出 `AccessDeniedException`，该异常会被前面的 `ExceptionTranslationFilter` 捕获并处理。

---

#### 四、 在 Spring Boot 中的用法

在 Spring Boot 中，通过 `WebSecurityConfigurerAdapter` (旧) 或直接配置 `SecurityFilterChain` Bean (新) 来定义过滤器链。

**使用 `@Bean SecurityFilterChain` (推荐，Spring Boot 2.7+)**:

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.provisioning.InMemoryUserDetailsManager;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
public class SecurityConfig {

    // 1. 定义 SecurityFilterChain Bean
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
            // 2. 配置请求授权规则
            .authorizeHttpRequests(authz -> authz
                .requestMatchers("/public/**").permitAll() // 公共路径放行
                .requestMatchers("/admin/**").hasRole("ADMIN") // /admin/** 需要 ADMIN 角色
                .anyRequest().authenticated() // 其他所有请求都需要认证
            )
            // 3. 配置表单登录
            .formLogin(form -> form
                .loginPage("/login") // 自定义登录页
                .permitAll() // 登录页放行
            )
            // 4. 配置登出
            .logout(logout -> logout
                .permitAll() // 登出页放行
            )
            // 5. (可选) 禁用 CSRF (仅在测试API时，生产环境通常开启)
            //.csrf(csrf -> csrf.disable())
            ;

        // 6. (可选) 在特定位置添加自定义过滤器
        // http.addFilterBefore(new MyCustomFilter(), UsernamePasswordAuthenticationFilter.class);
        // http.addFilterAfter(new AnotherCustomFilter(), CsrfFilter.class);

        // 7. 构建并返回 SecurityFilterChain
        return http.build();
    }

    // 8. 提供 UserDetailsService Bean
    @Bean
    public UserDetailsService userDetailsService() {
        UserDetails user = User.withDefaultPasswordEncoder()
            .username("user")
            .password("password")
            .roles("USER")
            .build();
        UserDetails admin = User.withDefaultPasswordEncoder()
            .username("admin")
            .password("adminpass")
            .roles("ADMIN", "USER")
            .build();
        return new InMemoryUserDetailsManager(user, admin);
    }
}
```

*   **`HttpSecurity`**: 提供了流畅的 DSL 来配置安全策略，内部会根据配置自动构建相应的 `SecurityFilterChain` 和 `Filter`。
*   **自动配置**：Spring Boot 的 `spring-boot-starter-security` 会自动将 `FilterChainProxy` 注册到 Servlet 容器的过滤器链中，并查找应用上下文中的 `SecurityFilterChain` Bean。

---

#### 五、 自定义过滤器

当内置过滤器无法满足需求时，可以创建自定义过滤器。

**步骤**:

1.  **创建过滤器类**：实现 `javax.servlet.Filter` 接口。

    ```java
    import javax.servlet.*;
    import javax.servlet.http.HttpServletRequest;
    import java.io.IOException;

    public class MyCustomFilter implements Filter {

        @Override
        public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
                throws IOException, ServletException {

            HttpServletRequest httpRequest = (HttpServletRequest) request;

            // 1. 前处理 (Pre-processing)
            System.out.println("MyCustomFilter: Processing request for " + httpRequest.getRequestURI());

            // (可选) 进行一些安全检查或修改
            // String apiKey = httpRequest.getHeader("X-API-Key");
            // if (!isValidApiKey(apiKey)) {
            //     ((HttpServletResponse) response).sendError(HttpServletResponse.SC_FORBIDDEN, "Invalid API Key");
            //     return; // 中断链条
            // }

            // 2. 将请求传递给下一个过滤器 (关键!)
            chain.doFilter(request, response); // 放行

            // 3. 后处理 (Post-processing) - 响应返回时执行
            System.out.println("MyCustomFilter: Request processing completed for " + httpRequest.getRequestURI());
        }

        // 其他方法 (init, destroy) 通常留空或根据需要实现
        @Override
        public void init(FilterConfig filterConfig) throws ServletException {}

        @Override
        public void destroy() {}
    }
    ```

2.  **注册并添加到过滤器链**：在 `SecurityConfig` 中使用 `addFilterBefore()` 或 `addFilterAfter()`。

    ```java
    @Configuration
    public class SecurityConfig {

        @Bean
        public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
            // ... 其他配置 (authorizeHttpRequests, formLogin 等)

            // 将自定义过滤器添加到 UsernamePasswordAuthenticationFilter 之前
            http.addFilterBefore(new MyCustomFilter(), UsernamePasswordAuthenticationFilter.class);

            // 或者添加到 CsrfFilter 之后
            // http.addFilterAfter(new MyCustomFilter(), CsrfFilter.class);

            return http.build();
        }

        // ... userDetailsService Bean
    }
    ```

**注意事项**:
*   **顺序至关重要**：过滤器的顺序决定了它们的执行顺序。例如，一个用于认证的过滤器必须在 `FilterSecurityInterceptor`（授权）之前。
*   **调用 `chain.doFilter()`**：除非你想中断请求（如返回错误响应），否则**必须**调用 `chain.doFilter(request, response)` 以将请求传递给下一个过滤器。
*   **线程安全**：`Filter` 实例通常是单例，其 `doFilter` 方法会被多个线程并发调用，确保代码是线程安全的。
*   **`SecurityContextHolder`**：自定义过滤器可以安全地读取和修改 `SecurityContextHolder` 中的 `SecurityContext`。



## AuthenticationProvider

### `AuthenticationProvider` 接口介绍

在 Spring Security 中，`AuthenticationProvider` 是一个核心接口，用于定义认证逻辑。它允许开发者实现自定义的认证机制，无论是基于数据库、LDAP、OAuth2、JWT 还是其他任何形式的身份验证。

#### 功能概述

- **认证处理**：`AuthenticationProvider` 的主要职责是对传入的 `Authentication` 对象进行验证，并返回一个完全填充（包含权限信息）的 `Authentication` 对象，如果认证成功；或者抛出相应的异常，如果认证失败。
- **支持多种认证方式**：通过实现 `AuthenticationProvider` 接口，可以支持不同的认证方式，比如用户名密码登录、API Token 认证、OAuth2 认证等。
- **集成到安全框架**：一旦实现了 `AuthenticationProvider`，你可以将其注册到 Spring Security 的 `AuthenticationManager` 中，这样 Spring Security 就可以在需要时调用你的认证逻辑。

#### 方法说明

`AuthenticationProvider` 接口定义了两个方法：

1. **`authenticate(Authentication authentication)`**:
   - **参数**：传入待认证的 `Authentication` 对象。
   - **返回值**：如果认证成功，则返回一个填充了用户详细信息和权限的 `Authentication` 对象；如果无法处理该类型的认证请求（例如，不是预期的认证类型），则返回 `null`。
   - **异常**：
     - `AuthenticationException`：如果认证失败（如密码错误），则抛出此异常或其子类（如 `BadCredentialsException`）。

2. **`supports(Class<?> authentication)`**:
   - **参数**：待检查的 `Authentication` 类型。
   - **返回值**：如果该 `AuthenticationProvider` 支持给定类型的认证请求，则返回 `true`；否则返回 `false`。
   - **用途**：帮助 Spring Security 确定哪个 `AuthenticationProvider` 应该用来处理特定类型的认证请求。

#### 通常使用场景

1. **自定义认证逻辑**：当你需要实现不同于默认提供的认证方式（如基于内存或 JDBC 的用户存储）时，可以通过实现 `AuthenticationProvider` 来定制化认证流程。
   
2. **多因素认证（MFA）**：可以为不同阶段的认证过程提供多个 `AuthenticationProvider` 实例，每个实例负责验证一部分凭据（如密码+短信验证码）。

3. **第三方服务集成**：当需要与外部系统（如 OAuth2 提供商、LDAP 目录服务器）进行交互以完成认证时，可以编写对应的 `AuthenticationProvider`。

#### 示例代码

下面是一个简单的示例，展示了如何创建一个自定义的 `AuthenticationProvider`，以及如何将其集成到 Spring Security 配置中。

```java
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.stereotype.Component;

@Component
public class CustomAuthenticationProvider implements AuthenticationProvider {

    private final UserDetailsService userDetailsService;

    public CustomAuthenticationProvider(UserDetailsService userDetailsService) {
        this.userDetailsService = userDetailsService;
    }

    @Override
    public Authentication authenticate(Authentication authentication) throws AuthenticationException {
        String username = authentication.getName();
        String password = authentication.getCredentials().toString();

        UserDetails userDetails = userDetailsService.loadUserByUsername(username);

        if (!password.equals(userDetails.getPassword())) { // 实际应用中应使用 PasswordEncoder 比较密码
            throw new BadCredentialsException("Invalid username or password");
        }

        return new UsernamePasswordAuthenticationToken(userDetails, password, userDetails.getAuthorities());
    }

    @Override
    public boolean supports(Class<?> authentication) {
        return authentication.equals(UsernamePasswordAuthenticationToken.class);
    }
}
```

然后，在配置类中注册这个 `AuthenticationProvider`：

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.ProviderManager;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;

@Configuration
@EnableWebSecurity
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    private final CustomAuthenticationProvider customAuthenticationProvider;

    public SecurityConfig(CustomAuthenticationProvider customAuthenticationProvider) {
        this.customAuthenticationProvider = customAuthenticationProvider;
    }

    @Override
    protected void configure(AuthenticationManagerBuilder auth) throws Exception {
        auth.authenticationProvider(customAuthenticationProvider);
    }

    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http
            .authorizeRequests()
                .antMatchers("/public/**").permitAll()
                .anyRequest().authenticated()
            .and()
            .formLogin(); // 启用表单登录，默认会使用配置的 AuthenticationProvider
    }
}
```

在这个例子中，我们定义了一个名为 `CustomAuthenticationProvider` 的类来执行基本的用户名/密码认证，并将其注册到了 Spring Security 的 `AuthenticationManager` 中。这样，每当有基于用户名和密码的认证请求时，Spring Security 就会调用我们的 `CustomAuthenticationProvider` 来处理认证逻辑。



## UserDetailsService vs AuthenticationProvider

在许多情况下，特别是当你只需要基于用户名和密码进行认证时，通过实现 `UserDetailsService` 接口并重写 `loadUserByUsername` 方法就足够了。这个方法的主要职责是从持久层（如数据库、LDAP等）加载用户信息，并将其封装成一个 `UserDetails` 对象返回给 Spring Security。

然而，有些场景下你可能需要更复杂的认证逻辑，这时候就需要自定义 `AuthenticationProvider`。下面我将详细解释为什么有时候需要这样做，以及两者的区别和适用场景。

### `UserDetailsService` vs `AuthenticationProvider`

#### `UserDetailsService`
- **功能**：主要用于从数据源（如数据库）加载用户详情。
- **使用场景**：适用于简单的认证场景，尤其是当认证过程仅涉及用户名和密码验证时。例如，标准的表单登录流程中，Spring Security 会调用 `UserDetailsService` 来获取用户的详细信息（包括权限），然后由框架内部的认证机制（如 `DaoAuthenticationProvider` 默认实现）来进行密码校验。
- **优点**：简化了开发工作，尤其适合快速集成或小型应用。
- **局限性**：如果需要支持额外的认证方式（如多因素认证、OAuth2、JWT等），或者需要在认证过程中执行特定的业务逻辑，则不够灵活。

#### `AuthenticationProvider`
- **功能**：提供完整的认证逻辑，包括但不限于验证凭据（如密码）、检查附加条件（如账户是否启用）、处理不同类型的认证请求（如API令牌、OAuth2访问令牌等）。
- **使用场景**：
  - 当你需要实现非标准的认证机制时（比如基于API密钥、JWT令牌、OAuth2等）。
  - 如果认证过程不仅仅依赖于用户名和密码，还涉及到其他形式的身份验证（如短信验证码、生物识别等）。
  - 在认证过程中需要执行一些特殊的逻辑，比如动态调整权限集、记录登录尝试等。
- **优点**：提供了更高的灵活性和控制力，能够满足各种复杂的安全需求。
- **局限性**：相比 `UserDetailsService`，编写和维护成本更高，因为需要手动处理更多的细节。

### 示例说明何时选择哪种方式

假设你正在构建一个RESTful API服务，并决定使用JWT作为身份验证手段。在这种情况下：

1. **使用 `UserDetailsService` 的场景**：
   - 如果你的API只接受用户名和密码来换取JWT令牌，并且后续的所有请求都携带此JWT令牌进行鉴权，那么你可以仅依赖 `UserDetailsService` 来验证初始的用户名/密码组合，然后生成JWT令牌。
   
2. **使用 `AuthenticationProvider` 的场景**：
   - 如果你想直接使用JWT令牌进行身份验证，而不需要首先通过用户名和密码交换令牌，你就需要创建一个自定义的 `AuthenticationProvider` 来解析和验证传入的JWT令牌。
   - 或者，如果你希望在认证过程中加入更多步骤，比如检查JWT的有效性、解码JWT以提取用户信息并验证其签名等，这都需要在 `AuthenticationProvider` 中实现。

### 实际例子

以下是一个简单的示例，展示如何使用 `JwtAuthenticationProvider` 进行基于JWT的身份验证：

```java
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.authentication.preauth.PreAuthenticatedAuthenticationToken;

public class JwtAuthenticationProvider implements AuthenticationProvider {

    @Override
    public Authentication authenticate(Authentication authentication) throws AuthenticationException {
        String token = (String) authentication.getCredentials();
        
        // 假设这里有一个工具类来验证和解析JWT
        if (!JwtUtil.validateToken(token)) {
            throw new BadCredentialsException("Invalid JWT token");
        }
        
        // 解析出用户信息
        UserDetails userDetails = JwtUtil.parseToken(token);
        
        return new PreAuthenticatedAuthenticationToken(userDetails, token, userDetails.getAuthorities());
    }

    @Override
    public boolean supports(Class<?> authentication) {
        return PreAuthenticatedAuthenticationToken.class.isAssignableFrom(authentication);
    }
}
```

在这个例子中，我们实现了 `authenticate` 方法来验证JWT的有效性，并从中提取用户信息。同时，我们指定了该 `AuthenticationProvider` 支持 `PreAuthenticatedAuthenticationToken` 类型的认证请求。

### 总结

- **`UserDetailsService`** 是一种简便的方式，适用于大多数基于用户名和密码的传统认证场景。
- **`AuthenticationProvider`** 提供了更大的灵活性，适用于需要自定义认证逻辑的情况，比如多因素认证、OAuth2、JWT等高级认证机制。



## 密码加密器

在 Spring Boot 应用中，设置密码加密器主要是通过配置 `PasswordEncoder` 来实现的。Spring Security 提供了多种 `PasswordEncoder` 实现，包括但不限于 `BCryptPasswordEncoder`, `Pbkdf2PasswordEncoder`, `SCryptPasswordEncoder` 等等。下面将介绍如何在 Spring Boot 中设置和使用 `PasswordEncoder`。

### 1. 添加依赖

确保你的 `pom.xml` 或 `build.gradle` 文件中包含 Spring Security 的依赖。如果你正在使用 Spring Boot Starter，通常只需添加：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-security</artifactId>
</dependency>
```

对于 Gradle 用户，则是：

```gradle
implementation 'org.springframework.boot:spring-boot-starter-security'
```

### 2. 配置 PasswordEncoder Bean

你可以在配置类中定义一个 `PasswordEncoder` Bean。例如，使用 BCrypt 进行密码加密：

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;

@Configuration
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
```

这段代码创建了一个 `BCryptPasswordEncoder` 的 Bean，它会在整个应用程序上下文中被自动发现并使用。

### 3. 使用 PasswordEncoder

#### 在 Service 层使用

当你需要存储用户信息时（比如注册新用户），可以使用 `PasswordEncoder` 对用户提供的明文密码进行加密处理：

```java
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class UserService {

    private final PasswordEncoder passwordEncoder;

    public UserService(PasswordEncoder passwordEncoder) {
        this.passwordEncoder = passwordEncoder;
    }

    public void createUser(User user) {
        String hashedPassword = passwordEncoder.encode(user.getPassword());
        // 将 hashedPassword 存储到数据库中...
    }
}
```

#### 在 AuthenticationProvider 中使用

如果你自定义了 `AuthenticationProvider`，也需要在这里使用 `PasswordEncoder` 来验证输入的密码是否与存储的哈希密码匹配：

```java
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.crypto.password.PasswordEncoder;

public class CustomAuthenticationProvider implements AuthenticationProvider {

    private final PasswordEncoder passwordEncoder;

    public CustomAuthenticationProvider(PasswordEncoder passwordEncoder) {
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public Authentication authenticate(Authentication authentication) throws AuthenticationException {
        String username = authentication.getPrincipal().toString();
        String presentedPassword = authentication.getCredentials().toString();

        // 假设这里从数据库加载用户信息
        User userDetails = loadUserByUsername(username);

        if (passwordEncoder.matches(presentedPassword, userDetails.getPassword())) {
            // 密码匹配成功
            return new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
        } else {
            throw new BadCredentialsException("密码错误");
        }
    }

    @Override
    public boolean supports(Class<?> authentication) {
        return true;
    }
}
```

在这个例子中，`passwordEncoder.matches()` 方法用于比较原始密码和存储的哈希密码。

### 4. 自动配置

Spring Boot 自动配置机制会自动搜索所有已声明的 `PasswordEncoder` Beans，并选择其中一个作为默认的密码编码器。如果你只有一个 `PasswordEncoder` Bean，它将自动成为默认值。如果有多个，你可以通过 `@Primary` 注解指定哪个应该优先使用，或者手动配置 `AuthenticationManagerBuilder` 使用特定的 `PasswordEncoder`。

### 总结

- 在 Spring Boot 中设置密码加密器主要涉及定义一个 `PasswordEncoder` 类型的 Bean。
- 可以根据需求选择不同的加密算法，如 BCrypt、Pbkdf2、SCrypt 等。
- 在服务层或认证提供者中使用 `PasswordEncoder` 来加密新用户的密码或验证登录尝试中的密码。
- 利用 Spring Boot 的自动配置特性简化集成过程。





> **参考资料：**
- 中文文档：https://springdoc.cn/spring-security/

- springSecurity使用教程：https://www.cnblogs.com/xxctx/p/18441536

- Jwt集成：https://springdoc.cn/spring-boot-spring-security-jwt-mysql/