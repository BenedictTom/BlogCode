---
title: Python装饰器
main_color: "#458d8dff"  
categories: Python
tags:
  - Python    
cover: https://free.picui.cn/free/2026/03/28/69c74dead15ee.png
---

# Python装饰器：优雅的代码增强艺术

装饰器（Decorator）是Python中最优雅和强大的特性之一，它允许我们在不修改原函数代码的情况下，为函数添加新的功能。装饰器本质上是一个返回函数的高阶函数，它遵循"开放-封闭"原则，让代码更加简洁、可读和可维护。

## 1. 装饰器的基本概念

### 1.1 什么是装饰器

装饰器是一种设计模式，它允许向一个现有的对象添加新的功能，同时又不改变其结构。在Python中，装饰器本质上是一个函数，它接受一个函数作为参数，并返回一个新的函数。

### 1.2 装饰器的语法糖

Python提供了`@`符号作为装饰器的语法糖，让装饰器的使用更加简洁优雅：

```python
@decorator
def function():
    pass

# 等价于
def function():
    pass
function = decorator(function)
```

## 2. 装饰器的实现方式

### 2.1 函数装饰器

最简单的装饰器实现方式：

```python
def my_decorator(func):
    def wrapper(*args, **kwargs):
        print("函数执行前")
        result = func(*args, **kwargs)
        print("函数执行后")
        return result
    return wrapper

@my_decorator
def say_hello(name):
    print(f"Hello, {name}!")
    return f"Greeting for {name}"

# 使用
result = say_hello("Alice")
```

### 2.2 带参数的装饰器

```python
def repeat(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for i in range(times):
                print(f"第 {i+1} 次执行:")
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def greet(name):
    print(f"Hello, {name}!")

greet("Bob")
```

### 2.3 类装饰器

```python
class CountCalls:
    def __init__(self, func):
        self.func = func
        self.count = 0
    
    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"函数被调用了 {self.count} 次")
        return self.func(*args, **kwargs)

@CountCalls
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(5))
```

### 2.4 保持函数元信息的装饰器

使用`functools.wraps`保持原函数的元信息：

```python
import functools
import time

def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} 执行时间: {end_time - start_time:.4f}秒")
        return result
    return wrapper

@timing_decorator
def slow_function():
    time.sleep(1)
    return "完成"

print(slow_function.__name__)  # 输出: slow_function
```

## 3. 实际应用场景

### 3.1 日志记录

```python
import logging
import functools
from datetime import datetime

def log_execution(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        
        logger.info(f"开始执行 {func.__name__}")
        logger.info(f"参数: args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} 执行成功")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} 执行失败: {str(e)}")
            raise
    
    return wrapper

@log_execution
def calculate_sum(a, b):
    return a + b

result = calculate_sum(5, 3)
```

### 3.2 权限验证

```python
def require_permission(permission):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 模拟权限检查
            user_permissions = ["read", "write"]  # 从数据库或配置获取
            
            if permission not in user_permissions:
                raise PermissionError(f"需要 {permission} 权限")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

@require_permission("admin")
def delete_user(user_id):
    print(f"删除用户 {user_id}")

@require_permission("read")
def get_user_info(user_id):
    print(f"获取用户 {user_id} 信息")
```

### 3.3 缓存装饰器

```python
def memoize(func):
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 创建缓存键
        key = str(args) + str(sorted(kwargs.items()))
        
        if key in cache:
            print(f"从缓存获取 {func.__name__}({args})")
            return cache[key]
        
        result = func(*args, **kwargs)
        cache[key] = result
        print(f"计算结果并缓存 {func.__name__}({args})")
        return result
    
    return wrapper

@memoize
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
```

### 3.4 重试机制

```python
import time
import random

def retry(max_attempts=3, delay=1):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        print(f"重试 {max_attempts} 次后仍然失败: {e}")
                        raise
                    print(f"第 {attempt + 1} 次尝试失败: {e}, {delay}秒后重试")
                    time.sleep(delay)
        return wrapper
    return decorator

@retry(max_attempts=3, delay=1)
def unreliable_function():
    if random.random() < 0.7:  # 70% 概率失败
        raise Exception("随机失败")
    return "成功!"

result = unreliable_function()
```

