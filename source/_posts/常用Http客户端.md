---
title: 常用Http客户端
main_color: "rgb(11, 32, 228)"
categories: Http
tags:
  - Http
cover: https://free.picui.cn/free/2026/03/28/69c74d13d5696.png
---

## RestTemplate

Spring框架提供的HTTP客户端，支持同步HTTP请求。

### 主要API

- `getForObject(url, responseType)` - GET请求，返回指定类型对象
- `postForObject(url, request, responseType)` - POST请求，返回指定类型对象
- `exchange(url, method, requestEntity, responseType)` - 通用请求方法
- `put(url, request)` - PUT请求
- `delete(url)` - DELETE请求

### 完整示例

```java
@Configuration
public class RestTemplateConfig {
    
    @Bean
    public RestTemplate restTemplate() {
        RestTemplate restTemplate = new RestTemplate();
        
        // 配置消息转换器
        restTemplate.getMessageConverters().add(new MappingJackson2HttpMessageConverter());
        
        // 配置错误处理器
        restTemplate.setErrorHandler(new DefaultResponseErrorHandler() {
            @Override
            public boolean hasError(ClientHttpResponse response) throws IOException {
                return response.getStatusCode().series() == HttpStatus.Series.CLIENT_ERROR ||
                       response.getStatusCode().series() == HttpStatus.Series.SERVER_ERROR;
            }
        });
        
        return restTemplate;
    }
}

// 使用示例
@Service
public class UserService {
    
    @Autowired
    private RestTemplate restTemplate;
    
    public User getUserById(Long id) {
        String url = "https://api.example.com/users/" + id;
        return restTemplate.getForObject(url, User.class);
    }
    
    public User createUser(User user) {
        String url = "https://api.example.com/users";
        return restTemplate.postForObject(url, user, User.class);
    }
    
    public void updateUser(Long id, User user) {
        String url = "https://api.example.com/users/" + id;
        restTemplate.put(url, user);
    }
    
    public void deleteUser(Long id) {
        String url = "https://api.example.com/users/" + id;
        restTemplate.delete(url);
    }
    
    // 带请求头的请求
    public User getUserWithAuth(Long id, String token) {
        String url = "https://api.example.com/users/" + id;
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(token);
        headers.setContentType(MediaType.APPLICATION_JSON);
        
        HttpEntity<String> entity = new HttpEntity<>(headers);
        ResponseEntity<User> response = restTemplate.exchange(url, HttpMethod.GET, entity, User.class);
        return response.getBody();
    }
}
```

### 封装工具类

```java
@Component
public class RestTemplateUtil {
    
    @Autowired
    private RestTemplate restTemplate;
    
    /**
     * GET请求
     */
    public <T> T get(String url, Class<T> responseType) {
        return restTemplate.getForObject(url, responseType);
    }
    
    /**
     * GET请求（带请求头）
     */
    public <T> T get(String url, Map<String, String> headers, Class<T> responseType) {
        HttpHeaders httpHeaders = new HttpHeaders();
        headers.forEach(httpHeaders::set);
        HttpEntity<String> entity = new HttpEntity<>(httpHeaders);
        
        ResponseEntity<T> response = restTemplate.exchange(url, HttpMethod.GET, entity, responseType);
        return response.getBody();
    }
    
    /**
     * POST请求
     */
    public <T> T post(String url, Object request, Class<T> responseType) {
        return restTemplate.postForObject(url, request, responseType);
    }
    
    /**
     * POST请求（带请求头）
     */
    public <T> T post(String url, Object request, Map<String, String> headers, Class<T> responseType) {
        HttpHeaders httpHeaders = new HttpHeaders();
        headers.forEach(httpHeaders::set);
        httpHeaders.setContentType(MediaType.APPLICATION_JSON);
        
        HttpEntity<Object> entity = new HttpEntity<>(request, httpHeaders);
        ResponseEntity<T> response = restTemplate.exchange(url, HttpMethod.POST, entity, responseType);
        return response.getBody();
    }
    
    /**
     * PUT请求
     */
    public void put(String url, Object request) {
        restTemplate.put(url, request);
    }
    
    /**
     * DELETE请求
     */
    public void delete(String url) {
        restTemplate.delete(url);
    }
    
    /**
     * 通用请求方法
     */
    public <T> T exchange(String url, HttpMethod method, Object request, 
                          Map<String, String> headers, Class<T> responseType) {
        HttpHeaders httpHeaders = new HttpHeaders();
        headers.forEach(httpHeaders::set);
        httpHeaders.setContentType(MediaType.APPLICATION_JSON);
        
        HttpEntity<Object> entity = new HttpEntity<>(request, httpHeaders);
        ResponseEntity<T> response = restTemplate.exchange(url, method, entity, responseType);
        return response.getBody();
    }
}
```

