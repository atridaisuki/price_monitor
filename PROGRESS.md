# 项目进度梳理

## 已完成内容

### 1. 项目基础结构

```
price_monitor/
├── .env                    # 环境变量配置（空文件，待填写）
├── Dockerfile              # Docker 镜像构建文件（空文件）
├── docker-compose.yml      # Docker Compose 编排配置
├── requirements.txt        # Python 依赖列表
└── app/                    # FastAPI 应用目录
    ├── __init__.py
    ├── main.py             # FastAPI 应用入口
    ├── database.py         # 数据库连接配置
    ├── models.py           # SQLModel 数据模型
    ├── shemas.py           # Pydantic 数据验证模型
    └── routers/
        ├── __init__.py
        └── products.py     # 商品路由（未完成）
```

---

### 2. Docker 配置 ✓

**docker-compose.yml** - 已配置三个服务：

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| web | 自定义构建 | 8000 | FastAPI 应用 |
| db | postgres:15-alpine | 5432 | PostgreSQL 数据库 |
| redis_cache | redis:alpine | 6379 | Redis 缓存 |

**环境变量**:
```
DATABASE_URL=postgresql+asyncpg://admin:mypassword@db/monitor_db
REDIS_URL=redis://redis:6379
```

**数据库配置**:
- 用户名: admin
- 密码: myypassword
- 数据库: monitor_db
- 健康检查: 已配置

---

### 3. FastAPI 框架 ✓

**app/main.py** - 应用入口:
```python
from fastapi import FastAPI
from app.database import init_db
from app import models

app = FastAPI(title="Price Monitor")

@app.on_event("startup")
async def on_startup():
    await init_db()

@app.get("/")
def read_root():
    return {"Hello":"Price Monitor is Running"}
```

**功能**:
- FastAPI 应用已初始化
- 启动时自动创建数据库表
- 根路由返回欢迎信息

---

### 4. 数据模型 ✓

**app/models.py** - SQLModel 模型定义:

#### Product (商品表)
```python
class Product(ProductBase, table=True):
    id: Optional[int]          # 主键
    name: str                  # 商品名称
    url: str                   # 商品链接
    platform: str              # 平台（默认 "steam"）
    target_price: float        # 目标价格
    current_price: Optional[float] = None    # 当前价格
    last_checked_time: Optional[datetime] = None  # 最后检查时间
    history: List["PriceHistory"]  # 价格历史关联
```

#### PriceHistory (价格历史表)
```python
class PriceHistory(SQLModel, table=True):
    id: Optional[int]          # 主键
    price: float               # 价格
    check_time: datetime       # 检查时间（自动生成）
    product_id: int            # 外键关联 product.id
    product: Optional[Product] # 关联商品
```

---

### 5. 数据库连接 ✓

**app/database.py** - 异步数据库配置:

```python
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://admin:mypassword@localhost:5432/monitor_db"
)

engine = create_async_engine(DATABASE_URL, echo=True, future=True)

async def init_db():
    # 创建所有表
    await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    # 获取数据库会话
    ...
```

**功能**:
- 使用 asyncpg 异步驱动
- SQLModel 元数据自动建表
- 依赖注入获取会话

---

### 6. Pydantic Schemas ✓

**app/shemas.py** - 数据验证模型:

```python
class ProductBaseSchema(SQLModel):
    name: str
    url: str
    platform: str = "steam"
    target_price: float

class ProductCreate(ProductBaseSchema):
    # 创建商品时使用
    pass

class ProductRead(ProductBaseSchema):
    id: int
    current_price: Optional[float] = None
    last_checked_time: Optional[datetime] = None
```

---

### 7. Python 依赖 ✓

**requirements.txt** - 已安装依赖:

| 包名 | 用途 |
|------|------|
| fastapi | Web 框架 |
| uvicorn | ASGI 服务器 |
| sqlmodel | ORM |
| psycopg2-binary | PostgreSQL 驱动（同步）|
| asyncpg | PostgreSQL 驱动（异步）|
| redis | Redis 客户端 |
| httpx | HTTP 异步客户端 |
| alembic | 数据库迁移工具 |

---

## 未完成内容

### 1. API 路由 ✗

**app/routers/products.py** - 当前为空文件

需要实现:
- POST /api/products - 创建商品
- GET /api/products - 获取商品列表
- GET /api/products/{id} - 获取单个商品
- PUT /api/products/{id} - 更新商品
- DELETE /api/products/{id} - 删除商品
- GET /api/products/{id}/history - 获取价格历史

---

### 2. 价格爬虫模块 ✗

需要实现:
- 爬取 Steam 游戏价格
- 支持其他平台（可选）
- 统一的爬取接口
- 反爬策略

---

### 3. 定时任务 ✗

需要实现:
- 定期检查所有商品价格
- 更新 current_price 和 last_checked_time
- 记录价格历史到 PriceHistory 表
- 触发价格变动通知

---

### 4. 通知系统 ✗

需要实现:
- 价格 <= target_price 时触发通知
- Redis 发布/订阅机制
- 支持绑定 QQ 号到商品

---

### 5. NoneBot2 集成 ✗

需要实现:
- NoneBot2 项目创建
- NapCat 配置
- QQ 机器人指令
- 与 FastAPI 的对接

---

### 6. Dockerfile ✗

**Dockerfile** - 当前为空文件

需要配置:
- 基础镜像（Python 3.11+）
- 工作目录
- 依赖安装
- 启动命令

---

### 7. 数据库迁移 ✗

需要配置:
- Alembic 初始化
- 迁移脚本
- 版本管理

---

### 8. 环境变量配置 ✗

**.env** - 当前为空文件

需要添加:
```
DATABASE_URL=postgresql+asyncpg://admin:mypassword@localhost:5432/monitor_db
REDIS_URL=redis://localhost:6379
```

---

## 项目评估

### 完成度: 约 40%

| 模块 | 状态 | 完成度 |
|------|------|--------|
| 项目结构 | ✓ | 100% |
| Docker 配置 | ✓ | 100% |
| FastAPI 框架 | ✓ | 100% |
| 数据模型 | ✓ | 100% |
| 数据库连接 | ✓ | 100% |
| Pydantic Schemas | ✓ | 100% |
| API 路由 | ✗ | 0% |
| 爬虫模块 | ✗ | 0% |
| 定时任务 | ✗ | 0% |
| 通知系统 | ✗ | 0% |
| NoneBot2 | ✗ | 0% |
| Dockerfile | ✗ | 0% |
| 数据库迁移 | ✗ | 0% |

---

## 下一步建议

### 优先级 P0（必须）:
1. **编写 Dockerfile** - 让项目能启动
2. **完成 CRUD API** - 实现基础的商品管理
3. **实现爬虫模块** - 能获取真实价格

### 优先级 P1（重要）:
4. **定时任务** - 自动检查价格
5. **通知系统** - 价格变动提醒

### 优先级 P2（可延后）:
6. **NoneBot2 集成** - QQ 机器人对接
7. **数据库迁移** - Alembic 配置
8. **测试和优化** - 单元测试、性能优化