# Python 基础面试详细讲解

> 基于价格监控项目，详细展开 Python 基础知识点，达到面试标准

---

## 目录

- [一、类型提示](#一类型提示)
- [二、装饰器](#二装饰器)
- [三、异常处理](#三异常处理)
- [四、上下文管理器](#四上下文管理器)
- [五、生成器与迭代器](#五生成器与迭代器)
- [六、类与面向对象](#六类与面向对象)
- [七、面试总结](#七面试总结)

---

## 一、类型提示

### 1.1 为什么需要类型提示？

**面试标准答案：**

1. **代码可读性**：让其他开发者快速了解函数参数和返回值类型
2. **IDE 智能提示**：编辑器可以根据类型提示提供自动补全和类型检查
3. **静态类型检查**：配合 mypy 等工具在运行前发现类型错误
4. **文档作用**：类型提示即文档，减少额外的注释需求

**面试追问：**
```
Q: Python 是动态类型语言，为什么还要用类型提示？
A: 动态类型方便灵活，但大型项目中容易产生类型错误
   类型提示提供"最佳平衡"：保持 Python 灵活性的同时，
   获得静态类型的安全性
```

### 1.2 核心类型标注语法

#### 基本类型
```python
# 基本类型
def add(a: int, b: int) -> int:
    return a + b

# 可选类型
def get_name(user_id: Optional[int] = None) -> str:
    if user_id:
        return fetch_name(user_id)
    return "Guest"

# 列表和字典
def process_data(
    items: List[str],
    config: Dict[str, int]
) -> List[int]:
    return [len(item) for item in items]

# 元组
def get_coordinates() -> Tuple[float, float]:
    return (100.5, 200.3)

# 联合类型
def process(value: Union[int, str]) -> str:
    return str(value)

# Python 3.10+ 可以使用 | 语法
def process(value: int | str) -> str:
    return str(value)
```

#### 高级类型
```python
# 泛型 TypeVar
from typing import TypeVar, List

T = TypeVar('T')  # 泛型类型变量

def first(items: List[T]) -> T:
    return items[0]

# Callable - 可调用对象
def apply_func(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

# Literal - 字面量类型
def set_mode(mode: Literal["dev", "prod"]) -> None:
    pass

# Protocol - 协议（结构子类型）
from typing import Protocol

class SupportsClose(Protocol):
    def close(self) -> None: ...

def close_resource(resource: SupportsClose) -> None:
    resource.close()
```

### 1.3 面试高频问题

**Q1: `Optional[T]` 和 `Union[T, None]` 有什么区别？**

```python
# 答案：它们是等价的
from typing import Optional, Union

# 下面两个定义完全相同
def func1(x: Optional[int]) -> int:
    return x or 0

def func2(x: Union[int, None]) -> int:
    return x or 0

# Optional[T] 是 Union[T, None] 的语法糖
# 使用 Optional 更简洁，语义更清晰
```

**Q2: 什么是类型守卫（Type Guard）？**

  类型守卫是一种机制，用于在运行时检查类型后，
  让类型检查器能够缩小变量的类型推断范围。

  通过定义返回 TypeGuard[具体类型] 的函数，
  告诉类型检查器：当函数返回 True 时，
  参数一定是这个具体类型。

  这解决了 isinstance
  检查后类型检查器无法智能推断的问题。

```python
from typing import Union, TypeGuard

def is_string(value: Union[str, int]) -> TypeGuard[str]:
    return isinstance(value, str)

def process(value: Union[str, int]) -> int:
    if is_string(value):
        # 这里 value 被推断为 str 类型
        return len(value)
    else:
        # 这里 value 被推断为 int 类型
        return value * 2
```

**Q3: `List[int]` 和 `list[int]` 有什么区别？**

```python
# 答案：Python 3.9+ 的内置语法
# 3.9 之前必须用 typing.List
# 3.9+ 可以直接用 list, dict, tuple 等

# 推荐写法（Python 3.9+）
def process(items: list[int]) -> int:
    return sum(items)

# 旧写法（向后兼容）
def process(items: List[int]) -> int:
    return sum(items)
```

**Q4: `Any` 类型的使用场景？**

```python
from typing import Any

# 使用场景：
# 1. 处理不确定类型的动态数据
def deserialize(data: Any) -> dict:
    # json.loads 返回的类型不确定
    return json.loads(data)

# 2. 遗留代码迁移
def legacy_api(param: Any) -> Any:
    # 暂时不确定类型，后续重构
    pass

# 注意：Any 是"逃逸类型"，使用后类型检查会失效
# 尽量避免在类型系统核心使用 Any
```

---

## 二、装饰器

### 2.1 装饰器原理

**核心概念：**
```python
# 装饰器的本质
def my_decorator(func):
    def wrapper(*args, **kwargs):
        # 前置逻辑
        print("调用前")
        result = func(*args, **kwargs)
        # 后置逻辑
        print("调用后")
        return result
    return wrapper

# 使用装饰器
@my_decorator
def greet(name):
    print(f"Hello, {name}")

# 等价于
greet = my_decorator(greet)
```

**面试标准解释：**

- 装饰器是一个函数，接收函数作为参数，返回一个新函数
- 使用 `@` 语法糖简化应用
- 新函数通常会包裹原函数，添加额外功能

### 2.2 带参数的装饰器

```python
def repeat(times: int):
    """重复执行装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            results = []
            for _ in range(times):
                results.append(func(*args, **kwargs))
            return results
        return wrapper
    return decorator

@repeat(times=3)
def say_hello():
    return "Hello"

# say_hello() 返回 ["Hello", "Hello", "Hello"]
```

### 2.3 类装饰器

```python
class CountCalls:
    """统计调用次数的类装饰器"""

    def __init__(self, func):
        self.func = func
        self.count = 0

    def __call__(self, *args, **kwargs):
        self.count += 1
        print(f"第 {self.count} 次调用")
        return self.func(*args, **kwargs)

@CountCalls
def calculate(x, y):
    return x + y
```

### 2.4 保留元信息

装饰器会返回一个新函数 wrapper，替换原函数。
  这导致原函数的元信息（名称、文档等）丢失。

  @functools.wraps 是一个装饰器，用于将原函数的元信息
  复制到 wrapper 函数上，让 wrapper "伪装" 成原函数。

  这样既保留了装饰器的功能，又保持了原函数的身份信息，
  对调试、文档生成、单元测试等都非常重要。

```python
import functools

def my_decorator(func):
    @functools.wraps(func)  # 保留原函数的元信息
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def important_function():
    """这个文档很重要"""
    pass

print(important_function.__name__)  # 输出: important_function
print(important_function.__doc__)    # 输出: 这个文档很重要
```

### 2.5 面试高频问题

**Q1: `@staticmethod`、`@classmethod` 和普通方法的区别？**

```python
class MyClass:
    def instance_method(self):
        # 可以访问实例属性和类属性
        # 需要通过实例调用
        pass

    @staticmethod
    def static_method():
        # 无法访问实例或类属性
        # 相当于普通函数，只是放在类里面
        pass

    @classmethod
    def class_method(cls):
        # 可以访问类属性，无法访问实例属性
        # 第一个参数是类本身
        pass

# 使用场景：
# instance_method: 需要操作实例数据
# static_method: 工具方法，与类和实例无关
# class_method: 需要操作类级别的数据或创建实例
```

**Q2: `@property` 装饰器的作用？**

```python
class Temperature:
    def __init__(self, celsius):
        self._celsius = celsius

    @property
    def celsius(self):
        """获取摄氏度"""
        return self._celsius

    @property
    def fahrenheit(self):
        """自动计算华氏度"""
        return self._celsius * 9/5 + 32

    @celsius.setter
    def celsius(self, value):
        """设置时进行验证"""
        if value < -273.15:
            raise ValueError("绝对零度以下不可能")
        self._celsius = value

# 使用
temp = Temperature(25)
print(temp.fahrenheit)  # 自动计算：77.0
temp.celsius = 30       # 调用 setter
```

**Q3: FastAPI 中的装饰器是如何工作的？**

```python
from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter(prefix="/api")

# FastAPI 将路由函数注册到路由表
# 通过装饰器收集元数据（HTTP方法、路径、参数等）
@router.get("/products")
async def get_products():
    return {"products": []}

app.include_router(router)

# 底层原理：
# 1. @router.get 返回一个装饰器函数
# 2. 装饰器函数接收路由函数作为参数
# 3. 将函数信息注册到路由器的路由表中
# 4. 返回原函数（或修改后的函数）
```

---

## 三、异常处理

### 3.1 异常层次结构

```python
# Python 异常层次
BaseException
├── SystemExit          # sys.exit()
├── KeyboardInterrupt  # Ctrl+C
├── GeneratorExit     # 生成器关闭
└── Exception         # 用户异常基类
    ├── StopIteration # 迭代结束
    ├── ArithmeticError
    │   ├── ZeroDivisionError  # 除零
    │   └── OverflowError      # 溢出
    ├── LookupError
    │   ├── IndexError         # 索引越界
    │   └── KeyError           # 键不存在
    ├── TypeError             # 类型错误
    ├── ValueError            # 值错误
    ├── AttributeError        # 属性不存在
    ├── RuntimeError          # 运行时错误
    └── ... 更多
```

### 3.2 完整的异常处理

```python
try:
    # 可能抛出异常的代码
    result = 10 / 0
except ZeroDivisionError as e:
    # 捕获特定异常
    print(f"除零错误: {e}")
except (ValueError, TypeError) as e:
    # 捕获多个异常
    print(f"类型或值错误: {e}")
except Exception as e:
    # 捕获所有异常（慎用）
    print(f"未知错误: {e}")
else:
    # 没有异常时执行
    print("计算成功")
finally:
    # 无论是否有异常都执行
    print("清理资源")
```

### 3.3 自定义异常

```python
# 你的项目中的异常定义
class FetchException(Exception):
    """抓取失败的基类异常"""
    pass

class InvalidURLException(FetchException):
    """无效的 URL"""
    pass

class PriceNotFoundException(FetchException):
    """未找到价格信息"""
    pass

class NetworkException(FetchException):
    """网络错误"""
    pass

# 使用自定义异常
async def scrape_price(url: str) -> float:
    try:
        if not is_valid_url(url):
            raise InvalidURLException(f"无效的 URL: {url}")

        html = await fetch_html(url)
        price = extract_price(html)

        if price is None:
            raise PriceNotFoundException("未找到价格")

        return price

    except Exception as e:
        # 将底层异常包装为业务异常
        raise FetchException(f"抓取失败: {e}") from e
```

### 3.4 上下文管理器处理异常

```python
class Resource:
    def __init__(self):
        self.acquired = False

    def __enter__(self):
        print("获取资源")
        self.acquired = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("释放资源")
        self.acquired = False

        # 返回 True 会抑制异常
        # 返回 None 或 False 会让异常继续传播
        if exc_type is ValueError:
            print("捕获到 ValueError，不传播")
            return True

        return False

# 使用
with Resource():
    print("使用资源")
    raise ValueError("测试异常")  # 被抑制

print("继续执行")

with Resource():
    print("使用资源")
    raise RuntimeError("测试异常")  # 会传播
```

### 3.5 面试高频问题

**Q1: `raise ... from e` 的作用？**

```python
try:
    result = risky_operation()
except ValueError as e:
    # from e 保留原始异常链
    raise BusinessError("业务处理失败") from e

# 这样可以保留完整的异常追踪信息
# 方便调试时找到根本原因
```

**Q2: 什么时候应该捕获异常，什么时候应该抛出？**

```python
# 应该捕获异常：
# 1. 可以恢复的情况
def connect_to_database():
    for attempt in range(3):
        try:
            return Database.connect()
        except ConnectionError:
            if attempt == 2:
                raise
            time.sleep(1)

# 2. 需要转换异常类型
try:
    result = external_api_call()
except ExternalAPIError as e:
    raise InternalError("外部服务不可用") from e

# 3. 需要清理资源
with open_file() as f:
    try:
        process_file(f)
    except IOError:
        log_error()
        raise

# 应该抛出异常：
# 1. 调用者无法处理的情况
def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("除数不能为零")
    return a / b

# 2. 前置条件不满足
def get_user(user_id: int):
    if user_id <= 0:
        raise ValueError("用户 ID 必须为正数")
    return fetch_user(user_id)
```

**Q3: `try-except` 的性能影响？**

```python
# 常见误解：try-except 很慢

# 实际上：
# 1. Python 的异常处理机制很高效
# 2. 没有异常时，性能影响很小
# 3. 有异常时，会慢一些（抛出和捕获异常的开销）

# 风格建议：
# 1. 正常流程不要用异常处理
# 2. 预期可能的异常才用 try-except

# 不好的做法：
def get_first_char(text):
    try:
        return text[0]
    except IndexError:  # 预期可能发生的错误
        return ""

# 更好的做法：
def get_first_char(text):
    return text[0] if text else ""

# 好的做法：
def parse_int(s):
    try:
        return int(s)
    except ValueError:  # 预期可能的错误
        return 0
```

---

## 四、上下文管理器

### 4.1 基础上下文管理器

```python
class DatabaseConnection:
    def __init__(self, database_url):
        self.url = database_url
        self.connection = None

    def __enter__(self):
        print("建立数据库连接")
        self.connection = connect(self.url)
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("关闭数据库连接")
        if self.connection:
            self.connection.close()

        # 返回 True 抑制异常，False 让异常继续传播
        return False

# 使用
with DatabaseConnection("postgresql://...") as conn:
    conn.execute("SELECT * FROM users")
# 自动关闭连接
```

### 4.2 异步上下文管理器

```python
class AsyncDatabaseConnection:
    def __init__(self, database_url):
        self.url = database_url
        self.connection = None

    async def __aenter__(self):
        print("异步建立数据库连接")
        self.connection = await async_connect(self.url)
        return self.connection

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        print("异步关闭数据库连接")
        if self.connection:
            await self.connection.close()
        return False

# 使用 - 你的项目中的 SQLModel
async def get_products():
    async with AsyncSession(engine) as session:
        result = await session.execute(select(Product))
        return result.scalars().all()
    # 自动关闭会话
```

### 4.3 contextlib 简化上下文管理器

```python
from contextlib import contextmanager

@contextmanager
def database_transaction(session):
    """简化的数据库事务上下文管理器"""
    try:
        yield session  # 返回给 with 语句
        session.commit()
    except Exception:
        session.rollback()
        raise

# 使用
with database_transaction(session) as sess:
    sess.add(Product(name="Game"))
    sess.add(Product(name="App"))
# 自动提交或回滚

# 异步版本
from contextlib import asynccontextmanager

@asynccontextmanager
async def async_database_transaction(session):
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
```

### 4.4 面试高频问题

**Q1: `with` 语句的优势是什么？**

```python
# 优势：
# 1. 自动资源清理 - 不用手动调用 close
# 2. 异常安全 - 即使发生异常也会清理
# 3. 代码简洁 - 减少重复代码
# 4. 明确作用域 - 资源的生命周期清晰

# 对比：
# 不用 with
file = open("data.txt")
try:
    data = file.read()
    process(data)
finally:
    file.close()  # 容易忘记

# 用 with
with open("data.txt") as file:
    data = file.read()
    process(data)
# 自动关闭
```

**Q2: 如何实现一个计时上下文管理器？**

```python
import time
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    """计时上下文管理器"""
    start = time.time()
    print(f"{name} 开始")
    try:
        yield
    finally:
        elapsed = time.time() - start
        print(f"{name} 完成，耗时: {elapsed:.2f}s")

# 使用
with timer("数据库查询"):
    result = await database.query()

# 输出：
# 数据库查询 开始
# 数据库查询 完成，耗时: 0.34s
```

**Q3: 嵌套 with 语句的处理？**

```python
# 嵌套使用
with open("input.txt") as infile, open("output.txt", "w") as outfile:
    data = infile.read()
    outfile.write(data.upper())

# 或者使用 ExitStack 处理动态数量的资源
from contextlib import ExitStack

def process_files(file_paths):
    with ExitStack() as stack:
        files = [stack.enter_context(open(path)) for path in file_paths]
        # 同时处理多个文件
        for file in files:
            process(file)
    # 自动关闭所有文件
```

---

## 五、生成器与迭代器

### 5.1 迭代器协议

```python
# 迭代器协议：实现 __iter__ 和 __next__ 方法

class Counter:
    """可迭代计数器"""

    def __init__(self, limit):
        self.limit = limit
        self.count = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.count >= self.limit:
            raise StopIteration
        value = self.count
        self.count += 1
        return value

# 使用
counter = Counter(3)
for num in counter:
    print(num)
# 输出: 0 1 2

# 或者手动迭代
counter = Counter(3)
print(next(counter))  # 0
print(next(counter))  # 1
print(next(counter))  # 2
print(next(counter))  # StopIteration
```

### 5.2 生成器

```python
# 生成器：使用 yield 关键字

def countdown(n):
    """倒计时生成器"""
    while n > 0:
        yield n
        n -= 1

# 使用
for i in countdown(5):
    print(i)
# 输出: 5 4 3 2 1

# 生成器表达式（类似列表推导）
squares = (x * x for x in range(10))
# 注意括号，不是 []
```

### 5.3 生成器的高级用法

```python
def fibonacci_generator():
    """斐波那契数列生成器"""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

def filter_even(numbers):
    """过滤偶数"""
    for num in numbers:
        if num % 2 == 0:
            yield num

# 组合生成器
even_fib = filter_even(fibonacci_generator())

# 取前 10 个偶数斐波那契数
import itertools
result = list(itertools.islice(even_fib, 10))#itertools迭代工具
print(result)
```

### 5.4 `yield from` 语法

```python
def flatten(nested_list):
    """展平嵌套列表"""
    for item in nested_list:
        if isinstance(item, list):
            # yield from 委托给子生成器
            yield from flatten(item)#递归
        else:
            yield item

# 使用
nested = [[1, 2], [3, [4, 5]], 6]
for item in flatten(nested):
    print(item)
# 输出: 1 2 3 4 5 6
```

### 5.5 惰性求值的优势

```python
# 列表：立即计算，占用内存
numbers_list = [x * x for x in range(1000000)]
print(sum(numbers_list))  # 需要存储所有元素

# 生成器：惰性计算，节省内存
numbers_gen = (x * x for x in range(1000000))
print(sum(numbers_gen))  # 只计算当前需要的元素

# 处理大数据流时特别有用
def process_large_file(file_path):
    with open(file_path) as file:
        for line in file:  # 逐行读取，不一次性加载
            yield process_line(line)
```

### 5.6 面试高频问题

**Q1: 生成器和迭代器的区别？**

```python
# 区别：
# 1. 实现方式
#    迭代器：实现 __iter__ 和 __next__ 方法
#    生成器：使用 yield 关键字的函数

# 2. 自动实现
#    生成器函数自动实现迭代器协议
#    不需要手动定义 __iter__ 和 __next__

# 3. 简洁性
#    生成器代码更简洁

# 4. 状态保存
#    生成器自动保存和恢复执行状态

# 迭代器版本
class Countdown:
    def __init__(self, n):
        self.n = n

    def __iter__(self):
        return self

    def __next__(self):
        if self.n <= 0:
            raise StopIteration
        self.n -= 1
        return self.n + 1

# 生成器版本
def countdown(n):
    while n > 0:
        yield n
        n -= 1
```

**Q2: 下面代码输出什么？**

```python
def gen():
    for i in range(3):
        yield i
        print(f"After yield {i}")

g = gen()
print(next(g))
print(next(g))

# 答案：
# 0
# After yield 0
# 1

# 解释：
# 1. next(g) 执行到第一个 yield i，返回 0
# 2. print(f"After yield {i}") 执行，输出 "After yield 0"
# 3. next(g) 继续执行，到第二个 yield i，返回 1
# 4. print(f"After yield {i}") 会等待下一次 next() 调用
```

**Q3: 生成器的 send() 方法？**

```python
def interactive_generator():
    """可交互的生成器"""
    received = yield "Ready"
    while True:
        received = yield f"Received: {received}"

gen = interactive_generator()
print(next(gen))  # 输出: Ready
print(gen.send("Hello"))  # 输出: Received: Hello
print(gen.send("World"))  # 输出: Received: World

# send() 可以向生成器发送数据
# 第一次必须用 next() 或 send(None) 启动
```

---

## 六、类与面向对象

### 6.1 类和实例的区别

```python
class Product:
    # 类属性：所有实例共享
    count = 0

    def __init__(self, name: str, price: float):
        # 实例属性：每个实例独立
        self.name = name
        self.price = price
        Product.count += 1  # 修改类属性

# 实例化
product1 = Product("Game", 99.99)
product2 = Product("App", 49.99)

print(product1.name)  # 实例属性: "Game"
print(product2.name)  # 实例属性: "App"
print(product1.count)  # 类属性: 2
print(product2.count)  # 类属性: 2（共享）
```

### 6.2 `self` 的作用

```python
class Product:
    def __init__(self, name):
        # self 指向当前实例
        self.name = name

    def display(self):
        # self 可以访问实例属性
        print(f"Product: {self.name}")

# Python 自动传递 self 参数
product = Product("Game")
product.display()  # 等价于 Product.display(product)
```

### 6.3 继承

```python
# 你的项目中的继承示例
class BaseScraper:
    """爬虫基类"""

    def scrape(self, url: str) -> float:
        """抓取价格"""
        html = self._fetch_page(url)
        return self._parse_price(html)

    def _fetch_page(self, url: str) -> str:
        """获取页面"""
        raise NotImplementedError

    def _parse_price(self, html: str) -> float:
        """解析价格"""
        raise NotImplementedError

class SteamScraper(BaseScraper):
    """Steam 爬虫"""

    def _fetch_page(self, url: str) -> str:
        # 实现具体的抓取逻辑
        return httpx.get(url).text

    def _parse_price(self, html: str) -> float:
        # 实现具体的解析逻辑
        soup = BeautifulSoup(html, "lxml")
        price_text = soup.select_one(".discount_final_price").text
        return parse_price(price_text)
```

### 6.4 多态

```python
from abc import ABC, abstractmethod

class PaymentProcessor(ABC):
    """支付处理器接口"""

    @abstractmethod
    def process_payment(self, amount: float) -> bool:
        pass

class CreditCardPayment(PaymentProcessor):
    def process_payment(self, amount: float) -> bool:
        print(f"信用卡支付: {amount}")
        return True

class PayPalPayment(PaymentProcessor):
    def process_payment(self, amount: float) -> bool:
        print(f"PayPal 支付: {amount}")
        return True

# 多态使用
def make_payment(processor: PaymentProcessor, amount: float):
    # 不需要知道具体是哪种支付方式
    success = processor.process_payment(amount)
    return success

# 可以传入任何实现了 PaymentProcessor 的类
make_payment(CreditCardPayment(), 100.0)
make_payment(PayPalPayment(), 50.0)
```

### 6.5 魔术方法

```python
class Product:
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price

    def __str__(self):
        """面向用户的字符串表示"""
        return f"{self.name} - ${self.price:.2f}"

    def __repr__(self):
        """面向开发者的字符串表示（可 eval）"""
        return f"Product(name='{self.name}', price={self.price})"

    def __eq__(self, other):
        """相等性比较"""
        if not isinstance(other, Product):
            return False
        return self.name == other.name and self.price == other.price

    def __lt__(self, other):
        """小于比较（用于排序）"""
        return self.price < other.price

    def __add__(self, other):
        """加法运算"""
        return self.price + other.price

product = Product("Game", 99.99)
print(product)              # 调用 __str__: "Game - $99.99"
print(repr(product))        # 调用 __repr__: "Product(name='Game', price=99.99)"
```

### 6.6 属性访问控制

```python
class Product:
    def __init__(self, name: str, price: float):
        # 私有属性（约定）：_前缀
        self._name = name
        # 私有属性（名称改写）：__前缀
        self.__price = price

    @property
    def name(self):
        """只读属性"""
        return self._name

    @property
    def price(self):
        """获取价格"""
        return self.__price

    @price.setter
    def price(self, value: float):
        """设置价格（带验证）"""
        if value < 0:
            raise ValueError("价格不能为负数")
        self.__price = value

    def display(self):
        # 内部访问 __price 会被改写为 _Product__price
        print(f"{self._name}: ${self._Product__price}")

# Python 没有真正的私有，只是约定
product = Product("Game", 99.99)
print(product.name)        # Game
# product._name = "Hack"  # 可以访问，但不推荐
# product.__price         # 会报错，改名为 _Product__price
```

### 6.7 面试高频问题

**Q1: `__init__` 和 `__new__` 的区别？**

```python
class MyClass:
    def __new__(cls, *args, **kwargs):
        """创建实例"""
        print("Creating instance...")
        # 调用父类的 __new__ 创建实例
        instance = super().__new__(cls)
        return instance

    def __init__(self, value):
        """初始化实例"""
        print("Initializing instance...")
        self.value = value

# 执行顺序：
# 1. __new__ 创建实例
# 2. __init__ 初始化实例
obj = MyClass(42)

# 使用场景：
# - __new__: 控制实例创建（单例模式、自定义对象创建）
# - __init__: 初始化实例属性

# 单例模式示例
class Singleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**Q2: 什么是鸭子类型（Duck Typing）？**

```python
# "如果它走起来像鸭子，叫起来像鸭子，那它就是鸭子"

class Duck:
    def quack(self):
        print("Quack!")

class Person:
    def quack(self):
        print("I'm quacking like a duck!")

def make_it_quack(thing):
    thing.quack()

# 不需要显式继承或实现接口
make_it_quack(Duck())    # Quack!
make_it_quack(Person())  # I'm quacking like a duck!

# 优势：
# - 代码更灵活
# - 不需要复杂的继承层次
# - 关注行为而非类型
```

**Q3: 方法重载 vs 方法覆盖？**

```python
# Python 不支持方法重载（同名不同参数）
# 但可以使用默认参数或可变参数模拟

class Calculator:
    def add(self, a, b=0, c=0):
        """支持 2-3 个数的加法"""
        return a + b + c

# 方法覆盖：子类重写父类方法

class Animal:
    def speak(self):
        print("Animal speaks")

class Dog(Animal):
    def speak(self):
        print("Dog barks")

class Cat(Animal):
    def speak(self):
        print("Cat meows")

animal = Animal()
dog = Dog()
cat = Cat()

animal.speak()  # Animal speaks
dog.speak()     # Dog barks（覆盖）
cat.speak()     # Cat meows（覆盖）

# 调用父类方法
class Dog(Animal):
    def speak(self):
        super().speak()  # 调用父类方法
        print("Dog barks")
```

---

## 七、面试总结

### 优先级排序

| 知识点 | 重要性 | 面试频率 |
|--------|--------|----------|
| 类型提示 | ⭐⭐⭐⭐⭐ | 90% |
| 装饰器 | ⭐⭐⭐⭐⭐ | 85% |
| 异常处理 | ⭐⭐⭐⭐⭐ | 90% |
| 上下文管理器 | ⭐⭐⭐⭐ | 70% |
| 生成器 | ⭐⭐⭐⭐ | 60% |
| 面向对象 | ⭐⭐⭐⭐⭐ | 95% |

### 面试准备建议

1. **理解原理**：不仅要知道怎么用，还要知道为什么
2. **手写代码**：能够独立写出各个知识点的代码
3. **结合项目**：用项目中的实际例子说明
4. **举一反三**：准备好变种问题的答案

### 自测问题

```python
# 1. 下面代码会输出什么？
def gen():
    yield 1
    yield 2
    return 3

g = gen()
for x in g:
    print(x)

# 2. 这个装饰器有什么问题？
def decorator(func):
    result = func()
    return result

@decorator
def my_func():
    return "Hello"

# 3. 如何实现一个支持 with 语句的计时器？

# 4. 解释多重继承中的 MRO（方法解析顺序）
```

### 项目结合示例

在面试中，可以这样结合你的项目：

```
面试官：请介绍一下你的项目
我：我开发了一个价格监控系统，监控 Steam 游戏价格变化。
   在项目中，我大量使用了 Python 的类型提示和面向对象特性。

面试官：能具体说说吗？
我：比如，我定义了一个 BaseScraper 基类，实现了爬虫的通用接口，
   然后 SteamScraper 继承它，实现了具体的抓取逻辑。这样设计的好处
   是如果将来要支持其他平台，只需要继承 BaseScraper 实现相应的
   方法即可。

面试官：你在项目中使用了装饰器吗？
我：是的，我使用了 FastAPI 框架的装饰器来定义路由，比如
   @router.get("/api/products") 来定义获取产品列表的接口。
   同时，在爬虫模块中，我也自定义了装饰器来处理异常和重试逻辑。

面试官：异常处理是怎么做的？
我：我定义了 FetchException 基类，以及 InvalidURLException、
   PriceNotFoundException 等子类。当抓取失败时，会抛出具体
   的异常，这样可以在上层进行统一的错误处理和日志记录。
```

---

**祝你面试顺利！**