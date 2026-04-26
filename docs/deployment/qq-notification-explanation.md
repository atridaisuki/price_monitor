# 精确 QQ 通知改造说明

## 1. 这次改动解决了什么问题

原来的通知链路虽然已经能跑通：

`POST /api/tasks/check-prices -> check_all_prices -> publish_price_alert -> Redis subscriber / bot consumer`

但是 bot 侧在真正发 QQ 消息时，仍然是把提醒广播给 `SUPERUSERS`，而不是发给“创建这个商品的那个 QQ 用户”。

这会带来两个问题：

1. 提醒不精确：谁添加的商品，并不能只通知谁。
2. bot 不能作为真正可用的通知终点：它只是一个管理员广播器，而不是用户级通知器。

这次改造做的事情，本质上就是：

**把接收提醒的 QQ 号绑定到商品上，然后沿着现有链路把这个 QQ 号一直带到 bot 消费端，最后由 bot 定向私聊发送。**

---

## 2. 你现在应该从哪里开始看

如果你想最快理解这次改造，建议按下面顺序阅读：

### 第一层：先看“数据长什么样”
1. `app/models.py`
2. `app/schemas.py`
3. `alembic/versions/20260409_0003_add_user_qq_to_product.py`

先搞清楚：
- `user_qq` 是什么字段
- 它存在哪里
- 为什么要加数据库迁移

### 第二层：再看“API 怎么接这个字段”
4. `app/routers/products.py`

这里重点理解：
- 创建商品时为什么不用额外写很多逻辑也能保存 `user_qq`
- 更新商品时为什么局部更新逻辑天然支持 `user_qq`

### 第三层：再看“提醒消息怎么把这个字段带出去”
5. `app/tasks/price_checker.py`
6. `app/notifications.py`

这里重点理解：
- 什么时候触发提醒
- Redis 发布的消息体长什么样
- `user_qq` 是怎么从商品对象进入通知消息的

### 第四层：最后看“bot 怎么用这个字段发消息”
7. `bot/src/plugins/price_monitor.py`
8. `bot/src/plugins/price_alert.py`

这里重点理解：
- 用户在 QQ 里 `/添加商品` 时，QQ 号是怎么拿到的
- 为什么现在 bot 能知道提醒应该发给谁
- 为什么还保留 `SUPERUSERS` fallback

### 第五层：最后补测试
9. `tests/test_product_routes.py`
10. `tests/test_price_checker.py`
11. `tests/test_notifications.py`
12. `tests/test_task_routes.py`
13. `tests/test_bot_price_alert.py`

测试是帮你确认“我理解的行为”是不是和代码真的一致。

---

## 3. 整体架构变化，一句话总结

从：

**商品只存价格监控信息，通知接收人靠 bot 全局配置 `SUPERUSERS` 决定**

变成：

**商品自身就带 `user_qq`，通知接收人跟着商品走，bot 只负责执行定向发送**

也就是说，接收人信息从“bot 配置层”下沉到了“业务数据层”。

这是一种更合理的设计，因为：
- 商品属于谁，是业务数据；
- 不是 bot 的全局配置。

---

## 4. 本次新增 / 修改了哪些内容

---

### 4.1 数据模型层：给商品增加 `user_qq`

#### 文件
- `app/models.py`
- `app/schemas.py`
- `alembic/versions/20260409_0003_add_user_qq_to_product.py`

#### 做了什么

在 `ProductBase` 中新增：

```python
user_qq: Optional[str] = None
```

对应 API schema 也同步新增：
- `ProductBaseSchema`
- `ProductCreate`
- `ProductRead`
- `ProductUpdate`

数据库迁移中新增列：

```python
op.add_column("product", sa.Column("user_qq", sa.String(), nullable=True))
```

#### 为什么这样做

因为我们需要让“这个商品应该通知哪个 QQ 号”成为商品自己的属性。

而且这里故意用了：
- **单字段**
- **可空**
- **字符串**

这样做是最小改动方案：

1. **单字段**：不引入新表，不做用户表，不做多对多。
2. **可空**：老数据不受影响，没绑定的商品也还能继续跑。
3. **字符串**：QQ 号本质上更像标识符，不需要做算术运算，用字符串更稳。

#### 这里用到的技术

##### SQLModel
`app/models.py` 里的 `Product` 是 SQLModel 模型。

SQLModel 同时融合了：
- SQLAlchemy 的 ORM 能力
- Pydantic/数据校验风格

所以它既能描述数据库表，也能描述 Python 对象结构。

