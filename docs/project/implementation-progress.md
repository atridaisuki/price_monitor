# 项目实施进度

## 当前目标
按既定顺序推进以下主线，并在每完成一部分后同步更新本文件：

1. 阶段 1：确认并补齐价格检查主链路
2. 阶段 2：把通知闭环做成最小可用版本
3. 阶段 3：验证 bot / napcat 链路，只保留一个主通知通道
4. 阶段 4：补配置样例、最小测试和启动说明
5. 阶段 5：引入 Alembic 迁移并完善部署收口

---

## 阶段 1：价格检查主链路

### 目标
打通这条最小闭环：

`POST /api/tasks/check-prices -> check_all_prices -> 抓取价格 -> 更新商品/历史 -> publish_price_alert -> subscriber 消费`

### 已完成
- 已将 `check_all_prices` 收口为单一入口：`app/tasks/price_checker.py`
- 已明确任务职责：读取商品、抓取价格、更新商品、写入 `PriceHistory`、按规则发布通知
- 已补充结构化执行结果，包含：
  - `total_products`
  - `success_count`
  - `failure_count`
  - `history_count`
  - `notification_count`
  - 每个商品的明细结果
- 已将 `POST /api/tasks/check-prices` 改为直接执行并返回 summary，便于联调验证：`app/routers/tasks.py`
- 已确定当前价格判定规则：
  - 每次成功检查都写入一条 `PriceHistory`
  - 当 `current_price <= target_price` 时发布提醒
  - 单个商品失败不阻断整批任务

### 当前状态
- 代码改造已完成
- 已通过基础语法校验
- 尚未完成真实服务联调验证

### 关键文件
- `app/tasks/price_checker.py`
- `app/routers/tasks.py`
- `app/models.py`
- `app/database.py`
- `app/scrapers/steam.py`

---

## 阶段 2：通知闭环最小可用版本

### 目标
让通知不只是发布到 Redis，而是有稳定消息结构和最小可用消费者。

### 已完成
- 已统一通知发布入口：`NotificationService.publish_price_alert()`
- 已统一通知订阅入口：`NotificationService.subscribe_price_alerts()`
- 已固定消息结构，包含：
  - `product_id`
  - `product_name`
  - `platform`
  - `url`
  - `current_price`
  - `target_price`
  - `trigger_reason`
  - `timestamp`
- 已将 `app/subscriber.py` 从示例脚本升级为最小可用消费者
- 已为 `POST /api/tasks/test-notification` 增加 `trigger_reason=manual_test`
- 已补最小自动化测试，覆盖通知发布结构、订阅回调和任务路由触发

### 当前状态
- 发布端与 subscriber 已对齐
- 自动化测试已覆盖最小通知闭环
- 真实 Redis 联调尚待本地 Docker 恢复后再完成

### 关键文件
- `app/notifications.py`
- `app/subscriber.py`
- `app/redis_client.py`
- `app/routers/tasks.py`
- `tests/test_notifications.py`
- `tests/test_task_routes.py`

---

## 阶段 3：bot / napcat 链路评估

### 目标
判断 bot / napcat 是否已经稳定到足以成为主通知通道；若未稳定，则先以 Redis + subscriber 为主线。

### 已完成
- 已检查 `docker-compose.yml`，Compose 配置可正常解析
- 已确认 `bot/bot.py`、`bot/src/plugins/price_alert.py`、`bot/src/plugins/price_monitor.py` 均可通过基础编译校验
- 已确认 `bot/` 具备真实运行入口、插件目录、Dockerfile 与项目配置
- 已确认 `napcat/` 当前主要是配置目录，不是独立业务逻辑目录
- 已将 bot 侧 `/检查价格` 指令对齐新的后端返回结构，能够显示本次检查 summary
- 已收口 `bot/README.md`、`docs/getting-started/napcat-setup.md`、`docs/deployment/nonebot2-setup.md`、`docs/deployment/nonebot2-complete-guide.md` 中与当前实现不一致的配置与启动说明

### 当前发现
- `bot/` 目录已存在可运行插件与项目配置
- `napcat/` 目录当前主要是配置目录
- `docker-compose.yml` 已定义 `bot` 与 `napcat` 服务
- bot 的价格提醒插件基于 Redis 订阅，方向上与当前主链路一致
- 仓库内现有 `bot/.env` / `bot/.env.prod` 含真实敏感配置，后续应改为样例文件驱动，避免继续依赖已提交的环境文件
- 已补商品 `user_qq` 字段，并打通 `POST /api/tasks/check-prices -> publish_price_alert -> bot consumer` 的精确接收人传递
- bot 现在会优先向商品绑定的 `user_qq` 发送私聊；仅在未绑定商品或手工测试通知时回退到 `SUPERUSERS`

