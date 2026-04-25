---
title: 常用Json解析器
main_color: "#1985b7ff"
categories: Java
tags:
  - 开发工具
cover: https://apifox.com/apiskills/content/images/size/w1000/2023/12/image-93.png
---


JSON 是现代软件开发中常用的数据交换格式，尤其在微服务和前后端分离的架构中更是必不可少。

本文介绍下常用的Json解析库，并记录常用API

## Jackson
当然可以！以下是关于 **Jackson** 的完整、全面的笔记，涵盖其核心概念、模块、常用注解、序列化与反序列化操作、树模型处理、自定义配置、性能优化建议以及丰富的代码示例。适用于 Java 开发者深入掌握 Jackson 框架。

---

# ✅ Jackson 全面使用指南（含代码示例）

> **当前时间：2025年8月1日**  
> 作者：Qwen  
> 适用于 Java 8+，Spring Boot / Spring MVC / 原生 Java 项目

---

## 一、什么是 Jackson？

**Jackson** 是一个高性能的 Java JSON 处理库，用于将 Java 对象与 JSON 字符串之间进行转换（即 **序列化/反序列化**）。它由 FasterXML 维护，是目前 Java 生态中最主流的 JSON 库之一。

### 🔹 主要特性：

- 高性能：处理大文件速度快，内存占用低。
- 灵活：支持注解、泛型、自定义序列化器/反序列化器。
- 功能丰富：支持流式解析（Streaming）、数据绑定（Object Mapping）、树模型（Tree Model）。
- 广泛集成：Spring、Spring Boot、Jersey 等框架默认使用 Jackson。

---

## 二、Jackson 的三大核心模块

| 模块 | 说明 |
|------|------|
| `jackson-core` | 核心底层流式 API，提供 `JsonParser` 和 `JsonGenerator`，实现高效的字节/字符级读写。 |
| `jackson-annotations` | 提供标准注解，如 `@JsonProperty`, `@JsonIgnore` 等。 |
| `jackson-databind` | 基于 `jackson-core` 和 `annotations`，提供 `ObjectMapper`，实现对象与 JSON 的自动映射。 |

> ⚠️ 注意：`jackson-databind` 依赖前两个模块，通常引入它即可自动包含其他两个。

### Maven 依赖（推荐版本）

```xml
<dependency>
    <groupId>com.fasterxml.jackson.core</groupId>
    <artifactId>jackson-databind</artifactId>
    <version>2.17.2</version> <!-- 推荐使用较新稳定版 -->
</dependency>
```

Gradle:

```groovy
implementation 'com.fasterxml.jackson.core:jackson-databind:2.17.2'
```

---

## 三、核心类：`ObjectMapper`

`ObjectMapper` 是 Jackson 最核心的类，负责：

- Java 对象 ↔ JSON 字符串 转换
- 支持泛型、集合、嵌套对象
- 可配置序列化/反序列化行为

### ✅ 创建 ObjectMapper 实例

```java
import com.fasterxml.jackson.databind.ObjectMapper;

// 通常建议作为单例使用（线程安全）
ObjectMapper mapper = new ObjectMapper();
```

> ✅ `ObjectMapper` 是线程安全的，推荐在应用中只创建一个实例并复用。

---

## 四、基本用法：序列化与反序列化

### 示例 Java 类

```java
public class User {
    private String name;
    private int age;
    private String email;
    private boolean active;

    // 构造函数
    public User() {}

    public User(String name, int age, String email, boolean active) {
        this.name = name;
        this.age = age;
        this.email = email;
        this.active = active;
    }

    // Getter 和 Setter 方法（省略，实际需生成）
    // ...
}
```

### 1️⃣ 序列化：Java 对象 → JSON 字符串

```java
User user = new User("张三", 28, "zhangsan@example.com", true);

ObjectMapper mapper = new ObjectMapper();

try {
    String json = mapper.writeValueAsString(user);
    System.out.println(json);
    // 输出: {"name":"张三","age":28,"email":"zhangsan@example.com","active":true}
} catch (Exception e) {
    e.printStackTrace();
}
```

> ✅ 也可写入文件：
```java
mapper.writeValue(new File("user.json"), user);
```

---

### 2️⃣ 反序列化：JSON 字符串 → Java 对象

```java
String json = "{\"name\":\"李四\",\"age\":30,\"email\":\"lisi@example.com\",\"active\":false}";

try {
    User user = mapper.readValue(json, User.class);
    System.out.println("Name: " + user.getName()); // 输出: 李四
} catch (Exception e) {
    e.printStackTrace();
}
```

> ✅ 从文件读取：
```java
User user = mapper.readValue(new File("user.json"), User.class);
```

---

## 五、处理集合类型（泛型支持）

由于 Java 泛型擦除，需使用 `TypeReference`

```java
String jsonArray = "[{\"name\":\"Alice\",\"age\":25},{\"name\":\"Bob\",\"age\":30}]";

try {
    List<User> users = mapper.readValue(jsonArray, new TypeReference<List<User>>() {});
    users.forEach(u -> System.out.println(u.getName()));
} catch (Exception e) {
    e.printStackTrace();
}
```

---

## 六、树模型（Tree Model）：JsonNode

当结构不确定或需要动态解析时，可用 `JsonNode`

