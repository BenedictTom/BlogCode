---
title: Java注解
main_color: "#458d8dff"  
categories: Java
tags:
  - Java    
cover: https://free.picui.cn/free/2024/06/08/6663c7524fbbe.png
---

# Java注解详解

## 1. 注解基础概念

### 1.1 什么是注解

注解（Annotation）是Java 5引入的一种元数据机制，它提供了一种在代码中添加元数据的方式。注解本身不会影响程序的执行，但可以被编译器、工具或运行时环境读取和处理。

### 1.2 注解的本质

注解本质上是一个接口，所有注解都隐式继承自`java.lang.annotation.Annotation`接口：

```java
public interface Annotation {
    boolean equals(Object obj);
    int hashCode();
    String toString();
    Class<? extends Annotation> annotationType();
}
```

### 1.3 注解的优势

- **元数据支持**：为代码添加描述性信息
- **编译时检查**：提供编译时验证
- **代码生成**：支持自动代码生成
- **框架集成**：简化框架配置
- **文档化**：提高代码可读性

## 2. 注解的底层原理

### 2.1 注解的存储机制

注解信息在编译时被存储在class文件的属性表中，主要包括：

```java
// 注解在class文件中的存储结构
public class AnnotationInfo {
    // 注解类型
    private String annotationType;
    // 注解元素值
    private Map<String, Object> elementValues;
    // 注解位置（类、方法、字段等）
    private AnnotationTarget target;
}
```

### 2.2 注解的反射机制

```java
import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.lang.reflect.Field;

public class AnnotationReflectionDemo {
    
    public static void main(String[] args) throws Exception {
        Class<?> clazz = MyClass.class;
        
        // 获取类上的注解
        Annotation[] classAnnotations = clazz.getAnnotations();
        for (Annotation annotation : classAnnotations) {
            System.out.println("类注解: " + annotation.annotationType().getSimpleName());
        }
        
        // 获取方法上的注解
        Method method = clazz.getMethod("myMethod");
        Annotation[] methodAnnotations = method.getAnnotations();
        for (Annotation annotation : methodAnnotations) {
            System.out.println("方法注解: " + annotation.annotationType().getSimpleName());
        }
        
        // 获取字段上的注解
        Field field = clazz.getField("myField");
        Annotation[] fieldAnnotations = field.getAnnotations();
        for (Annotation annotation : fieldAnnotations) {
            System.out.println("字段注解: " + annotation.annotationType().getSimpleName());
        }
    }
}

class MyClass {
    @Deprecated
    public String myField;
    
    @Override
    public void myMethod() {
        System.out.println("Hello World");
    }
}
```

### 2.3 注解处理器

```java
import javax.annotation.processing.*;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.*;
import javax.tools.Diagnostic;
import java.util.Set;

@SupportedAnnotationTypes("com.example.MyAnnotation")
@SupportedSourceVersion(SourceVersion.RELEASE_8)
public class MyAnnotationProcessor extends AbstractProcessor {
    
    @Override
    public boolean process(Set<? extends TypeElement> annotations, 
                          RoundEnvironment roundEnv) {
        
        for (Element element : roundEnv.getElementsAnnotatedWith(MyAnnotation.class)) {
            // 处理被注解的元素
            processingEnv.getMessager().printMessage(
                Diagnostic.Kind.NOTE, 
                "Processing element: " + element.getSimpleName()
            );
        }
        
        return true;
    }
}
```

## 3. 内置注解详解

### 3.1 元注解（Meta-Annotations）

#### @Retention - 注解保留策略

```java
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

// SOURCE: 仅保留在源码中，编译时丢弃
@Retention(RetentionPolicy.SOURCE)
public @interface SourceAnnotation {
    String value() default "";
}

// CLASS: 保留在class文件中，但运行时不可见（默认）
@Retention(RetentionPolicy.CLASS)
public @interface ClassAnnotation {
    String value() default "";
}

// RUNTIME: 运行时可见，可以通过反射获取
@Retention(RetentionPolicy.RUNTIME)
public @interface RuntimeAnnotation {
    String value() default "";
}
```

#### @Target - 注解作用目标

