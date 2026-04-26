# 异步编程面试完全指南

> 基于 Price Monitor 项目，深入讲解 Python 异步编程的面试核心知识点

---

## 目录

- [一、异步编程核心概念](#一异步编程核心概念)
- [二、AsyncIO 详解](#二asyncio-详解)
- [三、异步数据库操作](#三异步数据库操作)
- [四、异步 HTTP 客户端](#四异步-http-客户端)
- [五、异步编程进阶](#五异步编程进阶)
- [六、常见面试题汇总](#六常见面试题汇总)

---

## 一、异步编程核心概念

### 1.1 什么是异步编程？

**定义**：异步编程是一种非阻塞的编程模式，允许程序在等待 I/O 操作（如网络请求、数据库查询、文件读写）完成时，去执行其他任务，而不是傻傻地等待。

**生活类比**：

```
同步模式（传统餐厅）：
你点餐 → 等待厨师做完 → 你吃饭 → 下一个顾客点餐
问题：你等待的时候，后面的顾客都在排队

异步模式（快餐店）：
你点餐 → 拿号 → 去找座位玩手机 → 餐好了叫你 → 你取餐
优势：你等待的时候，收银员可以服务下一个顾客
```

### 1.2 同步 vs 异步 vs 并行

| 概念 | 特点 | 适用场景 |
|------|------|----------|
| **同步** | 一件一件做，等待完成 | 简单逻辑、顺序执行 |
| **异步** | 发起后不等待，完成时通知 | I/O 密集型（网络、磁盘） |
| **并行** | 多个 CPU 同时执行 | CPU 密集型（计算） |

**代码对比**：

```python
# 同步版本 - 总耗时 = 1+1+1 = 3秒
import time

def fetch_price_sync(url):
    time.sleep(1)  # 模拟网络请求
    return f"Price from {url}"

def main_sync():
    start = time.time()
    results = []
    for url in ["url1", "url2", "url3"]:
        results.append(fetch_price_sync(url))
    print(f"同步耗时: {time.time() - start:.2f}秒")  # 约3秒
    return results

# 异步版本 - 总耗时 = max(1,1,1) ≈ 1秒
import asyncio

async def fetch_price_async(url):
    await asyncio.sleep(1)  # 模拟网络请求
    return f"Price from {url}"

async def main_async():
    start = time.time()
    # 并发执行三个请求
    results = await asyncio.gather(
        fetch_price_async("url1"),
        fetch_price_async("url2"),
        fetch_price_async("url3")
    )
    print(f"异步耗时: {time.time() - start:.2f}秒")  # 约1秒
    return results

asyncio.run(main_async())
```

### 1.3 为什么你的项目使用异步？

**你的项目中的实际应用**：

```python
# app/routers/products.py
@router.post("/", response_model=schemas.ProductRead)
async def create_product(
    product: schemas.ProductCreate,
    session: AsyncSession = Depends(get_session)
):
    db_product = models.Product.from_orm(product)
    session.add(db_product)
    await session.commit()    # 异步等待数据库写入
    await session.refresh(db_product)  # 异步刷新数据
    return db_product
```

**选择异步的原因**：

1. **高并发场景**：价格监控系统可能同时处理大量请求（查询商品、抓取价格）
2. **I/O 密集型**：主要操作是数据库查询和网络请求
3. **资源效率**：一个线程就能处理成千上万的并发连接
4. **FastAPI 原生支持**：框架本身就是异步的

### 1.4 协程（Coroutine）详解

**什么是协程？**

协程是一种比线程更轻量的并发单元，可以暂停和恢复执行。

```python
# 定义协程函数
async def my_coroutine():
    print("开始")
    await asyncio.sleep(1)  # 暂停点，可以切换到其他协程
    print("结束")

# 调用协程函数不会立即执行，而是返回协程对象
coro = my_coroutine()
print(type(coro))  # <class 'coroutine'>

# 需要通过事件循环来运行
asyncio.run(coro)
```

**协程 vs 线程 vs 进程**：

| 特性 | 进程 | 线程 | 协程 |
|------|------|------|------|
| 切换开销 | 最大 | 中等 | 最小 |
| 内存占用 | MB 级 | MB 级 | KB 级 |
| 并发数量 | 几十个 | 几百个 | 几万个 |
| 数据隔离 | 完全隔离 | 共享内存 | 共享内存 |
| 适用场景 | CPU 密集型 | I/O 密集型 | I/O 密集型 |

---

## 二、AsyncIO 详解

### 2.1 事件循环（Event Loop）

**核心概念**：事件循环是异步编程的"心脏"，负责调度和执行协程。

```
┌─────────────────────────────────────────┐
│            Event Loop                   │
│  ┌─────────────────────────────────┐   │
│  │        Task Queue（任务队列）    │   │
│  │   Task1  Task2  Task3  Task4    │   │
│  └─────────────────────────────────┘   │
│              ↓                          │
│  ┌─────────────────────────────────┐   │
│  │     执行 Task1 遇到 await       │   │
│  │     Task1 挂起，切换到 Task2    │   │
│  └─────────────────────────────────┘   │
│              ↓                          │
│  ┌─────────────────────────────────┐   │
│  │     Task2 完成，Task1 的 I/O    │   │
│  │     也完成了，继续执行 Task1    │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**你的项目中的事件循环**：

```python
# FastAPI 自动管理事件循环
# uvicorn 启动时创建事件循环，处理所有请求

@router.get("/")
async def list_products():  # 每个请求都是一个协程
    result = await session.execute(...)  # 遇到 await 挂起
    # 此时事件循环可以处理其他请求
    return result  # I/O 完成后恢复执行
```

### 2.2 async/await 关键字

**async**：声明一个协程函数

```python
# 普通函数
def normal_func():
    return "result"

# 协程函数
async def async_func():
    return "result"

# 调用方式不同
result = normal_func()           # 直接得到结果
coro = async_func()              # 得到协程对象
result = await async_func()      # 等待协程执行完成
result = asyncio.run(async_func())  # 在事件循环中运行
```

**await**：暂停协程，等待异步操作完成

```python
async def example():
    print("1. 开始")

    # await 暂停当前协程，让出控制权
    # 事件循环可以去执行其他协程
    result = await some_async_operation()

    print("2. 继续执行")  # I/O 完成后恢复
    return result
```

**你的项目中的实际使用**：

```python
# app/scrapers/steam.py
async def _fetch_page(self, url: str) -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        # await 等待 HTTP 请求完成
        # 在等待期间，事件循环可以处理其他请求
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        return response.text
```

### 2.3 asyncio 常用函数

#### 2.3.1 asyncio.run()

**用途**：运行协程的入口点（Python 3.7+）

```python
import asyncio

async def main():
    print("Hello Async!")

# 运行协程
asyncio.run(main())
```

**注意事项**：
- 一个程序只能调用一次 `asyncio.run()`
- 它会创建新的事件循环
- FastAPI/uvicorn 已经管理了事件循环，不需要手动调用

#### 2.3.2 asyncio.gather()

**用途**：并发执行多个协程

```python
import asyncio

async def fetch_price(store: str):
    await asyncio.sleep(1)
    return f"{store}: ¥99"

async def main():
    # 并发抓取多个平台价格
    results = await asyncio.gather(
        fetch_price("Steam"),
        fetch_price("Epic"),
        fetch_price("GOG"),
    )
    print(results)
    # ['Steam: ¥99', 'Epic: ¥99', 'GOG: ¥99']

asyncio.run(main())
```

**在你的项目中的应用场景**：

```python
# 假设要同时抓取多个商品的价格
async def batch_scrape(urls: list[str]):
    tasks = [scraper.scrape(url) for url in urls]
    prices = await asyncio.gather(*tasks, return_exceptions=True)
    return prices
```

**参数说明**：

```python
# return_exceptions=True：异常不会中断其他任务
results = await asyncio.gather(
    task1(),  # 正常
    task2(),  # 抛出异常
    task3(),  # 正常
    return_exceptions=True
)
# results: [result1, Exception(...), result3]
```

#### 2.3.3 asyncio.create_task()

**用途**：创建后台任务，立即返回

```python
async def background_task():
    await asyncio.sleep(5)
    print("后台任务完成")

async def main():
    # 创建任务后立即继续执行
    task = asyncio.create_task(background_task())

    print("主线程继续执行...")

    # 需要时等待任务完成
    await task

asyncio.run(main())
```

#### 2.3.4 asyncio.wait_for()

**用途**：设置超时

```python
async def slow_operation():
    await asyncio.sleep(10)
    return "完成"

async def main():
    try:
        # 最多等待3秒
        result = await asyncio.wait_for(
            slow_operation(),
            timeout=3.0
        )
    except asyncio.TimeoutError:
        print("操作超时！")

asyncio.run(main())
```

### 2.4 异步上下文管理器

**同步版本**：

```python
# 使用 __enter__ 和 __exit__
class SyncContext:
    def __enter__(self):
        print("进入")
        return self

    def __exit__(self, *args):
        print("退出")

with SyncContext():
    print("执行中")
```

**异步版本**：

```python
# 使用 __aenter__ 和 __aexit__
class AsyncContext:
    async def __aenter__(self):
        print("进入")
        return self

    async def __aexit__(self, *args):
        print("退出")

async def main():
    async with AsyncContext():
        print("执行中")

asyncio.run(main())
```

**你的项目中的实际使用**：

```python
# app/database.py
async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    async with async_session() as session:  # 异步上下文管理器
        yield session
        # 自动关闭会话，释放资源
```

```python
# app/scrapers/steam.py
async with httpx.AsyncClient(timeout=10.0) as client:
    response = await client.get(url)
    # 自动关闭 HTTP 连接
```

---

## 三、异步数据库操作

### 3.1 为什么数据库操作要异步？

**同步数据库的问题**：

```
请求1 → 查询数据库（等待100ms）→ 返回
请求2 → 查询数据库（等待100ms）→ 返回
请求3 → 查询数据库（等待100ms）→ 返回
总耗时：300ms
```

**异步数据库的优势**：

```
请求1 → 发起查询 → 等待 → 返回
请求2 → 发起查询 → 等待 → 返回
请求3 → 发起查询 → 等待 → 返回
总耗时：约100ms（三个查询几乎同时进行）
```

### 3.2 你的项目中的异步数据库配置

```python
# app/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 注意 URL 前缀是 postgresql+asyncpg
# asyncpg 是 PostgreSQL 的异步驱动
DATABASE_URL = "postgresql+asyncpg://admin:mypassword@localhost:5432/monitor_db"

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=True,      # 打印 SQL 日志
    future=True,    # 使用 SQLAlchemy 2.0 风格
    # pool_size=5,        # 连接池大小
    # max_overflow=10,    # 最大溢出连接数
    # pool_timeout=30,    # 等待连接的超时时间
)

# 创建异步会话工厂
async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False  # 提交后对象不过期
    )
    async with async_session() as session:
        yield session
```

### 3.3 异步 CRUD 操作详解

#### 创建（Create）

```python
@router.post("/", response_model=schemas.ProductRead)
async def create_product(
    product: schemas.ProductCreate,
    session: AsyncSession = Depends(get_session)
):
    # 1. 创建对象
    db_product = models.Product.from_orm(product)

    # 2. 添加到会话（此时还未写入数据库）
    session.add(db_product)

    # 3. 提交事务（异步等待数据库写入）
    await session.commit()

    # 4. 刷新对象（获取数据库生成的字段，如 id）
    await session.refresh(db_product)

    return db_product
```

**面试点：为什么需要 refresh？**

```python
# 提交前
db_product.id  # None（数据库还没生成）

# 提交后但不 refresh
db_product.id  # 可能还是 None（本地对象未更新）

# refresh 后
await session.refresh(db_product)
db_product.id  # 1（从数据库重新加载）
```

#### 读取（Read）

```python
@router.get("/", response_model=List[schemas.ProductRead])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    # 构建查询
    stmt = select(models.Product).offset(skip).limit(limit)

    # 异步执行查询
    result = await session.execute(stmt)

    # 提取结果
    products = result.scalars().all()

    return products
```

**结果提取方法对比**：

```python
result = await session.execute(select(Product))

# scalar() - 获取单个值（第一行第一列）
count = result.scalar()

# scalar_one() - 获取单行，如果没有或有多行会抛异常
product = result.scalar_one()

# scalar_one_or_none() - 获取单行，没有返回 None
product = result.scalar_one_or_none()

# scalars() - 获取所有行的指定列
products = result.scalars().all()

# all() - 获取所有行（元组形式）
rows = result.all()
```

#### 更新（Update）

```python
@router.put("/{product_id}")
async def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    session: AsyncSession = Depends(get_session)
):
    # 1. 查询现有对象
    result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(status_code=404, detail="Not found")

    # 2. 只更新提供的字段
    product_data = product_update.dict(exclude_unset=True)
    for field, value in product_data.items():
        setattr(db_product, field, value)

    # 3. 提交更改
    await session.commit()
    await session.refresh(db_product)

    return db_product
```

#### 删除（Delete）

```python
@router.delete("/{product_id}")
async def delete_product(product_id: int, session: AsyncSession = Depends(get_session)):
    # 1. 查询对象
    result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(status_code=404)

    # 2. 删除对象
    await session.delete(db_product)

    # 3. 提交事务
    await session.commit()

    return db_product
```

### 3.4 异步数据库连接池

**为什么需要连接池？**

```
没有连接池：
请求1 → 建立连接 → 查询 → 关闭连接（耗时）
请求2 → 建立连接 → 查询 → 关闭连接（耗时）

有连接池：
请求1 → 从池中获取连接 → 查询 → 归还连接（快）
请求2 → 从池中获取连接 → 查询 → 归还连接（快）
```

**配置连接池**：

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,        # 常驻连接数
    max_overflow=10,    # 高峰时额外连接数
    pool_timeout=30,    # 等待连接的超时时间（秒）
    pool_recycle=3600,  # 连接回收时间（秒）
)
```

---

## 四、异步 HTTP 客户端

### 4.1 httpx 库介绍

**为什么用 httpx 而不是 requests？**

| 特性 | requests | httpx |
|------|----------|-------|
| 同步请求 | ✅ | ✅ |
| 异步请求 | ❌ | ✅ |
| HTTP/2 | ❌ | ✅ |
| 现代设计 | 较老 | 现代 |

**简单对比**：

```python
# requests（同步，阻塞）
import requests

def fetch_sync():
    response = requests.get("https://api.example.com/data")
    return response.json()

# httpx 异步版本
import httpx

async def fetch_async():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

### 4.2 你的项目中的 httpx 使用

```python
# app/scrapers/steam.py
async def _fetch_page(self, url: str) -> str:
    """异步获取页面内容"""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()  # 检查 HTTP 错误
        return response.text
```

### 4.3 httpx 常用操作

#### 基本请求

```python
import httpx

async def demo():
    async with httpx.AsyncClient() as client:
        # GET 请求
        response = await client.get("https://api.example.com/users")
        data = response.json()

        # POST 请求
        response = await client.post(
            "https://api.example.com/users",
            json={"name": "张三", "age": 25}
        )

        # 带参数的请求
        response = await client.get(
            "https://api.example.com/users",
            params={"page": 1, "limit": 10}
        )

        # 带请求头
        response = await client.get(
            "https://api.example.com/users",
            headers={"Authorization": "Bearer token"}
        )
```

#### 超时设置

```python
# 全局超时
async with httpx.AsyncClient(timeout=30.0) as client:
    ...

# 分别设置连接和读取超时
timeout = httpx.Timeout(
    connect=5.0,    # 连接超时
    read=10.0,      # 读取超时
    write=10.0,     # 写入超时
    pool=5.0        # 从连接池获取连接的超时
)
async with httpx.AsyncClient(timeout=timeout) as client:
    ...
```

#### 异常处理

```python
from httpx import RequestError, HTTPStatusError

async def safe_fetch(url: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()  # 4xx/5xx 抛异常
            return response.text

    except httpx.TimeoutException:
        print("请求超时")
    except httpx.ConnectError:
        print("连接失败")
    except httpx.HTTPStatusError as e:
        print(f"HTTP 错误: {e.response.status_code}")
    except httpx.RequestError as e:
        print(f"请求错误: {e}")
```

### 4.4 并发请求优化

**场景**：同时抓取多个商品价格

```python
import httpx
import asyncio

async def fetch_single_price(client: httpx.AsyncClient, url: str) -> float:
    """抓取单个商品价格"""
    response = await client.get(url)
    # 解析价格逻辑...
    return 99.99

async def fetch_all_prices(urls: list[str]) -> list[float]:
    """并发抓取所有价格"""
    async with httpx.AsyncClient() as client:
        # 创建所有任务
        tasks = [fetch_single_price(client, url) for url in urls]
        # 并发执行
        prices = await asyncio.gather(*tasks, return_exceptions=True)
        return prices

# 使用
urls = [
    "https://store.steampowered.com/app/1",
    "https://store.steampowered.com/app/2",
    "https://store.steampowered.com/app/3",
]
prices = asyncio.run(fetch_all_prices(urls))
```

**性能对比**：

```
同步版本：10 个请求 × 1 秒 = 10 秒
异步版本：10 个请求并发 ≈ 1 秒
```

---

## 五、异步编程进阶

### 5.1 在同步代码中调用异步

```python
import asyncio

async def async_function():
    await asyncio.sleep(1)
    return "异步结果"

# 方法1：asyncio.run()（Python 3.7+）
def sync_call_async_1():
    result = asyncio.run(async_function())
    return result

# 方法2：获取事件循环（不推荐，但有时必要）
def sync_call_async_2():
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(async_function())
    return result

# 方法3：在已有事件循环中（如在 FastAPI 中）
async def in_fastapi():
    result = await async_function()
    return result
```

### 5.2 在异步代码中调用同步

**问题**：同步代码会阻塞事件循环

```python
# 错误示例
async def bad_example():
    time.sleep(5)  # 阻塞整个事件循环！
    # 在这5秒内，所有请求都无法处理
```

**解决方案1**：使用异步库替代

```python
# 用 asyncio.sleep 替代 time.sleep
async def good_example():
    await asyncio.sleep(5)  # 不阻塞，可以切换
```

**解决方案2**：使用 run_in_executor

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def blocking_function():
    time.sleep(5)
    return "结果"

async def main():
    # 在线程池中运行同步代码
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,  # 使用默认线程池
        blocking_function
    )
    return result
```

### 5.3 FastAPI 中的异步最佳实践

**规则1**：如果操作是异步的，使用 `async def`

```python
# ✅ 正确
@router.get("/")
async def get_data(session: AsyncSession = Depends(get_session)):
    result = await session.execute(...)
    return result
```

**规则2**：如果操作是同步阻塞的，使用普通 `def`

```python
# ✅ 正确 - FastAPI 会在线程池中运行
@router.get("/cpu-intensive")
def calculate():
    result = heavy_cpu_calculation()  # CPU 密集型
    return result
```

**规则3**：不要混用

```python
# ❌ 错误 - 阻塞事件循环
@router.get("/")
async def bad():
    time.sleep(5)  # 阻塞！
    return "done"

# ✅ 正确
@router.get("/")
async def good():
    await asyncio.sleep(5)  # 不阻塞
    return "done"
```

### 5.4 异步迭代器

```python
# 异步生成器
async def async_range(n: int):
    for i in range(n):
        await asyncio.sleep(0.1)
        yield i

# 使用 async for
async def main():
    async for num in async_range(5):
        print(num)

# 使用 async comprehensions
async def main2():
    result = [i async for i in async_range(5)]
    print(result)  # [0, 1, 2, 3, 4]

asyncio.run(main2())
```

---

## 六、常见面试题汇总

### Q1：什么是协程？与线程有什么区别？

**答案**：

```
协程：
- 用户态的轻量级线程
- 由程序控制切换，不是操作系统
- 切换开销极小（只保存寄存器状态）
- 一个线程可以运行多个协程
- 适合 I/O 密集型任务

线程：
- 内核态的执行单元
- 由操作系统调度
- 切换开销较大（需要内核参与）
- 适合 CPU 密集型任务（多核）
```

### Q2：async/await 是如何工作的？

**答案**：

```python
async def example():
    result = await some_async_operation()
    return result

# 工作原理：
# 1. async def 定义协程函数，调用它返回协程对象
# 2. await 暂停当前协程，将控制权还给事件循环
# 3. 事件循环执行其他协程
# 4. 当异步操作完成，事件循环恢复执行当前协程
# 5. await 表达式返回异步操作的结果
```

### Q3：什么时候用异步，什么时候用多线程/多进程？

**答案**：

| 场景 | 推荐方案 | 原因 |
|------|----------|------|
| 网络请求密集 | 异步 | 等待时间可以处理其他请求 |
| 数据库查询密集 | 异步 | 同上 |
| 文件读写密集 | 异步 | 同上 |
| CPU 计算密集 | 多进程 | 绕过 GIL，利用多核 |
| 混合型 | 异步 + 线程池 | 用 run_in_executor 处理 CPU 任务 |

### Q4：什么是 GIL？对异步有什么影响？

**答案**：

```
GIL（Global Interpreter Lock）：
- Python 的全局解释器锁
- 同一时刻只有一个线程执行 Python 字节码
- 限制多线程的并行能力

对异步的影响：
- 异步是单线程的，不受 GIL 影响
- 异步在等待 I/O 时会释放 GIL
- 异步 + 多线程可以配合使用
- CPU 密集型任务需要多进程绕过 GIL
```

### Q5：你项目中如何使用异步的？为什么要用异步？

**答案**（结合你的项目）：

```
在我的价格监控项目中，我全面采用了异步编程：

1. 数据库操作：
   - 使用 asyncpg 作为 PostgreSQL 异步驱动
   - 所有 CRUD 操作都是异步的
   - await session.execute() 不阻塞其他请求

2. 爬虫模块：
   - 使用 httpx.AsyncClient 异步抓取网页
   - 可以同时抓取多个商品价格
   - 大大提高了爬虫效率

3. FastAPI 路由：
   - 所有路由函数都是 async def
   - 使用依赖注入获取异步会话

为什么用异步：
- 价格监控是典型的 I/O 密集型应用
- 需要处理大量数据库查询和网络请求
- 异步可以用单个线程处理高并发
- FastAPI 原生支持异步，性能更好
```

### Q6：asyncio.gather() 和 asyncio.wait() 有什么区别？

**答案**：

```python
# gather - 按顺序返回结果
results = await asyncio.gather(task1(), task2(), task3())
# results[0] 是 task1 的结果

# wait - 返回完成和未完成的任务集合
done, pending = await asyncio.wait(
    [task1(), task2(), task3()],
    return_when=asyncio.ALL_COMPLETED
)
# 需要手动获取结果

# gather 更简洁，wait 更灵活
```

### Q7：如何处理异步代码中的异常？

**答案**：

```python
# 方法1：try-except
async def safe_task():
    try:
        result = await risky_operation()
        return result
    except Exception as e:
        logger.error(f"Error: {e}")
        return None

# 方法2：gather 的 return_exceptions
results = await asyncio.gather(
    task1(),
    task2(),  # 可能抛异常
    task3(),
    return_exceptions=True
)
# results: [result1, Exception(...), result3]

# 你的项目中的实际例子
async def scrape(self, url: str) -> float:
    try:
        html = await self._fetch_page(url)
        price = self._parse_price(html)
        return price
    except httpx.RequestError as e:
        raise FetchException(f"Failed to fetch: {e}")
    except Exception as e:
        raise ParseException(f"Failed to parse: {e}")
```

### Q8：异步数据库连接池是什么？为什么需要？

**答案**：

```
连接池是预先创建并复用的数据库连接集合。

为什么需要：
1. 建立连接开销大（TCP 握手、认证）
2. 频繁创建/销毁连接影响性能
3. 连接数有限，需要合理管理

我的项目中的配置：
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,        # 常驻5个连接
    max_overflow=10,    # 高峰时最多15个
    pool_timeout=30,    # 等待超时30秒
)

工作流程：
1. 请求到来，从池中获取连接
2. 执行查询
3. 归还连接到池中
4. 其他请求可以复用
```

### Q9：如何在同步框架（如 Flask）中使用异步？

**答案**：

```python
from flask import Flask
import asyncio

app = Flask(__name__)

async def async_operation():
    await asyncio.sleep(1)
    return "异步结果"

@app.route("/")
def sync_route():
    # 在同步路由中运行异步代码
    result = asyncio.run(async_operation())
    return result

# 或者使用 asgiref
from asgiref.sync import async_to_sync

@app.route("/")
def sync_route():
    result = async_to_sync(async_operation)()
    return result
```

### Q10：异步代码的性能优势有多大？

**答案**：

```
假设：
- 单次数据库查询耗时 10ms
- 需要处理 100 个并发请求

同步模式：
- 每个请求等待前一个完成
- 总耗时 = 100 × 10ms = 1000ms

异步模式：
- 所有请求几乎同时发起
- 总耗时 ≈ 10ms（理论上）

实际效果：
- 根据我的项目经验，异步可以提升 5-10 倍吞吐量
- 特别是在网络请求和数据库操作多的场景
- FastAPI + 异步比 Flask + 同步性能好很多
```

---

## 面试要点总结

### 必须掌握

1. **async/await 语法**
   - async def 定义协程
   - await 等待异步操作
   - 协程 vs 函数 vs 线程

2. **asyncio 核心**
   - 事件循环概念
   - asyncio.run()
   - asyncio.gather()
   - 异步上下文管理器

3. **异步数据库**
   - 异步驱动（asyncpg）
   - AsyncSession 使用
   - 连接池配置

4. **异步 HTTP**
   - httpx.AsyncClient
   - 超时设置
   - 异常处理

### 高频追问

1. "你为什么在项目中使用异步？"
2. "异步和同步有什么区别？什么时候用哪个？"
3. "什么是事件循环？"
4. "如何在异步代码中处理异常？"
5. "asyncio.gather() 是做什么的？"

### 项目结合话术

```
"在我的价格监控项目中，我使用 FastAPI + SQLModel + PostgreSQL
构建了完全异步的后端。

具体来说：
- 数据库操作使用 asyncpg 驱动和 AsyncSession
- 爬虫使用 httpx.AsyncClient 异步抓取网页
- 所有 API 路由都是 async def

这样设计的好处是：
- 单个 worker 可以处理大量并发请求
- 在等待数据库或网络响应时，可以处理其他请求
- 系统吞吐量大大提高

实际效果：
- 10 个并发请求，同步可能需要 1 秒
- 异步只需要约 100ms"
```

---

## 参考资源

- [Python asyncio 官方文档](https://docs.python.org/zh-cn/3/library/asyncio.html)
- [FastAPI 异步文档](https://fastapi.tiangolo.com/async/)
- [httpx 官方文档](https://www.python-httpx.org/)
- [SQLAlchemy 异步文档](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
