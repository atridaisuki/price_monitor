# Python Web 后端实习面试准备指南

> 基于价格监控项目，整理后端开发实习面试所需掌握的知识点和细节

---

## 目录

- [一、Python 基础（必考）](#一python-基础必考)
- [二、Web 框架核心](#二web-框架核心)
- [三、数据库与 ORM](#三数据库与-orm)
- [四、异步编程](#四异步编程)
- [五、RESTful API 设计](#五restful-api-设计)
- [六、Docker 与部署](#六docker-与部署)
- [七、Git 版本控制](#七git-版本控制)
- [八、爬虫与反爬](#八爬虫与反爬)
- [九、数据结构与算法](#九数据结构与算法)
- [十、系统设计基础](#十系统设计基础)
- [十一、性能优化](#十一性能优化)
- [十二、测试](#十二测试)
- [十三、常见面试问题](#十三常见面试问题)

---

## 一、Python 基础（必考）

### 1.1 类型提示（Type Hinting）

**你的项目中用到**：
```python
from typing import Optional, List, Dict, Union

def greet(name: Optional[str] = None) -> str:
    return f"Hello, {name or 'Guest'}"
```

**面试要点**：
- 为什么使用类型提示？（代码可读性、IDE 提示、静态检查）
- `Optional[T]` vs `Union[T, None]`
- `List[T]`、`Dict[K, V]`、`Tuple[T, ...]`
- `Any` 的使用场景

**高频问题**：
```python
# 问：下面有什么区别？
def func1(data: dict):
    pass

def func2(data: Dict[str, int]):
    pass

# 答：func2 更严格，限制了键是字符串，值是整数
```

### 1.2 装饰器（Decorator）

**面试要点**：
- 装饰器原理（函数作为参数、返回新函数）
- `@staticmethod`、`@classmethod`、`@property`
- FastAPI 中的装饰器（`@router.get`、`@app.on_event`）

**常见问题**：
```python
# 问：这个装饰器做了什么？
def timing(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"耗时: {time.time() - start}")
        return result
    return wrapper

@timing
def slow_function():
    time.sleep(1)

# 答：记录函数执行时间
```

### 1.3 异常处理

**你的项目中用到**：
```python
from app.scrapers.exceptions import FetchException

try:
    price = await scraper.scrape(url)
except FetchException as e:
    logger.error(f"抓取失败: {e}")
```

**面试要点**：
- `try-except-else-finally` 结构
- 自定义异常（继承 `Exception`）
- 异常层次结构（你的项目中就有）
- 什么时候捕获异常，什么时候向上抛出

### 1.4 上下文管理器

**你的项目中用到**：
```python
# AsyncSession 是上下文管理器
async with AsyncSession(engine) as session:
    result = await session.execute(...)
# 自动关闭连接
```

**面试要点**：
- `__enter__` 和 `__exit__` 方法
- `with` 语句的作用（自动资源清理）
- 异步上下文管理器（`__aenter__`、`__aexit__`）

### 1.5 生成器与迭代器

**面试要点**：
- 生成器表达式（`x for x in range(10)`）
- `yield` 关键字
- 惰性求值（节省内存）
- `yield from` 用法

**常见问题**：
```python
# 问：下面输出什么？
def gen():
    for i in range(3):
        yield i
        print(f"After yield {i}")

g = gen()
print(next(g))
print(next(g))

# 答：
# 0
# After yield 0
# 1
```

### 1.6 类与面向对象

**你的项目中用到**：
```python
class SteamScraper(BaseScraper):
    def is_valid_url(self, url: str) -> bool:
        return self.STEAM_STORE_DOMAIN in url
```

**面试要点**：
- 类和实例的区别
- `self` 的作用
- `__init__` 方法
- 继承（你的项目：`SteamScraper` 继承 `BaseScraper`）
- 多态（抽象类、接口）

---

## 二、Web 框架核心

### 2.1 HTTP 协议基础

**面试必考**：
- HTTP 方法（GET、POST、PUT、DELETE、PATCH）
- 状态码（200、201、400、404、500）
- 请求头（Content-Type、Authorization、User-Agent）
- 响应头（Content-Type、Cache-Control）
- HTTPS vs HTTP

**你的项目中的实践**：
```python
@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate):
    # POST 创建资源，返回 201 Created
    pass
```

**高频问题**：
```
Q: GET 和 POST 的区别？
A: GET 用于获取数据，参数在 URL 中，有长度限制
   POST 用于提交数据，参数在 Body 中，无长度限制

Q: 401 和 403 的区别？
A: 401 未认证（未登录）
   403 已认证但无权限
```

### 2.2 RESTful API 设计

**你的项目中遵循 RESTful**：

| 操作 | HTTP 方法 | 端点 | 状态码 |
|------|-----------|------|--------|
| 创建 | POST | `/api/products/` | 201 |
| 列表 | GET | `/api/products/` | 200 |
| 详情 | GET | `/api/products/{id}` | 200 |
| 更新 | PUT | `/api/products/{id}` | 200 |
| 删除 | DELETE | `/api/products/{id}` | 200 |
| 子资源 | GET | `/api/products/{id}/history` | 200 |

**面试要点**：
- RESTful 原则（资源、HTTP 方法、无状态、统一接口）
- URL 设计规范（名词复数、层级关系）
- 使用正确的 HTTP 状态码
- 幂等性（PUT 是幂等的，POST 不是）

**高频问题**：
```
Q: 为什么用 PUT 而不是 PATCH？
A: PUT 完整替换资源（幂等）
   PATCH 部分更新资源（可能不幂等）

Q: 什么是幂等性？
A: 多次执行结果相同
   PUT /products/1 {"name": "Game"}
   无论执行几次，结果都是 name="Game"
```

### 2.3 FastAPI 核心概念

**你的项目中用到**：
```python
from fastapi import FastAPI, APIRouter, Depends, Query, status

app = FastAPI(title="Price Monitor")

# 依赖注入
async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session

# 路由
@router.get("/", response_model=List[ProductRead])
async def list_products(
    skip: int = Query(0, ge=0),  # 查询参数验证
    session: AsyncSession = Depends(get_session)  # 依赖注入
):
    pass
```

**面试要点**：
- **路由**（Router）：`@router.get`、`@router.post`
- **依赖注入**（Dependency Injection）：`Depends(get_session)`
- **请求验证**（Request Validation）：Pydantic 自动验证
- **响应模型**（Response Model）：`response_model=ProductRead`
- **查询参数**（Query Parameters）：`Query(0, ge=0)`
- **路径参数**（Path Parameters）：`{product_id}`

**高频问题**：
```python
# 问：Depends 是如何工作的？
async def get_db():
    return "database connection"

@router.get("/products")
async def get_products(db: str = Depends(get_db)):
    # FastAPI 自动调用 get_db()，将结果传给 db
    pass

# 答：FastAPI 在调用路由前，先执行依赖函数
# 将结果注入到函数参数中
```

### 2.4 中间件（Middleware）

**面试要点**：
- 中间件的作用（请求/响应拦截）
- 执行顺序（洋葱模型）
- CORS 中间件（跨域处理）
- 日志中间件
- 错误处理中间件

**示例**：
```python
from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"请求耗时: {process_time}")
    return response
```

---

## 三、数据库与 ORM

### 3.1 SQL 基础（必考）

**高频语句**：
```sql
-- 创建
INSERT INTO products (name, url, platform, target_price)
VALUES ('Game', '...', 'steam', 99.99);

-- 查询
SELECT * FROM products WHERE id = 1;
SELECT * FROM products ORDER BY price DESC LIMIT 10;

-- 更新
UPDATE products SET current_price = 89.99 WHERE id = 1;

-- 删除
DELETE FROM products WHERE id = 1;

-- 关联查询
SELECT p.*, ph.price, ph.check_time
FROM products p
LEFT JOIN price_history ph ON p.id = ph.product_id
WHERE p.id = 1;
```

**面试要点**：
- 基本 CRUD 操作
- JOIN 类型（INNER、LEFT、RIGHT、FULL）
- GROUP BY 和聚合函数（COUNT、SUM、AVG）
- 子查询
- 索引（PRIMARY KEY、INDEX、UNIQUE）
- 事务（BEGIN、COMMIT、ROLLBACK）

**高频问题**：
```
Q: INNER JOIN 和 LEFT JOIN 的区别？
A: INNER JOIN 只返回匹配的行
   LEFT JOIN 返回左表所有行，右表匹配不上则 NULL

Q: 什么是索引？
A: 加速查询的数据结构（类似书的目录）
   主键自动创建索引
   常用字段应该建索引
```

### 3.2 PostgreSQL 特性

**你的项目使用**：
```python
DATABASE_URL = "postgresql+asyncpg://..."
```

**面试要点**：
- PostgreSQL vs MySQL vs SQLite
- JSONB 类型（存储 JSON 数据）
- Array 类型（数组字段）
- 全文搜索
- 事务隔离级别

### 3.3 SQLModel/SQLAlchemy ORM

**你的项目中核心代码**：
```python
from sqlmodel import SQLModel, Field, Relationship, select

# 模型定义
class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    history: List["PriceHistory"] = Relationship(back_populates="product")

# 查询
stmt = select(Product).where(Product.id == 1)
result = await session.execute(stmt)
product = result.scalar_one_or_none()

# 创建
session.add(product)
await session.commit()
await session.refresh(product)

# 更新
product.name = "New Name"
await session.commit()

# 删除
session.delete(product)
await session.commit()
```

**面试要点**：
- **模型定义**（Model Definition）：`table=True`
- **字段配置**（Field）：`primary_key`、`default`、`index`
- **关系**（Relationship）：`back_populates`
- **查询**（Query）：`select()`、`where()`、`order_by()`
- **会话**（Session）：`add`、`commit`、`refresh`
- **异步操作**（Async）：`await session.execute()`

**高频问题**：
```python
# 问：relationship back_populates 是什么？
class Product(SQLModel, table=True):
    history: List["PriceHistory"] = Relationship(back_populates="product")

class PriceHistory(SQLModel, table=True):
    product: Optional[Product] = Relationship(back_populates="history")

# 答：定义双向关系
# product.history 可以获取所有历史
# history.product 可以获取所属商品
```

### 3.4 数据库迁移（Alembic）

**面试要点**：
- 为什么需要迁移？（版本控制数据库结构）
- 迁移命令（`alembic revision --autogenerate`）
- 回滚迁移（`alembic downgrade`）

---

## 四、异步编程

### 4.1 异步基础

**你的项目使用异步**：
```python
async def create_product(
    product: ProductCreate,
    session: AsyncSession = Depends(get_session)
):
    db_product = Product.from_orm(product)
    session.add(db_product)
    await session.commit()  # 异步提交
    await session.refresh(db_product)  # 异步刷新
```

**面试要点**：
- `async` 和 `await` 关键字
- 协程（Coroutine）vs 线程（Thread）
- 事件循环（Event Loop）
- 异步 I/O 的优势（非阻塞）

**高频问题**：
```
Q: 异步和同步的区别？
A: 同步：等待 I/O 时阻塞线程
   异步：等待 I/O 时切换任务，不阻塞

Q: 什么时候用异步？
A: I/O 密集型任务（网络请求、数据库查询）
   CPU 密集型任务用多进程更好
```

### 4.2 AsyncIO

**面试要点**：
- `asyncio.run()` 运行协程
- `asyncio.gather()` 并发执行
- `asyncio.sleep()` 异步延迟
- `async with` 异步上下文管理器

**示例**：
```python
import asyncio

async def fetch_data(url: str):
    # 异步请求
    await asyncio.sleep(1)
    return f"Data from {url}"

async def main():
    # 并发执行
    results = await asyncio.gather(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3")
    )
    print(results)

asyncio.run(main())
```

### 4.3 异步 HTTP 客户端

**你的项目中使用**：
```python
import httpx

async def _fetch_page(self, url: str) -> str:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        return response.text
```

**面试要点**：
- `httpx` vs `requests`（httpx 支持异步）
- `AsyncClient` 的使用
- 连接池
- 超时设置

---

## 五、RESTful API 设计

### 5.1 URL 设计规范

**你的项目遵循**：
```
GET    /api/products/           # 列表
GET    /api/products/{id}       # 详情
POST   /api/products/           # 创建
PUT    /api/products/{id}       # 更新
DELETE /api/products/{id}       # 删除
GET    /api/products/{id}/history # 子资源
```

**面试要点**：
- 使用名词复数（`/products` 不是 `/product`）
- 层级关系（`/products/{id}/history`）
- 查询参数（`?skip=0&limit=10`）
- 版本控制（`/api/v1/products`）

### 5.2 状态码选择

**你的项目使用**：
| 场景 | 状态码 |
|------|--------|
| 创建成功 | `201 Created` |
| 获取数据 | `200 OK` |
| 资源不存在 | `404 Not Found` |
| 验证失败 | `422 Unprocessable Entity` |
| 服务器错误 | `500 Internal Server Error` |

**面试要点**：
- `200` vs `201`（创建资源用 201）
- `400` vs `422`（请求格式错 vs 验证失败）
- `401` vs `403`（未认证 vs 无权限）
- `404`（资源不存在）
- `500`（服务器错误）

---

## 六、Docker 与部署

### 6.1 Docker 基础

**你的项目使用**：
```dockerfile
FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**面试要点**：
- 镜像（Image）vs 容器（Container）
- `Dockerfile` 指令（FROM、WORKDIR、COPY、RUN、CMD）
- 端口映射（`-p 8000:8000`）
- 数据卷（`-v`）

**高频问题**：
```
Q: COPY 和 ADD 的区别？
A: COPY 只复制文件
   ADD 可以复制 URL 并自动解压 tar

Q: CMD 和 ENTRYPOINT 的区别？
A: CMD 可以被 docker run 覆盖
   ENTRYPOINT 作为容器启动命令
```

### 6.2 Docker Compose

**你的项目使用**：
```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=mypassword
```

**面试要点**：
- 编排多个服务
- 服务依赖（`depends_on`）
- 环境变量（`environment`）
- 网络（自动创建）
- 数据卷（`volumes`）

---

## 七、Git 版本控制

### 7.1 常用命令

**面试必考**：
```bash
git clone         # 克隆仓库
git status       # 查看状态
git add .       # 添加文件
git commit -m "message"  # 提交
git push        # 推送到远程
git pull        # 拉取远程更新
git branch      # 查看分支
git checkout -b new-branch  # 创建并切换分支
git merge branch_name  # 合并分支
git log --oneline  # 查看提交历史
```

### 7.2 工作流程

**面试要点**：
- 分支策略（master/main、develop、feature）
- 合并请求（Pull Request）
- 冲突解决（Merge Conflict）

### 7.3 你的项目提交历史

```bash
# 你的项目最近提交
da47951 完成 P0 核心功能：Docker 支持、CRUD API 和 Steam 爬虫
```

**可以谈论**：
- 你如何组织提交（按功能提交）
- 提交信息规范（用中文描述清楚做了什么）
- 使用 Git 管理代码

---

## 八、爬虫与反爬

### 8.1 爬虫基础

**你的项目实现**：
```python
from bs4 import BeautifulSoup

def _parse_price(self, html: str) -> float:
    soup = BeautifulSoup(html, "lxml")
    price_element = soup.select_one(".discount_final_price")
    price_text = price_element.get_text(strip=True)
    return extract_price(price_text)
```

**面试要点**：
- HTTP 请求（GET、POST、Headers）
- HTML 解析（BeautifulSoup）
- 选择器（CSS Selector）
- 正则表达式（提取数据）

### 8.2 反爬策略

**你的项目已实现**：
```python
headers = {
    "User-Agent": "Mozilla/5.0 ..."
}
```

**面试要点**：
- User-Agent 伪装
- Cookie 处理
- IP 代理
- 请求频率控制
- 验证码识别（了解即可）

**高频问题**：
```
Q: 如何避免被反爬？
A: 设置合理的 User-Agent
   控制请求频率（添加延迟）
   使用代理 IP
   处理 Cookie
```

---

## 九、数据结构与算法

### 9.1 基础数据结构

**面试必考**：
- 列表（List）
- 字典（Dict/Hash Table）
- 集合（Set）
- 元组（Tuple）

**高频问题**：
```python
# 问：List 和 Dict 的区别？
# 答：List 有序、可重复、O(1) 索引访问、O(n) 查找
#     Dict 无序（Python 3.7+ 保持插入顺序）、唯一键、O(1) 查找
```

### 9.2 时间复杂度

**必掌握**：
- O(1) - 常数时间（字典查找）
- O(log n) - 对数时间（二分查找）
- O(n) - 线性时间（遍历列表）
- O(n log n) - 线性对数（快速排序）
- O(n²) - 平方时间（嵌套循环）

### 9.3 常见算法

**基础算法**：
- 排序（冒泡、快速、归并）
- 查找（线性、二分）
- 递归

---

## 十、系统设计基础

### 10.1 分层架构

**你的项目遵循**：
```
┌─────────────────────────────────┐
│      API 层（FastAPI）        │
├─────────────────────────────────┤
│      业务层（Service）         │  ← 你的项目可以添加
├─────────────────────────────────┤
│      数据层（SQLModel）        │
├─────────────────────────────────┤
│      数据库（PostgreSQL）      │
└─────────────────────────────────┘
```

**面试要点**：
- 为什么分层？（解耦、易维护）
- 每层的职责
- 依赖注入

### 10.2 缓存

**你的项目配置**：
```yaml
services:
  redis_cache:
    image: redis:alpine
```

**面试要点**：
- 为什么使用缓存？（减少数据库查询）
- Redis vs Memcached
- 缓存策略（LRU、TTL）
- 缓存穿透、雪崩、击穿

### 10.3 消息队列

**面试要点**：
- 为什么需要消息队列？（异步处理、解耦）
- RabbitMQ vs Redis vs Kafka
- 使用场景（价格变动通知）

---

## 十一、性能优化

### 11.1 数据库优化

**面试要点**：
- 索引（加速查询）
- 查询优化（避免 N+1 查询）
- 连接池
- 分页查询

**你的项目已实现**：
```python
# 分页避免一次性加载太多数据
stmt = select(Product).offset(skip).limit(limit)
```

### 11.2 API 优化

**面试要点**：
- 响应压缩（gzip）
- 异步处理
- 限流（Rate Limiting）
- CDN

---

## 十二、测试

### 12.1 测试类型

**面试要点**：
- 单元测试（测试函数/类）
- 集成测试（测试模块交互）
- 端到端测试（测试完整流程）

### 12.2 pytest

**常用操作**：
```python
import pytest

def test_create_product():
    product = ProductCreate(name="Game", price=99.99)
    assert product.name == "Game"
```

---

## 十三、常见面试问题

### 13.1 Python 相关

```
Q: GIL 是什么？有什么影响？
A: Global Interpreter Lock
   同一时间只有一个线程执行 Python 字节码
   多线程不适合 CPU 密集型任务
   但适合 I/O 密集型任务

Q: 深拷贝和浅拷贝的区别？
A: 浅拷贝：复制引用，共享对象
   深拷贝：完全复制，独立对象
   import copy; copy.copy() / copy.deepcopy()

Q: __str__ 和 __repr__ 的区别？
A: __str__: 面向用户的字符串
   __repr__: 面向开发者的字符串（可以 eval）
```

### 13.2 Web 相关

```
Q: Session 和 Cookie 的区别？
A: Session: 服务端存储，用 SessionID 标识
   Cookie: 客户端存储，每次请求携带

Q: 什么是 CORS？
A: 跨域资源共享
   允许不同域名访问资源
   浏览器安全策略

Q: JWT 是什么？
A: JSON Web Token
   无状态认证
   包含用户信息，用签名验证
```

### 13.3 数据库相关

```
Q: 事务是什么？
A: 一组操作，要么全部成功，要么全部失败
   ACID 特性
   BEGIN、COMMIT、ROLLBACK

Q: 索引的优缺点？
A: 优点：加速查询
   缺点：占用空间，降低插入/更新速度
```

### 13.4 项目相关

```
Q: 你的项目用了什么技术栈？
A: FastAPI + SQLModel + PostgreSQL + Redis + Docker
   异步编程 + 爬虫 + RESTful API

Q: 你遇到的最大挑战是什么？
A: 可以谈论：
   - 异步编程的学习曲线
   - Steam 网页结构变化导致解析失败
   - Docker 部署的配置问题
   - 数据库关系设计

Q: 如果要扩展开新平台，你会怎么做？
A: 1. 继承 BaseScraper
   2. 实现 scrape() 和 is_valid_url()
   3. 在 SCRAPER_MAP 中注册
   4. 测试价格抓取
```

---

## 十四、面试准备建议

### 14.1 技术准备

**按优先级**：
1. ✅ **Python 基础** - 类型提示、装饰器、异常、OOP
2. ✅ **HTTP 协议** - 方法、状态码、RESTful
3. ✅ **FastAPI** - 路由、依赖注入、验证
4. ✅ **数据库** - SQL 基础、ORM 操作
5. ✅ **异步编程** - async/await
6. ✅ **Docker** - 基本概念和使用
7. ✅ **Git** - 常用命令和工作流

### 14.2 项目准备

**准备讲述你的项目**：

```
1. 项目背景
   "我做了个价格监控系统，监控 Steam 游戏价格..."

2. 技术选型
   "为什么选 FastAPI？
    - 性能好（异步）
    - 自动文档
    - 类型提示
    为什么选 SQLModel？
    - 结合 Pydantic 和 SQLAlchemy
    - 简化开发"

3. 实现细节
   "实现了 CRUD API...
    实现了爬虫模块...
    使用了异步数据库操作..."

4. 遇到的挑战
   "Steam 页面结构变化导致解析失败
    我是如何解决的..."

5. 未来改进
   "添加更多平台支持
    实现定时任务
    集成 QQ 机器人..."
```

### 14.3 算法准备

**基础算法题**（LeetCode 简单）：
- 两数之和
- 反转链表
- 两数相加
- 有效的括号
- 合并两个有序链表

### 14.4 模拟面试

**自我提问**：
1. 能完整描述你的项目吗？
2. 能解释每个文件的作用吗？
3. 知道每个技术的优缺点吗？
4. 遇到问题如何调试？
5. 如何改进你的项目？

---

## 十五、推荐学习资源

### 在线资源
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [SQLModel 官方文档](https://sqlmodel.tiangolo.com/)
- [Pydantic 官方文档](https://docs.pydantic.dev/)
- [Python 官方文档](https://docs.python.org/zh-cn/3/)

### 书籍
- 《流畅的 Python》
- 《Python 编程：从入门到实践》
- 《高性能 MySQL》

### 练习平台
- LeetCode（算法）
- Codeforces（算法）
- HackerRank（综合）

---

## 总结

| 分类 | 重要程度 | 你的项目覆盖 |
|------|---------|-------------|
| Python 基础 | ⭐⭐⭐⭐⭐ | ✅ |
| HTTP/Web | ⭐⭐⭐⭐⭐ | ✅ |
| FastAPI | ⭐⭐⭐⭐⭐ | ✅ |
| 数据库/ORM | ⭐⭐⭐⭐⭐ | ✅ |
| 异步编程 | ⭐⭐⭐⭐ | ✅ |
| RESTful | ⭐⭐⭐⭐ | ✅ |
| Docker | ⭐⭐⭐ | ✅ |
| Git | ⭐⭐⭐ | ✅ |
| 爬虫 | ⭐⭐⭐ | ✅ |
| 算法 | ⭐⭐⭐⭐ | ⚠️ 需额外练习 |
| 系统设计 | ⭐⭐⭐ | ⚠️ 需进一步学习 |
| 性能优化 | ⭐⭐⭐ | ⚠️ 需进一步学习 |

**你的项目已经覆盖了大部分核心知识点，非常扎实！**

重点复习：
1. HTTP 协议和 RESTful 设计
2. FastAPI 的核心概念
3. SQLModel/SQLAlchemy 的使用
4. 异步编程原理
5. 能够流畅地讲解你的项目

祝你面试顺利！🎉