```java
import java.lang.annotation.ElementType;
import java.lang.annotation.Target;

// 可以用于类、接口、枚举
@Target(ElementType.TYPE)
public @interface TypeAnnotation {
    String value();
}

// 可以用于字段
@Target(ElementType.FIELD)
public @interface FieldAnnotation {
    String value();
}

// 可以用于方法
@Target(ElementType.METHOD)
public @interface MethodAnnotation {
    String value();
}

// 可以用于参数
@Target(ElementType.PARAMETER)
public @interface ParameterAnnotation {
    String value();
}

// 可以用于构造器
@Target(ElementType.CONSTRUCTOR)
public @interface ConstructorAnnotation {
    String value();
}

// 可以用于局部变量
@Target(ElementType.LOCAL_VARIABLE)
public @interface LocalVariableAnnotation {
    String value();
}

// 可以用于注解类型
@Target(ElementType.ANNOTATION_TYPE)
public @interface AnnotationTypeAnnotation {
    String value();
}

// 可以用于包
@Target(ElementType.PACKAGE)
public @interface PackageAnnotation {
    String value();
}

// 可以用于类型参数（泛型）
@Target(ElementType.TYPE_PARAMETER)
public @interface TypeParameterAnnotation {
    String value();
}

// 可以用于类型使用
@Target(ElementType.TYPE_USE)
public @interface TypeUseAnnotation {
    String value();
}

// 多个目标
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD})
public @interface MultiTargetAnnotation {
    String value();
}
```

#### @Documented - 文档化注解

```java
import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Documented
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface DocumentedAnnotation {
    String value() default "This annotation will appear in JavaDoc";
}

@DocumentedAnnotation("This is a documented annotation")
public class DocumentedClass {
    // 这个类上的注解会出现在JavaDoc中
}
```

#### @Inherited - 继承注解

```java
import java.lang.annotation.Inherited;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.lang.annotation.ElementType;

@Inherited
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface InheritedAnnotation {
    String value() default "";
}

@InheritedAnnotation("Parent annotation")
class ParentClass {
    // 父类注解
}

class ChildClass extends ParentClass {
    // 子类会自动继承父类的@Inherited注解
}

// 测试继承
public class InheritanceTest {
    public static void main(String[] args) {
        // 检查子类是否有父类的注解
        if (ChildClass.class.isAnnotationPresent(InheritedAnnotation.class)) {
            InheritedAnnotation annotation = ChildClass.class.getAnnotation(InheritedAnnotation.class);
            System.out.println("子类继承了父类注解: " + annotation.value());
        }
    }
}
```

#### @Repeatable - 可重复注解

```java
import java.lang.annotation.Repeatable;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
import java.lang.annotation.ElementType;

// 容器注解
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Roles {
    Role[] value();
}

// 可重复注解
@Repeatable(Roles.class)
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
public @interface Role {
    String value();
}

// 使用可重复注解
@Role("ADMIN")
@Role("USER")
@Role("GUEST")
public class User {
    // 可以重复使用@Role注解
}

// 获取重复注解
public class RepeatableAnnotationDemo {
    public static void main(String[] args) {
        Class<?> clazz = User.class;
        
        // 方式1：通过容器注解获取
        if (clazz.isAnnotationPresent(Roles.class)) {
            Roles roles = clazz.getAnnotation(Roles.class);
            for (Role role : roles.value()) {
                System.out.println("角色: " + role.value());
            }
        }
        
        // 方式2：直接获取重复注解
        Role[] roles = clazz.getAnnotationsByType(Role.class);
        for (Role role : roles) {
            System.out.println("角色: " + role.value());
        }
    }
}
```

### 3.2 标准注解

#### @Override - 重写注解

```java
class Animal {
    public void makeSound() {
        System.out.println("Animal makes sound");
    }
}

class Dog extends Animal {
    @Override
    public void makeSound() {
        System.out.println("Dog barks");
    }
    
    // 编译错误：方法名拼写错误，@Override会提示
    // @Override
    // public void makeSond() {  // 拼写错误
    //     System.out.println("Dog barks");
    // }
}
```

#### @Deprecated - 废弃注解

```java
public class DeprecatedDemo {
    
    @Deprecated
    public void oldMethod() {
        System.out.println("This method is deprecated");
    }
    
    @Deprecated(since = "1.5", forRemoval = true)
    public void veryOldMethod() {
        System.out.println("This method will be removed in future version");
    }
    
    public void newMethod() {
        System.out.println("Use this method instead");
    }
}

// 使用示例
public class DeprecatedUsage {
    public static void main(String[] args) {
        DeprecatedDemo demo = new DeprecatedDemo();
        
        // 编译器会警告使用了废弃的方法
        demo.oldMethod();
        demo.veryOldMethod();
        
        // 推荐使用新方法
        demo.newMethod();
    }
}
```

