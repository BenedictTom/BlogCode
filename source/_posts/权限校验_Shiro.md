---
title: 权限校验_Shiro
main_color: "#5b144dff"
categories: 权限校验
tags:
  - 权限校验
cover: https://free.picui.cn/free/2026/03/28/69c74d6c4a422.png
---


## SecurityManager

在 Apache Shiro 中，`SecurityManager` 是整个安全框架的核心组件，它负责管理所有的安全相关的操作。下面将介绍 `SecurityManager` 的继承结构，并列举一些常用的实现类及其应用场景。

### SecurityManager 继承结构

1. **SecurityManager 接口**：
   - 这是 Shiro 安全管理器的顶级接口，定义了安全管理的基本方法。它涵盖了认证、授权、会话管理和加密等核心功能。
   
2. **Authenticator 接口**：
   - 专门用于处理用户认证的接口。默认实现为 `ModularRealmAuthenticator`。
   
3. **Authorizer 接口**：
   - 负责权限控制（授权）的接口。默认实现为 `ModularRealmAuthorizer`。
   
4. **SessionManager 接口**：
   - 管理会话生命周期的接口。Shiro 提供了 `DefaultWebSessionManager` 和 `DefaultSessionManager` 分别用于 Web 应用和非 Web 应用。
   
5. **CacheManager 接口**：
   - 缓存管理器接口，用于缓存认证信息和授权信息以提高性能。常见的实现有 `EhCacheManager`。
   
6. **RememberMeManager 接口**：
   - 记住我功能的管理接口，允许用户在关闭浏览器后仍然保持登录状态。

7. **DefaultSecurityManager 类**：
   - 这是 `SecurityManager` 的一个通用实现，适用于大多数场景，提供了对上述各个组件的支持。

8. **DefaultWebSecurityManager 类**：
   - 特别针对 Web 应用优化的 `SecurityManager` 实现，集成了更多的 Web 相关特性，如过滤器链等。

### 常用实现类及应用场景

- **DefaultSecurityManager**：
  - **用途**：作为最基本的 `SecurityManager` 实现，适合于各种类型的应用程序，无论是桌面应用还是简单的命令行工具。
  - **特点**：灵活性高，可以自定义 Authenticator, Authorizer, SessionManager 等组件。
  - **场景**：当你需要完全控制每一个安全方面的细节时使用。

- **DefaultWebSecurityManager**：
  - **用途**：专为 Web 应用设计的安全管理器，内置了许多与 HTTP 请求/响应相关的功能。
  - **特点**：支持基于 URL 的访问控制，集成 Shiro 的 Filter 链来保护 Web 资源。
  - **场景**：任何基于 Web 技术栈构建的应用程序，包括但不限于 Spring Boot Web 应用、传统的 Servlet 应用等。

- **IniSecurityManagerFactory**：
  - **用途**：从 INI 文件中加载配置创建 `SecurityManager` 实例。
  - **特点**：便于快速设置和测试，但不适合生产环境。
  - **场景**：开发阶段或小型项目中用于简化配置过程。

- **JdbcRealm / JndiJdbcRealm**：
  - **用途**：实现了 Realm 接口，通过 JDBC 连接到数据库进行身份验证和授权。
  - **特点**：直接与关系型数据库交互，支持标准 SQL 查询。
  - **场景**：当你的用户数据存储在关系型数据库中时使用。

- **Custom Realm**：
  - **用途**：根据具体需求定制 Realm 实现。
  - **特点**：高度可定制化，可以根据不同的业务逻辑调整认证和授权策略。
  - **场景**：对于有特殊安全需求的企业级应用来说非常有用。



## SessionManager

### SessionManager 继承结构及常用实现

在 Apache Shiro 中，`SessionManager` 负责管理会话的生命周期。它定义了如何创建、访问和销毁会话的基本操作。Shiro 提供了灵活的 `SessionManager` 接口以及多个具体的实现类来满足不同的应用场景需求。

#### SessionManager 继承结构

1. **SessionManager 接口**：
   - 定义了管理会话的基本方法，如创建、检索、删除会话等。
   
2. **DefaultSessionManager 类**：
   - 实现了 `SessionManager` 接口，提供了默认的会话管理功能，适用于非 Web 应用程序。
   
3. **DefaultWebSessionManager 类**：
   - 继承自 `DefaultSessionManager`，特别为 Web 应用优化，支持基于 HTTP 的会话管理。
   
4. **ServletContainerSessionManager 类**：
   - 一个简单的 Web 会话管理器，它直接使用 Servlet 容器（如 Tomcat）的会话机制而不是 Shiro 自己的会话管理机制。

#### 常用实现类及场景

- **DefaultSessionManager**：
  - **用途**：用于非 Web 环境下的会话管理。
  - **特点**：提供了一个基本的内存中的会话存储，也可以配置为持久化到数据库或其他存储介质中。
  - **场景**：适合桌面应用或命令行工具等不需要 HTTP 会话管理的应用场景。
  
- **DefaultWebSessionManager**：
  - **用途**：针对 Web 应用设计的会话管理器，可以与 Shiro 的过滤器链一起工作以保护 Web 资源。
  - **特点**：提供了对 Cookie 和 URL 重写的内置支持，并且允许你定制会话超时时间等参数。
  - **场景**：适用于任何需要管理用户会话的 Web 应用程序，例如 Spring Boot Web 应用。
  
- **ServletContainerSessionManager**：
  - **用途**：利用 Servlet 容器提供的原生会话管理功能。
  - **特点**：非常轻量级，不包含 Shiro 特定的功能，因此无法享受 Shiro 提供的高级特性如分布式会话。
  - **场景**：当你希望尽可能减少对现有应用架构的影响，或者已经有一个成熟的会话管理方案时使用。

#### 常用 API

以下是一些常用的 `SessionManager` 相关 API：

- **createSession()**：
  - 创建一个新的会话实例。
  
- **getSession(SessionKey key)**：
  - 根据给定的 `SessionKey` 获取现有的会话实例。
  
- **getSessionDAO() / setSessionDAO(SessionDAO sessionDAO)**：
  - 获取/设置当前使用的 `SessionDAO` 实例，用于持久化会话数据。
  
- **getGlobalSessionTimeout() / setGlobalSessionTimeout(long globalSessionTimeout)**：
  - 获取/设置全局会话超时时间（毫秒），适用于所有新创建的会话。
  
- **validateSessions()**：
  - 验证所有的活动会话是否已过期，并清理过期会话。

这些 API 可以帮助开发者有效地管理和维护用户的会话状态，确保安全性和用户体验的一致性。



## SimpleCookie

在 Apache Shiro 中，`SimpleCookie` 是一个用于处理 HTTP Cookie 的简单实现。它提供了对 Cookie 的创建、设置和读取等功能，并且可以很容易地集成到 Shiro 的安全框架中，特别是与 `SessionManager` 和 `RememberMeManager` 一起使用。

### SimpleCookie 的主要作用

1. **会话管理**：Shiro 使用 `SimpleCookie` 来存储会话 ID（sessionId），这样即使用户关闭浏览器后重新打开，仍然可以通过 Cookie 恢复之前的会话状态。
   
2. **记住我功能（Remember Me）**：通过 `RememberMeManager`，Shiro 可以利用 `SimpleCookie` 存储用户的登录状态。即使用户的会话过期或关闭了浏览器，只要 Cookie 未过期，下次访问时就可以自动登录。

3. **自定义 Cookie 属性**：开发者可以通过 `SimpleCookie` 设置各种属性，如 cookie 的名称、值、路径、域名、有效期等，从而更好地控制 Cookie 的行为。

### SimpleCookie 常用方法

- **setName(String name)** 和 **getName()**：
  - 设置或获取 Cookie 的名称。
  
- **setValue(String value)** 和 **getValue()**：
  - 设置或获取 Cookie 的值。
  
- **setMaxAge(int maxAge)** 和 **getMaxAge()**：
  - 设置或获取 Cookie 的最大存活时间（秒）。如果设置为负数，则表示 Cookie 只在当前浏览器会话期间有效；如果设置为0，则表示立即删除该 Cookie。
  
- **setPath(String path)** 和 **getPath()**：
  - 设置或获取 Cookie 的路径。只有当请求的 URL 路径与 Cookie 的路径匹配时，浏览器才会发送该 Cookie。
  
- **setDomain(String domain)** 和 **getDomain()**：
  - 设置或获取 Cookie 的域。允许跨子域共享 Cookie。
  
- **setHttpOnly(boolean httpOnly)** 和 **isHttpOnly()**：
  - 设置或判断 Cookie 是否只能通过 HTTP(S) 请求访问，防止 JavaScript 访问，有助于防范 XSS 攻击。
  
- **setSecure(boolean secure)** 和 **isSecure()**：
  - 设置或判断是否仅通过 HTTPS 发送 Cookie，提高安全性。

### 示例代码

以下是一个简单的例子，展示了如何使用 `SimpleCookie` 配置 Shiro 的记住我功能：