```java
String json = "{ \"users\": [ {\"name\": \"Tom\", \"age\": 22} ] }";

try {
    JsonNode root = mapper.readTree(json);
    JsonNode usersNode = root.get("users");
    JsonNode firstUser = usersNode.get(0);
    String name = firstUser.get("name").asText();
    int age = firstUser.get("age").asInt();

    System.out.println("Name: " + name + ", Age: " + age); // Tom, 22
} catch (Exception e) {
    e.printStackTrace();
}
```

### 修改 JSON 树

```java
ObjectNode node = mapper.createObjectNode();
node.put("name", "Jerry");
node.put("age", 20);
node.put("married", false);

ArrayNode hobbies = mapper.createArrayNode();
hobbies.add("reading").add("coding");
node.set("hobbies", hobbies);

System.out.println(mapper.writeValueAsString(node));
// {"name":"Jerry","age":20,"married":false,"hobbies":["reading","coding"]}
```

---

## 七、常用注解（jackson-annotations）

| 注解 | 说明 |
|------|------|
| `@JsonProperty("custom_name")` | 指定 JSON 中的字段名 |
| `@JsonIgnore` | 忽略该字段不参与序列化/反序列化 |
| `@JsonIgnoreProperties({"field1", "field2"})` | 类级别忽略某些字段 |
| `@JsonInclude(Include.NON_NULL)` | 仅序列化非 null 字段 |
| `@JsonFormat(pattern = "yyyy-MM-dd")` | 自定义日期格式 |
| `@JsonProperty(required = true)` | 标记字段为必需（反序列化时报错） |
| `@JsonAlias({"oldName"})` | 允许反序列化时接受别名 |
| `@JsonRawValue` | 将字符串作为原始 JSON 插入 |
| `@JsonValue` | 标记方法返回值作为序列化值（如枚举） |
| `@JsonDeserialize(using = CustomDeserializer.class)` | 自定义反序列化器 |
| `@JsonSerialize(using = CustomSerializer.class)` | 自定义序列化器 |

### 示例：使用注解

```java
@JsonInclude(JsonInclude.Include.NON_NULL)
@JsonIgnoreProperties(ignoreUnknown = true) // 忽略 JSON 中不存在的字段
public class Person {
    @JsonProperty("full_name")
    private String name;

    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate birthday;

    @JsonIgnore
    private String password;

    @JsonProperty(required = true)
    private String email;

    @JsonAlias({"phone", "tel"})
    private String mobile;

    // 构造函数、getter、setter...
}
```

#### 测试注解效果

```java
Person p = new Person();
p.setName("王五");
p.setEmail("wangwu@example.com");
p.setMobile("13800138000");
p.setPassword("secret"); // 被忽略
p.setBirthday(LocalDate.of(1990, 5, 20));

String json = mapper.writeValueAsString(p);
System.out.println(json);
// 输出: {"full_name":"王五","email":"wangwu@example.com","mobile":"13800138000","birthday":"1990-05-20"}
```

---

## 八、日期处理

默认 Jackson 使用时间戳（毫秒数），通常需要改为字符串格式。

### 方式一：使用 `@JsonFormat`

```java
public class Event {
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss", timezone = "GMT+8")
    private Date createTime;

    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate eventDate;
}
```

### 方式二：全局配置 ObjectMapper

```java
ObjectMapper mapper = new ObjectMapper();

// 启用 ISO-8601 日期格式（推荐）
mapper.findAndRegisterModules(); // 自动注册 JavaTimeModule 等

// 或手动注册
SimpleModule module = new SimpleModule();
module.addSerializer(LocalDate.class, new LocalDateSerializer(DateTimeFormatter.ISO_LOCAL_DATE));
module.addDeserializer(LocalDate.class, new LocalDateDeserializer(DateTimeFormatter.ISO_LOCAL_DATE));
mapper.registerModule(module);

// 或设置默认日期格式
mapper.setDateFormat(new SimpleDateFormat("yyyy-MM-dd HH:mm:ss"));
mapper.setTimeZone(TimeZone.getTimeZone("GMT+8"));
```

> 💡 推荐使用 `JavaTimeModule` 处理 `LocalDateTime`, `ZonedDateTime` 等：

```xml
<dependency>
    <groupId>com.fasterxml.jackson.datatype</groupId>
    <artifactId>jackson-datatype-jsr310</artifactId>
    <version>2.17.2</version>
</dependency>
```

```java
mapper.registerModule(new JavaTimeModule());
mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS); // 禁用时间戳
```

---

## 九、自定义序列化与反序列化

### 示例：将布尔值序列化为 "是"/"否"

```java
public class BooleanToChineseSerializer extends JsonSerializer<Boolean> {
    @Override
    public void serialize(Boolean value, JsonGenerator gen, SerializerProvider serializers) throws IOException {
        gen.writeString(value ? "是" : "否");
    }
}

public class ChineseToBooleanDeserializer extends JsonDeserializer<Boolean> {
    @Override
    public Boolean deserialize(JsonParser p, DeserializationContext ctxt) throws IOException {
        String text = p.getValueAsString();
        return "是".equals(text);
    }
}
```

应用到字段：

```java
public class Profile {
    private String username;

    @JsonSerialize(using = BooleanToChineseSerializer.class)
    @JsonDeserialize(using = ChineseToBooleanDeserializer.class)
    private Boolean vip;

    // getter/setter
}
```

测试：

```java
Profile p = new Profile();
p.setUsername("user1");
p.setVip(true);

String json = mapper.writeValueAsString(p); // {"username":"user1","vip":"是"}

Profile p2 = mapper.readValue(json, Profile.class); // vip = true
```

---

## 十、配置 ObjectMapper（常用设置）