#### @SuppressWarnings - 抑制警告

```java
import java.util.*;

public class SuppressWarningsDemo {
    
    @SuppressWarnings("unchecked")
    public void suppressUncheckedWarning() {
        List list = new ArrayList(); // 未检查的转换警告
        list.add("Hello");
    }
    
    @SuppressWarnings("rawtypes")
    public void suppressRawTypesWarning() {
        List list = new ArrayList(); // 原始类型警告
        list.add("World");
    }
    
    @SuppressWarnings({"unchecked", "rawtypes"})
    public void suppressMultipleWarnings() {
        List list = new ArrayList();
        list.add("Multiple warnings suppressed");
    }
    
    @SuppressWarnings("all")
    public void suppressAllWarnings() {
        // 抑制所有警告
        List list = new ArrayList();
        list.add("All warnings suppressed");
    }
}
```

#### @SafeVarargs - 安全可变参数

```java
import java.util.*;

public class SafeVarargsDemo {
    
    @SafeVarargs
    public static <T> List<T> createList(T... items) {
        List<T> list = new ArrayList<>();
        for (T item : items) {
            list.add(item);
        }
        return list;
    }
    
    // 不安全的可变参数方法
    public static <T> void unsafeMethod(T... items) {
        Object[] array = items; // 潜在的类型安全问题
        array[0] = "String"; // 如果T不是String，会抛出ClassCastException
    }
    
    public static void main(String[] args) {
        List<String> stringList = createList("Hello", "World");
        List<Integer> intList = createList(1, 2, 3);
        
        System.out.println(stringList);
        System.out.println(intList);
    }
}
```

#### @FunctionalInterface - 函数式接口

```java
@FunctionalInterface
public interface Calculator {
    int calculate(int a, int b);
    
    // 可以有默认方法
    default void printResult(int result) {
        System.out.println("Result: " + result);
    }
    
    // 可以有静态方法
    static Calculator getAdditionCalculator() {
        return (a, b) -> a + b;
    }
    
    // 可以有Object类的方法
    boolean equals(Object obj);
    String toString();
}

// 使用函数式接口
public class FunctionalInterfaceDemo {
    public static void main(String[] args) {
        // Lambda表达式
        Calculator add = (a, b) -> a + b;
        Calculator multiply = (a, b) -> a * b;
        
        System.out.println(add.calculate(5, 3)); // 8
        System.out.println(multiply.calculate(5, 3)); // 15
        
        // 方法引用
        Calculator subtract = Math::subtractExact;
        System.out.println(subtract.calculate(5, 3)); // 2
    }
}
```

## 4. 自定义注解

### 4.1 基本自定义注解

```java
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.TYPE, ElementType.METHOD})
public @interface MyAnnotation {
    String value() default "";
    int priority() default 0;
    String[] tags() default {};
}

// 使用自定义注解
@MyAnnotation(value = "Class annotation", priority = 1, tags = {"important", "demo"})
public class MyClass {
    
    @MyAnnotation(value = "Method annotation", priority = 2)
    public void myMethod() {
        System.out.println("Hello from annotated method");
    }
}
```

### 4.2 复杂自定义注解

```java
import java.lang.annotation.*;
import java.time.LocalDateTime;

@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD})
@Repeatable(Validations.class)
public @interface Validation {
    String field() default "";
    String message() default "Validation failed";
    ValidationType type() default ValidationType.REQUIRED;
    int minLength() default 0;
    int maxLength() default Integer.MAX_VALUE;
    String pattern() default "";
    LocalDateTime since() default @LocalDateTime;
}

@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.TYPE, ElementType.METHOD, ElementType.FIELD})
public @interface Validations {
    Validation[] value();
}

public enum ValidationType {
    REQUIRED, EMAIL, PHONE, URL, CUSTOM
}

// 使用复杂注解
public class User {
    @Validation(field = "name", type = ValidationType.REQUIRED, message = "用户名不能为空")
    @Validation(field = "name", type = ValidationType.CUSTOM, minLength = 2, maxLength = 20, message = "用户名长度必须在2-20之间")
    private String name;
    
    @Validation(field = "email", type = ValidationType.EMAIL, message = "邮箱格式不正确")
    private String email;
    
    @Validation(field = "phone", type = ValidationType.PHONE, message = "手机号格式不正确")
    private String phone;
    
    // getter和setter方法
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    
    public String getPhone() { return phone; }
    public void setPhone(String phone) { this.phone = phone; }
}
```