##### Optional
`Optional[str] = None` 表示这个字段可以没有值。

这很重要，因为：
- 历史商品没有绑定 QQ
- 手工创建商品时也可能暂时不填

##### Alembic 迁移
为什么不能只改 `models.py`？

因为改模型只会改变 Python 代码，不会自动改数据库表结构。

数据库要真正多出这一列，必须通过迁移执行：

```bash
alembic upgrade head
```

---

### 4.2 API 层：让商品 CRUD 正式支持 `user_qq`

#### 文件
- `app/routers/products.py`

#### 做了什么

严格说，这个文件我没有大改业务结构。

原因是你现有写法本来就已经非常适合这个扩展：

创建商品：
```python
db_product = models.Product.from_orm(product)
```

更新商品：
```python
product_data = product_update.dict(exclude_unset=True)
for field, value in product_data.items():
    setattr(db_product, field, value)
```

因为 schema 已经包含 `user_qq`，所以：
- 创建时会自动带进去
- 更新时会自动支持修改它
- 读取列表 / 详情时响应模型也会自动返回它

#### 为什么这里几乎不用改

因为你的路由层采用的是“schema 驱动”的写法。

意思是：
- 请求体由 schema 定义
- ORM 对象从 schema 转换而来
- 更新逻辑按传入字段遍历赋值

这种写法的好处就是：
**以后扩一个普通字段，往往只需要改 schema 和 model，路由层就能自动跟上。**

#### 你现在打开 `app/routers/products.py` 应该重点看什么

建议你重点看两处：

1. `create_product()`
   - 看 `models.Product.from_orm(product)`
   - 理解“为什么 schema 里多了字段，这里就能自动保存”

2. `update_product()`
   - 看 `product_update.dict(exclude_unset=True)`
   - 理解“为什么不需要为 `user_qq` 单独写 if 分支”

#### 技术点：局部更新

`exclude_unset=True` 的含义是：
- 只拿用户这次真正传了的字段
- 没传的字段不动

比如：

```json
{
  "user_qq": "123456"
}
```

那么更新时只会改 `user_qq`，不会把别的字段清空。

这就是典型的 partial update / patch-like 行为。

---

### 4.3 Bot 添加商品时，自动绑定发起人 QQ

#### 文件
- `bot/src/plugins/price_monitor.py`

#### 做了什么

在 `/添加商品` 命令里增加：

```python
user_qq = str(event.get_user_id())
```

然后在请求后端时，把它一起发给：

```python
json={
    "name": name,
    "url": url,
    "platform": "steam",
    "target_price": target_price,
    "user_qq": user_qq,
}
```

成功响应里也把绑定结果展示出来：

```python
绑定 QQ: {data.get('user_qq', user_qq)}
```

#### 这一步为什么关键

这是“精确通知”闭环里最关键的一跳之一。

因为如果商品从创建那一刻就没记住“是谁创建的”，后面就无从定向通知。

现在逻辑变成：

1. QQ 用户发 `/添加商品`
2. NoneBot 收到事件
3. 从事件对象里拿到发起人的 QQ
4. 调后端创建商品时，把 `user_qq` 一起传过去
5. 数据库保存这个绑定关系

#### 这里用到的技术

##### NoneBot 事件对象
`event.get_user_id()` 是 NoneBot / OneBot 事件对象提供的能力。

它代表：
- 当前这条消息是谁发的

对于你的业务来说，这个值就是最天然的商品归属人。

##### httpx.AsyncClient
bot 不是直接连数据库，而是通过 HTTP 请求调用后端 API：

```python
async with httpx.AsyncClient() as client:
```

这是一个典型的“bot 作为前端/客户端，FastAPI 作为后端服务”的结构。

优点：
- bot 和后端解耦
- bot 不需要知道数据库细节
- 所有商品逻辑统一走后端 API

---

### 4.4 价格检查任务：把 `user_qq` 带入提醒消息

#### 文件
- `app/tasks/price_checker.py`

#### 做了什么

在价格达标时，原来调用：

```python
await NotificationService.publish_price_alert(...)
```

现在额外传：

```python
user_qq=product.user_qq
```

也就是：
- 商品对象上有什么 `user_qq`
- 通知发布时就带什么 `user_qq`

#### 这里的业务意义

`check_product_price()` 是“商品数据”进入“通知系统”的桥。

前面都是商品领域：
- 商品信息
- 当前价格
- 目标价格
- 历史记录

从这一步开始，数据被转换成“通知事件”。

