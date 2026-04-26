# NoneBot2 QQ 机器人配置指南

## 当前定位

- `bot / napcat` 已具备运行入口、Compose 服务和基础联通条件
- bot 现在支持按商品绑定的 `user_qq` 精确投递价格提醒
- 通过 bot `/添加商品` 添加商品时，会自动绑定发起命令的 QQ 号
- `SUPERUSERS` 仍保留为未绑定商品和手工测试通知的 fallback
- 如需启用 bot，请优先使用 `bot/.env.example` 生成本地配置，不要继续依赖历史遗留的 `bot/.env.prod`

## 项目结构

```
bot/
├── .env.example           # 配置样例
├── .env                   # 本地实际配置
├── .gitignore             # Git 忽略文件
├── bot.py                 # 机器人入口
├── pyproject.toml         # 项目配置
├── requirements.txt       # Python 依赖
├── Dockerfile             # Docker 镜像
└── src/plugins/           # 插件目录
    ├── price_monitor.py   # 商品管理指令
    └── price_alert.py     # 价格提醒订阅
```

## 功能说明

### 1. 商品管理指令

| 指令 | 说明 | 示例 |
|------|------|------|
| `/添加商品` | 添加商品到监控 | `/添加商品 赛博朋克2077 https://store.steampowered.com/app/1091500 100` |
| `/商品列表` | 查看所有监控商品 | `/商品列表` |
| `/检查价格` | 手动触发价格检查 | `/检查价格` |
| `/删除商品` | 删除指定商品 | `/删除商品 1` |

### 2. 自动价格提醒

- 当商品价格 ≤ 目标价格时，自动发送 QQ 消息
- 若消息带有 `user_qq`，则优先定向发送给该商品绑定用户
- 若没有 `user_qq`，则回退发送给配置的超级用户（管理员）
- 通过 Redis Pub/Sub 实时接收通知

## 配置步骤

### 第 1 步：生成本地配置

不要直接编辑历史遗留的 `bot/.env.prod`，改为从样例文件生成本地配置：

```bash
cp bot/.env.example bot/.env
```

然后按实际情况修改：

```bash
SUPERUSERS=["123456789"]

# OneBot 适配器地址（本地一般是 127.0.0.1，Compose 中一般是 napcat）
ONEBOT_WS_URLS=["ws://127.0.0.1:3001"]

# Redis（本地）
REDIS_URL=redis://localhost:6379

# API 地址（本地）
API_BASE_URL=http://localhost:8000
```

### 第 2 步：配置 NapCat（QQ 协议适配器）

NapCat 是 QQ 机器人的协议适配器，需要单独部署。

#### 方案 A：Docker 部署（推荐）

在 `docker-compose.yml` 中添加 NapCat 服务：

```yaml
  napcat:
    image: mlikiowa/napcat-docker:latest
    container_name: napcat
    restart: always
    ports:
      - "3001:3001"
      - "6099:6099"  # WebUI 端口
    environment:
      - ACCOUNT=你的QQ号
      - WSR_ENABLE=true
      - WS_URLS=["ws://bot:8080/onebot/v11/ws"]
    volumes:
      - ./napcat/config:/app/napcat/config
      - ./napcat/data:/app/napcat/data
```

#### 方案 B：手动部署

1. 下载 NapCat：https://github.com/NapNeko/NapCatQQ
2. 配置 `config.json`
3. 启动 NapCat 并扫码登录

### 第 3 步：启动服务

推荐按主项目根目录分步启动，并先完成数据库迁移：

```bash
# 先启动数据库与 Redis
docker compose up -d db redis

# 先执行数据库迁移
docker compose run --rm web alembic upgrade head

# 再启动后端、bot 与 napcat
docker compose up -d web bot napcat

# 查看机器人日志
docker logs -f monitor_bot
```

### 第 4 步：QQ 登录

1. 访问 NapCat WebUI：http://localhost:6099
2. 扫码登录 QQ
3. 等待连接成功

### 第 5 步：测试机器人

在 QQ 中发送指令：

```
/添加商品 测试游戏 https://store.steampowered.com/app/123456 50
```

