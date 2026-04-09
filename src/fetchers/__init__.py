"""抓取器模块."""

from .ccgp_fetcher import CCGPFetcher
from .ggzy_fetcher import GGZYFetcher

try:
    from .ggzy_fetcher_playwright import GGZYFetcherPlaywright
    __all__ = ["CCGPFetcher", "GGZYFetcher", "GGZYFetcherPlaywright"]
except ImportError:
    __all__ = ["CCGPFetcher", "GGZYFetcher"]
