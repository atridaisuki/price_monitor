# SQLModel + Pydantic 核心概念详解

> 本文档讲解项目中用到的 SQLModel、Pydantic、session、select、Optional 等核心概念

---

## 目录

- [一、类型提示：typing.Optional](#一类型提示typingoptional)
- [二、Pydantic：数据验证框架](#二pydantic数据验证框架)
- [三、SQLModel：ORM 框架](#三sqlmodelorm框架)
- [四、session：数据库会话](#四session数据库会话)
- [五、select：查询构造器](#五select查询构造器)
- [六、综合案例](#六综合案例)
- [七、快速参考](#七快速参考)

---

## 一、类型提示：typing.Optional

### 1. Optional 是什么？

`Optional` 是 Python 的**类型提示**（Type Hint），表示一个值**可能存在或不存在**。

```python
from typing import Optional

# 表示 name 可能是 str，也可能是 None
def greet(name: Optional[str] = None):
    if name:
        print(f"Hello, {name}!")
    else:
        print("Hello, Guest!")
```

### 2. 语法展开

```python
# 这两个写法完全等价：
name: Optional[str]
name: Union[str, None]

# Optional[str] 是 Union[str, None] 的简写
```

### 3. 在 SQLModel/Pydantic 中的使用

```python
from typing import Optional
from sqlmodel import SQLModel

class Product(SQLModel):
    id: int                    # 必须有值
    name: str                  # 必须有值
    current_price: Optional[float] = None  # 可以为 None
    last_checked_time: Optional[datetime] = None  # 可以为 None
```

### 4. 为什么需要 Optional？

| 场景 | 不用 Optional | 用 Optional |
|------|-------------|-----------|
| 数据库字段 | `price: float` → 必须有值 | `price: Optional[float] = None` → 可为空 |
| API 参数 | `search: str` → 必须传 | `search: Optional[str] = None` → 可选 |
| 函数返回 | 返回具体类型 | 返回类型或 None |

### 5. 实际例子

```python
# 在 models.py 中
class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    #                         ↑
    #              为什么 Optional？
    #              创建时由数据库生成，所以创建时是 None

    current_price: Optional[float] = None
    #                         ↑
    #              为什么 Optional？
    #              可能还没抓取过价格，所以为 None

    last_checked_time: Optional[datetime] = None
    #                         ↑
    #              为什么 Optional？
    #              可能还没检查过，所以为 None
```

---

## 二、Pydantic：数据验证框架

### 1. Pydantic 是什么？

**Pydantic** 是 Python 的数据验证和解析库，使用**类型注解**来自动验证数据。

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int

# 自动验证
user = User(name="Alice", age=25)  # ✅ 正确
user = User(name="Alice", age="25")  # ✅ 自动转换为 int
user = User(name="Alice", age="twenty")  # ❌ 报错：不是 int
```

### 2. 核心功能

#### 2.1 数据验证

```python
from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)  # 长度验证
    price: float = Field(ge=0, le=10000)  # 范围验证：0-10000

# 验证通过
product = ProductCreate(name="Game", price=99.99)  # ✅

# 验证失败
product = ProductCreate(name="", price=99.99)
# ValidationError: name 字段长度至少为 1

product = ProductCreate(name="Game", price=-10)
# ValidationError: price 必须大于等于 0
```

#### 2.2 类型转换

```python
from pydantic import BaseModel
from datetime import datetime

class Event(BaseModel):
    name: str
    date: datetime

# 自动转换字符串为 datetime
event = Event(
    name="Meeting",
    date="2026-03-04T12:00:00"  # 字符串
)

print(event.date)  # 2026-03-04 12:00:00 (datetime 对象)
```

#### 2.3 数据序列化

```python
from pydantic import BaseModel
import json

class User(BaseModel):
    name: str
    age: int

user = User(name="Alice", age=25)

# 序列化为字典
user_dict = user.dict()
# {"name": "Alice", "age": 25}

# 序列化为 JSON
user_json = user.json()
# '{"name": "Alice", "age": 25}'

# 序列化到 JSON 文件
json.dump(user_dict, open("user.json", "w"))
```

### 3. Pydantic 模型

```python
from pydantic import BaseModel
from typing import Optional

# 基本模型
class UserCreate(BaseModel):
    name: str
    email: str
    age: Optional[int] = None

# 继承和扩展
class UserRead(UserCreate):
    id: int  # 新增字段

# 响应模型
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
```

### 4. 常用配置

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        description="产品名称"
    )
    price: float = Field(
        ge=0,  # greater than or equal
        le=100000,
        description="产品价格"
    )
    description: str = Field(
        default="",  # 默认值
        description="产品描述"
    )
```

### 5. Pydantic vs SQLModel

| 特性 | Pydantic | SQLModel |
|------|----------|----------|
| 用途 | 数据验证 | ORM + 数据验证 |
| 继承 | `BaseModel` | `SQLModel` |
| 数据库操作 | ❌ | ✅ |
| API 使用 | ✅ | ✅ |
| 表结构定义 | ❌ | ✅ |

---

## 三、SQLModel：ORM 框架

### 1. SQLModel 是什么？

**SQLModel** 是一个结合了 **Pydantic**（数据验证）和 **SQLAlchemy**（ORM）的库。

```python
from sqlmodel import SQLModel, Field, create_engine, Session

# 定义模型（兼具 Pydantic 验证 + SQLAlchemy ORM）
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str

# 创建引擎
engine = create_engine("sqlite:///database.db")

# 创建表
SQLModel.metadata.create_all(engine)

# 操作数据库
with Session(engine) as session:
    user = User(name="Alice", email="alice@example.com")
    session.add(user)
    session.commit()
```

### 2. 核心概念

#### 2.1 Model（模型）

```python
from sqlmodel import SQLModel, Field

# 数据库表
class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    price: float

# Schema（API 使用）
class ProductCreate(SQLModel):
    name: str
    price: float

class ProductRead(SQLModel):
    id: int
    name: str
    price: float
```

#### 2.2 Field（字段）

```python
from sqlmodel import Field

# 定义字段属性
id: Optional[int] = Field(
    default=None,           # 默认值
    primary_key=True,       # 主键
    index=True              # 创建索引
)

name: str = Field(
    default="",             # 默认值
    min_length=1,           # 最小长度
    max_length=100          # 最大长度
)

price: float = Field(
    ge=0,                   # greater than or equal (>=)
    le=100000               # less than or equal (<=)
)
```

#### 2.3 Relationship（关系）

```python
from sqlmodel import SQLModel, Field, Relationship

class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    history: List["PriceHistory"] = Relationship(back_populates="product")

class PriceHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    price: float
    product_id: int = Field(foreign_key="product.id")
    product: Optional[Product] = Relationship(back_populates="history")
```

### 3. CRUD 操作

```python
from sqlmodel import Session, select
from typing import List

# Create（创建）
def create_product(product: Product, session: Session):
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

# Read（读取）
def get_products(session: Session) -> List[Product]:
    result = session.exec(select(Product))
    return result.all()

def get_product_by_id(id: int, session: Session) -> Product:
    result = session.exec(select(Product).where(Product.id == id))
    return result.first()

# Update（更新）
def update_product(id: int, data: dict, session: Session):
    product = session.get(Product, id)
    for key, value in data.items():
        setattr(product, key, value)
    session.commit()
    return product

# Delete（删除）
def delete_product(id: int, session: Session):
    product = session.get(Product, id)
    session.delete(product)
    session.commit()
```

---

## 四、session：数据库会话

### 1. session 是什么？

**session** 是与数据库交互的**上下文环境**，管理所有数据库操作。

```
┌─────────────────────────────────────────────────────────────────┐
│                        Session 的作用                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  应用程序                                                          │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────┐                                                │
│  │   Session   │  ←── 数据库会话，管理所有操作                     │
│  │             │  ←── 保持连接状态                               │
│  │  ┌─────────┐│  ←── 跟踪对象变化                              │
│  │  │ Cache   ││  ←── 事务管理                                  │
│  │  └─────────┘│                                              │
│  └──────┬──────┘                                                │
│         │                                                        │
│         │ SQL 命令                                               │
│         ▼                                                        │
│  ┌─────────────┐                                                │
│  │  Database   │                                                │
│  └─────────────┘                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. session 的工作原理

```python
# 获取 session
session = Session(engine)

# 1. 添加对象（还未写入数据库）
product = Product(name="Game", price=99.99)
session.add(product)
# 此时数据库还没有这个记录

# 2. 提交事务（真正写入数据库）
session.commit()
# 现在 INSERT 语句才执行

# 3. 刷新对象（获取数据库生成的值）
session.refresh(product)
# 获取数据库生成的 id
```

### 3. 异步 session（项目使用）

```python
# database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

# 创建异步引擎
engine = create_async_engine(DATABASE_URL)

# 获取 session 的依赖注入函数
async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session  # 返回 session 给路由使用
```

### 4. 在路由中使用 session

```python
from fastapi import Depends
from app.database import get_session

# 依赖注入：自动获取 session
@router.post("/")
async def create_product(
    product: ProductCreate,
    session: AsyncSession = Depends(get_session)  # ← 依赖注入
):
    db_product = Product.from_orm(product)
    session.add(db_product)
    await session.commit()  # 异步提交
    await session.refresh(db_product)  # 异步刷新
    return db_product
```

### 5. session 生命周期

```python
# 方式 1：使用 with（自动关闭）
with Session(engine) as session:
    product = Product(name="Game", price=99.99)
    session.add(product)
    session.commit()
# session 自动关闭

# 方式 2：手动管理
session = Session(engine)
try:
    product = Product(name="Game", price=99.99)
    session.add(product)
    session.commit()
finally:
    session.close()  # 必须手动关闭

# 方式 3：依赖注入（项目使用）
async def get_session() -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session
# FastAPI 自动管理生命周期
```

---

## 五、select：查询构造器

### 1. select 是什么？

**select** 是 SQLModel/SQLAlchemy 的**查询构造器**，用于构建 SQL 查询语句。

```python
from sqlmodel import select

# 构建查询：SELECT * FROM products
stmt = select(Product)

# 执行查询
result = session.exec(stmt)
products = result.all()
```

### 2. select vs SQL

```python
# SQL 写法
SELECT * FROM products
WHERE id = 1
ORDER BY name
LIMIT 10;

# SQLModel 写法
stmt = (
    select(Product)
    .where(Product.id == 1)
    .order_by(Product.name)
    .limit(10)
)
```

### 3. 常用查询操作

#### 3.1 基本查询

```python
# 查询所有产品
stmt = select(Product)
result = session.exec(stmt)
products = result.all()

# 等价 SQL
# SELECT * FROM products;
```

#### 3.2 条件查询

```python
# 查询单个产品
stmt = select(Product).where(Product.id == 1)
result = session.exec(stmt)
product = result.first()  # 获取第一个

# 等价 SQL
# SELECT * FROM products WHERE id = 1 LIMIT 1;

# 多条件查询
stmt = select(Product).where(
    Product.platform == "steam",
    Product.target_price <= 100
)
result = session.exec(stmt)
products = result.all()

# 等价 SQL
# SELECT * FROM products
# WHERE platform = 'steam' AND target_price <= 100;
```

#### 3.3 排序

```python
# 按名称升序
stmt = select(Product).order_by(Product.name)
result = session.exec(stmt)
products = result.all()

# 按价格降序
stmt = select(Product).order_by(Product.price.desc())
result = session.exec(stmt)
products = result.all()

# 等价 SQL
# SELECT * FROM products ORDER BY price DESC;
```

#### 3.4 分页

```python
# 跳过 10 条，取 20 条（第 2 页，每页 20 条）
stmt = select(Product).offset(10).limit(20)
result = session.exec(stmt)
products = result.all()

# 等价 SQL
# SELECT * FROM products OFFSET 10 LIMIT 20;
```

#### 3.5 关联查询

```python
# 查询商品及其历史记录
stmt = select(Product).options(selectinload(Product.history))
result = session.exec(stmt)
products = result.all()

for product in products:
    print(product.name)
    for history in product.history:
        print(f"  - {history.price} at {history.check_time}")

# 等价 SQL
# SELECT * FROM products;
# SELECT * FROM price_history WHERE product_id IN (...);
```

### 4. 查询结果处理

```python
# all()：获取所有结果
result = session.exec(select(Product))
products = result.all()

# first()：获取第一个结果
result = session.exec(select(Product).where(Product.id == 1))
product = result.first()

# one()：必须有且仅有一个结果，否则报错
result = session.exec(select(Product).where(Product.id == 1))
product = result.one()  # 如果不存在或有多个，抛出异常

# one_or_none()：没有结果返回 None
result = session.exec(select(Product).where(Product.id == 1))
product = result.one_or_none()  # 可能是 None

# scalars()：返回对象而不是元组
result = session.exec(select(Product))
products = result.scalars().all()
```

### 5. 异步查询（项目使用）

```python
# 异步执行查询
stmt = select(Product).where(Product.id == 1)
result = await session.execute(stmt)  # ← await 关键字
product = result.scalar_one_or_none()

# 等价同步写法
stmt = select(Product).where(Product.id == 1)
result = session.exec(stmt)  # ← 不需要 await
product = result.first()
```

---

## 六、综合案例

### 案例 1：完整的 CRUD 操作

```python
from sqlmodel import Session, select
from typing import List

# 1. Create（创建）
def create_product(product_data: dict, session: Session) -> Product:
    product = Product(**product_data)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

# 2. Read - 获取列表
def get_products(
    skip: int = 0,
    limit: int = 100,
    session: Session
) -> List[Product]:
    stmt = select(Product).offset(skip).limit(limit)
    result = session.exec(stmt)
    return result.all()

# 3. Read - 获取单个
def get_product(id: int, session: Session) -> Optional[Product]:
    stmt = select(Product).where(Product.id == id)
    result = session.exec(stmt)
    return result.one_or_none()

# 4. Update（更新）
def update_product(
    id: int,
    update_data: dict,
    session: Session
) -> Optional[Product]:
    product = get_product(id, session)
    if not product:
        return None

    for field, value in update_data.items():
        setattr(product, field, value)

    session.commit()
    session.refresh(product)
    return product

# 5. Delete（删除）
def delete_product(id: int, session: Session) -> bool:
    product = get_product(id, session)
    if not product:
        return False

    session.delete(product)
    session.commit()
    return True
```

### 案例 2：复杂查询

```python
# 查询价格在范围内的商品
def search_products_by_price(
    min_price: float,
    max_price: float,
    session: Session
) -> List[Product]:
    stmt = select(Product).where(
        Product.current_price >= min_price,
        Product.current_price <= max_price
    ).order_by(Product.current_price)
    result = session.exec(stmt)
    return result.all()

# 查询最近检查过的商品
def get_recently_checked_products(
    days: int,
    session: Session
) -> List[Product]:
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=days)

    stmt = select(Product).where(
        Product.last_checked_time >= cutoff_date
    ).order_by(Product.last_checked_time.desc())
    result = session.exec(stmt)
    return result.all()

# 统计各平台商品数量
def count_products_by_platform(session: Session) -> dict:
    from sqlalchemy import func

    stmt = select(
        Product.platform,
        func.count(Product.id)
    ).group_by(Product.platform)
    result = session.exec(stmt)

    return {row[0]: row[1] for row in result}
```

---

## 七、快速参考

### 常用类型提示

```python
from typing import Optional, List, Dict, Union

# 可选值
value: Optional[str] = None

# 列表
items: List[str] = ["a", "b", "c"]

# 字典
data: Dict[str, int] = {"key": 1}

# 联合类型
result: Union[int, str] = "hello"  # 可以是 int 或 str

# 任意类型
value: Any = None
```

### Pydantic 常用字段验证

```python
from pydantic import Field

# 字符串
name: str = Field(min_length=1, max_length=100)

# 数字
age: int = Field(ge=0, le=150)  # 0-150
price: float = Field(gt=0, le=100000)  # >0, <=100000

# 必填
required: str = Field(...)

# 默认值
optional: str = Field(default="default")

# 描述
name: str = Field(description="用户名称")
```

### SQLModel 常用查询

```python
from sqlmodel import select

# 基本
select(Model)

# 条件
select(Model).where(Model.field == value)

# 多条件
select(Model).where(
    Model.field1 == value1,
    Model.field2 >= value2
)

# 排序
select(Model).order_by(Model.field.desc())

# 分页
select(Model).offset(0).limit(10)

# 关联
select(Model).options(selectinload(Model.relation))
```

### Session 常用操作

```python
# 添加
session.add(obj)
session.add_all([obj1, obj2])

# 提交
session.commit()

# 刷新（获取最新数据）
session.refresh(obj)

# 删除
session.delete(obj)

# 关闭
session.close()

# 获取单个
session.get(Model, id)

# 获取关系
session.exec(select(Model).where(Model.id == id)).scalars().first()
```

---

## 总结

| 概念 | 用途 | 项目中的应用 |
|------|------|------------|
| `Optional[T]` | 表示可空类型 | `id: Optional[int]` |
| `Field()` | 定义字段属性 | `id = Field(default=None, primary_key=True)` |
| `SQLModel` | ORM + 验证 | `class Product(SQLModel, table=True)` |
| `Session` | 数据库会话管理 | `session = Depends(get_session)` |
| `select()` | 构建查询 | `select(Product).where(Product.id == 1)` |
| `from_orm()` | Schema 转 Model | `db_product = Product.from_orm(schema)` |

---

## 进一步学习

- [SQLModel 官方文档](https://sqlmodel.tiangolo.com/)
- [Pydantic 官方文档](https://docs.pydantic.dev/)
- [SQLAlchemy 官方文档](https://docs.sqlalchemy.org/)