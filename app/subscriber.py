"""Redis 通知订阅者。"""
import asyncio
import logging

from app.notifications import NotificationService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def handle_price_alert(message: dict):
    """处理价格提醒消息。"""
    logger.info("=" * 60)
    logger.info("收到价格提醒通知")
    logger.info("商品 ID: %s", message["product_id"])
    logger.info("商品名称: %s", message["product_name"])
    logger.info("平台: %s", message["platform"])
    logger.info("链接: %s", message["url"])
    logger.info("当前价格: ¥%s", message["current_price"])
    logger.info("目标价格: ¥%s", message["target_price"])
    logger.info("触发原因: %s", message["trigger_reason"])
    logger.info("时间: %s", message["timestamp"])
    logger.info("通知消费完成")
    logger.info("=" * 60)


async def main():
    """启动最小可用通知消费者。"""
    logger.info("启动价格提醒订阅者...")
    logger.info("等待价格提醒通知...")

    try:
        await NotificationService.subscribe_price_alerts(handle_price_alert)
    except KeyboardInterrupt:
        logger.info("订阅者已停止")
    except Exception:
        logger.exception("订阅者运行出错")
        raise


if __name__ == "__main__":
    asyncio.run(main())