```java
import org.apache.shiro.web.servlet.SimpleCookie;
import org.apache.shiro.web.mgt.CookieRememberMeManager;

// 创建一个名为 "rememberMe" 的 SimpleCookie 实例
SimpleCookie rememberMeCookie = new SimpleCookie("rememberMe");
// 设置 Cookie 的最大存活时间为7天
rememberMeCookie.setMaxAge(7 * 24 * 60 * 60); // 7 days in seconds

// 创建 RememberMeManager 并设置上面创建的 Cookie
CookieRememberMeManager rememberMeManager = new CookieRememberMeManager();
rememberMeManager.setCookie(rememberMeCookie);

// 将 RememberMeManager 配置到 SecurityManager 中
securityManager.setRememberMeManager(rememberMeManager);
```

在这个示例中，我们创建了一个名为 `"rememberMe"` 的 Cookie，并设置了它的最大存活时间为7天。然后，我们将这个 Cookie 应用到了 `CookieRememberMeManager` 中，最终将 `RememberMeManager` 配置给 Shiro 的 `SecurityManager`，实现了“记住我”功能。



## AuthenticationInfo

在 Apache Shiro 中，`AuthenticationInfo` 是一个接口，用于封装从数据源（如数据库、LDAP 等）获取的认证信息。它主要用于验证用户的身份信息是否正确。下面将详细介绍 `AuthenticationInfo` 的继承结构、常用的实现类及其应用场景和常用 API。

### AuthenticationInfo 继承结构

1. **AuthenticationInfo 接口**：
   - 定义了认证信息的基本结构，包括主体（Principal）和凭证（Credentials）。它是所有认证信息对象的顶层接口。
   
2. **SimpleAuthenticationInfo 类**：
   - 实现了 `AuthenticationInfo` 接口，提供了一个简单的认证信息实现。通常用于存储用户名/密码对或类似的简单认证信息。
   
3. **Account 类**（已废弃）：
   - 早期版本中存在，现在已被弃用，不再推荐使用。
   
4. **Realm 类**：
   - 尽管不是直接继承自 `AuthenticationInfo`，但每个 Realm 都需要返回一个实现了 `AuthenticationInfo` 接口的对象作为认证结果的一部分。

### 常用实现类及场景

- **SimpleAuthenticationInfo**：
  - **用途**：这是一个非常基础且通用的 `AuthenticationInfo` 实现，适用于大多数场景。
  - **特点**：可以包含一个或多个主体（Principals），以及一个凭证（Credentials）。此外，还可以附加一些其他信息，比如角色或权限等。
  - **场景**：几乎所有的应用程序都可以使用 `SimpleAuthenticationInfo` 来表示认证信息，特别是那些只需要用户名和密码进行身份验证的应用。
  - **示例代码**：
    ```java
    import org.apache.shiro.authc.SimpleAuthenticationInfo;
    import org.apache.shiro.crypto.hash.SimpleHash;

    // 创建一个 SimpleAuthenticationInfo 实例
    Object principal = "username"; // 主体
    Object hashedCredentials = new SimpleHash("SHA-256", "password", "salt", 1024).toHex(); // 凭证
    String realmName = "myRealm"; // Realm 名称

    SimpleAuthenticationInfo info = new SimpleAuthenticationInfo(principal, hashedCredentials, realmName);
    ```

### 常用 API

尽管 `SimpleAuthenticationInfo` 提供了许多有用的方法，这里列出几个最常用的：

- **getPrincipals()**：
  - 获取主体集合。主体通常是用户的唯一标识符，例如用户名。
  
- **getCredentials()**：
  - 获取凭证。这通常是用户的密码或其哈希值。
  
- **getCredentialsSalt()**：
  - 如果在创建 `SimpleAuthenticationInfo` 对象时提供了盐值，则可以通过此方法获取。
  
- **setPrincipals(PrincipalCollection principals)** 和 **setCredentials(Object credentials)**：
  - 设置主体和凭证，通常在创建实例后不需要调用这些方法，因为可以在构造函数中直接指定。

### 场景应用

1. **基本认证流程**：
   - 在大多数情况下，`SimpleAuthenticationInfo` 被用来封装用户提供的用户名和密码，并与存储在数据库或其他安全存储中的哈希密码进行比较。
   
2. **集成第三方认证服务**：
   - 当与 LDAP、OAuth 或 SAML 等第三方认证服务集成时，也可以使用 `SimpleAuthenticationInfo` 来封装从这些服务获得的认证信息。
   
3. **自定义 Realm**：
   - 开发者可以根据自己的需求创建自定义的 `Realm`，并在其中使用 `SimpleAuthenticationInfo` 来封装认证信息。例如，在企业级应用中，可能需要根据复杂的业务逻辑来决定如何认证用户。

通过理解和正确使用 `SimpleAuthenticationInfo`，开发者能够有效地处理用户的身份验证过程，确保应用程序的安全性和可靠性。对于更复杂的需求，Shiro 还允许你实现自己的 `AuthenticationInfo` 来满足特定的业务要求。


## CredentialsMatcher

### CredentialsMatcher 继承结构及常用实现

在 Apache Shiro 中，`CredentialsMatcher` 是一个用于验证提交的凭证（如密码）是否与存储的凭证相匹配的重要接口。它允许开发者自定义凭证匹配逻辑，以适应不同的安全需求。

#### CredentialsMatcher 继承结构

1. **CredentialsMatcher 接口**：
   - 定义了 `doCredentialsMatch(AuthenticationToken token, AuthenticationInfo info)` 方法，该方法用于比较用户提供的凭证（通常是从登录表单获取的）和系统中存储的凭证（通常是加密后的密码）是否匹配。
   
2. **SimpleCredentialsMatcher 类**：
   - 直接实现了 `CredentialsMatcher` 接口，提供了一个简单的基于等值比较的凭证匹配器。适用于明文密码或者直接可比较的凭证类型。
   
3. **HashedCredentialsMatcher 类**：
   - 继承自 `SimpleCredentialsMatcher`，专门用于处理哈希过的凭证（例如 SHA-256、MD5 等）。它支持对盐值的支持，并且可以指定哈希算法以及迭代次数。
   
4. **Custom CredentialsMatcher 实现**：
   - 开发者可以根据具体的安全要求实现自己的 `CredentialsMatcher`，比如集成第三方认证服务或使用更复杂的加密算法。

#### 常用实现类及场景

- **SimpleCredentialsMatcher**：
  - **用途**：简单地比较两个凭证是否相同。如果凭证是明文字符串或可以直接比较的数据，则适合使用此匹配器。
  - **特点**：不支持哈希或加密的凭证，仅适用于非常基础的应用场景。
  - **场景**：不适合生产环境中的应用，因为安全性较低，容易受到攻击。
  
- **HashedCredentialsMatcher**：
  - **用途**：专为处理经过哈希算法处理的凭证而设计，支持多种哈希算法（如 SHA-256、MD5 等），并且支持加盐以增加安全性。
  - **特点**：可以通过设置哈希算法名称、盐值位置、哈希迭代次数等参数来增强安全性。
  - **场景**：广泛应用于需要较高安全性的Web应用中，特别是那些涉及敏感信息保护的情况。
  - **示例代码**：
    ```java
    HashedCredentialsMatcher matcher = new HashedCredentialsMatcher();
    matcher.setHashAlgorithmName("SHA-256"); // 设置哈希算法
    matcher.setHashIterations(1024); // 设置哈希迭代次数
    ```

#### 常用 API

对于 `HashedCredentialsMatcher`，这里有一些常用的配置选项：

- **setHashAlgorithmName(String algorithmName)**：
  - 设置哈希算法名称（如 "SHA-256", "MD5"）。
  
- **setHashIterations(int iterations)**：
  - 设置哈希算法的迭代次数，增加这个值可以提高安全性但会增加计算时间。
  
- **setStoredCredentialsHexEncoded(boolean hexEncoded)**：
  - 设置是否将存储的凭证编码为十六进制字符串，默认为 true。
  
- **setSaltStyle(SaltStyle style)**：
  - 设置盐值样式，有 NONE、PREFIX、SUFFIX 可选，决定如何处理盐值。

此外，`doCredentialsMatch` 方法是核心方法，用来实际执行凭证匹配：

```java
@Override
public boolean doCredentialsMatch(AuthenticationToken token, AuthenticationInfo info) {
    Object tokenCredentials = getCredentials(token);
    Object accountCredentials = getCredentials(info);
    return equals(tokenCredentials, accountCredentials);
}
```

在这个方法中，Shiro 会调用具体的 `CredentialsMatcher` 来判断提交的凭证是否与存储的凭证相匹配。

### 总结

