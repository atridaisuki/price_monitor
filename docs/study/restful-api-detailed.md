# RESTful API 设计详解（面试版）

> 基于 price_monitor 项目的 RESTful API 实践，深入讲解面试必考知识点

---

## 目录

1. [RESTful 核心概念](#1-restful-核心概念)
2. [URL 设计规范](#2-url-设计规范)
3. [HTTP 方法详解](#3-http-方法详解)
4. [状态码选择与使用](#4-状态码选择与使用)
5. [请求与响应设计](#5-请求与响应设计)
6. [幂等性与安全性](#6-幂等性与安全性)
7. [版本控制](#7-版本控制)
8. [常见面试问题](#8-常见面试问题)

---

## 1. RESTful 核心概念

### 1.1 什么是 REST？

**REST**（Representational State Transfer，表述性状态转移）是一种软件架构风格，由 Roy Fielding 在 2000 年提出。

**核心思想**：
- 将服务器端的数据抽象为"资源"（Resource）
- 客户端通过 HTTP 方法操作资源
- 资源通过 URL 唯一标识
- 服务器返回资源的表述（JSON、XML 等）

### 1.2 REST 六大约束

面试中可能会问到 REST 的设计原则：

1. **客户端-服务器分离**（Client-Server）
   - 前后端分离，各自独立演化

2. **无状态**（Stateless）
   - 每个请求包含所有必要信息
   - 服务器不保存客户端状态

3. **可缓存**（Cacheable）
   - 响应可以被缓存以提高性能

4. **统一接口**（Uniform Interface）
   - 使用标准 HTTP 方法
   - 资源通过 URL 标识

5. **分层系统**（Layered System）
   - 客户端不知道是否直接连接到服务器

6. **按需代码**（Code on Demand，可选）
   - 服务器可以返回可执行代码

### 1.3 你的项目中的 REST 实践

```python
# app/routers/products.py

# ✅ 资源导向：以 products 为资源
router = APIRouter(prefix="/products", tags=["products"])

# ✅ 使用标准 HTTP 方法
@router.post("/")          # 创建
@router.get("/")           # 列表
@router.get("/{id}")       # 详情
@router.put("/{id}")       # 更新
@router.delete("/{id}")    # 删除

# ✅ 无状态：每个请求通过 session 参数获取数据库连接
async def create_product(
    product: schemas.ProductCreate,
    session: AsyncSession = Depends(get_session)  # 依赖注入，不保存状态
):
    pass
```

---

## 2. URL 设计规范

### 2.1 基本原则

#### 原则 1：使用名词，不使用动词

❌ **错误示例**：
```
POST /createProduct
GET /getProducts
DELETE /deleteProduct/1
```

✅ **正确示例**（你的项目）：
```
POST   /products          # 创建商品
GET    /products          # 获取商品列表
DELETE /products/1        # 删除商品
```

**面试要点**：
- URL 表示资源，资源是名词
- 动作由 HTTP 方法表示（POST、GET、DELETE）

#### 原则 2：使用复数形式

❌ **错误示例**：
```
GET /product/1
GET /product
```

✅ **正确示例**（你的项目）：
```
GET /products/1           # 获取单个商品
GET /products             # 获取商品列表
```

**面试要点**：
- 统一使用复数形式（`/products`）
- 即使获取单个资源也用复数（`/products/1`）
- 保持 API 一致性

#### 原则 3：层级关系表示资源关联

✅ **你的项目实现**：
```python
# app/routers/products.py:109

@router.get("/{product_id}/history")
async def get_price_history(product_id: int):
    """获取商品的价格历史"""
    pass
```

**URL 结构**：
```
GET /products/1/history   # 获取商品 1 的价格历史
```

**面试要点**：
- 子资源通过层级关系表示
- `/products/{id}/history` 表示"商品的历史记录"
- 最多 2-3 层，避免过深嵌套

### 2.2 你的项目完整 API 设计

| 操作 | HTTP 方法 | URL | 说明 |
|------|-----------|-----|------|
| 创建商品 | `POST` | `/products/` | 创建新商品 |
| 商品列表 | `GET` | `/products/` | 获取所有商品 |
| 商品详情 | `GET` | `/products/{id}` | 获取单个商品 |
| 更新商品 | `PUT` | `/products/{id}` | 更新商品信息 |
| 删除商品 | `DELETE` | `/products/{id}` | 删除商品 |
| 价格历史 | `GET` | `/products/{id}/history` | 获取价格历史 |

### 2.3 查询参数（Query Parameters）

✅ **你的项目实现**：
```python
# app/routers/products.py:28-33

@router.get("/", response_model=List[schemas.ProductRead])
async def list_products(
    skip: int = Query(0, ge=0),           # 偏移量，最小为 0
    limit: int = Query(100, ge=1, le=100), # 限制数量，1-100
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(models.Product).offset(skip).limit(limit)
    )
    return result.scalars().all()
```

**URL 示例**：
```
GET /products?skip=0&limit=10    # 获取前 10 个商品
GET /products?skip=10&limit=10   # 获取第 11-20 个商品
```

**面试要点**：
- 查询参数用于过滤、排序、分页
- 使用 `Query()` 进行参数验证
- `ge=0` 表示 greater than or equal（大于等于 0）
- `le=100` 表示 less than or equal（小于等于 100）

### 2.4 路径参数（Path Parameters）

✅ **你的项目实现**：
```python
# app/routers/products.py:43-58

@router.get("/{product_id}", response_model=schemas.ProductRead)
async def get_product(
    product_id: int,  # 路径参数
    session: AsyncSession = Depends(get_session)
):
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
```

**URL 示例**：
```
GET /products/1      # product_id = 1
GET /products/42     # product_id = 42
```

**面试要点**：
- 路径参数用于标识特定资源
- FastAPI 自动解析并验证类型
- 如果资源不存在，返回 404

### 2.5 URL 设计最佳实践

#### ✅ 推荐做法

```
# 1. 使用小写字母
GET /products          ✅
GET /Products          ❌

# 2. 使用连字符分隔单词
GET /price-history     ✅
GET /price_history     ❌（下划线不推荐）
GET /priceHistory      ❌（驼峰命名不推荐）

# 3. 不要在 URL 末尾加斜杠
GET /products          ✅
GET /products/         ❌

# 4. 使用查询参数进行过滤
GET /products?platform=steam&price_lt=100  ✅
GET /products/steam/under-100              ❌
```

---

## 3. HTTP 方法详解

### 3.1 五大核心方法

| 方法 | 作用 | 幂等性 | 安全性 | 你的项目使用 |
|------|------|--------|--------|-------------|
| `GET` | 获取资源 | ✅ | ✅ | ✅ |
| `POST` | 创建资源 | ❌ | ❌ | ✅ |
| `PUT` | 完整更新 | ✅ | ❌ | ✅ |
| `PATCH` | 部分更新 | ❌ | ❌ | ❌ |
| `DELETE` | 删除资源 | ✅ | ❌ | ✅ |

### 3.2 GET - 获取资源

**特点**：
- 只读操作，不修改服务器状态
- 幂等且安全
- 可以被缓存
- 参数在 URL 中

✅ **你的项目实现**：
```python
# 1. 获取列表
@router.get("/")
async def list_products(skip: int = 0, limit: int = 100):
    pass

# 2. 获取单个资源
@router.get("/{product_id}")
async def get_product(product_id: int):
    pass

# 3. 获取子资源
@router.get("/{product_id}/history")
async def get_price_history(product_id: int):
    pass
```

**面试高频问题**：
```
Q: GET 请求可以有 Body 吗？
A: 技术上可以，但不推荐
   - HTTP 规范没有禁止
   - 但很多工具和框架不支持
   - 参数应该放在 URL 查询参数中

Q: GET 和 POST 的区别？
A: 1. GET 用于获取，POST 用于创建
   2. GET 参数在 URL，POST 参数在 Body
   3. GET 有长度限制（浏览器限制），POST 无限制
   4. GET 可缓存，POST 不可缓存
   5. GET 幂等，POST 不幂等
```

### 3.3 POST - 创建资源

**特点**：
- 创建新资源
- 非幂等（多次调用创建多个资源）
- 参数在 Body 中
- 成功返回 `201 Created`

✅ **你的项目实现**：
```python
# app/routers/products.py:12-25

@router.post("/", response_model=schemas.ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: schemas.ProductCreate,  # 请求体
    session: AsyncSession = Depends(get_session)
):
    """创建商品"""
    db_product = models.Product.from_orm(product)
    session.add(db_product)
    await session.commit()
    await session.refresh(db_product)
    return db_product  # 返回创建的资源
```

**请求示例**：
```http
POST /products/
Content-Type: application/json

{
  "name": "Elden Ring",
  "url": "https://store.steampowered.com/app/1245620/",
  "platform": "steam",
  "target_price": 199.00
}
```

**响应示例**：
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": 1,
  "name": "Elden Ring",
  "url": "https://store.steampowered.com/app/1245620/",
  "platform": "steam",
  "target_price": 199.00,
  "current_price": null,
  "created_at": "2024-03-09T10:00:00"
}
```

**面试要点**：
- 返回 `201 Created` 状态码
- 返回创建的资源（包含 ID）
- 可以在响应头中添加 `Location: /products/1`

### 3.4 PUT - 完整更新资源

**特点**：
- 完整替换资源
- 幂等（多次调用结果相同）
- 必须提供所有字段

✅ **你的项目实现**：
```python
# app/routers/products.py:61-85

@router.put("/{product_id}", response_model=schemas.ProductRead)
async def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,
    session: AsyncSession = Depends(get_session)
):
    """更新商品"""
    # 1. 查找资源
    result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    db_product = result.scalar_one_or_none()

    # 2. 资源不存在返回 404
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )

    # 3. 更新字段（只更新提供的字段）
    product_data = product_update.dict(exclude_unset=True)
    for field, value in product_data.items():
        setattr(db_product, field, value)

    # 4. 提交并返回
    await session.commit()
    await session.refresh(db_product)
    return db_product
```

**请求示例**：
```http
PUT /products/1
Content-Type: application/json

{
  "name": "Elden Ring - Updated",
  "target_price": 149.00
}
```

**面试高频问题**：
```
Q: PUT 和 PATCH 的区别？
A: PUT：完整替换资源（幂等）
   - PUT /products/1 {"name": "Game"}
   - 会替换整个资源，未提供的字段可能被清空

   PATCH：部分更新资源（可能不幂等）
   - PATCH /products/1 {"name": "Game"}
   - 只更新提供的字段

Q: 为什么 PUT 是幂等的？
A: 多次执行相同的 PUT 请求，结果相同
   PUT /products/1 {"name": "Game", "price": 100}
   无论执行 1 次还是 10 次，资源状态都是 name="Game", price=100
```

### 3.5 DELETE - 删除资源

**特点**：
- 删除资源
- 幂等（删除已删除的资源返回 404）
- 可以返回被删除的资源或 204 No Content

✅ **你的项目实现**：
```python
# app/routers/products.py:88-106

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )

    await session.delete(db_product)
    await session.commit()
    return db_product  # 返回被删除的资源
```

**响应选择**：
```python
# 选项 1：返回被删除的资源（你的项目）
return db_product  # 200 OK + 资源数据

# 选项 2：返回 204 No Content
return Response(status_code=status.HTTP_204_NO_CONTENT)
```

---

## 4. 状态码选择与使用

### 4.1 状态码分类

| 类别 | 范围 | 含义 |
|------|------|------|
| 1xx | 100-199 | 信息响应（很少用）|
| 2xx | 200-299 | 成功 |
| 3xx | 300-399 | 重定向 |
| 4xx | 400-499 | 客户端错误 |
| 5xx | 500-599 | 服务器错误 |

### 4.2 常用状态码详解

#### 2xx 成功

**200 OK** - 请求成功
```python
# 你的项目：GET、PUT、DELETE 返回 200
@router.get("/{product_id}")  # 返回 200
@router.put("/{product_id}")  # 返回 200
@router.delete("/{product_id}")  # 返回 200
```

**201 Created** - 资源创建成功
```python
# 你的项目：POST 返回 201
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(product: schemas.ProductCreate):
    # 创建成功返回 201
    pass
```

**204 No Content** - 成功但无返回内容
```python
# 适用场景：DELETE 不返回资源
@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int):
    # 删除成功，不返回内容
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

#### 4xx 客户端错误

**400 Bad Request** - 请求格式错误
```python
# 示例：JSON 格式错误
{
  "name": "Game"
  "price": 100  # 缺少逗号
}
```

**401 Unauthorized** - 未认证
```python
# 示例：未登录
raise HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"}
)
```

**403 Forbidden** - 已认证但无权限
```python
# 示例：普通用户尝试删除管理员资源
raise HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="You don't have permission to delete this resource"
)
```

**404 Not Found** - 资源不存在
```python
# 你的项目实现
if not product:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Product with id {product_id} not found"
    )
```

**422 Unprocessable Entity** - 验证失败
```python
# FastAPI 自动返回 422
# 示例：target_price 应该是数字，但传了字符串
{
  "name": "Game",
  "target_price": "not a number"  # 验证失败
}

# 响应
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

#### 5xx 服务器错误

**500 Internal Server Error** - 服务器内部错误
```python
# 示例：数据库连接失败、未捕获的异常
try:
    result = await session.execute(stmt)
except Exception as e:
    # 未处理的异常会返回 500
    raise
```

### 4.3 你的项目状态码使用总结

| 场景 | 状态码 | 代码位置 |
|------|--------|----------|
| 创建商品成功 | `201 Created` | `products.py:12` |
| 获取商品成功 | `200 OK` | `products.py:28, 43` |
| 更新商品成功 | `200 OK` | `products.py:61` |
| 删除商品成功 | `200 OK` | `products.py:88` |
| 商品不存在 | `404 Not Found` | `products.py:54, 74, 100` |
| 请求验证失败 | `422 Unprocessable Entity` | FastAPI 自动处理 |

### 4.4 面试高频问题

```
Q: 400 和 422 的区别？
A: 400：请求格式错误（如 JSON 格式错误）
   422：请求格式正确，但验证失败（如字段类型错误）

Q: 401 和 403 的区别？
A: 401：未认证（没登录）→ "请先登录"
   403：已认证但无权限（登录了但权限不够）→ "你没有权限"

Q: 什么时候返回 200，什么时候返回 201？
A: 200：通用成功响应（GET、PUT、DELETE）
   201：创建资源成功（POST）

Q: DELETE 应该返回什么状态码？
A: 两种选择都可以：
   - 200 + 被删除的资源（你的项目）
   - 204 No Content（不返回内容）
```

---

## 5. 请求与响应设计

### 5.1 请求体设计（Request Body）

✅ **你的项目使用 Pydantic Schema**：
```python
# 创建商品的请求体
class ProductCreate(SQLModel):
    name: str
    url: str
    platform: str
    target_price: float

# 更新商品的请求体
class ProductUpdate(SQLModel):
    name: Optional[str] = None
    url: Optional[str] = None
    target_price: Optional[float] = None
```

**请求示例**：
```http
POST /products/
Content-Type: application/json

{
  "name": "Elden Ring",
  "url": "https://store.steampowered.com/app/1245620/",
  "platform": "steam",
  "target_price": 199.00
}
```

**面试要点**：
- 使用 JSON 格式（`Content-Type: application/json`）
- 字段命名使用 snake_case（`target_price`）
- 必填字段不提供默认值
- 可选字段使用 `Optional` 并提供默认值

### 5.2 响应体设计（Response Body）

✅ **你的项目使用 response_model**：
```python
@router.post("/", response_model=schemas.ProductRead)
async def create_product(product: schemas.ProductCreate):
    pass

# ProductRead Schema
class ProductRead(SQLModel):
    id: int
    name: str
    url: str
    platform: str
    target_price: float
    current_price: Optional[float] = None
    created_at: datetime
```

**响应示例**：
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": 1,
  "name": "Elden Ring",
  "url": "https://store.steampowered.com/app/1245620/",
  "platform": "steam",
  "target_price": 199.00,
  "current_price": null,
  "created_at": "2024-03-09T10:00:00"
}
```

**面试要点**：
- 返回的数据包含 ID（客户端需要）
- 包含时间戳（`created_at`）
- 使用 `response_model` 自动过滤字段
- 不返回敏感信息（如密码）

### 5.3 错误响应设计

✅ **你的项目错误处理**：
```python
if not product:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Product with id {product_id} not found"
    )
```

**错误响应示例**：
```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "detail": "Product with id 999 not found"
}
```

**标准错误响应格式**：
```json
{
  "error": {
    "code": "PRODUCT_NOT_FOUND",
    "message": "Product with id 999 not found",
    "details": {
      "product_id": 999
    }
  }
}
```

### 5.4 分页响应设计

✅ **你的项目分页实现**：
```python
@router.get("/", response_model=List[schemas.ProductRead])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    result = await session.execute(
        select(models.Product).offset(skip).limit(limit)
    )
    return result.scalars().all()
```

**当前响应**：
```json
[
  {"id": 1, "name": "Game 1"},
  {"id": 2, "name": "Game 2"}
]
```

**改进建议（面试加分项）**：
```json
{
  "data": [
    {"id": 1, "name": "Game 1"},
    {"id": 2, "name": "Game 2"}
  ],
  "pagination": {
    "total": 100,
    "skip": 0,
    "limit": 10,
    "has_more": true
  }
}
```

---

## 6. 幂等性与安全性

### 6.1 什么是幂等性？

**定义**：多次执行相同操作，结果相同。

**面试必考**：

| HTTP 方法 | 幂等性 | 说明 |
|-----------|--------|------|
| `GET` | ✅ 是 | 多次获取，结果相同 |
| `POST` | ❌ 否 | 多次创建，产生多个资源 |
| `PUT` | ✅ 是 | 多次更新，结果相同 |
| `PATCH` | ❌ 否 | 取决于实现 |
| `DELETE` | ✅ 是 | 多次删除，资源仍然不存在 |

### 6.2 幂等性示例

**PUT 是幂等的**：
```python
# 第 1 次执行
PUT /products/1
{"name": "Game", "price": 100}
# 结果：name="Game", price=100

# 第 2 次执行（相同请求）
PUT /products/1
{"name": "Game", "price": 100}
# 结果：name="Game", price=100（相同）
```

**POST 不是幂等的**：
```python
# 第 1 次执行
POST /products/
{"name": "Game", "price": 100}
# 结果：创建 id=1 的商品

# 第 2 次执行（相同请求）
POST /products/
{"name": "Game", "price": 100}
# 结果：创建 id=2 的商品（不同）
```

**DELETE 是幂等的**：
```python
# 第 1 次执行
DELETE /products/1
# 结果：商品被删除

# 第 2 次执行
DELETE /products/1
# 结果：返回 404（商品仍然不存在）
```

### 6.3 什么是安全性？

**定义**：不修改服务器状态的操作。

| HTTP 方法 | 安全性 | 说明 |
|-----------|--------|------|
| `GET` | ✅ 是 | 只读，不修改数据 |
| `POST` | ❌ 否 | 创建资源 |
| `PUT` | ❌ 否 | 修改资源 |
| `DELETE` | ❌ 否 | 删除资源 |

**面试要点**：
- 安全的方法可以被缓存
- 安全的方法可以被预加载（浏览器预取）
- GET 请求不应该有副作用

---

## 7. 版本控制

### 7.1 为什么需要版本控制？

**场景**：
- API 需要重大变更
- 不能破坏现有客户端
- 需要同时支持新旧版本

### 7.2 版本控制方式

#### 方式 1：URL 路径版本（推荐）

```python
# v1 版本
@router.get("/api/v1/products/")

# v2 版本
@router.get("/api/v2/products/")
```

**优点**：
- 清晰明确
- 易于路由
- 易于测试

#### 方式 2：请求头版本

```http
GET /api/products/
Accept: application/vnd.myapi.v1+json
```

#### 方式 3：查询参数版本

```http
GET /api/products/?version=1
```

### 7.3 你的项目可以添加版本控制

```python
# app/main.py

from fastapi import FastAPI

app = FastAPI()

# V1 API
from app.routers import products as products_v1
app.include_router(products_v1.router, prefix="/api/v1")

# V2 API（未来）
# from app.routers import products_v2
# app.include_router(products_v2.router, prefix="/api/v2")
```

**URL 变化**：
```
# 之前
GET /products/

# 添加版本后
GET /api/v1/products/
```

---

## 8. 常见面试问题

### 8.1 RESTful 基础问题

**Q1: 什么是 RESTful API？**
```
A: REST 是一种架构风格，RESTful API 遵循 REST 原则：
   1. 资源导向（使用名词）
   2. 使用标准 HTTP 方法
   3. 无状态
   4. 统一接口
   5. 资源通过 URL 唯一标识
```

**Q2: RESTful API 的优点是什么？**
```
A: 1. 简单易懂（使用标准 HTTP）
   2. 无状态（易于扩展）
   3. 可缓存（提高性能）
   4. 分层系统（易于维护）
   5. 跨平台（任何语言都可以调用）
```

**Q3: REST 和 SOAP 的区别？**
```
A: REST:
   - 轻量级，使用 JSON
   - 基于 HTTP
   - 无状态
   - 易于使用

   SOAP:
   - 重量级，使用 XML
   - 可以使用多种协议
   - 有状态
   - 更严格的规范
```

### 8.2 HTTP 方法问题

**Q4: GET 和 POST 的区别？**
```
A: 1. 用途：GET 获取数据，POST 创建数据
   2. 参数：GET 在 URL，POST 在 Body
   3. 长度：GET 有限制，POST 无限制
   4. 缓存：GET 可缓存，POST 不可缓存
   5. 幂等：GET 幂等，POST 不幂等
   6. 安全：GET 安全，POST 不安全
```

**Q5: PUT 和 PATCH 的区别？**
```
A: PUT：完整替换资源（幂等）
   - 必须提供所有字段
   - 多次执行结果相同

   PATCH：部分更新资源（可能不幂等）
   - 只提供需要更新的字段
   - 取决于实现方式
```

**Q6: 什么是幂等性？为什么重要？**
```
A: 幂等性：多次执行相同操作，结果相同

   重要性：
   1. 网络不稳定时可以安全重试
   2. 避免重复操作（如重复扣款）
   3. 提高系统可靠性

   幂等的方法：GET、PUT、DELETE
   非幂等的方法：POST
```


### 8.3 状态码问题

**Q7: 常用的 HTTP 状态码有哪些？**
```
A: 2xx 成功：
   - 200 OK：请求成功
   - 201 Created：创建成功
   - 204 No Content：成功但无内容

   4xx 客户端错误：
   - 400 Bad Request：请求格式错误
   - 401 Unauthorized：未认证
   - 403 Forbidden：无权限
   - 404 Not Found：资源不存在
   - 422 Unprocessable Entity：验证失败

   5xx 服务器错误：
   - 500 Internal Server Error：服务器错误
```

**Q8: 401 和 403 的区别？**
```
A: 401 Unauthorized：未认证（没登录）
   - 需要提供认证信息
   - 响应头：WWW-Authenticate

   403 Forbidden：已认证但无权限
   - 已登录但权限不够
   - 即使提供认证信息也无法访问
```

**Q9: 什么时候返回 200，什么时候返回 201？**
```
A: 200 OK：通用成功响应
   - GET：获取资源成功
   - PUT：更新资源成功
   - DELETE：删除资源成功

   201 Created：创建资源成功
   - POST：创建新资源
   - 应该返回创建的资源
   - 可以在响应头添加 Location
```

### 8.4 设计问题

**Q10: 如何设计一个商品评论的 API？**
```
A: 资源关系：商品 -> 评论

   URL 设计：
   POST   /products/{id}/comments      # 创建评论
   GET    /products/{id}/comments      # 获取评论列表
   GET    /comments/{id}               # 获取单个评论
   PUT    /comments/{id}               # 更新评论
   DELETE /comments/{id}               # 删除评论

   说明：
   - 创建评论属于商品的子资源
   - 操作评论本身使用 /comments
```

**Q11: 如何设计分页 API？**
```
A: 方式 1：Offset + Limit（你的项目）
   GET /products?skip=0&limit=10

   方式 2：Page + Size
   GET /products?page=1&size=10

   方式 3：Cursor（大数据量）
   GET /products?cursor=abc123&limit=10

   响应应该包含：
   - 数据列表
   - 总数
   - 当前页/偏移量
   - 是否还有更多数据
```

**Q12: 如何处理批量操作？**
```
A: 方式 1：批量端点
   POST /products/batch
   {
     "ids": [1, 2, 3],
     "action": "delete"
   }

   方式 2：单独请求（推荐）
   DELETE /products/1
   DELETE /products/2
   DELETE /products/3

   说明：
   - 单独请求更符合 REST 原则
   - 可以并发执行
   - 错误处理更清晰
```

### 8.5 项目相关问题

**Q13: 介绍一下你的项目 API 设计**
```
A: 我的项目是价格监控系统，设计了 RESTful API：

   资源：商品（products）、价格历史（history）

   API 端点：
   - POST   /products/              创建商品
   - GET    /products/              商品列表（支持分页）
   - GET    /products/{id}          商品详情
   - PUT    /products/{id}          更新商品
   - DELETE /products/{id}          删除商品
   - GET    /products/{id}/history  价格历史

   技术栈：
   - FastAPI：自动文档、类型验证
   - Pydantic：请求/响应验证
   - 异步数据库操作

   特点：
   - 遵循 RESTful 规范
   - 使用正确的 HTTP 方法和状态码
   - 支持分页和查询参数验证
   - 层级关系表示子资源
```

**Q14: 你的项目如何处理错误？**
```
A: 使用 FastAPI 的 HTTPException：

   1. 资源不存在：404
   if not product:
       raise HTTPException(
           status_code=404,
           detail=f"Product with id {id} not found"
       )

   2. 验证失败：422（FastAPI 自动处理）
   - Pydantic 自动验证请求体
   - 类型错误、必填字段缺失等

   3. 服务器错误：500
   - 未捕获的异常
   - 数据库连接失败等

   改进方向：
   - 统一错误响应格式
   - 添加错误码
   - 记录错误日志
```

**Q15: 如果要添加用户认证，你会怎么设计？**
```
A: 1. 认证端点：
   POST /auth/login       # 登录，返回 token
   POST /auth/register    # 注册
   POST /auth/logout      # 登出

   2. 保护资源：
   @router.post("/products/")
   async def create_product(
       product: ProductCreate,
       current_user: User = Depends(get_current_user)  # 依赖注入
   ):
       pass

   3. Token 验证：
   - 使用 JWT（JSON Web Token）
   - 请求头：Authorization: Bearer <token>
   - 验证 token 有效性和过期时间

   4. 权限控制：
   - 普通用户：只能操作自己的商品
   - 管理员：可以操作所有商品
```

---

## 9. 总结与最佳实践

### 9.1 RESTful API 设计清单

✅ **URL 设计**
- [ ] 使用名词，不使用动词
- [ ] 使用复数形式
- [ ] 使用小写字母和连字符
- [ ] 层级关系表示子资源
- [ ] 查询参数用于过滤和分页

✅ **HTTP 方法**
- [ ] GET 用于获取资源
- [ ] POST 用于创建资源
- [ ] PUT 用于更新资源
- [ ] DELETE 用于删除资源
- [ ] 正确理解幂等性和安全性

✅ **状态码**
- [ ] 200 用于通用成功
- [ ] 201 用于创建成功
- [ ] 404 用于资源不存在
- [ ] 422 用于验证失败
- [ ] 500 用于服务器错误

✅ **请求与响应**
- [ ] 使用 JSON 格式
- [ ] 请求体使用 Schema 验证
- [ ] 响应体包含必要信息（ID、时间戳）
- [ ] 错误响应包含详细信息

✅ **其他**
- [ ] 支持分页
- [ ] 支持过滤和排序
- [ ] 考虑版本控制
- [ ] 提供 API 文档

### 9.2 你的项目优点

✅ **已经做得很好的地方**：
1. 遵循 RESTful 规范
2. 使用正确的 HTTP 方法
3. 使用正确的状态码（201、404）
4. 支持分页（skip、limit）
5. 使用 Pydantic 验证
6. 层级关系表示子资源（/products/{id}/history）
7. 异步数据库操作
8. 自动生成 API 文档

### 9.3 改进建议（面试加分项）

🔧 **可以改进的地方**：
1. 添加版本控制（/api/v1/products）
2. 统一错误响应格式
3. 分页响应包含元数据（total、has_more）
4. 添加过滤和排序（?platform=steam&sort=price）
5. 添加用户认证和权限控制
6. 添加限流（Rate Limiting）
7. 添加 API 文档说明

### 9.4 面试准备建议

**准备讲述你的项目**：
```
1. 项目背景
   "我做了一个价格监控系统，监控 Steam 游戏价格..."

2. API 设计
   "我设计了 RESTful API，包括商品的 CRUD 操作和价格历史查询..."

3. 技术选型
   "使用 FastAPI 因为它支持异步、自动文档、类型验证..."

4. 遵循规范
   "严格遵循 RESTful 规范，使用正确的 HTTP 方法和状态码..."

5. 实现细节
   "使用 Pydantic 进行请求验证，使用依赖注入管理数据库连接..."

6. 遇到的挑战
   "如何设计层级资源关系，如何处理错误..."

7. 未来改进
   "添加用户认证、版本控制、更完善的错误处理..."
```

---

## 10. 参考资源

### 官方文档
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [HTTP 状态码](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status)
- [REST API 设计指南](https://restfulapi.net/)

### 推荐阅读
- 《RESTful Web APIs》
- 《HTTP 权威指南》
- 《Web API 设计》

---

**祝你面试顺利！** 🎉

记住：
1. 理解 REST 核心原则
2. 熟悉 HTTP 方法和状态码
3. 能够流畅讲解你的项目
4. 准备常见面试问题的答案
