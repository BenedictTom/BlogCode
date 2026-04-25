---
title: Spring-Doc
main_color: "#1881a2ff"
categories: Swagger
tags:
  - Swagger
cover: https://free.picui.cn/free/2026/03/28/69c74fc1a9b96.png
---

# Spring-Doc 完整指南

## 概述

Spring-Doc 是一个用于生成 API 文档的工具，它基于 Springfox 和 Swagger UI。它提供了一种简单的方式来自动生成 RESTful API 的文档，并且支持 OpenAPI 3.0 标准。

## 版本依赖

### Maven 依赖

```xml
<dependency>
    <groupId>org.springdoc</groupId>
    <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
    <version>2.2.0</version>
</dependency>
```

### Gradle 依赖

```gradle
implementation 'org.springdoc:springdoc-openapi-starter-webmvc-ui:2.2.0'
```

## 基本配置

### 配置文件 (application.yml)

```yaml
springdoc:
  api-docs:
    path: /api-docs
  swagger-ui:
    path: /swagger-ui.html
    tags-sorter: alpha
    operations-sorter: alpha
  packages-to-scan: com.example.controller
  paths-to-match: /api/**
```

### 配置类

```java
@Configuration
public class OpenApiConfig {
    
    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("API 文档")
                        .version("1.0")
                        .description("Spring Boot 应用 API 文档")
                        .contact(new Contact()
                                .name("开发团队")
                                .email("dev@example.com")))
                .servers(Arrays.asList(
                        new Server().url("http://localhost:8080").description("本地环境"),
                        new Server().url("https://api.example.com").description("生产环境")
                ));
    }
}
```

## 核心注解

### @Tag - 控制器标签

```java
@Tag(name = "用户管理", description = "用户相关的所有操作")
@RestController
@RequestMapping("/api/users")
public class UserController {
    // 控制器方法
}
```

### @Operation - 操作描述

```java
@Operation(
    summary = "获取用户信息",
    description = "根据用户ID获取用户的详细信息",
    responses = {
        @ApiResponse(responseCode = "200", description = "成功获取用户信息"),
        @ApiResponse(responseCode = "404", description = "用户不存在"),
        @ApiResponse(responseCode = "500", description = "服务器内部错误")
    }
)
@GetMapping("/{id}")
public ResponseEntity<User> getUserById(@PathVariable Long id) {
    // 方法实现
}
```

### @Parameter - 参数描述

```java
@Operation(summary = "创建用户")
@PostMapping
public ResponseEntity<User> createUser(
    @Parameter(description = "用户信息", required = true) @RequestBody User user,
    @Parameter(description = "用户类型", example = "VIP") @RequestParam String type
) {
    // 方法实现
}
```

### @Schema - 模型属性描述

```java
@Schema(description = "用户实体")
public class User {
    
    @Schema(description = "用户ID", example = "1")
    private Long id;
    
    @Schema(description = "用户名", example = "john_doe", minLength = 3, maxLength = 50)
    @NotBlank(message = "用户名不能为空")
    private String username;
    
    @Schema(description = "邮箱地址", example = "john@example.com", format = "email")
    @Email(message = "邮箱格式不正确")
    private String email;
    
    @Schema(description = "年龄", example = "25", minimum = "18", maximum = "100")
    @Min(value = 18, message = "年龄必须大于18岁")
    @Max(value = 100, message = "年龄不能超过100岁")
    private Integer age;
    
    // getters and setters
}
```

## 完整示例

### 控制器示例