```java
ObjectMapper mapper = new ObjectMapper();

// 1. 忽略未知字段（防止反序列化报错）
mapper.configure(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES, false);

// 2. 允许单个值作为数组（如字符串转 List）
mapper.configure(DeserializationFeature.ACCEPT_SINGLE_VALUE_AS_ARRAY, true);

// 3. 空值处理
mapper.setSerializationInclusion(JsonInclude.Include.NON_NULL); // 不序列化 null 字段
mapper.setSerializationInclusion(JsonInclude.Include.NON_EMPTY); // 不序列化空集合/字符串

// 4. 缩进输出（美化）
mapper.enable(SerializationFeature.INDENT_OUTPUT);

// 5. 禁用写入日期为时间戳
mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

// 6. 注册模块（如 Java 8 时间）
mapper.registerModule(new JavaTimeModule());

// 7. 自定义属性命名策略（如驼峰转下划线）
mapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
```

---

## 十一、性能优化建议

| 优化项 | 建议 |
|-------|------|
| ✅ 复用 ObjectMapper | 它是线程安全的，避免重复创建 |
| ✅ 使用流式 API 处理大文件 | `JsonParser` 逐条解析，避免 OOM |
| ✅ 关闭不需要的功能 | 如 `FAIL_ON_UNKNOWN_PROPERTIES` |
| ✅ 使用 `@JsonView` 或 DTO 控制输出字段 | 减少网络传输 |
| ✅ 启用 `jackson-module-afterburner`（高级） | 通过字节码生成提升性能 |

---

## 十二、常见问题与解决方案

### ❌ 报错：`No suitable constructor found`
> 原因：类没有无参构造函数或字段无 setter。

✅ 解决：添加 `@NoArgsConstructor` 或提供默认构造函数。

### ❌ 报错：`Can not construct instance of ...`
> 原因：无法反序列化抽象类或接口。

✅ 解决：使用 `@JsonDeserialize(as = ConcreteClass.class)` 指定实现类。

### ❌ 日期格式错误
✅ 解决：注册 `JavaTimeModule` 并禁用时间戳。

### ❌ 字段名大小写不匹配
✅ 解决：使用 `@JsonProperty` 或设置命名策略。

---

## 十三、与 Gson 对比

| 特性 | Jackson | Gson |
|------|--------|------|
| 性能 | 更快（尤其大文件） | 稍慢 |
| 内存占用 | 更低 | 较高 |
| 功能 | 更丰富（注解、模块化） | 简洁易用 |
| Spring 集成 | 默认 | 需配置 |
| 泛型支持 | `TypeReference` | `TypeToken` |
| 自定义序列化 | 灵活 | 简单 |

> ✅ 推荐：企业级项目首选 Jackson；小型项目可选 Gson。

---

## 十四、Spring Boot 中的 Jackson 配置

在 `application.yml` 中配置：

```yaml
spring:
  jackson:
    date-format: yyyy-MM-dd HH:mm:ss
    time-zone: GMT+8
    default-property-inclusion: non_null
    serialization:
      write-dates-as-timestamps: false
    deserialization:
      fail-on-unknown-properties: false
```

或通过 `@Configuration` 定制：

```java
@Configuration
public class JacksonConfig {
    @Bean
    @Primary
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.registerModule(new JavaTimeModule());
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        return mapper;
    }
}
```

---

## ✅ 总结

| 能力 | Jackson 是否支持 |
|------|----------------|
| 对象绑定 | ✅ `ObjectMapper` |
| 树模型 | ✅ `JsonNode` |
| 流式处理 | ✅ `JsonParser/Generator` |
| 注解配置 | ✅ 丰富注解 |
| 自定义序列化 | ✅ 支持 |
| 泛型处理 | ✅ `TypeReference` |
| 日期处理 | ✅ `JavaTimeModule` |
| 高性能 | ✅ 优于 Gson |
| Spring 集成 | ✅ 默认 |

---

📌 **最佳实践建议**：

1. 使用 `ObjectMapper` 单例。
2. 处理时间使用 `JavaTimeModule`。
3. 忽略未知字段避免报错。
4. 使用 `@JsonInclude` 减少无效数据传输。
5. 大文件使用流式 API。
6. 合理使用注解控制序列化行为。

---

📚 **官方文档**：
- https://github.com/FasterXML/jackson
- https://fasterxml.github.io/jackson-databind/javadoc/2.17/

---


## FastJson2
当然可以！以下是按照 **Jackson 笔记的格式** 编写的 **Fastjson2 全面使用指南**，内容全面、结构清晰，并包含丰富的代码示例，适用于 Java 开发者深入掌握 Fastjson2。

---

# ✅ Fastjson2 全面使用指南（含代码示例）

> **当前时间：2025年8月1日**  
> 作者：Qwen  
> 适用于 Java 8+，Spring Boot / 原生 Java 项目  
> 由 Alibaba 开源，Fastjson 的升级版

---

## 一、什么是 Fastjson2？

**Fastjson2** 是 Alibaba 开源的高性能 Java JSON 库 `Fastjson` 的 **重构与升级版本**，在性能、安全性、功能扩展性和标准兼容性上均有显著提升。它支持将 Java 对象与 JSON 字符串之间进行高效转换（序列化/反序列化），并广泛应用于国内 Java 生态系统中。

### 🔹 主要特性：