## OkHttp

Square公司开发的HTTP客户端，支持HTTP/2、连接池等特性。

### 主要API

- `newCall(Request)` - 创建新的请求
- `Request.Builder` - 构建请求
- `Response` - 响应对象
- `RequestBody` - 请求体
- `ResponseBody` - 响应体

### 完整示例

```java
@Configuration
public class OkHttpConfig {
    
    @Bean
    public OkHttpClient okHttpClient() {
        return new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .connectionPool(new ConnectionPool(5, 5, TimeUnit.MINUTES))
                .addInterceptor(new HttpLoggingInterceptor()
                        .setLevel(HttpLoggingInterceptor.Level.BODY))
                .build();
    }
}

// 使用示例
@Service
public class UserService {
    
    @Autowired
    private OkHttpClient okHttpClient;
    
    public User getUserById(Long id) throws IOException {
        Request request = new Request.Builder()
                .url("https://api.example.com/users/" + id)
                .get()
                .build();
        
        try (Response response = okHttpClient.newCall(request).execute()) {
            if (response.isSuccessful() && response.body() != null) {
                String json = response.body().string();
                return new ObjectMapper().readValue(json, User.class);
            }
            throw new RuntimeException("Request failed: " + response.code());
        }
    }
    
    public User createUser(User user) throws IOException {
        String json = new ObjectMapper().writeValueAsString(user);
        RequestBody body = RequestBody.create(json, MediaType.get("application/json"));
        
        Request request = new Request.Builder()
                .url("https://api.example.com/users")
                .post(body)
                .build();
        
        try (Response response = okHttpClient.newCall(request).execute()) {
            if (response.isSuccessful() && response.body() != null) {
                String responseJson = response.body().string();
                return new ObjectMapper().readValue(responseJson, User.class);
            }
            throw new RuntimeException("Request failed: " + response.code());
        }
    }
    
    public void updateUser(Long id, User user) throws IOException {
        String json = new ObjectMapper().writeValueAsString(user);
        RequestBody body = RequestBody.create(json, MediaType.get("application/json"));
        
        Request request = new Request.Builder()
                .url("https://api.example.com/users/" + id)
                .put(body)
                .build();
        
        try (Response response = okHttpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new RuntimeException("Request failed: " + response.code());
            }
        }
    }
    
    public void deleteUser(Long id) throws IOException {
        Request request = new Request.Builder()
                .url("https://api.example.com/users/" + id)
                .delete()
                .build();
        
        try (Response response = okHttpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new RuntimeException("Request failed: " + response.code());
            }
        }
    }
    
    // 带请求头的请求
    public User getUserWithAuth(Long id, String token) throws IOException {
        Request request = new Request.Builder()
                .url("https://api.example.com/users/" + id)
                .addHeader("Authorization", "Bearer " + token)
                .addHeader("Content-Type", "application/json")
                .get()
                .build();
        
        try (Response response = okHttpClient.newCall(request).execute()) {
            if (response.isSuccessful() && response.body() != null) {
                String json = response.body().string();
                return new ObjectMapper().readValue(json, User.class);
            }
            throw new RuntimeException("Request failed: " + response.code());
        }
    }
}
```

### 封装工具类