选择合适的 `CredentialsMatcher` 对于确保应用程序的安全至关重要。对于大多数现代 Web 应用来说，推荐使用 `HashedCredentialsMatcher`，因为它提供了更好的安全性，特别是在处理用户密码时。通过合理配置哈希算法、盐值和迭代次数，可以有效地防止诸如彩虹表攻击等常见的密码破解技术。如果你的应用有特殊的安全需求，也可以考虑实现自定义的 `CredentialsMatcher`。




## Permission

在 Apache Shiro 中，`Permission` 是一个核心概念，用于表示用户可以执行的操作或访问的资源。权限（Permissions）是细粒度的安全控制机制，允许你精确地定义哪些用户或角色能够对特定资源执行何种操作。

#### Permission 接口

`Permission` 接口定义了如何检查某个身份是否被授权执行某一操作。Shiro 提供了几种不同的 `Permission` 实现，它们各自适用于不同场景。

### 常用的 Permission 实现类及其应用场景

1. **WildcardPermission**：
   - **用途**：这是 Shiro 默认的权限实现，支持通过通配符来定义复杂的权限规则。
   - **特点**：灵活且强大，可以通过点分隔的字符串定义层次化的权限结构，并使用通配符进行匹配。
   - **格式**：`domain:action:instance`，例如 `"user:create:*"` 表示可以在任何实例上创建用户。
   - **示例**：
     ```java
     Subject currentUser = SecurityUtils.getSubject();
     if (currentUser.isPermitted("user:update")) {
         // 执行更新用户的逻辑
     }
     ```
   - **场景**：适用于大多数需要细粒度权限控制的应用场景，尤其是当你的应用有复杂权限需求时。

2. **BitPermission**（较少使用）：
   - **用途**：基于位运算的权限实现，主要用于需要高效处理大量权限的情况。
   - **特点**：通过位掩码来表示权限，虽然效率高但不够直观，通常只在特殊情况下使用。
   - **场景**：对于性能要求极高且权限体系相对简单的场景可能有用，但在现代应用中不常见。

3. **Custom Permission Implementations**：
   - **用途**：根据具体业务需求自定义权限实现。
   - **特点**：灵活性强，可以根据实际需求设计权限模型。
   - **场景**：当你需要实现特定领域的权限模型时，如基于图的权限管理、基于时间窗口的权限等。

### 常用 API

- **isPermitted(String permission)**：
  - 检查当前用户是否有指定权限。
  
- **isPermittedAll(String... permissions)**：
  - 检查当前用户是否拥有所有列出的权限。
  
- **checkPermission(String permission)**：
  - 如果当前用户没有指定权限，则抛出 `AuthorizationException` 异常。
  
- **hasRole(String roleIdentifier)** 和 **hasAllRoles(Collection<String> roleIdentifiers)**：
  - 虽然不是直接与 `Permission` 相关，但在实际开发中经常配合使用，用于检查用户的角色信息。

### 示例代码

下面是一个使用 `WildcardPermission` 的简单例子：

```java
import org.apache.shiro.SecurityUtils;
import org.apache.shiro.subject.Subject;

public class PermissionExample {

    public static void main(String[] args) {
        // 获取当前登录的用户
        Subject currentUser = SecurityUtils.getSubject();

        // 检查用户是否具有指定权限
        if (currentUser.isPermitted("user:read:12345")) {
            System.out.println("You are permitted to read user with ID 12345.");
        } else {
            System.out.println("You do not have permission to read user with ID 12345.");
        }

        // 或者使用更通用的权限检查
        if (currentUser.isPermitted("user:*")) {
            System.out.println("You have general permissions over users.");
        }

        // 强制性权限检查
        currentUser.checkPermission("user:delete:67890");
        System.out.println("User is allowed to delete user with ID 67890.");
    }
}
```

### 场景应用

1. **资源级权限控制**：
   - 在 Web 应用中，可以为每个页面、按钮甚至是 AJAX 请求设置权限，确保只有授权用户才能访问或操作。
   
2. **模块化权限管理**：
   - 对于大型企业级应用，权限往往按照模块划分，比如财务模块、人力资源模块等。使用 `WildcardPermission` 可以方便地定义和管理这些模块的权限。
   
3. **动态权限分配**：
   - 在某些场景下，权限不是固定的，而是根据用户行为或环境变化而改变。例如，在线教育平台中，讲师可能只能对自己教授的课程拥有编辑权限，这时可以通过动态生成权限字符串来实现这种灵活的权限控制。





## SecurityUtils

`SecurityUtils` 是 Apache Shiro 框架中的一个实用工具类，它提供了静态方法来获取当前执行上下文的安全相关信息，如当前用户（即 `Subject`），以及与安全管理器（`SecurityManager`）相关的操作。它是连接应用程序代码和 Shiro 安全机制的桥梁。

### SecurityUtils 的主要功能

1. **获取当前用户（Subject）**：
   - 通过 `SecurityUtils.getSubject()` 方法可以获取当前执行线程的 `Subject` 对象。`Subject` 表示当前用户或正在执行的代码的身份和权限。
   
2. **设置和获取 `SecurityManager`**：
   - `setSecurityManager(SecurityManager securityManager)`：设置全局的 `SecurityManager` 实例。
   - `getSecurityManager()`：返回当前应用中配置的 `SecurityManager`。

3. **创建无会话的匿名 Subject**：
   - `createSubject(SubjectContext context)`：根据给定的 `SubjectContext` 创建一个新的 `Subject` 实例，这在测试或者需要临时创建非活跃的 `Subject` 实例时非常有用。

### 常用方法介绍

#### 获取当前用户（Subject）

```java
Subject currentUser = SecurityUtils.getSubject();
```

- 这是使用最频繁的方法之一，用于获取当前执行环境下的 `Subject`。你可以利用这个 `Subject` 对象来进行认证、授权等操作。

#### 设置和获取 `SecurityManager`

```java
// 设置 SecurityManager
SecurityUtils.setSecurityManager(securityManager);

// 获取 SecurityManager
SecurityManager securityManager = SecurityUtils.getSecurityManager();
```

- 在初始化 Shiro 环境时，通常需要先设置一个 `SecurityManager` 实例，之后可以通过 `getSecurityManager()` 方法在整个应用程序中访问它。

#### 其他常用操作

- **检查是否已认证**：

    ```java
    if (currentUser.isAuthenticated()) {
        // 用户已登录
    }
    ```

- **登录/登出**：

    ```java
    // 登录
    UsernamePasswordToken token = new UsernamePasswordToken(username, password);
    currentUser.login(token);

    // 登出
    currentUser.logout();
    ```

- **权限检查**：

    ```java
    if (currentUser.isPermitted("user:delete:12345")) {
        // 执行删除用户的逻辑
    }
    ```

### 使用场景

- **身份验证**：通过 `SecurityUtils.getSubject()` 获取 `Subject` 后，可以进行用户的身份验证操作。
  
- **权限控制**：在服务层或控制器层检查当前用户是否有执行某些操作的权限。
  
- **会话管理**：管理用户的会话信息，例如获取会话属性、注销会话等。
  
- **跨模块安全集成**：在不同的模块之间共享安全上下文，确保一致的安全策略。

### 示例代码

下面是一个简单的例子，展示了如何使用 `SecurityUtils` 来实现用户登录和权限检查：

```java
import org.apache.shiro.SecurityUtils;
import org.apache.shiro.authc.UsernamePasswordToken;
import org.apache.shiro.subject.Subject;

public class ShiroExample {

    public static void main(String[] args) {
        // 获取当前用户
        Subject currentUser = SecurityUtils.getSubject();

        // 创建用户名密码令牌
        UsernamePasswordToken token = new UsernamePasswordToken("username", "password");

        try {
            // 登录
            currentUser.login(token);
            System.out.println("User [" + currentUser.getPrincipal() + "] logged in successfully.");

            // 权限检查
            if (currentUser.isPermitted("user:read")) {
                System.out.println("Has permission to read user data.");
            } else {
                System.out.println("Does not have permission to read user data.");
            }

            // 登出
            currentUser.logout();
            System.out.println("User logged out successfully.");
        } catch (Exception e) {
            System.out.println("Login failed: " + e.getMessage());
        }
    }
}
```



## ShiroFilterFactoryBean

`ShiroFilterFactoryBean` 是 Apache Shiro 与 Spring 集成时的一个核心组件，它用于创建和配置 `ShiroFilter` 实例。`ShiroFilter` 是 Shiro 框架中的一个 Servlet 过滤器，负责拦截所有进入应用的请求，并根据配置的安全规则决定是否允许这些请求继续执行。

### 主要功能

1. **安全管理**：通过 `SecurityManager` 对象来管理安全相关的操作，包括认证、授权等。
2. **过滤器链定义**：允许你为不同的 URL 定义不同的过滤器链，从而实现细粒度的访问控制。
3. **自定义过滤器**：支持添加自定义的过滤器，以满足特定的安全需求。
4. **未授权/未登录处理**：可以设置当用户尝试访问无权限资源或未登录时跳转到的页面。

### 核心属性