### 4.3 注解处理器实现

```java
import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

public class ValidationProcessor {
    
    public static List<String> validate(Object obj) {
        List<String> errors = new ArrayList<>();
        Class<?> clazz = obj.getClass();
        
        Field[] fields = clazz.getDeclaredFields();
        for (Field field : fields) {
            field.setAccessible(true);
            
            // 获取字段上的所有验证注解
            Validation[] validations = field.getAnnotationsByType(Validation.class);
            
            for (Validation validation : validations) {
                try {
                    Object value = field.get(obj);
                    String error = validateField(validation, value);
                    if (error != null) {
                        errors.add(error);
                    }
                } catch (IllegalAccessException e) {
                    errors.add("无法访问字段: " + field.getName());
                }
            }
        }
        
        return errors;
    }
    
    private static String validateField(Validation validation, Object value) {
        String fieldName = validation.field();
        String message = validation.message();
        
        // 必填验证
        if (validation.type() == ValidationType.REQUIRED) {
            if (value == null || (value instanceof String && ((String) value).trim().isEmpty())) {
                return fieldName + ": " + message;
            }
        }
        
        // 长度验证
        if (value instanceof String) {
            String strValue = (String) value;
            if (strValue.length() < validation.minLength()) {
                return fieldName + ": 长度不能少于 " + validation.minLength() + " 个字符";
            }
            if (strValue.length() > validation.maxLength()) {
                return fieldName + ": 长度不能超过 " + validation.maxLength() + " 个字符";
            }
        }
        
        // 邮箱验证
        if (validation.type() == ValidationType.EMAIL && value instanceof String) {
            String emailPattern = "^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$";
            if (!Pattern.matches(emailPattern, (String) value)) {
                return fieldName + ": " + message;
            }
        }
        
        // 手机号验证
        if (validation.type() == ValidationType.PHONE && value instanceof String) {
            String phonePattern = "^1[3-9]\\d{9}$";
            if (!Pattern.matches(phonePattern, (String) value)) {
                return fieldName + ": " + message;
            }
        }
        
        // 自定义正则验证
        if (!validation.pattern().isEmpty() && value instanceof String) {
            if (!Pattern.matches(validation.pattern(), (String) value)) {
                return fieldName + ": " + message;
            }
        }
        
        return null;
    }
}

// 测试验证处理器
public class ValidationTest {
    public static void main(String[] args) {
        User user = new User();
        user.setName(""); // 空用户名
        user.setEmail("invalid-email"); // 无效邮箱
        user.setPhone("12345678901"); // 无效手机号
        
        List<String> errors = ValidationProcessor.validate(user);
        for (String error : errors) {
            System.out.println(error);
        }
    }
}
```

## 5. 注解与AOP结合应用

### 5.1 日志注解

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Log {
    String value() default "";
    LogLevel level() default LogLevel.INFO;
    boolean includeArgs() default true;
    boolean includeResult() default true;
}

public enum LogLevel {
    DEBUG, INFO, WARN, ERROR
}

// 日志切面
public class LogAspect {
    
    public static void logMethod(Method method, Object[] args, Object result, Throwable throwable) {
        Log logAnnotation = method.getAnnotation(Log.class);
        if (logAnnotation == null) return;
        
        String methodName = method.getName();
        String className = method.getDeclaringClass().getSimpleName();
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
        
        StringBuilder logMessage = new StringBuilder();
        logMessage.append("[").append(timestamp).append("] ");
        logMessage.append("[").append(logAnnotation.level()).append("] ");
        logMessage.append(className).append(".").append(methodName);
        
        if (logAnnotation.includeArgs() && args != null) {
            logMessage.append(" - Args: [");
            for (int i = 0; i < args.length; i++) {
                if (i > 0) logMessage.append(", ");
                logMessage.append(args[i]);
            }
            logMessage.append("]");
        }
        
        if (throwable != null) {
            logMessage.append(" - Exception: ").append(throwable.getMessage());
        } else if (logAnnotation.includeResult() && result != null) {
            logMessage.append(" - Result: ").append(result);
        }
        
        System.out.println(logMessage.toString());
    }
}

