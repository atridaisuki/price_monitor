# 定时任务模块使用说明

## 功能概述

定时任务模块会自动检查所有商品的价格，并记录价格历史。

## 核心功能

### 1. 自动价格检查
- **执行频率**: 每 30 分钟
- **检查内容**: 所有数据库中的商品
- **操作流程**:
  1. 获取所有商品列表
  2. 使用对应平台的爬虫获取最新价格
  3. 更新商品的 `current_price` 和 `last_checked_time`
  4. 记录价格历史到 `PriceHistory` 表
  5. 检查是否达到目标价格（触发通知）

### 2. 手动触发检查
可以通过 API 手动触发价格检查：

```bash
POST /api/tasks/check-prices
```

响应示例：
```json
{
  "message": "价格检查完成",
  "summary": {
    "total_products": 1,
    "success_count": 1,
    "failure_count": 0,
    "history_count": 1,
    "notification_count": 1
  }
}
```

## 文件结构

```
app/tasks/
├── __init__.py          # 模块导出
├── scheduler.py         # APScheduler 调度器配置
└── price_checker.py     # 价格检查任务逻辑
```

## 配置说明

### 修改检查频率

编辑 `app/tasks/scheduler.py`:

```python
# 修改 minutes 参数
scheduler.add_job(
    check_all_prices,
    trigger=IntervalTrigger(minutes=30),  # 改为你想要的分钟数
    ...
)
```

### 日志输出

任务执行时会输出日志：
- 开始检查商品
- 每个商品的价格信息
- 达到目标价格的提醒
- 错误信息

## 测试步骤

1. 启动应用：
```bash
docker compose up -d db redis
docker compose run --rm web alembic upgrade head
docker compose up -d web
```

2. 添加测试商品：
```bash
curl -X POST http://localhost:8000/api/products/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试游戏",
    "url": "https://store.steampowered.com/app/123456",
    "platform": "steam",
    "target_price": 50.0
  }'
```

3. 手动触发价格检查：
```bash
curl -X POST http://localhost:8000/api/tasks/check-prices
```

4. 查看价格历史：
```bash
curl http://localhost:8000/api/products/1/history
```

## 注意事项

1. **爬虫频率**: 避免过于频繁的请求，建议不低于 15 分钟
2. **错误处理**: 爬取失败不会中断整个任务，会继续检查其他商品
3. **数据库连接**: 使用独立的 session，不会影响 API 请求
4. **通知系统**: 当前已接入 Redis 发布/订阅，默认主链路为 `Redis + subscriber`，bot / napcat 仍属增强通道

## 下一步

- [x] 已实现 Redis 通知系统
- [ ] 继续完善 NoneBot2 QQ 机器人
- [x] 已添加任务执行统计
- [ ] 如有需要再支持自定义检查频率（每个商品独立配置）
