"""价格检查任务"""
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app import models
from app.database import async_session_maker
from app.notifications import NotificationService
from app.scrapers import get_scraper
from app.scrapers.exceptions import ScraperException

logger = logging.getLogger(__name__)


@dataclass
class ProductCheckResult:
    """单个商品检查结果"""

    product_id: int
    product_name: str
    platform: str
    status: str
    current_price: Optional[float] = None
    previous_price: Optional[float] = None
    target_price: Optional[float] = None
    history_written: bool = False
    notification_sent: bool = False
    error: Optional[str] = None


@dataclass
class PriceCheckSummary:
    """价格检查汇总结果"""

    started_at: str
    finished_at: Optional[str] = None
    total_products: int = 0
    success_count: int = 0
    failure_count: int = 0
    notification_count: int = 0
    history_count: int = 0
    results: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.results is None:
            self.results = []

    def add_result(self, result: ProductCheckResult):
        self.results.append(asdict(result))
        if result.status == "success":
            self.success_count += 1
        else:
            self.failure_count += 1
        if result.history_written:
            self.history_count += 1
        if result.notification_sent:
            self.notification_count += 1

    def finish(self):
        self.finished_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


async def check_all_prices() -> Dict[str, Any]:
    """检查所有商品的价格并返回可观测结果"""
    logger.info("开始检查所有商品价格...")
    summary = PriceCheckSummary(started_at=datetime.now().isoformat())

    async with async_session_maker() as session:
        result = await session.execute(select(models.Product))
        products: List[models.Product] = result.scalars().all()
        summary.total_products = len(products)

        if not products:
            logger.info("没有需要检查的商品")
            summary.finish()
            return summary.to_dict()

        logger.info("找到 %s 个商品需要检查", len(products))

        for product in products:
            product_result = await check_product_price(product, session)
            summary.add_result(product_result)

        await session.commit()
        summary.finish()

    logger.info(
        "价格检查完成，总数=%s，成功=%s，失败=%s，历史记录=%s，通知=%s",
        summary.total_products,
        summary.success_count,
        summary.failure_count,
        summary.history_count,
        summary.notification_count,
    )
    return summary.to_dict()


async def check_product_price(
    product: models.Product,
    session: AsyncSession,
) -> ProductCheckResult:
    """检查单个商品价格并返回执行结果"""
    previous_price = product.current_price

    try:
        logger.info("检查商品: %s (ID: %s)", product.name, product.id)
        scraper = get_scraper(product.platform)
        new_price = await scraper.scrape(product.url)
        logger.info("商品 %s 当前价格: %s", product.name, new_price)

        product.current_price = new_price
        product.last_checked_time = datetime.now()

        price_history = models.PriceHistory(
            price=new_price,
            product_id=product.id,
        )
        session.add(price_history)

        notification_sent = False
        if new_price <= product.target_price:
            logger.warning(
                "商品 %s 价格达到目标，当前=%s，目标=%s",
                product.name,
                new_price,
                product.target_price,
            )
            notification_sent = await NotificationService.publish_price_alert(
                product_id=product.id,
                product_name=product.name,
                current_price=new_price,
                target_price=product.target_price,
                url=product.url,
                platform=product.platform,
                trigger_reason="target_price_reached",
                user_qq=product.user_qq,
            )

        return ProductCheckResult(
            product_id=product.id,
            product_name=product.name,
            platform=product.platform,
            status="success",
            current_price=new_price,
            previous_price=previous_price,
            target_price=product.target_price,
            history_written=True,
            notification_sent=notification_sent,
        )

    except ScraperException as e:
        logger.error("爬取商品 %s 价格失败: %s", product.name, e)
        return ProductCheckResult(
            product_id=product.id,
            product_name=product.name,
            platform=product.platform,
            status="failed",
            previous_price=previous_price,
            target_price=product.target_price,
            error=str(e),
        )
    except Exception as e:
        logger.exception("检查商品 %s 时发生未知错误", product.name)
        return ProductCheckResult(
            product_id=product.id,
            product_name=product.name,
            platform=product.platform,
            status="failed",
            previous_price=previous_price,
            target_price=product.target_price,
            error=str(e),
        )
