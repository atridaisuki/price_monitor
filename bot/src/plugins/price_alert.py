"""
价格提醒插件

订阅 Redis 通知并发送 QQ 消息
"""
from nonebot.plugin import PluginMetadata

__plugin_meta__ = PluginMetadata(
    name="价格提醒",
    description="自动推送价格达标通知",
    usage="自动运行，无需手动操作",
    type="application",
    homepage="https://github.com/yourusername/price-monitor",
    supported_adapters={"~onebot.v11"},
)

import json
import asyncio
import redis.asyncio as redis
from nonebot import get_driver, get_bot, logger
from nonebot.adapters.onebot.v11 import Bot, MessageSegment

# 获取配置
config = get_driver().config
REDIS_URL = getattr(config, "redis_url", "redis://redis:6379")
SUPERUSERS = getattr(config, "superusers", [])
PRICE_ALERT_CHANNEL = "price_alerts"

# Redis 客户端
redis_client = None
subscription_task = None


async def subscribe_price_alerts():
    """订阅价格提醒通知"""
    global redis_client

    retry_count = 0
    max_retries = 5

    while retry_count < max_retries:
        try:
            redis_client = redis.from_url(
                REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )

            # 测试连接
            await redis_client.ping()
            logger.success(f"Redis 连接成功: {REDIS_URL}")

            # bot 自己也订阅 price alert
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(PRICE_ALERT_CHANNEL)
            logger.success(f"已订阅 Redis 频道: {PRICE_ALERT_CHANNEL}")

            # 重置重试计数
            retry_count = 0

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        # 解析消息
                        data = json.loads(message["data"])
                        logger.info(f"收到价格提醒: {data['product_name']}")

                        # 发送 QQ 消息
                        await send_price_alert(data)

                    except json.JSONDecodeError as e:
                        logger.error(f"消息解析失败: {e}")
                    except Exception as e:
                        logger.error(f"处理消息失败: {e}")

        except redis.ConnectionError as e:
            retry_count += 1
            logger.warning(f"Redis 连接失败 ({retry_count}/{max_retries}): {e}")

            if retry_count < max_retries:
                wait_time = min(2 ** retry_count, 60)  # 指数退避，最多60秒
                logger.info(f"等待 {wait_time} 秒后重试...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Redis 连接失败次数过多，停止重试")
                break

        except asyncio.CancelledError:
            logger.info("订阅任务被取消")
            break

        except Exception as e:
            logger.error(f"订阅价格提醒失败: {e}")
            await asyncio.sleep(5)

        finally:
            if redis_client:
                try:
                    await redis_client.close()
                except:
                    pass
                redis_client = None


async def send_price_alert(data: dict):
    """发送价格提醒到 QQ"""
    try:
        bot: Bot = get_bot()

        # 构造消息
        message = MessageSegment.text(
            f"🎉 价格提醒！\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"商品: {data['product_name']}\n"
            f"当前价格: ¥{data['current_price']}\n"
            f"目标价格: ¥{data['target_price']}\n"
            f"平台: {data['platform']}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"链接: {data['url']}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"快去购买吧！💰"
        )

        user_qq = data.get("user_qq")
        if user_qq:
            target_user_ids = [str(user_qq)]
            logger.info(f"价格提醒将定向发送给 QQ: {user_qq}")
        else:
            target_user_ids = [str(user_id) for user_id in SUPERUSERS]
            logger.info("价格提醒未携带 user_qq，回退到 SUPERUSERS 广播")

        success_count = 0
        for user_id in target_user_ids:
            try:
                await bot.send_private_msg(
                    user_id=int(user_id),
                    message=message
                )
                success_count += 1
                logger.success(f"价格提醒已发送给用户: {user_id}")
            except Exception as e:
                logger.error(f"发送消息给用户 {user_id} 失败: {e}")

        if success_count > 0:
            logger.info(f"价格提醒发送完成，成功 {success_count}/{len(target_user_ids)} 个用户")
        else:
            logger.warning("价格提醒发送失败，没有成功发送给任何用户")

    except ValueError as e:
        logger.error(f"获取 Bot 实例失败: {e}")
        logger.warning("机器人可能尚未连接，请检查 OneBot 适配器配置")
    except Exception as e:
        logger.error(f"发送价格提醒失败: {e}")


@get_driver().on_startup
async def start_subscription():
    """启动时开始订阅"""
    global subscription_task

    logger.info("正在启动价格提醒订阅...")

    # 延迟启动，等待机器人完全初始化
    await asyncio.sleep(3)

    subscription_task = asyncio.create_task(subscribe_price_alerts())
    logger.success("价格提醒订阅任务已启动")


@get_driver().on_shutdown
async def stop_subscription():
    """关闭时停止订阅"""
    global subscription_task, redis_client

    logger.info("正在停止价格提醒订阅...")

    if subscription_task:
        subscription_task.cancel()
        try:
            await subscription_task
        except asyncio.CancelledError:
            pass

    if redis_client:
        try:
            await redis_client.close()
        except:
            pass
        redis_client = None

    logger.success("价格提醒订阅已停止")
