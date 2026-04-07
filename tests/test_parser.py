"""HTML解析模块测试."""

import pytest
from datetime import datetime
from src.parser import TenderInfo, TenderParser


class TestTenderInfo:
    """TenderInfo测试类."""
    
    def test_to_dict(self):
        """测试转换为字典."""
        tender = TenderInfo(
            title="测试招标",
            url="http://example.com",
            publish_date="2024-01-01",
            source="中国政府采购网",
            keyword="眼科",
            description="测试描述",
            region="北京市",
            agency="测试代理",
            project_code="XYZ123"
        )
        
        data = tender.to_dict()
        
        assert data["标题"] == "测试招标"
        assert data["链接"] == "http://example.com"
        assert data["发布日期"] == "2024-01-01"
        assert data["信息来源"] == "中国政府采购网"
        assert data["关键词"] == "眼科"
        assert data["项目描述"] == "测试描述"
        assert data["地区"] == "北京市"
        assert data["代理机构"] == "测试代理"
        assert data["项目编号"] == "XYZ123"
        assert "抓取时间" in data
    
    def test_from_dict(self):
        """测试从字典创建."""
        data = {
            "标题": "测试招标",
            "链接": "http://example.com",
            "发布日期": "2024-01-01",
            "信息来源": "中国政府采购网",
            "关键词": "眼科",
            "项目描述": "测试描述",
            "地区": "北京市",
            "代理机构": "测试代理",
            "项目编号": "XYZ123",
        }
        
        tender = TenderInfo.from_dict(data)
        
        assert tender.title == "测试招标"
        assert tender.url == "http://example.com"
        assert tender.publish_date == "2024-01-01"
        assert tender.source == "中国政府采购网"
        assert tender.keyword == "眼科"
        assert tender.description == "测试描述"
        assert tender.region == "北京市"
        assert tender.agency == "测试代理"
        assert tender.project_code == "XYZ123"
    
    def test_default_crawled_at(self):
        """测试默认抓取时间."""
        before = datetime.now()
        tender = TenderInfo(
            title="测试",
            url="http://example.com",
            publish_date="2024-01-01",
            source="测试来源"
        )
        after = datetime.now()
        
        assert before <= tender.crawled_at <= after


