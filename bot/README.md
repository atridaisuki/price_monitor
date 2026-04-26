# Price Monitor QQ Bot

基于 NoneBot2 的价格监控 QQ 机器人。

## 功能特性

- 🛒 商品管理：添加、查询、删除监控商品
- 💰 价格提醒：自动推送价格达标通知
- 🔄 实时同步：通过 Redis 订阅价格变动
- 🤖 QQ 交互：支持私聊和群聊指令

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

复制样例文件并修改配置：

```bash
cp .env.example .env
```

至少修改 `SUPERUSERS`、`ONEBOT_WS_URLS`、`REDIS_URL`、`API_BASE_URL`。不要把真实敏感配置提交回仓库。

### 3. 启动机器人

```bash
python bot.py
```

或使用 nb-cli：

```bash
nb run
```

## Docker 部署

当前更推荐按主项目根目录统一启动，并先完成数据库迁移：

```bash
docker compose up -d db redis
docker compose run --rm web alembic upgrade head
docker compose up -d web bot napcat
```

说明：
- `bot` 当前依赖 Redis 订阅价格提醒事件
- `API_BASE_URL` 在 Compose 中默认走 `http://web:8000`
- `ONEBOT_WS_URLS` 在 Compose 中默认连接 `ws://napcat:3001`

## 指令列表

| 指令 | 说明 | 示例 |
|------|------|------|
| `/添加商品` | 添加商品到监控 | `/添加商品 游戏名 URL 目标价格` |
| `/商品列表` | 查看所有监控商品 | `/商品列表` |
| `/检查价格` | 手动触发价格检查 | `/检查价格` |
| `/删除商品` | 删除指定商品 | `/删除商品 1` |

## 配置说明

### 环境变量

- `SUPERUSERS`: 超级用户 QQ 号列表，主要用于未绑定商品提醒和手工测试通知的 fallback
- `ONEBOT_WS_URLS`: OneBot 适配器 WebSocket 地址
- `REDIS_URL`: Redis 连接地址
- `API_BASE_URL`: FastAPI 服务地址

### 当前限制

- 现在 bot 会优先把价格提醒定向发给商品绑定的 `user_qq`
- 通过 `/添加商品` 创建商品时，会自动绑定发起命令的 QQ 号
- 未绑定商品或 `POST /api/tasks/test-notification` 这类手工测试通知，仍会 fallback 到 `SUPERUSERS`
- 在完成真实 QQ 消息链路长期稳定验证前，主线仍以 `Redis + subscriber` 为准

### 适配器配置

需要配合 NapCat 或 go-cqhttp 使用。

## 项目结构

```
bot/
├── .env.example        # 配置样例
├── .env                # 本地实际配置（不应提交敏感内容）
├── .env.prod           # 历史生产配置文件，后续建议停用并改为样例驱动
├── .gitignore          # Git 忽略文件
├── bot.py              # 机器人入口
├── pyproject.toml      # 项目配置
├── requirements.txt    # Python 依赖
├── Dockerfile          # Docker 镜像
├── README.md           # 说明文档
└── src/
    └── plugins/        # 插件目录
        ├── price_monitor.py   # 商品管理插件
        └── price_alert.py     # 价格提醒插件
```

## 开发指南

### 添加新插件

在 `src/plugins/` 目录下创建新的 Python 文件：

```python
from nonebot import on_command

my_command = on_command("我的指令")

@my_command.handle()
async def handle():
    await my_command.finish("响应内容")
```

### 调试模式

设置环境变量 `LOG_LEVEL=DEBUG` 启用详细日志。

## 常见问题

### 1. 机器人无法连接

检查 OneBot 适配器是否正常运行，WebSocket 地址是否正确。

### 2. 收不到消息

确认 `SUPERUSERS` 配置正确，且 Redis 连接正常。

### 3. 指令无响应

检查命令前缀配置，默认支持 `/` 和无前缀。

## 许可证

MIT License

## 相关链接

- [NoneBot2 文档](https://nonebot.dev/)
- [OneBot 标准](https://onebot.dev/)
- [项目主页](https://github.com/yourusername/price-monitor)
