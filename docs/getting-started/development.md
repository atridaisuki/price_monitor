# 价格监控系统开发流程

## 项目概述

通过 **NapCat + NoneBot2** 将价格监控功能部署为 QQ 机器人，当商品价格降到目标价时通过 QQ 通知用户。

## 系统架构

```
┌─────────────────┐         ┌─────────────────┐
│   NoneBot2      │◄────────┤   NapCat        │◄── QQ用户
│   (QQ Bot)      │  HTTP   │   (OneBot 11)   │
└────────┬────────┘         └─────────────────┘
         │
         │ HTTP API
         │
┌────────▼────────┐
│   FastAPI       │
│   (后端服务)    │
└────────┬────────┘
         │
    ┌────┴────┬────────┬──────────┐
    ▼         ▼        ▼          ▼
┌──────┐ ┌──────────┐ ┌─────┐ ┌─────────┐
│PostgreSQL││   Redis  │ │爬虫  │ │ 定时任务  │
│(数据库)  ││(缓存/队列)│ │模块  │ │         │
└──────┘ └──────────┘ └─────┘ └─────────┘
```

## 开发流程

### 第一阶段：完善 FastAPI 后端基础功能

#### 1.1 完成 CRUD API 端点
- [ ] 创建商品 (POST /api/products)
- [ ] 查询商品列表 (GET /api/products)
- [ ] 查询单个商品 (GET /api/products/{id})
- [ ] 更新商品 (PUT /api/products/{id})
- [ ] 删除商品 (DELETE /api/products/{id})
- [ ] 获取价格历史 (GET /api/products/{id}/history)

**文件**: `app/routers/products.py`

#### 1.2 实现价格爬取模块
- [ ] Steam 平台爬取
- [ ] 其他平台爬取（可选）
- [ ] 统一的爬取接口

**建议文件结构**:
```
app/
├── scrapers/
│   ├── __init__.py
│   ├── base.py          # 基础爬虫类
│   ├── steam.py         # Steam 爬虫
│   └── ...
```

#### 1.3 实现定时检查任务
- [ ] 定时扫描所有商品
- [ ] 爬取最新价格
- [ ] 更新数据库
- [ ] 记录价格历史

**建议使用**: APScheduler 或 Celery

#### 1.4 价格变动通知
- [ ] 当价格 <= 目标价格时触发通知
- [ ] 通过 Redis 发布/订阅或队列推送通知
- [ ] 支持绑定 QQ 号码到商品

**数据模型调整**:
```python
# Product 模型需要添加
user_qq: str  # 绑定的 QQ 号
notify_enabled: bool = True  # 是否启用通知
```

#### 1.5 数据库迁移
- [x] 已配置 Alembic
- [x] 已创建初始迁移
- [x] 已补数据库修复迁移
- [x] 已切到迁移优先启动策略（默认不再自动 `create_all`）

**当前约定**:
- 默认先执行 `alembic upgrade head`
- 应用启动依赖迁移后的数据库结构
- 仅在空开发库快速初始化时，才显式设置 `DB_INIT_MODE=create_all`

---

### 第二阶段：NoneBot2 + NapCat 集成

#### 2.1 NoneBot2 项目初始化
- [ ] 创建 NoneBot2 项目结构
- [ ] 配置 NapCat 适配器

**推荐目录结构**:
```
price_monitor/
├── app/                    # FastAPI 后端
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   └── ...
├── bot/                    # NoneBot2 机器人
│   ├── __init__.py
│   ├── config.py
│   └── plugins/
│       ├── price_monitor/  # 价格监控插件
│       │   ├── __init__.py
│       │   └── command.py
├── docker-compose.yml
└── requirements.txt
```

#### 2.2 实现 QQ 机器人指令
- [ ] `/添加监控 <商品链接> <目标价格>` - 添加商品监控
- [ ] `/查看监控` - 查看用户监控的商品列表
- [ ] `/删除监控 <商品ID>` - 删除某个监控
- [ ] `/修改价格 <商品ID> <新价格>` - 修改目标价格
- [ ] `/立即检查` - 手动触发价格检查（管理员）
- [ ] `/帮助` - 显示帮助信息

#### 2.3 NapCat 配置
- [ ] 安装 NapCat
- [ ] 配置 OneBot 11 协议
- [ ] 设置反向 Websocket 或 HTTP 地址

---

### 第三阶段：前后端集成

#### 3.1 QQ 机器人调用 FastAPI
- [ ] 封装 API 客户端（使用 httpx）
- [ ] 处理 API 错误和重试
- [ ] 消息格式化

#### 3.2 价格通知推送到 QQ
- [ ] Redis 订阅价格变动事件
- [ ] 通过 NoneBot2 发送 QQ 私信/群消息
- [ ] 通知模板优化（价格变动详情、链接等）

#### 3.3 Docker 部署
- [x] 已统一 Docker Compose 配置
- [x] 已包含：FastAPI、PostgreSQL、Redis、NoneBot2、NapCat
- [x] 已验证容器间网络通信
- [x] 已修复 `web` 服务挂载目录，确保本地代码同步到 `/app`

**当前推荐流程**:
1. `docker compose up -d db redis`
2. `docker compose run --rm web alembic upgrade head`
3. `docker compose up -d web`
4. 按需再启动 `bot` / `napcat`

---

### 第四阶段：优化与测试

#### 4.1 功能测试
- [ ] 添加商品测试
- [ ] 价格爬取测试
- [ ] 定时任务测试
- [ ] QQ 指令测试
- [ ] 通知功能测试

#### 4.2 性能优化
- [ ] Redis 缓存热点数据
- [ ] 数据库查询优化
- [ ] 爬虫并发控制
- [ ] API 限流

#### 4.3 健壮性
- [ ] 异常处理和日志
- [ ] 爬虫反爬策略
- [ ] 数据备份
- [ ] 监控告警

---

## 技术栈

| 模块 | 技术选型 |
|------|---------|
| Web 框架 | FastAPI |
| 数据库 | PostgreSQL + asyncpg |
| ORM | SQLModel |
| 缓存 | Redis |
| 任务调度 | APScheduler |
| QQ 机器人 | NoneBot2 + NapCat |
| HTTP 客户端 | httpx |
| 数据库迁移 | Alembic |
| 容器化 | Docker + Docker Compose |

---

## 依赖清单

### FastAPI 后端
```
fastapi
uvicorn
sqlmodel
psycopg2-binary
asyncpg
redis
httpx
alembic
apscheduler
```

### NoneBot2 机器人
```
nonebot2
nonebot-adapter-onebot
nonebot-plugin-apscheduler
```

---

## 下一步行动

1. **继续观察 bot / napcat** - 判断是否能从增强通道转为主通知通道
2. **保持迁移优先** - 所有数据库结构变更优先通过 Alembic 落地
3. **继续补部署说明** - 收口本地、Compose、生产环境运行步骤
4. **按需增强 bot 能力** - 在不影响主链路的前提下完善 QQ 指令与通知体验
5. **继续做最小验证** - 以 API、通知链路和消费者联调为主

---

## 注意事项

1. **NapCat 需要 NTQQ** - 确保服务器上有 QQ 客户端或使用 QQ Docker 版本
2. **爬虫频率控制** - 避免请求过快被反爬
3. **QQ 消息频率限制** - 避免触发风控
4. **数据库连接池** - 合理配置连接数
5. **日志记录** - 记录关键操作便于排查问题