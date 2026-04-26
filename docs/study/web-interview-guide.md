# Web 后端面试核心知识点详解

> 基于 Price Monitor 项目实战，深度讲解 Web 开发核心概念

---

## 目录

- [一、HTTP 协议（面试必考）](#一http-协议面试必考)
- [二、RESTful API 设计](#二restful-api-设计)
- [三、FastAPI 框架核心](#三fastapi-框架核心)
- [四、请求生命周期](#四请求生命周期)
- [五、常见面试问题汇总](#五常见面试问题汇总)

---

## 一、HTTP 协议（面试必考）

### 1.1 HTTP 是什么？

HTTP（HyperText Transfer Protocol）是客户端和服务器之间通信的协议。

```
客户端（浏览器）  ----请求---->  服务器
                 <----响应----
```

### 1.2 HTTP 方法

| 方法 | 用途 | 是否幂等 | 项目示例 |
|------|------|---------|---------|
| GET | 获取资源 | ✅ 是 | `list_products()` 获取商品列表 |
| POST | 创建资源 | ❌ 否 | `create_product()` 创建商品 |
| PUT | 完整更新资源 | ✅ 是 | `update_product()` 更新商品 |
| DELETE | 删除资源 | ✅ 是 | `delete_product()` 删除商品 |
| PATCH | 部分更新 | ❌ 可能不幂等 | 未使用 |

**什么是幂等性？**
> 多次执行相同请求，结果相同。

```python
# 幂等示例：PUT
PUT /products/1 {"name": "Game", "price": 99}
# 无论执行多少次，结果都是 name="Game", price=99

# 非幂等示例：POST
POST /products {"name": "Game"}
# 每次执行都会创建一个新商品
```

### 1.3 HTTP 状态码

**你的项目中的实际使用：**

```python
# app/routers/products.py

@router.post("/", status_code=status.HTTP_201_CREATED)  # 创建成功返回 201
async def create_product(...):
    pass

@router.get("/")  # 默认返回 200
async def list_products(...):
    pass

# 资源不存在返回 404
if not product:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Product with id {product_id} not found"
    )
```

**状态码分类（必背）：**

| 范围 | 含义 | 常见状态码 |
|------|------|-----------|
| 1xx | 信息性 | 100 Continue |
| 2xx | 成功 | **200 OK**, **201 Created**, 204 No Content |
| 3xx | 重定向 | 301 永久重定向, 302 临时重定向 |
| 4xx | 客户端错误 | **400 Bad Request**, **401 Unauthorized**, **403 Forbidden**, **404 Not Found**, **422 Validation Error** |
| 5xx | 服务器错误 | **500 Internal Server Error**, 502 Bad Gateway, 503 Service Unavailable |

**高频面试题：401 vs 403**

```
Q: 401 和 403 有什么区别？

A: 401 Unauthorized - 未认证（没登录，或 token 无效）
   403 Forbidden - 已认证但无权限（登录了，但没有访问该资源的权限）

   举例：
   - 访问 /admin 但没登录 → 401
   - 普通用户访问 /admin → 403（你是用户，不是管理员）
```

### 1.4 请求头和响应头

**常见请求头：**

```
Content-Type: application/json     # 请求体格式
Authorization: Bearer <token>      # 认证信息
User-Agent: Mozilla/5.0...         # 客户端标识
Accept: application/json           # 期望的响应格式
```

**你的爬虫中使用 User-Agent：**

```python
# app/scrapers/steam.py

async def _fetch_page(self, url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    # 伪装成浏览器，避免被反爬
```

**常见响应头：**

```
Content-Type: application/json     # 响应体格式
Cache-Control: max-age=3600        # 缓存策略
Set-Cookie: session=abc123         # 设置 Cookie
```

### 1.5 HTTPS vs HTTP

```
Q: HTTPS 和 HTTP 的区别？

A: 1. HTTPS = HTTP + SSL/TLS 加密
   2. HTTPS 数据传输是加密的，HTTP 是明文的
   3. HTTPS 需要 CA 证书
   4. HTTPS 默认端口 443，HTTP 默认端口 80
   5. HTTPS 更安全，防止中间人攻击
```

---

## 二、RESTful API 设计

### 2.1 REST 是什么？

REST（Representational State Transfer）是一种 API 设计风格，核心原则：

1. **资源（Resource）** - 一切皆资源，用 URL 标识
2. **HTTP 方法** - 用方法表达操作
3. **无状态（Stateless）** - 每个请求包含所有信息
4. **统一接口** - 遵循一致的规范

### 2.2 URL 设计规范

**你的项目遵循的规范：**

```
# app/routers/products.py

router = APIRouter(prefix="/products", tags=["products"])

# 最终 URL 路径：
GET    /api/products/              # 商品列表（复数名词）
GET    /api/products/{id}          # 单个商品
POST   /api/products/              # 创建商品
PUT    /api/products/{id}          # 更新商品
DELETE /api/products/{id}          # 删除商品
GET    /api/products/{id}/history  # 子资源（价格历史）
```

**设计原则：**

| 原则 | 正确示例 | 错误示例 |
|------|---------|---------|
| 用名词不用动词 | `/products` | `/getProducts` |
| 用复数 | `/products` | `/product` |
| 层级关系 | `/products/{id}/history` | `/history?product_id={id}` |
| 用 HTTP 方法表达操作 | `DELETE /products/1` | `/products/1/delete` |

### 2.3 你的项目完整 RESTful 实现

```python
# app/routers/products.py

# 1. 创建资源 - POST
@router.post("/", response_model=schemas.ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: schemas.ProductCreate,
    session: AsyncSession = Depends(get_session)
):
    """创建商品"""
    db_product = models.Product.from_orm(product)
    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product


# 2. 获取列表 - GET
@router.get("/", response_model=List[schemas.ProductRead])
async def list_products(
    skip: int = Query(0, ge=0),      # 分页参数
    limit: int = Query(100, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """获取商品列表"""
    result = await session.execute(
        select(models.Product).offset(skip).limit(limit)
    )
    products = result.scalars().all()
    return products


# 3. 获取单个资源 - GET
@router.get("/{product_id}", response_model=schemas.ProductRead)
async def get_product(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """获取单个商品"""
    result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return product


# 4. 更新资源 - PUT
@router.put("/{product_id}", response_model=schemas.ProductRead)
async def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    session: AsyncSession = Depends(get_session)
):
    """更新商品"""
    # 先查询
    result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    db_product = result.scalar_one_or_none()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, ...)

    # 部分更新（只更新提供的字段）
    product_data = product_update.dict(exclude_unset=True)
    for field, value in product_data.items():
        setattr(db_product, field, value)

    await session.commit()
    await session.refresh(db_product)
    return db_product


# 5. 删除资源 - DELETE
@router.delete("/{product_id}", response_model=schemas.ProductRead)
async def delete_product(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """删除商品"""
    result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    db_product = result.scalar_one_or_none()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, ...)

    await session.delete(db_product)
    await session.commit()
    return db_product  # 返回被删除的对象


# 6. 子资源 - GET
@router.get("/{product_id}/history", response_model=List[schemas.PriceHistoryRead])
async def get_price_history(product_id: int, ...):
    """获取价格历史（子资源）"""
    ...
```

### 2.4 面试高频问题

```
Q: PUT 和 PATCH 的区别？

A: PUT - 完整替换资源（幂等）
   PATCH - 部分更新资源（可能不幂等）

   示例：
   资源: {"name": "Game", "price": 100}

   PUT /products/1 {"name": "New Game"}
   结果: {"name": "New Game"}  # price 被删除了！

   PATCH /products/1 {"name": "New Game"}
   结果: {"name": "New Game", "price": 100}  # price 保留
```

```
Q: 什么是无状态（Stateless）？

A: 服务器不保存客户端状态，每个请求必须包含所有信息。
   好处：易于扩展，可以负载均衡
   缺点：每次请求都要传认证信息

   反例（有状态）：Session 存在服务器内存中
   正例（无状态）：JWT Token 每次请求都携带
```

---

## 三、FastAPI 框架核心

### 3.1 项目结构

```
app/
├── main.py           # 应用入口
├── database.py       # 数据库配置
├── models.py         # 数据库模型（ORM）
├── schemas.py        # API 数据模式（Pydantic）
├── routers/
│   └── products.py   # 商品路由
└── scrapers/
    ├── base.py       # 爬虫基类
    ├── steam.py      # Steam 爬虫
    └── exceptions.py # 自定义异常
```

**分层架构：**

```
┌─────────────────────────────────────┐
│         API 层（routers/）          │  ← 处理 HTTP 请求/响应
├─────────────────────────────────────┤
│         模式层（schemas.py）        │  ← 数据验证/序列化
├─────────────────────────────────────┤
│         模型层（models.py）         │  ← 数据库 ORM 映射
├─────────────────────────────────────┤
│         数据库（PostgreSQL）        │  ← 持久化存储
└─────────────────────────────────────┘
```

### 3.2 应用入口

```python
# app/main.py

from fastapi import FastAPI
from app.database import init_db
from app.routers import products

# 创建 FastAPI 应用实例
app = FastAPI(title="Price Monitor")

# 注册路由（prefix 添加统一前缀）
app.include_router(products.router, prefix="/api")

# 启动事件：应用启动时执行
@app.on_event("startup")
async def on_startup():
    await init_db()  # 初始化数据库，创建表

# 根路由
@app.get("/")
def read_root():
    return {"Hello": "Price Monitor is Running"}
```

**面试要点：**

- `FastAPI()` 创建应用实例
- `include_router()` 注册路由模块
- `@app.on_event("startup")` 启动时执行的钩子
- `@app.get()` 定义路由

### 3.3 路由（Router）

```python
# app/routers/products.py

from fastapi import APIRouter

# 创建路由器
router = APIRouter(prefix="/products", tags=["products"])

# 定义路由
@router.post("/")
@router.get("/")
@router.get("/{product_id}")
@router.put("/{product_id}")
@router.delete("/{product_id}")
```

**APIRouter vs app：**

| 方式 | 使用场景 |
|------|---------|
| `@app.get()` | 小项目，所有路由在一个文件 |
| `@router.get()` | 大项目，按模块拆分路由 |

### 3.4 依赖注入（Dependency Injection）

**这是 FastAPI 最核心的特性之一！**

```python
# app/database.py

async def get_session() -> AsyncSession:
    """依赖函数：提供数据库会话"""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session  # yield 使得请求结束后自动关闭连接
```

```python
# app/routers/products.py

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

@router.post("/")
async def create_product(
    product: schemas.ProductCreate,
    session: AsyncSession = Depends(get_session)  # 依赖注入！
):
    # FastAPI 自动调用 get_session()，把结果赋给 session
    # 请求结束后自动清理资源
    ...
```

**依赖注入的工作流程：**

```
1. 请求到达 create_product
2. FastAPI 发现 Depends(get_session)
3. 调用 get_session() 生成器
4. yield 返回 session 对象
5. 执行 create_product 函数体
6. 函数返回后，继续执行 get_session 的剩余代码（清理资源）
7. async with 结束，关闭数据库连接
```

**为什么使用依赖注入？**

```
Q: 为什么不直接在路由里创建 session？

A: 1. 解耦 - 路由不关心 session 如何创建
   2. 复用 - 多个路由共用同一个依赖
   3. 测试 - 可以轻松替换为 Mock 依赖
   4. 资源管理 - 自动清理资源（yield 模式）
```

### 3.5 请求验证（Pydantic）

**你的项目中的 Schema 设计：**

```python
# app/schemas.py

from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime

# 1. 基础 Schema（公共字段）
class ProductBaseSchema(SQLModel):
    name: str
    url: str
    platform: str = "steam"      # 默认值
    target_price: float          # 自动验证类型

# 2. 创建请求 Schema（继承基础字段）
class ProductCreate(ProductBaseSchema):
    pass  # 创建时需要所有基础字段

# 3. 响应 Schema（包含 id 等服务端生成的字段）
class ProductRead(ProductBaseSchema):
    id: int                       # 必须返回
    current_price: Optional[float] = None   # 可选
    last_checked_time: Optional[datetime] = None

# 4. 更新请求 Schema（所有字段可选）
class ProductUpdate(SQLModel):
    name: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None
    target_price: Optional[float] = None
    # ...
```

**为什么要分离 Schema？**

```
Q: 为什么不直接用 Model？

A: 1. 安全性 - 创建时不应该传 id
   2. 灵活性 - 响应可以包含额外字段（如计算字段）
   3. 验证 - 不同操作有不同的验证规则
   4. 解耦 - API 格式和数据库格式可以不同
```

**自动验证示例：**

```python
@router.post("/")
async def create_product(product: schemas.ProductCreate):
    # FastAPI 自动验证：
    # - name 必须是 str
    # - url 必须是 str
    # - target_price 必须是 float
    # 如果验证失败，自动返回 422 错误
    ...
```

**验证失败的响应：**

```json
{
  "detail": [
    {
      "loc": ["body", "target_price"],
      "msg": "value is not a valid float",
      "type": "type_error.float"
    }
  ]
}
```

### 3.6 查询参数和路径参数

```python
# 路径参数（URL 的一部分）
@router.get("/{product_id}")
async def get_product(product_id: int):  # 自动从 URL 提取
    # /products/123  →  product_id = 123
    ...

# 查询参数（URL 中 ? 后面的部分）
@router.get("/")
async def list_products(
    skip: int = Query(0, ge=0),        # ge=0 表示 >= 0
    limit: int = Query(100, ge=1, le=100)  # ge=1, le=100 表示 1-100
):
    # /products?skip=0&limit=10
    ...

# Query 参数详解
skip: int = Query(
    default=0,      # 默认值
    ge=0,           # 最小值（greater or equal）
    le=100,         # 最大值（less or equal）
    description="跳过的记录数"  # API 文档描述
)
```

**Query vs Path：**

```python
from fastapi import Query, Path

# 路径参数（必填）
@router.get("/{product_id}")
async def get_product(
    product_id: int = Path(..., ge=1, description="商品 ID")
):
    ...

# 查询参数（可选）
@router.get("/")
async def list_products(
    name: str = Query(None, max_length=50)  # 可选，最大长度 50
):
    ...
```

### 3.7 响应模型

```python
@router.post("/", response_model=schemas.ProductRead)
#                          ↑ 自动转换为 ProductRead 格式
async def create_product(...):
    return db_product  # 返回 Product 模型，自动转换为 ProductRead
```

**response_model 的作用：**

1. **自动过滤字段** - 只返回 response_model 中定义的字段
2. **自动转换类型** - 确保响应格式正确
3. **生成 API 文档** - OpenAPI/Swagger 自动显示响应格式

---

## 四、请求生命周期

### 4.1 完整的请求流程

```
客户端                        FastAPI                     数据库
  │                            │                           │
  │── POST /api/products ─────>│                           │
  │   {"name": "Game"}         │                           │
  │                            │                           │
  │                    1. 解析请求                           │
  │                            │                           │
  │                    2. 验证数据（Pydantic）               │
  │                            │                           │
  │                    3. 执行依赖注入                       │
  │                            │─── get_session() ────────>│
  │                            │<── session ───────────────│
  │                            │                           │
  │                    4. 执行路由函数                       │
  │                            │─── INSERT INTO ──────────>│
  │                            │<── 返回数据 ───────────────│
  │                            │                           │
  │                    5. 转换响应（response_model）         │
  │                            │                           │
  │                    6. 清理依赖资源                       │
  │                            │─── 关闭 session ─────────>│
  │                            │                           │
  │<── 201 Created ────────────│                           │
  │    {"id": 1, "name": ...}  │                           │
```

### 4.2 中间件（Middleware）

```python
# 中间件示例（虽然你的项目没用到，但面试常考）

from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    # 请求前
    start_time = time.time()
    print(f"请求开始: {request.method} {request.url}")

    # 执行下一个处理者
    response = await call_next(request)

    # 响应后
    process_time = time.time() - start_time
    print(f"请求耗时: {process_time:.2f}s")

    return response
```

**中间件执行顺序（洋葱模型）：**

```
请求 → 中间件1 → 中间件2 → 路由 → 中间件2 → 中间件1 → 响应
         ↓          ↓        ↑          ↑          ↑
       前置处理   前置处理   业务逻辑   后置处理   后置处理
```

---

## 五、常见面试问题汇总

### 5.1 HTTP 相关

```
Q: GET 和 POST 的区别？

A: 1. 用途：GET 获取资源，POST 创建资源
   2. 参数位置：GET 在 URL 中，POST 在 Body 中
   3. 长度限制：GET 有 URL 长度限制，POST 无限制
   4. 缓存：GET 可被缓存，POST 不能
   5. 安全性：都不安全，POST 只是稍好（参数不在 URL 中）
   6. 幂等性：GET 幂等，POST 不幂等
```

```
Q: 什么是 CORS？

A: Cross-Origin Resource Sharing（跨域资源共享）
   浏览器的安全策略，阻止网页从不同域名请求资源

   解决方案：
   1. 后端设置 Access-Control-Allow-Origin 响应头
   2. FastAPI 中使用 CORSMiddleware

   from fastapi.middleware.cors import CORSMiddleware
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],
       allow_methods=["*"],
       allow_headers=["*"],
   )
```

### 5.2 FastAPI 相关

```
Q: 为什么选择 FastAPI 而不是 Django/Flask？

A: 1. 性能 - 异步支持，性能接近 Node.js 和 Go
   2. 开发效率 - 自动生成 API 文档（Swagger）
   3. 类型提示 - Pydantic 自动验证，IDE 支持好
   4. 现代 - 基于 Python 3.6+ 的类型注解
   5. 简单 - 学习曲线平缓

   Django：全功能框架，适合大型项目
   Flask：轻量级，但需要自己组装很多组件
   FastAPI：现代化，异步支持好，自动文档
```

```
Q: 解释 FastAPI 的依赖注入？

A: 依赖注入是一种设计模式：
   - 把依赖的创建和管理交给框架
   - 路由函数通过 Depends() 声明依赖
   - FastAPI 自动调用依赖函数并注入结果

   好处：
   1. 解耦 - 路由不关心依赖如何创建
   2. 复用 - 多个路由共用同一依赖
   3. 测试 - 容易 Mock 依赖进行测试
   4. 资源管理 - yield 模式自动清理资源
```

### 5.3 RESTful 相关

```
Q: RESTful API 的设计原则？

A: 1. 资源为中心 - URL 表示资源，用名词不用动词
   2. HTTP 方法表达操作 - GET 读取，POST 创建，PUT 更新，DELETE 删除
   3. 无状态 - 每个请求包含所有必要信息
   4. 统一接口 - 一致的设计风格
   5. 层次化 - 清晰的分层架构
```

```
Q: 如何设计一个好的 API？

A: 1. 使用正确的 HTTP 方法和状态码
   2. URL 用名词复数，层级清晰
   3. 支持过滤、排序、分页
   4. 返回有意义的错误信息
   5. 版本控制（/api/v1/）
   6. 提供良好的文档
```

### 5.4 项目实战问题

```
Q: 你的项目是怎么分层的？

A: 1. API 层（routers/） - 处理 HTTP 请求/响应，参数验证
   2. Schema 层（schemas.py） - 定义请求/响应格式
   3. Model 层（models.py） - 数据库 ORM 映射
   4. 数据库层 - PostgreSQL 存储

   这样分层的优点：
   - 职责分离，代码清晰
   - 易于测试和维护
   - API 格式和数据库格式解耦
```

```
Q: 你的项目如何处理错误？

A: 1. 自定义异常类（scrapers/exceptions.py）
   2. HTTPException 返回正确的状态码
   3. try-except 捕获异常并转换

   示例：
   if not product:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail=f"Product with id {product_id} not found"
       )
```

```
Q: 如果要给你的项目添加用户认证，你会怎么做？

A: 1. 使用 JWT（JSON Web Token）
   2. 添加 /auth/login 和 /auth/register 接口
   3. 创建认证依赖函数
   4. 在需要认证的路由上使用依赖

   # 认证依赖
   async def get_current_user(token: str = Depends(oauth2_scheme)):
       # 验证 token，返回用户
       ...

   # 使用认证
   @router.post("/")
   async def create_product(
       ...,
       user: User = Depends(get_current_user)  # 需要登录
   ):
       ...
```

---

## 六、面试时如何介绍你的项目

### 6.1 项目介绍模板

```
"我开发了一个价格监控系统，用于监控 Steam 游戏的价格变动。

技术栈：
- FastAPI 作为后端框架，利用其异步特性和自动文档
- SQLModel 做 ORM，结合了 Pydantic 和 SQLAlchemy 的优点
- PostgreSQL 作为数据库
- Docker 做容器化部署

核心功能：
1. 商品的 CRUD 操作（RESTful API）
2. Steam 平台价格爬虫（异步 HTTP + BeautifulSoup）
3. 价格历史记录查询

项目亮点：
1. 完全异步的架构，适合 I/O 密集型场景
2. 清晰的分层设计，易于维护和扩展
3. 爬虫模块采用抽象基类设计，易于扩展新平台"
```

### 6.2 可能被问到的问题

准备这些问题的答案：

1. **为什么选择 FastAPI？** - 异步、自动文档、类型验证
2. **为什么用 SQLModel 而不是 SQLAlchemy？** - 更简洁，结合 Pydantic
3. **项目中最难的部分是什么？** - 可以说爬虫解析、异步编程
4. **如果要扩展到其他平台怎么做？** - 继承 BaseScraper，实现接口
5. **如何处理并发请求？** - 异步 + 数据库连接池

---

## 总结

| 知识点 | 重要程度 | 掌握要求 |
|--------|---------|---------|
| HTTP 方法 | ⭐⭐⭐⭐⭐ | 背诵，能说出区别 |
| HTTP 状态码 | ⭐⭐⭐⭐⭐ | 背诵常用状态码 |
| RESTful 设计 | ⭐⭐⭐⭐⭐ | 能设计规范 API |
| FastAPI 路由 | ⭐⭐⭐⭐⭐ | 熟练使用 |
| 依赖注入 | ⭐⭐⭐⭐⭐ | 理解原理，能解释 |
| Pydantic 验证 | ⭐⭐⭐⭐ | 熟练使用 |
| 中间件 | ⭐⭐⭐ | 理解概念 |
| 项目介绍 | ⭐⭐⭐⭐⭐ | 能流畅讲述 |

**面试前复习清单：**

- [ ] 背诵 HTTP 方法和状态码
- [ ] 理解幂等性
- [ ] 能解释 RESTful 设计原则
- [ ] 能解释 FastAPI 依赖注入
- [ ] 熟悉自己的项目代码
- [ ] 准备项目介绍（2-3 分钟）
- [ ] 准备遇到的挑战和解决方案

祝你面试顺利！
