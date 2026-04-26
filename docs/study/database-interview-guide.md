# 数据库与 ORM 面试详解

> 基于 Price Monitor 项目的深度解析，达到面试官期望的回答标准

---

## 目录

- [一、SQL 基础（面试必考）](#一sql-基础面试必考)
- [二、PostgreSQL 特性](#二postgresql-特性)
- [三、SQLModel/SQLAlchemy ORM](#三sqlmodelsqlalchemy-orm)
- [四、数据库设计原则](#四数据库设计原则)
- [五、数据库性能优化](#五数据库性能优化)
- [六、事务与并发控制](#六事务与并发控制)
- [七、面试高频问题汇总](#七面试高频问题汇总)

---

## 一、SQL 基础（面试必考）

### 1.1 四大基本操作（CRUD）

面试官常问：**"请写出基本的 SQL 增删改查语句"**

#### CREATE（插入数据）

```sql
-- 向 products 表插入一条记录
INSERT INTO products (name, url, platform, target_price, current_price)
VALUES ('Elden Ring', 'https://store.steampowered.com/app/1245620', 'steam', 199.00, 298.00);

-- 批量插入
INSERT INTO products (name, url, platform, target_price)
VALUES
    ('Game 1', 'url1', 'steam', 99.00),
    ('Game 2', 'url2', 'steam', 149.00);
```

**你的项目对应代码**（`app/routers/products.py:12-25`）：
```python
@router.post("/", response_model=schemas.ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: schemas.ProductCreate,
    session: AsyncSession = Depends(get_session)
):
    """创建商品"""
    db_product = models.Product.from_orm(product)  # Pydantic 模型转 ORM 模型
    session.add(db_product)       # 添加到会话（相当于 INSERT 语句）
    await session.commit()        # 提交事务（真正执行 SQL）
    await session.refresh(db_product)  # 刷新获取数据库生成的字段（如 id）
    return db_product
```

**面试加分点**：
> "在我的项目中，使用 ORM 而不是手写 SQL。`session.add()` 不会立即执行 SQL，而是将对象加入会话的待处理列表。只有调用 `commit()` 时才会真正执行 INSERT 语句。这样可以批量操作，提高性能。"

---

#### READ（查询数据）

```sql
-- 查询所有商品
SELECT * FROM products;

-- 条件查询
SELECT * FROM products WHERE platform = 'steam';

-- 排序和分页
SELECT * FROM products
ORDER BY target_price DESC
LIMIT 10 OFFSET 0;

-- 关联查询（你的项目中 Product 和 PriceHistory 是一对多关系）
SELECT p.name, ph.price, ph.check_time
FROM products p
INNER JOIN pricehistory ph ON p.id = ph.product_id
WHERE p.id = 1
ORDER BY ph.check_time DESC;
```

**你的项目对应代码**（`app/routers/products.py:28-40`）：
```python
@router.get("/", response_model=List[schemas.ProductRead])
async def list_products(
    skip: int = Query(0, ge=0),      # OFFSET
    limit: int = Query(100, ge=1, le=100),  # LIMIT
    session: AsyncSession = Depends(get_session)
):
    """获取商品列表（带分页）"""
    result = await session.execute(
        select(models.Product).offset(skip).limit(limit)
    )
    products = result.scalars().all()  # 获取所有结果
    return products
```

**单条查询**（`app/routers/products.py:43-58`）：
```python
@router.get("/{product_id}", response_model=schemas.ProductRead)
async def get_product(product_id: int, session: AsyncSession = Depends(get_session)):
    """获取单个商品"""
    result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    product = result.scalar_one_or_none()  # 获取单条或 None
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with id {product_id} not found")
    return product
```

**面试加分点**：
> "我使用 `scalar_one_or_none()` 而不是 `one()` 或 `all()`。因为：
> - `one()` 找不到会抛异常，找到多条也会抛异常
> - `all()` 返回列表，需要额外判断
> - `scalar_one_or_none()` 找到返回对象，找不到返回 None，最灵活"

---

#### UPDATE（更新数据）

```sql
-- 更新单个字段
UPDATE products SET current_price = 89.99 WHERE id = 1;

-- 更新多个字段
UPDATE products
SET current_price = 89.99, last_checked_time = NOW()
WHERE id = 1;

-- 条件更新
UPDATE products
SET current_price = target_price
WHERE current_price IS NULL;
```

**你的项目对应代码**（`app/routers/products.py:61-85`）：
```python
@router.put("/{product_id}", response_model=schemas.ProductRead)
async def update_product(
    product_id: int,
    product_update: schemas.ProductUpdate,  # 所有字段都是 Optional
    session: AsyncSession = Depends(get_session)
):
    """更新商品（部分更新）"""
    # 1. 先查询
    result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(status_code=404, detail="...")

    # 2. 只更新提供的字段（PATCH 语义）
    product_data = product_update.dict(exclude_unset=True)  # 关键！
    for field, value in product_data.items():
        setattr(db_product, field, value)

    # 3. 提交
    await session.commit()
    await session.refresh(db_product)
    return db_product
```

**面试加分点**：
> "我使用 `dict(exclude_unset=True)` 来实现部分更新（Partial Update）。这样用户只需要传想修改的字段，其他字段保持不变。这是 RESTful API 的最佳实践。"

---

#### DELETE（删除数据）

```sql
-- 删除单条
DELETE FROM products WHERE id = 1;

-- 条件删除
DELETE FROM products WHERE current_price IS NULL;

-- 删除所有（危险！）
DELETE FROM products;
```

**你的项目对应代码**（`app/routers/products.py:88-106`）：
```python
@router.delete("/{product_id}", response_model=schemas.ProductRead)
async def delete_product(product_id: int, session: AsyncSession = Depends(get_session)):
    """删除商品"""
    # 先查询
    result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    db_product = result.scalar_one_or_none()

    if not db_product:
        raise HTTPException(status_code=404, detail="...")

    # 删除并返回被删除的对象
    await session.delete(db_product)
    await session.commit()
    return db_product  # 返回被删除的数据
```

---

### 1.2 JOIN 详解（高频面试题）

**面试官常问：**"请解释 JOIN 的几种类型和区别"

#### JOIN 类型对比

```
┌─────────────────────────────────────────────────────────────┐
│                        JOIN 类型对比                         │
├──────────────┬──────────────────────────────────────────────┤
│ INNER JOIN   │ 只返回两个表中都匹配的行                       │
├──────────────┼──────────────────────────────────────────────┤
│ LEFT JOIN    │ 返回左表所有行，右表没有则 NULL                │
├──────────────┼──────────────────────────────────────────────┤
│ RIGHT JOIN   │ 返回右表所有行，左表没有则 NULL                │
├──────────────┼──────────────────────────────────────────────┤
│ FULL JOIN    │ 返回两表所有行，不匹配则为 NULL                │
└──────────────┴──────────────────────────────────────────────┘
```

#### 图解 JOIN

```
     INNER JOIN          LEFT JOIN           RIGHT JOIN         FULL JOIN
    ┌─────────┐        ┌─────────┐         ┌─────────┐        ┌─────────┐
    │    A    │        │    A    │         │    A    │        │    A    │
    │  ┌───┐  │        │  ┌───┐  │         │  ┌───┐  │        │  ┌───┐  │
    │  │███│  │        │██│███│  │         │  │███│██│        │██│███│██│
    │  └───┘  │        │  └───┘  │         │  └───┘  │        │  └───┘  │
    │    B    │        │    B    │         │    B    │        │    B    │
    └─────────┘        └─────────┘         └─────────┘        └─────────┘
     只取交集             左边全取            右边全取            两边全取
```

#### 你的项目中的关联查询

```sql
-- 查询商品及其价格历史（INNER JOIN - 只显示有历史记录的商品）
SELECT p.name, ph.price, ph.check_time
FROM products p
INNER JOIN pricehistory ph ON p.id = ph.product_id;

-- 查询所有商品及其价格历史（LEFT JOIN - 显示所有商品，没有历史则为 NULL）
SELECT p.name, ph.price, ph.check_time
FROM products p
LEFT JOIN pricehistory ph ON p.id = ph.product_id;
```

**ORM 中的关联查询**（`app/routers/products.py:109-137`）：
```python
@router.get("/{product_id}/history", response_model=List[schemas.PriceHistoryRead])
async def get_price_history(product_id: int, session: AsyncSession = Depends(get_session)):
    """获取价格历史"""
    # 先验证商品存在
    product_result = await session.execute(
        select(models.Product).where(models.Product.id == product_id)
    )
    product = product_result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="...")

    # 查询价格历史
    result = await session.execute(
        select(models.PriceHistory)
        .where(models.PriceHistory.product_id == product_id)
        .order_by(models.PriceHistory.check_time.desc())
        .offset(skip)
        .limit(limit)
    )
    history = result.scalars().all()
    return history
```

**面试加分点**：
> "在我的项目中，Product 和 PriceHistory 是一对多关系。通过 `Relationship` 定义后，可以直接访问 `product.history` 获取关联数据。但在 API 中我选择显式查询，因为更清晰可控，也便于添加过滤和排序。"

---

### 1.3 聚合函数与分组

```sql
-- 统计商品数量
SELECT COUNT(*) FROM products;

-- 按平台分组统计
SELECT platform, COUNT(*) as count
FROM products
GROUP BY platform;

-- 统计每个商品的价格变化次数
SELECT product_id, COUNT(*) as check_count, AVG(price) as avg_price
FROM pricehistory
GROUP BY product_id
HAVING COUNT(*) > 5;  -- HAVING 用于过滤分组后的结果

-- 查询最低价
SELECT product_id, MIN(price) as min_price, MAX(price) as max_price
FROM pricehistory
GROUP BY product_id;
```

**面试必问**：**WHERE 和 HAVING 的区别？**

```
WHERE: 过滤原始行，在 GROUP BY 之前
HAVING: 过滤分组后的结果，在 GROUP BY 之后

示例：
SELECT platform, COUNT(*) as count
FROM products
WHERE target_price > 100   -- 先过滤 target_price > 100 的商品
GROUP BY platform
HAVING COUNT(*) > 3;       -- 再过滤商品数 > 3 的平台
```

---

## 二、PostgreSQL 特性

### 2.1 为什么选择 PostgreSQL？

面试官问：**"你的项目为什么用 PostgreSQL 而不是 MySQL？"**

**标准回答**：
> "选择 PostgreSQL 主要考虑以下几点：
>
> 1. **JSONB 支持**：PostgreSQL 的 JSONB 类型比 MySQL 的 JSON 更强大，支持索引和高效查询
> 2. **更好的并发控制**：MVCC 实现更优秀，读操作不阻塞写操作
> 3. **丰富的数据类型**：支持数组、JSON、几何类型等
> 4. **更好的 SQL 标准兼容性**：更严格地遵循 SQL 标准
> 5. **开源且免费**：完全开源，没有企业版功能限制
>
> 对于我的价格监控项目，未来可能需要存储商品的各种元数据（如配置要求、标签等），PostgreSQL 的 JSONB 类型会非常方便。"

---

### 2.2 PostgreSQL 独有特性

#### JSONB 类型

```sql
-- 创建带 JSONB 字段的表
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    metadata JSONB  -- 存储任意 JSON 数据
);

-- 插入 JSON 数据
INSERT INTO products (name, metadata)
VALUES ('Game', '{"tags": ["RPG", "Action"], "rating": 4.5}');

-- 查询 JSON 字段
SELECT name, metadata->>'rating' as rating FROM products;
SELECT name FROM products WHERE metadata @> '{"tags": ["RPG"]}';
```

#### 数组类型

```sql
-- 创建带数组字段的表
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT,
    tags TEXT[]  -- 文本数组
);

-- 插入数组数据
INSERT INTO products (name, tags) VALUES ('Game', ARRAY['RPG', 'Action']);

-- 查询数组
SELECT * FROM products WHERE 'RPG' = ANY(tags);
```

---

### 2.3 你的项目数据库配置

**配置文件**（`app/database.py`）：
```python
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

# 数据库连接字符串
# postgresql+asyncpg://用户名:密码@主机:端口/数据库名
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://admin:mypassword@localhost:5432/monitor_db"
)

# 创建异步引擎
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# 初始化数据库（创建表）
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# 获取数据库会话（依赖注入）
async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False  # 重要！提交后对象不过期
    )
    async with async_session() as session:
        yield session
```

**面试加分点**：
> "我使用 `asyncpg` 作为 PostgreSQL 的异步驱动，比同步驱动性能更好。`expire_on_commit=False` 是一个重要的配置，它让对象在 commit 后仍然可以访问属性，否则会触发额外的数据库查询。"

---

## 三、SQLModel/SQLAlchemy ORM

### 3.1 什么是 ORM？

**面试回答**：
> "ORM（Object-Relational Mapping）是对象关系映射，它将数据库表映射为 Python 类，将表中的行映射为对象实例。使用 ORM 的好处是：
>
> 1. **不用手写 SQL**：减少错误，提高开发效率
> 2. **数据库无关**：切换数据库只需要改连接字符串
> 3. **类型安全**：配合类型提示，IDE 能提供更好的支持
> 4. **防 SQL 注入**：ORM 会自动转义参数
>
> SQLModel 是 SQLAlchemy 和 Pydantic 的结合体，既有 SQLAlchemy 的强大功能，又有 Pydantic 的数据验证。"

---

### 3.2 模型定义详解

**你的项目模型**（`app/models.py`）：
```python
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

# ============ 基类（不映射到数据库）============
class ProductBase(SQLModel):
    """商品基类 - 定义公共字段"""
    name: str
    url: str
    platform: str = Field(default="steam")
    target_price: float

# ============ 商品表 ============
class Product(ProductBase, table=True):  # table=True 表示映射到数据库表
    id: Optional[int] = Field(default=None, primary_key=True)  # 主键，自动生成
    current_price: Optional[float] = None
    last_checked_time: Optional[datetime] = None

    # 关系：一个商品有多个价格历史记录（list）
    history: List["PriceHistory"] = Relationship(back_populates="product")

# ============ 价格历史表 ============
class PriceHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    price: float
    check_time: datetime = Field(default_factory=datetime.now)  # 默认值：当前时间

    # 外键：关联到 products 表的 id 字段
    product_id: int = Field(foreign_key="product.id")

    # 关系：每条历史记录属于一个商品
    product: Optional[Product] = Relationship(back_populates="history")
```

#### Field 参数详解

| 参数 | 说明 | 示例 |
|------|------|------|
| `primary_key` | 主键 | `Field(primary_key=True)` |
| `default` | 默认值 | `Field(default="steam")` |
| `default_factory` | 默认值工厂函数 | `Field(default_factory=datetime.now)` |
| `foreign_key` | 外键 | `Field(foreign_key="product.id")` |
| `index` | 是否创建索引 | `Field(index=True)` |
| `unique` | 是否唯一 | `Field(unique=True)` |
| `nullable` | 是否允许 NULL | `Field(nullable=False)` |

---

### 3.3 Relationship 详解

**面试官问：**"请解释 Relationship 的作用和 back_populates"

**标准回答**：
> "Relationship 定义了表之间的关联关系，让我们可以通过对象属性直接访问关联数据，而不需要手写 JOIN 查询。
>
> `back_populates` 是双向绑定的关键：
>
> ```python
> # Product 表
> history: List["PriceHistory"] = Relationship(back_populates="product")
>
> # PriceHistory 表
> product: Optional[Product] = Relationship(back_populates="history")
> ```
>
> 这样设置后：
> - `product.history` 可以获取该商品的所有价格历史
> - `price_history.product` 可以获取该历史记录所属的商品
>
> 注意 `"PriceHistory"` 用字符串是因为类定义顺序问题，Python 会延迟解析。"

#### 关系类型

```
┌─────────────────────────────────────────────────────────────────┐
│                        关系类型                                  │
├─────────────────┬───────────────────────────────────────────────┤
│ 一对一 (1:1)     │ 一个用户对应一个资料                          │
│                 │ user.profile / profile.user                   │
├─────────────────┼───────────────────────────────────────────────┤
│ 一对多 (1:N)     │ 一个商品有多个价格历史 ← 你的项目              │
│                 │ product.history / history.product             │
├─────────────────┼───────────────────────────────────────────────┤
│ 多对多 (M:N)     │ 一个商品有多个标签，一个标签属于多个商品       │
│                 │ 需要中间表来实现                               │
└─────────────────┴───────────────────────────────────────────────┘
```

---

### 3.4 Schema 模式（Pydantic）

**你的项目 Schema**（`app/schemas.py`）：
```python
from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime

# ============ 基类 ============
class ProductBaseSchema(SQLModel):
    """API 层的公共字段"""
    name: str
    url: str
    platform: str = "steam"
    target_price: float

# ============ 创建请求 ============
class ProductCreate(ProductBaseSchema):
    """创建商品时的请求体"""
    pass  # 继承所有字段

# ============ 读取响应 ============
class ProductRead(ProductBaseSchema):
    """返回给客户端的响应体"""
    id: int  # 包含 id
    current_price: Optional[float] = None
    last_checked_time: Optional[datetime] = None

# ============ 更新请求 ============
class ProductUpdate(SQLModel):
    """更新商品时的请求体 - 所有字段可选"""
    name: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None
    target_price: Optional[float] = None
    current_price: Optional[float] = None
    last_checked_time: Optional[datetime] = None
```

**面试官问：**"为什么要把 Model 和 Schema 分开？"

**标准回答**：
> "分开 Model 和 Schema 是最佳实践，原因如下：
>
> 1. **关注点分离**：
>    - Model（`models.py`）：数据库层，定义表结构和关系
>    - Schema（`schemas.py`）：API 层，定义请求/响应格式和验证规则
>
> 2. **安全性**：
>    - 创建用户时不应包含 `id`、`created_at` 等服务端生成的字段
>    - 返回用户时可能需要隐藏 `password` 等敏感字段
>
> 3. **灵活性**：
>    - 更新接口所有字段设为 Optional，实现部分更新
>    - 可以添加额外的验证逻辑
>
> 4. **文档生成**：
>    - FastAPI 根据 Schema 自动生成 OpenAPI 文档
>    - 不同的 Schema 展示不同的接口需求"

---

### 3.5 CRUD 操作完整流程

#### 创建流程

```
┌──────────────────────────────────────────────────────────────────┐
│                        创建商品流程                               │
├──────────────────────────────────────────────────────────────────┤
│  客户端请求                                                       │
│  POST /products                                                  │
│  {"name": "Game", "url": "...", "target_price": 99.0}           │
│                           ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 1. FastAPI 接收请求，用 ProductCreate 验证               │    │
│  │    product: ProductCreate                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 2. 转换为 ORM 模型                                        │    │
│  │    db_product = Product.from_orm(product)               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 3. 添加到会话                                             │    │
│  │    session.add(db_product)                              │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 4. 提交事务（执行 SQL INSERT）                            │    │
│  │    await session.commit()                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 5. 刷新获取数据库生成的字段                                │    │
│  │    await session.refresh(db_product)                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                           ↓                                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ 6. 返回响应（用 ProductRead 格式化）                      │    │
│  │    {"id": 1, "name": "Game", ...}                       │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

#### 查询流程

```python
# 基本查询
result = await session.execute(
    select(models.Product).where(models.Product.id == product_id)
)
product = result.scalar_one_or_none()

# 带排序的查询
result = await session.execute(
    select(models.PriceHistory)
    .where(models.PriceHistory.product_id == product_id)
    .order_by(models.PriceHistory.check_time.desc())  # 按时间倒序
    .offset(skip)
    .limit(limit)
)
history = result.scalars().all()
```

#### 查询结果获取方法对比

| 方法 | 返回值 | 适用场景 |
|------|--------|----------|
| `all()` | 列表 | 获取多条记录 |
| `one()` | 单个对象 | 确定只有一条，否则抛异常 |
| `scalar_one()` | 单个值 | 获取单个值（如 COUNT） |
| `scalar_one_or_none()` | 单个值或 None | 获取单个值，找不到返回 None |
| `scalars().all()` | 对象列表 | 获取 ORM 对象列表 |
| `scalars().first()` | 第一个对象 | 获取第一条记录 |

---

## 四、数据库设计原则

### 4.1 范式（Normalization）

**面试官问：**"什么是数据库范式？"

**标准回答**：
> "数据库范式是设计数据库表的规范，目的是减少数据冗余和不一致性。
>
> 主要范式：
>
> - **第一范式（1NF）**：每个字段都是原子值，不可再分
> - **第二范式（2NF）**：在 1NF 基础上，非主键字段完全依赖主键
> - **第三范式（3NF）**：在 2NF 基础上，非主键字段不传递依赖主键
>
> 以我的项目为例：
>
> ```sql
> -- 反范式设计（不好）
> CREATE TABLE bad_products (
>     id INT,
>     name TEXT,
>     platform_name TEXT,   -- 平台信息重复存储
>     platform_url TEXT,
>     price1 FLOAT,         -- 价格历史混在一起
>     price2 FLOAT,
>     price3 FLOAT
> );
>
> -- 范式设计（好）- 我的项目的做法
> CREATE TABLE products (
>     id SERIAL PRIMARY KEY,
>     name TEXT,
>     platform TEXT,
>     target_price FLOAT
> );
>
> CREATE TABLE pricehistory (
>     id SERIAL PRIMARY KEY,
>     product_id INT REFERENCES products(id),
>     price FLOAT,
>     check_time TIMESTAMP
> );
> ```
>
> 我的商品表和价格历史表分开设计，符合第三范式。"

---

### 4.2 索引设计

**面试官问：**"什么是索引？什么时候需要建索引？"

**标准回答**：
> "索引是数据库中加速查询的数据结构，类似于书的目录。
>
> **索引的优缺点**：
>
> | 优点 | 缺点 |
> |------|------|
> | 加速查询 | 占用存储空间 |
> | 加速排序 | 降低插入/更新/删除速度 |
>
> **什么时候建索引**：
>
> 1. **主键自动建索引** - 我的项目的 `id` 字段
> 2. **外键应该建索引** - 我的项目的 `product_id` 字段
> 3. **常用于 WHERE 条件的字段**
> 4. **常用于 ORDER BY 的字段**
> 5. **常用于 JOIN 的字段**
>
> **在我的项目中**：
>
> ```python
> # 可以添加索引的字段
> class Product(ProductBase, table=True):
>     id: Optional[int] = Field(default=None, primary_key=True)
>     name: str = Field(index=True)  # 经常按名称搜索
>     platform: str = Field(index=True)  # 经常按平台过滤
>     # ...
>
> class PriceHistory(SQLModel, table=True):
>     product_id: int = Field(foreign_key="product.id", index=True)  # 外键索引
>     check_time: datetime = Field(default_factory=datetime.now, index=True)  # 经常按时间排序
> ```
>
> **索引类型**：
> - B-Tree：默认类型，适合等值和范围查询
> - Hash：只适合等值查询
> - GIN：适合 JSONB 和数组类型
> - GiST：适合地理数据"

---

### 4.3 你的项目 ER 图

```
┌─────────────────────────────────────────────────────────────────┐
│                        ER 图                                     │
│                                                                  │
│   ┌─────────────────────┐         ┌─────────────────────────┐   │
│   │      products       │         │     pricehistory        │   │
│   ├─────────────────────┤         ├─────────────────────────┤   │
│   │ PK  id (SERIAL)     │────────<│ FK  product_id (INT)    │   │
│   │     name (TEXT)     │    1:N  │ PK  id (SERIAL)         │   │
│   │     url (TEXT)      │         │     price (FLOAT)       │   │
│   │     platform (TEXT) │         │     check_time (TIMESTAMP)│  │
│   │     target_price    │         └─────────────────────────┘   │
│   │     current_price   │                                        │
│   │     last_checked_time│                                       │
│   └─────────────────────┘                                        │
│                                                                  │
│   关系说明：                                                      │
│   - 一个 Product 可以有多个 PriceHistory (1:N)                   │
│   - 一个 PriceHistory 只属于一个 Product (N:1)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 五、数据库性能优化

### 5.1 N+1 查询问题

**面试官问：**"什么是 N+1 查询问题？如何解决？"

**标准回答**：
> "N+1 查询是一个常见的性能问题。
>
> **问题场景**：
> 假设要获取 10 个商品及其价格历史：
>
> ```python
> # 1 次查询获取商品列表
> products = await session.execute(select(Product))
>
> # N 次查询获取每个商品的历史
> for product in products:
>     # 每次访问 product.history 都会触发一次数据库查询！
>     history = product.history  # N 次查询
> ```
>
> 总共 1 + N = 11 次查询！
>
> **解决方案 - eager loading**：
>
> ```python
> from sqlalchemy.orm import selectinload
>
> # 使用 selectinload 预加载关联数据
> stmt = select(Product).options(selectinload(Product.history))
> products = await session.execute(stmt)
>
> # 现在访问 product.history 不会触发额外查询
> for product in products:
>     history = product.history  # 已加载，无额外查询
> ```
>
> 这样只需要 2 次查询：1 次获取商品，1 次获取所有历史。"

---

### 5.2 分页优化

**你的项目已实现**（`app/routers/products.py:28-40`）：
```python
@router.get("/", response_model=List[schemas.ProductRead])
async def list_products(
    skip: int = Query(0, ge=0),      # 偏移量
    limit: int = Query(100, ge=1, le=100),  # 每页数量
    session: AsyncSession = Depends(get_session)
):
    result = await session.execute(
        select(models.Product).offset(skip).limit(limit)
    )
    return result.scalars().all()
```

**分页方式对比**：

| 方式 | SQL | 优缺点 |
|------|-----|--------|
| OFFSET 分页 | `OFFSET 100 LIMIT 10` | 简单，但大偏移量性能差 |
| 游标分页 | `WHERE id > 100 LIMIT 10` | 性能好，但不支持跳页 |

**面试加分点**：
> "对于大数据量表，OFFSET 分页在翻到后面的页面时会很慢，因为数据库需要扫描并跳过前面所有的记录。更好的方式是使用游标分页（Cursor-based Pagination），用 WHERE id > last_id 来获取下一页。"

---

### 5.3 连接池

**你的项目配置**（`app/database.py`）：
```python
engine = create_async_engine(
    DATABASE_URL,
    echo=True,      # 打印 SQL 日志
    future=True,    # 使用 SQLAlchemy 2.0 风格
    pool_size=5,    # 连接池大小（可以添加）
    max_overflow=10  # 最大溢出连接数（可以添加）
)
```

**面试官问：**"为什么需要连接池？"

**标准回答**：
> "数据库连接是很昂贵的资源，每次创建连接都需要：
> 1. TCP 三次握手
> 2. 认证
> 3. 分配资源
>
> 连接池预先创建一定数量的连接，复用这些连接，避免频繁创建和销毁。
>
> 配置参数：
> - `pool_size`：连接池保持的连接数
> - `max_overflow`：超过 pool_size 后允许创建的额外连接
> - `pool_timeout`：等待可用连接的超时时间"

---

## 六、事务与并发控制

### 6.1 事务基础

**面试官问：**"什么是事务？事务的 ACID 特性是什么？"

**标准回答**：
> "事务是一组数据库操作，要么全部成功，要么全部失败。
>
> **ACID 特性**：
>
> | 特性 | 说明 | 示例 |
> |------|------|------|
> | Atomicity（原子性） | 事务不可分割，要么全做要么全不做 | 转账：A扣款 + B收款是一个整体 |
> | Consistency（一致性） | 事务前后数据库状态一致 | 转账前后总额不变 |
> | Isolation（隔离性） | 事务之间互不干扰 | A的事务没提交，B看不到 |
> | Durability（持久性） | 事务提交后永久保存 | 提交后断电也不会丢失 |
>
> **在我的项目中**：
>
> ```python
> # 每个请求自动是一个事务
> async def create_product(...):
>     session.add(db_product)
>     await session.commit()  # 提交事务
>     # 如果出错，自动回滚
> ```
>
> **手动控制事务**：
>
> ```python
> async with session.begin():  # 开始事务
>     session.add(product)
>     session.add(price_history)
>     # 成功自动提交，异常自动回滚
> ```"

---

### 6.2 并发问题与隔离级别

**面试官问：**"数据库有哪些并发问题？隔离级别是什么？"

**标准回答**：
> "**并发问题**：
>
> | 问题 | 说明 | 示例 |
> |------|------|------|
> | 脏读 | 读到未提交的数据 | A修改后未提交，B读到了 |
> | 不可重复读 | 同一事务两次读取结果不同 | A第一次读是100，B修改提交后，A第二次读是200 |
> | 幻读 | 同一条件查询结果数量不同 | A查询有5条，B插入1条后，A再查有6条 |
>
> **隔离级别**（从低到高）：
>
> | 隔离级别 | 脏读 | 不可重复读 | 幻读 |
> |----------|------|------------|------|
> | READ UNCOMMITTED | 可能 | 可能 | 可能 |
> | READ COMMITTED | 不可能 | 可能 | 可能 |
> | REPEATABLE READ | 不可能 | 不可能 | 可能 |
> | SERIALIZABLE | 不可能 | 不可能 | 不可能 |
>
> PostgreSQL 默认是 READ COMMITTED，提供了很好的平衡。"

---

## 七、面试高频问题汇总

### 7.1 基础概念题

```
Q1: 主键和唯一索引的区别？

A: 1. 主键不能为 NULL，唯一索引可以
   2. 一个表只能有一个主键，可以有多个唯一索引
   3. 主键默认是聚簇索引（某些数据库）
   4. 主键常作为外键引用

Q2: CHAR 和 VARCHAR 的区别？

A: CHAR 是定长，不足补空格
   VARCHAR 是变长，实际占用空间根据内容
   固定长度用 CHAR（如 MD5 哈希），变长用 VARCHAR

Q3: 数据库三范式是什么？

A: 1NF：字段不可再分
   2NF：非主键完全依赖主键
   3NF：非主键不传递依赖主键

   实际开发中会在范式和性能之间权衡
```

### 7.2 SQL 题目

```sql
-- Q1: 查询每个商品的最高价和最低价
SELECT
    product_id,
    MAX(price) as max_price,
    MIN(price) as min_price
FROM pricehistory
GROUP BY product_id;

-- Q2: 查询价格变化超过 50% 的商品
SELECT DISTINCT product_id
FROM pricehistory h1
JOIN pricehistory h2 ON h1.product_id = h2.product_id
WHERE ABS(h1.price - h2.price) / h1.price > 0.5;

-- Q3: 查询最近一次价格检查记录
SELECT DISTINCT ON (product_id) *
FROM pricehistory
ORDER BY product_id, check_time DESC;
```

### 7.3 ORM 相关

```
Q1: ORM 的优缺点？

A: 优点：
   - 提高开发效率，不用写 SQL
   - 类型安全，IDE 支持好
   - 数据库无关，易于迁移
   - 防 SQL 注入

   缺点：
   - 复杂查询性能不如原生 SQL
   - 学习成本
   - 可能生成低效 SQL

Q2: 什么时候用原生 SQL 而不是 ORM？

A: - 复杂的统计查询
   - 需要 UNION 的查询
   - 批量插入/更新
   - 需要使用数据库特有功能

   我的做法：90% 用 ORM，10% 复杂场景用原生 SQL
```

### 7.4 项目相关问题

```
Q1: 你的项目数据库表是如何设计的？

A: "我的价格监控系统有两个核心表：

    1. products 表：存储商品基本信息
       - id: 主键
       - name, url, platform: 商品标识
       - target_price: 用户期望价格
       - current_price: 当前价格
       - last_checked_time: 最后检查时间

    2. pricehistory 表：存储价格变化历史
       - id: 主键
       - product_id: 外键，关联商品
       - price: 检查时的价格
       - check_time: 检查时间

    这样设计符合第三范式，避免了数据冗余。
    通过外键关系可以轻松查询商品的历史价格。"

Q2: 为什么用 SQLModel 而不是纯 SQLAlchemy？

A: "SQLModel 是 SQLAlchemy 和 Pydantic 的结合：
    - 代码更简洁，一个类既是 ORM 模型也是 Pydantic 模型
    - 自动数据验证
    - 类型提示更完善
    - 与 FastAPI 完美配合

    对于新项目，SQLModel 是更好的选择。"

Q3: 如果数据量大了怎么办？

A: "1. 索引优化：给常用查询字段加索引
    2. 分表：按时间或平台分表
    3. 读写分离：主库写，从库读
    4. 缓存：热点数据放 Redis
    5. 归档：历史数据定期归档"
```

---

## 总结：面试必备知识点

### 必须掌握（⭐⭐⭐⭐⭐）

| 知识点 | 你的项目对应 |
|--------|-------------|
| SQL CRUD 语句 | `products.py` 中的 CRUD 操作 |
| JOIN 查询 | Product 和 PriceHistory 的关联 |
| 索引原理 | `id` 主键、`product_id` 外键 |
| 事务 ACID | `session.commit()` 事务提交 |
| ORM 基本操作 | SQLModel 的增删改查 |
| 模型关系定义 | `Relationship` 和 `back_populates` |

### 应该了解（⭐⭐⭐⭐）

| 知识点 | 说明 |
|--------|------|
| 范式 | 第三范式，避免数据冗余 |
| 隔离级别 | READ COMMITTED 等隔离级别 |
| 连接池 | 为什么需要，如何配置 |
| N+1 问题 | 什么是 N+1，如何解决 |

### 加分项（⭐⭐⭐）

| 知识点 | 说明 |
|--------|------|
| PostgreSQL 特性 | JSONB、数组类型 |
| 分页优化 | OFFSET vs 游标分页 |
| 慢查询优化 | EXPLAIN 分析查询 |

---

## 模拟面试问答

**面试官**："请介绍一下你项目中的数据库设计"

**你**：
> "我的价格监控系统使用 PostgreSQL 作为数据库，SQLModel 作为 ORM。
>
> 数据库设计遵循第三范式，有两个核心表：
>
> **products 表**存储商品基本信息，包括名称、URL、平台、目标价格、当前价格和最后检查时间。id 是自增主键。
>
> **pricehistory 表**存储价格变化历史，包括价格和检查时间。通过 product_id 外键关联到 products 表。
>
> 两表是一对多关系：一个商品可以有多个价格历史记录。
>
> 在代码实现上，我使用 SQLModel 定义模型，通过 Relationship 定义双向关系。这样可以通过 product.history 直接访问历史数据。
>
> API 层使用 Pydantic Schema 分离请求和响应格式，确保安全性和灵活性。"

---

**祝你面试顺利！**