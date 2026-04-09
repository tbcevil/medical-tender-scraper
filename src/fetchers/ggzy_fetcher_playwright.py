"""全国公共资源交易平台抓取器 - Playwright版本.

使用Playwright进行浏览器自动化，支持JavaScript渲染。

安装依赖:
    pip install playwright
    playwright install chromium

或使用 uv:
    uv pip install playwright
    playwright install chromium
"""

import re
import time
from typing import List, Optional, Dict
from urllib.parse import urljoin, quote

from bs4 import BeautifulSoup

try:
    from playwright.sync_api import sync_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("警告: Playwright未安装，请运行: pip install playwright && playwright install chromium")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import TenderConfig


class TenderInfo:
    """招标信息数据类."""
    
    def __init__(
        self,
        title: str = "",
        url: str = "",
        publish_date: str = "",
        province: str = "",
        platform: str = "",
        business_type: str = "",
        info_type: str = "",
        industry: str = "",
        project_code: str = "",
        keyword: str = ""
    ):
        self.title = title
        self.url = url
        self.publish_date = publish_date
        self.province = province
        self.platform = platform
        self.business_type = business_type
        self.info_type = info_type
        self.industry = industry
        self.project_code = project_code
        self.keyword = keyword


class GGZYFetcherPlaywright:
    """全国公共资源交易平台抓取器 - Playwright版本."""
    
    BASE_URL = "https://www.ggzy.gov.cn"
    SEARCH_URL = "https://www.ggzy.gov.cn/deal/dealList.html"
    
    def __init__(self, config: TenderConfig, headless: bool = True):
        """初始化抓取器.
        
        Args:
            config: 配置对象
            headless: 是否使用无头模式（默认True）
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright未安装。请运行: pip install playwright && playwright install chromium"
            )
        
        self.config = config
        self.headless = headless
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._seen_urls = set()
    
    def _init_browser(self):
        """初始化浏览器."""
        if self._browser is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._page = self._browser.new_page()
            self._page.set_viewport_size({"width": 1280, "height": 800})
    
    def _close_browser(self):
        """关闭浏览器."""
        if self._browser:
            self._browser.close()
            self._browser = None
        if self._playwright:
            self._playwright.stop()
            self._playwright = None
    
    def _search_keyword(self, keyword: str) -> str:
        """在网站上搜索关键词并返回页面HTML.
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            str: 页面HTML
        """
        self._init_browser()
        
        print(f"  打开搜索页面...")
        self._page.goto(self.SEARCH_URL, wait_until="networkidle")
        
        # 等待页面加载
        time.sleep(2)
        
        # 输入关键词
        print(f"  输入关键词: {keyword}")
        search_input = self._page.locator('input[placeholder*="关键字"], input[type="text"]').first
        search_input.fill(keyword)
        
        # 点击搜索按钮
        print(f"  点击搜索...")
        search_button = self._page.locator('button:has-text("搜索"), input[value="搜索"]').first
        search_button.click()
        
        # 等待结果加载
        print(f"  等待结果加载...")
        time.sleep(3)
        
        # 等待结果出现
        try:
            self._page.wait_for_selector('h4', timeout=10000)
        except:
            pass
        
        # 获取页面HTML
        html = self._page.content()
        return html
    
    def _get_next_page(self) -> str:
        """获取下一页内容.
        
        Returns:
            str: 页面HTML
        """
        # 查找下一页按钮
        try:
            next_button = self._page.locator('a:has-text("下一页"), .next').first
            if next_button.is_visible():
                next_button.click()
                time.sleep(2)
                return self._page.content()
        except:
            pass
        
        return ""
    
    def parse_list_page(self, html: str) -> List[TenderInfo]:
        """解析列表页HTML.
        
        Args:
            html: 页面HTML
            
        Returns:
            List[TenderInfo]: 招标信息列表
        """
        results = []
        soup = BeautifulSoup(html, "html.parser")
        
        # 查找所有招标条目 - 每个条目是一个h4标题
        headings = soup.find_all('h4', level='4')
        
        for heading in headings:
            try:
                # 获取标题链接
                link = heading.find('a')
                if not link:
                    continue
                
                title = link.get_text(strip=True)
                href = link.get('href', '')
                
                # 获取日期（heading后面的文本）
                date_text = ""
                heading_text = heading.get_text(strip=True)
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', heading_text)
                if date_match:
                    date_text = date_match.group(1)
                
                # 获取详细信息
                info_para = heading.find_next('p')
                province = ""
                platform = ""
                business_type = ""
                info_type = ""
                industry = ""
                
                if info_para:
                    info_text = info_para.get_text(strip=True)
                    
                    province_match = re.search(r'省份：([^来源]+)', info_text)
                    if province_match:
                        province = province_match.group(1).strip()
                    
                    platform_match = re.search(r'来源平台：([^业务]+)', info_text)
                    if platform_match:
                        platform = platform_match.group(1).strip()
                    
                    business_match = re.search(r'业务类型：([^信息]+)', info_text)
                    if business_match:
                        business_type = business_match.group(1).strip()
                    
                    info_type_match = re.search(r'信息类型：([^行业]+)', info_text)
                    if info_type_match:
                        info_type = info_type_match.group(1).strip()
                    
                    industry_match = re.search(r'行业：(.+)', info_text)
                    if industry_match:
                        industry = industry_match.group(1).strip()
                
                # 构建完整URL
                if href.startswith('/'):
                    url = urljoin(self.BASE_URL, href)
                else:
                    url = href
                
                tender = TenderInfo(
                    title=title,
                    url=url,
                    publish_date=date_text,
                    province=province,
                    platform=platform,
                    business_type=business_type,
                    info_type=info_type,
                    industry=industry
                )
                results.append(tender)
                
            except Exception as e:
                continue
        
        return results
    
    def get_total_results(self, html: str) -> int:
        """获取总结果数.
        
        Args:
            html: 页面HTML
            
        Returns:
            int: 总结果数
        """
        soup = BeautifulSoup(html, "html.parser")
        text_content = soup.get_text()
        match = re.search(r'搜索记录数[:：]\s*(\d+)', text_content)
        if match:
            return int(match.group(1))
        
        match = re.search(r'共\s*(\d+)\s*条', text_content)
        if match:
            return int(match.group(1))
        
        return 0
    
    def search(self, keyword: str, max_results: Optional[int] = None) -> List[TenderInfo]:
        """搜索单个关键词的招标信息.
        
        Args:
            keyword: 搜索关键词
            max_results: 最大结果数，None表示使用配置值，0表示获取所有
            
        Returns:
            List[TenderInfo]: 招标信息列表
        """
        if max_results is None:
            max_results = self.config.max_results
        
        fetch_all = max_results == 0
        if fetch_all:
            print(f"搜索关键词: {keyword} (获取所有结果)")
        else:
            print(f"搜索关键词: {keyword} (最多 {max_results} 条)")
        
        all_results = []
        
        try:
            # 搜索关键词
            html = self._search_keyword(keyword)
            
            # 获取总结果数
            total = self.get_total_results(html)
            print(f"  共找到 {total} 条记录")
            
            # 解析第一页
            results = self.parse_list_page(html)
            
            for result in results:
                if result.url not in self._seen_urls:
                    self._seen_urls.add(result.url)
                    result.keyword = keyword
                    all_results.append(result)
                    
                    if not fetch_all and len(all_results) >= max_results:
                        break
            
            print(f"  第1页找到 {len(results)} 条，累计 {len(all_results)} 条")
            
            # 如果需要获取更多页
            if fetch_all or len(all_results) < max_results:
                page = 1
                while True:
                    if not fetch_all and len(all_results) >= max_results:
                        break
                    
                    page += 1
                    print(f"  获取第 {page} 页...")
                    
                    next_html = self._get_next_page()
                    if not next_html:
                        print(f"  没有更多页面")
                        break
                    
                    results = self.parse_list_page(next_html)
                    if not results:
                        print(f"  第 {page} 页无数据")
                        break
                    
                    for result in results:
                        if result.url not in self._seen_urls:
                            self._seen_urls.add(result.url)
                            result.keyword = keyword
                            all_results.append(result)
                            
                            if not fetch_all and len(all_results) >= max_results:
                                break
                    
                    print(f"  第{page}页找到 {len(results)} 条，累计 {len(all_results)} 条")
                    
                    # 检查是否还有下一页
                    if len(results) < 20:  # 每页通常20条
                        break
                    
                    time.sleep(1.5)
        
        except Exception as e:
            print(f"  搜索失败: {e}")
        
        print(f"关键词 '{keyword}' 共找到 {len(all_results)} 条招标信息")
        if not fetch_all:
            return all_results[:max_results]
        return all_results
    
    def search_all_keywords(self) -> Dict[str, List[TenderInfo]]:
        """搜索所有关键词.
        
        Returns:
            Dict[str, List[TenderInfo]]: 关键词到结果列表的映射
        """
        results = {}
        
        for keyword in self.config.keywords:
            results[keyword] = self.search(keyword)
            
            # 关键词之间添加延迟
            if keyword != self.config.keywords[-1]:
                time.sleep(3)
        
        return results
    
    def close(self):
        """关闭资源."""
        self._close_browser()


if __name__ == "__main__":
    # 测试代码
    from config import TenderConfig
    
    if not PLAYWRIGHT_AVAILABLE:
        print("请先安装Playwright:")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)
    
    config = TenderConfig(
        keywords=["眼科"],
        days_back=7,
        max_results=10
    )
    
    fetcher = GGZYFetcherPlaywright(config, headless=False)  # 设置为True使用无头模式
    
    try:
        results = fetcher.search_all_keywords()
        
        for keyword, tenders in results.items():
            print(f"\n关键词 '{keyword}' 找到 {len(tenders)} 条:")
            for tender in tenders[:5]:
                print(f"  - {tender.title}")
                print(f"    日期: {tender.publish_date}")
                print(f"    省份: {tender.province}")
                print(f"    平台: {tender.platform}")
                print(f"    业务类型: {tender.business_type}")
                print()
    finally:
        fetcher.close()
