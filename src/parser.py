"""HTML解析模块 - 使用BeautifulSoup4解析招标信息."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup


@dataclass
class TenderInfo:
    """招标信息数据类."""
    
    title: str
    url: str
    publish_date: str
    source: str
    keyword: str = ""
    description: str = ""
    region: str = ""
    agency: str = ""
    project_code: str = ""
    
    # 元数据
    crawled_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式."""
        return {
            "标题": self.title,
            "链接": self.url,
            "发布日期": self.publish_date,
            "信息来源": self.source,
            "关键词": self.keyword,
            "项目描述": self.description,
            "地区": self.region,
            "代理机构": self.agency,
            "项目编号": self.project_code,
            "抓取时间": self.crawled_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TenderInfo":
        """从字典创建实例."""
        return cls(
            title=data.get("标题", ""),
            url=data.get("链接", ""),
            publish_date=data.get("发布日期", ""),
            source=data.get("信息来源", ""),
            keyword=data.get("关键词", ""),
            description=data.get("项目描述", ""),
            region=data.get("地区", ""),
            agency=data.get("代理机构", ""),
            project_code=data.get("项目编号", ""),
        )


class TenderParser:
    """招标信息HTML解析器."""
    
    def __init__(self, keyword: str = ""):
        """初始化解析器.
        
        Args:
            keyword: 当前搜索关键词
        """
        self.keyword = keyword
    
    def parse_list_page(self, html: str) -> List[TenderInfo]:
        """解析列表页面HTML.
        
        Args:
            html: 页面HTML内容
            
        Returns:
            List[TenderInfo]: 招标信息列表
        """
        soup = BeautifulSoup(html, "html.parser")
        tenders = []
        
        # 查找搜索结果列表
        # 中国政府采购网搜索结果通常在 ul.vT-srch-result-list > li 中
        result_list = soup.find("ul", class_="vT-srch-result-list")
        
        if result_list:
            items = result_list.find_all("li")
        else:
            # 备选：尝试其他常见结构
            items = soup.find_all("li", class_=lambda x: x and "result" in x.lower())
        
        for item in items:
            tender = self._parse_list_item(item)
            if tender:
                tender.keyword = self.keyword
                tenders.append(tender)
        
        return tenders
    
    def _parse_list_item(self, item: BeautifulSoup) -> Optional[TenderInfo]:
        """解析单个列表项.
        
        Args:
            item: BeautifulSoup元素
            
        Returns:
            Optional[TenderInfo]: 解析结果，失败返回None
        """
        try:
            # 查找标题和链接
            title_link = item.find("a")
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            url = title_link.get("href", "")
            
            # 查找发布日期
            publish_date = ""
            date_elem = item.find("span", class_="time")
            if date_elem:
                publish_date = date_elem.get_text(strip=True)
            
            # 查找来源
            source = ""
            source_elem = item.find("span", class_="source")
            if source_elem:
                source = source_elem.get_text(strip=True)
            
            # 查找地区
            region = ""
            region_elem = item.find("span", class_="region")
            if region_elem:
                region = region_elem.get_text(strip=True)
            
            # 查找代理机构
            agency = ""
            agency_elem = item.find("span", class_="agency")
            if agency_elem:
                agency = agency_elem.get_text(strip=True)
            
            # 查找项目编号
            project_code = ""
            code_elem = item.find("span", class_="code")
            if code_elem:
                project_code = code_elem.get_text(strip=True)
            
            # 提取描述（通常是标题后的文本）
            description = ""
            desc_elem = item.find("p", class_="des")
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            return TenderInfo(
                title=title,
                url=url,
                publish_date=publish_date,
                source=source,
                region=region,
                agency=agency,
                project_code=project_code,
                description=description,
            )
        
        except Exception as e:
            # 解析失败，返回None
            return None
    
    def filter_by_date(
        self, 
        tenders: List[TenderInfo], 
        start_date: str, 
        end_date: str
    ) -> List[TenderInfo]:
        """按日期范围过滤招标信息.
        
        Args:
            tenders: 招标信息列表
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            List[TenderInfo]: 过滤后的列表
        """
        filtered = []
        
        for tender in tenders:
            try:
                # 尝试解析日期
                tender_date = self._parse_date(tender.publish_date)
                if tender_date:
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                    end = datetime.strptime(end_date, "%Y-%m-%d")
                    
                    if start <= tender_date <= end:
                        filtered.append(tender)
                else:
                    # 日期解析失败，保留
                    filtered.append(tender)
            except Exception:
                # 日期比较失败，保留
                filtered.append(tender)
        
        return filtered
    
    def filter_by_keywords(
        self, 
        tenders: List[TenderInfo], 
        keywords: List[str]
    ) -> List[TenderInfo]:
        """按关键词过滤招标信息.
        
        Args:
            tenders: 招标信息列表
            keywords: 关键词列表
            
        Returns:
            List[TenderInfo]: 过滤后的列表
        """
        if not keywords:
            return tenders
        
        filtered = []
        
        for tender in tenders:
            text = f"{tender.title} {tender.description}".lower()
            if any(kw.lower() in text for kw in keywords):
                filtered.append(tender)
        
        return filtered
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串.
        
        Args:
            date_str: 日期字符串
            
        Returns:
            Optional[datetime]: 解析后的日期，失败返回None
        """
        if not date_str:
            return None
        
        # 尝试多种日期格式
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
            "%Y.%m.%d",
            "%Y:%m:%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def extract_total_pages(self, html: str) -> int:
        """提取总页数.
        
        Args:
            html: 页面HTML内容
            
        Returns:
            int: 总页数，失败返回1
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # 查找分页信息
        # 常见格式：共 X 页 或 Page X of Y
        page_info = soup.find("span", class_="page-info")
        if page_info:
            text = page_info.get_text()
            # 尝试提取数字
            import re
            match = re.search(r'(\d+)', text)
            if match:
                return int(match.group(1))
        
        # 查找分页链接
        pagination = soup.find("div", class_="pagination")
        if pagination:
            links = pagination.find_all("a")
            max_page = 1
            for link in links:
                try:
                    page_num = int(link.get_text(strip=True))
                    max_page = max(max_page, page_num)
                except ValueError:
                    continue
            return max_page
        
        return 1
