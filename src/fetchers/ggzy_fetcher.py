"""全国公共资源交易平台抓取器.

网站: https://www.ggzy.gov.cn/deal/dealList.html
特点:
- 使用JavaScript动态加载内容
- 需要浏览器渲染
- 支持关键词搜索
- 数据包含政府采购、工程建设等多种类型

注意: 由于网站使用JavaScript动态加载，此fetcher需要Playwright支持
安装: pip install playwright && playwright install
"""

import re
import time
from typing import List, Optional, Dict
from urllib.parse import urljoin, quote

from bs4 import BeautifulSoup

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import TenderConfig


class TenderInfo:
    """招标信息数据类 - 13个字段.
    
    字段列表:
    1. keyword - 关键词
    2. title - 标题
    3. publish_date - 发布日期
    4. notice_type - 公告类型
    5. province - 省份
    6. purchaser - 采购单位
    7. agency - 代理机构
    8. budget - 预算金额
    9. subject - 标的物
    10. contact_name - 联系人
    11. contact_phone - 联系电话
    12. contact_address - 联系地址
    13. url - URL
    """
    
    def __init__(
        self,
        title: str = "",
        url: str = "",
        publish_date: str = "",
        province: str = "",
        purchaser: str = "",
        budget: str = "",
        keyword: str = "",
        notice_type: str = "",
        agency: str = "",
        contact_name: str = "",
        contact_phone: str = "",
        contact_address: str = "",
        subject: str = ""
    ):
        self.title = title
        self.url = url
        self.publish_date = publish_date
        self.province = province
        self.purchaser = purchaser
        self.budget = budget
        self.keyword = keyword
        self.notice_type = notice_type
        self.agency = agency
        self.contact_name = contact_name
        self.contact_phone = contact_phone
        self.contact_address = contact_address
        self.subject = subject


class GGZYFetcher:
    """全国公共资源交易平台抓取器.
    
    由于该网站使用JavaScript动态加载，需要使用浏览器渲染获取数据。
    可以通过以下方式使用:
    1. 使用Playwright/Selenium进行浏览器自动化
    2. 调用已渲染好的页面内容
    
    当前实现基于静态HTML解析，适用于已获取的渲染后页面内容。
    """
    
    BASE_URL = "https://www.ggzy.gov.cn"
    SEARCH_URL = "https://www.ggzy.gov.cn/deal/dealList.html"
    
    def __init__(self, config: TenderConfig):
        """初始化抓取器.
        
        Args:
            config: 配置对象
        """
        self.config = config
        self._seen_urls = set()
    
    def build_search_url(self, keyword: str, page: int = 1) -> str:
        """构建搜索URL.
        
        Args:
            keyword: 搜索关键词
            page: 页码
            
        Returns:
            str: 搜索URL
        """
        return f"{self.SEARCH_URL}?keyword={quote(keyword)}&page={page}"
    
    def parse_list_page(self, html: str) -> List[TenderInfo]:
        """解析列表页HTML.
        
        Args:
            html: 页面HTML（需要是浏览器渲染后的内容）
            
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
                # 日期通常在heading的文本中，格式：标题 日期
                heading_text = heading.get_text(strip=True)
                date_match = re.search(r'(\d{4}-\d{2}-\d{2})', heading_text)
                if date_match:
                    date_text = date_match.group(1)
                
                # 获取详细信息（在heading后面的paragraph中）
                info_para = heading.find_next('p')
                province = ""
                platform = ""
                business_type = ""
                info_type = ""
                industry = ""
                
                if info_para:
                    info_text = info_para.get_text(strip=True)
                    # 解析：省份：xxx来源平台：xxx业务类型：xxx信息类型：xxx行业：xxx
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
                # 解析失败，跳过
                continue
        
        return results
    
    def get_total_pages(self, html: str) -> int:
        """获取总页数.
        
        Args:
            html: 页面HTML
            
        Returns:
            int: 总页数
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # 查找分页信息 - 格式：共 20 条 或 共 71824 条
        text_content = soup.get_text()
        match = re.search(r'共\s*(\d+)\s*条', text_content)
        if match:
            total_items = int(match.group(1))
            # 每页大约20条
            return (total_items + 19) // 20
        
        return 1
    
    def parse_from_browser(self, html: str, keyword: str, max_results: Optional[int] = None) -> List[TenderInfo]:
        """从浏览器渲染后的HTML解析结果.
        
        这是主要的解析方法，需要传入浏览器渲染后的页面HTML。
        
        Args:
            html: 浏览器渲染后的页面HTML
            keyword: 搜索关键词
            max_results: 最大结果数
            
        Returns:
            List[TenderInfo]: 招标信息列表
        """
        if max_results is None:
            max_results = self.config.max_results
        
        results = self.parse_list_page(html)
        
        # 添加关键词并去重
        unique_results = []
        for result in results:
            if result.url not in self._seen_urls:
                self._seen_urls.add(result.url)
                result.keyword = keyword
                unique_results.append(result)
                
                if max_results > 0 and len(unique_results) >= max_results:
                    break
        
        return unique_results
    
    def search(self, keyword: str, max_results: Optional[int] = None) -> List[TenderInfo]:
        """搜索单个关键词的招标信息.
        
        注意：由于网站使用JavaScript动态加载，此方法需要配合浏览器使用。
        建议使用 parse_from_browser() 方法传入已渲染的HTML。
        
        Args:
            keyword: 搜索关键词
            max_results: 最大结果数
            
        Returns:
            List[TenderInfo]: 招标信息列表
        """
        print(f"GGZYFetcher: 关键词 '{keyword}' 需要浏览器渲染支持")
        print(f"请使用 parse_from_browser() 方法传入浏览器渲染后的HTML")
        return []
    
    def close(self):
        """关闭资源."""
        pass


if __name__ == "__main__":
    # 测试代码 - 需要传入浏览器渲染后的HTML
    from config import TenderConfig
    
    config = TenderConfig(
        keywords=["眼科"],
        days_back=7,
        max_results=20
    )
    
    fetcher = GGZYFetcher(config)
    
    # 示例：传入浏览器渲染后的HTML
    # html = "...浏览器渲染后的HTML内容..."
    # results = fetcher.parse_from_browser(html, "眼科", max_results=5)
    
    print("GGZYFetcher 需要浏览器渲染支持")
    print("请使用 Playwright 或 Selenium 获取渲染后的页面HTML，然后调用 parse_from_browser()")
