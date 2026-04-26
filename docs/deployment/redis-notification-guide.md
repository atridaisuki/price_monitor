# Redis 通知系统使用说明

## 功能概述

Redis 通知系统使用 Redis 的发布/订阅（Pub/Sub）机制实现实时价格提醒。当商品价格达到目标价格时，系统会自动发布通知消息。

## 架构设计

```
价格检查任务 → Redis Pub/Sub → 订阅者（QQ机器人/邮件/Webhook等）
```

## 核心组件

### 1. Redis 客户端 (`app/redis_client.py`)
- 管理 Redis 连接
- 提供全局 Redis 实例

### 2. 通知服务 (`app/notifications.py`)
- `NotificationService.publish_price_alert()` - 发布价格提醒
- `NotificationService.subscribe_price_alerts()` - 订阅价格提醒

### 3. 订阅者示例 (`app/subscriber.py`)
- 独立的订阅者脚本
- 可作为 QQ 机器人集成的基础

## 消息格式

价格提醒消息 JSON 格式：

```json
{
  "type": "price_alert",
  "product_id": 1,
  "product_name": "游戏名称",
  "current_price": 49.99,
  "target_price": 50.00,
  "url": "https://store.steampowered.com/app/123456",
  "platform": "steam",
  "trigger_reason": "target_price_reached",
  "timestamp": "2026-03-11T10:30:00"
}
```

## 使用方法

### 1. 启动应用

推荐按当前仓库的迁移优先流程启动：

```bash
# 启动数据库与 Redis
docker compose up -d db redis

# 执行数据库迁移
docker compose run --rm web alembic upgrade head

# 启动后端服务
docker compose up -d web
```

### 2. 启动订阅者（测试用）

在另一个终端中运行：

```bash
# 进入容器
docker exec -it monitor_web bash

# 运行订阅者
python -m app.subscriber
```

### 3. 测试通知系统

发送测试通知：

```bash
curl -X POST http://localhost:8000/api/tasks/test-notification
```

### 4. 实际使用流程

1. 添加商品并设置目标价格
2. 定时任务自动检查价格
3. 当价格 ≤ 目标价格时，自动发布通知
4. 订阅者接收通知并处理（发送 QQ 消息等）

## API 端点

### 测试通知
```bash
POST /api/tasks/test-notification
```

响应：
```json
{
  "message": "测试通知已发送",
  "success": true
}
```

### 手动触发价格检查
```bash
POST /api/tasks/check-prices
```

## 集成示例

### 自定义订阅者

```python
import asyncio
from app.notifications import NotificationService

async def my_handler(message: dict):
    """自定义消息处理"""
    print(f"收到通知: {message['product_name']}")
    # 在这里添加你的逻辑
    # 例如：发送 QQ 消息、邮件、Webhook 等

async def main():
    await NotificationService.subscribe_price_alerts(my_handler)

if __name__ == "__main__":
    asyncio.run(main())
```

### 在代码中发布通知

```python
from app.notifications import NotificationService

await NotificationService.publish_price_alert(
    product_id=1,
    product_name="游戏名称",
    current_price=49.99,
    target_price=50.00,
    url="https://example.com",
    platform="steam"
)
```

## Redis 频道

- **频道名称**: `price_alerts`
- **消息格式**: JSON 字符串
- **编码**: UTF-8

## 配置说明

### 环境变量

```bash
REDIS_URL=redis://redis:6379
```

### Docker Compose 配置

当前仓库中的 Redis 服务名是 `redis`：

```yaml
redis:
  image: redis:alpine
  container_name: monitor_redis
  restart: always
  ports:
    - "6379:6379"
```

## 测试步骤

### 完整测试流程

1. **启动数据库、Redis 和后端**
```bash
docker compose up -d db redis
docker compose run --rm web alembic upgrade head
docker compose up -d web
```

2. **启动订阅者（新终端）**
```bash
docker compose exec web python -m app.subscriber
```

3. **添加测试商品**
```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试游戏",
    "url": "https://store.steampowered.com/app/123456",
    "platform": "steam",
    "target_price": 999999.0
  }'
```

4. **发送测试通知**
```bash
curl -X POST http://localhost:8000/api/tasks/test-notification
```

5. **观察订阅者输出**
应该能看到类似输出：
```
============================================================
🔔 收到价格提醒通知！
商品名称: 测试商品
当前价格: ¥99.99
目标价格: ¥100.00
平台: test
链接: https://example.com
时间: 2026-03-11T10:30:00
============================================================
```

## 下一步集成

### NoneBot2 QQ 机器人

将订阅者逻辑集成到 NoneBot2：

```python
# 在 NoneBot2 插件中
from app.notifications import NotificationService

async def send_qq_message(message: dict):
    """发送 QQ 消息"""
    await bot.send_private_msg(
        user_id=qq_number,
        message=f"价格提醒：{message['product_name']} "
                f"现价 ¥{message['current_price']}"
    )

# 启动订阅
await NotificationService.subscribe_price_alerts(send_qq_message)
```

## 注意事项

1. **Redis 连接**: 确保 Redis 服务正常运行
2. **订阅者数量**: Redis Pub/Sub 会显示当前订阅者数量
3. **消息持久化**: Pub/Sub 不持久化消息，订阅者离线时会丢失消息
4. **性能**: Redis Pub/Sub 性能优秀，适合实时通知场景

## 故障排查

### 订阅者收不到消息

1. 检查 Redis 连接：
```bash
docker exec -it monitor_redis redis-cli ping
```

2. 检查订阅者是否运行
3. 检查 REDIS_URL 环境变量

### 发布失败

查看应用日志：
```bash
docker logs monitor_web
```

## 扩展功能

- [ ] 支持多种通知类型（价格上涨、价格下跌等）
- [ ] 添加通知去重机制
- [ ] 支持用户订阅特定商品
- [ ] 集成 NoneBot2 QQ 机器人
- [ ] 添加邮件通知
- [ ] 添加 Webhook 通知