- ⚡ **极致性能**：基于 ASM 字节码技术生成序列化器，速度远超 Jackson、Gson。
- 🔐 **高安全性**：修复 Fastjson v1 中大量反序列化漏洞，增强类型校验。
- 🧩 **功能丰富**：支持流式处理、泛型、日期格式、自定义序列化、字段过滤等。
- 📦 **模块化设计**：核心与扩展分离，支持 AOT（提前编译）和 GraalVM。
- 🔄 **兼容 Fastjson v1 API**：大部分 API 兼容，便于迁移。

> ⚠️ 注意：Fastjson2 不再维护 v1 版本，推荐新项目使用 `fastjson2`，旧项目建议升级。

---

## 二、Fastjson2 的核心模块

| 模块 | 说明 |
|------|------|
| `fastjson2` | 核心模块，包含 `JSON`、`JSONObject`、`JSONArray`、`JSONWriter`、`JSONReader` 等核心类。 |
| `fastjson2-extension` | 扩展模块，支持 Spring、JAXB、Kotlin 等集成。 |
| `fastjson2-processor` | 注解处理器，用于编译期生成序列化代码（提升运行时性能）。 |

> 💡 大多数场景只需引入核心模块即可。

### Maven 依赖（推荐版本）

```xml
<dependency>
    <groupId>com.alibaba.fastjson2</groupId>
    <artifactId>fastjson2</artifactId>
    <version>2.0.45</version> <!-- 推荐使用最新稳定版 -->
</dependency>
```

Gradle:

```groovy
implementation 'com.alibaba.fastjson2:fastjson2:2.0.45'
```

> ✅ 注意：包名为 `com.alibaba.fastjson2`，与 v1 的 `com.alibaba.fastjson` 不同，可共存。

---

## 三、核心类：`JSON` 与 `JSONObject` / `JSONArray`

Fastjson2 的核心入口是 `JSON` 类，提供静态方法进行序列化与反序列化。

### ✅ 常用核心类：

- `JSON`：主工具类，提供 `parseObject`, `parseArray`, `toJSONString` 等方法。
- `JSONObject`：代表一个 JSON 对象，类似 `Map<String, Object>`。
- `JSONArray`：代表一个 JSON 数组，类似 `List<Object>`。
- `JSONWriter` / `JSONReader`：流式 API，用于高性能读写大文件。

---

## 四、基本用法：序列化与反序列化

### 示例 Java 类

```java
public class User {
    private String name;
    private int age;
    private String email;
    private boolean active;

    public User() {}

    public User(String name, int age, String email, boolean active) {
        this.name = name;
        this.age = age;
        this.email = email;
        this.active = active;
    }

    // Getter 和 Setter 方法（省略，实际需生成）
    // ...
}
```

### 1️⃣ 序列化：Java 对象 → JSON 字符串

```java
User user = new User("张三", 28, "zhangsan@example.com", true);

String json = JSON.toJSONString(user);
System.out.println(json);
// 输出: {"active":true,"age":28,"email":"zhangsan@example.com","name":"张三"}
```

> ✅ 支持格式化输出：
```java
String prettyJson = JSON.toJSONString(user, 
    JSONWriter.Feature.PrettyFormat, 
    JSONWriter.Feature.WriteMapNullValue);
System.out.println(prettyJson);
```

---

### 2️⃣ 反序列化：JSON 字符串 → Java 对象

```java
String json = "{\"name\":\"李四\",\"age\":30,\"email\":\"lisi@example.com\",\"active\":false}";

User user = JSON.parseObject(json, User.class);
System.out.println("Name: " + user.getName()); // 输出: 李四
```

> ✅ 从文件读取（需自行读取字符串）：
```java
String jsonStr = new String(Files.readAllBytes(Paths.get("user.json")));
User user = JSON.parseObject(jsonStr, User.class);
```

---

## 五、处理集合类型（泛型支持）

由于 Java 泛型擦除，需使用 `TypeReference`

```java
import com.alibaba.fastjson2.TypeReference;

String jsonArray = "[{\"name\":\"Alice\",\"age\":25},{\"name\":\"Bob\",\"age\":30}]";

TypeReference<List<User>> typeRef = new TypeReference<List<User>>() {};
List<User> users = JSON.parseObject(jsonArray, typeRef);

users.forEach(u -> System.out.println(u.getName()));
```

---

## 六、树模型：JSONObject 与 JSONArray

Fastjson2 提供类似 Jackson 的树模型，适合动态解析。

```java
String json = "{ \"users\": [ {\"name\": \"Tom\", \"age\": 22} ] }";

JSONObject root = JSON.parseObject(json);
JSONArray users = root.getJSONArray("users");
JSONObject firstUser = users.getJSONObject(0);

String name = firstUser.getString("name");
int age = firstUser.getIntValue("age");

System.out.println("Name: " + name + ", Age: " + age); // Tom, 22
```

### 构建 JSON 树

```java
JSONObject user = new JSONObject();
user.put("name", "Jerry");
user.put("age", 20);
user.put("married", false);

JSONArray hobbies = new JSONArray();
hobbies.add("reading");
hobbies.add("coding");
user.put("hobbies", hobbies);

System.out.println(user.toJSONString(JSONWriter.Feature.PrettyFormat));
```

---

## 七、常用注解（fastjson2-annotations）

