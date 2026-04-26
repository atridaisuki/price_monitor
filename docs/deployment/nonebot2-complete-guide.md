# NoneBot2 QQ 机器人完整配置指南

## 当前定位

- 当前默认主通知通道仍是 `Redis + subscriber`
- `bot / napcat` 已具备基础运行条件，但还没有做到按商品绑定 QQ 用户精确通知
- 现阶段 bot 的价格提醒仍是广播给 `SUPERUSERS`
- 因此本指南更适合作为增强通道接入说明，而不是“唯一主通知链路”说明
- 配置上请优先使用 `bot/.env.example -> bot/.env`，不要继续依赖历史遗留的 `.env.prod`

## 项目结构（当前仓库）

```
bot/
├── .env.example             # 配置样例
├── .env                     # 本地实际配置
├── .gitignore               # Git 忽略文件
├── bot.py                   # 机器人入口
├── pyproject.toml           # 项目配置
├── requirements.txt         # Python 依赖
├── Dockerfile               # Docker 镜像
├── README.md                # 项目说明
└── src/
    └── plugins/             # 插件目录
        ├── price_monitor.py # 商品管理插件
        └── price_alert.py   # 价格提醒插件
```

## 与当前最小可用方案的关系

### 当前仓库状态
✅ 使用 `bot/.env.example -> bot/.env` 作为推荐配置方式
✅ 具备真实的 NoneBot2 入口、插件目录与 Dockerfile
✅ bot 可通过 Redis 订阅价格提醒，并可调用后端 API
✅ `/商品详情`、`/检查价格` 等指令已接入当前后端接口
✅ 文档已切到迁移优先启动流程

### 当前限制
❌ 价格提醒仍广播给 `SUPERUSERS`
❌ 还没有按商品绑定具体 QQ 用户
❌ 因此尚不适合作为唯一主通知通道

## 核心改进

### 1. 插件元数据
每个插件都有完整的元数据：
```python
__plugin_meta__ = PluginMetadata(
    name="价格监控",
    description="商品价格监控管理",
    usage="...",
    type="application",
    ...
)
```

### 2. 错误处理
- 网络超时处理
- Redis 连接重试（指数退避）
- 详细的错误日志

### 3. 消息格式
- 更美观的消息排版
- 使用分隔线和 Emoji
- 状态指示器（✅ ⏳ ❌）

### 4. 新增功能
- `/商品详情` - 查看商品详情和价格历史
- 更详细的商品列表展示
- 自动重连机制

## 配置步骤

### 第 1 步：从样例生成本地配置

```bash
cp bot/.env.example bot/.env
```

按实际情况修改，例如：

#### 本地环境（bot/.env）
```bash
# 超级用户（改成你的 QQ 号）
SUPERUSERS=["123456789"]

# OneBot 适配器（本地测试）
ONEBOT_WS_URLS=["ws://127.0.0.1:3001"]

# Redis（本地）
REDIS_URL=redis://localhost:6379

# API 地址（本地）
API_BASE_URL=http://localhost:8000
```

#### Docker Compose 场景常见取值
```bash
SUPERUSERS=["123456789"]
ONEBOT_WS_URLS=["ws://napcat:3001"]
REDIS_URL=redis://redis:6379
API_BASE_URL=http://web:8000
```

### 第 2 步：配置 NapCat

在 `docker-compose.yml` 中添加：

```yaml
  napcat:
    image: mlikiowa/napcat-docker:latest
    container_name: napcat
    restart: always
    ports:
      - "3001:3001"
      - "6099:6099"  # WebUI
    environment:
      - ACCOUNT=你的QQ号
      - WSR_ENABLE=true
      - WS_URLS=["ws://bot:8080/onebot/v11/ws"]
    volumes:
      - ./napcat/config:/app/napcat/config
      - ./napcat/data:/app/napcat/data
    depends_on:
      - bot
```

### 第 3 步：启动服务

```bash
# 先启动数据库与 Redis
docker compose up -d db redis

# 先执行数据库迁移
docker compose run --rm web alembic upgrade head

# 再启动后端、bot 与 napcat
docker compose up -d web bot napcat

# 查看日志
docker logs -f monitor_bot
```

### 第 4 步：QQ 登录

1. 访问 NapCat WebUI：http://localhost:6099
2. 扫码登录 QQ
3. 等待连接成功

## 功能说明

### 商品管理指令

| 指令 | 别名 | 说明 | 示例 |
|------|------|------|------|
| `/添加商品` | `/add` `/添加` | 添加商品到监控 | `/添加商品 游戏名 URL 100` |
| `/商品列表` | `/list` `/列表` | 查看所有监控商品 | `/商品列表` |
| `/商品详情` | `/detail` `/详情` | 查看商品详情和历史 | `/商品详情 1` |
| `/检查价格` | `/check` `/检查` | 手动触发价格检查 | `/检查价格` |
| `/删除商品` | `/del` `/删除` | 删除指定商品 | `/删除商品 1` |

### 自动提醒