// 使用日志注解
public class UserService {
    
    @Log(value = "用户登录", level = LogLevel.INFO)
    public boolean login(String username, String password) {
        // 模拟登录逻辑
        return "admin".equals(username) && "123456".equals(password);
    }
    
    @Log(value = "获取用户信息", level = LogLevel.DEBUG, includeArgs = false)
    public String getUserInfo(String userId) {
        // 模拟获取用户信息
        return "User info for: " + userId;
    }
    
    @Log(value = "删除用户", level = LogLevel.WARN)
    public void deleteUser(String userId) {
        // 模拟删除用户
        System.out.println("Deleting user: " + userId);
    }
}
```

### 5.2 缓存注解

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;
import java.util.concurrent.ConcurrentHashMap;

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Cache {
    String key() default "";
    int expireSeconds() default 300; // 5分钟默认过期
    boolean refresh() default false;
}

// 缓存管理器
public class CacheManager {
    private static final ConcurrentHashMap<String, CacheEntry> cache = new ConcurrentHashMap<>();
    
    public static Object get(String key) {
        CacheEntry entry = cache.get(key);
        if (entry == null) return null;
        
        if (entry.isExpired()) {
            cache.remove(key);
            return null;
        }
        
        return entry.getValue();
    }
    
    public static void put(String key, Object value, int expireSeconds) {
        cache.put(key, new CacheEntry(value, expireSeconds));
    }
    
    public static void clear() {
        cache.clear();
    }
    
    private static class CacheEntry {
        private final Object value;
        private final long expireTime;
        
        public CacheEntry(Object value, int expireSeconds) {
            this.value = value;
            this.expireTime = System.currentTimeMillis() + expireSeconds * 1000L;
        }
        
        public Object getValue() {
            return value;
        }
        
        public boolean isExpired() {
            return System.currentTimeMillis() > expireTime;
        }
    }
}

// 缓存切面
public class CacheAspect {
    
    public static Object handleCache(Method method, Object[] args, Object target) throws Exception {
        Cache cacheAnnotation = method.getAnnotation(Cache.class);
        if (cacheAnnotation == null) {
            return method.invoke(target, args);
        }
        
        String cacheKey = generateCacheKey(method, args, cacheAnnotation.key());
        
        // 尝试从缓存获取
        Object cachedResult = CacheManager.get(cacheKey);
        if (cachedResult != null) {
            System.out.println("Cache hit for key: " + cacheKey);
            return cachedResult;
        }
        
        // 缓存未命中，执行方法
        System.out.println("Cache miss for key: " + cacheKey);
        Object result = method.invoke(target, args);
        
        // 存入缓存
        CacheManager.put(cacheKey, result, cacheAnnotation.expireSeconds());
        
        return result;
    }
    
    private static String generateCacheKey(Method method, Object[] args, String customKey) {
        if (!customKey.isEmpty()) {
            return customKey;
        }
        
        StringBuilder keyBuilder = new StringBuilder();
        keyBuilder.append(method.getDeclaringClass().getSimpleName());
        keyBuilder.append(".").append(method.getName());
        
        if (args != null && args.length > 0) {
            keyBuilder.append("(");
            for (int i = 0; i < args.length; i++) {
                if (i > 0) keyBuilder.append(",");
                keyBuilder.append(args[i]);
            }
            keyBuilder.append(")");
        }
        
        return keyBuilder.toString();
    }
}

// 使用缓存注解
public class DataService {
    
    @Cache(key = "user_list", expireSeconds = 600)
    public String getUsers() {
        System.out.println("Executing expensive database query...");
        // 模拟数据库查询
        try {
            Thread.sleep(1000); // 模拟耗时操作
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return "User list data";
    }
    
    @Cache(expireSeconds = 300)
    public String getUserById(String userId) {
        System.out.println("Querying user by ID: " + userId);
        return "User data for ID: " + userId;
    }
    
    @Cache(key = "config", expireSeconds = 3600)
    public String getConfig() {
        System.out.println("Loading configuration...");
        return "Configuration data";
    }
}
```

### 5.3 权限控制注解

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;
import java.util.*;