class TestTenderParser:
    """TenderParser测试类."""
    
    def test_init_with_keyword(self):
        """测试带关键词初始化."""
        parser = TenderParser(keyword="眼科")
        assert parser.keyword == "眼科"
    
    def test_parse_list_page_empty(self):
        """测试解析空页面."""
        parser = TenderParser()
        html = "<html><body></body></html>"
        
        tenders = parser.parse_list_page(html)
        
        assert tenders == []
    
    def test_parse_list_page_with_results(self):
        """测试解析有结果的页面."""
        parser = TenderParser(keyword="眼科")
        html = """
        <html>
        <body>
            <ul class="vT-srch-result-list">
                <li>
                    <a href="http://example.com/1">眼科设备采购项目</a>
                    <span class="time">2024-01-15</span>
                    <span class="source">中国政府采购网</span>
                    <span class="region">北京市</span>
                    <span class="agency">北京代理公司</span>
                    <span class="code">ABC123</span>
                    <p class="des">采购眼科医疗设备</p>
                </li>
                <li>
                    <a href="http://example.com/2">皮肤科治疗设备</a>
                    <span class="time">2024-01-14</span>
                    <span class="source">中国政府采购网</span>
                </li>
            </ul>
        </body>
        </html>
        """
        
        tenders = parser.parse_list_page(html)
        
        assert len(tenders) == 2
        assert tenders[0].title == "眼科设备采购项目"
        assert tenders[0].url == "http://example.com/1"
        assert tenders[0].publish_date == "2024-01-15"
        assert tenders[0].source == "中国政府采购网"
        assert tenders[0].region == "北京市"
        assert tenders[0].agency == "北京代理公司"
        assert tenders[0].project_code == "ABC123"
        assert tenders[0].description == "采购眼科医疗设备"
        assert tenders[0].keyword == "眼科"
        
        assert tenders[1].title == "皮肤科治疗设备"
    
    def test_parse_list_page_alternative_structure(self):
        """测试解析备选结构的页面."""
        parser = TenderParser()
        html = """
        <html>
        <body>
            <li class="search-result">
                <a href="http://example.com/1">测试项目</a>
            </li>
        </body>
        </html>
        """
        
        tenders = parser.parse_list_page(html)
        
        assert len(tenders) == 1
        assert tenders[0].title == "测试项目"
    
    def test_filter_by_date(self):
        """测试按日期过滤."""
        parser = TenderParser()
        tenders = [
            TenderInfo("项目1", "url1", "2024-01-10", "source"),
            TenderInfo("项目2", "url2", "2024-01-15", "source"),
            TenderInfo("项目3", "url3", "2024-01-20", "source"),
        ]
        
        filtered = parser.filter_by_date(tenders, "2024-01-12", "2024-01-18")
        
        assert len(filtered) == 1
        assert filtered[0].title == "项目2"
    
    def test_filter_by_date_different_formats(self):
        """测试不同日期格式的过滤."""
        parser = TenderParser()
        tenders = [
            TenderInfo("项目1", "url1", "2024/01/10", "source"),
            TenderInfo("项目2", "url2", "2024年01月15日", "source"),
        ]
        
        filtered = parser.filter_by_date(tenders, "2024-01-01", "2024-01-31")
        
        assert len(filtered) == 2
    
    def test_filter_by_keywords(self):
        """测试按关键词过滤."""
        parser = TenderParser()
        tenders = [
            TenderInfo("眼科设备采购", "url1", "2024-01-10", "source", description="眼科相关"),
            TenderInfo("普通办公用品", "url2", "2024-01-15", "source", description="办公用品"),
            TenderInfo("皮肤科治疗设备", "url3", "2024-01-20", "source", description="皮肤科"),
        ]
        
        filtered = parser.filter_by_keywords(tenders, ["眼科", "皮肤科"])
        
        assert len(filtered) == 2
        assert filtered[0].title == "眼科设备采购"
        assert filtered[1].title == "皮肤科治疗设备"
    
    def test_filter_by_keywords_empty_list(self):
        """测试空关键词列表不过滤."""
        parser = TenderParser()
        tenders = [
            TenderInfo("项目1", "url1", "2024-01-10", "source"),
            TenderInfo("项目2", "url2", "2024-01-15", "source"),
        ]
        
        filtered = parser.filter_by_keywords(tenders, [])
        
        assert len(filtered) == 2
    
    def test_parse_date_various_formats(self):
        """测试多种日期格式解析."""
        parser = TenderParser()
        
        assert parser._parse_date("2024-01-15") == datetime(2024, 1, 15)
        assert parser._parse_date("2024/01/15") == datetime(2024, 1, 15)
        assert parser._parse_date("2024年01月15日") == datetime(2024, 1, 15)
        assert parser._parse_date("2024.01.15") == datetime(2024, 1, 15)
        assert parser._parse_date("2024:01:15") == datetime(2024, 1, 15)
    
    def test_parse_date_invalid(self):
        """测试无效日期解析."""
        parser = TenderParser()
        
        assert parser._parse_date("") is None
        assert parser._parse_date("invalid") is None
        assert parser._parse_date("2024-13-45") is None
    
    def test_extract_total_pages(self):
        """测试提取总页数."""
        parser = TenderParser()
        html = """
        <html>
        <body>
            <span class="page-info">共 10 页</span>
        </body>
        </html>
        """
        
        pages = parser.extract_total_pages(html)
        
        assert pages == 10
    
    def test_extract_total_pages_from_pagination(self):
        """测试从分页链接提取总页数."""
        parser = TenderParser()
        html = """
        <html>
        <body>
            <div class="pagination">
                <a href="?page=1">1</a>
                <a href="?page=2">2</a>
                <a href="?page=3">3</a>
            </div>
        </body>
        </html>
        """
        
        pages = parser.extract_total_pages(html)
        
        assert pages == 3
    
    def test_extract_total_pages_default(self):
        """测试默认页数."""
        parser = TenderParser()
        html = "<html><body></body></html>"
        
        pages = parser.extract_total_pages(html)
        
        assert pages == 1