| 注解 | 说明 |
|------|------|
| `@JSONField(name = "custom_name")` | 指定 JSON 中的字段名 |
| `@JSONField(serialize = false)` | 忽略该字段序列化 |
| `@JSONField(deserialize = false)` | 忽略该字段反序列化 |
| `@JSONField(format = "yyyy-MM-dd")` | 自定义日期格式 |
| `@JSONField(alternateNames = {"oldName"})` | 反序列化时接受别名 |
| `@JSONField(ordinal = 1)` | 控制字段输出顺序 |
| `@JSONType(ignores = {"field"})` | 类级别忽略字段 |
| `@JSONCreator` | 指定构造函数或静态工厂方法用于反序列化 |

### 示例：使用注解

```java
@JSONType(ignores = {"password"})
public class Person {
    @JSONField(name = "full_name")
    private String name;

    @JSONField(format = "yyyy-MM-dd")
    private LocalDate birthday;

    private String password; // 被 @JSONType 忽略

    @JSONField(alternateNames = {"phone", "tel"})
    private String mobile;

    // 构造函数、getter、setter...
}
```

#### 测试注解效果

```java
Person p = new Person();
p.setName("王五");
p.setMobile("13800138000");
p.setPassword("secret");
p.setBirthday(LocalDate.of(1990, 5, 20));

String json = JSON.toJSONString(p, JSONWriter.Feature.PrettyFormat);
System.out.println(json);
// 输出不包含 password 字段
```

---

## 八、日期处理

Fastjson2 支持多种日期类型，默认支持 ISO 格式。

### 方式一：使用 `@JSONField(format = "...")`

```java
public class Event {
    @JSONField(format = "yyyy-MM-dd HH:mm:ss")
    private Date createTime;

    @JSONField(format = "yyyy-MM-dd")
    private LocalDate eventDate;
}
```

### 方式二：全局配置

```java
JSONWriter.Feature[] writerFeatures = {
    JSONWriter.Feature.WriteDateUseDateFormat,
    JSONWriter.Feature.PrettyFormat
};

// 全局设置日期格式
JSON.setDateFormat("yyyy-MM-dd HH:mm:ss");

String json = JSON.toJSONString(event, writerFeatures);
```

> ✅ 默认支持 `java.time` 类型（Java 8+），无需额外模块。

---

## 九、自定义序列化与反序列化

### 实现 `ObjectSerializer` 和 `ObjectDeserializer`

```java
public class BooleanToChineseSerializer implements ObjectSerializer {
    @Override
    public void write(JSONWriter writer, Object object, Object fieldName, Type fieldType, long features) {
        Boolean value = (Boolean) object;
        writer.writeString(value ? "是" : "否");
    }
}

public class ChineseToBooleanDeserializer implements ObjectDeserializer {
    @Override
    public <T> T deserialize(JSONReader reader, Type fieldType, Object fieldName) {
        String text = reader.readString();
        return (T) ("是".equals(text) ? Boolean.TRUE : Boolean.FALSE);
    }
}
```

注册并使用：

```java
// 注册自定义序列化器
JSON.register(User.class, new BooleanToChineseSerializer(), new ChineseToBooleanDeserializer());

// 使用
User user = new User("test", 25, "a@b.com", true);
String json = JSON.toJSONString(user); // "active":"是"
User parsed = JSON.parseObject(json, User.class); // active = true
```

---

## 十、配置与特性（Features）

Fastjson2 使用 `JSONWriter.Feature` 和 `JSONReader.Feature` 控制行为。

### 常用写入特性（序列化）

```java
JSON.toJSONString(obj,
    JSONWriter.Feature.PrettyFormat,           // 格式化输出
    JSONWriter.Feature.WriteMapNullValue,      // 输出 null 值
    JSONWriter.Feature.IgnoreErrorGetter,      // 忽略 getter 异常
    JSONWriter.Feature.WriteClassName          // 写入类型信息（慎用）
);
```

### 常用读取特性（反序列化）

```java
JSON.parseObject(json, User.class,
    JSONReader.Feature.SupportAutoType,        // 支持自动类型识别（需谨慎）
    JSONReader.Feature.IgnoreSetNullValue      // 忽略 null 赋值
);
```

> 🔐 安全建议：禁用 `SupportAutoType` 或设置白名单防止反序列化攻击。

---

## 十一、性能优化建议

| 优化项 | 建议 |
|-------|------|
| ✅ 使用 `JSONWriter.Feature` 控制输出 | 减少冗余数据 |
| ✅ 复用 `JSONReader` / `JSONWriter` | 处理大文件时避免频繁创建 |
| ✅ 启用编译期代码生成 | 使用 `fastjson2-processor` 生成序列化代码 |
| ✅ 避免使用 `WriteClassName` | 增加安全风险和体积 |
| ✅ 使用流式 API 处理大文件 | 防止 OOM |

### 流式处理大 JSON 文件

```java
try (JSONReader reader = JSONReader.of(new FileReader("large.json"))) {
    reader.startArray(); // 假设是数组
    while (reader.hasNext()) {
        User user = reader.read(User.class);
        // 处理单个对象
        System.out.println(user.getName());
    }
}
```

---

## 十二、常见问题与解决方案

### ❌ 报错：`can not cast to ...`
> 原因：类型不匹配或泛型未正确传递。

✅ 解决：使用 `TypeReference` 明确泛型类型。

### ❌ 字段为 null 时不输出
✅ 解决：添加 `JSONWriter.Feature.WriteMapNullValue`。

### ❌ 日期格式不符合预期
✅ 解决：使用 `@JSONField(format = "...")` 或全局设置 `JSON.setDateFormat()`。

### ❌ 反序列化失败，字段名大小写不匹配
✅ 解决：使用 `@JSONField(name = "...")` 或 `alternateNames`。