@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.TYPE, ElementType.METHOD})
public @interface RequirePermission {
    String[] value() default {};
    PermissionType type() default PermissionType.AND; // AND 或 OR
}

public enum PermissionType {
    AND, OR
}

// 权限管理器
public class PermissionManager {
    private static final Set<String> userPermissions = new HashSet<>();
    
    public static void setUserPermissions(String... permissions) {
        userPermissions.clear();
        userPermissions.addAll(Arrays.asList(permissions));
    }
    
    public static boolean hasPermission(String[] requiredPermissions, PermissionType type) {
        if (requiredPermissions.length == 0) return true;
        
        if (type == PermissionType.AND) {
            // 需要所有权限
            for (String permission : requiredPermissions) {
                if (!userPermissions.contains(permission)) {
                    return false;
                }
            }
            return true;
        } else {
            // 需要任一权限
            for (String permission : requiredPermissions) {
                if (userPermissions.contains(permission)) {
                    return true;
                }
            }
            return false;
        }
    }
    
    public static void clearPermissions() {
        userPermissions.clear();
    }
}

// 权限切面
public class PermissionAspect {
    
    public static void checkPermission(Method method, Object[] args) {
        RequirePermission permissionAnnotation = method.getAnnotation(RequirePermission.class);
        if (permissionAnnotation == null) {
            // 检查类级别的权限注解
            permissionAnnotation = method.getDeclaringClass().getAnnotation(RequirePermission.class);
        }
        
        if (permissionAnnotation == null) return;
        
        String[] requiredPermissions = permissionAnnotation.value();
        PermissionType type = permissionAnnotation.type();
        
        if (!PermissionManager.hasPermission(requiredPermissions, type)) {
            throw new SecurityException("Access denied. Required permissions: " + 
                Arrays.toString(requiredPermissions));
        }
    }
}

// 使用权限注解
public class AdminService {
    
    @RequirePermission({"USER_READ", "USER_WRITE"})
    public void createUser(String username) {
        System.out.println("Creating user: " + username);
    }
    
    @RequirePermission({"ADMIN"})
    public void deleteUser(String userId) {
        System.out.println("Deleting user: " + userId);
    }
    
    @RequirePermission(value = {"USER_READ", "ADMIN"}, type = PermissionType.OR)
    public void viewUser(String userId) {
        System.out.println("Viewing user: " + userId);
    }
    
    @RequirePermission({"SYSTEM_CONFIG"})
    public void updateSystemConfig() {
        System.out.println("Updating system configuration");
    }
}

// 测试权限控制
public class PermissionTest {
    public static void main(String[] args) {
        AdminService adminService = new AdminService();
        
        // 设置用户权限
        PermissionManager.setUserPermissions("USER_READ", "USER_WRITE");
        
        try {
            adminService.createUser("testuser"); // 成功
            adminService.viewUser("123"); // 成功
            adminService.deleteUser("123"); // 失败，需要ADMIN权限
        } catch (SecurityException e) {
            System.out.println("权限检查失败: " + e.getMessage());
        }
        
        // 更新权限
        PermissionManager.setUserPermissions("ADMIN");
        
        try {
            adminService.deleteUser("123"); // 现在可以成功
            adminService.updateSystemConfig(); // 失败，需要SYSTEM_CONFIG权限
        } catch (SecurityException e) {
            System.out.println("权限检查失败: " + e.getMessage());
        }
    }
}
```

## 6. 注解在框架中的应用

### 6.1 Spring框架注解

```java
import org.springframework.stereotype.*;
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.transaction.annotation.*;

// 组件注解
@Component
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    @Value("${app.name:DefaultApp}")
    private String appName;
    
    @Transactional
    public void saveUser(User user) {
        userRepository.save(user);
    }
    
    @Transactional(readOnly = true)
    public User findUserById(Long id) {
        return userRepository.findById(id);
    }
}

// 配置类
@Configuration
@EnableTransactionManagement
public class AppConfig {
    
    @Bean
    public DataSource dataSource() {
        // 数据源配置
        return new HikariDataSource();
    }
    
    @Bean
    public PlatformTransactionManager transactionManager(DataSource dataSource) {
        return new DataSourceTransactionManager(dataSource);
    }
}

