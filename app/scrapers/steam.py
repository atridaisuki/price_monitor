"""Steam 平台价格爬虫 — 基于 Steam Web API"""
import re
import httpx
from app.scrapers.base import BaseScraper
from app.scrapers.exceptions import FetchException, ParseException, PriceNotFoundException


class SteamScraper(BaseScraper):
    """Steam 商店价格爬虫，通过 appdetails API 获取价格"""

    STEAM_STORE_DOMAIN = "store.steampowered.com"
    API_URL = "https://store.steampowered.com/api/appdetails"

    def is_valid_url(self, url: str) -> bool:
        """验证是否为 Steam 商店 URL"""
        return self.STEAM_STORE_DOMAIN in url

    def _extract_app_id(self, url: str) -> str:
        """从 Steam URL 中提取 app_id"""
        match = re.search(r'/app/(\d+)', url)
        if not match:
            raise FetchException(f"Cannot extract app_id from URL: {url}")
        return match.group(1)

    async def scrape(self, url: str) -> float:
        """通过 Steam API 获取商品价格"""
        if not self.is_valid_url(url):
            raise FetchException(f"Invalid Steam URL: {url}")

        app_id = self._extract_app_id(url)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    self.API_URL,
                    params={"appids": app_id, "cc": "cn", "l": "schinese"},
                )
                response.raise_for_status()
                data = response.json()
        except httpx.RequestError as e:
            raise FetchException(f"Failed to fetch Steam API: {e}")

        app_data = data.get(app_id)
        if not app_data or not app_data.get("success"):
            raise FetchException(f"Steam API returned no data for app {app_id}")

        price_overview = app_data.get("data", {}).get("price_overview")
        if not price_overview:
            # 可能是免费游戏或未上架
            if app_data.get("data", {}).get("is_free"):
                return 0.0
            raise PriceNotFoundException(f"No price info for app {app_id}")

        # final_formatted 示例: "¥ 298.00"，final 是分为单位的整数: 29800
        final = price_overview.get("final")
        if final is not None:
            return final / 100.0

        raise ParseException("Unexpected price_overview format")