```java
@Tag(name = "用户管理", description = "用户相关的所有操作")
@RestController
@RequestMapping("/api/users")
@Validated
public class UserController {
    
    @Operation(
        summary = "获取所有用户",
        description = "分页获取用户列表，支持按用户名和邮箱搜索"
    )
    @ApiResponses({
        @ApiResponse(responseCode = "200", description = "成功获取用户列表"),
        @ApiResponse(responseCode = "400", description = "请求参数错误"),
        @ApiResponse(responseCode = "500", description = "服务器内部错误")
    })
    @GetMapping
    public ResponseEntity<Page<User>> getUsers(
        @Parameter(description = "页码", example = "0") @RequestParam(defaultValue = "0") int page,
        @Parameter(description = "每页大小", example = "10") @RequestParam(defaultValue = "10") int size,
        @Parameter(description = "用户名搜索") @RequestParam(required = false) String username,
        @Parameter(description = "邮箱搜索") @RequestParam(required = false) String email
    ) {
        // 实现逻辑
        return ResponseEntity.ok(userService.getUsers(page, size, username, email));
    }
    
    @Operation(
        summary = "根据ID获取用户",
        description = "根据用户ID获取用户的详细信息"
    )
    @GetMapping("/{id}")
    public ResponseEntity<User> getUserById(
        @Parameter(description = "用户ID", example = "1") @PathVariable Long id
    ) {
        User user = userService.getUserById(id);
        return ResponseEntity.ok(user);
    }
    
    @Operation(
        summary = "创建新用户",
        description = "创建新的用户账户"
    )
    @PostMapping
    public ResponseEntity<User> createUser(
        @Parameter(description = "用户信息", required = true) @Valid @RequestBody User user
    ) {
        User createdUser = userService.createUser(user);
        return ResponseEntity.status(HttpStatus.CREATED).body(createdUser);
    }
    
    @Operation(
        summary = "更新用户信息",
        description = "根据用户ID更新用户信息"
    )
    @PutMapping("/{id}")
    public ResponseEntity<User> updateUser(
        @Parameter(description = "用户ID", example = "1") @PathVariable Long id,
        @Parameter(description = "更新的用户信息", required = true) @Valid @RequestBody User user
    ) {
        User updatedUser = userService.updateUser(id, user);
        return ResponseEntity.ok(updatedUser);
    }
    
    @Operation(
        summary = "删除用户",
        description = "根据用户ID删除用户"
    )
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteUser(
        @Parameter(description = "用户ID", example = "1") @PathVariable Long id
    ) {
        userService.deleteUser(id);
        return ResponseEntity.noContent().build();
    }
}
```

### 请求/响应模型示例

```java
@Schema(description = "用户创建请求")
public class CreateUserRequest {
    
    @Schema(description = "用户名", example = "john_doe", minLength = 3, maxLength = 50)
    @NotBlank(message = "用户名不能为空")
    private String username;
    
    @Schema(description = "邮箱地址", example = "john@example.com")
    @Email(message = "邮箱格式不正确")
    private String email;
    
    @Schema(description = "密码", example = "password123", minLength = 6)
    @NotBlank(message = "密码不能为空")
    @Size(min = 6, message = "密码长度不能少于6位")
    private String password;
    
    // getters and setters
}

@Schema(description = "用户响应")
public class UserResponse {
    
    @Schema(description = "用户ID", example = "1")
    private Long id;
    
    @Schema(description = "用户名", example = "john_doe")
    private String username;
    
    @Schema(description = "邮箱地址", example = "john@example.com")
    private String email;
    
    @Schema(description = "创建时间", example = "2024-01-01T00:00:00Z")
    private LocalDateTime createdAt;
    
    // getters and setters
}
```

## 高级配置

### 安全配置

```java
@Configuration
public class OpenApiSecurityConfig {
    
    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("API 文档")
                        .version("1.0")
                        .description("Spring Boot 应用 API 文档"))
                .components(new Components()
                        .addSecuritySchemes("bearer-jwt", new SecurityScheme()
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")
                                .description("JWT 认证令牌")))
                .addSecurityItem(new SecurityRequirement().addList("bearer-jwt"));
    }
}
```

### 分组配置

```java
@Configuration
public class OpenApiGroupConfig {
    
    @Bean
    public GroupedOpenApi publicApi() {
        return GroupedOpenApi.builder()
                .group("public")
                .pathsToMatch("/api/public/**")
                .build();
    }
    
    @Bean
    public GroupedOpenApi adminApi() {
        return GroupedOpenApi.builder()
                .group("admin")
                .pathsToMatch("/api/admin/**")
                .build();
    }
    
    @Bean
    public GroupedOpenApi userApi() {
        return GroupedOpenApi.builder()
                .group("user")
                .pathsToMatch("/api/user/**")
                .build();
    }
}
```

### 自定义响应示例

```java
@Schema(description = "API 响应包装器")
public class ApiResponse<T> {
    
    @Schema(description = "响应状态码", example = "200")
    private Integer code;
    
    @Schema(description = "响应消息", example = "操作成功")
    private String message;
    
    @Schema(description = "响应数据")
    private T data;
    
    @Schema(description = "时间戳", example = "2024-01-01T00:00:00Z")
    private LocalDateTime timestamp;
    
    // 静态工厂方法
    public static <T> ApiResponse<T> success(T data) {
        ApiResponse<T> response = new ApiResponse<>();
        response.setCode(200);
        response.setMessage("操作成功");
        response.setData(data);
        response.setTimestamp(LocalDateTime.now());
        return response;
    }
    
    public static <T> ApiResponse<T> error(String message) {
        ApiResponse<T> response = new ApiResponse<>();
        response.setCode(500);
        response.setMessage(message);
        response.setTimestamp(LocalDateTime.now());
        return response;
    }
    
    // getters and setters
}
```

