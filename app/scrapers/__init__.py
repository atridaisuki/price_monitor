"""爬虫模块 - 提供统一的价格抓取接口"""
from app.scrapers.base import BaseScraper
from app.scrapers.steam import SteamScraper


# 平台名称到爬虫类的映射
SCRAPER_MAP = {
    "steam": SteamScraper,
}


def get_scraper(platform_or_url: str) -> BaseScraper:
    """
    根据平台名称或 URL 获取对应的爬虫实例

    Args:
        platform_or_url: 平台名称（如 "steam"）或商品 URL

    Returns:
        对应平台的爬虫实例

    Raises:
        ValueError: 不支持的平台
    """
    # 如果是 URL，尝试从中提取平台名称
    if "/" in platform_or_url:
        # 检查是否为已知平台的 URL
        for platform, scraper_class in SCRAPER_MAP.items():
            test_scraper = scraper_class()
            if test_scraper.is_valid_url(platform_or_url):
                return test_scraper
        raise ValueError(f"Unsupported URL: {platform_or_url}")

    # 如果是平台名称，直接返回对应的爬虫
    platform = platform_or_url.lower()
    if platform not in SCRAPER_MAP:
        raise ValueError(f"Unsupported platform: {platform}. Supported: {list(SCRAPER_MAP.keys())}")

    return SCRAPER_MAP[platform]()


# 导出主要类和函数
__all__ = [
    "get_scraper",
    "BaseScraper",
    "SteamScraper",
]