// REST控制器
@RestController
@RequestMapping("/api/users")
@Validated
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @GetMapping("/{id}")
    public ResponseEntity<User> getUser(@PathVariable Long id) {
        User user = userService.findUserById(id);
        return ResponseEntity.ok(user);
    }
    
    @PostMapping
    public ResponseEntity<User> createUser(@Valid @RequestBody User user) {
        userService.saveUser(user);
        return ResponseEntity.ok(user);
    }
    
    @PutMapping("/{id}")
    public ResponseEntity<User> updateUser(@PathVariable Long id, @Valid @RequestBody User user) {
        user.setId(id);
        userService.saveUser(user);
        return ResponseEntity.ok(user);
    }
    
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id) {
        userService.deleteUser(id);
        return ResponseEntity.noContent().build();
    }
}
```

### 6.2 JPA注解

```java
import javax.persistence.*;
import javax.validation.constraints.*;
import java.time.LocalDateTime;
import java.util.List;

@Entity
@Table(name = "users")
public class User {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "username", nullable = false, unique = true, length = 50)
    @NotBlank(message = "用户名不能为空")
    @Size(min = 2, max = 50, message = "用户名长度必须在2-50之间")
    private String username;
    
    @Column(name = "email", nullable = false, unique = true)
    @Email(message = "邮箱格式不正确")
    @NotBlank(message = "邮箱不能为空")
    private String email;
    
    @Column(name = "password", nullable = false)
    @NotBlank(message = "密码不能为空")
    @Size(min = 6, message = "密码长度不能少于6位")
    private String password;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private UserStatus status;
    
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;
    
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Order> orders;
    
    @ManyToMany(fetch = FetchType.LAZY)
    @JoinTable(
        name = "user_roles",
        joinColumns = @JoinColumn(name = "user_id"),
        inverseJoinColumns = @JoinColumn(name = "role_id")
    )
    private List<Role> roles;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
    
    // 构造函数
    public User() {}
    
    public User(String username, String email, String password) {
        this.username = username;
        this.email = email;
        this.password = password;
        this.status = UserStatus.ACTIVE;
    }
    
    // getter和setter方法
    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
    
    public UserStatus getStatus() { return status; }
    public void setStatus(UserStatus status) { this.status = status; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
    
    public List<Order> getOrders() { return orders; }
    public void setOrders(List<Order> orders) { this.orders = orders; }
    
    public List<Role> getRoles() { return roles; }
    public void setRoles(List<Role> roles) { this.roles = roles; }
}

@Entity
@Table(name = "orders")
public class Order {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;
    
    @Column(name = "total_amount", nullable = false, precision = 10, scale = 2)
    @DecimalMin(value = "0.0", message = "订单金额不能为负数")
    private Double totalAmount;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private OrderStatus status;
    
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;
    
    // 构造函数和getter/setter方法...
}

@Entity
@Table(name = "roles")
public class Role {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "name", nullable = false, unique = true, length = 50)
    @NotBlank(message = "角色名称不能为空")
    private String name;
    
    @Column(name = "description")
    private String description;
    
    // 构造函数和getter/setter方法...
}

public enum UserStatus {
    ACTIVE, INACTIVE, LOCKED, DELETED
}

public enum OrderStatus {
    PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED
}
```

### 6.3 自定义框架注解

```java
import java.lang.annotation.*;
import java.lang.reflect.Method;
import java.util.concurrent.TimeUnit;

// 重试注解
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Retry {
    int maxAttempts() default 3;
    long delay() default 1000;
    TimeUnit timeUnit() default TimeUnit.MILLISECONDS;
    Class<? extends Throwable>[] retryFor() default {Exception.class};
    Class<? extends Throwable>[] noRetryFor() default {};
}

// 限流注解
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface RateLimit {
    int value() default 100; // 每秒允许的请求数
    String key() default ""; // 限流键
    int windowSize() default 1; // 时间窗口大小（秒）
}

// 监控注解
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Monitor {
    String name() default "";
    boolean recordArgs() default false;
    boolean recordResult() default false;
    boolean recordTime() default true;
}

// 重试切面
public class RetryAspect {
    