---

## 十三、与 Jackson 对比

| 特性 | Fastjson2 | Jackson |
|------|----------|--------|
| 性能 | ⚡ 极致（ASM 字节码生成） | 高（C++ 优化） |
| 内存占用 | 低 | 低 |
| 功能 | 丰富，国内生态强 | 更标准，国际主流 |
| 安全性 | v2 版本已大幅增强 | 高 |
| Spring 集成 | 需配置 | 默认 |
| 泛型支持 | `TypeReference` | `TypeReference` |
| 自定义序列化 | 灵活 | 灵活 |
| 社区支持 | 国内活跃 | 国际广泛 |

> ✅ 推荐：国内项目、追求极致性能 → Fastjson2；国际化、标准兼容 → Jackson。

---

## 十四、Spring Boot 中的 Fastjson2 配置

### 添加依赖

```xml
<dependency>
    <groupId>com.alibaba.fastjson2</groupId>
    <artifactId>fastjson2-extension-spring6</artifactId>
    <version>2.0.45</version>
</dependency>
```

### 配置 `HttpMessageConverter`

```java
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {
    @Override
    public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
        FastJson2HttpMessageConverter converter = new FastJson2HttpMessageConverter();
        
        FastJsonConfig config = new FastJsonConfig();
        config.setWriterFeatures(
            JSONWriter.Feature.WriteMapNullValue,
            JSONWriter.Feature.PrettyFormat
        );
        config.setDateFormat("yyyy-MM-dd HH:mm:ss");
        
        converter.setFastJsonConfig(config);
        converters.add(0, converter); // 置于首位
    }
}
```

---

## ✅ 总结

| 能力 | Fastjson2 是否支持 |
|------|------------------|
| 对象绑定 | ✅ `JSON.parseObject` |
| 树模型 | ✅ `JSONObject/JSONArray` |
| 流式处理 | ✅ `JSONReader/Writer` |
| 注解配置 | ✅ `@JSONField` 等 |
| 自定义序列化 | ✅ 支持 |
| 泛型处理 | ✅ `TypeReference` |
| 日期处理 | ✅ 内置支持 |
| 高性能 | ✅ 行业领先 |
| Spring 集成 | ✅ 支持 |

---

📌 **最佳实践建议**：

1. 使用 `fastjson2` 替代 `fastjson` v1。
2. 新项目优先考虑性能与安全。
3. 使用 `TypeReference` 处理泛型。
4. 避免开启 `WriteClassName` 和 `SupportAutoType` 除非必要。
5. 大文件使用流式 API。
6. 合理使用 `Feature` 控制输出行为。

---

📚 **官方文档**：
- https://github.com/alibaba/fastjson2
- https://fastjson.dev/

---


## GJson

当然可以！以下是按照 **Jackson 和 Fastjson2 笔记的统一格式** 编写的 **Gson（Google Gson）全面使用指南**，内容全面、结构清晰，并包含丰富的代码示例，适合 Java 开发者系统掌握 Gson 框架。

---

# ✅ Gson 全面使用指南（含代码示例）

> **当前时间：2025年8月1日**  
> 作者：Qwen  
> 适用于 Java 8+，Android / Spring / 原生 Java 项目  
> 由 Google 开源，轻量级 JSON 处理库

---

## 一、什么是 Gson？

**Gson** 是 Google 开源的一款轻量级 Java JSON 库，用于将 Java 对象与 JSON 字符串之间进行序列化和反序列化。它设计简洁、API 易用，特别适合 Android 开发和中小型 Java 项目。

### 🔹 主要特性：

- 🧼 **简单易用**：无需注解即可自动映射，学习成本低。
- 📦 **无依赖**：jar 包小（约 300KB），不依赖其他库。
- 💡 **支持复杂类型**：泛型、嵌套类、集合、枚举等。
- 🔧 **可扩展性强**：支持自定义序列化器/反序列化器。
- 🔄 **支持流式处理**：`JsonReader` 和 `JsonWriter` 用于高效读写大文件。
- ✅ **空安全**：对 `null` 值处理友好。

> ⚠️ 注意：Gson 性能略低于 Jackson 和 Fastjson2，但在大多数场景下足够高效。

---

## 二、Gson 的核心模块

| 模块 | 说明 |
|------|------|
| `gson` | 核心模块，包含 `Gson`, `GsonBuilder`, `JsonElement`, `TypeToken` 等核心类。 |

> ✅ Gson 只有一个核心 jar 包，无额外依赖。

### Maven 依赖（推荐版本）

```xml
<dependency>
    <groupId>com.google.code.gson</groupId>
    <artifactId>gson</artifactId>
    <version>2.10.1</version> <!-- 推荐使用最新稳定版 -->
</dependency>
```

Gradle:

```groovy
implementation 'com.google.code.gson:gson:2.10.1'
```

---

## 三、核心类：`Gson` 与 `GsonBuilder`

- `Gson`：主类，提供 `toJson()` 和 `fromJson()` 方法。
- `GsonBuilder`：用于构建自定义配置的 `Gson` 实例（推荐使用）。

> ✅ `Gson` 实例是线程安全的，建议作为单例复用。

### 创建 Gson 实例

```java
// 简单实例
Gson gson = new Gson();

// 推荐：使用 GsonBuilder 自定义配置
Gson gson = new GsonBuilder()
    .setPrettyPrinting()                    // 格式化输出
    .serializeNulls()                       // 序列化 null 字段
    .setDateFormat("yyyy-MM-dd HH:mm:ss")   // 日期格式
    .create();
```

