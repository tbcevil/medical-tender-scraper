"""中国政府采购网抓取器."""

import time
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urlencode
from dataclasses import dataclass


@dataclass
class TenderInfo:
    """招标信息数据类."""
    title: str
    url: str
    publish_date: str
    province: str = ""
    purchaser: str = ""
    budget: str = ""
    keyword: str = ""
    notice_type: str = ""  # 公告类型：公开招标、中标公告等
    agency: str = ""  # 代理机构
    # 联系人信息（从详情页获取）
    contact_name: str = ""  # 联系人姓名
    contact_phone: str = ""  # 联系人电话
    contact_address: str = ""  # 联系地址
    # 标的物信息（从详情页获取）
    subject: str = ""  # 标的物/采购内容


class CCGPFetcher:
    """中国政府采购网招标信息抓取器."""
    
    SEARCH_URL = "http://search.ccgp.gov.cn/bxsearch"
    
    # 医疗设备关键词库
    MEDICAL_DEVICE_KEYWORDS = [
        '显微镜', '激光', '超声', 'CT', 'MRI', '核磁', '内窥镜', '监护仪',
        '呼吸机', '麻醉机', '手术床', '无影灯', '消毒', '清洗',
        '培养箱', '离心机', '分析仪', '检测仪', '治疗仪', '手术机器人',
        '导航', '定位系统', '扫描仪', '照相机', '造影', '断层', 'OCT',
        '裂隙灯', '眼压计', '验光仪', '视野计', '角膜', '眼底',
        '手术', '治疗', '检查', '诊断', '护理', '康复', '急救'
    ]
    
    def __init__(self, config):
        """初始化抓取器."""
        self.config = config
        self.http_client = None
        self._seen_urls = set()
        
    def _get_http_client(self):
        """获取HTTP客户端（延迟导入）."""
        if self.http_client is None:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from http_client import HttpClient
            self.http_client = HttpClient(timeout=self.config.timeout)
        return self.http_client
    
    def build_search_url(self, keyword: str, page: int = 1) -> str:
        """构建搜索URL."""
        start_date, end_date = self.config.get_date_range()
        
        params = {
            "searchtype": "2",
            "page_index": str(page),
            "kw": keyword,
            "startTime": start_date,
            "endTime": end_date,
        }
        
        return f"{self.SEARCH_URL}?{urlencode(params)}"
    
    def parse_list_page(self, html: str) -> List[TenderInfo]:
        """解析列表页面HTML."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, "html.parser")
        tenders = []
        
        # 查找搜索结果列表 - 使用正确的class名
        result_div = soup.find("div", class_="vT-srch-result-list-con2")
        
        if result_div:
            for li in result_div.find_all("li"):
                try:
                    tender = self._parse_tender_item(li)
                    if tender:
                        tenders.append(tender)
                except Exception as e:
                    # 解析失败则跳过
                    continue
        
        return tenders
    
    def _parse_tender_item(self, li) -> Optional[TenderInfo]:
        """解析单个招标信息项."""
        # 提取标题和链接
        title_elem = li.find("a")
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        url = title_elem.get("href", "")
        
        if not title or not url:
            return None
        
        # 提取描述段落（包含预算信息）
        desc_elem = li.find("p")
        budget = ""
        if desc_elem:
            desc_text = desc_elem.get_text(strip=True)
            # 尝试提取预算金额 - 支持多种格式
            budget_patterns = [
                r'预算金额[：:]\s*([\d,\.]+)\s*元',
                r'预算[：:]\s*([\d,\.]+)\s*元',
                r'预算金额\s*[:：]\s*([\d,\.]+)',
                r'([\d,\.]+)\s*万元',
            ]
            for pattern in budget_patterns:
                budget_match = re.search(pattern, desc_text)
                if budget_match:
                    budget = budget_match.group(1)
                    if '万元' in desc_text and '元' not in budget:
                        budget += '万元'
                    else:
                        budget += '元'
                    break
        
        # 提取发布时间和来源信息
        span_elem = li.find("span")
        publish_date = ""
        province = ""
        purchaser = ""
        notice_type = ""
        agency = ""
        
        if span_elem:
            span_text = span_elem.get_text(strip=True)
            
            # 提取日期 - 格式: 2026.04.07 01:00:55
            date_match = re.search(r'(\d{4})\.(\d{2})\.(\d{2})', span_text)
            if date_match:
                publish_date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
            
            # 提取公告类型（在strong标签中）
            strong_elem = span_elem.find("strong")
            if strong_elem:
                notice_type = strong_elem.get_text(strip=True)
            
            # 提取省份 - 格式: | 山东 | 或 | 内蒙古 |
            province_match = re.search(r'\|\s*([^|]{2,10}?)\s*\|\s*$', span_text)
            if province_match:
                province = province_match.group(1).strip()
            
            # 提取采购人 - 格式: 采购人：xxx
            purchaser_match = re.search(r'采购人[：:]\s*([^|]+)', span_text)
            if purchaser_match:
                purchaser = purchaser_match.group(1).strip()
            
            # 提取代理机构 - 格式: 代理机构：xxx
            agency_match = re.search(r'代理机构[：:]\s*([^|]+)', span_text)
            if agency_match:
                agency = agency_match.group(1).strip()
        
        return TenderInfo(
            title=title,
            url=url,
            publish_date=publish_date,
            province=province,
            purchaser=purchaser,
            budget=budget,
            notice_type=notice_type,
            agency=agency
        )
    
    def get_total_pages(self, html: str) -> int:
        """获取总页数."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, "html.parser")
        
        # 查找分页信息 - 在包含 "共找到 X 条内容" 的段落中
        page_info = soup.find("p", string=re.compile(r'共找到\s*\d+\s*条内容'))
        if page_info:
            text = page_info.get_text()
            # 提取总条数
            total_match = re.search(r'共找到\s*(\d+)\s*条内容', text)
            if total_match:
                total_items = int(total_match.group(1))
                # 每页20条
                return (total_items + 19) // 20
        
        # 查找页码链接
        page_links = soup.find_all("a", class_=lambda x: x and "page" in str(x).lower())
        if page_links:
            max_page = 1
            for link in page_links:
                try:
                    page_text = link.get_text(strip=True)
                    if page_text.isdigit():
                        page_num = int(page_text)
                        max_page = max(max_page, page_num)
                except (ValueError, AttributeError):
                    continue
            return max_page
        
        return 1
    
    def search(self, keyword: str, max_results: Optional[int] = None) -> List[TenderInfo]:
        """搜索单个关键词的招标信息."""
        if max_results is None:
            max_results = self.config.max_results
            
        print(f"搜索关键词: {keyword}")
        
        http_client = self._get_http_client()
        
        all_results = []
        page = 1
        
        while len(all_results) < max_results:
            url = self.build_search_url(keyword, page)
            print(f"  获取第 {page} 页...")
            
            try:
                html = http_client.get_text(url)
                results = self.parse_list_page(html)
                
                if not results:
                    print(f"  第 {page} 页无数据，结束搜索")
                    break
                
                # 去重并添加关键词，同时获取详情页信息
                for result in results:
                    if result.url not in self._seen_urls:
                        self._seen_urls.add(result.url)
                        result.keyword = keyword
                        
                        # 获取详情页信息
                        try:
                            self._fetch_detail_info(result)
                        except Exception as e:
                            # 详情页获取失败不影响主流程
                            pass
                        
                        all_results.append(result)
                        
                        if len(all_results) >= max_results:
                            break
                
                print(f"  找到 {len(results)} 条，累计 {len(all_results)} 条")
                
                # 检查是否还有下一页
                total_pages = self.get_total_pages(html)
                if page >= total_pages:
                    break
                    
                page += 1
                
                # 请求频率控制
                time.sleep(1.5)
                
            except Exception as e:
                print(f"  获取第 {page} 页失败: {e}")
                break
        
        print(f"关键词 '{keyword}' 共找到 {len(all_results)} 条招标信息")
        return all_results[:max_results]
    
    def _fetch_detail_info(self, tender: TenderInfo):
        """从详情页获取完整信息（联系人和标的物）."""
        http_client = self._get_http_client()
        
        try:
            html = http_client.get_text(tender.url)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            full_text = soup.get_text()
            
            # 提取联系人信息
            self._extract_contact_info(tender, soup, full_text)
            
            # 提取标的物信息
            self._extract_subject_info(tender, soup, full_text)
            
        except Exception:
            # 获取详情页失败，忽略
            pass
    
    def _extract_contact_info(self, tender: TenderInfo, soup, full_text: str):
        """提取联系人信息."""
        try:
            # 查找联系方式部分
            contact_start = -1
            for keyword in ['联系方式', '联系方法', '凡对本次公告内容提出询问']:
                pos = full_text.find(keyword)
                if pos != -1:
                    contact_start = pos
                    break
            
            if contact_start != -1:
                contact_text = full_text[contact_start:contact_start+1500]
            else:
                contact_text = full_text
            
            # 提取项目联系人
            if not tender.contact_name:
                patterns = [
                    r'项目联系人[：:\s]+([^\n]+?)(?:\n|$)',
                    r'项目联系人[：:\s]+([^\n]+?)(?:电\s*话|$)',
                    r'联系人[：:\s]+([^\n]+?)(?:\n|$)',
                    r'联系人[：:\s]+([^\n]+?)(?:电\s*话|$)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, contact_text)
                    if match:
                        tender.contact_name = match.group(1).strip()
                        break
            
            # 提取电话
            if not tender.contact_phone:
                patterns = [
                    r'项目联系人电话[：:\s]+([^\n]+?)(?:\n|$)',
                    r'电\s*话[：:\s]+([^\n]+?)(?:\n|$)',
                    r'联系方式[：:\s]+([^\n]+?)(?:\n|$)',
                    r'电\s*话[：:\s]+([\d\-]+)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, contact_text)
                    if match:
                        phone = match.group(1).strip()
                        if len(phone) < 50:
                            tender.contact_phone = phone
                            break
            
            # 提取地址
            if not tender.contact_address:
                patterns = [
                    r'地\s*址[：:\s]+([^\n]+?)(?:\n|$)',
                    r'地\s*址[：:\s]+([^\n]+?)(?:联系方式|$)',
                ]
                for pattern in patterns:
                    match = re.search(pattern, contact_text)
                    if match:
                        tender.contact_address = match.group(1).strip()
                        break
            
            # 备用：遍历所有段落
            if not tender.contact_name or not tender.contact_phone:
                for elem in soup.find_all(['p', 'div', 'span', 'li']):
                    text = elem.get_text(strip=True)
                    
                    if not tender.contact_name:
                        match = re.search(r'项目联系人[：:\s]+([^\n]{2,20})(?:\n|$)', text)
                        if match:
                            tender.contact_name = match.group(1).strip()
                    
                    if not tender.contact_phone:
                        phone_patterns = [
                            r'(\d{3,4}-\d{7,8})',
                            r'(1[3-9]\d{9})',
                            r'(\d{7,8})',
                        ]
                        for pattern in phone_patterns:
                            match = re.search(pattern, text)
                            if match and '电话' in text:
                                tender.contact_phone = match.group(1)
                                break
                    
                    if not tender.contact_address:
                        if '地址' in text and len(text) > 10 and len(text) < 100:
                            match = re.search(r'地址[：:\s]+(.+)', text)
                            if match:
                                tender.contact_address = match.group(1).strip()
        
        except Exception:
            pass
    
    def _extract_subject_info(self, tender: TenderInfo, soup, full_text: str):
        """提取标的物信息."""
        try:
            subjects = []
            
            # 方法1: 查找"包内容"列的表格（最准确的医疗设备列表）
            for table in soup.find_all('table'):
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                # 获取表头
                header_row = rows[0]
                headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                
                # 查找"包内容"列
                subject_col_idx = -1
                for idx, header in enumerate(headers):
                    if '包内容' in header:
                        subject_col_idx = idx
                        break
                
                if subject_col_idx >= 0:
                    for row in rows[1:]:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) > subject_col_idx:
                            subject = cells[subject_col_idx].get_text(strip=True)
                            if subject and len(subject) > 3 and subject != '包内容':
                                # 过滤掉分类代码
                                if not re.match(r'^[A-Z]\d+$', subject):
                                    # 过滤无效内容
                                    if not self._is_invalid_subject(subject):
                                        subjects.append(subject)
            
            # 方法2: 查找"品目名称"列（询价公告常用）
            if not subjects:
                for table in soup.find_all('table'):
                    rows = table.find_all('tr')
                    if len(rows) < 2:
                        continue
                    
                    header_row = rows[0]
                    headers = [th.get_text(strip=True) for th in header_row.find_all(['th', 'td'])]
                    
                    # 查找品目名称列
                    subject_col_idx = -1
                    for idx, header in enumerate(headers):
                        if '品目名称' in header or '产品名称' in header or '货物名称' in header:
                            subject_col_idx = idx
                            break
                    
                    if subject_col_idx >= 0:
                        for row in rows[1:]:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) > subject_col_idx:
                                subject = cells[subject_col_idx].get_text(strip=True)
                                if subject and len(subject) > 3:
                                    # 过滤掉分类代码（如A02322700）
                                    if not re.match(r'^[A-Z]\d{6,}$', subject):
                                        # 如果包含分类代码和设备名，只取设备名
                                        if ' ' in subject:
                                            parts = subject.split()
                                            for part in parts:
                                                if not re.match(r'^[A-Z]\d+$', part) and len(part) > 3:
                                                    if not self._is_invalid_subject(part):
                                                        subjects.append(part)
                                                        break
                                        else:
                                            if not self._is_invalid_subject(subject):
                                                subjects.append(subject)
            
            # 方法3: 从标题中提取医疗设备名称
            if not subjects:
                # 匹配标题中的设备名称
                for keyword in self.MEDICAL_DEVICE_KEYWORDS:
                    # 匹配"XX keyword"或"keyword XX"格式
                    patterns = [
                        rf'([\u4e00-\u9fa5]{{2,8}}{keyword})',
                        rf'({keyword}[\u4e00-\u9fa5]{{2,8}})',
                        rf'([\u4e00-\u9fa5]{{2,6}}{keyword}[\u4e00-\u9fa5]{{0,6}})',
                    ]
                    for pattern in patterns:
                        matches = re.findall(pattern, tender.title)
                        for match in matches:
                            if len(match) > 4 and len(match) < 30:
                                subjects.append(match)
            
            # 方法4: 从页面文本中提取包含医疗设备关键词的内容
            if not subjects:
                # 查找包含医疗设备关键词的段落
                for elem in soup.find_all(['p', 'div', 'li', 'td']):
                    text = elem.get_text(strip=True)
                    if len(text) < 10 or len(text) > 100:
                        continue
                    
                    for keyword in self.MEDICAL_DEVICE_KEYWORDS:
                        if keyword in text:
                            # 提取包含关键词的短语
                            match = re.search(rf'([\u4e00-\u9fa5]{{2,15}}{keyword}[\u4e00-\u9fa5]{{0,10}})', text)
                            if match:
                                subject = match.group(1)
                                if len(subject) > 5 and len(subject) < 40:
                                    subjects.append(subject)
                                    break
            
            # 方法5: 从"采购需求"或"项目概况"后的文本提取
            if not subjects:
                patterns = [
                    r'采购需求[：:\s]*([^\n]{10,200})',
                    r'项目概况[：:\s]*([^\n]{10,200})',
                    r'标的内容[：:\s]*([^\n]{10,200})',
                ]
                for pattern in patterns:
                    match = re.search(pattern, full_text)
                    if match:
                        content = match.group(1).strip()
                        # 提取包含医疗设备关键词的部分
                        for keyword in self.MEDICAL_DEVICE_KEYWORDS:
                            if keyword in content:
                                # 找到关键词前后各20个字符
                                idx = content.find(keyword)
                                start = max(0, idx - 20)
                                end = min(len(content), idx + len(keyword) + 20)
                                subject = content[start:end].strip()
                                if len(subject) > 5:
                                    subjects.append(subject)
                                    break
                        if subjects:
                            break
            
            # 去重并合并
            if subjects:
                seen = set()
                unique_subjects = []
                for s in subjects:
                    # 检查是否是无效内容
                    if self._is_invalid_subject(s):
                        continue
                    
                    s_normalized = s.replace(' ', '').replace('\n', '').replace('\t', '')
                    if s_normalized not in seen and len(s) > 3 and len(s) < 100:
                        seen.add(s_normalized)
                        unique_subjects.append(s)
                
                if unique_subjects:
                    tender.subject = '；'.join(unique_subjects[:5])
                else:
                    # 如果从表格提取失败，尝试从标题提取
                    tender.subject = self._extract_subject_from_title(tender.title)
            
            # 最终检查：如果标的物包含无效内容，清空并使用标题提取
            if tender.subject and self._is_invalid_subject(tender.subject):
                tender.subject = self._extract_subject_from_title(tender.title)
        
        except Exception:
            pass
    
    def _extract_subject_from_title(self, title: str) -> str:
        """从标题中提取标的物（医疗设备名称）.
        
        Args:
            title: 招标标题
            
        Returns:
            str: 提取的标的物，如果没有则返回空字符串
        """
        subjects = []
        
        # 匹配标题中的设备名称
        for keyword in self.MEDICAL_DEVICE_KEYWORDS:
            # 匹配"XX keyword"或"keyword XX"格式
            patterns = [
                rf'([\u4e00-\u9fa5]{{2,8}}{keyword})',
                rf'({keyword}[\u4e00-\u9fa5]{{2,8}})',
                rf'([\u4e00-\u9fa5]{{2,6}}{keyword}[\u4e00-\u9fa5]{{0,6}})',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, title)
                for match in matches:
                    if len(match) > 4 and len(match) < 30:
                        subjects.append(match)
        
        # 去重
        if subjects:
            seen = set()
            unique_subjects = []
            for s in subjects:
                if s not in seen:
                    seen.add(s)
                    unique_subjects.append(s)
            return '；'.join(unique_subjects[:3])
        
        return ''
    
    def _is_invalid_subject(self, text: str) -> bool:
        """检查文本是否是无效的标的物内容.
        
        Args:
            text: 要检查的文本
            
        Returns:
            bool: 如果是无效内容返回True
        """
        invalid_patterns = [
            r'本公告页面内容仅供阅览使用',
            r'供应商只有登陆',
            r'政府采购网',
            r'首次参与',
            r'CA数字证书',
            r'投标文件',
            r'投标人',
            r'招标公告',
            r'中标公告',
            r'采购公告',
            r'在线开评标',
            r'电子招投标',
            r'操作手册',
            r'下载',
            r'注册',
            r'登录',
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def search_all_keywords(self) -> Dict[str, List[TenderInfo]]:
        """搜索所有关键词."""
        results = {}
        
        for keyword in self.config.keywords:
            results[keyword] = self.search(keyword)
            
            # 关键词之间也添加延迟
            if keyword != self.config.keywords[-1]:
                time.sleep(2)
        
        return results
    
    def close(self):
        """关闭抓取器，释放资源."""
        if self.http_client:
            self.http_client.close()
