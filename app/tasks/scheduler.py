"""定时任务调度器"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# 创建调度器实例
scheduler = AsyncIOScheduler()


def start_scheduler():
    """启动定时任务调度器"""
    from app.tasks.price_checker import check_all_prices

    # 添加价格检查任务（每 30 分钟执行一次）
    scheduler.add_job(
        check_all_prices, # 这个就是调用price checker的那个方法
        trigger=IntervalTrigger(minutes=30),
        id="check_all_prices",
        name="检查所有商品价格",
        replace_existing=True,
    )

    # 启动调度器
    scheduler.start()
    logger.info("定时任务调度器已启动")
    logger.info("价格检查任务将每 30 分钟执行一次")


def shutdown_scheduler():
    """关闭定时任务调度器"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("定时任务调度器已关闭")