## 枚举类型支持

```java
@Schema(description = "用户状态枚举")
public enum UserStatus {
    
    @Schema(description = "活跃状态")
    ACTIVE("活跃"),
    
    @Schema(description = "非活跃状态")
    INACTIVE("非活跃"),
    
    @Schema(description = "已删除状态")
    DELETED("已删除");
    
    private final String description;
    
    UserStatus(String description) {
        this.description = description;
    }
    
    public String getDescription() {
        return description;
    }
}

@Schema(description = "用户实体")
public class User {
    
    @Schema(description = "用户状态", example = "ACTIVE")
    private UserStatus status;
    
    // 其他字段...
}
```

## 文件上传支持

```java
@Tag(name = "文件管理", description = "文件上传下载相关操作")
@RestController
@RequestMapping("/api/files")
public class FileController {
    
    @Operation(
        summary = "上传文件",
        description = "上传单个文件到服务器"
    )
    @PostMapping("/upload")
    public ResponseEntity<FileUploadResponse> uploadFile(
        @Parameter(description = "要上传的文件", required = true) 
        @RequestParam("file") MultipartFile file
    ) {
        // 文件上传逻辑
        String fileName = fileService.uploadFile(file);
        FileUploadResponse response = new FileUploadResponse(fileName, file.getSize());
        return ResponseEntity.ok(response);
    }
    
    @Operation(
        summary = "批量上传文件",
        description = "一次上传多个文件"
    )
    @PostMapping("/upload-multiple")
    public ResponseEntity<List<FileUploadResponse>> uploadMultipleFiles(
        @Parameter(description = "要上传的文件列表", required = true) 
        @RequestParam("files") MultipartFile[] files
    ) {
        // 批量文件上传逻辑
        List<FileUploadResponse> responses = new ArrayList<>();
        for (MultipartFile file : files) {
            String fileName = fileService.uploadFile(file);
            responses.add(new FileUploadResponse(fileName, file.getSize()));
        }
        return ResponseEntity.ok(responses);
    }
}

@Schema(description = "文件上传响应")
public class FileUploadResponse {
    
    @Schema(description = "文件名", example = "document.pdf")
    private String fileName;
    
    @Schema(description = "文件大小（字节）", example = "1024")
    private Long fileSize;
    
    @Schema(description = "上传时间", example = "2024-01-01T00:00:00Z")
    private LocalDateTime uploadTime;
    
    // 构造函数、getters和setters
}
```

## 分页和排序支持

```java
@Schema(description = "分页请求参数")
public class PageRequest {
    
    @Schema(description = "页码（从0开始）", example = "0", minimum = "0")
    @Min(value = 0, message = "页码不能小于0")
    private Integer page = 0;
    
    @Schema(description = "每页大小", example = "10", minimum = "1", maximum = "100")
    @Min(value = 1, message = "每页大小不能小于1")
    @Max(value = 100, message = "每页大小不能超过100")
    private Integer size = 10;
    
    @Schema(description = "排序字段", example = "createdAt")
    private String sortBy = "createdAt";
    
    @Schema(description = "排序方向", example = "DESC", allowableValues = {"ASC", "DESC"})
    @Pattern(regexp = "ASC|DESC", message = "排序方向必须是ASC或DESC")
    private String sortDirection = "DESC";
    
    // getters and setters
}

@Schema(description = "分页响应")
public class PageResponse<T> {
    
    @Schema(description = "当前页内容")
    private List<T> content;
    
    @Schema(description = "当前页码", example = "0")
    private Integer currentPage;
    
    @Schema(description = "每页大小", example = "10")
    private Integer pageSize;
    
    @Schema(description = "总记录数", example = "100")
    private Long totalElements;
    
    @Schema(description = "总页数", example = "10")
    private Integer totalPages;
    
    @Schema(description = "是否有下一页", example = "true")
    private Boolean hasNext;
    
    @Schema(description = "是否有上一页", example = "false")
    private Boolean hasPrevious;
    
    // getters and setters
}
```

## 错误处理

