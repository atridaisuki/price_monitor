# Price Monitor

Steam 游戏价格监控系统。自动抓取商品价格，低于目标价时通过 Redis 推送通知，支持 QQ 机器人提醒。

Built with FastAPI, PostgreSQL, Redis, APScheduler, NoneBot2.

## 核心链路

`创建商品 → 定时/手动触发价格检查 → 抓取价格 → 更新历史 → Redis Pub/Sub 通知 → QQ Bot 推送`

## 项目结构

```text
app/
  main.py                 FastAPI 入口
  database.py             数据库连接与会话
  notifications.py        Redis 通知发布/订阅
  subscriber.py           最小可用通知消费者
  routers/
    products.py           商品 CRUD 与历史接口
    tasks.py              手动价格检查与测试通知接口
  tasks/
    price_checker.py      价格检查主链路
    scheduler.py          定时调度入口
bot/
  bot.py                  NoneBot2 入口
  src/plugins/            QQ 机器人插件
napcat/                   NapCat 配置目录
tests/                    最小自动化测试
docs/project/implementation-progress.md  分阶段实施记录
```

## 文档导航

- [总索引](docs/INDEX.md)
- [快速开始](docs/getting-started/INDEX.md)
- [架构说明](docs/architecture/INDEX.md)
- [部署与集成](docs/deployment/INDEX.md)
- [项目进展](docs/project/INDEX.md)
- [学习/面试资料](docs/study/INDEX.md)
- [数据文件](docs/data/INDEX.md)

## 环境准备

- Python 3.10+
- PostgreSQL
- Redis
- 可选：Docker / Docker Compose

## 配置

### 1. 后端配置

复制根目录配置样例：

```bash
cp .env.example .env
```

关键变量：

- `DATABASE_URL`: 异步 PostgreSQL 连接串
- `REDIS_URL`: Redis 连接串

默认本地样例：

- PostgreSQL: `postgresql+asyncpg://admin:mypassword@localhost:5432/monitor_db`
- Redis: `redis://localhost:6379`

### 2. Bot 配置

如需启用 bot，复制 bot 配置样例：

```bash
cp bot/.env.example bot/.env
```

至少需要按实际情况修改：

- `SUPERUSERS`
- `ONEBOT_WS_URLS`
- `REDIS_URL`
- `API_BASE_URL`

现在 bot 会优先把价格提醒发送给商品绑定的 `user_qq`；`SUPERUSERS` 主要作为未绑定商品和手工测试通知的 fallback。

## 本地启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

如需运行 bot：

```bash
pip install -r bot/requirements.txt
```

### 2. 启动后端依赖

先确保 PostgreSQL 和 Redis 已启动。

### 3. 启动 FastAPI

```bash
uvicorn app.main:app --reload
```

启动后可访问：

- API 文档: `http://localhost:8000/docs`
- 根路径: `http://localhost:8000/`

### 4. 启动 subscriber

```bash
python -m app.subscriber
```

它会订阅 Redis `price_alerts` 频道并打印消费结果。

### 5. 启动 bot（可选）

```bash
python bot/bot.py
```

## Docker Compose 启动

项目提供了 `docker-compose.yml`，包含以下服务：

- `web`
- `db`
- `redis`
- `bot`
- `napcat`

启动命令：

```bash
docker compose up -d db redis web
```

如需同时拉起 bot / napcat：

```bash
docker compose up -d
```

当前已确认 Compose 配置可解析，但本机最近一次真实联调被 Docker daemon 不可用阻塞；如果你也遇到类似错误，先确认 Docker Desktop 已启动。

## 最小验证流程

### 1. 创建商品

请求：

```bash
curl -X POST "http://localhost:8000/api/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Game",
    "url": "https://store.steampowered.com/app/1",
    "platform": "steam",
    "target_price": 50,
    "user_qq": "123456"
  }'
```

说明：`user_qq` 为可选字段。通过 bot `/添加商品` 创建时，会自动写入发起命令的 QQ 号。

### 2. 手动触发价格检查

```bash
curl -X POST "http://localhost:8000/api/tasks/check-prices"
```

当前接口会直接执行并返回 summary，字段包括：

- `total_products`
- `success_count`
- `failure_count`
- `history_count`
- `notification_count`
- `results`

### 3. 查看商品与历史

```bash
curl "http://localhost:8000/api/products/"
curl "http://localhost:8000/api/products/1/history"
```

也可以通过更新接口补录或修改绑定 QQ：

```bash
curl -X PUT "http://localhost:8000/api/products/1" \
  -H "Content-Type: application/json" \
  -d '{
    "user_qq": "654321"
  }'
```

### 4. 发送测试通知

```bash
curl -X POST "http://localhost:8000/api/tasks/test-notification"
```

## 自动化测试

运行最小测试集合：

```bash
python -m unittest discover -s tests -p "test_*.py"
```

当前测试覆盖：

- `tests/test_price_checker.py`: 价格检查主链路关键分支
- `tests/test_notifications.py`: 通知消息结构与订阅回调
- `tests/test_task_routes.py`: 任务路由返回与测试通知触发
- `tests/test_product_routes.py`: 商品创建/更新对 `user_qq` 的持久化
- `tests/test_bot_price_alert.py`: bot 定向发送与 `SUPERUSERS` fallback

## 数据库迁移（Alembic）

项目已补入 Alembic 基础目录与首个迁移版本，用于替代正式环境长期依赖 `create_all` 的方式。

### 常用命令

执行迁移：

```bash
alembic upgrade head
```

回滚一步：

```bash
alembic downgrade -1
```

创建新迁移：

```bash
alembic revision --autogenerate -m "describe change"
```

### 说明

- Alembic 配置文件：`alembic.ini`
- 环境脚本：`alembic/env.py`
- 版本目录：`alembic/versions/`
- 初始迁移：`alembic/versions/20260408_0001_initial_schema.py`
- 修复迁移：`alembic/versions/20260408_0002_rename_currunt_price_column.py`
- 迁移默认从 `DATABASE_URL` 读取数据库连接，并自动将 `postgresql+asyncpg` 转为 Alembic 可用的同步驱动 URL
- `DB_INIT_MODE` 默认建议为 `migrate_only`，表示应用启动时不自动建表
- 如需对空开发库临时执行 `SQLModel.create_all`，可设置 `DB_INIT_MODE=create_all`

### 当前建议

- 默认使用迁移优先策略：应用启动时不会自动执行 `create_all`
- 启动前请先执行 `alembic upgrade head`
- 仅在明确需要快速初始化空开发库时，才临时设置 `DB_INIT_MODE=create_all`

## 已知限制

- bot / napcat 通道已具备基础结构，尚未完成最终联调验证

## 关键文件

- `app/tasks/price_checker.py`
- `app/notifications.py`
- `app/subscriber.py`
- `app/routers/tasks.py`
- `docs/project/implementation-progress.md`