而 `user_qq` 恰好就是通知事件路由所必需的信息。

所以最合理的做法，就是在这里把它一起塞进消息。

#### 你应该怎么理解这个函数

`check_product_price()` 干的事情其实可以拆成 5 步：

1. 调 scraper 抓当前价格
2. 更新商品当前价格和最后检查时间
3. 写一条价格历史
4. 判断是否达到提醒阈值
5. 如果达到，就发布通知

而这次改造只影响第 5 步：
- 以前发“普通提醒”
- 现在发“带目标接收人的提醒”

所以这次改动没有破坏主链路结构，只是增强了事件内容。

---

### 4.5 通知服务：统一发布带 `user_qq` 的 Redis 消息

#### 文件
- `app/notifications.py`

#### 做了什么

`publish_price_alert()` 签名新增参数：

```python
user_qq: Optional[str] = None
```

发布的消息体新增字段：

```python
"user_qq": user_qq,
```

日志中也补充了：

```python
user_qq=%s
```

#### 为什么这里是核心收口点

`NotificationService.publish_price_alert()` 是当前系统里统一的通知发布入口。

也就是说：
- 无论提醒从哪来
- 最后只要要发价格提醒
- 都应该走这里

所以这里只要定义好了消息结构，下游消费者就都能统一按这个结构处理。

这是一种很标准的“事件发布中心”设计。

#### Redis 消息现在长什么样

现在 price alert 消息大致是：

```json
{
  "type": "price_alert",
  "product_id": 1,
  "product_name": "Test Game",
  "platform": "steam",
  "url": "https://example.com/game",
  "current_price": 49.99,
  "target_price": 50.0,
  "trigger_reason": "target_price_reached",
  "user_qq": "123456",
  "timestamp": "2026-04-09T00:00:00"
}
```

#### 技术点：Redis Pub/Sub

这里采用的是 Redis 发布订阅模型：

- 发布者：后端 `NotificationService`
- 频道：`price_alerts`
- 订阅者：bot 或 subscriber

优点：
- 发布端和消费端解耦
- 后端不关心谁在接消息
- 以后还能增加更多消费者

比如：
- bot 发 QQ
- subscriber 打日志
- 未来邮件服务也可以订阅同一频道

---

### 4.6 手工测试通知接口：兼容无 `user_qq` 情况

#### 文件
- `app/routers/tasks.py`

#### 做了什么

`POST /api/tasks/test-notification` 调用发布接口时，显式传：

```python
user_qq=None
```

#### 为什么要这么做

因为测试通知不是某个真实商品触发的，它没有天然的归属用户。

所以这里明确表示：
- 这是一个没有绑定接收人的通知
- 下游 bot 应该走 fallback 逻辑

这样你就能继续保留：
- 管理员手工发一条测试消息
- 看 bot 是否正常收发

而不会因为新加了 `user_qq` 字段就把测试链路搞坏。

---

### 4.7 Bot 消费端：从广播改为定向发送优先

#### 文件
- `bot/src/plugins/price_alert.py`

#### 做了什么

原来逻辑：
- 遍历 `SUPERUSERS`
- 给所有超级用户都发一遍

现在逻辑：

```python
user_qq = data.get("user_qq")
if user_qq:
    target_user_ids = [str(user_qq)]
else:
    target_user_ids = [str(user_id) for user_id in SUPERUSERS]
```

然后统一遍历 `target_user_ids` 发送私聊。

#### 为什么这样设计

这是这次改动最核心的行为变化：

##### 情况 1：消息里有 `user_qq`
说明这是一个已经绑定商品归属人的真实提醒。

那么就：
- 只发给这个 QQ
- 不广播给别人

##### 情况 2：消息里没有 `user_qq`
说明它可能是：
- 老数据
- 手工测试通知
- 未绑定商品

那么就：
- 回退到原来的 `SUPERUSERS`
- 保证系统兼容、不至于完全失效

#### 这为什么叫 fallback

fallback 就是“主方案失败或缺失时的兜底方案”。

你的系统现在的主方案是：
- 精确定向发送

兜底方案是：
- 发给 `SUPERUSERS`

这是一个非常实用的过渡设计。

它既完成了新需求，也避免了：
- 旧商品全都收不到提醒
- 测试接口突然失效

#### 技术点：消费者路由逻辑

这里本质上是一个消息路由规则：

- 如果事件中自带目标接收人，就按事件路由
- 否则按系统默认配置路由

这种设计在消息系统里非常常见。

---

## 5. 这次没有大改，但为什么依然是完整闭环