- **securityManager**：设置 `SecurityManager` 实例，这是 Shiro 的核心组件，负责所有的安全操作。
- **filters**：注册自定义过滤器，键值对形式，键为过滤器名称，值为具体的过滤器实例。
- **filterChainDefinitionMap**：定义 URL 和对应的过滤器链，通常是一个 Map 结构，键为 URL 模式，值为相应的过滤器链（如 "authc" 表示需要登录验证)。
- **loginUrl**：指定登录页面的 URL，如果用户未登录且试图访问受保护的资源时将被重定向到这里。
- **successUrl**：成功登录后的默认跳转地址。
- **unauthorizedUrl**：未经授权的访问将被重定向至此URL。

### 示例代码

下面是一个简单的 `ShiroFilterFactoryBean` 配置示例：

```java
import org.apache.shiro.spring.web.ShiroFilterFactoryBean;
import org.apache.shiro.mgt.SecurityManager;
import org.apache.shiro.web.filter.authc.AnonymousFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.HashMap;
import java.util.Map;

@Configuration
public class ShiroConfig {

    @Bean("shiroFilter")
    public ShiroFilterFactoryBean shiroFilterFactoryBean(SecurityManager securityManager) {
        ShiroFilterFactoryBean shiroFilterFactoryBean = new ShiroFilterFactoryBean();
        
        // 设置 SecurityManager
        shiroFilterFactoryBean.setSecurityManager(securityManager);
        
        // 注册自定义过滤器
        Map<String, Filter> filters = new HashMap<>();
        filters.put("anon", new AnonymousFilter());
        shiroFilterFactoryBean.setFilters(filters);
        
        // 配置过滤链定义
        Map<String, String> filterChainDefinitionMap = new LinkedHashMap<>();
        filterChainDefinitionMap.put("/public/**", "anon"); // 公共资源，无需认证
        filterChainDefinitionMap.put("/admin/**", "roles[admin]"); // 管理员角色可访问
        filterChainDefinitionMap.put("/**", "authc"); // 所有其他路径都需要认证
        
        shiroFilterFactoryBean.setFilterChainDefinitionMap(filterChainDefinitionMap);
        
        // 设置登录页面
        shiroFilterFactoryBean.setLoginUrl("/login");
        
        // 设置未授权页面
        shiroFilterFactoryBean.setUnauthorizedUrl("/unauthorized");

        return shiroFilterFactoryBean;
    }
}
```

### 关键点解释

- **过滤链定义 (`filterChainDefinitionMap`)**：
  - `/public/**`: 匹配所有以 `/public/` 开头的路径，使用 `anon` 过滤器表示匿名访问，即不需要任何认证即可访问。
  - `/admin/**`: 只有拥有 `admin` 角色的用户才能访问以 `/admin/` 开头的所有路径。
  - `/**`: 所有其他路径都需要经过 `authc` 过滤器进行认证。

- **`setLoginUrl` 和 `setUnauthorizedUrl`**：
  - 当用户尝试访问需要认证但尚未登录的资源时，会被重定向到设置的登录页面。
  - 当用户尝试访问没有权限的资源时，会被重定向到未授权页面。

### 使用场景

- **Web 应用的安全控制**：通过 `ShiroFilterFactoryBean` 可以为你的 Web 应用添加强大的安全控制机制，确保只有经过认证并具有适当权限的用户才能访问特定资源。
- **REST API 安全性**：除了传统的 Web 页面外，也可以用来保护 RESTful API 接口，确保只有合法的客户端能够调用这些接口。



## `ShiroFilterChainDefinition` 

Apache Shiro 中用于定义过滤器链（Filter Chain）的一个接口。它允许开发者以一种结构化的方式为不同的 URL 模式指定相应的过滤器链，从而实现细粒度的安全控制。在 Spring Boot 环境下，通过实现 `ShiroFilterChainDefinition` 接口，可以灵活地配置哪些 URL 需要进行认证、授权等安全检查。

### 主要功能

- **URL 模式与过滤器的映射**：允许你为不同的 URL 模式指定一个或多个过滤器，这样当请求匹配某个 URL 模式时，对应的过滤器链就会被应用。
- **支持多种内置过滤器**：如 `authc`（需要登录）、`roles`（角色检查）、`perms`（权限检查）、`anon`（匿名访问，无需认证）等。
- **自定义过滤器**：除了使用 Shiro 提供的内置过滤器外，还可以注册和使用自定义的过滤器。

### 为什么使用 ShiroFilterChainDefinition？

在传统的 Shiro 配置中，我们通常会直接在 `ShiroFilterFactoryBean` 中通过 `setFilterChainDefinitionMap()` 方法来设置过滤器链。然而，使用 `ShiroFilterChainDefinition` 可以提供更加灵活和模块化的配置方式，特别是在 Spring Boot 环境下，它可以让你更好地组织和管理你的过滤器链配置。

### 实现示例

下面是一个简单的示例，展示了如何在 Spring Boot 应用中实现 `ShiroFilterChainDefinition` 来配置过滤器链：

```java
import org.apache.shiro.spring.web.ShiroFilterChainDefinition;
import org.apache.shiro.web.filter.mgt.DefaultFilterChainManager;
import org.apache.shiro.web.filter.mgt.PathMatchingFilterChainResolver;
import org.apache.shiro.web.servlet.AbstractShiroFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.LinkedHashMap;
import java.util.Map;

@Configuration
public class ShiroConfig {

    @Bean
    public ShiroFilterChainDefinition shiroFilterChainDefinition() {
        DefaultFilterChainDefinition chainDefinition = new DefaultFilterChainDefinition();

        // 定义过滤器链
        Map<String, String> filterChainMap = new LinkedHashMap<>();
        
        // 允许匿名访问的资源
        filterChainMap.put("/public/**", "anon");
        
        // 需要管理员角色才能访问的资源
        filterChainMap.put("/admin/**", "roles[admin]");
        
        // 所有其他路径都需要认证
        filterChainMap.put("/**", "authc");

        chainDefinition.addPathDefinitions(filterChainMap);
        return chainDefinition;
    }

    // 如果你需要进一步定制Shiro Filter的行为，可能还需要配置ShiroFilterFactoryBean
    /*
    @Bean(name = "shiroFilter")
    public ShiroFilterFactoryBean shiroFilterFactoryBean(SecurityManager securityManager) throws Exception {
        ShiroFilterFactoryBean shiroFilterFactoryBean = new ShiroFilterFactoryBean();
        shiroFilterFactoryBean.setSecurityManager(securityManager);

        // 获取之前定义的过滤器链
        Map<String, String> filterChainDefinitionMap = shiroFilterChainDefinition().getFilterChainMap();
        shiroFilterFactoryBean.setFilterChainDefinitionMap(filterChainDefinitionMap);

        return shiroFilterFactoryBean;
    }
    */
}
```

在这个例子中，我们创建了一个 `DefaultFilterChainDefinition` 的实例，并为其添加了几个过滤器链规则：

1. `/public/**`：允许匿名访问，即不需要任何认证即可访问这些资源。
2. `/admin/**`：只有拥有 `admin` 角色的用户才能访问这些资源。
3. `/**`：所有其他路径都需要经过认证 (`authc`)。

### 关键点解释

- **LinkedHashMap**：这里使用 `LinkedHashMap` 而不是普通的 `HashMap`，因为过滤器链定义是有顺序的，`LinkedHashMap` 可以保证插入顺序，从而确保优先级较高的规则先被匹配。
- **filterChainMap.put()**：第一个参数是 URL 模式，第二个参数是过滤器链字符串，可以包含多个过滤器名称，中间用逗号分隔。
- **addPathDefinitions()**：将 URL 模式和对应的过滤器链添加到 `ShiroFilterChainDefinition` 中。

### 总结

`ShiroFilterChainDefinition` 提供了一种灵活且易于维护的方式来配置 Shiro 的过滤器链。通过这种方式，你可以轻松地为应用程序的不同部分设置适当的安全策略，无论是保护 REST API 还是 Web 页面。这种配置方法特别适合于 Spring Boot 应用程序，因为它能够很好地与其他 Spring 组件集成，使得整个安全配置过程更加简洁明了。


## 必须配置ShiroFilterFactoryBean？

在 Spring Boot 项目中集成 Apache Shiro 时，是否需要配置 `ShiroFilterFactoryBean` 取决于你选择的集成方式。简单来说：

- **如果你使用 Shiro 提供的 Starter（如 `shiro-spring-boot-web-starter`），那么大部分的基础配置会被自动处理**，包括创建和配置 `ShiroFilterFactoryBean`。在这种情况下，你可能不需要手动配置 `ShiroFilterFactoryBean`，除非你需要进行一些自定义设置。
  
- **如果选择手动集成 Shiro 到你的 Spring Boot 应用程序中**，则需要你自己创建并配置 `ShiroFilterFactoryBean`，以便能够正确地设置过滤器链、安全管理器等关键组件。

### 使用 Shiro Starter 的情况

