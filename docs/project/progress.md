# 项目进度梳理

## 完成度: 约 85%

| 模块 | 状态 | 完成度 |
|------|------|--------|
| 项目结构 | ✓ | 100% |
| Docker 配置 | ✓ | 100% |
| FastAPI 框架 | ✓ | 100% |
| 数据模型 | ✓ | 100% |
| 数据库连接 | ✓ | 100% |
| Pydantic Schemas | ✓ | 100% |
| API 路由 (CRUD) | ✓ | 100% |
| Steam 爬虫 | ✓ | 100% |
| 定时任务 | ✓ | 100% |
| Redis 通知系统 | ✓ | 100% |
| NoneBot2 QQ 机器人 | ✓ | 100% |
| Dockerfile | ✓ | 100% |
| 数据库迁移 (Alembic) | ✗ | 0% |
| 测试 | ✗ | 0% |

---

## 已完成内容

### 1. 项目结构

```
price_monitor/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── app/
│   ├── main.py             # FastAPI 入口，注册路由、定时任务、Redis
│   ├── database.py         # 异步 PostgreSQL 连接
│   ├── models.py           # SQLModel 模型（Product, PriceHistory）
│   ├── schemas.py          # Pydantic 验证模型
│   ├── notifications.py    # Redis pub/sub 通知服务
│   ├── redis_client.py     # Redis 客户端单例
│   ├── subscriber.py       # 独立订阅者脚本（测试用）
│   ├── routers/
│   │   ├── products.py     # 商品 CRUD + 价格历史 API
│   │   └── tasks.py        # 手动触发任务 API
│   ├── scrapers/
│   │   ├── base.py         # 爬虫基类
│   │   ├── steam.py        # Steam 价格爬虫
│   │   └── exceptions.py   # 爬虫异常
│   └── tasks/
│       ├── price_checker.py # 价格检查逻辑
│       └── scheduler.py    # APScheduler 定时任务
└── bot/
    ├── Dockerfile
    ├── bot.py
    └── src/plugins/
        ├── price_monitor.py # QQ 商品管理指令
        ├── price_alert.py   # Redis 订阅 → QQ 推送
        └── ai_chat.py       # AI 对话插件
```

### 2. Docker 服务

| 服务 | 镜像 | 端口 | 说明 |
|------|------|------|------|
| web | 自定义构建 | 8000 | FastAPI 应用 |
| db | postgres:15-alpine | 5432 | PostgreSQL |
| redis | redis:alpine | 6379 | Redis |
| bot | 自定义构建 | 8080 | NoneBot2 机器人 |
| napcat | mlikiowa/napcat-docker | 3001/6099 | QQ 协议端 |

### 3. API 路由

**商品管理 `/api/products`**
- `POST /` - 创建商品
- `GET /` - 商品列表（分页）
- `GET /{id}` - 商品详情
- `PUT /{id}` - 更新商品
- `DELETE /{id}` - 删除商品
- `GET /{id}/history` - 价格历史

**任务 `/api/tasks`**
- `POST /check-prices` - 手动触发价格检查
- `POST /test-notification` - 测试通知

### 4. QQ 机器人指令

| 指令 | 说明 |
|------|------|
| `/添加商品 <名称> <URL> <价格>` | 添加监控商品 |
| `/商品列表` | 查看所有商品 |
| `/商品详情 <ID>` | 查看详情+价格历史 |
| `/检查价格` | 手动触发检查 |
| `/删除商品 <ID>` | 删除商品 |

---

## 未完成内容

### 1. 数据库迁移 (Alembic) ✗

当前使用 `SQLModel.metadata.create_all` 自动建表，无法管理 schema 变更。

需要:
- `alembic init` 初始化
- 配置 `env.py` 使用异步引擎
- 生成初始迁移脚本

### 2. 测试 ✗

需要:
- API 端点集成测试
- Steam 爬虫单元测试（mock HTTP）
- 通知系统测试

---

## 下一步建议

### P0 - 让项目跑起来
1. **配置 `.env` 文件** - 填写 QQ 号到 `SUPERUSERS`，确认 `REDIS_URL` 和 `API_BASE_URL`
2. **按迁移优先流程启动 Docker Compose** - `docker compose up -d db redis` -> `docker compose run --rm web alembic upgrade head` -> `docker compose up -d web bot napcat`
3. **NapCat 扫码登录** - 访问 `http://localhost:6099` 完成 QQ 登录

### P1 - 稳定性
4. **Alembic 迁移** - 替换 `create_all`，支持生产环境 schema 变更
5. **错误重试** - Steam 爬虫加请求重试逻辑

### P2 - 扩展
6. **多平台爬虫** - 支持 Epic、GOG 等平台
7. **测试覆盖** - 核心逻辑单元测试