这次改造看起来代码量不算特别大，但它其实把一个完整闭环补齐了。

### 旧闭环
1. 用户加商品
2. 商品被监控
3. 达标后发通知
4. bot 收到通知
5. bot 广播给管理员

### 新闭环
1. 用户在 QQ 中加商品
2. bot 自动记录这个用户的 QQ 号
3. 商品保存 `user_qq`
4. 价格检查触发提醒
5. Redis 消息携带 `user_qq`
6. bot 收到消息后识别目标 QQ
7. bot 只给对应用户发送私聊

所以本次真正完成的是：

**从“价格提醒能发出去”升级到“价格提醒能发给正确的人”。**

---

## 6. 这次改动涉及到的技术栈，分别起什么作用

---

### 6.1 FastAPI
用于提供 HTTP API，例如：
- `POST /api/products/`
- `GET /api/products/{id}`
- `PUT /api/products/{id}`
- `POST /api/tasks/check-prices`
- `POST /api/tasks/test-notification`

它是整个系统的后端入口。

这次改造里，FastAPI 的作用是：
- 接收 bot 创建商品时传来的 `user_qq`
- 对外暴露商品 CRUD
- 提供任务触发接口

---

### 6.2 SQLModel
用于定义：
- 数据库表模型
- API schema 风格的数据结构

在这个项目里：
- `app/models.py` 偏数据库层
- `app/schemas.py` 偏 API 层

这次改造里，它的作用是：
- 给 `Product` 增加 `user_qq`
- 让请求和响应模型都能理解这个字段

---

### 6.3 Alembic
用于数据库迁移。

它负责把“代码里的表结构变化”真正应用到数据库里。

这次改造里，它的作用是：
- 给 `product` 表新增 `user_qq` 列

如果没有 Alembic，代码虽然写了 `user_qq`，数据库里却没有这列，运行时会报错。

---

### 6.4 Redis Pub/Sub
用于通知发布与消费。

发布者把消息发到频道，消费者订阅频道后收到消息。

这次改造里，它的作用是：
- 把提醒事件从后端传给 bot
- 并把 `user_qq` 一起带过去

---

### 6.5 NoneBot2
用于实现 QQ bot 逻辑。

这次改造里，它的作用是：
- 接收 QQ 用户的 `/添加商品` 命令
- 从消息事件里拿到发起人的 QQ
- 订阅 Redis 提醒并调用 OneBot 发私聊

---

### 6.6 httpx
用于 bot 调后端 API。

bot 并不直接写数据库，而是用 HTTP 调用 FastAPI：

- 添加商品
- 查询商品
- 删除商品
- 手动触发检查

这是一个很典型的服务边界设计。

---

## 7. 我具体新增 / 修改了哪些文件

## 新增
- `alembic/versions/20260409_0003_add_user_qq_to_product.py`
- `tests/test_product_routes.py`
- `tests/test_bot_price_alert.py`

## 修改
- `app/models.py`
- `app/schemas.py`
- `app/notifications.py`
- `app/tasks/price_checker.py`
- `app/routers/tasks.py`
- `bot/src/plugins/price_monitor.py`
- `bot/src/plugins/price_alert.py`
- `README.md`
- `bot/README.md`
- `docs/deployment/nonebot2-setup.md`
- `docs/project/implementation-progress.md`
- 以及现有测试文件：
  - `tests/test_notifications.py`
  - `tests/test_price_checker.py`
  - `tests/test_task_routes.py`

---

## 8. 测试层我补了什么，为什么这样补

### 8.1 `tests/test_product_routes.py`
验证：
- 创建商品时 `user_qq` 能被保存
- 更新商品时 `user_qq` 能被修改

目的：
- 保证 API 层真的接住了这个字段

### 8.2 `tests/test_price_checker.py`
验证：
- 价格达标时调用 `publish_price_alert`
- 并且传出了 `user_qq`

目的：
- 保证商品上的归属 QQ 能进入通知链路

### 8.3 `tests/test_notifications.py`
验证：
- 发布到 Redis 的消息 payload 里包含 `user_qq`

目的：
- 保证通知消息结构已经升级

### 8.4 `tests/test_task_routes.py`
验证：
- 手工测试通知仍然会调用统一发布入口
- 并且 `user_qq` 为 `None`

目的：
- 保证 fallback 测试路径还可用

### 8.5 `tests/test_bot_price_alert.py`
验证两条关键行为：

1. 有 `user_qq` 时，只给这个 QQ 发
2. 没有 `user_qq` 时，回退给 `SUPERUSERS`