当你通过添加依赖 `shiro-spring-boot-web-starter` 来集成 Shiro 时，许多默认配置已经被预先设置好。例如，`SecurityManager` 和基本的 `ShiroFilterFactoryBean` 配置可能会被自动加载。你可以通过简单的配置文件（如 `application.yml` 或 `application.properties`）来调整一些基础设置。但是，对于更复杂的需求或自定义逻辑，仍然可能需要提供额外的配置类来覆盖默认行为。

### 手动配置的情况

在手动配置 Shiro 的情况下，你需要明确地定义 `ShiroFilterFactoryBean` 并为其设置必要的属性，比如 `SecurityManager`、过滤器链定义（filter chain definitions）、登录页面 URL 等。这是因为你需要完全控制如何初始化 Shiro 的核心组件以及它们之间的交互方式。

### 示例：手动配置 `ShiroFilterFactoryBean`

下面是一个手动配置 `ShiroFilterFactoryBean` 的简化示例：

```java
import org.apache.shiro.spring.web.ShiroFilterFactoryBean;
import org.apache.shiro.mgt.SecurityManager;
import org.apache.shiro.web.filter.authc.AnonymousFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.HashMap;
import java.util.Map;

@Configuration
public class ShiroConfig {

    @Bean("shiroFilter")
    public ShiroFilterFactoryBean shiroFilterFactoryBean(SecurityManager securityManager) {
        ShiroFilterFactoryBean shiroFilterFactoryBean = new ShiroFilterFactoryBean();
        
        // 设置 SecurityManager
        shiroFilterFactoryBean.setSecurityManager(securityManager);
        
        // 注册自定义过滤器
        Map<String, Filter> filters = new HashMap<>();
        filters.put("anon", new AnonymousFilter());
        shiroFilterFactoryBean.setFilters(filters);
        
        // 配置过滤器链定义
        Map<String, String> filterChainDefinitionMap = new LinkedHashMap<>();
        filterChainDefinitionMap.put("/public/**", "anon"); // 公共资源，无需认证
        filterChainDefinitionMap.put("/admin/**", "roles[admin]"); // 管理员角色可访问
        filterChainDefinitionMap.put("/**", "authc"); // 所有其他路径都需要认证
        
        shiroFilterFactoryBean.setFilterChainDefinitionMap(filterChainDefinitionMap);
        
        // 设置登录页面
        shiroFilterFactoryBean.setLoginUrl("/login");
        
        // 设置未授权页面
        shiroFilterFactoryBean.setUnauthorizedUrl("/unauthorized");

        return shiroFilterFactoryBean;
    }
}
```

### 结论

- **对于大多数标准需求**，使用 Shiro 的 Starter 包通常就足够了，它提供了足够的灵活性和简便性来满足常见的安全需求，而无需手动配置 `ShiroFilterFactoryBean`。
  
- **当你的项目有特殊的安全需求**，如复杂的权限模型、特定的过滤器逻辑或是对现有流程的高度定制化要求时，则可能需要手动配置 `ShiroFilterFactoryBean` 以实现这些高级功能。

因此，是否需要配置 `ShiroFilterFactoryBean` 主要取决于项目的具体需求以及你所选择的集成方法。



在使用 Apache Shiro 与 Spring Boot 集成时，有两种常见的方法：一种是通过使用 Shiro 提供的 Starter（`shiro-spring-boot-web-starter`），另一种是手动配置 Shiro 的各个组件。这两种方式的主要区别在于配置的自动化程度和灵活性。

### 使用 Shiro Starter (shiro-spring-boot-web-starter)

Shiro 提供了一个专门针对 Spring Boot 的 starter，它简化了 Shiro 的集成过程，使得开发者可以更快地开始使用 Shiro 的功能而不需要过多的手动配置。

#### 步骤：

1. **添加依赖**：
   在你的 `pom.xml` 文件中加入 Shiro 的 Starter 依赖。
   ```xml
   <dependency>
       <groupId>org.apache.shiro</groupId>
       <artifactId>shiro-spring-boot-web-starter</artifactId>
       <version>1.9.1</version> <!-- 确保使用最新版本 -->
   </dependency>
   ```

2. **配置文件**：
   可以在 `application.yml` 或 `application.properties` 中配置一些基本的 Shiro 设置。
   ```yaml
   shiro:
     web:
       enabled: true
     sessionManager:
       sessionIdCookieEnabled: true
       sessionIdUrlRewritingEnabled: false
     securityManager:
       realm: yourCustomRealmBeanName
   ```

3. **自定义 Realm**：
   创建一个继承自 `AuthorizingRealm` 的类来实现用户认证和授权逻辑。
   ```java
   @Component
   public class MyShiroRealm extends AuthorizingRealm {
       // 实现 doGetAuthenticationInfo 和 doGetAuthorizationInfo 方法
   }
   ```

4. **自动配置**：
   Spring Boot 会自动扫描并注册必要的 Bean，如 `SecurityManager`、`ShiroFilterFactoryBean` 等。你只需要提供自定义的 Realm 和其他可能需要的配置即可。

### 手动配置 Shiro + Spring Boot 自动配置

在这种方式下，你需要手动创建并配置 Shiro 的核心组件，如 `SecurityManager`、`ShiroFilterFactoryBean` 等，但是依然可以利用 Spring Boot 的特性来简化一些工作。

#### 步骤：

1. **添加依赖**：
   同样需要添加 Shiro 和 Spring 的依赖，但不一定是 Starter 包。
   ```xml
   <dependency>
       <groupId>org.apache.shiro</groupId>
       <artifactId>shiro-spring</artifactId>
       <version>1.7.1</version> <!-- 根据实际情况选择版本 -->
   </dependency>
   ```

2. **创建配置类**：
   编写一个配置类来初始化 Shiro 的各个组件。
   ```java
   @Configuration
   public class ShiroConfig {

       @Bean
       public SecurityManager securityManager(Realm myShiroRealm) {
           DefaultWebSecurityManager securityManager = new DefaultWebSecurityManager();
           securityManager.setRealm(myShiroRealm);
           return securityManager;
       }

       @Bean
       public Realm myShiroRealm() {
           return new MyShiroRealm();
       }

       @Bean
       public ShiroFilterFactoryBean shiroFilterFactoryBean(SecurityManager securityManager) {
           ShiroFilterFactoryBean shiroFilterFactoryBean = new ShiroFilterFactoryBean();
           shiroFilterFactoryBean.setSecurityManager(securityManager);
           // 其他配置...
           return shiroFilterFactoryBean;
       }
   }
   ```

3. **自定义 Realm**：
   这部分与 Starter 方式相同，你需要实现自己的 Realm 类来处理认证和授权逻辑。

4. **配置过滤器链**：
   在上面的 `shiroFilterFactoryBean` 方法中配置过滤器链，定义哪些 URL 需要进行安全控制。

5. **启用 Shiro**：
   由于没有 Starter 来自动完成这些步骤，你需要确保所有必需的 Bean 都被正确创建，并且在应用启动时能够正常工作。

### 总结

- **Starter 方式** 更加简单快捷，适合快速开发和标准化项目，因为很多默认设置已经为你准备好，只需少量配置或自定义代码即可运行。
- **手动配置方式** 提供了更高的灵活性，允许你完全掌控 Shiro 的每一个细节，适合对安全性有特殊要求或需要定制化解决方案的情况。

根据你的需求选择合适的方式来集成 Shiro 到 Spring Boot 应用中。如果你想要快速上手并且不需要太多自定义设置，那么使用 Starter 是最好的选择；反之，如果你需要更多的控制权，则可以选择手动配置的方式。


是的，你提到的 **通过 `ShiroFilterChainDefinition` 直接注入的方式** 是 **Shiro 在 Spring Boot 中推荐的一种更现代、更简洁的配置方式**，而且 **确实可以不使用 `ShiroFilterFactoryBean`** 来手动配置过滤器链。

下面我们来详细解释：

---

## ✅ 你的做法是完全正确的

你使用了：

```java
@Bean
public ShiroFilterChainDefinition shiroFilterChainDefinition() {
    DefaultShiroFilterChainDefinition chainDefinition = new DefaultShiroFilterChainDefinition();
    chainDefinition.addPathDefinition("/logout", "logout");
    chainDefinition.addPathDefinition("/error", "anon");
    chainDefinition.addPathDefinition("/druid/**", "authc, roles[admin]");
    chainDefinition.addPathDefinition("/static/**", "anon");
    chainDefinition.addPathDefinition("/**", "authc");
    return chainDefinition;
}
```

这种方式是 **Shiro 官方从 1.4 版本开始推荐的基于 `ShiroFilterChainDefinition` 的配置方式**，它通过声明一个 `ShiroFilterChainDefinition` Bean 来替代传统的 `ShiroFilterFactoryBean` 配置。

---

## 🧠 为什么可以不用 `ShiroFilterFactoryBean`？