```java
@Component
public class OkHttpUtil {
    
    @Autowired
    private OkHttpClient okHttpClient;
    
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    /**
     * GET请求
     */
    public <T> T get(String url, Class<T> responseType) throws IOException {
        Request request = new Request.Builder()
                .url(url)
                .get()
                .build();
        
        return executeRequest(request, responseType);
    }
    
    /**
     * GET请求（带请求头）
     */
    public <T> T get(String url, Map<String, String> headers, Class<T> responseType) throws IOException {
        Request.Builder builder = new Request.Builder().url(url).get();
        headers.forEach(builder::addHeader);
        
        Request request = builder.build();
        return executeRequest(request, responseType);
    }
    
    /**
     * POST请求
     */
    public <T> T post(String url, Object requestBody, Class<T> responseType) throws IOException {
        String json = objectMapper.writeValueAsString(requestBody);
        RequestBody body = RequestBody.create(json, MediaType.get("application/json"));
        
        Request request = new Request.Builder()
                .url(url)
                .post(body)
                .build();
        
        return executeRequest(request, responseType);
    }
    
    /**
     * POST请求（带请求头）
     */
    public <T> T post(String url, Object requestBody, Map<String, String> headers, Class<T> responseType) throws IOException {
        String json = objectMapper.writeValueAsString(requestBody);
        RequestBody body = RequestBody.create(json, MediaType.get("application/json"));
        
        Request.Builder builder = new Request.Builder().url(url).post(body);
        headers.forEach(builder::addHeader);
        
        Request request = builder.build();
        return executeRequest(request, responseType);
    }
    
    /**
     * PUT请求
     */
    public void put(String url, Object requestBody) throws IOException {
        String json = objectMapper.writeValueAsString(requestBody);
        RequestBody body = RequestBody.create(json, MediaType.get("application/json"));
        
        Request request = new Request.Builder()
                .url(url)
                .put(body)
                .build();
        
        executeRequest(request, Void.class);
    }
    
    /**
     * DELETE请求
     */
    public void delete(String url) throws IOException {
        Request request = new Request.Builder()
                .url(url)
                .delete()
                .build();
        
        executeRequest(request, Void.class);
    }
    
    /**
     * 执行请求
     */
    private <T> T executeRequest(Request request, Class<T> responseType) throws IOException {
        try (Response response = okHttpClient.newCall(request).execute()) {
            if (response.isSuccessful()) {
                if (responseType == Void.class) {
                    return null;
                }
                if (response.body() != null) {
                    String json = response.body().string();
                    return objectMapper.readValue(json, responseType);
                }
                return null;
            }
            throw new RuntimeException("Request failed: " + response.code());
        }
    }
}
```

## Retrofit

Square公司基于OkHttp开发的类型安全的HTTP客户端，支持注解和接口定义。

### 主要API

- `@GET` - GET请求注解
- `@POST` - POST请求注解
- `@PUT` - PUT请求注解
- `@DELETE` - DELETE请求注解
- `@Body` - 请求体参数
- `@Query` - 查询参数
- `@Path` - 路径参数
- `@Header` - 请求头参数

### 完整示例

