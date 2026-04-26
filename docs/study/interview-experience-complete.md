# 全面面试经验整理

> 涵盖技术面试、项目经验、算法题、行为面试的完整指南

## 目录

- [第一部分：面试流程与准备](#第一部分面试流程与准备)
- [第二部分：Python技术面试](#第二部分python技术面试)
- [第三部分：数据库面试题](#第三部分数据库面试题)
- [第四部分：Web开发面试](#第四部分web开发面试)
- [第五部分：数据分析面试](#第五部分数据分析面试)
- [第六部分：算法面试](#第六部分算法面试)
- [第七部分：项目经验讲解](#第七部分项目经验讲解)
- [第八部分：行为面试](#第八部分行为面试)
- [第九部分：系统设计](#第九部分系统设计)
- [第十部分：面试技巧](#第十部分面试技巧)

---

## 第一部分：面试流程与准备

### 1.1 典型面试流程

**互联网公司：**
1. 简历筛选（1-3天）
2. 电话/视频初筛（30分钟）
3. 技术一面（1-1.5小时）
4. 技术二面（1-1.5小时）
5. HR面试（30分钟-1小时）
6. Offer发放

**数据分析岗位：**
1. 简历筛选
2. 笔试（SQL + Python + 统计）
3. 技术面试（业务理解 + 技术能力）
4. 业务面试（部门负责人）
5. HR面试

### 1.2 面试前准备清单

**技术准备：**
- [ ] 复习项目代码，能流畅讲解
- [ ] 刷50-100道LeetCode题（Medium为主）
- [ ] 复习数据库、网络、操作系统基础
- [ ] 准备3-5个技术难点的解决方案

**简历准备：**
- [ ] 项目经验用STAR法则描述
- [ ] 量化成果（提升XX%，优化XX倍）
- [ ] 技术栈与岗位JD匹配度>70%
- [ ] 准备简历中每个项目的详细讲解

**心态准备：**
- [ ] 准备自我介绍（1分钟、3分钟版本）
- [ ] 准备3个问题问面试官
- [ ] 模拟面试练习
- [ ] 准备失败案例和反思

---

## 第二部分：Python技术面试

### 2.1 Python基础（必考）

#### Q1: Python的可变类型和不可变类型？

**答案：**
- 不可变类型：int、float、str、tuple、frozenset
- 可变类型：list、dict、set

**追问：为什么要区分？**
- 不可变类型可以作为字典的key
- 不可变类型线程安全
- 函数参数传递时的行为不同

```python
# 示例
def modify_list(lst):
    lst.append(4)  # 会修改原列表

def modify_int(num):
    num += 1  # 不会修改原变量

my_list = [1, 2, 3]
modify_list(my_list)
print(my_list)  # [1, 2, 3, 4]

my_num = 10
modify_int(my_num)
print(my_num)  # 10
```

#### Q2: 深拷贝和浅拷贝的区别？

**答案：**
```python
import copy

# 浅拷贝：只复制第一层
original = [[1, 2], [3, 4]]
shallow = copy.copy(original)
shallow[0][0] = 999
print(original)  # [[999, 2], [3, 4]]  # 原数据被修改！

# 深拷贝：递归复制所有层
original = [[1, 2], [3, 4]]
deep = copy.deepcopy(original)
deep[0][0] = 999
print(original)  # [[1, 2], [3, 4]]  # 原数据不变
```

#### Q3: 装饰器的原理和应用？

**答案：**
```python
# 基础装饰器
def timer(func):
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} 耗时: {end - start:.2f}秒")
        return result
    return wrapper

@timer
def slow_function():
    import time
    time.sleep(1)

# 带参数的装饰器
def repeat(times):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(times):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def say_hello():
    print("Hello!")
```

**应用场景：**
- 日志记录
- 性能监控
- 权限验证
- 缓存
- 重试机制

#### Q4: 生成器和迭代器的区别？

**答案：**
```python
# 迭代器
class MyIterator:
    def __init__(self, n):
        self.n = n
        self.current = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.current < self.n:
            self.current += 1
            return self.current
        raise StopIteration

# 生成器（更简洁）
def my_generator(n):
    for i in range(1, n + 1):
        yield i

# 生成器表达式
gen = (x * x for x in range(10))
```

**区别：**
- 生成器是特殊的迭代器
- 生成器使用yield，更简洁
- 生成器自动实现__iter__和__next__

#### Q5: GIL（全局解释器锁）是什么？

**答案：**
- GIL是Python解释器的互斥锁，同一时刻只有一个线程执行Python字节码
- 影响：多线程无法利用多核CPU进行CPU密集型任务
- 解决方案：
  - 使用多进程（multiprocessing）
  - 使用C扩展
  - 使用异步IO（asyncio）

```python
# 多线程适合IO密集型
import threading
import requests

def download(url):
    response = requests.get(url)
    return response.content

# 多进程适合CPU密集型
import multiprocessing

def calculate(n):
    return sum(i * i for i in range(n))

with multiprocessing.Pool(4) as pool:
    results = pool.map(calculate, [1000000] * 4)
```

### 2.2 Python进阶

#### Q6: *args和**kwargs的作用？

**答案：**
```python
def func(*args, **kwargs):
    print(f"位置参数: {args}")
    print(f"关键字参数: {kwargs}")

func(1, 2, 3, name="Alice", age=25)
# 位置参数: (1, 2, 3)
# 关键字参数: {'name': 'Alice', 'age': 25}

# 解包
numbers = [1, 2, 3]
print(*numbers)  # 1 2 3

data = {'name': 'Bob', 'age': 30}
func(**data)
```

#### Q7: 列表推导式和生成器表达式的区别？

**答案：**
```python
# 列表推导式：立即生成所有元素，占用内存
list_comp = [x * x for x in range(1000000)]

# 生成器表达式：惰性求值，节省内存
gen_exp = (x * x for x in range(1000000))

# 使用场景
# 需要多次遍历 → 列表推导式
# 只遍历一次 → 生成器表达式
```

#### Q8: 上下文管理器（with语句）的原理？

**答案：**
```python
# 自定义上下文管理器
class DatabaseConnection:
    def __enter__(self):
        print("打开数据库连接")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("关闭数据库连接")
        if exc_type:
            print(f"发生异常: {exc_val}")
        return False  # 不抑制异常

with DatabaseConnection() as db:
    print("执行数据库操作")

# 使用contextlib简化
from contextlib import contextmanager

@contextmanager
def file_manager(filename):
    f = open(filename, 'w')
    try:
        yield f
    finally:
        f.close()

with file_manager('test.txt') as f:
    f.write('Hello')
```

---

## 第三部分：数据库面试题

### 3.1 SQL基础（必考）

#### Q1: JOIN的区别？

**答案：**
```sql
-- INNER JOIN：只返回匹配的行
SELECT * FROM products p
INNER JOIN price_history ph ON p.id = ph.product_id;

-- LEFT JOIN：返回左表所有行，右表没有则NULL
SELECT * FROM products p
LEFT JOIN price_history ph ON p.id = ph.product_id;

-- RIGHT JOIN：返回右表所有行
SELECT * FROM products p
RIGHT JOIN price_history ph ON p.id = ph.product_id;

-- FULL OUTER JOIN：返回两表所有行
SELECT * FROM products p
FULL OUTER JOIN price_history ph ON p.id = ph.product_id;
```

#### Q2: GROUP BY和HAVING的区别？

**答案：**
- WHERE：过滤行（分组前）
- HAVING：过滤分组（分组后）

```sql
SELECT
    product_id,
    COUNT(*) as count,
    AVG(price) as avg_price
FROM price_history
WHERE created_at > '2024-01-01'  -- 先过滤行
GROUP BY product_id              -- 再分组
HAVING COUNT(*) > 10;            -- 最后过滤分组
```

#### Q3: 索引的优缺点？

**答案：**

**优点：**
- 加快查询速度（特别是WHERE、JOIN、ORDER BY）
- 唯一索引保证数据唯一性

**缺点：**
- 占用额外存储空间
- 降低INSERT、UPDATE、DELETE速度
- 需要维护成本

**何时使用索引：**

- WHERE子句中频繁查询的列
- JOIN连接的列
- ORDER BY排序的列
- 外键列

**何时不用索引：**
- 小表（几百行）
- 频繁更新的列
- 低基数列（如性别）

```sql
-- 创建索引
CREATE INDEX idx_products_name ON products(name);

-- 复合索引
CREATE INDEX idx_price_product_date
ON price_history(product_id, created_at);

-- 查看索引使用情况
EXPLAIN ANALYZE
SELECT * FROM products WHERE name = 'Steam游戏';
```

#### Q4: 事务的ACID特性？

**答案：**

- **Atomicity（原子性）**：要么全部成功，要么全部失败
- **Consistency（一致性）**：数据保持一致状态
- **Isolation（隔离性）**：事务之间互不干扰
- **Durability（持久性）**：提交后永久保存

```sql
BEGIN;

UPDATE products SET current_price = 99.99 WHERE id = 1;
INSERT INTO price_history (product_id, price) VALUES (1, 99.99);

COMMIT;  -- 提交
-- 或
ROLLBACK;  -- 回滚
```

#### Q5: 隔离级别有哪些？

**答案：**

| 隔离级别 | 脏读 | 不可重复读 | 幻读 |
|---------|------|-----------|------|
| READ UNCOMMITTED读未提交 | 可能 | 可能 | 可能 |
| READ COMMITTED读已提交 | 不可能 | 可能 | 可能 |
| REPEATABLE READ可重复读 | 不可能 | 不可能 | 可能 |
| SERIALIZABLE串行化 | 不可能 | 不可能 | 不可能 |

**PostgreSQL默认：READ COMMITTED**

### 3.2 SQL进阶

#### Q6: 如何查询每个分组的前N条记录？

**答案：使用窗口函数**
```sql
-- 查询每个产品的最新3条价格记录
SELECT *
FROM (
    SELECT
        product_id,
        price,
        created_at,
        ROW_NUMBER() OVER (
            PARTITION BY product_id
            ORDER BY created_at DESC
        ) as rn
    FROM price_history
) t
WHERE rn <= 3;
```

#### Q7: 如何优化慢查询？

**答案：**

1. **使用EXPLAIN分析**
```sql
EXPLAIN ANALYZE
SELECT * FROM products WHERE name LIKE '%游戏%';
```

2. **添加索引**
```sql
CREATE INDEX idx_products_name ON products(name);
```

3. **避免SELECT ***
```sql
-- 慢
SELECT * FROM products;

-- 快
SELECT id, name, current_price FROM products;
```

4. **使用LIMIT**
```sql
SELECT * FROM products
ORDER BY created_at DESC
LIMIT 10;
```

5. **避免在WHERE中使用函数**
```sql
-- 慢（无法使用索引）
SELECT * FROM products WHERE LOWER(name) = 'steam';

-- 快（使用表达式索引）
CREATE INDEX idx_products_lower_name ON products(LOWER(name));
```

---

## 第四部分：Web开发面试

### 4.1 FastAPI/Django

#### Q1: FastAPI的优势？

**答案：**
- 基于Python类型提示，自动生成API文档
- 异步支持，性能优秀
- 自动数据验证（Pydantic）
- 易于测试

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class Product(BaseModel):
    name: str
    price: float

@app.post("/products/")
async def create_product(product: Product):
    # 自动验证数据类型
    return {"id": 1, **product.dict()}
```

#### Q2: 什么是依赖注入？

**答案：**
```python
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/products/")
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()
```

#### Q3: 如何处理跨域（CORS）？

**答案：**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4.2 RESTful API设计

#### Q4: RESTful API的设计原则？

**答案：**

**资源命名：**
- 使用名词，不用动词
- 使用复数形式
- 使用小写字母，用连字符分隔

```
GET    /products          # 获取所有产品
GET    /products/1        # 获取单个产品
POST   /products          # 创建产品
PUT    /products/1        # 更新产品
DELETE /products/1        # 删除产品
```

**HTTP状态码：**
- 200 OK：成功
- 201 Created：创建成功
- 400 Bad Request：请求错误
- 401 Unauthorized：未授权
- 404 Not Found：资源不存在
- 500 Internal Server Error：服务器错误

#### Q5: 如何设计API版本控制？

**答案：**

**方式1：URL路径**
```
/api/v1/products
/api/v2/products
```

**方式2：请求头**
```
Accept: application/vnd.myapi.v1+json
```

**方式3：查询参数**
```
/api/products?version=1
```

---

## 第五部分：数据分析面试

### 5.1 Pandas（必考）

#### Q1: Pandas的核心数据结构？

**答案：**
- Series：一维数组
- DataFrame：二维表格

```python
import pandas as pd

# Series
s = pd.Series([1, 2, 3], index=['a', 'b', 'c'])

# DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'salary': [50000, 60000, 70000]
})
```

#### Q2: 如何处理缺失值？

**答案：**
```python
# 检查缺失值
df.isnull().sum()

# 删除缺失值
df.dropna()  # 删除包含缺失值的行
df.dropna(axis=1)  # 删除包含缺失值的列

# 填充缺失值
df.fillna(0)  # 填充为0
df.fillna(df.mean())  # 填充为平均值
df.fillna(method='ffill')  # 前向填充
df.fillna(method='bfill')  # 后向填充
```

#### Q3: 如何进行数据分组聚合？

**答案：**
```python
# 按部门分组，计算平均工资
df.groupby('department')['salary'].mean()

# 多列分组
df.groupby(['department', 'gender'])['salary'].agg(['mean', 'min', 'max'])

# 自定义聚合函数
df.groupby('department').agg({
    'salary': ['mean', 'sum'],
    'age': 'max'
})
```

#### Q4: 如何合并数据？

**答案：**
```python
# merge（类似SQL JOIN）
pd.merge(df1, df2, on='id', how='left')

# concat（拼接）
pd.concat([df1, df2], axis=0)  # 垂直拼接
pd.concat([df1, df2], axis=1)  # 水平拼接

# join（基于索引）
df1.join(df2, how='inner')
```

### 5.2 数据分析实战

#### Q5: 如何分析价格趋势？

**答案：**
```python
import pandas as pd
import matplotlib.pyplot as plt

# 读取数据
df = pd.read_sql("SELECT * FROM price_history", conn)

# 转换日期
df['created_at'] = pd.to_datetime(df['created_at'])

# 按日期分组，计算平均价格
daily_avg = df.groupby(df['created_at'].dt.date)['price'].mean()

# 可视化
daily_avg.plot(figsize=(12, 6))
plt.title('价格趋势')
plt.xlabel('日期')
plt.ylabel('平均价格')
plt.show()

# 计算价格变化率
df['price_change'] = df.groupby('product_id')['price'].pct_change()

# 识别异常值
Q1 = df['price'].quantile(0.25)
Q3 = df['price'].quantile(0.75)
IQR = Q3 - Q1
outliers = df[(df['price'] < Q1 - 1.5 * IQR) | (df['price'] > Q3 + 1.5 * IQR)]
```

---

## 第六部分：算法面试

### 6.1 高频算法题

#### Q1: 两数之和（LeetCode 1）

**题目：**给定一个整数数组和目标值，找出数组中和为目标值的两个数的索引。

**答案：**
```python
def two_sum(nums, target):
    # 哈希表
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []

# 时间复杂度：O(n)
# 空间复杂度：O(n)
```

#### Q2: 反转链表（LeetCode 206）

**答案：**
```python
class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def reverse_list(head):
    prev = None
    current = head

    while current:
        next_node = current.next
        current.next = prev
        prev = current
        current = next_node

    return prev

# 时间复杂度：O(n)
# 空间复杂度：O(1)
```

#### Q3: 有效的括号（LeetCode 20）

**答案：**
```python
def is_valid(s):
    stack = []
    mapping = {')': '(', '}': '{', ']': '['}

    for char in s:
        if char in mapping:
            top = stack.pop() if stack else '#'
            if mapping[char] != top:
                return False
        else:
            stack.append(char)

    return not stack

# 时间复杂度：O(n)
# 空间复杂度：O(n)
```

#### Q4: 最大子数组和（LeetCode 53）

**答案：**
```python
def max_subarray(nums):
    # 动态规划（Kadane算法）
    max_sum = current_sum = nums[0]

    for num in nums[1:]:
        current_sum = max(num, current_sum + num)
        max_sum = max(max_sum, current_sum)

    return max_sum

# 时间复杂度：O(n)
# 空间复杂度：O(1)
```

### 6.2 数据结构

#### Q5: 实现LRU缓存（LeetCode 146）

**答案：**
```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
```

---

## 第七部分：项目经验讲解

### 7.1 STAR法则

**Situation（情境）**：项目背景
**Task（任务）**：你的职责
**Action（行动）**：你的具体行动
**Result（结果）**：量化成果

### 7.2 价格监控项目示例

**面试官：介绍一下你的价格监控项目。**

**回答示例：**

"我开发了一个Steam游戏价格监控系统，主要解决用户无法及时获知游戏降价信息的问题。

**技术栈：**
- 后端：Python + FastAPI
- 数据库：PostgreSQL
- 爬虫：aiohttp + BeautifulSoup
- 部署：Docker + docker-compose

**核心功能：**
1. 异步爬虫定时抓取Steam游戏价格
2. RESTful API提供CRUD操作
3. 价格历史记录和趋势分析

**技术亮点：**
1. 使用异步爬虫，并发处理100+产品，性能提升5倍
2. 设计了合理的数据库索引，查询速度提升3倍
3. 使用Docker容器化部署，一键启动

**遇到的挑战：**
- 问题：Steam有反爬虫机制
- 解决：添加随机延迟、User-Agent轮换、代理池

**成果：**
- 支持监控200+游戏
- 每日自动更新价格
- API响应时间<100ms"

### 7.3 常见追问

#### Q1: 如何处理高并发？

**答案：**
- 使用异步IO（asyncio）
- 数据库连接池
- Redis缓存热点数据
- 负载均衡

#### Q2: 如何保证数据一致性？

**答案：**
- 使用数据库事务
- 乐观锁/悲观锁
- 分布式锁（Redis）

#### Q3: 如何监控系统运行状态？

**答案：**
- 日志记录（logging）
- 性能监控（Prometheus）
- 错误追踪（Sentry）
- 健康检查接口

---

## 第八部分：行为面试

### 8.1 常见问题

#### Q1: 自我介绍

**模板：**
"您好，我是XXX，有X年Python开发经验。

我最近的项目是价格监控系统，使用FastAPI和PostgreSQL，实现了游戏价格的自动抓取和分析。在这个项目中，我负责后端API开发和数据库设计，通过异步爬虫和索引优化，将系统性能提升了5倍。

我熟悉Python Web开发、数据库优化和Docker部署，也有数据分析经验，熟练使用Pandas和SQL进行数据处理。

我对贵公司的XXX业务很感兴趣，希望能加入团队，贡献我的技术能力。"

#### Q2: 为什么离职/换工作？

**正面回答：**
- 寻求更大的技术挑战
- 希望在XX领域深入发展
- 公司业务调整，岗位不匹配

**避免：**
- 抱怨前公司
- 说工资低
- 说人际关系差

#### Q3: 你的优缺点？

**优点（结合岗位）：**
- 学习能力强：快速掌握新技术
- 责任心强：项目按时交付
- 注重代码质量：编写可维护的代码

**缺点（可改进）：**
- 有时过于追求完美，需要平衡时间
- 公开演讲经验不足，正在练习
- 某个技术栈经验较少，正在学习

#### Q4: 遇到过最大的挑战？

**STAR法则回答：**
"在价格监控项目中，我遇到了Steam的反爬虫机制。

最初爬虫频繁被封IP，导致数据采集失败。我分析了Steam的反爬策略，发现主要是请求频率和User-Agent检测。

我采取了三个措施：
1. 添加随机延迟（1-3秒）
2. 轮换User-Agent
3. 使用代理IP池

最终爬虫稳定运行，成功率从30%提升到95%。"

### 8.2 反问环节

**好问题：**
- 团队的技术栈和开发流程？
- 这个岗位的主要职责和挑战？
- 团队的规模和协作方式？
- 公司对技术人员的培养计划？

**避免问：**
- 工资、加班（HR面再问）
- 公司负面新闻
- 太基础的问题（官网能查到）

---

## 第九部分：系统设计

### 9.1 设计一个短链接系统

**需求分析：**
- 将长URL转换为短URL
- 访问短URL时重定向到长URL
- 高并发读取
- URL唯一性

**设计方案：**

**1. 数据库设计**
```sql
CREATE TABLE urls (
    id BIGSERIAL PRIMARY KEY,
    short_code VARCHAR(10) UNIQUE NOT NULL,
    long_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    visit_count INT DEFAULT 0
);

CREATE INDEX idx_short_code ON urls(short_code);
```

**2. 短码生成算法**
```python
import hashlib
import base62

def generate_short_code(long_url, length=6):
    # 方式1：哈希 + Base62
    hash_value = hashlib.md5(long_url.encode()).hexdigest()
    return base62.encode(int(hash_value[:16], 16))[:length]

    # 方式2：自增ID + Base62
    # id = get_next_id()
    # return base62.encode(id)
```

**3. API设计**
```python
@app.post("/shorten")
async def shorten_url(long_url: str):
    short_code = generate_short_code(long_url)
    # 保存到数据库
    return {"short_url": f"http://short.url/{short_code}"}

@app.get("/{short_code}")
async def redirect(short_code: str):
    long_url = get_long_url(short_code)  # 从数据库或缓存获取
    return RedirectResponse(url=long_url)
```

**4. 优化方案**
- Redis缓存热点短链接
- 布隆过滤器判断短码是否存在
- 数据库分片（按短码哈希）
- CDN加速

---

## 第十部分：面试技巧

### 10.1 技术面试技巧

**1. 听清问题**
- 不确定时，重复问题确认
- 询问边界条件和约束

**2. 思考后再回答**
- 不要急于写代码
- 先说思路，再实现

**3. 边写边讲**
- 解释你的思路
- 让面试官跟上你的节奏

**4. 测试你的代码**
- 考虑边界情况
- 举例验证

**5. 分析复杂度**
- 时间复杂度
- 空间复杂度

### 10.2 常见错误

**避免：**
- 不懂装懂
- 沉默不语
- 过度紧张
- 批评前公司
- 问薪资福利（技术面）

### 10.3 面试后跟进

**当天：**
- 发感谢邮件
- 总结面试问题

**一周内：**
- 礼貌询问进度
- 补充遗漏的信息

---

## 学习资源

### 在线刷题
- [LeetCode](https://leetcode.com/)
- [牛客网](https://www.nowcoder.com/)
- [HackerRank](https://www.hackerrank.com/)

### 技术博客
- [SQL面试题精解](https://blog.csdn.net/weixin_38892128/article/details/103391898)
- [算法面试题总结](https://www.cnblogs.com/NaughtyCoder/p/13511123.html)
- [面试常问SQL查询](https://www.cnblogs.com/hd-test/p/18113221)

### 书籍推荐
- 《剑指Offer》
- 《Python Cookbook》
- 《高性能MySQL》

---

## 总结

**面试准备优先级：**

1. **基础知识（40%）**
   - Python基础
   - 数据库SQL
   - 数据结构与算法

2. **项目经验（30%）**
   - 能流畅讲解
   - 准备技术难点
   - 量化成果

3. **算法题（20%）**
   - LeetCode Medium 50题
   - 高频题必刷

4. **行为面试（10%）**
   - 自我介绍
   - STAR法则
   - 反问问题

**最后建议：**
- 每天刷2-3道算法题
- 复习项目代码
- 模拟面试练习
- 保持自信，诚实回答

祝你面试成功！🎉