### 暂定判断
- `Redis + subscriber` 主链路已稳定
- bot 价格提醒已具备最小可用的精确通知能力：商品可绑定单一 `user_qq`，bot 添加商品时会自动绑定发起人 QQ，提醒优先定向私聊
- `SUPERUSERS` 仍保留为未绑定商品与手工测试通知的 fallback
- 后续重点转为真实 QQ 长稳联调与部署收口，而不是继续扩展通知模型复杂度
- 阶段 4 已完成配置样例与主要文档收口，后续以补充生产部署细节为主

---

## 阶段 4：配置样例、最小测试和启动说明

### 目标
让项目从“本机作者能跑”推进到“按文档即可完成最小验证”。

### 已完成
- 已新增根目录配置样例：`.env.example`
- 已新增 bot 配置样例：`bot/.env.example`
- 已新增根目录启动说明：`README.md`
- 已将 bot 文档改为优先使用 `.env.example`，不再引导直接依赖已提交环境文件
- 已在 README 中补充：
  - 本地启动步骤
  - Docker Compose 启动方式
  - 最小接口验证流程
  - 自动化测试运行命令
  - 当前已知限制说明

### 当前状态
- 阶段 4 的“配置样例 + 最小启动说明”已完成首版收口
- 真实服务联调仍受本机 Docker / Redis / PostgreSQL 可用性限制
- 后续还可以继续细化 README，但当前已具备最小可用说明

### 关键文件
- `README.md`
- `.env.example`
- `bot/.env.example`
- `bot/README.md`
- `docs/project/implementation-progress.md`

---

## 阶段 5：Alembic 迁移与部署收口

### 目标
让数据库结构变更具备明确迁移入口，逐步替代正式环境长期依赖 `create_all` 的方式。

### 已完成
- 已新增 Alembic 基础配置：`alembic.ini`
- 已新增 Alembic 环境脚本：`alembic/env.py`
- 已新增版本目录：`alembic/versions/`
- 已补首个基线迁移：`alembic/versions/20260408_0001_initial_schema.py`
- 已补数据库修复迁移：`alembic/versions/20260408_0002_rename_currunt_price_column.py`
- 已在 README 中补充迁移命令与使用说明
- 已明确并落地当前迁移策略：
  - 默认 `DB_INIT_MODE=migrate_only`
  - 应用启动时不再无条件执行 `create_all`
  - 仅在空开发库快速初始化时才显式使用 `DB_INIT_MODE=create_all`

### 当前状态
- 阶段 5 已完成 Alembic 首版接入
- 已在真实数据库上完成一次修复迁移验证：`20260408_0001 -> 20260408_0002`
- 应用启动已切为迁移优先：默认不再自动执行 `create_all`
- 仍保留 `DB_INIT_MODE=create_all` 作为空开发库的显式兜底开关

### 关键文件
- `alembic.ini`
- `alembic/env.py`
- `alembic/versions/20260408_0001_initial_schema.py`
- `app/database.py`
- `README.md`

---

## 下一步执行顺序
1. 继续观察 bot / napcat 是否需要从增强通道转为主通道
2. 继续补部署收口与生产启动说明
3. 视后续需要再决定是否彻底删除 `DB_INIT_MODE=create_all` 开发兜底

---

## 最近一次更新
- 已完成阶段 1 核心代码收口
- 已完成阶段 2 的消息结构统一与 subscriber 最小可用实现
- 已补最小自动化测试并通过：`python -m unittest discover -s tests -p "test_*.py"`
- 已新增商品 `user_qq` 字段与 Alembic 迁移：`20260409_0003_add_user_qq_to_product.py`
- 已让商品 CRUD 支持创建、读取、更新 `user_qq`
- 已让 bot `/添加商品` 自动绑定发起命令的 QQ 号
- 已让价格提醒消息沿现有链路携带 `user_qq`，并让 bot 优先定向私聊、缺失时 fallback 到 `SUPERUSERS`
- 已新增针对 `user_qq` 传递与 bot 定向发送的自动化测试
- 已确认 Alembic head 为 `20260409_0003`
- 已继续收口部署文档：`docs/getting-started/development.md`、`docs/deployment/docker-deployment.md` 已对齐迁移优先启动流程
- 已继续清理文档残留：修正 `docs/study/interview-prep.md` 中过时的 Redis 服务名，并将 `docs/deployment/docker-deployment.md` 中剩余旧 `docker-compose` 命令表述切到当前写法