```java
// API接口定义
public interface UserApi {
    
    @GET("users/{id}")
    Call<User> getUserById(@Path("id") Long id);
    
    @GET("users")
    Call<List<User>> getUsers(@Query("page") int page, @Query("size") int size);
    
    @POST("users")
    Call<User> createUser(@Body User user);
    
    @PUT("users/{id}")
    Call<Void> updateUser(@Path("id") Long id, @Body User user);
    
    @DELETE("users/{id}")
    Call<Void> deleteUser(@Path("id") Long id);
    
    @GET("users/{id}")
    Call<User> getUserWithAuth(@Path("id") Long id, @Header("Authorization") String token);
}

@Configuration
public class RetrofitConfig {
    
    @Bean
    public Retrofit retrofit() {
        OkHttpClient okHttpClient = new OkHttpClient.Builder()
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(30, TimeUnit.SECONDS)
                .addInterceptor(new HttpLoggingInterceptor()
                        .setLevel(HttpLoggingInterceptor.Level.BODY))
                .build();
        
        return new Retrofit.Builder()
                .baseUrl("https://api.example.com/")
                .client(okHttpClient)
                .addConverterFactory(GsonConverterFactory.create())
                .build();
    }
}

// 使用示例
@Service
public class UserService {
    
    @Autowired
    private UserApi userApi;
    
    public User getUserById(Long id) throws IOException {
        Call<User> call = userApi.getUserById(id);
        Response<User> response = call.execute();
        
        if (response.isSuccessful()) {
            return response.body();
        }
        throw new RuntimeException("Request failed: " + response.code());
    }
    
    public List<User> getUsers(int page, int size) throws IOException {
        Call<List<User>> call = userApi.getUsers(page, size);
        Response<List<User>> response = call.execute();
        
        if (response.isSuccessful()) {
            return response.body();
        }
        throw new RuntimeException("Request failed: " + response.code());
    }
    
    public User createUser(User user) throws IOException {
        Call<User> call = userApi.createUser(user);
        Response<User> response = call.execute();
        
        if (response.isSuccessful()) {
            return response.body();
        }
        throw new RuntimeException("Request failed: " + response.code());
    }
    
    public void updateUser(Long id, User user) throws IOException {
        Call<Void> call = userApi.updateUser(id, user);
        Response<Void> response = call.execute();
        
        if (!response.isSuccessful()) {
            throw new RuntimeException("Request failed: " + response.code());
        }
    }
    
    public void deleteUser(Long id) throws IOException {
        Call<Void> call = userApi.deleteUser(id);
        Response<Void> response = call.execute();
        
        if (!response.isSuccessful()) {
            throw new RuntimeException("Request failed: " + response.code());
        }
    }
    
    public User getUserWithAuth(Long id, String token) throws IOException {
        Call<User> call = userApi.getUserWithAuth(id, "Bearer " + token);
        Response<User> response = call.execute();
        
        if (response.isSuccessful()) {
            return response.body();
        }
        throw new RuntimeException("Request failed: " + response.code());
    }
}
```

### 封装工具类

```java
@Component
public class RetrofitUtil {
    
    @Autowired
    private Retrofit retrofit;
    
    /**
     * 创建API接口实例
     */
    public <T> T createApi(Class<T> apiClass) {
        return retrofit.create(apiClass);
    }
    
    /**
     * 执行同步请求
     */
    public <T> T executeSync(Call<T> call) throws IOException {
        Response<T> response = call.execute();
        if (response.isSuccessful()) {
            return response.body();
        }
        throw new RuntimeException("Request failed: " + response.code());
    }
    
    /**
     * 执行异步请求
     */
    public <T> void executeAsync(Call<T> call, Callback<T> callback) {
        call.enqueue(callback);
    }
    
    /**
     * 创建通用回调
     */
    public <T> Callback<T> createCallback(Consumer<T> onSuccess, Consumer<Throwable> onError) {
        return new Callback<T>() {
            @Override
            public void onResponse(Call<T> call, Response<T> response) {
                if (response.isSuccessful()) {
                    onSuccess.accept(response.body());
                } else {
                    onError.accept(new RuntimeException("Request failed: " + response.code()));
                }
            }
            
            @Override
            public void onFailure(Call<T> call, Throwable t) {
                onError.accept(t);
            }
        };
    }
}
```

## WebClient

Spring WebFlux提供的响应式HTTP客户端，支持非阻塞I/O。

### 主要API

- `get()` - GET请求
- `post()` - POST请求
- `put()` - PUT请求
- `delete()` - DELETE请求
- `uri()` - 设置URI
- `bodyValue()` - 设置请求体
- `body()` - 设置请求体（Mono/Flux）
- `retrieve()` - 获取响应
- `bodyToMono()` - 转换为Mono
- `bodyToFlux()` - 转换为Flux

### 完整示例