```java
@Schema(description = "错误响应")
public class ErrorResponse {
    
    @Schema(description = "错误时间戳", example = "2024-01-01T00:00:00Z")
    private LocalDateTime timestamp;
    
    @Schema(description = "HTTP状态码", example = "400")
    private Integer status;
    
    @Schema(description = "错误类型", example = "Bad Request")
    private String error;
    
    @Schema(description = "错误消息", example = "请求参数验证失败")
    private String message;
    
    @Schema(description = "错误详情")
    private List<String> details;
    
    @Schema(description = "请求路径", example = "/api/users")
    private String path;
    
    // getters and setters
}

@ControllerAdvice
public class GlobalExceptionHandler {
    
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationExceptions(
            MethodArgumentNotValidException ex, HttpServletRequest request) {
        
        List<String> details = ex.getBindingResult()
                .getFieldErrors()
                .stream()
                .map(error -> error.getField() + ": " + error.getDefaultMessage())
                .collect(Collectors.toList());
        
        ErrorResponse errorResponse = new ErrorResponse();
        errorResponse.setTimestamp(LocalDateTime.now());
        errorResponse.setStatus(HttpStatus.BAD_REQUEST.value());
        errorResponse.setError("Bad Request");
        errorResponse.setMessage("请求参数验证失败");
        errorResponse.setDetails(details);
        errorResponse.setPath(request.getRequestURI());
        
        return ResponseEntity.badRequest().body(errorResponse);
    }
    
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(
            Exception ex, HttpServletRequest request) {
        
        ErrorResponse errorResponse = new ErrorResponse();
        errorResponse.setTimestamp(LocalDateTime.now());
        errorResponse.setStatus(HttpStatus.INTERNAL_SERVER_ERROR.value());
        errorResponse.setError("Internal Server Error");
        errorResponse.setMessage("服务器内部错误");
        errorResponse.setPath(request.getRequestURI());
        
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
    }
}
```

## 测试和验证

### 单元测试示例

```java
@SpringBootTest
@AutoConfigureTestDatabase
class UserControllerTest {
    
    @Autowired
    private TestRestTemplate restTemplate;
    
    @Test
    void testGetUserById() {
        // 创建测试用户
        User user = createTestUser();
        
        // 测试获取用户
        ResponseEntity<User> response = restTemplate.getForEntity(
            "/api/users/" + user.getId(), User.class);
        
        assertEquals(HttpStatus.OK, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals(user.getUsername(), response.getBody().getUsername());
    }
    
    @Test
    void testCreateUser() {
        User user = new User();
        user.setUsername("testuser");
        user.setEmail("test@example.com");
        
        ResponseEntity<User> response = restTemplate.postForEntity(
            "/api/users", user, User.class);
        
        assertEquals(HttpStatus.CREATED, response.getStatusCode());
        assertNotNull(response.getBody());
        assertEquals("testuser", response.getBody().getUsername());
    }
    
    private User createTestUser() {
        // 创建测试用户的辅助方法
        return new User();
    }
}
```

## 最佳实践

### 1. 命名规范
- 使用清晰的API路径命名
- 控制器类名以`Controller`结尾
- 请求/响应类名以`Request`/`Response`结尾

### 2. 文档质量
- 为每个API提供清晰的summary和description
- 使用example属性提供示例值
- 详细描述请求参数和响应格式

### 3. 错误处理
- 定义标准的错误响应格式
- 为不同的HTTP状态码提供详细的错误描述
- 使用全局异常处理器统一处理异常

### 4. 安全性
- 在文档中明确标注需要认证的API
- 使用安全方案描述认证方式
- 避免在文档中暴露敏感信息

### 5. 性能考虑
- 合理使用分页和排序
- 避免返回过大的数据集
- 使用适当的HTTP缓存头

## 常见问题

### Q: 如何隐藏某些API接口？
A: 使用`@Hidden`注解或在配置中排除特定路径。

### Q: 如何自定义Swagger UI主题？
A: 在配置文件中设置`springdoc.swagger-ui.theme`属性。

### Q: 如何支持多环境配置？
A: 使用Spring Profile和条件配置。

### Q: 如何处理循环引用？
A: 使用`@JsonManagedReference`和`@JsonBackReference`注解。

## 总结

Spring-Doc是一个功能强大的API文档生成工具，它提供了丰富的注解和配置选项来生成高质量的API文档。通过合理使用这些特性，可以创建出专业、易读、易维护的API文档，提升开发效率和用户体验。

记住，好的API文档不仅仅是自动生成的，还需要开发者的精心设计和维护。持续更新文档，保持与实际代码的同步，才能真正发挥API文档的价值。