### 1. **Shiro 自动配置机制**
当你使用了 Shiro 的 Spring Boot Starter（如 `shiro-spring-boot-web-starter`）时，Shiro 已经通过自动配置类（如 `ShiroAutoConfiguration`）为你配置好了：

- `SecurityManager`
- `ShiroFilter`
- 以及 `ShiroFilterFactoryBean` 的创建逻辑（如果检测到 `ShiroFilterChainDefinition`）

### 2. **ShiroFilterChainDefinition 是更高级别的抽象**
`ShiroFilterChainDefinition` 是一个接口，用于定义 URL 路径和过滤器链的映射关系，它比 `ShiroFilterFactoryBean.setFilterChainDefinitionMap()` 更加模块化、易于维护。

- `DefaultShiroFilterChainDefinition` 是其默认实现。
- 它的职责是：**定义 URL 到 Filter Chain 的映射关系**。

### 3. **自动创建 `ShiroFilterFactoryBean`**
在 Spring Boot 的自动配置中，如果检测到你定义了 `ShiroFilterChainDefinition` Bean，则会自动创建并配置 `ShiroFilterFactoryBean`，并将你定义的链规则应用上去。

你可以理解为：

```java
// 自动配置伪代码
if (beanFactory.containsBean("shiroFilterChainDefinition")) {
    ShiroFilterFactoryBean filterFactoryBean = new ShiroFilterFactoryBean();
    filterFactoryBean.setSecurityManager(securityManager);
    filterFactoryBean.setFilterChainDefinitionMap(
        shiroFilterChainDefinition.getFilterChainMap()
    );
    // 注册为 Bean
}
```

---

## ✅ 什么时候需要手动配置 `ShiroFilterFactoryBean`？

虽然 `ShiroFilterChainDefinition` 简化了配置，但在以下场景中你仍然需要手动配置 `ShiroFilterFactoryBean`：

| 场景 | 是否需要手动配置 |
|------|------------------|
| 只需配置过滤器链（如 anon、authc、roles） | ❌ 不需要 |
| 需要自定义过滤器（如 JWT、验证码等） | ✅ 需要 |
| 需要设置登录页、成功页、未授权页 | ✅ 需要 |
| 需要设置全局 Cookie、Session 配置 | ✅ 需要 |
| 需要自定义 FilterChainResolver | ✅ 需要 |

---

## 🔁 总结对比

| 方式 | 是否推荐 | 适用场景 | 是否需要 `ShiroFilterFactoryBean` |
|------|----------|----------|-------------------------------|
| `ShiroFilterChainDefinition` | ✅ 推荐 | 简单过滤器链配置 | ❌ 不需要 |
| `ShiroFilterFactoryBean` | ✅ 必要时 | 高级定制（自定义过滤器、跳转页等） | ✅ 需要 |

---

## ✅ 最佳实践建议

- 如果你只是配置基本的权限控制（如 `/admin/** = roles[admin]`），使用 `ShiroFilterChainDefinition` 就足够了。
- 如果你需要添加自定义过滤器、设置登录页面、登出处理等高级功能，可以在配置 `ShiroFilterChainDefinition` 的基础上，再手动配置 `ShiroFilterFactoryBean`。

---

## 📌 示例：两者结合使用

```java
@Bean
public ShiroFilterChainDefinition shiroFilterChainDefinition() {
    DefaultShiroFilterChainDefinition chain = new DefaultShiroFilterChainDefinition();
    chain.addPathDefinition("/logout", "logout");
    chain.addPathDefinition("/public/**", "anon");
    chain.addPathDefinition("/admin/**", "roles[admin]");
    chain.addPathDefinition("/**", "authc");
    return chain;
}

@Bean
public ShiroFilterFactoryBean shiroFilterFactoryBean(SecurityManager securityManager,
                                                    ShiroFilterChainDefinition chainDefinition) {
    ShiroFilterFactoryBean filterFactoryBean = new ShiroFilterFactoryBean();
    filterFactoryBean.setSecurityManager(securityManager);
    filterFactoryBean.setFilterChainDefinitionMap(chainDefinition.getFilterChainMap());
    filterFactoryBean.setLoginUrl("/login");
    filterFactoryBean.setUnauthorizedUrl("/unauthorized");
    return filterFactoryBean;
}
```

这样可以同时利用自动配置和手动配置的优势，实现更灵活的安全策略。

---

## 自定义过滤器


在 Apache Shiro 中自定义过滤器可以让你扩展或修改默认的安全行为，以满足特定的应用需求。下面是如何创建和配置自定义过滤器的详细步骤。

### 1. 创建自定义过滤器

首先，你需要创建一个类继承 `org.apache.shiro.web.filter.AccessControlFilter` 或其他合适的基类（如 `PathMatchingFilter`）。然后根据需要覆盖相应的方法来实现你的逻辑。

#### 示例：创建一个简单的自定义过滤器

```java
import org.apache.shiro.web.filter.AccessControlFilter;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;

public class MyCustomFilter extends AccessControlFilter {

    @Override
    protected boolean isAccessAllowed(ServletRequest request, ServletResponse response, Object mappedValue) throws Exception {
        // 判断是否允许访问资源
        // 返回 true 表示允许访问，false 表示拒绝访问
        return false; // 这里只是示例，实际逻辑需要你根据业务需求编写
    }

    @Override
    protected boolean onAccessDenied(ServletRequest request, ServletResponse response) throws Exception {
        // 当访问被拒绝时的操作
        // 可以在这里执行重定向、返回错误信息等操作
        return false; // 返回 false 表示继续处理下一个过滤器；返回 true 表示已经处理完毕，不再继续
    }
}
```

- **`isAccessAllowed()`** 方法用于判断当前请求是否有权限访问指定的资源。
- **`onAccessDenied()`** 方法则是在 `isAccessAllowed()` 返回 `false` 时调用，你可以在此方法中处理访问被拒绝的情况，例如重定向到登录页面或者返回错误信息。

### 2. 注册自定义过滤器

接下来，在 Spring Boot 配置类中注册这个自定义过滤器，并将其添加到过滤器链中。

#### 示例：将自定义过滤器注册为 Bean 并添加到过滤器链

```java
import org.apache.shiro.spring.web.ShiroFilterFactoryBean;
import org.apache.shiro.web.filter.mgt.DefaultFilterChainManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.Map;

@Configuration
public class ShiroConfig {

    @Bean
    public ShiroFilterChainDefinition shiroFilterChainDefinition() {
        DefaultShiroFilterChainDefinition chainDefinition = new DefaultShiroFilterChainDefinition();

        // 添加自定义过滤器到路径 /custom/**
        chainDefinition.addPathDefinition("/custom/**", "myCustom");

        return chainDefinition;
    }

    @Bean(name = "shiroFilter")
    public ShiroFilterFactoryBean shiroFilterFactoryBean(SecurityManager securityManager,
                                                          ShiroFilterChainDefinition chainDefinition) {
        ShiroFilterFactoryBean shiroFilterFactoryBean = new ShiroFilterFactoryBean();
        shiroFilterFactoryBean.setSecurityManager(securityManager);

        // 注册自定义过滤器
        Map<String, String> filterChainMap = chainDefinition.getFilterChainMap();
        shiroFilterFactoryBean.setFilterChainDefinitionMap(filterChainMap);

        // 将自定义过滤器添加到 ShiroFilterFactoryBean 中
        shiroFilterFactoryBean.getFilters().put("myCustom", new MyCustomFilter());

        return shiroFilterFactoryBean;
    }
}
```

这里我们通过 `getFilters().put()` 方法将自定义过滤器添加到了 `ShiroFilterFactoryBean` 的过滤器集合中，并在过滤器链定义中使用 `"myCustom"` 来引用这个过滤器。

### 3. 使用过滤器链

现在，任何对 `/custom/**` 路径下的请求都会经过 `MyCustomFilter` 处理。你可以根据业务需求调整 `isAccessAllowed()` 和 `onAccessDenied()` 方法中的逻辑。

### 注意事项

- **顺序**：如果你有多个过滤器作用于同一个 URL 模式，请注意它们的执行顺序。通常，更具体的规则应该放在前面。
- **异常处理**：确保在自定义过滤器中正确处理异常情况，避免因为未捕获的异常导致请求流程中断。
- **性能考虑**：对于高并发场景，尽量保持过滤器逻辑简单高效，减少不必要的计算或数据库查询。


## Shiro中的缓存机制

在使用 Apache Shiro 的 Spring Boot Starter (`shiro-spring-boot-web-starter` 或类似的) 时，设置 `CacheManager` 可以通过 Java 配置类或利用 Spring Boot 的自动配置功能来完成。虽然 Shiro 和 Spring Boot 提供了灵活的配置选项，但默认情况下，并没有直接提供针对缓存的配置文件（如 `application.properties` 或 `application.yml`）。不过，你可以通过编写配置类或者扩展 Spring Boot 自动配置来集成和配置 `CacheManager`。

### 使用 Java 配置

