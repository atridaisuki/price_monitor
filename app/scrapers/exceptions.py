"""爬虫模块自定义异常"""


class ScraperException(Exception):
    """爬虫基础异常"""
    pass


class FetchException(ScraperException):
    """HTTP 请求失败异常"""
    pass


class ParseException(ScraperException):
    """HTML 解析失败异常"""
    pass


class PriceNotFoundException(ScraperException):
    """价格未找到异常"""
    pass