---

## 四、基本用法：序列化与反序列化

### 示例 Java 类

```java
public class User {
    private String name;
    private int age;
    private String email;
    private boolean active;

    public User() {}

    public User(String name, int age, String email, boolean active) {
        this.name = name;
        this.age = age;
        this.email = email;
        this.active = active;
    }

    // Getter 和 Setter 方法（省略）
}
```

### 1️⃣ 序列化：Java 对象 → JSON 字符串

```java
User user = new User("张三", 28, "zhangsan@example.com", true);

Gson gson = new GsonBuilder().setPrettyPrinting().create();
String json = gson.toJson(user);

System.out.println(json);
/*
输出:
{
  "name": "张三",
  "age": 28,
  "email": "zhangsan@example.com",
  "active": true
}
*/
```

> ✅ 写入文件：
```java
try (FileWriter writer = new FileWriter("user.json")) {
    gson.toJson(user, writer);
}
```

---

### 2️⃣ 反序列化：JSON 字符串 → Java 对象

```java
String json = "{ \"name\": \"李四\", \"age\": 30, \"email\": \"lisi@example.com\", \"active\": false }";

User user = gson.fromJson(json, User.class);
System.out.println("Name: " + user.getName()); // 输出: 李四
```

> ✅ 从文件读取：
```java
User user = gson.fromJson(new FileReader("user.json"), User.class);
```

---

## 五、处理集合类型（泛型支持）

由于 Java 泛型擦除，需使用 `TypeToken`

```java
import com.google.gson.reflect.TypeToken;

String jsonArray = "[{\"name\":\"Alice\",\"age\":25},{\"name\":\"Bob\",\"age\":30}]";

TypeToken<List<User>> typeToken = new TypeToken<List<User>>() {};
List<User> users = gson.fromJson(jsonArray, typeToken.getType());

users.forEach(u -> System.out.println(u.getName()));
```

---

## 六、树模型：JsonElement、JsonObject、JsonArray

Gson 提供完整的树模型 API，适合动态解析或构建 JSON。

```java
String json = "{ \"users\": [ {\"name\": \"Tom\", \"age\": 22} ] }";

JsonElement root = JsonParser.parseString(json);
JsonObject rootObj = root.getAsJsonObject();

JsonArray users = rootObj.getAsJsonArray("users");
JsonObject firstUser = users.get(0).getAsJsonObject();

String name = firstUser.get("name").getAsString();
int age = firstUser.get("age").getAsInt();

System.out.println("Name: " + name + ", Age: " + age); // Tom, 22
```

### 构建 JSON 树

```java
JsonObject user = new JsonObject();
user.addProperty("name", "Jerry");
user.addProperty("age", 20);
user.addProperty("married", false);

JsonArray hobbies = new JsonArray();
hobbies.add("reading");
hobbies.add("coding");
user.add("hobbies", hobbies);

System.out.println(gson.toJson(user));
// {"name":"Jerry","age":20,"married":false,"hobbies":["reading","coding"]}
```

---

## 七、常用配置与特性（通过 GsonBuilder）

Gson 使用 `GsonBuilder` 进行配置，无注解驱动。

| 配置方法 | 说明 |
|--------|------|
| `.setPrettyPrinting()` | 格式化输出（缩进） |
| `.serializeNulls()` | 序列化 null 字段（默认跳过） |
| `.excludeFieldsWithoutExposeAnnotation()` | 仅序列化 `@Expose` 标记的字段 |
| `.setDateFormat("yyyy-MM-dd")` | 全局日期格式 |
| `.enableComplexMapKeySerialization()` | 支持 Map 的复杂 key |
| `.setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)` | 字段命名策略（如驼峰转下划线） |

### 示例：配置 Gson

```java
Gson gson = new GsonBuilder()
    .setPrettyPrinting()
    .serializeNulls()
    .setFieldNamingPolicy(FieldNamingPolicy.LOWER_CASE_WITH_UNDERSCORES)
    .setDateFormat("yyyy-MM-dd HH:mm:ss")
    .create();
```

### 使用 `@Expose` 控制字段可见性

```java
public class User {
    @Expose
    private String name;

    @Expose(serialize = false, deserialize = true)
    private String password; // 反序列化时读取，序列化时不输出

    private String email; // 未标记 @Expose，且使用 excludeFieldsWithoutExposeAnnotation 时被忽略
}
```

启用 `@Expose`：

```java
Gson gson = new GsonBuilder()
    .excludeFieldsWithoutExposeAnnotation()
    .create();
```

---

## 八、日期处理

Gson 支持 `java.util.Date`、`java.sql.Date` 等，需手动设置格式。

```java
Gson gson = new GsonBuilder()
    .setDateFormat("yyyy-MM-dd HH:mm:ss")
    .create();

// 对于 Java 8 时间（LocalDateTime 等），需注册 TypeAdapter
// 见下文自定义序列化
```

---

## 九、自定义序列化与反序列化

### 实现 `JsonSerializer` 和 `JsonDeserializer`

```java
public class BooleanToChineseSerializer implements JsonSerializer<Boolean> {
    @Override
    public JsonElement serialize(Boolean src, Type typeOfSrc, JsonSerializationContext context) {
        return new JsonPrimitive(src ? "是" : "否");
    }
}

public class ChineseToBooleanDeserializer implements JsonDeserializer<Boolean> {
    @Override
    public Boolean deserialize(JsonElement json, Type typeOfT, JsonDeserializationContext context) {
        return "是".equals(json.getAsString());
    }
}
```