通常情况下，你将需要创建一个配置类来定义 `CacheManager` 并将其注入到 Shiro 的 `SecurityManager` 中。下面是一个如何为 Shiro 配置 Redis 缓存的例子：

#### 1. 添加依赖

首先，确保你的项目中包含了必要的依赖项，例如 Shiro 和 Redis 支持库。

```xml
<dependency>
    <groupId>org.apache.shiro</groupId>
    <artifactId>shiro-spring-boot-web-starter</artifactId>
    <version>1.9.1</version>
</dependency>
<dependency>
    <groupId>org.apache.shiro</groupId>
    <artifactId>shiro-redis</artifactId>
    <version>3.3.1</version> <!-- 确保选择与Shiro版本兼容的版本 -->
</dependency>
```

#### 2. 配置 CacheManager

接下来，你需要创建一个配置类来设置 `CacheManager`。这里我们以 Redis 为例：

```java
import org.apache.shiro.cache.CacheManager;
import org.apache.shiro.cache.ehcache.EhCacheManager;
import org.apache.shiro.realm.Realm;
import org.apache.shiro.spring.web.ShiroFilterFactoryBean;
import org.apache.shiro.mgt.SecurityManager;
import org.apache.shiro.web.mgt.DefaultWebSecurityManager;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.crazycake.shiro.RedisCacheManager;
import org.crazycake.shiro.RedisManager;

@Configuration
public class ShiroConfig {

    @Bean
    public RedisManager redisManager() {
        RedisManager redisManager = new RedisManager();
        // 设置Redis连接信息
        redisManager.setHost("localhost");
        redisManager.setPort(6379);
        // 如果有密码
        // redisManager.setPassword("yourpassword");
        return redisManager;
    }

    @Bean
    public CacheManager cacheManager(RedisManager redisManager) {
        RedisCacheManager cacheManager = new RedisCacheManager();
        cacheManager.setRedisManager(redisManager);
        return cacheManager;
    }

    @Bean
    public Realm myRealm(CacheManager cacheManager) {
        MyCustomRealm realm = new MyCustomRealm();
        realm.setCacheManager(cacheManager);
        realm.setCachingEnabled(true);
        realm.setAuthenticationCachingEnabled(true);
        realm.setAuthorizationCachingEnabled(true);
        return realm;
    }

    @Bean
    public SecurityManager securityManager(Realm realm, CacheManager cacheManager) {
        DefaultWebSecurityManager securityManager = new DefaultWebSecurityManager();
        securityManager.setRealm(realm);
        securityManager.setCacheManager(cacheManager);
        return securityManager;
    }

    @Bean(name = "shiroFilter")
    public ShiroFilterFactoryBean shiroFilterFactoryBean(SecurityManager securityManager) {
        ShiroFilterFactoryBean shiroFilterFactoryBean = new ShiroFilterFactoryBean();
        shiroFilterFactoryBean.setSecurityManager(securityManager);
        // 其他过滤器链等配置...
        return shiroFilterFactoryBean;
    }
}
```

### 注意事项

- **缓存过期时间**：根据业务需求调整缓存的有效期，避免因缓存中的数据更新不及时导致的安全问题。
- **分布式环境下的缓存一致性**：如果你的应用部署在一个分布式环境中，确保所有节点之间的缓存同步。例如，使用 Redis 这样的集中式缓存解决方案可以帮助解决这个问题。
- **缓存大小限制**：合理设置缓存的最大容量，避免因缓存过大而导致内存溢出或其他性能问题。



## CacheManager

### CacheManager 概述

在 Apache Shiro 中，`CacheManager` 是一个用于管理缓存实例的接口。它为 Shiro 提供了统一的缓存抽象层，使得开发者可以方便地将不同的缓存技术（如 Ehcache、Redis 等）集成到 Shiro 的认证和授权流程中，而无需关心具体的缓存实现细节。通过 `CacheManager`，Shiro 可以显著提升性能，尤其是在处理大量并发请求时。

### CacheManager 架构设置

#### 核心组件

1. **`CacheManager`**：这是 Shiro 缓存体系的核心接口，负责创建和管理 `Cache` 实例。
2. **`Cache`**：表示一个具体的数据缓存，每个 `Cache` 实例都与特定的命名空间相关联，用于存储特定类型的数据（例如认证信息或授权信息）。
3. **`SecurityManager`**：Shiro 的核心安全管理器，通常会配置一个 `CacheManager` 来优化其性能。
4. **`Realm`**：安全领域对象，代表了一个数据源，可以通过配置来使用 `CacheManager` 提供的缓存功能。

#### 配置架构

通常情况下，你需要执行以下步骤来设置 `CacheManager`：

1. **选择并配置一个合适的 `CacheManager` 实现**。
2. **将其注入到 `SecurityManager` 和相关的 `Realm` 中**。
3. **启用 `Realm` 的缓存功能**，以便利用缓存加速认证和授权过程。

### 常用实现类

Shiro 支持多种 `CacheManager` 实现，以下是几个常见的例子：

- **`EhCacheManager`**：基于 Ehcache 实现的缓存管理器，适合于需要内存级高速缓存的应用场景。
  
  ```java
  import org.apache.shiro.cache.ehcache.EhCacheManager;

  @Bean
  public EhCacheManager cacheManager() {
      return new EhCacheManager();
  }
  ```

- **`RedisCacheManager`**（来自第三方库 `shiro-redis`）：如果你正在使用 Redis 作为缓存后端，可以选择此实现。

  ```java
  import org.crazycake.shiro.RedisCacheManager;
  import org.crazycake.shiro.RedisManager;

  @Bean
  public RedisCacheManager cacheManager(RedisManager redisManager) {
      RedisCacheManager cacheManager = new RedisCacheManager();
      cacheManager.setRedisManager(redisManager);
      return cacheManager;
  }

  @Bean
  public RedisManager redisManager() {
      RedisManager redisManager = new RedisManager();
      redisManager.setHost("localhost");
      redisManager.setPort(6379);
      return redisManager;
  }
  ```

- **`MemoryConstrainedCacheManager`**：这是一种简单的内存缓存管理器，适用于小规模应用或开发测试环境。

  ```java
  import org.apache.shiro.cache.MemoryConstrainedCacheManager;

  @Bean
  public MemoryConstrainedCacheManager cacheManager() {
      return new MemoryConstrainedCacheManager();
  }
  ```

### 开发中的常用 API

#### `CacheManager`

- **`getCache(String name)`**：获取指定名称的缓存实例。如果该名称的缓存不存在，则可能会自动创建一个新的缓存实例（取决于具体实现）。

  ```java
  Cache<Object, Object> authenticationCache = cacheManager.getCache("authenticationCache");
  ```

#### `Cache`

- **`put(Object key, Object value)`**：将给定的键值对放入缓存中。

  ```java
  authenticationCache.put(user.getId(), user);
  ```

- **`Object get(Object key)`**：根据给定的键检索缓存中的值。

  ```java
  User cachedUser = (User) authenticationCache.get(user.getId());
  ```

- **`remove(Object key)`**：从缓存中移除指定键对应的条目。

  ```java
  authenticationCache.remove(user.getId());
  ```

- **`clear()`**：清空整个缓存。

  ```java
  authenticationCache.clear();
  ```

#### 在 `Realm` 中使用缓存

为了在 `Realm` 中启用缓存，你可以这样做：

```java
@Bean
public MyCustomRealm myCustomRealm(CacheManager cacheManager) {
    MyCustomRealm realm = new MyCustomRealm();
    realm.setCachingEnabled(true); // 启用缓存
    realm.setAuthenticationCachingEnabled(true); // 启用认证缓存
    realm.setAuthorizationCachingEnabled(true); // 启用授权缓存
    realm.setCacheManager(cacheManager); // 设置缓存管理器
    return realm;
}
```


## 分布式会话

在分布式环境中，确保会话数据的一致性和可用性是一个关键挑战。对于 Apache Shiro 而言，实现分布式会话管理通常涉及到将 Shiro 的会话存储从默认的内存或本地文件系统迁移到一个分布式的存储解决方案，如 Redis、数据库或其他支持分布式访问的存储系统。以下是如何使用 Redis 来实现 Shiro 分布式会话管理的示例。

### 使用 Redis 实现 Shiro 分布式会话

#### 1. 添加依赖

首先，你需要添加必要的 Maven 依赖项，包括 Shiro 和 Shiro-redis 集成库（`shiro-redis`）。确保选择与你的 Shiro 版本兼容的 `shiro-redis` 库版本。

```xml
<dependency>
    <groupId>org.apache.shiro</groupId>
    <artifactId>shiro-spring-boot-web-starter</artifactId>
    <version>1.9.1</version>
</dependency>
<dependency>
    <groupId>org.crazycake</groupId>
    <artifactId>shiro-redis</artifactId>
    <version>3.3.0</version> <!-- 根据需要选择合适的版本 -->
</dependency>
```

同时，不要忘记添加 Redis 相关的依赖：

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

