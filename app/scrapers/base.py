"""爬虫抽象基类"""
from abc import ABC, abstractmethod
from app.scrapers.exceptions import ScraperException


class BaseScraper(ABC):
    """爬虫抽象基类，定义统一的接口规范"""

    @abstractmethod
    async def scrape(self, url: str) -> float:
        """
        抓取商品价格

        Args:
            url: 商品页面 URL

        Returns:
            商品价格（浮点数）

        Raises:
            FetchException: HTTP 请求失败
            ParseException: HTML 解析失败
            PriceNotFoundException: 价格未找到
        """
        pass

    @abstractmethod
    def is_valid_url(self, url: str) -> bool:
        """
        验证 URL 是否属于该平台

        Args:
            url: 待验证的 URL

        Returns:
            True 如果 URL 属于该平台，否则 False
        """
        pass