### 3.5 性能监控

```python
import time
import psutil
import os

def performance_monitor(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process(os.getpid())
        
        # 记录开始状态
        start_time = time.time()
        start_memory = process.memory_info().rss / 1024 / 1024  # MB
        start_cpu = process.cpu_percent()
        
        result = func(*args, **kwargs)
        
        # 记录结束状态
        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024  # MB
        end_cpu = process.cpu_percent()
        
        print(f"性能监控 - {func.__name__}:")
        print(f"  执行时间: {end_time - start_time:.4f}秒")
        print(f"  内存使用: {end_memory - start_memory:.2f}MB")
        print(f"  CPU使用: {end_cpu - start_cpu:.2f}%")
        
        return result
    return wrapper

@performance_monitor
def heavy_computation(n):
    return sum(i**2 for i in range(n))

result = heavy_computation(1000000)
```

## 4. 装饰器的组合使用

```python
def debug(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"调试: 调用 {func.__name__} 参数: {args}, {kwargs}")
        result = func(*args, **kwargs)
        print(f"调试: {func.__name__} 返回: {result}")
        return result
    return wrapper

def validate_input(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        for arg in args:
            if not isinstance(arg, (int, float)):
                raise ValueError(f"参数必须是数字: {arg}")
        return func(*args, **kwargs)
    return wrapper

@debug
@validate_input
@timing_decorator
def calculate_average(*numbers):
    return sum(numbers) / len(numbers)

result = calculate_average(1, 2, 3, 4, 5)
```

## 5. 装饰器的最佳实践

### 5.1 使用functools.wraps

```python
import functools

def good_decorator(func):
    @functools.wraps(func)  # 保持原函数的元信息
    def wrapper(*args, **kwargs):
        # 装饰器逻辑
        return func(*args, **kwargs)
    return wrapper
```

### 5.2 处理装饰器参数

```python
def smart_decorator(func=None, *, option1=True, option2=False):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if option1:
                print("选项1启用")
            if option2:
                print("选项2启用")
            return f(*args, **kwargs)
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)

# 使用方式
@smart_decorator
def func1():
    pass

@smart_decorator(option1=False, option2=True)
def func2():
    pass
```

### 5.3 装饰器工厂模式

```python
def create_decorator(prefix="[INFO]"):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            print(f"{prefix} 执行 {func.__name__}")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# 创建不同前缀的装饰器
info_decorator = create_decorator("[INFO]")
error_decorator = create_decorator("[ERROR]")
debug_decorator = create_decorator("[DEBUG]")

@info_decorator
def process_data():
    return "数据处理完成"

@error_decorator
def handle_error():
    return "错误处理完成"
```

## 6. 常见使用场景总结

1. **日志记录**: 自动记录函数调用和执行结果
2. **性能监控**: 测量函数执行时间和资源使用
3. **权限验证**: 检查用户权限后再执行函数
4. **缓存机制**: 避免重复计算，提高性能
5. **重试机制**: 自动重试失败的操作
6. **参数验证**: 验证函数参数的有效性
7. **事务管理**: 自动处理数据库事务
8. **API限流**: 控制API调用频率
9. **错误处理**: 统一处理异常
10. **代码分析**: 统计函数调用次数和频率

## 7. 总结

装饰器是Python中非常强大的特性，它让我们能够：

- **优雅地扩展功能**: 在不修改原代码的情况下添加新功能
- **提高代码复用性**: 将通用逻辑抽象为装饰器
- **保持代码简洁**: 避免重复代码，提高可读性
- **遵循设计原则**: 符合开放-封闭原则

掌握装饰器的使用，能够让你的Python代码更加优雅、可维护和强大。在实际开发中，合理使用装饰器可以大大提高代码质量和开发效率。