注册并使用：

```java
Gson gson = new GsonBuilder()
    .registerTypeAdapter(Boolean.class, new BooleanToChineseSerializer())
    .registerTypeAdapter(Boolean.class, new ChineseToBooleanDeserializer())
    .setPrettyPrinting()
    .create();

User user = new User("test", 25, "a@b.com", true);
String json = gson.toJson(user); // "active":"是"
User parsed = gson.fromJson(json, User.class); // active = true
```

### 处理 Java 8 时间类型

```java
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class LocalDateTimeAdapter {
    private static final DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    public static class Serializer implements JsonSerializer<LocalDateTime> {
        @Override
        public JsonElement serialize(LocalDateTime src, Type typeOfSrc, JsonSerializationContext context) {
            return new JsonPrimitive(formatter.format(src));
        }
    }

    public static class Deserializer implements JsonDeserializer<LocalDateTime> {
        @Override
        public LocalDateTime deserialize(JsonElement json, Type typeOfT, JsonDeserializationContext context) {
            return LocalDateTime.parse(json.getAsString(), formatter);
        }
    }
}
```

注册：

```java
Gson gson = new GsonBuilder()
    .registerTypeAdapter(LocalDateTime.class, new LocalDateTimeAdapter.Serializer())
    .registerTypeAdapter(LocalDateTime.class, new LocalDateTimeAdapter.Deserializer())
    .create();
```

---

## 十、性能优化建议

| 优化项 | 建议 |
|-------|------|
| ✅ 复用 `Gson` 实例 | 线程安全，避免重复创建 |
| ✅ 避免频繁创建 `TypeToken` | 可缓存常用类型 |
| ✅ 使用流式 API 处理大文件 | `JsonReader` 逐条解析 |
| ✅ 合理使用 `@Expose` | 减少无效字段传输 |
| ✅ 禁用 `serializeNulls` | 减小 JSON 体积（除非必要） |

### 流式处理大 JSON 文件

```java
try (JsonReader reader = new JsonReader(new FileReader("large.json"))) {
    reader.beginArray();
    while (reader.hasNext()) {
        User user = gson.fromJson(reader, User.class);
        // 处理单个对象
        System.out.println(user.getName());
    }
    reader.endArray();
}
```

---

## 十一、常见问题与解决方案

### ❌ 字段为 null 时不输出
✅ 解决：调用 `.serializeNulls()`。

### ❌ 静态字段被序列化
✅ 解决：Gson 默认跳过 `transient` 和 `static` 字段，无需处理。

### ❌ 泛型反序列化失败
✅ 解决：必须使用 `TypeToken`。

### ❌ 日期格式错误
✅ 解决：使用 `setDateFormat()` 或自定义 `TypeAdapter`。

---

## 十二、与 Jackson / Fastjson2 对比

| 特性 | Gson | Jackson | Fastjson2 |
|------|------|--------|----------|
| 性能 | 中等 | 高 | ⚡ 极高 |
| 内存占用 | 低 | 低 | 低 |
| 功能丰富度 | 简洁 | 丰富 | 丰富 |
| 学习成本 | 低 | 中 | 中 |
| 注解支持 | 少（`@Expose`） | 丰富 | 丰富 |
| 泛型支持 | `TypeToken` | `TypeReference` | `TypeReference` |
| Spring 集成 | 需配置 | 默认 | 需配置 |
| Android 友好度 | ✅ 极佳 | 可用 | 可用 |

> ✅ 推荐：
> - Android 项目 → **Gson**
> - 企业级 Java → **Jackson**
> - 高性能服务 → **Fastjson2**

---

## 十三、Spring Boot 中的 Gson 配置

### 添加依赖

```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
</dependency>
<dependency>
    <groupId>com.google.code.gson</groupId>
    <artifactId>gson</artifactId>
</dependency>
```

Spring Boot 会自动检测到 Gson 并使用它替代 Jackson（如果 Jackson 不存在）。

### 手动配置 `HttpMessageConverter`

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
        Gson gson = new GsonBuilder()
            .setPrettyPrinting()
            .serializeNulls()
            .create();

        GsonHttpMessageConverter converter = new GsonHttpMessageConverter();
        converter.setGson(gson);
        converters.add(0, converter);
    }
}
```

---

## ✅ 总结

| 能力 | Gson 是否支持 |
|------|--------------|
| 对象绑定 | ✅ `gson.toJson/fromJson` |
| 树模型 | ✅ `JsonElement` 层次结构 |
| 流式处理 | ✅ `JsonReader/Writer` |
| 自定义序列化 | ✅ `TypeAdapter` / `Serializer` |
| 泛型处理 | ✅ `TypeToken` |
| 日期处理 | ✅ 支持，可扩展 |
| 空安全 | ✅ 友好处理 null |
| Android 友好 | ✅ 官方推荐 |
| Spring 集成 | ✅ 支持 |

---

📌 **最佳实践建议**：

1. 使用 `GsonBuilder` 创建配置化实例。
2. 处理泛型务必使用 `TypeToken`。
3. 大文件使用 `JsonReader` 流式解析。
4. Android 项目优先选择 Gson。
5. 日期类型建议注册 `TypeAdapter`。
6. 合理控制 `null` 字段输出。

---

📚 **官方文档**：
- https://github.com/google/gson
- https://sites.google.com/site/gson/gson-user-guide

---