- 当商品价格 ≤ 目标价格时自动发送 QQ 消息
- 当前消息发送给 `SUPERUSERS` 中配置的账号
- 通过 Redis Pub/Sub 实时接收
- 如需转为主通知通道，还需要补“商品与接收 QQ 用户绑定”能力

## 测试流程

### 1. 测试 API 连接

```bash
# 添加商品
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试游戏",
    "url": "https://store.steampowered.com/app/123456",
    "platform": "steam",
    "target_price": 999999.0
  }'
```

### 2. 测试 QQ 指令

在 QQ 中发送：
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

### 3. 测试价格提醒

```bash
# 发送测试通知
curl -X POST http://localhost:8000/api/tasks/test-notification
```

应该收到 QQ 消息：
```
🎉 价格提醒！
━━━━━━━━━━━━━━━━
商品: 测试商品
当前价格: ¥99.99
目标价格: ¥100.00
平台: test
━━━━━━━━━━━━━━━━
链接: https://example.com
━━━━━━━━━━━━━━━━
快去购买吧！💰
```

## 常见问题

### 1. 机器人无法连接

**检查 NapCat 状态：**
```bash
docker logs napcat
```

**检查 WebSocket 配置：**
- NoneBot2 的 `ONEBOT_WS_URLS` 指向 NapCat
- NapCat 的 `WS_URLS` 指向 NoneBot2

### 2. Redis 连接失败

**检查 Redis 状态：**
```bash
docker exec -it monitor_redis redis-cli ping
# 应该返回 PONG
```

**查看机器人日志：**
```bash
docker logs -f monitor_bot
# 应该看到 "Redis 连接成功"
```

### 3. 收不到消息

**检查超级用户配置：**
```bash
# bot/.env
SUPERUSERS=["你的QQ号"]  # 必须是字符串列表
```

**检查机器人是否在线：**
- 在 QQ 中发送任意指令测试
- 查看 NapCat WebUI 连接状态

### 4. 指令无响应

**检查命令前缀：**
```bash
# bot/.env
COMMAND_START=["/", ""]  # 支持 / 或无前缀
```

**查看日志：**
```bash
docker logs -f monitor_bot
# 应该看到指令处理日志
```

## 高级配置

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

修改 `bot/src/plugins/price_alert.py`：
```python
# 发送到群聊
await bot.send_group_msg(
    group_id=123456789,  # 群号
    message=message
)
```

### 3. 自定义消息格式

修改插件中的消息构造部分，使用 MessageSegment 组合：
```python
from nonebot.adapters.onebot.v11 import MessageSegment

message = (
    MessageSegment.text("文本") +
    MessageSegment.image("图片URL") +
    MessageSegment.at(user_id)
)
```

## 性能优化

### 1. 连接池配置

Redis 连接已使用连接池，默认配置足够使用。

### 2. 并发控制

如果商品数量很多，可以在 `price_checker.py` 中添加并发控制：
```python
import asyncio

# 限制并发数
semaphore = asyncio.Semaphore(5)

async def check_with_limit(product, session):
    async with semaphore:
        await check_product_price(product, session)
```

### 3. 日志级别

生产环境建议使用 `INFO` 级别：
```bash
LOG_LEVEL=INFO
```

## 安全建议

1. **不要提交敏感配置**
   - `bot/.env` 应仅保留在本地
   - 历史遗留的 `.env.prod` 不应再作为当前推荐流程
   - 不要在公开仓库提交 QQ 号等信息

2. **使用小号测试**
   - 避免主号被封
   - 测试稳定后再用主号

3. **控制消息频率**
   - 不要频繁发送消息
   - 避免触发 QQ 风控

4. **定期备份数据**
   - 备份数据库
   - 备份配置文件

## 开发指南

### 添加新插件

在 `src/plugins/` 创建新文件：

```python
from nonebot import on_command
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="插件名称",
    description="插件描述",
    usage="使用说明",
)

my_command = on_command("指令名", priority=5, block=True)

@my_command.handle()
async def handle():
    await my_command.finish("响应内容")
```

### 调试技巧

1. **启用详细日志：**
```bash
LOG_LEVEL=DEBUG
```

2. **查看实时日志：**
```bash
docker logs -f monitor_bot
```

3. **测试单个插件：**
```python
# 在 bot.py 中注释其他插件
# nonebot.load_plugins("src/plugins")
nonebot.load_plugin("src.plugins.price_monitor")
```

## 下一步

- [ ] 使用 `bot/.env.example` 生成本地配置并填写真实值
- [ ] 配置 NapCat 并登录 QQ
- [ ] 测试所有指令
- [ ] 测试价格提醒功能
- [ ] 如需转正为主通道，再补“商品绑定具体 QQ 用户”的通知路由能力

## 参考资料

- [NoneBot2 官方文档](https://nonebot.dev/)
- [NapCat 项目](https://github.com/NapNeko/NapCatQQ)
- [OneBot 标准](https://onebot.dev/)
- [NoneBot2 插件开发](https://nonebot.dev/docs/tutorial/plugin/)

## 技术支持

遇到问题可以：
1. 查看 Docker 日志
2. 检查配置文件
3. 测试 API 连接
4. 查阅官方文档
