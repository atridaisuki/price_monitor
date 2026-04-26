"""通知服务模块"""
import json
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Optional

from app.redis_client import get_redis

logger = logging.getLogger(__name__)

# Redis 频道名称
PRICE_ALERT_CHANNEL = "price_alerts"


class NotificationService:
    """通知服务类"""

    @staticmethod
    async def publish_price_alert(
        product_id: int,
        product_name: str,
        current_price: float,
        target_price: float,
        url: str,
        platform: str = "steam",
        trigger_reason: str = "target_price_reached",
        user_qq: Optional[str] = None,
    ) -> bool:
        """发布价格提醒通知"""
        try:
            #获取redis客户端
            redis_client = await get_redis()

            #组装消息体
            message = {
                "type": "price_alert",
                "product_id": product_id,
                "product_name": product_name,
                "platform": platform,
                "url": url,
                "current_price": current_price,
                "target_price": target_price,
                "trigger_reason": trigger_reason,
                "user_qq": user_qq,
                "timestamp": datetime.now().isoformat(),
            }

            #publish
            subscribers = await redis_client.publish(
                PRICE_ALERT_CHANNEL,
                json.dumps(message, ensure_ascii=False),
            )

            logger.info(
                "价格提醒已发布: product_id=%s, name=%s, current=%s, target=%s, reason=%s, user_qq=%s, subscribers=%s",
                product_id,
                product_name,
                current_price,
                target_price,
                trigger_reason,
                user_qq,
                subscribers,
            )
            return True

        except Exception as e:
            logger.exception("发布价格提醒失败: %s", e)
            return False

    @staticmethod
    async def subscribe_price_alerts(
        callback: Callable[[Dict[str, Any]], Awaitable[None]],
    ):
        """订阅价格提醒通知"""
        pubsub = None
        try:
            redis_client = await get_redis()
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(PRICE_ALERT_CHANNEL)
            logger.info("已订阅频道: %s", PRICE_ALERT_CHANNEL)

            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue

                try:
                    data = json.loads(message["data"])
                    logger.info(
                        "收到价格提醒: product_id=%s, name=%s, reason=%s, user_qq=%s",
                        data.get("product_id"),
                        data.get("product_name"),
                        data.get("trigger_reason"),
                        data.get("user_qq"),
                    )
                    await callback(data)
                except json.JSONDecodeError as e:
                    logger.error("消息解析失败: %s", e)
                except Exception:
                    logger.exception("处理消息失败")

        except Exception:
            logger.exception("订阅价格提醒失败")
            raise
        finally:
            if pubsub is not None:
                await pubsub.close()
