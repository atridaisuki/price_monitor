# 爬虫模块详解

> 本文档讲解项目中爬虫模块的实现原理、使用方法和扩展方式

---

## 目录

- [一、爬虫模块概览](#一爬虫模块概览)
- [二、文件结构](#二文件结构)
- [三、核心概念](#三核心概念)
- [四、实现详解](#四实现详解)
- [五、使用示例](#五使用示例)
- [六、扩展新平台](#六扩展新平台)
- [七、常见问题](#七常见问题)

---

## 一、爬虫模块概览

### 1. 可以直接用吗？

**是的，可以！** 爬虫模块已经完整实现，可以直接使用。

### 2. 前置条件

确保已安装以下依赖（`requirements.txt` 已包含）：

```bash
pip install httpx beautifulsoup4 lxml
```

| 依赖 | 用途 |
|------|------|
| `httpx` | 异步 HTTP 客户端 |
| `beautifulsoup4` | HTML 解析 |
| `lxml` | BeautifulSoup 的解析引擎 |

---

## 二、文件结构

```
app/scrapers/
├── __init__.py          # 模块入口，提供 get_scraper()
├── base.py              # 抽象基类，定义接口规范
├── exceptions.py        # 自定义异常
└── steam.py             # Steam 平台爬虫实现
```

---

## 三、核心概念

### 1. 抽象基类 (base.py)

**base.py 不是空白文件**！它定义了**接口规范**，确保所有爬虫都有统一的接口。

```python
from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """爬虫抽象基类"""

    @abstractmethod
    async def scrape(self, url: str) -> float:
        """抓取价格（子类必须实现）"""
        pass

    @abstractmethod
    def is_valid_url(self, url: str) -> bool:
        """验证 URL（子类必须实现）"""
        pass
```

**为什么需要抽象基类？**

| 优势 | 说明 |
|------|------|
| 统一接口 | 所有爬虫都有 `scrape()` 方法 |
| 类型提示 | IDE 可以提示可用方法 |
| 防止遗漏 | 子类必须实现所有抽象方法 |
| 易于扩展 | 新增平台只需继承基类 |

### 2. 自定义异常 (exceptions.py)

**exceptions.py 也不是空白**！定义了清晰的错误类型。

```python
class ScraperException(Exception):
    """爬虫基础异常"""
    pass

class FetchException(ScraperException):
    """HTTP 请求失败"""
    pass

class ParseException(ScraperException):
    """HTML 解析失败"""
    pass

class PriceNotFoundException(ScraperException):
    """价格未找到"""
    pass
```

**异常层次结构**：

```
Exception
    └── ScraperException (基础异常)
            ├── FetchException (请求失败)
            ├── ParseException (解析失败)
            └── PriceNotFoundException (价格未找到)
```

**使用场景**：

```python
try:
    price = await scraper.scrape(url)
except FetchException as e:
    # 网络错误，可以重试
    print(f"网络错误: {e}")
except ParseException as e:
    # HTML 结构变化，需要更新选择器
    print(f"解析错误: {e}")
except PriceNotFoundException as e:
    # 商品下架或价格区域变化
    print(f"价格未找到: {e}")
```

---

## 四、实现详解

### 4.1 Steam 爬虫完整流程

```python
# steam.py
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
        ".discount_final_price",      # 折扣价（优先）
        ".game_purchase_price",      # 原价
    ]

    def is_valid_url(self, url: str) -> bool:
        """验证是否为 Steam 商店 URL"""
        return self.STEAM_STORE_DOMAIN in url

    async def scrape(self, url: str) -> float:
        """抓取 Steam 商品价格"""
        # 步骤 1: 验证 URL
        if not self.is_valid_url(url):
            raise FetchException(f"Invalid Steam URL: {url}")

        try:
            # 步骤 2: 获取页面内容
            html = await self._fetch_page(url)

            # 步骤 3: 解析价格
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
            response.raise_for_status()  # HTTP 错误时抛异常
            return response.text

    def _parse_price(self, html: str) -> float:
        """从 HTML 中解析价格"""
        soup = BeautifulSoup(html, "lxml")

        # 步骤 1: 查找价格元素
        price_element = None
        for selector in self.PRICE_SELECTORS:
            price_element = soup.select_one(selector)
            if price_element:
                break  # 找到就停止

        if not price_element:
            raise PriceNotFoundException("Price element not found in page")

        # 步骤 2: 提取价格文本
        price_text = price_element.get_text(strip=True)
        # 例如: "¥ 298.00" 或 "$59.99"

        # 步骤 3: 解析价格数字
        price = self._extract_price_number(price_text)

        return price

    def _extract_price_number(self, text: str) -> float:
        """从价格文本中提取数字部分"""
        # 步骤 1: 移除货币符号和空格
        text = re.sub(r'[¥$€£\s]', '', text)

        # 步骤 2: 提取数字（支持小数和千分位）
        match = re.search(r'[\d,]+\.?\d*', text)
        if not match:
            raise ParseException(f"Cannot extract price from: {text}")

        # 步骤 3: 移除千分位分隔符
        price_str = match.group().replace(',', '')

        # 步骤 4: 转换为浮点数
        try:
            return float(price_str)
        except ValueError:
            raise ParseException(f"Invalid price format: {price_str}")
```

### 4.2 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Steam 爬虫抓取流程                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  用户请求                                                         │
│     │                                                            │
│     ▼                                                            │
│  scraper.scrape(url)                                            │
│     │                                                            │
│     ▼                                                            │
│  ┌─────────────────────────────────────────────┐                 │
│  │  1. URL 验证 (is_valid_url)              │                 │
│  │     检查是否包含 "store.steampowered.com" │                 │
│  └─────────────┬───────────────────────────────┘                 │
│                │ 有效                                              │
│                ▼                                                 │
│  ┌─────────────────────────────────────────────┐                 │
│  │  2. 获取页面 (_fetch_page)                │                 │
│  │     - 设置 User-Agent                      │                 │
│  │     - 使用 httpx 异步请求                  │                 │
│  │     - 返回 HTML 文本                       │                 │
│  └─────────────┬───────────────────────────────┘                 │
│                │ 成功                                              │
│                ▼                                                 │
│  ┌─────────────────────────────────────────────┐                 │
│  │  3. 解析 HTML (_parse_price)              │                 │
│  │     - BeautifulSoup 解析                   │                 │
│  │     - 按选择器查找价格元素                 │                 │
│  │     - .discount_final_price (优先)         │                 │
│  │     - .game_purchase_price                 │                 │
│  └─────────────┬───────────────────────────────┘                 │
│                │ 找到元素                                          │
│                ▼                                                 │
│  ┌─────────────────────────────────────────────┐                 │
│  │  4. 提取价格文本                          │                 │
│  │     price_text = "¥ 298.00"              │                 │
│  └─────────────┬───────────────────────────────┘                 │
│                │                                                   │
│                ▼                                                 │
│  ┌─────────────────────────────────────────────┐                 │
│  │  5. 解析数字 (_extract_price_number)      │                 │
│  │     - 移除 ¥ $ € £                      │                 │
│  │     - 提取数字部分                        │                 │
│  │     - 转换为 float: 298.0                 │                 │
│  └─────────────┬───────────────────────────────┘                 │
│                │                                                   │
│                ▼                                                 │
│  返回: 298.0                                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 模块入口 (__init__.py)

```python
# 平台名称到爬虫类的映射
SCRAPER_MAP = {
    "steam": SteamScraper,
}

def get_scraper(platform_or_url: str) -> BaseScraper:
    """根据平台名称或 URL 获取爬虫实例"""
    # 情况 1: 传入 URL
    if "/" in platform_or_url:
        for platform, scraper_class in SCRAPER_MAP.items():
            scraper = scraper_class()
            if scraper.is_valid_url(platform_or_url):
                return scraper
        raise ValueError(f"Unsupported URL: {platform_or_url}")

    # 情况 2: 传入平台名称
    platform = platform_or_url.lower()
    if platform not in SCRAPER_MAP:
        raise ValueError(f"Unsupported platform: {platform}")

    return SCRAPER_MAP[platform]()
```

---

## 五、使用示例

### 示例 1: 基本使用

```python
from app.scrapers import get_scraper
import asyncio

async def main():
    # 获取 Steam 爬虫
    scraper = get_scraper("steam")

    # 抓取价格
    url = "https://store.steampowered.com/app/1091500/Cyberpunk_2077/"
    price = await scraper.scrape(url)

    print(f"当前价格: ¥{price}")

asyncio.run(main())
```

### 示例 2: 自动识别平台

```python
from app.scrapers import get_scraper
import asyncio

async def main():
    # 直接传入 URL，自动识别平台
    url = "https://store.steampowered.com/app/1091500/Cyberpunk_2077/"
    scraper = get_scraper(url)  # 自动返回 SteamScraper

    price = await scraper.scrape(url)
    print(f"价格: ¥{price}")

asyncio.run(main())
```

### 示例 3: 错误处理

```python
from app.scrapers import get_scraper, FetchException, ParseException, PriceNotFoundException
import asyncio

async def main():
    scraper = get_scraper("steam")
    url = "https://store.steampowered.com/app/1091500/Cyberpunk_2077/"

    try:
        price = await scraper.scrape(url)
        print(f"价格: ¥{price}")

    except FetchException as e:
        print(f"网络请求失败: {e}")
        # 可以重试或记录日志

    except ParseException as e:
        print(f"页面解析失败: {e}")
        # 可能需要更新选择器

    except PriceNotFoundException as e:
        print(f"未找到价格: {e}")
        # 商品可能下架

asyncio.run(main())
```

### 示例 4: 在 FastAPI 路由中使用

```python
from fastapi import APIRouter, Depends
from app.scrapers import get_scraper
from app.database import AsyncSession, get_session
from app import models

router = APIRouter()

@router.post("/check-price/{product_id}")
async def check_price(
    product_id: int,
    session: AsyncSession = Depends(get_session)
):
    """检查商品价格"""
    # 1. 获取商品
    product = session.get(models.Product, product_id)
    if not product:
        return {"error": "商品不存在"}

    # 2. 获取爬虫
    scraper = get_scraper(product.platform)

    # 3. 抓取价格
    try:
        new_price = await scraper.scrape(product.url)

        # 4. 更新数据库
        product.current_price = new_price
        product.last_checked_time = datetime.now()

        # 5. 记录历史
        history = models.PriceHistory(
            price=new_price,
            product_id=product_id
        )
        session.add(history)

        session.commit()

        return {"price": new_price}

    except Exception as e:
        return {"error": str(e)}
```

---

## 六、扩展新平台

### 步骤 1: 创建新爬虫类

```python
# app/scrapers/epic.py
from app.scrapers.base import BaseScraper
from app.scrapers.exceptions import FetchException, ParseException, PriceNotFoundException
import httpx
from bs4 import BeautifulSoup

class EpicScraper(BaseScraper):
    """Epic Games 商店爬虫"""

    EPIC_DOMAIN = "store.epicgames.com"

    PRICE_SELECTORS = [
        ".css-price",           # 主价格
        ".css-discount-price",   # 折扣价
    ]

    def is_valid_url(self, url: str) -> bool:
        """验证是否为 Epic URL"""
        return self.EPIC_DOMAIN in url

    async def scrape(self, url: str) -> float:
        """抓取 Epic 商品价格"""
        if not self.is_valid_url(url):
            raise FetchException(f"Invalid Epic URL: {url}")

        try:
            html = await self._fetch_page(url)
            price = self._parse_price(html)
            return price
        except Exception as e:
            raise ParseException(f"Failed to parse price: {e}")

    async def _fetch_page(self, url: str) -> str:
        """获取页面"""
        headers = {
            "User-Agent": "Mozilla/5.0 ..."
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.text

    def _parse_price(self, html: str) -> float:
        """解析价格"""
        soup = BeautifulSoup(html, "lxml")

        for selector in self.PRICE_SELECTORS:
            price_element = soup.select_one(selector)
            if price_element:
                price_text = price_element.get_text(strip=True)
                return self._extract_price_number(price_text)

        raise PriceNotFoundException("Price not found")

    def _extract_price_number(self, text: str) -> float:
        """提取数字"""
        import re
        text = re.sub(r'[¥$€£\s]', '', text)
        match = re.search(r'[\d,]+\.?\d*', text)
        if not match:
            raise ParseException(f"Cannot extract price: {text}")

        price_str = match.group().replace(',', '')
        return float(price_str)
```

### 步骤 2: 注册到模块

```python
# app/scrapers/__init__.py
from app.scrapers.epic import EpicScraper  # ← 添加导入

SCRAPER_MAP = {
    "steam": SteamScraper,
    "epic": EpicScraper,  # ← 添加映射
}
```

### 步骤 3: 使用新平台

```python
from app.scrapers import get_scraper

# 使用 Epic 爬虫
scraper = get_scraper("epic")
price = await scraper.scrape("https://store.epicgames.com/...")

# 或通过 URL 自动识别
scraper = get_scraper("https://store.epicgames.com/...")
price = await scraper.scrape("https://store.epicgames.com/...")
```

---

## 七、常见问题

### Q1: base.py 和 exceptions.py 为什么是空的？

**它们不是空的！** 它们包含**抽象定义**和**异常类**。

```python
# base.py - 定义接口规范
class BaseScraper(ABC):
    @abstractmethod
    async def scrape(self, url: str) -> float:
        pass  # 子类必须实现

# exceptions.py - 定义异常类型
class FetchException(ScraperException):
    pass  # 只是标记，逻辑在父类
```

### Q2: 如何获取 Steam 价格选择器？

使用浏览器开发者工具：

```
1. 打开 Steam 商店页面
2. 右键价格区域 → "检查"
3. 查看元素，找到对应的 class 或 id
4. 复制选择器（如 .discount_final_price）
```

### Q3: 如果 Steam 页面结构变化怎么办？

修改 `steam.py` 中的 `PRICE_SELECTORS`：

```python
class SteamScraper(BaseScraper):
    PRICE_SELECTORS = [
        ".new-selector-1",      # 新的选择器（优先）
        ".old-selector-1",      # 旧的选择器（兼容）
        ".discount_final_price", # 更旧的选择器
        ".game_purchase_price",
    ]
```

### Q4: 如何添加反爬策略？

在 `_fetch_page` 方法中添加：

```python
async def _fetch_page(self, url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 ...",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://store.steampowered.com/",  # 添加 Referer
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()

        # 添加延迟（避免请求过快）
        await asyncio.sleep(1)

        return response.text
```

### Q5: 如何处理多货币？

```python
def _extract_price_number(self, text: str) -> float:
    """提取数字，自动识别货币"""
    import re

    # 检测货币符号
    currency = None
    if "¥" in text:
        currency = "CNY"
    elif "$" in text:
        currency = "USD"
    elif "€" in text:
        currency = "EUR"

    # 提取数字
    text = re.sub(r'[¥$€£\s]', '', text)
    match = re.search(r'[\d,]+\.?\d*', text)
    price = float(match.group().replace(',', ''))

    # 可以在这里添加货币转换逻辑
    if currency == "USD":
        price = price * 7.2  # 美元转人民币

    return price
```

---

## 总结

| 文件 | 作用 | 是否空白 |
|------|------|---------|
| `base.py` | 定义爬虫接口规范 | ❌ 包含抽象基类 |
| `exceptions.py` | 定义异常类型 | ❌ 包含异常类 |
| `steam.py` | Steam 爬虫实现 | ❌ 完整实现 |
| `__init__.py` | 模块入口，提供 get_scraper() | ❌ 包含映射逻辑 |

**爬虫模块已完整实现，可以直接使用！**