    public static Object handleRetry(Method method, Object[] args, Object target) throws Exception {
        Retry retryAnnotation = method.getAnnotation(Retry.class);
        if (retryAnnotation == null) {
            return method.invoke(target, args);
        }
        
        int maxAttempts = retryAnnotation.maxAttempts();
        long delay = retryAnnotation.delay();
        TimeUnit timeUnit = retryAnnotation.timeUnit();
        Class<? extends Throwable>[] retryFor = retryAnnotation.retryFor();
        Class<? extends Throwable>[] noRetryFor = retryAnnotation.noRetryFor();
        
        Exception lastException = null;
        
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return method.invoke(target, args);
            } catch (Exception e) {
                lastException = e;
                
                // 检查是否应该重试
                if (!shouldRetry(e, retryFor, noRetryFor) || attempt == maxAttempts) {
                    throw e;
                }
                
                System.out.println("Attempt " + attempt + " failed: " + e.getMessage() + 
                    ". Retrying in " + delay + " " + timeUnit.name().toLowerCase());
                
                try {
                    timeUnit.sleep(delay);
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    throw new RuntimeException("Retry interrupted", ie);
                }
            }
        }
        
        throw lastException;
    }
    
    private static boolean shouldRetry(Throwable throwable, 
                                     Class<? extends Throwable>[] retryFor,
                                     Class<? extends Throwable>[] noRetryFor) {
        // 检查不应该重试的异常
        for (Class<? extends Throwable> noRetryClass : noRetryFor) {
            if (noRetryClass.isInstance(throwable)) {
                return false;
            }
        }
        
        // 检查应该重试的异常
        for (Class<? extends Throwable> retryClass : retryFor) {
            if (retryClass.isInstance(throwable)) {
                return true;
            }
        }
        
        return false;
    }
}

// 限流切面
public class RateLimitAspect {
    private static final ConcurrentHashMap<String, RateLimiter> limiters = new ConcurrentHashMap<>();
    
    public static void checkRateLimit(Method method, Object[] args) {
        RateLimit rateLimitAnnotation = method.getAnnotation(RateLimit.class);
        if (rateLimitAnnotation == null) return;
        
        String key = generateKey(method, args, rateLimitAnnotation.key());
        int permitsPerSecond = rateLimitAnnotation.value();
        int windowSize = rateLimitAnnotation.windowSize();
        
        RateLimiter limiter = limiters.computeIfAbsent(key, 
            k -> RateLimiter.create(permitsPerSecond / (double) windowSize));
        
        if (!limiter.tryAcquire()) {
            throw new RuntimeException("Rate limit exceeded for key: " + key);
        }
    }
    
    private static String generateKey(Method method, Object[] args, String customKey) {
        if (!customKey.isEmpty()) {
            return customKey;
        }
        
        StringBuilder keyBuilder = new StringBuilder();
        keyBuilder.append(method.getDeclaringClass().getSimpleName());
        keyBuilder.append(".").append(method.getName());
        
        if (args != null && args.length > 0) {
            keyBuilder.append("(");
            for (int i = 0; i < args.length; i++) {
                if (i > 0) keyBuilder.append(",");
                keyBuilder.append(args[i]);
            }
            keyBuilder.append(")");
        }
        
        return keyBuilder.toString();
    }
}

// 监控切面
public class MonitorAspect {
    
    public static Object handleMonitor(Method method, Object[] args, Object target) throws Exception {
        Monitor monitorAnnotation = method.getAnnotation(Monitor.class);
        if (monitorAnnotation == null) {
            return method.invoke(target, args);
        }
        
        String methodName = monitorAnnotation.name().isEmpty() ? 
            method.getName() : monitorAnnotation.name();
        
        long startTime = System.currentTimeMillis();
        Object result = null;
        Exception exception = null;
        
        try {
            result = method.invoke(target, args);
            return result;
        } catch (Exception e) {
            exception = e;
            throw e;
        } finally {
            long endTime = System.currentTimeMillis();
            long executionTime = endTime - startTime;
            
            // 记录监控信息
            System.out.println("=== Method Monitor ===");
            System.out.println("Method: " + methodName);
            
            if (monitorAnnotation.recordTime()) {
                System.out.println("Execution Time: " + executionTime + "ms");
            }
            
            if (monitorAnnotation.recordArgs() && args != null) {
                System.out.println("Arguments: " + java.util.Arrays.toString(args));
            }
            
            if (monitorAnnotation.recordResult() && result != null) {
                System.out.println("Result: " + result);
            }
            
            if (exception != null) {
                System.out.println("Exception: " + exception.getMessage());
            }
            
            System.out.println("=====================");
        }
    }
}
