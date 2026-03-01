"""Steam 平台价格爬虫"""
import re
import httpx
from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper
from app.scrapers.exceptions import FetchException, ParseException, PriceNotFoundException


class SteamScraper(BaseScraper):
    """Steam 商店价格爬虫"""

    # Steam 商店域名
    STEAM_STORE_DOMAIN = "store.steampowered.com"

    # 价格元素选择器（按优先级）
    PRICE_SELECTORS = [
        ".discount_final_price",      # 折扣价
        ".game_purchase_price",      # 原价
    ]

    def is_valid_url(self, url: str) -> bool:
        """验证是否为 Steam 商店 URL"""
        return self.STEAM_STORE_DOMAIN in url

    async def scrape(self, url: str) -> float:
        """抓取 Steam 商品价格"""
        if not self.is_valid_url(url):
            raise FetchException(f"Invalid Steam URL: {url}")

        try:
            # 获取页面内容
            html = await self._fetch_page(url)
            # 解析价格
            price = self._parse_price(html)
            return price

        except httpx.RequestError as e:
            raise FetchException(f"Failed to fetch page: {e}")
        except Exception as e:
            raise ParseException(f"Failed to parse price: {e}")

    async def _fetch_page(self, url: str) -> str:
        """异步获取页面内容"""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text

    def _parse_price(self, html: str) -> float:
        """从 HTML 中解析价格"""
        soup = BeautifulSoup(html, "lxml")

        # 按优先级查找价格元素
        price_element = None
        for selector in self.PRICE_SELECTORS:
            price_element = soup.select_one(selector)
            if price_element:
                break

        if not price_element:
            raise PriceNotFoundException("Price element not found in page")

        # 提取价格文本
        price_text = price_element.get_text(strip=True)

        # 解析价格（去除货币符号）
        price = self._extract_price_number(price_text)

        return price

    def _extract_price_number(self, text: str) -> float:
        """从价格文本中提取数字部分"""
        # 移除货币符号（¥, $, €, £ 等）和空格
        text = re.sub(r'[¥$€£\s]', '', text)

        # 提取数字（支持小数和千分位分隔符）
        match = re.search(r'[\d,]+\.?\d*', text)
        if not match:
            raise ParseException(f"Cannot extract price from: {text}")

        price_str = match.group().replace(',', '')

        try:
            return float(price_str)
        except ValueError:
            raise ParseException(f"Invalid price format: {price_str}")