```java
@Configuration
public class WebClientConfig {
    
    @Bean
    public WebClient webClient() {
        return WebClient.builder()
                .baseUrl("https://api.example.com")
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(2 * 1024 * 1024))
                .build();
    }
}

// 使用示例
@Service
public class UserService {
    
    @Autowired
    private WebClient webClient;
    
    public Mono<User> getUserById(Long id) {
        return webClient.get()
                .uri("/users/{id}", id)
                .retrieve()
                .bodyToMono(User.class);
    }
    
    public Mono<User> createUser(User user) {
        return webClient.post()
                .uri("/users")
                .bodyValue(user)
                .retrieve()
                .bodyToMono(User.class);
    }
    
    public Mono<Void> updateUser(Long id, User user) {
        return webClient.put()
                .uri("/users/{id}", id)
                .bodyValue(user)
                .retrieve()
                .bodyToMono(Void.class);
    }
    
    public Mono<Void> deleteUser(Long id) {
        return webClient.delete()
                .uri("/users/{id}", id)
                .retrieve()
                .bodyToMono(Void.class);
    }
    
    public Flux<User> getUsers(int page, int size) {
        return webClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/users")
                        .queryParam("page", page)
                        .queryParam("size", size)
                        .build())
                .retrieve()
                .bodyToFlux(User.class);
    }
    
    // 带请求头的请求
    public Mono<User> getUserWithAuth(Long id, String token) {
        return webClient.get()
                .uri("/users/{id}", id)
                .header("Authorization", "Bearer " + token)
                .retrieve()
                .bodyToMono(User.class);
    }
    
    // 带查询参数的请求
    public Flux<User> searchUsers(String keyword, String sortBy) {
        return webClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/users/search")
                        .queryParam("keyword", keyword)
                        .queryParam("sortBy", sortBy)
                        .build())
                .retrieve()
                .bodyToFlux(User.class);
    }
    
    // 文件上传
    public Mono<String> uploadFile(MultipartFile file) {
        return webClient.post()
                .uri("/upload")
                .body(BodyInserters.fromMultipartData("file", file.getResource()))
                .retrieve()
                .bodyToMono(String.class);
    }
    
    // 流式响应处理
    public Flux<String> getStreamData() {
        return webClient.get()
                .uri("/stream")
                .retrieve()
                .bodyToFlux(String.class);
    }
}
```

### 封装工具类

```java
@Component
public class WebClientUtil {
    
    @Autowired
    private WebClient webClient;
    
    /**
     * GET请求
     */
    public <T> Mono<T> get(String path, Class<T> responseType, Object... uriVariables) {
        return webClient.get()
                .uri(path, uriVariables)
                .retrieve()
                .bodyToMono(responseType);
    }
    
    /**
     * GET请求（带查询参数）
     */
    public <T> Mono<T> get(String path, Map<String, String> queryParams, Class<T> responseType, Object... uriVariables) {
        return webClient.get()
                .uri(uriBuilder -> {
                    uriBuilder.path(path);
                    queryParams.forEach(uriBuilder::queryParam);
                    return uriBuilder.build(uriVariables);
                })
                .retrieve()
                .bodyToMono(responseType);
    }
    
    /**
     * POST请求
     */
    public <T> Mono<T> post(String path, Object requestBody, Class<T> responseType, Object... uriVariables) {
        return webClient.post()
                .uri(path, uriVariables)
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(responseType);
    }
    
    /**
     * PUT请求
     */
    public <T> Mono<T> put(String path, Object requestBody, Class<T> responseType, Object... uriVariables) {
        return webClient.put()
                .uri(path, uriVariables)
                .bodyValue(requestBody)
                .retrieve()
                .bodyToMono(responseType);
    }
    
    /**
     * DELETE请求
     */
    public Mono<Void> delete(String path, Object... uriVariables) {
        return webClient.delete()
                .uri(path, uriVariables)
                .retrieve()
                .bodyToMono(Void.class);
    }
    
    /**
     * 带请求头的请求
     */
    public <T> Mono<T> requestWithHeaders(HttpMethod method, String path, Object requestBody, 
                                         Map<String, String> headers, Class<T> responseType, Object... uriVariables) {
        WebClient.RequestBodySpec requestSpec = webClient.method(method)
                .uri(path, uriVariables);
        
        headers.forEach(requestSpec::header);
        
        if (requestBody != null) {
            requestSpec.bodyValue(requestBody);
        }
        
        return requestSpec.retrieve().bodyToMono(responseType);
    }
    
    /**
     * 处理错误响应
     */
    public <T> Mono<T> handleErrors(Mono<T> response, Class<? extends Exception> exceptionType) {
        return response.onErrorMap(WebClientResponseException.class, ex -> {
            try {
                return exceptionType.getConstructor(String.class).newInstance(ex.getMessage());
            } catch (Exception e) {
                return new RuntimeException(ex.getMessage(), ex);
            }
        });
    }
}
```