应该收到回复：
```
✅ 商品添加成功！
ID: 1
名称: 测试游戏
目标价格: ¥50.0
绑定 QQ: 你的QQ号
```

## 测试价格提醒

### 方法 1：使用测试 API

```bash
curl -X POST http://localhost:8000/api/tasks/test-notification
```

你应该会收到 QQ 消息：
```
🎉 价格提醒！
━━━━━━━━━━━━━━━━
商品: 测试商品
当前价格: ¥99.99
目标价格: ¥100.00
平台: test
链接: https://example.com
━━━━━━━━━━━━━━━━
快去购买吧！
```

### 方法 2：添加真实商品

1. 添加一个目标价格很高的商品
2. 等待定时任务检查（30 分钟）
3. 或手动触发：`/检查价格`

## 常见问题

### 1. 机器人无法连接

**检查 NapCat 是否运行：**
```bash
docker logs napcat
```

**检查 WebSocket 配置：**
- NoneBot2 的 `ONEBOT_WS_URLS` 必须指向 NapCat
- NapCat 的 `WS_URLS` 必须指向 NoneBot2

### 2. 收不到消息

**检查超级用户配置：**
```bash
# bot/.env
SUPERUSERS=["你的QQ号"]  # 用于未绑定商品提醒和手工测试 fallback
```

**检查 Redis 连接：**
```bash
docker exec -it monitor_redis redis-cli ping
# 应该返回 PONG
```

### 3. QQ 被风控

**降低风险的方法：**
- 使用小号测试
- 控制消息频率（不要频繁发送）
- 添加随机延迟
- 模拟人类行为（不要立即回复）

**如果被封：**
- 尝试申诉
- 更换账号
- 考虑使用其他通知方式（Telegram、邮件等）

### 4. 指令无响应

**检查命令前缀：**
```bash
# bot/.env
COMMAND_START=["/", ""]  # 支持 / 或无前缀
```

**查看机器人日志：**
```bash
docker logs -f monitor_bot
```

## 进阶配置

### 1. 修改检查频率

编辑 `app/tasks/scheduler.py`：

```python
scheduler.add_job(
    check_all_prices,
    trigger=IntervalTrigger(minutes=30),  # 改为你想要的分钟数
    ...
)
```

### 2. 添加群聊支持

修改 `bot/plugins/price_alert.py`：

```python
# 发送到群聊
await bot.send_group_msg(
    group_id=123456789,  # 群号
    message=message
)
```

### 3. 添加更多指令

在 `bot/plugins/` 创建新的插件文件：

```python
from nonebot import on_command

my_command = on_command("我的指令", priority=5)

@my_command.handle()
async def handle_my_command():
    await my_command.finish("指令响应")
```

## 安全建议

1. **不要在公开仓库提交真实环境文件**（如 `bot/.env`、历史遗留的 `.env.prod`）
2. **使用小号测试**，避免主号被封
3. **控制消息频率**，避免触发风控
4. **定期备份数据**
5. **监控日志**，及时发现异常

## 目录结构说明

```
price_monitor/
├── app/                   # FastAPI 应用
├── bot/                   # NoneBot2 机器人
│   ├── src/plugins/       # 机器人插件
│   ├── .env.example       # 配置样例
│   └── .env               # 本地实际配置
├── docs/                  # 文档
├── docker-compose.yml     # Docker 编排（已包含 NapCat）
└── ...
```

## 下一步

- [ ] 配置 NapCat 并登录 QQ
- [ ] 测试所有指令
- [ ] 测试价格提醒功能
- [ ] 根据需要调整配置
- [ ] 添加更多自定义功能

## 参考资料

- NoneBot2 文档：https://nonebot.dev/
- NapCat 项目：https://github.com/NapNeko/NapCatQQ
- OneBot 标准：https://onebot.dev/

## 技术支持

如遇问题，可以：
1. 查看 Docker 日志：`docker logs monitor_bot`
2. 检查 Redis 连接：`docker exec -it monitor_redis redis-cli`
3. 测试 API：`curl http://localhost:8000/api/products/`
