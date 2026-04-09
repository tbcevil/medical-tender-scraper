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
                platform = ""  # 作为代理机构
                notice_type = ""  # 信息类型映射到公告类型
                
                if info_para:
                    info_text = info_para.get_text(strip=True)
                    
                    province_match = re.search(r'省份：([^来源]+)', info_text)
                    if province_match:
                        province = province_match.group(1).strip()
                    
                    platform_match = re.search(r'来源平台：([^业务]+)', info_text)
                    if platform_match:
                        platform = platform_match.group(1).strip()
                    
                    # 信息类型映射到公告类型
                    info_type_match = re.search(r'信息类型：([^行业]+)', info_text)
                    if info_type_match:
                        notice_type = info_type_match.group(1).strip()
                
                # 构建完整URL
                if href.startswith('/'):
                    url = urljoin(self.BASE_URL, href)
                else:
                    url = href
                
                # 创建TenderInfo，映射到13个标准字段
                tender = TenderInfo(
                    title=title,
                    url=url,
                    publish_date=date_text,
                    province=province,
                    agency=platform,  # 来源平台作为代理机构
                    notice_type=notice_type,  # 信息类型作为公告类型
                    # 其他字段需要从详情页获取或保持为空
                )
                results.append(tender)
                
            except Exception as e:
                continue
        
        return results
    
    def _fetch_detail_info(self, tender: TenderInfo):
        """从详情页获取更多信息.
        
        Args:
            tender: TenderInfo对象，会被修改
        """
        try:
            # 访问详情页
            self._page.goto(tender.url, wait_until="networkidle")
            time.sleep(2)
            
            html = self._page.content()
            soup = BeautifulSoup(html, "html.parser")
            full_text = soup.get_text()
            
            # 提取采购单位（采购人）
            if not tender.purchaser:
                patterns = [
                    r'采购人[：:]\s*([^\n]+?)(?:\n|$)',
                    r'采购单位[：:]\s*([^\n]+?)(?:\n|$)',
                    r'招标人[：:]\s*([^\n]+?)(?:\n|$)',
                    r'招标单位[：:]\s*([^\n]+?)(?:\n|$)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        tender.purchaser = match.group(1).strip()
                        break
            
            # 提取预算金额
            if not tender.budget:
                patterns = [
                    r'预算金额[：:]\s*([^\n]+?)(?:\n|$)',
                    r'项目预算[：:]\s*([^\n]+?)(?:\n|$)',
                    r'采购预算[：:]\s*([^\n]+?)(?:\n|$)',
                    r'金额[：:]\s*([^\n]+?)(?:\n|$)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        budget = match.group(1).strip()
                        if '元' in budget or '万' in budget or '¥' in budget:
                            tender.budget = budget
                            break
            
            # 提取联系人信息
            self._extract_contact_info(tender, soup, full_text)
            
            # 提取标的物
            self._extract_subject_info(tender, soup, full_text)
            
        except Exception as e:
            # 详情页获取失败，忽略
            pass
    
    def _extract_contact_info(self, tender: TenderInfo, soup, full_text: str):
        """提取联系人信息."""
        try:
            # 提取联系人姓名
            if not tender.contact_name:
                patterns = [
                    r'项目联系人[：:]\s*([^\n]{2,20})(?:\n|$)',
                    r'联系人[：:]\s*([^\n]{2,20})(?:\n|$)',
                    r'联系人员[：:]\s*([^\n]{2,20})(?:\n|$)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        tender.contact_name = match.group(1).strip()
                        break
            
            # 提取电话
            if not tender.contact_phone:
                patterns = [
                    r'项目联系人电话[：:\s]+([\d\-]+)',
                    r'电\s*话[：:\s]+([\d\-]+)',
                    r'联系方式[：:\s]+([\d\-]+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        phone = match.group(1).strip()
                        if len(phone) < 50:
                            tender.contact_phone = phone
                            break
            
            # 提取地址
            if not tender.contact_address:
                patterns = [
                    r'地\s*址[：:]\s*([^\n]+?)(?:\n|$)',
                    r'联系地址[：:]\s*([^\n]+?)(?:\n|$)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        tender.contact_address = match.group(1).strip()
                        break
        except Exception:
            pass
    
    def _extract_subject_info(self, tender: TenderInfo, soup, full_text: str):
        """提取标的物信息."""
        try:
            subjects = []
            
            # 方法1: 从标题中提取医疗设备名称
            title_subjects = self._extract_subject_from_title(tender.title)
            if title_subjects:
                subjects.append(title_subjects)
            
            # 方法2: 从页面文本中提取
            if not subjects:
                # 查找包含医疗设备关键词的短语
                medical_keywords = [
                    '显微镜', '激光', '超声', 'CT', 'MRI', '内窥镜', '监护仪',
                    '呼吸机', '麻醉机', '手术床', '无影灯', '分析仪', '检测仪',
                    '治疗仪', '手术机器人', '扫描仪', 'OCT', '裂隙灯', '眼压计',
                    '验光仪', '视野计', '角膜', '眼底'
                ]
                
                for keyword in medical_keywords:
                    if keyword in full_text:
                        # 提取包含关键词的短语
                        pattern = rf'([\u4e00-\u9fa5]{{2,15}}{keyword}[\u4e00-\u9fa5]{{0,10}})'
                        matches = re.findall(pattern, full_text)
                        for match in matches:
                            if len(match) > 5 and len(match) < 40:
                                subjects.append(match)
            
            # 去重并合并
            if subjects:
                seen = set()
                unique_subjects = []
                for s in subjects:
                    s_normalized = s.replace(' ', '').replace('\n', '').replace('\t', '')
                    if s_normalized not in seen and len(s) > 3:
                        seen.add(s_normalized)
                        unique_subjects.append(s)
                
                if unique_subjects:
                    tender.subject = '；'.join(unique_subjects[:3])
        except Exception:
            pass
    
    def _extract_subject_from_title(self, title: str) -> str:
        """从标题中提取标的物（医疗设备名称）."""
        subjects = []
        
        # 医疗设备关键词
        medical_keywords = [
            '显微镜', '激光', '超声', 'CT', 'MRI', '核磁', '内窥镜', '监护仪',
            '呼吸机', '麻醉机', '手术床', '无影灯', '分析仪', '检测仪',
            '治疗仪', '手术机器人', '扫描仪', 'OCT', '裂隙灯', '眼压计',
            '验光仪', '视野计', '角膜', '眼底', '生物测量仪', '光学生物测量仪'
        ]
        
        # 提取包含医疗设备关键词的短语
        for keyword in medical_keywords:
            if keyword in title:
                # 找到关键词前后各15个字符
                idx = title.find(keyword)
                start = max(0, idx - 15)
                end = min(len(title), idx + len(keyword) + 15)
                subject = title[start:end].strip()
                # 清理开头和结尾的无关字符
                subject = re.sub(r'^[\s\-–—]+', '', subject)
                subject = re.sub(r'[\s\-–—]+$', '', subject)
                if len(subject) > 3 and len(subject) < 50:
                    subjects.append(subject)
        
        # 去重
        if subjects:
            seen = set()
            unique_subjects = []
            for s in subjects:
                if s not in seen:
                    seen.add(s)
                    unique_subjects.append(s)
            return '；'.join(unique_subjects[:2])
        
        return ""
    
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
                    
                    # 获取详情页信息
                    print(f"    获取详情: {result.title[:30]}...")
                    self._fetch_detail_info(result)
                    
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
                            
                            # 获取详情页信息
                            print(f"    获取详情: {result.title[:30]}...")
                            self._fetch_detail_info(result)
                            
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
