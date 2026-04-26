# NapCat QQ 机器人快速配置指南

## 🚀 快速开始

### 第 1 步：准备配置

不要直接编辑历史遗留的 `bot/.env.prod`，改为从样例文件生成本地配置：

```bash
cp bot/.env.example bot/.env
```

然后按实际情况修改：

```bash
SUPERUSERS=["你的QQ号"]
```

如使用 Docker Compose，通常还需要确认：

- `API_BASE_URL=http://web:8000`
- `REDIS_URL=redis://redis:6379`
- `ONEBOT_WS_URLS=["ws://napcat:3001"]`

### 第 2 步：启动服务

```bash
# 先启动数据库与 Redis
docker compose up -d db redis

# 先执行数据库迁移
docker compose run --rm web alembic upgrade head

# 再启动后端、bot 与 napcat
docker compose up -d web bot napcat

# 查看日志
docker logs -f monitor_napcat
docker logs -f monitor_bot
```

### 第 3 步：登录 QQ

1. 打开浏览器访问：http://localhost:6099
2. 在 NapCat WebUI 中扫码登录 QQ
3. 等待连接成功（查看日志确认）

### 第 4 步：测试机器人

在 QQ 中给机器人发送消息：

```
/添加商品 测试游戏 https://store.steampowered.com/app/123456 50
```

应该收到回复：
```
✅ 商品添加成功！
━━━━━━━━━━━━━━━━
ID: 1
名称: 测试游戏
目标价格: ¥50.0
━━━━━━━━━━━━━━━━
系统将自动监控价格变动
```

## 当前判断

- `bot / napcat` 已具备运行入口、插件、Compose 服务和基础联通条件
- 但当前提醒发送仍基于 `SUPERUSERS` 广播，不是按商品绑定用户精确投递
- 因此目前更适合作为增强通知通道，暂不建议替代 `Redis + subscriber` 主链路
- 后续若要转正，至少需要补“商品与接收 QQ 用户的绑定关系”以及一次稳定的真实 QQ 联调验证

## 📝 可用指令

| 指令 | 说明 | 示例 |
|------|------|------|
| `/添加商品` | 添加商品到监控 | `/添加商品 游戏名 URL 目标价格` |
| `/商品列表` | 查看所有监控商品 | `/商品列表` |
| `/商品详情` | 查看商品详情 | `/商品详情 1` |
| `/检查价格` | 手动触发价格检查 | `/检查价格` |
| `/删除商品` | 删除指定商品 | `/删除商品 1` |

## 🔧 服务端口

- **8000**: FastAPI 后端服务
- **8080**: NoneBot2 机器人服务
- **3001**: NapCat WebSocket 端口
- **6099**: NapCat WebUI 管理界面
- **5432**: PostgreSQL 数据库
- **6379**: Redis 缓存

## 🐛 常见问题

### 1. 机器人无法连接

**检查 NapCat 状态：**
```bash
docker logs napcat
```

**检查 Bot 状态：**
```bash
docker logs monitor_bot
```

### 2. 收不到消息

确认：
- QQ 已成功登录（查看 NapCat WebUI）
- SUPERUSERS 配置正确
- 机器人和 NapCat 都在运行

### 3. 指令无响应

检查：
- 命令前缀是否正确（默认支持 `/` 和无前缀）
- 查看 bot 日志是否有错误

## 🧪 测试价格提醒

手动触发测试通知：

```bash
curl -X POST http://localhost:8000/api/tasks/test-notification
```

你应该在 QQ 中收到价格提醒消息。

## 📊 查看日志

```bash
# 查看所有服务
docker compose logs -f

# 查看特定服务
docker logs -f monitor_web
docker logs -f monitor_bot
docker logs -f monitor_napcat
docker logs -f monitor_redis
docker logs -f monitor_db
```

## 🛑 停止服务

```bash
# 停止所有服务
docker compose down

# 停止并删除数据卷（慎用！）
docker compose down -v
```

## 📚 更多文档

- 详细配置：`docs/deployment/nonebot2-complete-guide.md`
- Redis 通知：`docs/deployment/redis-notification-guide.md`
- 任务系统：`docs/architecture/task-module-guide.md`