## Apache HttpClient

Apache基金会开发的HTTP客户端，功能强大，支持连接池、代理、认证等特性。

### 主要API

- `HttpClients.createDefault()` - 创建默认客户端
- `HttpGet` - GET请求
- `HttpPost` - POST请求
- `HttpPut` - PUT请求
- `HttpDelete` - DELETE请求
- `HttpPatch` - PATCH请求
- `StringEntity` - 字符串请求体
- `UrlEncodedFormEntity` - 表单请求体
- `MultipartEntityBuilder` - 多部分请求体
- `HttpResponse` - 响应对象
- `HttpEntity` - 响应实体

### 完整示例

```java
@Configuration
public class ApacheHttpClientConfig {
    
    @Bean
    public CloseableHttpClient httpClient() {
        return HttpClients.custom()
                .setConnectionManager(createConnectionManager())
                .setDefaultRequestConfig(createRequestConfig())
                .addInterceptorFirst(new HttpRequestInterceptor() {
                    @Override
                    public void process(HttpRequest request, HttpContext context) {
                        request.addHeader("User-Agent", "ApacheHttpClient/1.0");
                    }
                })
                .build();
    }
    
    private PoolingHttpClientConnectionManager createConnectionManager() {
        PoolingHttpClientConnectionManager connectionManager = new PoolingHttpClientConnectionManager();
        connectionManager.setMaxTotal(200);
        connectionManager.setDefaultMaxPerRoute(20);
        return connectionManager;
    }
    
    private RequestConfig createRequestConfig() {
        return RequestConfig.custom()
                .setConnectTimeout(30000)
                .setSocketTimeout(30000)
                .setConnectionRequestTimeout(10000)
                .build();
    }
}

// 使用示例
@Service
public class UserService {
    
    @Autowired
    private CloseableHttpClient httpClient;
    
    public User getUserById(Long id) throws IOException {
        String url = "https://api.example.com/users/" + id;
        HttpGet request = new HttpGet(url);
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity entity = response.getEntity();
            if (response.getStatusLine().getStatusCode() == 200 && entity != null) {
                String json = EntityUtils.toString(entity);
                return new ObjectMapper().readValue(json, User.class);
            }
            throw new RuntimeException("Request failed: " + response.getStatusLine().getStatusCode());
        }
    }
    
    public User createUser(User user) throws IOException {
        String url = "https://api.example.com/users";
        HttpPost request = new HttpPost(url);
        
        String json = new ObjectMapper().writeValueAsString(user);
        StringEntity entity = new StringEntity(json, ContentType.APPLICATION_JSON);
        request.setEntity(entity);
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity responseEntity = response.getEntity();
            if (response.getStatusLine().getStatusCode() == 201 && responseEntity != null) {
                String responseJson = EntityUtils.toString(responseEntity);
                return new ObjectMapper().readValue(responseJson, User.class);
            }
            throw new RuntimeException("Request failed: " + response.getStatusLine().getStatusCode());
        }
    }
    
    public void updateUser(Long id, User user) throws IOException {
        String url = "https://api.example.com/users/" + id;
        HttpPut request = new HttpPut(url);
        
        String json = new ObjectMapper().writeValueAsString(user);
        StringEntity entity = new StringEntity(json, ContentType.APPLICATION_JSON);
        request.setEntity(entity);
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            if (response.getStatusLine().getStatusCode() != 200) {
                throw new RuntimeException("Request failed: " + response.getStatusLine().getStatusCode());
            }
        }
    }
    
    public void deleteUser(Long id) throws IOException {
        String url = "https://api.example.com/users/" + id;
        HttpDelete request = new HttpDelete(url);
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            if (response.getStatusLine().getStatusCode() != 204) {
                throw new RuntimeException("Request failed: " + response.getStatusLine().getStatusCode());
            }
        }
    }
    
    // 带请求头的请求
    public User getUserWithAuth(Long id, String token) throws IOException {
        String url = "https://api.example.com/users/" + id;
        HttpGet request = new HttpGet(url);
        request.addHeader("Authorization", "Bearer " + token);
        request.addHeader("Content-Type", "application/json");
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity entity = response.getEntity();
            if (response.getStatusLine().getStatusCode() == 200 && entity != null) {
                String json = EntityUtils.toString(entity);
                return new ObjectMapper().readValue(json, User.class);
            }
            throw new RuntimeException("Request failed: " + response.getStatusLine().getStatusCode());
        }
    }
    
    // 表单提交
    public String submitForm(Map<String, String> formData) throws IOException {
        String url = "https://api.example.com/submit";
        HttpPost request = new HttpPost(url);
        
        List<NameValuePair> params = new ArrayList<>();
        formData.forEach((key, value) -> params.add(new BasicNameValuePair(key, value)));
        UrlEncodedFormEntity entity = new UrlEncodedFormEntity(params, "UTF-8");
        request.setEntity(entity);
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity responseEntity = response.getEntity();
            if (response.getStatusLine().getStatusCode() == 200 && responseEntity != null) {
                return EntityUtils.toString(responseEntity);
            }
            throw new RuntimeException("Request failed: " + response.getStatusLine().getStatusCode());
        }
    }
    
    // 文件上传
    public String uploadFile(File file) throws IOException {
        String url = "https://api.example.com/upload";
        HttpPost request = new HttpPost(url);
        
        MultipartEntityBuilder builder = MultipartEntityBuilder.create();
        builder.addBinaryBody("file", file, ContentType.APPLICATION_OCTET_STREAM, file.getName());
        HttpEntity multipart = builder.build();
        request.setEntity(multipart);
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity responseEntity = response.getEntity();
            if (response.getStatusLine().getStatusCode() == 200 && responseEntity != null) {
                return EntityUtils.toString(responseEntity);
            }
            throw new RuntimeException("Request failed: " + response.getStatusLine().getStatusCode());
        }
    }
    
    // 代理请求
    public User getUserWithProxy(Long id, String proxyHost, int proxyPort) throws IOException {
        String url = "https://api.example.com/users/" + id;
        HttpGet request = new HttpGet(url);
        
        HttpHost proxy = new HttpHost(proxyHost, proxyPort);
        RequestConfig config = RequestConfig.custom()
                .setProxy(proxy)
                .setConnectTimeout(30000)
                .setSocketTimeout(30000)
                .build();
        request.setConfig(config);
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity entity = response.getEntity();
            if (response.getStatusLine().getStatusCode() == 200 && entity != null) {
                String json = EntityUtils.toString(entity);
                return new ObjectMapper().readValue(json, User.class);
            }
            throw new RuntimeException("Request failed: " + response.getStatusLine().getStatusCode());
        }
    }
}
```