#### 2. 配置 RedisSessionDAO

接下来，在 Spring Boot 配置类中配置 `RedisSessionDAO`，以便 Shiro 可以将 session 数据存储到 Redis 中。

```java
import org.apache.shiro.session.mgt.eis.SessionDAO;
import org.apache.shiro.spring.web.config.DefaultShiroFilterChainDefinition;
import org.apache.shiro.spring.web.config.ShiroFilterChainDefinition;
import org.apache.shiro.web.session.mgt.DefaultWebSessionManager;
import org.crazycake.shiro.RedisCacheManager;
import org.crazycake.shiro.RedisManager;
import org.crazycake.shiro.RedisSessionDAO;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ShiroConfig {

    @Bean
    public RedisManager redisManager() {
        RedisManager redisManager = new RedisManager();
        redisManager.setHost("localhost");
        redisManager.setPort(6379);
        // 如果有密码
        // redisManager.setPassword("yourpassword");
        return redisManager;
    }

    @Bean
    public SessionDAO sessionDAO(RedisManager redisManager) {
        RedisSessionDAO sessionDAO = new RedisSessionDAO();
        sessionDAO.setRedisManager(redisManager);
        return sessionDAO;
    }

    @Bean
    public DefaultWebSessionManager sessionManager(SessionDAO sessionDAO) {
        DefaultWebSessionManager sessionManager = new DefaultWebSessionManager();
        sessionManager.setSessionDAO(sessionDAO);
        return sessionManager;
    }
}
```

这里的关键是 `RedisSessionDAO`，它负责与 Redis 进行交互来存储和检索 Shiro 的会话信息。

#### 3. 配置 SecurityManager

确保将 `sessionManager` 注入到 `SecurityManager` 中：

```java
@Bean
public SecurityManager securityManager(DefaultWebSessionManager sessionManager, Realm realm) {
    DefaultWebSecurityManager securityManager = new DefaultWebSecurityManager();
    securityManager.setRealm(realm);
    securityManager.setSessionManager(sessionManager);
    return securityManager;
}
```

#### 4. 配置 Shiro Filter

最后，别忘了配置 Shiro 的过滤器链定义，虽然这部分与分布式会话无直接关系，但它对于整个安全框架的运行至关重要。

```java
@Bean
public ShiroFilterChainDefinition shiroFilterChainDefinition() {
    DefaultShiroFilterChainDefinition chainDefinition = new DefaultShiroFilterChainDefinition();
    // 定义你的过滤器链规则
    return chainDefinition;
}
```

### 注意事项

- **序列化**：由于 Redis 是基于键值对存储的，因此所有存储在 Redis 中的对象都需要能够被序列化。确保你的会话对象实现了 `Serializable` 接口。
- **过期时间**：根据业务需求设置适当的会话超时时间，并确保 Redis 中存储的会话数据也遵循这一策略。
- **安全性**：考虑对存储在 Redis 中的敏感信息进行加密处理，防止未授权访问。



Apache Shiro 的 `AccessControlFilter` 是其安全过滤器体系中的一个核心抽象类，用于控制对资源的访问。它位于 `org.apache.shiro.web.filter` 包下，是许多具体安全过滤器的基类。

下面我将为你详细列出 **`AccessControlFilter` 的完整继承结构**，并以**文字结构图**的方式呈现（由于无法画图，用缩进表示继承关系），同时对每个类进行简要说明。

---

## 🧱 Shiro 中 `AccessControlFilter` 的完整继承结构（从上到下）

```
javax.servlet.Filter
└── org.apache.shiro.web.servlet.OncePerRequestFilter
    └── org.apache.shiro.web.servlet.NameableFilter
        └── org.apache.shiro.web.servlet.AdviceFilter
            └── org.apache.shiro.web.filter.PathMatchingFilter
                └── org.apache.shiro.web.filter.AccessControlFilter
                    ├── org.apache.shiro.web.filter.authc.AuthenticatingFilter
                    │   ├── org.apache.shiro.web.filter.authc.BasicHttpAuthenticationFilter
                    │   ├── org.apache.shiro.web.filter.authc.FormAuthenticationFilter
                    │   ├── org.apache.shiro.web.filter.authc.KickoutSessionControlFilter
                    │   └── org.apache.shiro.web.filter.authc.AnonymousFilter
                    │   └── org.apache.shiro.web.filter.authc.UserFilter
                    │
                    ├── org.apache.shiro.web.filter.authz.AuthorizationFilter
                    │   ├── org.apache.shiro.web.filter.authz.RolesAuthorizationFilter
                    │   ├── org.apache.shiro.web.filter.authz.PermissionsAuthorizationFilter
                    │   └── org.apache.shiro.web.filter.authz.PortFilter
                    │
                    ├── org.apache.shiro.web.filter.mgt.ValidatingFilter
                    │   └── org.apache.shiro.web.filter.mgt.JwtFilter
                    │
                    ├── org.apache.shiro.web.filter.session.NoSessionCreationFilter
                    │
                    ├── org.apache.shiro.web.filter.authz.SslFilter
                    │
                    ├── org.apache.shiro.web.filter.authz.LogoutFilter
                    │
                    └── org.apache.shiro.web.filter.authz.UserAgentFilter
```

---

## 🧩 各层级类说明

### 1. `javax.servlet.Filter`（Java EE 标准接口）

- 所有过滤器的顶级接口。
- 定义了 `doFilter()` 方法（Servlet 2.x）或 `doFilterInternal()`（Shiro 实现）。

---

### 2. `OncePerRequestFilter`

- 确保每个请求只被过滤一次。
- 防止在请求处理过程中被多次调用。

---

### 3. `NameableFilter`

- 为过滤器提供一个名称（name），用于在配置中引用。

---

### 4. `AdviceFilter`

- 提供类似 AOP 的拦截能力。
- 提供了 `before()`、`after()`、`afterCompletion()` 等生命周期方法。

---

### 5. `PathMatchingFilter`

- 支持基于路径匹配的过滤器。
- 可以通过配置指定哪些路径需要该过滤器生效。

---

### 6. `AccessControlFilter`（关键抽象类）

- 提供了访问控制的基础逻辑。
- 定义了两个关键方法：
  - `boolean isAccessAllowed(ServletRequest request, ServletResponse response, Object mappedValue)`：判断是否允许访问。
  - `boolean onAccessDenied(ServletRequest request, ServletResponse response)`：当访问被拒绝时执行的逻辑。

---

## 📌 常见子类说明

### ✅ `AuthenticatingFilter`（认证相关）

- 用于处理认证逻辑的基类。
- 子类包括：
  - `BasicHttpAuthenticationFilter`：HTTP Basic 认证。
  - `FormAuthenticationFilter`：表单登录。
  - `AnonymousFilter`：允许匿名访问。
  - `UserFilter`：已登录用户可访问。
  - `KickoutSessionControlFilter`：踢出重复登录用户。

### ✅ `AuthorizationFilter`（授权相关）

- 用于处理授权逻辑的基类。
- 子类包括：
  - `RolesAuthorizationFilter`：按角色控制访问。
  - `PermissionsAuthorizationFilter`：按权限控制访问。
  - `PortFilter`：按端口限制访问。

### ✅ `ValidatingFilter`（验证相关）

- 用于验证 Token 或 JWT。
- 子类如 `JwtFilter`。

### ✅ `NoSessionCreationFilter`

- 禁止创建新会话，适用于无状态 API。

### ✅ `SslFilter`

- 强制使用 HTTPS 访问。

### ✅ `LogoutFilter`

- 处理登出逻辑。

### ✅ `UserAgentFilter`

- 根据 User-Agent 进行访问控制。

---

## 🧠 小结

- `AccessControlFilter` 是 Shiro 中所有安全过滤器的基类，它提供了访问控制的通用逻辑。
- 它的子类分为 **认证类（AuthenticatingFilter）** 和 **授权类（AuthorizationFilter）** 两大类。
- 实际开发中，你可以通过继承 `AccessControlFilter` 或其子类来自定义过滤器，实现特定的认证/授权逻辑。
- Shiro 的过滤器体系设计清晰、层次分明，适合扩展和集成。

---


> **参考资料：**
> - Shiro集成Springboot：https://segmentfault.com/a/1190000014479154
> - Shiro配置：https://shiro.apache.org/documentation.html
> - Shiro集成Springboot：https://shiro.apache.org/spring-boot.html
> - Spring Boot3.0(十八)：整合shiro+jwt：https://zhuanlan.zhihu.com/p/663925382
> - Shiro整合JWT实现认证和权限鉴定：https://developer.aliyun.com/article/1296302   
> - Shiro实现Oauth2.0：https://cloud.tencent.com/developer/article/1815267   
> - 基于SpringBoot+Shiro+JWT实现的SSO单点登录系统：https://juejin.cn/post/
> - springboot + shiro + cas 实现 登录 + 授权 + sso单点登录 :https://blog.csdn.net/qq_33101675/article/details/105577898