目的：
- 保证最终“发给谁”这件事符合设计

---

## 9. 你现在如果想真正理解，建议这样看代码

我建议你按下面方式逐段看，不要一上来就试图看全项目。

### 第一步：理解字段为什么加在商品上
看：
- `app/models.py`
- `app/schemas.py`
- `alembic/versions/20260409_0003_add_user_qq_to_product.py`

你要回答自己两个问题：
1. 为什么 `user_qq` 放在 `Product` 上最合理？
2. 为什么要做成 nullable？

### 第二步：理解 API 为什么几乎不用大改
看：
- `app/routers/products.py`

你要重点理解：
- schema 驱动 + ORM 转换
- partial update 的通用写法

### 第三步：理解通知主链路
看：
- `app/tasks/price_checker.py`
- `app/notifications.py`

你要重点理解：
- 商品数据怎样变成提醒事件
- Redis 消息是怎样组织的

### 第四步：理解 bot 两个插件的分工
看：
- `bot/src/plugins/price_monitor.py`
- `bot/src/plugins/price_alert.py`

分工其实很清楚：

#### `price_monitor.py`
负责“商品管理命令”
- 接收用户命令
- 调后端 API
- 添加商品时绑定 `user_qq`

#### `price_alert.py`
负责“通知消费与发送”
- 订阅 Redis
- 解析提醒消息
- 决定发给谁

### 第五步：最后看测试
测试不是附属物，而是帮你确认理解最直接的材料。

---

## 10. 现在这套设计的优点是什么

### 优点 1：改动小
没有引入用户表，没有重构通知系统，没有新增复杂关系。

### 优点 2：兼容老数据
老商品没有 `user_qq` 也不会崩，仍能 fallback。

### 优点 3：职责清晰
- 商品归属：数据库存
- 通知发布：后端发 Redis
- 通知执行：bot 按消息发送

### 优点 4：后续可扩展
未来如果你要支持：
- 一个商品绑定多个 QQ
- 绑定群号
- 绑定邮箱 / Telegram
- 用户订阅表

都可以在现在这个最小闭环基础上继续演进。

---

## 11. 现在还没做、但未来可能会做的优化

下面这些不是这次必须做的，但你以后可能会遇到：

### 11.1 把 `user_qq` 升级成正式用户模型
现在只是最小字段方案。

以后如果你想做：
- 用户管理
- 权限控制
- 一个用户多个商品
- 一个商品多个订阅者

就可能要引入 `User` 表或 `ProductSubscription` 表。

### 11.2 替换掉旧的 SQLModel 写法
当前 `app/routers/products.py` 里还有：
- `from_orm`
- `dict(exclude_unset=True)`

它们现在可用，但已经有 deprecation warning。

后面可以换成新版写法：
- `model_validate`
- `model_dump`

### 11.3 增加更完整的 API 集成测试
现在测试主要是单元测试和 mock 测试。

以后可以补：
- 真正起 FastAPI test client
- 真正打接口
- 更完整地验证数据库读写

---

## 12. 最后给你一个最实用的理解方式

如果你只想抓住这次改动的本质，请记住下面这句话：

> 这次改造不是在“增加一个字段”，而是在把“通知接收人”从 bot 配置提升为商品业务数据，并让这个数据沿着已有通知链路完整传递到最终发送端。

所以你理解这次改动时，不要只盯着 `user_qq` 三个字。

你真正要理解的是：

1. **业务归属信息应该存在哪一层**
2. **一条业务数据如何穿过 API、任务、消息队列、消费者，最后影响外部行为**

这才是这次改造最有价值的地方。

---

## 13. 推荐你的阅读顺序（最终版）

按这个顺序看最顺：

1. `app/models.py`
2. `app/schemas.py`
3. `alembic/versions/20260409_0003_add_user_qq_to_product.py`
4. `app/routers/products.py`
5. `bot/src/plugins/price_monitor.py`
6. `app/tasks/price_checker.py`
7. `app/notifications.py`
8. `bot/src/plugins/price_alert.py`
9. `tests/test_product_routes.py`
10. `tests/test_price_checker.py`
11. `tests/test_notifications.py`
12. `tests/test_bot_price_alert.py`

如果你按这个顺序看，你会看到一条非常清晰的数据流：

**QQ 用户 -> bot 命令 -> FastAPI -> 数据库商品 -> 价格检查 -> Redis 消息 -> bot 消费 -> 私聊发送**

这条链路就是这次改造的全部核心。