### 封装工具类

```java
@Component
public class ApacheHttpClientUtil {
    
    @Autowired
    private CloseableHttpClient httpClient;
    
    private final ObjectMapper objectMapper = new ObjectMapper();
    
    /**
     * GET请求
     */
    public <T> T get(String url, Class<T> responseType) throws IOException {
        HttpGet request = new HttpGet(url);
        return executeRequest(request, responseType);
    }
    
    /**
     * GET请求（带请求头）
     */
    public <T> T get(String url, Map<String, String> headers, Class<T> responseType) throws IOException {
        HttpGet request = new HttpGet(url);
        headers.forEach(request::addHeader);
        return executeRequest(request, responseType);
    }
    
    /**
     * POST请求
     */
    public <T> T post(String url, Object requestBody, Class<T> responseType) throws IOException {
        HttpPost request = new HttpPost(url);
        String json = objectMapper.writeValueAsString(requestBody);
        StringEntity entity = new StringEntity(json, ContentType.APPLICATION_JSON);
        request.setEntity(entity);
        return executeRequest(request, responseType);
    }
    
    /**
     * POST请求（带请求头）
     */
    public <T> T post(String url, Object requestBody, Map<String, String> headers, Class<T> responseType) throws IOException {
        HttpPost request = new HttpPost(url);
        headers.forEach(request::addHeader);
        String json = objectMapper.writeValueAsString(requestBody);
        StringEntity entity = new StringEntity(json, ContentType.APPLICATION_JSON);
        request.setEntity(entity);
        return executeRequest(request, responseType);
    }
    
    /**
     * PUT请求
     */
    public void put(String url, Object requestBody) throws IOException {
        HttpPut request = new HttpPut(url);
        String json = objectMapper.writeValueAsString(requestBody);
        StringEntity entity = new StringEntity(json, ContentType.APPLICATION_JSON);
        request.setEntity(entity);
        executeRequest(request, Void.class);
    }
    
    /**
     * DELETE请求
     */
    public void delete(String url) throws IOException {
        HttpDelete request = new HttpDelete(url);
        executeRequest(request, Void.class);
    }
    
    /**
     * 表单提交
     */
    public String submitForm(String url, Map<String, String> formData) throws IOException {
        HttpPost request = new HttpPost(url);
        List<NameValuePair> params = new ArrayList<>();
        formData.forEach((key, value) -> params.add(new BasicNameValuePair(key, value)));
        UrlEncodedFormEntity entity = new UrlEncodedFormEntity(params, "UTF-8");
        request.setEntity(entity);
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity responseEntity = response.getEntity();
            if (response.getStatusLine().getStatusCode() == 200 && responseEntity != null) {
                return EntityUtils.toString(responseEntity);
            }
            throw new RuntimeException("Request failed: " + response.getStatusLine().getStatusCode());
        }
    }
    
    /**
     * 文件上传
     */
    public String uploadFile(String url, File file) throws IOException {
        HttpPost request = new HttpPost(url);
        MultipartEntityBuilder builder = MultipartEntityBuilder.create();
        builder.addBinaryBody("file", file, ContentType.APPLICATION_OCTET_STREAM, file.getName());
        HttpEntity multipart = builder.build();
        request.setEntity(multipart);
        
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            HttpEntity responseEntity = response.getEntity();
            if (response.getStatusLine().getStatusCode() == 200 && responseEntity != null) {
                return EntityUtils.toString(responseEntity);
            }
            throw new RuntimeException("Request failed: " + response.getStatusLine().getStatusCode());
        }
    }
    
    /**
     * 执行请求
     */
    private <T> T executeRequest(HttpRequestBase request, Class<T> responseType) throws IOException {
        try (CloseableHttpResponse response = httpClient.execute(request)) {
            int statusCode = response.getStatusLine().getStatusCode();
            if (statusCode >= 200 && statusCode < 300) {
                if (responseType == Void.class) {
                    return null;
                }
                HttpEntity entity = response.getEntity();
                if (entity != null) {
                    String json = EntityUtils.toString(entity);
                    return objectMapper.readValue(json, responseType);
                }
                return null;
            }
            throw new RuntimeException("Request failed: " + statusCode);
        }
    }
    
    /**
     * 设置代理
     */
    public void setProxy(HttpRequestBase request, String proxyHost, int proxyPort) {
        HttpHost proxy = new HttpHost(proxyHost, proxyPort);
        RequestConfig config = RequestConfig.custom()
                .setProxy(proxy)
                .setConnectTimeout(30000)
                .setSocketTimeout(30000)
                .build();
        request.setConfig(config);
    }
}
```

## 总结对比

| 特性 | RestTemplate | OkHttp | Retrofit | WebClient | Apache HttpClient |
|------|-------------|---------|----------|-----------|-------------------|
| **同步/异步** | 同步 | 同步/异步 | 同步/异步 | 异步 | 同步 |
| **响应式** | 否 | 否 | 否 | 是 | 否 |
| **类型安全** | 否 | 否 | 是 | 是 | 否 |
| **配置复杂度** | 低 | 中 | 中 | 中 | 高 |
| **功能丰富度** | 中 | 高 | 高 | 高 | 最高 |
| **Spring集成** | 原生 | 需配置 | 需配置 | 原生 | 需配置 |
| **性能** | 中 | 高 | 高 | 高 | 中 |
| **学习曲线** | 低 | 中 | 中 | 中 | 高 |

### 选择建议

- **RestTemplate**: 适合简单的Spring项目，学习成本低
- **OkHttp**: 适合需要高性能和更多功能的项目
- **Retrofit**: 适合需要类型安全和接口定义的项目
- **WebClient**: 适合响应式编程和Spring WebFlux项目
- **Apache HttpClient**: 适合需要复杂HTTP功能的企业级项目