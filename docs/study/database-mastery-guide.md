# 数据库深度学习指南

> 从 CRUD 到数据库专家的完整路径

## 目录
- [第一部分：SQL 进阶](#第一部分sql-进阶)
- [第二部分：数据库设计](#第二部分数据库设计)
- [第三部分：索引与性能优化](#第三部分索引与性能优化)
- [第四部分：事务与并发控制](#第四部分事务与并发控制)
- [第五部分：ORM 进阶（SQLAlchemy）](#第五部分orm-进阶sqlalchemy)
- [第六部分：数据库迁移](#第六部分数据库迁移)
- [第七部分：实战案例](#第七部分实战案例)

---

## 第一部分：SQL 进阶

### 1.1 复杂查询

#### JOIN 连接查询（重要！）

**基础概念：**
- `INNER JOIN`：只返回两表都有的数据
- `LEFT JOIN`：返回左表所有数据，右表没有则为 NULL
- `RIGHT JOIN`：返回右表所有数据，左表没有则为 NULL
- `FULL OUTER JOIN`：返回两表所有数据

**实战示例：**
```sql
-- 查询所有产品及其价格历史（即使产品没有价格记录）
SELECT
    p.name,
    p.url,
    ph.price,
    ph.created_at
FROM products p
LEFT JOIN price_history ph ON p.id = ph.product_id
ORDER BY p.id, ph.created_at DESC;

-- 查询有价格记录的产品（内连接）
SELECT
    p.name,
    COUNT(ph.id) as price_count,
    MIN(ph.price) as lowest_price,
    MAX(ph.price) as highest_price
FROM products p
INNER JOIN price_history ph ON p.id = ph.product_id
GROUP BY p.id, p.name;
```

**多表连接：**
```sql
-- 查询产品、价格历史和用户关注信息（假设有 user_watches 表）
SELECT
    p.name,
    ph.price,
    ph.created_at,
    u.username
FROM products p
INNER JOIN price_history ph ON p.id = ph.product_id
LEFT JOIN user_watches uw ON p.id = uw.product_id
LEFT JOIN users u ON uw.user_id = u.id
WHERE ph.created_at > '2024-01-01';
```

#### 子查询（Subquery）

**标量子查询：**
```sql
-- 查询价格高于平均价格的产品
SELECT name, current_price
FROM products
WHERE current_price > (
    SELECT AVG(current_price)
    FROM products
);
```

**IN 子查询：**
```sql
-- 查询最近7天有价格变动的产品
SELECT *
FROM products
WHERE id IN (
    SELECT DISTINCT product_id
    FROM price_history
    WHERE created_at > NOW() - INTERVAL '7 days'
);
```

**相关子查询：**
```sql
-- 查询每个产品的最新价格
SELECT
    p.name,
    (SELECT ph.price
     FROM price_history ph
     WHERE ph.product_id = p.id
     ORDER BY ph.created_at DESC
     LIMIT 1) as latest_price
FROM products p;
```

#### 窗口函数（Window Functions）- 面试高频！

**基础概念：**
窗口函数在不改变行数的情况下进行聚合计算。

```sql
-- 计算每个产品的价格排名
SELECT
    product_id,
    price,
    created_at,
    ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY created_at DESC) as row_num,
    RANK() OVER (PARTITION BY product_id ORDER BY price ASC) as price_rank
FROM price_history;

-- 计算价格变化趋势
SELECT
    product_id,
    price,
    created_at,
    LAG(price, 1) OVER (PARTITION BY product_id ORDER BY created_at) as prev_price,
    price - LAG(price, 1) OVER (PARTITION BY product_id ORDER BY created_at) as price_change
FROM price_history;
```

**常用窗口函数：**
- `ROW_NUMBER()`：行号
- `RANK()`：排名（有并列）
- `DENSE_RANK()`：密集排名
- `LAG()`：上一行的值
- `LEAD()`：下一行的值
- `FIRST_VALUE()`：第一个值
- `LAST_VALUE()`：最后一个值

### 1.2 聚合与分组

#### GROUP BY 深入

```sql
-- 按产品统计价格信息
SELECT
    product_id,
    COUNT(*) as record_count,
    AVG(price) as avg_price,
    MIN(price) as min_price,
    MAX(price) as max_price,
    STDDEV(price) as price_volatility
FROM price_history
GROUP BY product_id;

-- HAVING 过滤分组结果
SELECT
    product_id,
    COUNT(*) as record_count
FROM price_history
GROUP BY product_id
HAVING COUNT(*) > 10;
```

#### GROUP BY 与 WHERE 的区别

- `WHERE`：过滤行（在分组前）
- `HAVING`：过滤分组（在分组后）

```sql
-- 正确的执行顺序示例
SELECT
    product_id,
    AVG(price) as avg_price
FROM price_history
WHERE created_at > '2024-01-01'  -- 1. 先过滤行
GROUP BY product_id              -- 2. 再分组
HAVING AVG(price) > 100;         -- 3. 最后过滤分组
```

---

## 第二部分：数据库设计

### 2.1 数据库范式（Normalization）

#### 第一范式（1NF）：原子性
每个字段都是不可分割的原子值。

**错误示例：**
```sql
CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    tags VARCHAR(200)  -- 错误：存储 "游戏,动作,冒险"
);
```

**正确示例：**
```sql
CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(100)
);

CREATE TABLE product_tags (
    product_id INT,
    tag VARCHAR(50),
    PRIMARY KEY (product_id, tag),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

#### 第二范式（2NF）：消除部分依赖
非主键字段必须完全依赖于主键。

**错误示例：**
```sql
CREATE TABLE order_items (
    order_id INT,
    product_id INT,
    product_name VARCHAR(100),  -- 错误：只依赖 product_id
    quantity INT,
    PRIMARY KEY (order_id, product_id)
);
```

**正确示例：**
```sql
CREATE TABLE order_items (
    order_id INT,
    product_id INT,
    quantity INT,
    PRIMARY KEY (order_id, product_id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(100)
);
```

#### 第三范式（3NF）：消除传递依赖
非主键字段不能依赖于其他非主键字段。

**错误示例：**
```sql
CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    category_id INT,
    category_name VARCHAR(50)  -- 错误：依赖于 category_id
);
```

**正确示例：**
```sql
CREATE TABLE products (
    id INT PRIMARY KEY,
    name VARCHAR(100),
    category_id INT,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE categories (
    id INT PRIMARY KEY,
    name VARCHAR(50)
);
```

### 2.2 外键约束（Foreign Key）

**作用：**
1. 保证数据完整性
2. 防止插入无效数据
3. 级联操作

```sql
CREATE TABLE price_history (
    id SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
        ON DELETE CASCADE      -- 删除产品时，删除所有价格记录
        ON UPDATE CASCADE      -- 更新产品ID时，同步更新
);
```

**级联选项：**
- `CASCADE`：级联删除/更新
- `SET NULL`：设置为 NULL
- `SET DEFAULT`：设置为默认值
- `RESTRICT`：禁止删除/更新（默认）
- `NO ACTION`：不做任何操作

### 2.3 数据类型选择

#### 数值类型
```sql
-- 整数
SMALLINT    -- 2字节，-32768 到 32767
INT         -- 4字节，-2147483648 到 2147483647
BIGINT      -- 8字节，更大范围

-- 小数
DECIMAL(10, 2)  -- 精确小数，适合金额
FLOAT           -- 浮点数，适合科学计算
```

#### 字符串类型
```sql
CHAR(10)        -- 固定长度，不足补空格
VARCHAR(100)    -- 可变长度，最大100字符
TEXT            -- 无限长度文本
```

#### 日期时间类型
```sql
DATE            -- 日期：2024-01-01
TIME            -- 时间：12:30:00
TIMESTAMP       -- 日期时间：2024-01-01 12:30:00
TIMESTAMPTZ     -- 带时区的时间戳（推荐）
```

#### 布尔类型
```sql
BOOLEAN         -- TRUE/FALSE/NULL
```

### 2.4 约束（Constraints）

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,                    -- 主键约束
    name VARCHAR(100) NOT NULL,               -- 非空约束
    url VARCHAR(500) NOT NULL UNIQUE,         -- 唯一约束
    current_price DECIMAL(10, 2) CHECK (current_price >= 0),  -- 检查约束
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,           -- 默认值
    status VARCHAR(20) CHECK (status IN ('active', 'inactive', 'deleted'))
);
```

---

## 第三部分：索引与性能优化

### 3.1 索引基础

#### 什么是索引？
索引是数据库的"目录"，可以快速定位数据，避免全表扫描。

**类似于：**
- 书的目录：通过目录快速找到章节
- 字典的拼音索引：通过拼音快速找到汉字

#### 索引类型

**1. B-Tree 索引（默认）**
```sql
-- 创建单列索引
CREATE INDEX idx_products_name ON products(name);

-- 创建复合索引
CREATE INDEX idx_price_history_product_date
ON price_history(product_id, created_at);
```

**2. 唯一索引**
```sql
CREATE UNIQUE INDEX idx_products_url ON products(url);
```

**3. 部分索引**
```sql
-- 只索引活跃产品
CREATE INDEX idx_active_products
ON products(name)
WHERE status = 'active';
```

**4. 表达式索引**
```sql
-- 索引小写的名称
CREATE INDEX idx_products_lower_name
ON products(LOWER(name));
```

### 3.2 何时使用索引

**应该创建索引：**
- WHERE 子句中频繁查询的列
- JOIN 连接的列
- ORDER BY 排序的列
- 外键列

**不应该创建索引：**
- 小表（几百行）
- 频繁更新的列
- 低基数列（如性别：只有男/女）

### 3.3 查询优化

#### EXPLAIN 分析查询

```sql
EXPLAIN ANALYZE
SELECT * FROM products
WHERE name LIKE '%游戏%';
```

**关键指标：**
- `Seq Scan`：全表扫描（慢）
- `Index Scan`：索引扫描（快）
- `cost`：查询成本
- `rows`：扫描行数

#### 优化技巧

**1. 避免 SELECT ***
```sql
-- 慢
SELECT * FROM products;

-- 快
SELECT id, name, current_price FROM products;
```

**2. 使用 LIMIT**
```sql
SELECT * FROM products
ORDER BY created_at DESC
LIMIT 10;
```

**3. 避免在 WHERE 中使用函数**
```sql
-- 慢（无法使用索引）
SELECT * FROM products
WHERE LOWER(name) = 'steam';

-- 快（使用表达式索引）
CREATE INDEX idx_products_lower_name ON products(LOWER(name));
```

**4. 使用 EXISTS 代替 IN**
```sql
-- 慢
SELECT * FROM products
WHERE id IN (SELECT product_id FROM price_history);

-- 快
SELECT * FROM products p
WHERE EXISTS (
    SELECT 1 FROM price_history ph
    WHERE ph.product_id = p.id
);
```

---

## 第四部分：事务与并发控制

### 4.1 事务（Transaction）

#### ACID 特性

- **Atomicity（原子性）**：要么全部成功，要么全部失败
- **Consistency（一致性）**：数据保持一致状态
- **Isolation（隔离性）**：事务之间互不干扰
- **Durability（持久性）**：提交后永久保存

#### 事务操作

```sql
BEGIN;  -- 开始事务

-- 更新产品价格
UPDATE products
SET current_price = 99.99
WHERE id = 1;

-- 记录价格历史
INSERT INTO price_history (product_id, price)
VALUES (1, 99.99);

COMMIT;  -- 提交事务
-- 或
ROLLBACK;  -- 回滚事务
```

### 4.2 隔离级别

#### 并发问题

1. **脏读（Dirty Read）**：读取未提交的数据
2. **不可重复读（Non-repeatable Read）**：同一事务中两次读取结果不同
3. **幻读（Phantom Read）**：同一事务中两次查询行数不同

#### 隔离级别

```sql
-- 设置隔离级别
SET TRANSACTION ISOLATION LEVEL READ COMMITTED;
```

| 隔离级别 | 脏读 | 不可重复读 | 幻读 |
|---------|------|-----------|------|
| READ UNCOMMITTED | 可能 | 可能 | 可能 |
| READ COMMITTED | 不可能 | 可能 | 可能 |
| REPEATABLE READ | 不可能 | 不可能 | 可能 |
| SERIALIZABLE | 不可能 | 不可能 | 不可能 |

**PostgreSQL 默认：READ COMMITTED**

### 4.3 锁机制

#### 行级锁

```sql
BEGIN;

-- 排他锁（写锁）
SELECT * FROM products
WHERE id = 1
FOR UPDATE;

-- 共享锁（读锁）
SELECT * FROM products
WHERE id = 1
FOR SHARE;

COMMIT;
```

#### 死锁

**示例：**
```
事务1：锁定产品A → 等待产品B
事务2：锁定产品B → 等待产品A
结果：死锁！
```

**避免死锁：**
- 按相同顺序访问资源
- 缩短事务时间
- 使用较低的隔离级别

---

## 第五部分：ORM 进阶（SQLAlchemy）

### 5.1 关系映射

#### 一对多关系

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    current_price = Column(DECIMAL(10, 2))

    # 一对多关系
    price_history = relationship(
        "PriceHistory",
        back_populates="product",
        cascade="all, delete-orphan"  # 级联删除
    )

class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)

    # 多对一关系
    product = relationship("Product", back_populates="price_history")
```

**使用示例：**
```python
# 查询产品及其价格历史
product = db.query(Product).filter(Product.id == 1).first()
for history in product.price_history:
    print(f"价格：{history.price}，时间：{history.created_at}")
```

#### 多对多关系

```python
# 关联表
product_tags = Table(
    'product_tags',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    # 多对多关系
    tags = relationship(
        "Tag",
        secondary=product_tags,
        back_populates="products"
    )

class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String(50))

    products = relationship(
        "Product",
        secondary=product_tags,
        back_populates="tags"
    )
```

### 5.2 查询技巧

#### 预加载（Eager Loading）

**问题：N+1 查询**
```python
# 慢：每个产品都会执行一次查询
products = db.query(Product).all()
for product in products:
    print(product.price_history)  # 每次都查询数据库
```

**解决：使用 joinedload**
```python
from sqlalchemy.orm import joinedload

# 快：一次查询获取所有数据
products = db.query(Product).options(
    joinedload(Product.price_history)
).all()
```

#### 复杂查询

```python
from sqlalchemy import func, and_, or_

# 聚合查询
result = db.query(
    Product.id,
    Product.name,
    func.count(PriceHistory.id).label('price_count'),
    func.min(PriceHistory.price).label('min_price'),
    func.max(PriceHistory.price).label('max_price')
).join(PriceHistory).group_by(Product.id, Product.name).all()

# 条件查询
products = db.query(Product).filter(
    and_(
        Product.current_price > 50,
        Product.current_price < 200,
        or_(
            Product.name.like('%游戏%'),
            Product.name.like('%软件%')
        )
    )
).all()

# 子查询
subquery = db.query(
    PriceHistory.product_id,
    func.max(PriceHistory.created_at).label('latest_date')
).group_by(PriceHistory.product_id).subquery()

latest_prices = db.query(PriceHistory).join(
    subquery,
    and_(
        PriceHistory.product_id == subquery.c.product_id,
        PriceHistory.created_at == subquery.c.latest_date
    )
).all()
```

### 5.3 事务管理

```python
from sqlalchemy.exc import SQLAlchemyError

# 方式1：手动管理
try:
    product = Product(name="测试产品", url="http://example.com")
    db.add(product)
    db.flush()  # 获取 product.id

    history = PriceHistory(product_id=product.id, price=99.99)
    db.add(history)

    db.commit()
except SQLAlchemyError as e:
    db.rollback()
    raise e

# 方式2：上下文管理器
from contextlib import contextmanager

@contextmanager
def transaction(db):
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

# 使用
with transaction(db):
    product = Product(name="测试产品", url="http://example.com")
    db.add(product)
```

---

## 第六部分：数据库迁移

### 6.1 Alembic 基础

#### 初始化

```bash
# 安装
pip install alembic

# 初始化
alembic init alembic
```

#### 配置 alembic.ini

```ini
sqlalchemy.url = postgresql://user:password@localhost/dbname
```

#### 配置 env.py

```python
from app.database import Base
from app.models import Product, PriceHistory

target_metadata = Base.metadata
```

### 6.2 创建迁移

```bash
# 自动生成迁移文件
alembic revision --autogenerate -m "add products table"

# 手动创建迁移文件
alembic revision -m "add index to products"
```

#### 迁移文件示例

```python
def upgrade():
    # 创建表
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('current_price', sa.DECIMAL(10, 2)),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建索引
    op.create_index('idx_products_name', 'products', ['name'])

    # 添加列
    op.add_column('products', sa.Column('status', sa.String(20)))

def downgrade():
    # 回滚操作
    op.drop_index('idx_products_name')
    op.drop_column('products', 'status')
    op.drop_table('products')
```

### 6.3 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade ae1027a6acf

# 回滚一个版本
alembic downgrade -1

# 查看当前版本
alembic current

# 查看迁移历史
alembic history
```

---

## 第七部分：实战案例

### 7.1 价格监控系统优化

#### 问题1：查询最新价格慢

**原始查询：**
```python
# 慢：每个产品都查询一次
for product in products:
    latest_price = db.query(PriceHistory).filter(
        PriceHistory.product_id == product.id
    ).order_by(PriceHistory.created_at.desc()).first()
```

**优化方案：**
```python
# 快：使用窗口函数
from sqlalchemy import func, literal_column

subquery = db.query(
    PriceHistory.product_id,
    PriceHistory.price,
    PriceHistory.created_at,
    func.row_number().over(
        partition_by=PriceHistory.product_id,
        order_by=PriceHistory.created_at.desc()
    ).label('rn')
).subquery()

latest_prices = db.query(subquery).filter(
    subquery.c.rn == 1
).all()
```

#### 问题2：价格历史表数据量大

**解决方案：分区表**
```sql
-- 按月分区
CREATE TABLE price_history (
    id SERIAL,
    product_id INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL
) PARTITION BY RANGE (created_at);

-- 创建分区
CREATE TABLE price_history_2024_01 PARTITION OF price_history
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE price_history_2024_02 PARTITION OF price_history
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

#### 问题3：并发更新产品价格

**解决方案：乐观锁**
```python
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    current_price = Column(DECIMAL(10, 2))
    version = Column(Integer, default=0)  # 版本号

# 更新时检查版本
def update_price(db, product_id, new_price):
    product = db.query(Product).filter(
        Product.id == product_id
    ).with_for_update().first()

    old_version = product.version
    product.current_price = new_price
    product.version += 1

    # 提交时检查版本是否被修改
    result = db.query(Product).filter(
        and_(
            Product.id == product_id,
            Product.version == old_version
        )
    ).update({
        'current_price': new_price,
        'version': old_version + 1
    })

    if result == 0:
        raise Exception("产品已被其他事务修改")

    db.commit()
```

### 7.2 性能监控

#### 慢查询日志

**PostgreSQL 配置：**
```sql
-- 记录执行时间超过1秒的查询
ALTER DATABASE your_db SET log_min_duration_statement = 1000;

-- 查看慢查询
SELECT * FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

#### 连接池监控

```python
from sqlalchemy import create_engine, event
from sqlalchemy.pool import Pool

engine = create_engine(
    "postgresql://user:password@localhost/dbname",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # 检查连接是否有效
)

# 监听连接事件
@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    print(f"新连接：{dbapi_conn}")

@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    print(f"从池中获取连接：{dbapi_conn}")
```

---

## 学习路径建议

### 第一阶段：基础巩固（1-2周）
1. 熟练掌握 JOIN、子查询、聚合函数
2. 理解数据库范式，能设计简单的表结构
3. 学会使用 EXPLAIN 分析查询

### 第二阶段：进阶提升（2-3周）
1. 掌握索引原理和使用场景
2. 理解事务和隔离级别
3. 熟练使用 SQLAlchemy 的关系映射和查询

### 第三阶段：实战优化（持续）
1. 优化你的价格监控项目
2. 处理并发问题
3. 使用 Alembic 管理数据库迁移

---

## 面试高频问题

### 基础问题
1. **JOIN 的区别？**
   - INNER JOIN：只返回匹配的行
   - LEFT JOIN：返回左表所有行
   - RIGHT JOIN：返回右表所有行

2. **索引的优缺点？**
   - 优点：加快查询速度
   - 缺点：占用空间，降低写入速度

3. **事务的 ACID 特性？**
   - Atomicity：原子性
   - Consistency：一致性
   - Isolation：隔离性
   - Durability：持久性

### 进阶问题
1. **如何优化慢查询？**
   - 使用 EXPLAIN 分析
   - 添加索引
   - 避免 SELECT *
   - 使用分页

2. **什么是 N+1 查询问题？**
   - 查询主表1次，查询关联表N次
   - 解决：使用 JOIN 或预加载

3. **如何处理高并发？**
   - 使用连接池
   - 读写分离
   - 缓存（Redis）
   - 数据库分片

---

## 实践建议

1. **在你的项目中实践：**
   - 为 products 表添加复合索引
   - 使用 Alembic 管理迁移
   - 优化价格历史查询

2. **每天练习 SQL：**
   - LeetCode 数据库题目
   - HackerRank SQL 挑战

3. **阅读源码：**
   - SQLAlchemy 源码
   - PostgreSQL 文档

---

**记住：数据库是 Python Web 开发的核心，投入时间深入学习绝对值得！**
